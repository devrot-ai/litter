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
    return parser.parse_args()


def main():
    args = parse_args()
    config = InferenceConfig()
    pipeline = LitteringPipeline(config=config, api_url=args.api_url, camera_id=args.camera_id)
    summary = pipeline.process_video(args.video)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
