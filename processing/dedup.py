from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class DeduplicationTracker:
    """
    Tracks recently-seen event_ids to detect duplicates, bounded to a
    rolling time window (see ADR-005 in docs/decisions.md — unbounded
    dedup state is not viable in a real streaming job, so we cap it).
    """
    window_seconds: float = 86400.0  # 24 hours, per ADR-005
    _seen: dict[str, datetime] = field(default_factory=dict)

    def is_duplicate(self, event_id: str, seen_at: datetime) -> bool:
        """Check if we've already seen this event_id within the window."""
        self._evict_expired(seen_at)
        return event_id in self._seen

    def mark_seen(self, event_id: str, seen_at: datetime) -> None:
        self._seen[event_id] = seen_at

    def _evict_expired(self, now: datetime) -> None:
        """Drop entries older than the window — keeps memory bounded."""
        cutoff = now - timedelta(seconds=self.window_seconds)
        expired = [eid for eid, ts in self._seen.items() if ts < cutoff]
        for eid in expired:
            del self._seen[eid]