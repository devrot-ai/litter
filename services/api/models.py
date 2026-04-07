from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from .database import Base


class ViolationEvent(Base):
    __tablename__ = "violation_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    violation_type = Column(String(64), nullable=False, default="LITTERING_CANDIDATE")
    vehicle_track_id = Column(Integer, nullable=False)
    plate_text = Column(String(32), nullable=False, default="")
    plate_confidence = Column(Float, nullable=False, default=0.0)
    detection_confidence = Column(Float, nullable=False)
    timestamp_ms = Column(Integer, nullable=False)
    camera_id = Column(String(64), nullable=False, default="cam-01")
    source_video = Column(String(500), nullable=False)
    image_path = Column(String(500), nullable=False)
    clip_path = Column(String(500), nullable=False, default="")
    metadata_json = Column(Text, nullable=False, default="{}")
    status = Column(String(32), nullable=False, default="PENDING")
    review_note = Column(String(500), nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
