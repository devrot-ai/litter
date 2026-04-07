from __future__ import annotations

import re
from typing import Optional

import easyocr

from .types import PlateRead


PLATE_PATTERN = re.compile(r"[^A-Z0-9]")


class PlateReader:
    def __init__(self) -> None:
        self.reader = easyocr.Reader(["en"], gpu=False)

    def read_plate(self, frame, bbox) -> Optional[PlateRead]:
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]

        mx = int((x2 - x1) * 0.15)
        my = int((y2 - y1) * 0.15)

        x1 = max(0, x1 - mx)
        y1 = max(0, y1 - my)
        x2 = min(w, x2 + mx)
        y2 = min(h, y2 + my)

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None

        results = self.reader.readtext(crop, detail=1)
        if not results:
            return None

        best = max(results, key=lambda item: float(item[2]))
        raw_text = str(best[1]).upper()
        clean_text = PLATE_PATTERN.sub("", raw_text)
        if len(clean_text) < 5:
            return None

        return PlateRead(text=clean_text, confidence=float(best[2]))
