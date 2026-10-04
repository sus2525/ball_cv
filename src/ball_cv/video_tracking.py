from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np

from ball_cv.tracking import Detection, SingleBallTracker

Detector = Callable[[np.ndarray], list[Detection]]


def load_yolo_detector(
    model_path: Path,
    device: str,
    confidence: float,
    class_id: int | None,
) -> Detector:
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Model weights not found: {model_path}. Put the weights under models/ "
            "or pass --model /models/your-model.pt."
        )

    from ultralytics import YOLO

    model = YOLO(str(model_path))

    def detect(frame: np.ndarray) -> list[Detection]:
        results = model.predict(
            source=frame,
            conf=confidence,
            device=device,
            verbose=False,
        )
        found: list[Detection] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            coordinates = boxes.xyxy.cpu().tolist()
            confidences = boxes.conf.cpu().tolist()
            class_ids = boxes.cls.cpu().tolist()
            names = result.names
            for coords, score, raw_class_id in zip(
                coordinates, confidences, class_ids, strict=True
            ):
                detected_class_id = int(raw_class_id)
                if class_id is not None and detected_class_id != class_id:
                    continue
                label = str(names[detected_class_id])
                found.append(
                    Detection(
                        x1=float(coords[0]),
                        y1=float(coords[1]),
                        x2=float(coords[2]),
                        y2=float(coords[3]),
                        confidence=float(score),
                        class_id=detected_class_id,
                        label=label,
                    )
                )
        return found

    return detect


def run_video_tracking(
    video_path: Path,
    output_dir: Path,
    detector: Detector,
    *,
    max_distance: float = 120.0,
    max_gap: int = 5,
) -> tuple[Path, Path, int]:
    if not video_path.is_file():
        raise FileNotFoundError(f"Input video not found: {video_path}")
    tracker = SingleBallTracker(max_distance=max_distance, max_gap=max_gap)
    output_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        capture.release()
        raise ValueError(f"Could not open input video: {video_path}")

    fps = float(capture.get(cv2.CAP_PROP_FPS))
    if not np.isfinite(fps) or fps <= 0:
        fps = 30.0

    success, frame = capture.read()
    if not success or frame is None:
        capture.release()
        raise ValueError(f"Input video contains no readable frames: {video_path}")

    height, width = frame.shape[:2]
    jsonl_path = output_dir / "tracking.jsonl"
    overlay_path = output_dir / "overlay.mp4"
    writer = cv2.VideoWriter(
        str(overlay_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        capture.release()
        raise RuntimeError(f"Could not create output video: {overlay_path}")

    previous_center: tuple[int, int] | None = None
    previous_track_id: int | None = None
    frame_index = 0

    try:
        with jsonl_path.open("w", encoding="utf-8") as records:
            while success and frame is not None:
                detections = detector(frame)
                tracked = tracker.update(detections)
                detection = tracked.detection

                if detection is None:
                    record = {
                        "frame": frame_index,
                        "timestamp_seconds": frame_index / fps,
                        "visible": False,
                        "bbox": None,
                        "pixel": None,
                        "confidence": None,
                        "class_id": None,
                        "label": None,
                        "track_id": None,
                    }
                    previous_center = None
                    previous_track_id = None
                    cv2.putText(
                        frame,
                        "ball not detected",
                        (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2,
                    )
                else:
                    center = tuple(round(value) for value in detection.center)
                    track_id = tracked.track_id
                    record = {
                        "frame": frame_index,
                        "timestamp_seconds": frame_index / fps,
                        "visible": True,
                        "bbox": [
                            round(detection.x1, 2),
                            round(detection.y1, 2),
                            round(detection.x2, 2),
                            round(detection.y2, 2),
                        ],
                        "pixel": [center[0], center[1]],
                        "confidence": round(detection.confidence, 6),
                        "class_id": detection.class_id,
                        "label": detection.label,
                        "track_id": track_id,
                    }
                    top_left = (round(detection.x1), round(detection.y1))
                    bottom_right = (round(detection.x2), round(detection.y2))
                    cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
                    cv2.circle(frame, center, 4, (0, 0, 255), -1)
                    cv2.putText(
                        frame,
                        f"{detection.label} {detection.confidence:.2f} id={track_id}",
                        (top_left[0], max(20, top_left[1] - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 0),
                        2,
                    )
                    if previous_center is not None and previous_track_id == track_id:
                        cv2.line(frame, previous_center, center, (255, 100, 0), 2)
                    previous_center = center
                    previous_track_id = track_id

                records.write(json.dumps(record, ensure_ascii=False) + "\n")
                writer.write(frame)
                frame_index += 1
                success, frame = capture.read()
    finally:
        capture.release()
        writer.release()

    return jsonl_path, overlay_path, frame_index
