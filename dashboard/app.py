from __future__ import annotations

from pathlib import Path

import requests
import streamlit as st


st.set_page_config(page_title="Littering Review Console", layout="wide")


def fetch_violations(api_url: str, status_filter: str):
    params = {}
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


st.title("Vehicle Littering Candidate Review")
st.caption("Human review is required before any enforcement action.")

with st.sidebar:
    st.subheader("Controls")
    api_url = st.text_input("API URL", value="http://127.0.0.1:8000")
    status_filter = st.selectbox("Filter status", options=["ALL", "PENDING", "APPROVED", "REJECTED"], index=1)
    refresh = st.button("Refresh")

if refresh:
    st.rerun()

try:
    events = fetch_violations(api_url, status_filter)
except Exception as exc:
    st.error(f"Failed to load violations: {exc}")
    st.stop()

st.write(f"Loaded {len(events)} events")

for idx, event in enumerate(events, start=1):
    event_id = event["event_id"]
    title = f"{idx}. {event_id} | {event['status']} | plate: {event.get('plate_text', '') or 'UNKNOWN'}"

    with st.expander(title, expanded=(idx <= 3)):
        col1, col2 = st.columns([2, 3])

        with col1:
            st.write("Detection")
            st.write(f"Confidence: {event['detection_confidence']:.2f}")
            st.write(f"Track ID: {event['vehicle_track_id']}")
            st.write(f"Timestamp (ms): {event['timestamp_ms']}")
            st.write(f"Camera: {event['camera_id']}")
            st.write(f"Source: {event['source_video']}")

            note_key = f"note_{event_id}"
            note = st.text_area("Review note", value=event.get("review_note", ""), key=note_key)

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Set Pending", key=f"pending_{event_id}"):
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

        with col2:
            image_path = Path(event["image_path"])
            clip_path = Path(event.get("clip_path", ""))

            if image_path.exists():
                st.image(str(image_path), caption="Evidence frame", use_column_width=True)
            else:
                st.warning(f"Image missing: {image_path}")

            if clip_path and clip_path.exists():
                st.video(str(clip_path))
            else:
                st.info("No clip available for this event.")
