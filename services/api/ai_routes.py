"""API routes for AI backend configuration and frame analysis."""

from __future__ import annotations

import base64
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Backend"])


# ---------------------------------------------------------------------------
# In-memory runtime state  (survives across requests, reset on restart)
# ---------------------------------------------------------------------------

class _RuntimeAIState:
    """Holds the currently active AI backend configuration at runtime."""

    def __init__(self) -> None:
        self.provider: str = "heuristic"
        self.api_key: str = ""
        self.model: str = ""
        self.ollama_url: str = "http://localhost:11434"
        self._backend = None

    def get_backend(self):
        from services.inference.ai_backend import create_backend
        if self._backend is None:
            self._backend = create_backend(
                provider=self.provider,
                api_key=self.api_key,
                model=self.model,
                ollama_url=self.ollama_url,
            )
        return self._backend

    def reset_backend(self):
        self._backend = None


_state = _RuntimeAIState()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class AIConfigureRequest(BaseModel):
    provider: str  # gemini | openai | claude | ollama | heuristic
    api_key: str = ""
    model: str = ""
    ollama_url: str = "http://localhost:11434"


class AIConfigureResponse(BaseModel):
    provider: str
    model: str
    status: str


class AIAnalyzeRequest(BaseModel):
    image_base64: str
    detection_context: str = ""


class AIAnalysisResponse(BaseModel):
    verdict: str
    confidence: float
    reasoning: str
    provider: str
    model: str


class AIStatusResponse(BaseModel):
    provider: str
    model: str
    status: str
    detail: str = ""
    available_models: List[str] = []


class ProviderInfo(BaseModel):
    id: str
    name: str
    requires_key: str
    default_model: str
    models: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/providers", response_model=List[ProviderInfo])
def list_ai_providers():
    """List all supported AI providers with their metadata."""
    from services.inference.ai_backend import list_providers
    return list_providers()


@router.get("/status", response_model=AIStatusResponse)
def ai_status():
    """Return current AI backend status and connectivity."""
    backend = _state.get_backend()
    info = backend.health_check()
    return AIStatusResponse(
        provider=info.get("provider", _state.provider),
        model=info.get("model", _state.model),
        status=info.get("status", "unknown"),
        detail=info.get("detail", ""),
        available_models=info.get("available_models", []),
    )


@router.post("/configure", response_model=AIConfigureResponse)
def configure_ai(req: AIConfigureRequest):
    """Set the active AI backend at runtime."""
    from services.inference.ai_backend import create_backend

    try:
        backend = create_backend(
            provider=req.provider,
            api_key=req.api_key,
            model=req.model,
            ollama_url=req.ollama_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Persist in runtime state
    _state.provider = req.provider
    _state.api_key = req.api_key
    _state.model = req.model
    _state.ollama_url = req.ollama_url
    _state.reset_backend()

    info = backend.health_check()
    return AIConfigureResponse(
        provider=req.provider,
        model=req.model or info.get("model", "default"),
        status=info.get("status", "configured"),
    )


@router.post("/analyze", response_model=AIAnalysisResponse)
def analyze_frame(req: AIAnalyzeRequest):
    """Analyze a single base64-encoded frame for littering."""
    try:
        image_bytes = base64.b64decode(req.image_base64)
        import numpy as np
        np_arr = np.frombuffer(image_bytes, dtype=np.uint8)
        import cv2
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Could not decode image")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image: {exc}")

    backend = _state.get_backend()
    result = backend.analyze_frame(frame, req.detection_context)

    return AIAnalysisResponse(
        verdict=result.verdict,
        confidence=result.confidence,
        reasoning=result.reasoning,
        provider=result.provider,
        model=result.model,
    )


@router.post("/analyze-upload", response_model=AIAnalysisResponse)
async def analyze_uploaded_frame(
    file: UploadFile = File(...),
    detection_context: str = Form(""),
):
    """Upload an image file and analyze it for littering."""
    contents = await file.read()
    try:
        import numpy as np
        np_arr = np.frombuffer(contents, dtype=np.uint8)
        import cv2
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Could not decode image")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image: {exc}")

    backend = _state.get_backend()
    result = backend.analyze_frame(frame, detection_context)

    return AIAnalysisResponse(
        verdict=result.verdict,
        confidence=result.confidence,
        reasoning=result.reasoning,
        provider=result.provider,
        model=result.model,
    )


@router.get("/ollama/models")
def list_ollama_models(ollama_url: str = "http://localhost:11434"):
    """Proxy: list models available on an Ollama server."""
    from services.inference.ai_backend import OllamaVisionBackend
    backend = OllamaVisionBackend(base_url=ollama_url)
    models = backend.list_models()
    return {"models": models, "url": ollama_url}
