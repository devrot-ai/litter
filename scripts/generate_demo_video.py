from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def draw_vehicle(frame, x, y, color=(20, 20, 20)):
    cv2.rectangle(frame, (x, y), (x + 140, y + 50), color, -1)
    cv2.rectangle(frame, (x + 25, y - 20), (x + 110, y + 10), color, -1)
    cv2.circle(frame, (x + 25, y + 55), 12, (0, 0, 0), -1)
    cv2.circle(frame, (x + 115, y + 55), 12, (0, 0, 0), -1)


def main() -> None:
    out_path = Path("data/raw/traffic.mp4")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    width, height = 1280, 720
    fps = 25
    seconds = 20
    frames = fps * seconds

    writer = cv2.VideoWriter(
        str(out_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    litter_pos = None
    litter_vel = None

    for i in range(frames):
        frame = np.full((height, width, 3), (150, 190, 220), dtype=np.uint8)

        cv2.rectangle(frame, (0, 430), (width, height), (70, 70, 70), -1)
        cv2.line(frame, (0, 550), (width, 550), (220, 220, 220), 3)

        car_x = int(120 + i * 4.0)
        bike_x = int(900 - i * 3.5)

        draw_vehicle(frame, car_x, 470, color=(25, 25, 25))
        cv2.rectangle(frame, (bike_x, 500), (bike_x + 80, 530), (40, 40, 40), -1)
        cv2.circle(frame, (bike_x + 15, 540), 10, (0, 0, 0), -1)
        cv2.circle(frame, (bike_x + 65, 540), 10, (0, 0, 0), -1)

        if i == 180:
            litter_pos = [car_x + 120, 485]
            litter_vel = [6.0, 1.8]

        if litter_pos is not None and litter_vel is not None:
            litter_pos[0] += litter_vel[0]
            litter_pos[1] += litter_vel[1]
            litter_vel[0] *= 0.98
            litter_vel[1] += 0.12

            lx, ly = int(litter_pos[0]), int(litter_pos[1])
            if 0 < lx < width and 0 < ly < height:
                cv2.rectangle(frame, (lx, ly), (lx + 10, ly + 8), (30, 200, 30), -1)

        cv2.putText(
            frame,
            "Demo traffic clip for MVP integration tests",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (10, 10, 10),
            2,
            cv2.LINE_AA,
        )

        writer.write(frame)

    writer.release()
    print(f"Generated {out_path}")


if __name__ == "__main__":
    main()
