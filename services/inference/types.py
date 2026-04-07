from dataclasses import dataclass
from typing import Optional, Tuple


BBox = Tuple[int, int, int, int]


@dataclass
class TrackedVehicle:
    track_id: int
    label: str
    confidence: float
    bbox: BBox


@dataclass
class PlateRead:
    text: str
    confidence: float


@dataclass
class LitterCandidate:
    frame_index: int
    vehicle_track_id: int
    vehicle_bbox: BBox
    object_bbox: BBox
    confidence: float
    reason: str
    timestamp_ms: int
    plate_text: Optional[str] = None
    plate_confidence: float = 0.0
