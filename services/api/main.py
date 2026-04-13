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
                        --bg: #e8efe7;
                        --paper: #ffffff;
                        --ink: #122016;
                        --muted: #4f6052;
                        --accent: #1b8f57;
                        --accent-2: #0f6a3f;
                        --danger: #be2f2f;
                        --warning: #a36b17;
                        --border: #d0ddcf;
                        --shadow: rgba(18, 32, 22, 0.14);
                    }

                    body {
                        margin: 0;
                        min-height: 100dvh;
                        background:
                            radial-gradient(circle at 0% 0%, #d7e6d8 0%, transparent 28%),
                            radial-gradient(circle at 100% 0%, #dceadf 0%, transparent 24%),
                            var(--bg);
                        font-family: "Trebuchet MS", "Segoe UI", sans-serif;
                        color: var(--ink);
                    }

                    .wrap {
                        width: min(1080px, 94vw);
                        margin: 26px auto 40px;
                    }

                    .card {
                        background: var(--paper);
                        border: 1px solid var(--border);
                        border-radius: 16px;
                        box-shadow: 0 12px 30px var(--shadow);
                    }

                    .hero {
                        padding: 22px 22px 14px;
                    }

                    h1 {
                        margin: 0;
                        font-size: clamp(1.35rem, 3.8vw, 2.1rem);
                    }

                    p {
                        margin: 8px 0 0;
                        color: var(--muted);
                        line-height: 1.5;
                    }

                    .links {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 10px;
                        margin-top: 16px;
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
                        box-shadow: 0 6px 14px rgba(24, 102, 63, 0.26);
                    }

                    .grid {
                        margin-top: 16px;
                        display: grid;
                        grid-template-columns: repeat(4, minmax(0, 1fr));
                        gap: 10px;
                    }

                    .metric {
                        background: #f8fbf7;
                        border: 1px solid var(--border);
                        border-radius: 12px;
                        padding: 12px;
                    }

                    .metric .label {
                        color: var(--muted);
                        font-size: 0.82rem;
                    }

                    .metric .value {
                        margin-top: 6px;
                        font-size: 1.35rem;
                        font-weight: 700;
                    }

                    .stack {
                        margin-top: 14px;
                        display: grid;
                        grid-template-columns: 1fr;
                        gap: 14px;
                    }

                    .panel {
                        padding: 16px;
                    }

                    .panel h2 {
                        margin: 0 0 10px;
                        font-size: 1.1rem;
                    }

                    .toolbar {
                        display: flex;
                        flex-wrap: wrap;
                        align-items: center;
                        gap: 8px;
                        margin-bottom: 10px;
                    }

                    select,
                    input,
                    button {
                        border: 1px solid var(--border);
                        border-radius: 9px;
                        padding: 9px 10px;
                        background: #fff;
                        color: var(--ink);
                        font: inherit;
                    }

                    button {
                        cursor: pointer;
                        font-weight: 600;
                    }

                    button.primary {
                        background: var(--accent);
                        border-color: var(--accent);
                        color: #fff;
                    }

                    button.warn {
                        background: #fff8ed;
                        color: var(--warning);
                    }

                    button.danger {
                        background: #fff2f2;
                        color: var(--danger);
                    }

                    table {
                        width: 100%;
                        border-collapse: collapse;
                        overflow: hidden;
                    }

                    th,
                    td {
                        text-align: left;
                        border-bottom: 1px solid #edf2ed;
                        padding: 9px 6px;
                        font-size: 0.92rem;
                    }

                    th {
                        color: #37503d;
                        font-weight: 700;
                        font-size: 0.84rem;
                        letter-spacing: 0.01em;
                        text-transform: uppercase;
                    }

                    .row-actions {
                        display: flex;
                        gap: 6px;
                        flex-wrap: wrap;
                    }

                    .status {
                        margin-top: 8px;
                        min-height: 1.2em;
                        color: var(--muted);
                        font-size: 0.9rem;
                    }

                    .form-grid {
                        display: grid;
                        grid-template-columns: repeat(3, minmax(0, 1fr));
                        gap: 8px;
                    }

                    .form-grid .wide {
                        grid-column: span 3;
                    }

                    @media (max-width: 860px) {
                        .grid {
                            grid-template-columns: repeat(2, minmax(0, 1fr));
                        }
                        .form-grid {
                            grid-template-columns: 1fr;
                        }
                        .form-grid .wide {
                            grid-column: span 1;
                        }
                        th:nth-child(4),
                        td:nth-child(4),
                        th:nth-child(5),
                        td:nth-child(5) {
                            display: none;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="wrap">
                    <section class="card hero">
                        <h1>Littering MVP Control Panel</h1>
                        <p>View violations, review statuses, and add test events directly from this page.</p>
                        <div class="links">
                            <a class="primary" href="/docs">Open API Docs</a>
                            <a href="/health">Health Check</a>
                        </div>
                        <div class="grid">
                            <article class="metric"><div class="label">Total</div><div class="value" id="mTotal">0</div></article>
                            <article class="metric"><div class="label">Pending</div><div class="value" id="mPending">0</div></article>
                            <article class="metric"><div class="label">Approved</div><div class="value" id="mApproved">0</div></article>
                            <article class="metric"><div class="label">Rejected</div><div class="value" id="mRejected">0</div></article>
                        </div>
                    </section>

                    <section class="stack">
                        <article class="card panel">
                            <h2>Violations</h2>
                            <div class="toolbar">
                                <label for="statusFilter">Status</label>
                                <select id="statusFilter">
                                    <option value="">All</option>
                                    <option value="PENDING">Pending</option>
                                    <option value="APPROVED">Approved</option>
                                    <option value="REJECTED">Rejected</option>
                                </select>
                                <button id="refreshBtn" class="primary" type="button">Refresh</button>
                            </div>
                            <div class="status" id="statusText"></div>
                            <div style="overflow:auto;">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Event ID</th>
                                            <th>Status</th>
                                            <th>Plate</th>
                                            <th>Confidence</th>
                                            <th>Time (ms)</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="rows"></tbody>
                                </table>
                            </div>
                        </article>

                        <article class="card panel">
                            <h2>Create Test Violation</h2>
                            <form id="createForm" class="form-grid">
                                <input id="eventId" placeholder="event_id (optional)" />
                                <input id="trackId" type="number" placeholder="vehicle_track_id" value="1" required />
                                <input id="detConf" type="number" step="0.01" placeholder="detection_confidence" value="0.88" required />
                                <input id="plateText" placeholder="plate_text" value="UNKNOWN" />
                                <input id="sourceVideo" class="wide" placeholder="source_video" value="demo.mp4" required />
                                <input id="imagePath" class="wide" placeholder="image_path" value="/tmp/sample.jpg" required />
                                <button class="primary" type="submit">Create Violation</button>
                            </form>
                        </article>
                    </section>
                </div>

                <script>
                    const rowsEl = document.getElementById("rows");
                    const statusText = document.getElementById("statusText");
                    const statusFilter = document.getElementById("statusFilter");
                    const refreshBtn = document.getElementById("refreshBtn");
                    const createForm = document.getElementById("createForm");

                    function showStatus(msg) {
                        statusText.textContent = msg;
                    }

                    function setMetrics(rows) {
                        const counts = { total: rows.length, PENDING: 0, APPROVED: 0, REJECTED: 0 };
                        rows.forEach((r) => {
                            const key = (r.status || "").toUpperCase();
                            if (counts[key] !== undefined) counts[key] += 1;
                        });
                        document.getElementById("mTotal").textContent = String(counts.total);
                        document.getElementById("mPending").textContent = String(counts.PENDING);
                        document.getElementById("mApproved").textContent = String(counts.APPROVED);
                        document.getElementById("mRejected").textContent = String(counts.REJECTED);
                    }

                    function renderRows(rows) {
                        rowsEl.innerHTML = "";
                        if (!rows.length) {
                            const tr = document.createElement("tr");
                            const td = document.createElement("td");
                            td.colSpan = 6;
                            td.textContent = "No violations found.";
                            tr.appendChild(td);
                            rowsEl.appendChild(tr);
                            return;
                        }

                        rows.forEach((row) => {
                            const tr = document.createElement("tr");

                            const eventId = document.createElement("td");
                            eventId.textContent = row.event_id;
                            tr.appendChild(eventId);

                            const status = document.createElement("td");
                            status.textContent = row.status;
                            tr.appendChild(status);

                            const plate = document.createElement("td");
                            plate.textContent = row.plate_text || "-";
                            tr.appendChild(plate);

                            const conf = document.createElement("td");
                            conf.textContent = String(row.detection_confidence ?? "-");
                            tr.appendChild(conf);

                            const ts = document.createElement("td");
                            ts.textContent = String(row.timestamp_ms ?? "-");
                            tr.appendChild(ts);

                            const actions = document.createElement("td");
                            const wrap = document.createElement("div");
                            wrap.className = "row-actions";

                            const approveBtn = document.createElement("button");
                            approveBtn.type = "button";
                            approveBtn.className = "primary";
                            approveBtn.textContent = "Approve";
                            approveBtn.onclick = () => updateStatus(row.event_id, "APPROVED");

                            const rejectBtn = document.createElement("button");
                            rejectBtn.type = "button";
                            rejectBtn.className = "danger";
                            rejectBtn.textContent = "Reject";
                            rejectBtn.onclick = () => updateStatus(row.event_id, "REJECTED");

                            const pendingBtn = document.createElement("button");
                            pendingBtn.type = "button";
                            pendingBtn.className = "warn";
                            pendingBtn.textContent = "Pending";
                            pendingBtn.onclick = () => updateStatus(row.event_id, "PENDING");

                            wrap.appendChild(approveBtn);
                            wrap.appendChild(rejectBtn);
                            wrap.appendChild(pendingBtn);
                            actions.appendChild(wrap);
                            tr.appendChild(actions);

                            rowsEl.appendChild(tr);
                        });
                    }

                    async function fetchViolations() {
                        const status = statusFilter.value;
                        const query = status ? "?status=" + encodeURIComponent(status) + "&limit=200" : "?limit=200";
                        showStatus("Loading violations...");
                        try {
                            const res = await fetch("/violations" + query);
                            if (!res.ok) throw new Error("Unable to load violations");
                            const data = await res.json();
                            renderRows(data);
                            setMetrics(data);
                            showStatus("Loaded " + data.length + " records.");
                        } catch (err) {
                            showStatus("Error: " + err.message);
                        }
                    }

                    async function updateStatus(eventId, status) {
                        showStatus("Updating " + eventId + "...");
                        try {
                            const res = await fetch("/violations/" + encodeURIComponent(eventId) + "/status", {
                                method: "PATCH",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ status, review_note: "updated from web panel" }),
                            });
                            if (!res.ok) {
                                const text = await res.text();
                                throw new Error(text || "Failed to update status");
                            }
                            await fetchViolations();
                        } catch (err) {
                            showStatus("Update failed: " + err.message);
                        }
                    }

                    createForm.addEventListener("submit", async (e) => {
                        e.preventDefault();
                        const now = Date.now();
                        const eventId = document.getElementById("eventId").value || "web-" + now;
                        const payload = {
                            event_id: eventId,
                            violation_type: "LITTERING_CANDIDATE",
                            vehicle_track_id: Number(document.getElementById("trackId").value || 1),
                            plate_text: document.getElementById("plateText").value || "UNKNOWN",
                            plate_confidence: 0.0,
                            detection_confidence: Number(document.getElementById("detConf").value || 0.8),
                            timestamp_ms: now,
                            camera_id: "cam-web",
                            source_video: document.getElementById("sourceVideo").value || "demo.mp4",
                            image_path: document.getElementById("imagePath").value || "/tmp/sample.jpg",
                            clip_path: "",
                            metadata_json: { created_from: "web-panel" },
                        };
                        showStatus("Creating violation...");
                        try {
                            const res = await fetch("/violations", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify(payload),
                            });
                            if (!res.ok) {
                                const text = await res.text();
                                throw new Error(text || "Failed to create violation");
                            }
                            createForm.reset();
                            document.getElementById("trackId").value = "1";
                            document.getElementById("detConf").value = "0.88";
                            document.getElementById("plateText").value = "UNKNOWN";
                            document.getElementById("sourceVideo").value = "demo.mp4";
                            document.getElementById("imagePath").value = "/tmp/sample.jpg";
                            await fetchViolations();
                            showStatus("Violation created successfully.");
                        } catch (err) {
                            showStatus("Create failed: " + err.message);
                        }
                    });

                    refreshBtn.addEventListener("click", fetchViolations);
                    statusFilter.addEventListener("change", fetchViolations);
                    fetchViolations();
                </script>
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
