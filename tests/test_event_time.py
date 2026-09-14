import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from processing.event_time import WatermarkTracker, compute_processing_delay_seconds


def test_first_event_is_never_late():
    tracker = WatermarkTracker(allowed_lateness_seconds=300)
    now = datetime.now(timezone.utc)
    assert tracker.is_late(now) is False


def test_watermark_advances_with_new_events():
    tracker = WatermarkTracker(allowed_lateness_seconds=300)
    t1 = datetime.now(timezone.utc)
    tracker.update(t1)
    assert tracker.current_watermark() == t1 - timedelta(seconds=300)

    t2 = t1 + timedelta(seconds=100)
    tracker.update(t2)
    assert tracker.current_watermark() == t2 - timedelta(seconds=300)


def test_event_within_lateness_window_is_on_time():
    tracker = WatermarkTracker(allowed_lateness_seconds=300)
    now = datetime.now(timezone.utc)
    tracker.update(now)

    slightly_late = now - timedelta(seconds=100)  # within 300s window
    assert tracker.is_late(slightly_late) is False


def test_event_beyond_lateness_window_is_late():
    tracker = WatermarkTracker(allowed_lateness_seconds=300)
    now = datetime.now(timezone.utc)
    tracker.update(now)

    very_late = now - timedelta(seconds=400)  # beyond 300s window
    assert tracker.is_late(very_late) is True


def test_watermark_does_not_move_backward():
    tracker = WatermarkTracker(allowed_lateness_seconds=300)
    t1 = datetime.now(timezone.utc)
    tracker.update(t1)

    earlier = t1 - timedelta(seconds=50)
    tracker.update(earlier)  # older event arriving after a newer one

    assert tracker.current_watermark() == t1 - timedelta(seconds=300)


def test_processing_delay_calculation():
    event_ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    ingestion_ts = datetime(2026, 1, 1, 12, 0, 5, tzinfo=timezone.utc)
    assert compute_processing_delay_seconds(event_ts, ingestion_ts) == 5.0