from ball_cv.tracking import Detection, SingleBallTracker


def detection(center_x: float, confidence: float = 0.8) -> Detection:
    return Detection(
        x1=center_x - 2,
        y1=8,
        x2=center_x + 2,
        y2=12,
        confidence=confidence,
        class_id=0,
        label="ball",
    )


def test_tracker_follows_nearest_detection_and_predicts_motion() -> None:
    tracker = SingleBallTracker(max_distance=20, max_gap=2)

    first = tracker.update([detection(10), detection(40, confidence=0.95)])
    second = tracker.update([detection(14), detection(39, confidence=0.99)])
    third = tracker.update([detection(18), detection(38, confidence=0.99)])

    assert first.detection == detection(40, confidence=0.95)
    assert second.detection == detection(39, confidence=0.99)
    assert third.detection == detection(38, confidence=0.99)
    assert first.track_id == second.track_id == third.track_id == 1


def test_tracker_keeps_identity_over_short_gap_then_starts_new_track() -> None:
    tracker = SingleBallTracker(max_distance=20, max_gap=1)
    tracker.update([detection(10)])

    missing = tracker.update([])
    same_track = tracker.update([detection(12)])
    tracker.update([])
    expired = tracker.update([])
    new_track = tracker.update([detection(80)])

    assert missing.detection is None
    assert same_track.track_id == 1
    assert expired.track_id is None
    assert new_track.track_id == 2
