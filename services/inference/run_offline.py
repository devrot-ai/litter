from __future__ import annotations

import argparse
import json

from .config import InferenceConfig
from .pipeline import LitteringPipeline


def parse_args():
    parser = argparse.ArgumentParser(description="Run littering MVP pipeline on a recorded video")
    parser.add_argument("--video", required=True, help="Path to input video")
    parser.add_argument("--api-url", default="", help="FastAPI endpoint base URL")
    parser.add_argument("--camera-id", default="cam-01", help="Camera identifier")
    parser.add_argument("--min-litter-confidence", type=float, default=None)
    parser.add_argument("--uncertain-floor", type=float, default=None)
    parser.add_argument("--confirm-steps", type=int, default=None)
    parser.add_argument("--min-object-confidence", type=float, default=None)
    parser.add_argument("--keep-uncertain", action="store_true")
    parser.add_argument("--drop-uncertain", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.keep_uncertain and args.drop_uncertain:
        raise ValueError("Use either --keep-uncertain or --drop-uncertain, not both.")

    config = InferenceConfig()
    if args.min_litter_confidence is not None:
        config.min_litter_confidence = args.min_litter_confidence
    if args.uncertain_floor is not None:
        config.uncertain_confidence_floor = max(
            0.0,
            min(args.uncertain_floor, config.min_litter_confidence - 0.01),
        )
    if args.confirm_steps is not None:
        config.confirm_steps = max(1, args.confirm_steps)
    if args.min_object_confidence is not None:
        config.min_object_confidence = min(max(0.0, args.min_object_confidence), 1.0)
    if args.keep_uncertain:
        config.emit_uncertain_events = True
    if args.drop_uncertain:
        config.emit_uncertain_events = False

    pipeline = LitteringPipeline(config=config, api_url=args.api_url, camera_id=args.camera_id)
    summary = pipeline.process_video(args.video)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
