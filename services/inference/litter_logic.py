from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from math import hypot
from typing import Deque, Dict, List, Tuple

import cv2

from .config import InferenceConfig
from .types import LitterCandidate, TrackedVehicle


Point = Tuple[int, int]
BBox = Tuple[int, int, int, int]


@dataclass
class TrackState:
    vehicle_centers: Deque[Point] = field(default_factory=lambda: deque(maxlen=4))
    last_blob_center: Point | None = None
    outward_steps: int = 0
    last_event_frame: int = -1_000_000


class LitterHeuristicEngine:
    def __init__(self, config: InferenceConfig) -> None:
        self.config = config
        self.prev_gray = None
        self.states: Dict[int, TrackState] = defaultdict(TrackState)

    def update(
        self,
        frame,
        frame_index: int,
        timestamp_ms: int,
        vehicles: List[TrackedVehicle],
        model_objects: List[dict],
    ) -> List[LitterCandidate]:
        candidates: List[LitterCandidate] = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        blobs = self._extract_blobs(gray, model_objects)

        for vehicle in vehicles:
            state = self.states[vehicle.track_id]
            v_center = center_of_bbox(vehicle.bbox)
            state.vehicle_centers.append(v_center)

            if not self._is_vehicle_moving(state.vehicle_centers):
                state.last_blob_center = None
                state.outward_steps = 0
                continue

            selected = self._nearest_blob(vehicle.bbox, blobs)
            if selected is None:
                continue

            blob_center = selected["center"]
            blob_bbox = selected["bbox"]
            blob_conf = selected["confidence"]

            if state.last_blob_center is not None:
                prev_dist = distance(state.last_blob_center, v_center)
                curr_dist = distance(blob_center, v_center)
                if curr_dist - prev_dist >= self.config.outward_step_px:
                    state.outward_steps += 1
                else:
                    state.outward_steps = max(0, state.outward_steps - 1)
            else:
                state.outward_steps = 0

            state.last_blob_center = blob_center

            if frame_index - state.last_event_frame < self.config.event_cooldown_frames:
                continue

            if state.outward_steps >= self.config.confirm_steps:
                state.last_event_frame = frame_index
                state.outward_steps = 0
                candidates.append(
                    LitterCandidate(
                        frame_index=frame_index,
                        vehicle_track_id=vehicle.track_id,
                        vehicle_bbox=vehicle.bbox,
                        object_bbox=blob_bbox,
                        confidence=min(0.95, 0.45 + 0.2 * self.config.confirm_steps + blob_conf * 0.2),
                        reason="motion_outward_from_vehicle",
                        timestamp_ms=timestamp_ms,
                    )
                )

        self.prev_gray = gray
        return candidates

    def _extract_blobs(self, gray, model_objects: List[dict]) -> List[dict]:
        blobs: List[dict] = []

        for det in model_objects:
            bbox = det.get("bbox")
            if not bbox:
                continue
            x1, y1, x2, y2 = bbox
            c = center_of_bbox((x1, y1, x2, y2))
            blobs.append(
                {
                    "center": c,
                    "bbox": (x1, y1, x2, y2),
                    "confidence": float(det.get("confidence", 0.5)),
                }
            )

        if self.prev_gray is None:
            return blobs

        diff = cv2.absdiff(self.prev_gray, gray)
        _, thresh = cv2.threshold(diff, self.config.motion_threshold, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        thresh = cv2.dilate(thresh, kernel, iterations=1)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.config.min_blob_area or area > self.config.max_blob_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            bbox = (x, y, x + w, y + h)
            blobs.append(
                {
                    "center": center_of_bbox(bbox),
                    "bbox": bbox,
                    "confidence": min(0.8, area / self.config.max_blob_area),
                }
            )

        return blobs

    def _nearest_blob(self, vehicle_bbox: BBox, blobs: List[dict]) -> dict | None:
        best = None
        best_score = float("inf")

        for blob in blobs:
            d = distance_point_to_bbox(blob["center"], vehicle_bbox)
            if d > self.config.attach_distance_px:
                continue
            if d < best_score:
                best_score = d
                best = blob

        return best

    def _is_vehicle_moving(self, centers: Deque[Point]) -> bool:
        if len(centers) < 2:
            return False

        movement = distance(centers[-1], centers[0])
        return movement >= self.config.min_vehicle_motion_px


def center_of_bbox(bbox: BBox) -> Point:
    x1, y1, x2, y2 = bbox
    return (int((x1 + x2) / 2), int((y1 + y2) / 2))


def distance(p1: Point, p2: Point) -> float:
    return hypot(p1[0] - p2[0], p1[1] - p2[1])


def distance_point_to_bbox(point: Point, bbox: BBox) -> float:
    x, y = point
    x1, y1, x2, y2 = bbox

    dx = max(x1 - x, 0, x - x2)
    dy = max(y1 - y, 0, y - y2)
    return hypot(dx, dy)
