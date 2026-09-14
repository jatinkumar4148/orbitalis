from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class WatermarkTracker:
    """
    Tracks the 'watermark' — the point in event-time before which we stop
    accepting late events. As events flow in, we track the maximum
    event_timestamp seen so far. The watermark is always
    (max_event_time_seen - allowed_lateness).

    Any event with event_timestamp BEFORE the watermark is considered
    too late.
    """
    allowed_lateness_seconds: float = 300.0  # 5 minutes, per the blueprint
    _max_event_time_seen: Optional[datetime] = None

    def current_watermark(self) -> Optional[datetime]:
        if self._max_event_time_seen is None:
            return None
        return self._max_event_time_seen - timedelta(seconds=self.allowed_lateness_seconds)

    def update(self, event_timestamp: datetime) -> None:
        """Call this for every event, in the order it's processed."""
        if self._max_event_time_seen is None or event_timestamp > self._max_event_time_seen:
            self._max_event_time_seen = event_timestamp

    def is_late(self, event_timestamp: datetime) -> bool:
        watermark = self.current_watermark()
        if watermark is None:
            return False  # first event ever seen — nothing to compare against yet
        return event_timestamp < watermark


def compute_processing_delay_seconds(event_timestamp: datetime, ingestion_timestamp: datetime) -> float:
    """
    processing_delay = ingestion_timestamp - event_timestamp
    This is THE core latency metric for the whole pipeline (M14 will
    track P95/P99 of this).
    """
    return (ingestion_timestamp - event_timestamp).total_seconds()