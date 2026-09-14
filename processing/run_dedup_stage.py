from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

from processing.dedup import DeduplicationTracker


def _json_default(o):
    if isinstance(o, datetime):
        return o.isoformat()
    return str(o)


def _parse_ts(value: str) -> datetime:
    ts = datetime.fromisoformat(value)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def run_dedup_stage(
    input_path: str,
    deduped_output_path: str,
    duplicates_output_path: str,
    window_seconds: float = 86400.0,
    simulate_duplicate_probability: float = 0.0,
    seed: int | None = None,
) -> dict:
    """
    Reads on-time events, checks each event_id against the dedup tracker,
    and splits into deduped (first-seen) vs duplicate (already-seen) output.

    simulate_duplicate_probability: LOCAL TESTING ONLY — re-emits some
    events a second time with the SAME event_id, so we can actually
    exercise the duplicate-detection path locally. Set to 0.0 for real runs.
    """
    rng = random.Random(seed)
    tracker = DeduplicationTracker(window_seconds=window_seconds)

    Path(deduped_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(duplicates_output_path).parent.mkdir(parents=True, exist_ok=True)

    deduped_count = 0
    duplicate_count = 0

    # Read all events first so we can inject synthetic duplicates for testing
    events = []
    with open(input_path, "r") as infile:
        for line in infile:
            line = line.strip()
            if line:
                events.append(json.loads(line))

    # --- LOCAL TEST HOOK: duplicate some events ---
    if simulate_duplicate_probability > 0:
        synthetic_dupes = [
            dict(e) for e in events if rng.random() < simulate_duplicate_probability
        ]
        events.extend(synthetic_dupes)
        rng.shuffle(events)  # duplicates won't always be back-to-back, more realistic

    with open(deduped_output_path, "w") as deduped_out, \
         open(duplicates_output_path, "w") as duplicates_out:

        for event in events:
            event_id = event["event_id"]
            seen_at = _parse_ts(event.get("ingestion_timestamp") or event["event_timestamp"])

            if tracker.is_duplicate(event_id, seen_at):
                duplicates_out.write(json.dumps(event, default=_json_default) + "\n")
                duplicate_count += 1
            else:
                tracker.mark_seen(event_id, seen_at)
                deduped_out.write(json.dumps(event, default=_json_default) + "\n")
                deduped_count += 1

    return {
        "total": deduped_count + duplicate_count,
        "deduped": deduped_count,
        "duplicates_removed": duplicate_count,
    }


if __name__ == "__main__":
    summary = run_dedup_stage(
        input_path="./data/on_time_events.jsonl",
        deduped_output_path="./data/deduped_events.jsonl",
        duplicates_output_path="./data/duplicate_events.jsonl",
        simulate_duplicate_probability=0.05,  # 5% events artificially duplicated for testing
        seed=42,
    )
    print(summary)