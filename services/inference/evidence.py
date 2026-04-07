from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple
from uuid import uuid4

import cv2

from .types import LitterCandidate


class EvidenceWriter:
    def __init__(self, evidence_dir: Path, clips_dir: Path) -> None:
        self.evidence_dir = evidence_dir
        self.clips_dir = clips_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.clips_dir.mkdir(parents=True, exist_ok=True)

    def save_event(
        self,
        candidate: LitterCandidate,
        clip_frames: List[Tuple[int, object]],
        fps: float,
        source_video: str,
    ) -> dict:
        event_id = uuid4().hex
        image_path = self.evidence_dir / f"{event_id}.jpg"
        clip_path = self.clips_dir / f"{event_id}.mp4"
        metadata_path = self.evidence_dir / f"{event_id}.json"

        event_frame = self._pick_event_frame(candidate.frame_index, clip_frames)
        cv2.imwrite(str(image_path), event_frame)

        clip_written = self._write_clip(clip_frames, clip_path, fps)

        metadata = {
            "event_id": event_id,
            "violation_type": "LITTERING_CANDIDATE",
            "frame_index": candidate.frame_index,
            "timestamp_ms": candidate.timestamp_ms,
            "vehicle_track_id": candidate.vehicle_track_id,
            "vehicle_bbox": candidate.vehicle_bbox,
            "object_bbox": candidate.object_bbox,
            "plate_text": candidate.plate_text or "",
            "plate_confidence": candidate.plate_confidence,
            "detection_confidence": candidate.confidence,
            "reason": candidate.reason,
            "source_video": source_video,
            "image_path": str(image_path),
            "clip_path": str(clip_path) if clip_written else "",
        }

        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return metadata

    def _pick_event_frame(self, event_index: int, clip_frames: List[Tuple[int, object]]):
        if not clip_frames:
            raise ValueError("clip_frames cannot be empty")

        best_idx = min(range(len(clip_frames)), key=lambda idx: abs(clip_frames[idx][0] - event_index))
        return clip_frames[best_idx][1]

    def _write_clip(self, clip_frames: List[Tuple[int, object]], clip_path: Path, fps: float) -> bool:
        if not clip_frames:
            return False

        sample = clip_frames[0][1]
        h, w = sample.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(clip_path), fourcc, max(fps, 1.0), (w, h))

        try:
            for _, frame in clip_frames:
                writer.write(frame)
        finally:
            writer.release()

        return True
