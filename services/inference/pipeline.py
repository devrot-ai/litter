from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Deque, Dict, List, Tuple
from urllib import error, request

import cv2

from .config import InferenceConfig
from .detector import LitterObjectDetector, VehicleTracker
from .evidence import EvidenceWriter
from .litter_logic import LitterHeuristicEngine
from .plate_reader import PlateReader
from .types import LitterCandidate


@dataclass
class PendingEvent:
    candidate: LitterCandidate
    finalize_at: int


class LitteringPipeline:
    def __init__(self, config: InferenceConfig, api_url: str | None = None, camera_id: str = "cam-01") -> None:
        self.config = config
        self.api_url = api_url.rstrip("/") if api_url else ""
        self.camera_id = camera_id

        self.vehicle_tracker = VehicleTracker(config.vehicle_model)
        self.litter_detector = LitterObjectDetector(config.litter_model)
        self.plate_reader = PlateReader()
        self.logic = LitterHeuristicEngine(config)
        self.evidence = EvidenceWriter(config.evidence_dir, config.clips_dir)

    def process_video(
        self,
        video_path: str,
        max_seconds: float | None = None,
        max_frames: int | None = None,
    ) -> Dict[str, int]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25.0

        frame_index = 0
        pending: List[PendingEvent] = []
        frame_buffer: Deque[Tuple[int, object]] = deque(
            maxlen=self.config.clip_pre_frames + self.config.clip_post_frames + 30
        )

        processed_frames = 0
        emitted_events = 0
        start_time = time.monotonic()

        while True:
            if max_seconds is not None and (time.monotonic() - start_time) >= max_seconds:
                break
            if max_frames is not None and processed_frames >= max_frames:
                break
            ok, frame = cap.read()
            if not ok:
                break

            timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            frame_buffer.append((frame_index, frame.copy()))

            if frame_index % self.config.frame_skip == 0:
                vehicles = self.vehicle_tracker.track(frame)
                model_objects = self.litter_detector.detect(frame)
                candidates = self.logic.update(frame, frame_index, timestamp_ms, vehicles, model_objects)

                for candidate in candidates:
                    plate = self.plate_reader.read_plate(frame, candidate.vehicle_bbox)
                    if plate:
                        candidate.plate_text = plate.text
                        candidate.plate_confidence = plate.confidence

                    pending.append(
                        PendingEvent(
                            candidate=candidate,
                            finalize_at=frame_index + self.config.clip_post_frames,
                        )
                    )

            finalized = [evt for evt in pending if frame_index >= evt.finalize_at]
            if finalized:
                for evt in finalized:
                    clip_frames = self._extract_clip(frame_buffer, evt.candidate.frame_index)
                    metadata = self.evidence.save_event(
                        evt.candidate,
                        clip_frames,
                        fps,
                        source_video=video_path,
                    )
                    self._publish_violation(metadata)
                    emitted_events += 1

                pending = [evt for evt in pending if frame_index < evt.finalize_at]

            processed_frames += 1
            frame_index += 1

        for evt in pending:
            clip_frames = self._extract_clip(frame_buffer, evt.candidate.frame_index)
            metadata = self.evidence.save_event(
                evt.candidate,
                clip_frames,
                fps,
                source_video=video_path,
            )
            self._publish_violation(metadata)
            emitted_events += 1

        cap.release()

        return {
            "processed_frames": processed_frames,
            "emitted_events": emitted_events,
        }

    def _extract_clip(self, frame_buffer: Deque[Tuple[int, object]], event_index: int):
        start = event_index - self.config.clip_pre_frames
        end = event_index + self.config.clip_post_frames
        return [item for item in frame_buffer if start <= item[0] <= end]

    def _publish_violation(self, metadata: dict) -> None:
        if not self.api_url:
            return

        payload = {
            "event_id": metadata["event_id"],
            "violation_type": metadata["violation_type"],
            "vehicle_track_id": metadata["vehicle_track_id"],
            "plate_text": metadata.get("plate_text", ""),
            "plate_confidence": metadata.get("plate_confidence", 0.0),
            "detection_confidence": metadata["detection_confidence"],
            "timestamp_ms": metadata["timestamp_ms"],
            "camera_id": self.camera_id,
            "source_video": metadata["source_video"],
            "image_path": metadata["image_path"],
            "clip_path": metadata["clip_path"],
            "metadata_json": metadata,
        }

        target = f"{self.api_url}/violations"
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            target,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=8) as resp:
                resp.read()
        except error.URLError:
            pass
