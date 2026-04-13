from __future__ import annotations

import json

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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


@app.get("/", response_class=HTMLResponse)
def root() -> str:
        return """
        <!doctype html>
        <html lang="en">
            <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <title>Littering MVP API</title>
                <style>
                    :root {
                        --bg: #f4f6f2;
                        --card: #ffffff;
                        --text: #1f2a1f;
                        --muted: #5a665a;
                        --accent: #1f7a4d;
                        --accent-2: #145a38;
                        --border: #d9e2d9;
                    }
                    body {
                        margin: 0;
                        min-height: 100vh;
                        display: grid;
                        place-items: center;
                        background: radial-gradient(circle at top left, #e7efe6 0%, var(--bg) 55%);
                        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                        color: var(--text);
                    }
                    .card {
                        width: min(680px, 92vw);
                        background: var(--card);
                        border: 1px solid var(--border);
                        border-radius: 18px;
                        padding: 28px;
                        box-shadow: 0 12px 28px rgba(28, 48, 30, 0.09);
                    }
                    h1 {
                        margin: 0 0 10px;
                        font-size: 1.9rem;
                    }
                    p {
                        margin: 0 0 18px;
                        color: var(--muted);
                        line-height: 1.5;
                    }
                    .links {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 10px;
                    }
                    a {
                        text-decoration: none;
                        padding: 10px 14px;
                        border-radius: 10px;
                        border: 1px solid var(--border);
                        color: var(--accent-2);
                        font-weight: 600;
                        transition: all 160ms ease;
                    }
                    a.primary {
                        background: var(--accent);
                        border-color: var(--accent);
                        color: #fff;
                    }
                    a:hover {
                        transform: translateY(-1px);
                        box-shadow: 0 6px 14px rgba(31, 122, 77, 0.2);
                    }
                </style>
            </head>
            <body>
                <main class="card">
                    <h1>Littering MVP API is Live</h1>
                    <p>
                        Server is healthy and ready. Use the API docs to test routes, or open
                        health check for quick status.
                    </p>
                    <div class="links">
                        <a class="primary" href="/docs">Open API Docs</a>
                        <a href="/health">Health Check</a>
                        <a href="/violations">Sample Violations List</a>
                    </div>
                </main>
            </body>
        </html>
        """


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
