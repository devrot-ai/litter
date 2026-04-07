from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class ViolationCreate(BaseModel):
    event_id: str
    violation_type: str = "LITTERING_CANDIDATE"
    vehicle_track_id: int
    plate_text: str = ""
    plate_confidence: float = 0.0
    detection_confidence: float
    timestamp_ms: int
    camera_id: str = "cam-01"
    source_video: str
    image_path: str
    clip_path: str = ""
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ViolationUpdateStatus(BaseModel):
    status: str
    review_note: str = ""


class ViolationRead(BaseModel):
    id: int
    event_id: str
    violation_type: str
    vehicle_track_id: int
    plate_text: str
    plate_confidence: float
    detection_confidence: float
    timestamp_ms: int
    camera_id: str
    source_video: str
    image_path: str
    clip_path: str
    metadata_json: Dict[str, Any]
    status: str
    review_note: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
