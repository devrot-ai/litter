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
    last_outward_delta: float = 0.0
    last_event_frame: int = -1_000_000


class LitterHeuristicEngine:
    def __init__(self, config: InferenceConfig) -> None:
        self.config = config
        self.prev_gray = None
        self.states: Dict[int, TrackState] = defaultdict(TrackState)
        self.litter_labels = set(config.litter_labels)
        self.non_litter_labels = set(config.non_litter_labels)

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

        model_blobs = [b for b in blobs if b.get("source") == "model"]
        candidates += self._direct_detection(
            frame_index, timestamp_ms, vehicles, model_blobs
        )

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
                state.last_blob_center = None
                state.outward_steps = max(0, state.outward_steps - 1)
                state.last_outward_delta = 0.0
                continue

            blob_center = selected["center"]
            blob_bbox = selected["bbox"]
            blob_conf = float(selected["confidence"])
            blob_label = str(selected.get("label", "")).strip().lower()
            blob_source = selected.get("source", "motion")
            attach_distance_px = float(selected.get("attach_distance_px", self.config.attach_distance_px))

            if state.last_blob_center is not None:
                prev_dist = distance(state.last_blob_center, v_center)
                curr_dist = distance(blob_center, v_center)
                delta = curr_dist - prev_dist
                state.last_outward_delta = max(0.0, delta)
                if delta >= self.config.outward_step_px:
                    state.outward_steps += 1
                else:
                    state.outward_steps = max(0, state.outward_steps - 1)
            else:
                state.outward_steps = 0
                state.last_outward_delta = 0.0

            state.last_blob_center = blob_center

            if frame_index - state.last_event_frame < self.config.event_cooldown_frames:
                continue

            effective_confirm = self.config.confirm_steps
            if blob_source == "model" and blob_label in self.litter_labels:
                effective_confirm = max(1, self.config.confirm_steps)

            if state.outward_steps >= effective_confirm:
                base_score = self._score_candidate(
                    blob_conf=blob_conf,
                    outward_steps=state.outward_steps,
                    outward_delta=state.last_outward_delta,
                    attach_distance_px=attach_distance_px,
                    is_model_detection=(blob_source == "model"),
                )
                verdict, confidence, verdict_reason = self._decide_verdict(
                    base_score=base_score,
                    blob_label=blob_label,
                    blob_conf=blob_conf,
                )
                state.last_event_frame = frame_index
                state.outward_steps = 0
                candidates.append(
                    LitterCandidate(
                        frame_index=frame_index,
                        vehicle_track_id=vehicle.track_id,
                        vehicle_bbox=vehicle.bbox,
                        object_bbox=blob_bbox,
                        confidence=confidence,
                        reason=f"motion_outward_from_vehicle|{verdict_reason}",
                        timestamp_ms=timestamp_ms,
                        verdict=verdict,
                        object_label=blob_label,
                        object_confidence=blob_conf,
                    )
                )

        self.prev_gray = gray
        return candidates

    def _direct_detection(
        self,
        frame_index: int,
        timestamp_ms: int,
        vehicles: List[TrackedVehicle],
        model_blobs: List[dict],
    ) -> List[LitterCandidate]:
        candidates: List[LitterCandidate] = []

        for vehicle in vehicles:
            state = self.states[vehicle.track_id]

            if frame_index - state.last_event_frame < self.config.event_cooldown_frames:
                continue

            if not self._is_vehicle_moving(state.vehicle_centers):
                continue

            for blob in model_blobs:
                label = str(blob.get("label", "")).strip().lower()
                conf = float(blob.get("confidence", 0.0))

                if label not in self.litter_labels:
                    continue
                if conf < max(self.config.min_label_confidence, 0.30):
                    continue

                d = distance_point_to_bbox(blob["center"], vehicle.bbox)
                if d > self.config.attach_distance_px:
                    continue

                proximity_signal = max(0.0, 1.0 - d / max(float(self.config.attach_distance_px), 1.0))
                score = min(0.98, 0.50 + 0.28 * conf + 0.12 * proximity_signal + 0.08)

                verdict, final_conf, reason = self._decide_verdict(
                    base_score=score,
                    blob_label=label,
                    blob_conf=conf,
                )

                state.last_event_frame = frame_index

                candidates.append(
                    LitterCandidate(
                        frame_index=frame_index,
                        vehicle_track_id=vehicle.track_id,
                        vehicle_bbox=vehicle.bbox,
                        object_bbox=blob["bbox"],
                        confidence=final_conf,
                        reason=f"direct_model_detection|{reason}",
                        timestamp_ms=timestamp_ms,
                        verdict=verdict,
                        object_label=label,
                        object_confidence=conf,
                    )
                )
                break

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
                    "label": str(det.get("label", "")).strip().lower(),
                    "source": "model",
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
                    "label": "",
                    "source": "motion",
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
            adjust = 0 if blob.get("source") == "model" else 5
            effective = d + adjust
            if effective < best_score:
                best_score = effective
                best = {
                    **blob,
                    "attach_distance_px": d,
                }

        return best

    def _score_candidate(
        self,
        blob_conf: float,
        outward_steps: int,
        outward_delta: float,
        attach_distance_px: float,
        is_model_detection: bool = False,
    ) -> float:
        steps_goal = max(self.config.confirm_steps, 1)
        steps_signal = min(1.0, outward_steps / steps_goal)
        outward_signal = min(1.0, outward_delta / max(float(self.config.outward_step_px), 1.0))
        attach_signal = max(0.0, 1.0 - (attach_distance_px / max(float(self.config.attach_distance_px), 1.0)))
        object_signal = max(0.0, min(blob_conf, 1.0))

        if is_model_detection:
            score = (
                0.42
                + 0.18 * steps_signal
                + 0.12 * outward_signal
                + 0.08 * attach_signal
                + 0.20 * object_signal
            )
        else:
            score = (
                0.38
                + 0.24 * steps_signal
                + 0.18 * outward_signal
                + 0.10 * attach_signal
                + 0.10 * object_signal
            )
        return max(0.0, min(0.98, score))

    def _decide_verdict(self, base_score: float, blob_label: str, blob_conf: float) -> tuple[str, float, str]:
        adjusted = base_score
        reason_tokens: List[str] = []
        label = blob_label.strip().lower()
        has_strong_label = blob_conf >= self.config.min_label_confidence

        if label:
            reason_tokens.append(f"label={label}")

        if label and has_strong_label and label in self.litter_labels:
            adjusted = min(0.98, adjusted + 0.12)
            reason_tokens.append("label_support=litter")
        elif label and has_strong_label and label in self.non_litter_labels:
            adjusted = max(0.0, adjusted - 0.24)
            reason_tokens.append("label_support=non_litter")

        min_litter_conf = max(self.config.min_litter_confidence, self.config.uncertain_confidence_floor + 0.01)
        uncertain_floor = min(self.config.uncertain_confidence_floor, min_litter_conf - 0.01)

        if adjusted >= min_litter_conf:
            verdict = "LITTER"
        elif adjusted >= uncertain_floor:
            verdict = "UNCERTAIN"
        else:
            verdict = "NOT_LITTER"

        reason_tokens.append(f"score={adjusted:.2f}")
        return verdict, adjusted, ",".join(reason_tokens)

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

