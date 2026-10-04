import json
from pathlib import Path

import cv2
import numpy as np

from ball_cv.tracking import Detection
from ball_cv.video_tracking import run_video_tracking


def test_video_tracking_writes_frame_records_and_overlay(tmp_path: Path) -> None:
    video_path = tmp_path / "input.mp4"
    writer = cv2.VideoWriter(
        str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (64, 48)
    )
    assert writer.isOpened()
    for _ in range(3):
        writer.write(np.zeros((48, 64, 3), dtype=np.uint8))
    writer.release()

    calls = 0

    def detector(_frame: np.ndarray) -> list[Detection]:
        nonlocal calls
        calls += 1
        if calls == 2:
            return []
        center_x = 20 + calls
        return [Detection(center_x - 3, 10, center_x + 3, 16, 0.9, 0, "ball")]

    jsonl_path, overlay_path, frame_count = run_video_tracking(
        video_path, tmp_path / "result", detector
    )

    records = [json.loads(line) for line in jsonl_path.read_text().splitlines()]
    assert frame_count == 3
    assert [record["visible"] for record in records] == [True, False, True]
    assert records[0]["frame"] == 0
    assert records[0]["pixel"] == [21, 13]
    assert records[1]["pixel"] is None
    assert overlay_path.is_file() and overlay_path.stat().st_size > 0
    overlay = cv2.VideoCapture(str(overlay_path))
    overlay_frames = 0
    while overlay.read()[0]:
        overlay_frames += 1
    overlay.release()
    assert overlay_frames == frame_count
