from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field, field_validator


class ViolationCreate(BaseModel):
    event_id: str = Field(..., max_length=128)
    violation_type: str = Field(default="LITTERING_CANDIDATE", max_length=64)
    vehicle_track_id: int
    plate_text: str = Field(default="", max_length=32)
    plate_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    detection_confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp_ms: int
    camera_id: str = Field(default="cam-01", max_length=64)
    source_video: str = Field(..., max_length=500)
    image_path: str = Field(..., max_length=500)
    clip_path: str = Field(default="", max_length=500)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata_json")
    @classmethod
    def limit_metadata_size(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Prevent excessively large metadata payloads (max ~64KB serialised)."""
        import json
        if len(json.dumps(v)) > 65_536:
            raise ValueError("metadata_json exceeds 64KB limit")
        return v

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, v: str) -> str:
        """Only allow safe characters in event IDs."""
        import re
        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", v):
            raise ValueError("event_id may only contain alphanumeric, dash, dot, underscore")
        return v


class ViolationUpdateStatus(BaseModel):
    status: str = Field(..., max_length=32)
    review_note: str = Field(default="", max_length=500)


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
