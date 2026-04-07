from dataclasses import dataclass
from pathlib import Path
import os


@dataclass
class InferenceConfig:
    vehicle_model: str = os.getenv("VEHICLE_MODEL", "yolov8n.pt")
    litter_model: str = os.getenv("LITTER_MODEL", "")
    evidence_dir: Path = Path(os.getenv("EVIDENCE_DIR", "data/evidence"))
    clips_dir: Path = Path(os.getenv("CLIPS_DIR", "data/clips"))
    frame_skip: int = int(os.getenv("FRAME_SKIP", "2"))
    motion_threshold: int = int(os.getenv("MOTION_THRESHOLD", "25"))
    min_blob_area: int = int(os.getenv("MIN_BLOB_AREA", "80"))
    max_blob_area: int = int(os.getenv("MAX_BLOB_AREA", "2000"))
    attach_distance_px: int = int(os.getenv("ATTACH_DISTANCE_PX", "24"))
    outward_step_px: int = int(os.getenv("OUTWARD_STEP_PX", "10"))
    min_vehicle_motion_px: float = float(os.getenv("MIN_VEHICLE_MOTION_PX", "1.2"))
    confirm_steps: int = int(os.getenv("CONFIRM_STEPS", "2"))
    event_cooldown_frames: int = int(os.getenv("EVENT_COOLDOWN_FRAMES", "75"))
    clip_pre_frames: int = int(os.getenv("CLIP_PRE_FRAMES", "45"))
    clip_post_frames: int = int(os.getenv("CLIP_POST_FRAMES", "45"))
