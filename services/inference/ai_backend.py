"""
Multi-LLM Vision AI backend for litter detection.

Supported providers:
  - Google Gemini  (gemini-2.0-flash, gemini-2.5-pro, …)
  - OpenAI         (gpt-4o, gpt-4o-mini, …)
  - Anthropic      (claude-sonnet-4-20250514, claude-haiku, …)
  - Ollama (local) (llava, llama3.2-vision, bakllava, …)
  - Heuristic-only (no API, uses YOLO + motion scores)
"""

from __future__ import annotations

import base64
import io
import json
import logging
import re
import asyncio
import httpx
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import numpy as np
except ImportError:
    class DummyNP:
        class ndarray:
            pass
    np = DummyNP

try:
    import cv2
except ImportError:
    cv2 = None

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared data types
# ---------------------------------------------------------------------------

@dataclass
class LitterAnalysis:
    """Standardised result returned by every AI backend."""
    verdict: str = "UNCERTAIN"          # LITTER | NOT_LITTER | UNCERTAIN
    confidence: float = 0.50
    reasoning: str = ""
    raw_response: str = ""
    provider: str = "unknown"
    model: str = "unknown"


ANALYSIS_PROMPT = (
    "You are a traffic-camera litter-detection assistant. "
    "Analyze this frame from a roadside camera. "
    "Determine whether a person or vehicle occupant is throwing or has thrown "
    "litter (trash, plastic, bottle, wrapper, food waste, etc.) out of a vehicle.\n\n"
    "Additional context from object detection:\n{detections}\n\n"
    "Respond ONLY with a JSON object (no markdown, no code fences):\n"
    '{{"verdict": "LITTER" | "NOT_LITTER" | "UNCERTAIN", '
    '"confidence": 0.0-1.0, '
    '"reasoning": "one-sentence explanation"}}'
)


def _encode_frame_base64(frame: np.ndarray, quality: int = 75) -> str:
    """Encode an OpenCV BGR frame as a base64 JPEG string."""
    import cv2
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    ok, buffer = cv2.imencode(".jpg", frame, encode_params)
    if not ok:
        raise ValueError("Failed to encode frame as JPEG")
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def _parse_llm_json(raw: str) -> Dict[str, Any]:
    """Best-effort extraction of JSON from an LLM response string."""
    # Try direct parse first
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"```", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: find the first {...} block
    match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {}


def _build_analysis(parsed: dict, raw: str, provider: str, model: str) -> LitterAnalysis:
    """Convert a parsed JSON dict into a LitterAnalysis."""
    verdict = str(parsed.get("verdict", "UNCERTAIN")).upper().strip()
    if verdict not in ("LITTER", "NOT_LITTER", "UNCERTAIN"):
        verdict = "UNCERTAIN"

    try:
        confidence = float(parsed.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
    except (ValueError, TypeError):
        confidence = 0.5

    reasoning = str(parsed.get("reasoning", ""))

    return LitterAnalysis(
        verdict=verdict,
        confidence=confidence,
        reasoning=reasoning,
        raw_response=raw,
        provider=provider,
        model=model,
    )


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class VisionAIBackend(ABC):
    """Interface that every AI backend implements."""

    provider_name: str = "unknown"

    @abstractmethod
    async def analyze_frame_async(
        self,
        frame: np.ndarray,
        detection_context: str = "",
    ) -> LitterAnalysis:
        """Analyze a single video frame asynchronously."""

    def analyze_frame(
        self,
        frame: np.ndarray,
        detection_context: str = "",
    ) -> LitterAnalysis:
        """Analyze a single video frame synchronously."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop and loop.is_running():
            raise RuntimeError("Called synchronous analyze_frame from inside an async loop. Use analyze_frame_async instead.")
        return asyncio.run(self.analyze_frame_async(frame, detection_context))

    async def health_check_async(self) -> Dict[str, Any]:
        """Return connectivity / status information asynchronously."""
        return {"provider": self.provider_name, "status": "ok"}

    def health_check(self) -> Dict[str, Any]:
        """Return connectivity / status information synchronously."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop and loop.is_running():
            raise RuntimeError("Called synchronous health_check from inside an async loop. Use health_check_async instead.")
        return asyncio.run(self.health_check_async())


# ---------------------------------------------------------------------------
# 1) Google Gemini
# ---------------------------------------------------------------------------

class GeminiVisionBackend(VisionAIBackend):
    provider_name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self.api_key = api_key
        self.model = model
        self._endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

    async def analyze_frame_async(self, frame: np.ndarray, detection_context: str = "") -> LitterAnalysis:
        b64 = _encode_frame_base64(frame)
        prompt = ANALYSIS_PROMPT.format(detections=detection_context or "none")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": b64,
                            }
                        },
                    ]
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self._endpoint, json=payload, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            raw = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:
            logger.warning("Gemini API error: %s", exc)
            return LitterAnalysis(
                verdict="UNCERTAIN", confidence=0.5,
                reasoning=f"Gemini API error: {exc}",
                provider="gemini", model=self.model,
            )

        parsed = _parse_llm_json(raw)
        return _build_analysis(parsed, raw, "gemini", self.model)

    async def health_check_async(self) -> Dict[str, Any]:
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.model}?key={self.api_key}"
            )
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10.0)
            return {
                "provider": "gemini",
                "model": self.model,
                "status": "connected" if resp.status_code == 200 else "error",
                "status_code": resp.status_code,
            }
        except Exception as exc:
            return {"provider": "gemini", "status": "error", "detail": str(exc)}


# ---------------------------------------------------------------------------
# 2) OpenAI (GPT-4o Vision)
# ---------------------------------------------------------------------------

class OpenAIVisionBackend(VisionAIBackend):
    provider_name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model
        self._endpoint = "https://api.openai.com/v1/chat/completions"

    async def analyze_frame_async(self, frame: np.ndarray, detection_context: str = "") -> LitterAnalysis:
        b64 = _encode_frame_base64(frame)
        prompt = ANALYSIS_PROMPT.format(detections=detection_context or "none")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}",
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 300,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self._endpoint, json=payload, headers=headers, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.warning("OpenAI API error: %s", exc)
            return LitterAnalysis(
                verdict="UNCERTAIN", confidence=0.5,
                reasoning=f"OpenAI API error: {exc}",
                provider="openai", model=self.model,
            )

        parsed = _parse_llm_json(raw)
        return _build_analysis(parsed, raw, "openai", self.model)

    async def health_check_async(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0,
                )
            return {
                "provider": "openai",
                "model": self.model,
                "status": "connected" if resp.status_code == 200 else "error",
                "status_code": resp.status_code,
            }
        except Exception as exc:
            return {"provider": "openai", "status": "error", "detail": str(exc)}


# ---------------------------------------------------------------------------
# 3) Anthropic Claude
# ---------------------------------------------------------------------------

class ClaudeVisionBackend(VisionAIBackend):
    provider_name = "claude"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self.api_key = api_key
        self.model = model
        self._endpoint = "https://api.anthropic.com/v1/messages"

    async def analyze_frame_async(self, frame: np.ndarray, detection_context: str = "") -> LitterAnalysis:
        b64 = _encode_frame_base64(frame)
        prompt = ANALYSIS_PROMPT.format(detections=detection_context or "none")

        payload = {
            "model": self.model,
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self._endpoint, json=payload, headers=headers, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            raw = data["content"][0]["text"]
        except Exception as exc:
            logger.warning("Claude API error: %s", exc)
            return LitterAnalysis(
                verdict="UNCERTAIN", confidence=0.5,
                reasoning=f"Claude API error: {exc}",
                provider="claude", model=self.model,
            )

        parsed = _parse_llm_json(raw)
        return _build_analysis(parsed, raw, "claude", self.model)

    async def health_check_async(self) -> Dict[str, Any]:
        # Claude doesn't have a lightweight health endpoint;
        # just confirm the key looks valid.
        return {
            "provider": "claude",
            "model": self.model,
            "status": "configured" if self.api_key else "no_key",
        }


# ---------------------------------------------------------------------------
# 4) Ollama (local)
# ---------------------------------------------------------------------------

class OllamaVisionBackend(VisionAIBackend):
    provider_name = "ollama"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llava",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def analyze_frame_async(self, frame: np.ndarray, detection_context: str = "") -> LitterAnalysis:
        b64 = _encode_frame_base64(frame)
        prompt = ANALYSIS_PROMPT.format(detections=detection_context or "none")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [b64],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=120.0,  # local models can be slow
                )
            resp.raise_for_status()
            data = resp.json()
            raw = data.get("response", "")
        except Exception as exc:
            logger.warning("Ollama error: %s", exc)
            return LitterAnalysis(
                verdict="UNCERTAIN", confidence=0.5,
                reasoning=f"Ollama error: {exc}",
                provider="ollama", model=self.model,
            )

        parsed = _parse_llm_json(raw)
        return _build_analysis(parsed, raw, "ollama", self.model)

    async def health_check_async(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                return {
                    "provider": "ollama",
                    "url": self.base_url,
                    "model": self.model,
                    "status": "connected",
                    "available_models": models,
                }
            return {"provider": "ollama", "status": "error", "status_code": resp.status_code}
        except Exception as exc:
            return {"provider": "ollama", "status": "offline", "detail": str(exc)}

    def list_models(self) -> List[str]:
        """Return model names available on the Ollama server."""
        try:
            # this is mostly a synchronous fallback for legacy clients
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []


# ---------------------------------------------------------------------------
# 5) Heuristic-only (no external API)
# ---------------------------------------------------------------------------

class HeuristicOnlyBackend(VisionAIBackend):
    """Pass-through that relies entirely on the existing YOLO + motion logic."""
    provider_name = "heuristic"

    async def analyze_frame_async(self, frame: np.ndarray, detection_context: str = "") -> LitterAnalysis:
        return LitterAnalysis(
            verdict="UNCERTAIN",
            confidence=0.50,
            reasoning="Heuristic-only mode: verdict determined by YOLO + motion pipeline.",
            provider="heuristic",
            model="yolov8n",
        )

    async def health_check_async(self) -> Dict[str, Any]:
        return {"provider": "heuristic", "status": "ok", "detail": "No external API needed."}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

# Registry of known providers. Keys are lowercase provider names.
_PROVIDER_REGISTRY = {
    "gemini": GeminiVisionBackend,
    "openai": OpenAIVisionBackend,
    "claude": ClaudeVisionBackend,
    "anthropic": ClaudeVisionBackend,
    "ollama": OllamaVisionBackend,
    "heuristic": HeuristicOnlyBackend,
}


def create_backend(
    provider: str,
    api_key: str = "",
    model: str = "",
    ollama_url: str = "http://localhost:11434",
) -> VisionAIBackend:
    """Instantiate the right backend from a provider name."""
    key = provider.strip().lower()

    if key in ("gemini",):
        return GeminiVisionBackend(api_key=api_key, model=model or "gemini-2.0-flash")
    if key in ("openai", "chatgpt", "gpt"):
        return OpenAIVisionBackend(api_key=api_key, model=model or "gpt-4o-mini")
    if key in ("claude", "anthropic"):
        return ClaudeVisionBackend(api_key=api_key, model=model or "claude-sonnet-4-20250514")
    if key in ("ollama", "local"):
        return OllamaVisionBackend(base_url=ollama_url, model=model or "llava")
    if key in ("heuristic", "none", ""):
        return HeuristicOnlyBackend()

    raise ValueError(
        f"Unknown AI provider '{provider}'. "
        f"Supported: {', '.join(sorted(_PROVIDER_REGISTRY.keys()))}"
    )


def list_providers() -> List[Dict[str, str]]:
    """Return metadata for all supported providers."""
    return [
        {
            "id": "gemini",
            "name": "Google Gemini",
            "requires_key": "true",
            "default_model": "gemini-2.0-flash",
            "models": "gemini-2.0-flash, gemini-2.5-pro, gemini-2.5-flash",
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "requires_key": "true",
            "default_model": "gpt-4o-mini",
            "models": "gpt-4o, gpt-4o-mini, gpt-4.1",
        },
        {
            "id": "claude",
            "name": "Anthropic Claude",
            "requires_key": "true",
            "default_model": "claude-sonnet-4-20250514",
            "models": "claude-sonnet-4-20250514, claude-haiku, claude-opus-4-20250514",
        },
        {
            "id": "ollama",
            "name": "Ollama (Local)",
            "requires_key": "false",
            "default_model": "llava",
            "models": "llava, llama3.2-vision, bakllava, moondream",
        },
        {
            "id": "heuristic",
            "name": "Heuristic Only (No AI)",
            "requires_key": "false",
            "default_model": "yolov8n",
            "models": "yolov8n (built-in)",
        },
    ]
