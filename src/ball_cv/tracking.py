from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Detection:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    label: str

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass(frozen=True, slots=True)
class TrackResult:
    detection: Detection | None
    track_id: int | None


class SingleBallTracker:
    """Associate detections to one ball using constant-velocity prediction."""

    def __init__(self, max_distance: float = 120.0, max_gap: int = 5) -> None:
        if not math.isfinite(max_distance) or max_distance <= 0:
            raise ValueError("max_distance must be greater than zero")
        if max_gap < 0:
            raise ValueError("max_gap cannot be negative")
        self.max_distance = max_distance
        self.max_gap = max_gap
        self._previous: Detection | None = None
        self._last: Detection | None = None
        self._misses = 0
        self._track_id = 1

    def update(self, detections: list[Detection]) -> TrackResult:
        if self._last is None:
            selected = self._best(detections)
            if selected is not None:
                self._previous, self._last, self._misses = None, selected, 0
            return TrackResult(selected, self._track_id if selected else None)

        predicted = self._predict()
        candidates = [
            (self._distance(predicted, item.center), item)
            for item in detections
        ]
        candidates = [item for item in candidates if item[0] <= self.max_distance]
        if candidates:
            _, selected = min(candidates, key=lambda item: (item[0], -item[1].confidence))
            self._previous, self._last, self._misses = self._last, selected, 0
            return TrackResult(selected, self._track_id)

        self._misses += 1
        if self._misses > self.max_gap:
            self._previous, self._last = None, None
            self._misses = 0
            self._track_id += 1
            selected = self._best(detections)
            if selected is not None:
                self._last = selected
                return TrackResult(selected, self._track_id)
        return TrackResult(None, None)

    def _predict(self) -> tuple[float, float]:
        assert self._last is not None
        current = self._last.center
        if self._previous is None:
            return current
        previous = self._previous.center
        steps = self._misses + 1
        return (
            current[0] + (current[0] - previous[0]) * steps,
            current[1] + (current[1] - previous[1]) * steps,
        )

    @staticmethod
    def _best(detections: list[Detection]) -> Detection | None:
        return max(detections, key=lambda item: item.confidence, default=None)

    @staticmethod
    def _distance(left: tuple[float, float], right: tuple[float, float]) -> float:
        return math.hypot(left[0] - right[0], left[1] - right[1])
