from __future__ import annotations

import json

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import ViolationEvent
from .schemas import ViolationCreate, ViolationRead, ViolationUpdateStatus


app = FastAPI(title="Littering MVP API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def root() -> dict:
    return {
        "service": "Littering MVP API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


def _row_to_response(row: ViolationEvent) -> ViolationEvent:
    if isinstance(row.metadata_json, str):
        row.metadata_json = json.loads(row.metadata_json or "{}")
    return row


@app.post("/violations", response_model=ViolationRead)
def create_violation(payload: ViolationCreate, db: Session = Depends(get_db)):
    existing = db.query(ViolationEvent).filter(ViolationEvent.event_id == payload.event_id).first()
    if existing:
        return _row_to_response(existing)

    event = ViolationEvent(
        event_id=payload.event_id,
        violation_type=payload.violation_type,
        vehicle_track_id=payload.vehicle_track_id,
        plate_text=payload.plate_text,
        plate_confidence=payload.plate_confidence,
        detection_confidence=payload.detection_confidence,
        timestamp_ms=payload.timestamp_ms,
        camera_id=payload.camera_id,
        source_video=payload.source_video,
        image_path=payload.image_path,
        clip_path=payload.clip_path,
        metadata_json=json.dumps(payload.metadata_json),
        status="PENDING",
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return _row_to_response(event)


@app.get("/violations", response_model=list[ViolationRead])
def list_violations(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(ViolationEvent)
    if status:
        query = query.filter(ViolationEvent.status == status.upper())

    rows = query.order_by(ViolationEvent.created_at.desc()).limit(limit).all()
    return [_row_to_response(row) for row in rows]


@app.patch("/violations/{event_id}/status", response_model=ViolationRead)
def update_status(event_id: str, payload: ViolationUpdateStatus, db: Session = Depends(get_db)):
    row = db.query(ViolationEvent).filter(ViolationEvent.event_id == event_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Violation not found")

    next_status = payload.status.upper()
    if next_status not in {"PENDING", "APPROVED", "REJECTED"}:
        raise HTTPException(status_code=400, detail="Invalid status")

    row.status = next_status
    row.review_note = payload.review_note
    db.commit()
    db.refresh(row)
    return _row_to_response(row)
