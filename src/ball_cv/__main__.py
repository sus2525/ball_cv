from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ball_cv.config import Settings
from ball_cv.doctor import run_doctor
from ball_cv.video_tracking import load_yolo_detector, run_video_tracking


def _unit_interval(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("value must be between 0 and 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ball-cv")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Verify the Python/CV runtime.")
    track = subparsers.add_parser(
        "track-video", help="Detect and track one ball through a video."
    )
    track.add_argument("video", type=Path, help="Input video path visible inside the container.")
    track.add_argument(
        "--model",
        type=Path,
        default=Settings().model_path,
        help="YOLO weights path (default: BALL_CV_MODEL_PATH).",
    )
    track.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: <artifacts-dir>/<video-name>).",
    )
    track.add_argument("--device", default=Settings().device, help="Inference device, default cpu.")
    track.add_argument("--class-id", type=int, help="Keep only this model class ID.")
    track.add_argument("--confidence", type=_unit_interval, default=0.25)
    track.add_argument("--max-distance", type=float, default=120.0)
    track.add_argument("--max-gap", type=int, default=5)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "doctor":
        return run_doctor()

    if args.command == "track-video":
        settings = Settings()
        output_dir = args.output_dir or settings.artifacts_dir / args.video.stem
        try:
            detector = load_yolo_detector(
                args.model,
                device=args.device,
                confidence=args.confidence,
                class_id=args.class_id,
            )
            jsonl_path, overlay_path, frames = run_video_tracking(
                args.video,
                output_dir,
                detector,
                max_distance=args.max_distance,
                max_gap=args.max_gap,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"error={exc}", file=sys.stderr)
            return 2
        print(f"frames_processed={frames}")
        print(f"tracking_jsonl={jsonl_path}")
        print(f"overlay_video={overlay_path}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
