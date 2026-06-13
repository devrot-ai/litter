from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from uuid import uuid4

import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.inference.config import InferenceConfig
from services.inference.pipeline import LitteringPipeline


DEFAULT_API_URL = "http://127.0.0.1:8000"
UPLOAD_DIR = Path("data/raw/uploads")
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


st.set_page_config(page_title="Litter Cam", layout="wide")

st.markdown(
    """
<style>
@import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Source+Sans+3:wght@400;600&display=swap");
:root {
    --bg: #f6f2ea;
    --panel: #ffffff;
    --ink: #111111;
    --muted: #5a5a5a;
    --accent: #0b5d4f;
    --accent-soft: #d6efe7;
}
html, body, [class*="css"] {
    font-family: "Source Sans 3", sans-serif;
    color: var(--ink);
}
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: "Space Grotesk", sans-serif;
    letter-spacing: 0.4px;
}
div[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 15% 20%, #ffffff 0%, var(--bg) 55%, #ece4d7 100%);
}
div[data-testid="stMetric"] {
    background: var(--panel);
    border: 1px solid #e5ddcf;
    border-radius: 12px;
    padding: 12px;
}
</style>
""",
    unsafe_allow_html=True,
)


def check_api(api_url: str) -> tuple[bool, str]:
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        response.raise_for_status()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def fetch_violations(api_url: str, status_filter: str, limit: int):
    params = {"limit": limit}
    if status_filter != "ALL":
        params["status"] = status_filter

    response = requests.get(f"{api_url}/violations", params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def update_status(api_url: str, event_id: str, status: str, note: str):
    response = requests.patch(
        f"{api_url}/violations/{event_id}/status",
        json={"status": status, "review_note": note},
        timeout=15,
    )
    response.raise_for_status()


def save_uploaded_file(uploaded) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(uploaded.name).suffix.lower()
    if suffix not in VIDEO_SUFFIXES:
        suffix = ".mp4"
    filename = f"upload_{datetime.utcnow():%Y%m%d_%H%M%S}_{uuid4().hex[:6]}{suffix}"
    target = UPLOAD_DIR / filename
    target.write_bytes(uploaded.getbuffer())
    return target


def run_pipeline(
    source: str,
    api_url: str,
    camera_id: str,
    max_seconds: float | None = None,
    min_litter_confidence: float | None = None,
    uncertain_confidence_floor: float | None = None,
    emit_uncertain_events: bool | None = None,
    confirm_steps: int | None = None,
    min_object_confidence: float | None = None,
) -> dict:
    config = InferenceConfig()
    if min_litter_confidence is not None:
        config.min_litter_confidence = min_litter_confidence
    if uncertain_confidence_floor is not None:
        cap = max(0.0, config.min_litter_confidence - 0.01)
        config.uncertain_confidence_floor = min(uncertain_confidence_floor, cap)
    if emit_uncertain_events is not None:
        config.emit_uncertain_events = emit_uncertain_events
    if confirm_steps is not None:
        config.confirm_steps = max(1, int(confirm_steps))
    if min_object_confidence is not None:
        config.min_object_confidence = min(max(0.0, min_object_confidence), 1.0)

    pipeline = LitteringPipeline(config=config, api_url=api_url, camera_id=camera_id)
    return pipeline.process_video(source, max_seconds=max_seconds)


def render_event(event: dict, api_url: str) -> None:
    event_id = event["event_id"]
    status = event["status"]
    plate_text = event.get("plate_text") or "UNKNOWN"
    metadata = event.get("metadata_json") or {}
    verdict = str(metadata.get("litter_verdict", "UNCERTAIN")).upper()
    object_label = metadata.get("object_label") or "unknown"
    object_confidence = float(metadata.get("object_confidence", 0.0) or 0.0)

    st.subheader(f"{event_id} | {status} | plate: {plate_text}")
    left, right = st.columns([2, 3])

    with left:
        if verdict == "LITTER":
            st.success("AI verdict: LITTER")
        elif verdict == "UNCERTAIN":
            st.warning("AI verdict: UNCERTAIN")
        else:
            st.info("AI verdict: NOT_LITTER")

        st.write(f"Confidence: {event['detection_confidence']:.2f}")
        st.write(f"Detected object: {object_label} ({object_confidence:.2f})")
        st.write(f"Track ID: {event['vehicle_track_id']}")
        st.write(f"Timestamp (ms): {event['timestamp_ms']}")
        st.write(f"Camera: {event['camera_id']}")
        st.write(f"Source: {event['source_video']}")

        note_key = f"note_{event_id}"
        note = st.text_area("Review note", value=event.get("review_note", ""), key=note_key)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Pending", key=f"pending_{event_id}"):
                update_status(api_url, event_id, "PENDING", note)
                st.rerun()
        with c2:
            if st.button("Approve", key=f"approve_{event_id}"):
                update_status(api_url, event_id, "APPROVED", note)
                st.rerun()
        with c3:
            if st.button("Reject", key=f"reject_{event_id}"):
                update_status(api_url, event_id, "REJECTED", note)
                st.rerun()

    with right:
        image_value = event.get("image_path", "")
        clip_value = event.get("clip_path", "")
        image_path = Path(image_value) if image_value else None
        clip_path = Path(clip_value) if clip_value else None

        if image_path and image_path.exists():
            st.image(str(image_path), caption="Evidence frame", use_container_width=True)
        else:
            st.info("Evidence frame not found.")

        if clip_path and clip_path.exists():
            st.video(str(clip_path))
        else:
            st.info("No clip available for this event.")

    st.divider()


st.title("Litter Cam")
st.caption("Upload footage or connect a stream. Review candidates with quick decisions.")

setup_col1, setup_col2, setup_col3 = st.columns([2, 1, 1])
api_url = setup_col1.text_input("API URL", value=DEFAULT_API_URL)
camera_id = setup_col2.text_input("Camera ID", value="cam-01")

api_ok, api_error = check_api(api_url)
if api_ok:
    setup_col3.success("API connected")
else:
    setup_col3.error("API offline")
    st.caption(f"Details: {api_error}")

tabs = st.tabs(["Ingest", "Review"])

with tabs[0]:
    st.subheader("Ingest")
    st.write("Pick a recorded clip or connect a live stream.")
    mode = st.radio("Input type", options=["Recorded video", "Live stream"], horizontal=True)

    ingest_defaults = InferenceConfig()
    with st.expander("AI litter verdict settings", expanded=True):
        st.caption("Tune how strict the AI should be when deciding if a thrown object is litter.")

        tune_c1, tune_c2 = st.columns(2)
        min_litter_confidence = tune_c1.slider(
            "Minimum confidence to mark as litter",
            min_value=0.50,
            max_value=0.95,
            value=float(ingest_defaults.min_litter_confidence),
            step=0.01,
        )

        max_uncertain_floor = max(0.31, min_litter_confidence - 0.01)
        uncertain_default = min(float(ingest_defaults.uncertain_confidence_floor), max_uncertain_floor)
        uncertain_confidence_floor = tune_c2.slider(
            "Uncertain floor (below this = not litter)",
            min_value=0.30,
            max_value=float(max_uncertain_floor),
            value=float(uncertain_default),
            step=0.01,
        )

        tune_c3, tune_c4, tune_c5 = st.columns(3)
        confirm_steps = tune_c3.slider(
            "Throw confirmation steps",
            min_value=1,
            max_value=4,
            value=int(ingest_defaults.confirm_steps),
            step=1,
        )
        min_object_confidence = tune_c4.slider(
            "Minimum object-model confidence",
            min_value=0.05,
            max_value=0.95,
            value=float(ingest_defaults.min_object_confidence),
            step=0.01,
        )
        emit_uncertain_events = tune_c5.checkbox(
            "Save uncertain events for review",
            value=bool(ingest_defaults.emit_uncertain_events),
        )

    if mode == "Recorded video":
        uploaded = st.file_uploader("Upload a video file", type=[s.lstrip(".") for s in VIDEO_SUFFIXES])
        if uploaded:
            size_mb = uploaded.size / (1024 * 1024)
            st.write(f"Selected: {uploaded.name} ({size_mb:.1f} MB)")

        run_clip = st.button("Process recorded video", disabled=not uploaded or not api_ok)
        if run_clip:
            try:
                video_path = save_uploaded_file(uploaded)
                with st.spinner("Running inference on the uploaded clip..."):
                    summary = run_pipeline(
                        str(video_path),
                        api_url,
                        camera_id,
                        min_litter_confidence=min_litter_confidence,
                        uncertain_confidence_floor=uncertain_confidence_floor,
                        emit_uncertain_events=emit_uncertain_events,
                        confirm_steps=confirm_steps,
                        min_object_confidence=min_object_confidence,
                    )
                st.session_state["last_summary"] = summary
                st.success(
                    "Done. Processed {processed_frames} frames and emitted {emitted_events} events.".format(
                        **summary
                    )
                )
                st.info("Open the Review tab to see new events.")
            except Exception as exc:
                st.error(f"Processing failed: {exc}")
    else:
        stream_url = st.text_input(
            "Live stream URL",
            placeholder="rtsp://user:pass@camera/stream",
        )
        run_seconds = st.slider("Run for seconds", min_value=10, max_value=300, value=60, step=10)

        run_stream = st.button("Process live stream", disabled=not stream_url or not api_ok)
        if run_stream:
            try:
                with st.spinner("Running inference on the live stream..."):
                    summary = run_pipeline(
                        stream_url,
                        api_url,
                        camera_id,
                        max_seconds=float(run_seconds),
                        min_litter_confidence=min_litter_confidence,
                        uncertain_confidence_floor=uncertain_confidence_floor,
                        emit_uncertain_events=emit_uncertain_events,
                        confirm_steps=confirm_steps,
                        min_object_confidence=min_object_confidence,
                    )
                st.session_state["last_summary"] = summary
                st.success(
                    "Done. Processed {processed_frames} frames and emitted {emitted_events} events.".format(
                        **summary
                    )
                )
                st.info("Open the Review tab to see new events.")
            except Exception as exc:
                st.error(f"Processing failed: {exc}")

    summary = st.session_state.get("last_summary")
    if summary:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Frames processed", summary.get("processed_frames", 0))
        m2.metric("Events emitted", summary.get("emitted_events", 0))
        m3.metric("Confirmed litter", summary.get("confirmed_litter_events", 0))
        m4.metric("Uncertain", summary.get("uncertain_events", 0))
        st.caption(
            "Filtered out: {discarded_not_litter} clear non-litter events and {discarded_uncertain} uncertain events."
            .format(**summary)
        )

with tabs[1]:
    st.subheader("Review")
    st.write("Approve or reject candidate events. Add a note when needed.")

    status_filter = st.selectbox("Filter", options=["PENDING", "ALL", "APPROVED", "REJECTED"], index=0)
    limit = st.slider("Max events", min_value=10, max_value=200, value=50, step=10)
    if st.button("Refresh events"):
        st.rerun()

    if not api_ok:
        st.warning("API is not reachable. Start the API to load events.")
    else:
        try:
            events = fetch_violations(api_url, status_filter, limit)
        except Exception as exc:
            st.error(f"Failed to load violations: {exc}")
            events = []

        if not events:
            st.info("No events yet. Use the Ingest tab to add footage.")
        else:
            st.write(f"Loaded {len(events)} events")
            for event in events:
                render_event(event, api_url)
