from dataclasses import dataclass
from pathlib import Path
import os


def _env_bool(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _env_labels(name: str, default: str) -> tuple[str, ...]:
    raw = os.getenv(name, default)
    return tuple(token.strip().lower() for token in raw.split(",") if token.strip())


@dataclass
class InferenceConfig:
    vehicle_model: str = os.getenv("VEHICLE_MODEL", "yolov8n.pt")
    litter_model: str = os.getenv("LITTER_MODEL", "yolov8n.pt")
    evidence_dir: Path = Path(os.getenv("EVIDENCE_DIR", "data/evidence"))
    clips_dir: Path = Path(os.getenv("CLIPS_DIR", "data/clips"))
    frame_skip: int = int(os.getenv("FRAME_SKIP", "1"))
    min_object_confidence: float = float(os.getenv("MIN_OBJECT_CONFIDENCE", "0.20"))
    motion_threshold: int = int(os.getenv("MOTION_THRESHOLD", "18"))
    min_blob_area: int = int(os.getenv("MIN_BLOB_AREA", "40"))
    max_blob_area: int = int(os.getenv("MAX_BLOB_AREA", "3500"))
    attach_distance_px: int = int(os.getenv("ATTACH_DISTANCE_PX", "80"))
    outward_step_px: int = int(os.getenv("OUTWARD_STEP_PX", "3"))
    min_vehicle_motion_px: float = float(os.getenv("MIN_VEHICLE_MOTION_PX", "0.8"))
    confirm_steps: int = int(os.getenv("CONFIRM_STEPS", "1"))
    min_litter_confidence: float = float(os.getenv("MIN_LITTER_CONFIDENCE", "0.58"))
    uncertain_confidence_floor: float = float(os.getenv("UNCERTAIN_CONFIDENCE_FLOOR", "0.45"))
    emit_uncertain_events: bool = _env_bool("EMIT_UNCERTAIN_EVENTS", "true")
    min_label_confidence: float = float(os.getenv("MIN_LABEL_CONFIDENCE", "0.30"))
    litter_labels: tuple[str, ...] = _env_labels(
        "LITTER_LABELS",
        "trash,litter,garbage,waste,plastic,bottle,cup,can,bag,wrapper,paper,"
        "handbag,backpack,umbrella,sports ball,frisbee,book,cell phone,"
        "banana,apple,sandwich,donut,pizza,cake,vase,scissors,teddy bear,"
        "wine glass,fork,knife,spoon,bowl,potted plant,remote,suitcase",
    )
    non_litter_labels: tuple[str, ...] = _env_labels(
        "NON_LITTER_LABELS",
        "person,car,bus,truck,motorcycle,bicycle,bird,dog,cat,horse,sheep,cow,"
        "elephant,bear,zebra,giraffe,traffic light,fire hydrant,stop sign,"
        "parking meter,bench,couch,bed,dining table,toilet,tv,laptop,oven,"
        "refrigerator,sink,microwave,toaster",
    )
    event_cooldown_frames: int = int(os.getenv("EVENT_COOLDOWN_FRAMES", "45"))
    clip_pre_frames: int = int(os.getenv("CLIP_PRE_FRAMES", "45"))
    clip_post_frames: int = int(os.getenv("CLIP_POST_FRAMES", "45"))

    # --- AI Vision Backend ---
    # Provider: "gemini", "openai", "claude", "ollama", "heuristic"
    ai_backend: str = os.getenv("AI_BACKEND", "heuristic")
    ai_model: str = os.getenv("AI_MODEL", "")  # override per-provider default

    # Cloud API keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Ollama (local hosting)
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llava")
