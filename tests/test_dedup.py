import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from processing.dedup import DeduplicationTracker


def test_first_occurrence_is_not_duplicate():
    tracker = DeduplicationTracker(window_seconds=86400)
    now = datetime.now(timezone.utc)
    assert tracker.is_duplicate("EVT-1", now) is False


def test_second_occurrence_of_same_id_is_duplicate():
    tracker = DeduplicationTracker(window_seconds=86400)
    now = datetime.now(timezone.utc)

    tracker.is_duplicate("EVT-1", now)
    tracker.mark_seen("EVT-1", now)

    assert tracker.is_duplicate("EVT-1", now) is True


def test_different_ids_are_not_duplicates():
    tracker = DeduplicationTracker(window_seconds=86400)
    now = datetime.now(timezone.utc)

    tracker.mark_seen("EVT-1", now)
    assert tracker.is_duplicate("EVT-2", now) is False


def test_entry_expires_after_window():
    tracker = DeduplicationTracker(window_seconds=60)  # short window for testing
    t1 = datetime.now(timezone.utc)
    tracker.mark_seen("EVT-1", t1)

    much_later = t1 + timedelta(seconds=120)  # beyond the 60s window
    assert tracker.is_duplicate("EVT-1", much_later) is False


def test_entry_still_duplicate_within_window():
    tracker = DeduplicationTracker(window_seconds=60)
    t1 = datetime.now(timezone.utc)
    tracker.mark_seen("EVT-1", t1)

    slightly_later = t1 + timedelta(seconds=30)  # within the 60s window
    assert tracker.is_duplicate("EVT-1", slightly_later) is True