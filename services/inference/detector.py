from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from ultralytics import YOLO

from .types import TrackedVehicle


VEHICLE_LABELS = {"car", "bus", "truck", "motorcycle", "bicycle"}


class VehicleTracker:
    def __init__(self, model_path: str) -> None:
        self.model = YOLO(model_path)

    def track(self, frame) -> List[TrackedVehicle]:
        results = self.model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)
        result = results[0]

        if result.boxes is None or result.boxes.id is None:
            return []

        tracked: List[TrackedVehicle] = []
        names = result.names
        xyxy = result.boxes.xyxy.cpu().numpy()
        ids = result.boxes.id.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy()

        for bbox, track_id, conf, cls_idx in zip(xyxy, ids, confs, classes):
            label = names[int(cls_idx)]
            if label not in VEHICLE_LABELS:
                continue

            x1, y1, x2, y2 = [int(v) for v in bbox]
            tracked.append(
                TrackedVehicle(
                    track_id=int(track_id),
                    label=label,
                    confidence=float(conf),
                    bbox=(x1, y1, x2, y2),
                )
            )

        return tracked


class LitterObjectDetector:
    def __init__(self, model_path: Optional[str]) -> None:
        self.model = None
        if model_path and Path(model_path).exists():
            self.model = YOLO(model_path)

    def detect(self, frame):
        if self.model is None:
            return []

        results = self.model(frame, verbose=False)
        result = results[0]

        if result.boxes is None:
            return []

        names = result.names
        detections = []
        for box, conf, cls_idx in zip(
            result.boxes.xyxy.cpu().numpy(),
            result.boxes.conf.cpu().numpy(),
            result.boxes.cls.cpu().numpy(),
        ):
            x1, y1, x2, y2 = [int(v) for v in box]
            detections.append(
                {
                    "bbox": (x1, y1, x2, y2),
                    "confidence": float(conf),
                    "label": names[int(cls_idx)],
                }
            )

        return detections
