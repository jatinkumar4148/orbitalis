from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from processing.event_time import WatermarkTracker, compute_processing_delay_seconds


def _json_default(o):
    if isinstance(o, datetime):
        return o.isoformat()
    return str(o)


def _parse_ts(value: str) -> datetime:
    ts = datetime.fromisoformat(value)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def run_watermark_stage(
    input_path: str,
    on_time_output_path: str,
    late_output_path: str,
    allowed_lateness_seconds: float = 300.0,
    simulate_late_event_probability: float = 0.0,
    seed: int | None = None,
) -> dict:
    """
    Reads validated events, assigns an ingestion_timestamp (simulating
    when the pipeline received them), tracks the watermark, and splits
    events into on_time vs late.

    simulate_late_event_probability: for LOCAL TESTING ONLY — artificially
    pushes some events' event_timestamp far into the past, so we can
    actually exercise the late-event path without a real distributed
    system introducing real delay. Set to 0.0 for "real" runs.
    """
    rng = random.Random(seed)
    tracker = WatermarkTracker(allowed_lateness_seconds=allowed_lateness_seconds)

    Path(on_time_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(late_output_path).parent.mkdir(parents=True, exist_ok=True)

    on_time_count = 0
    late_count = 0
    delays = []

    with open(input_path, "r") as infile, \
         open(on_time_output_path, "w") as on_time_out, \
         open(late_output_path, "w") as late_out:

        for line in infile:
            line = line.strip()
            if not line:
                continue

            event = json.loads(line)
            event_ts = _parse_ts(event["event_timestamp"])

            # --- LOCAL TEST HOOK: artificially age some events ---
            if rng.random() < simulate_late_event_probability:
                event_ts = event_ts - timedelta(seconds=rng.uniform(310, 600))
                event["event_timestamp"] = event_ts.isoformat()

            # ingestion_timestamp = "now" (simulating real-time arrival)
            ingestion_ts = datetime.now(timezone.utc)
            event["ingestion_timestamp"] = ingestion_ts.isoformat()

            delay = compute_processing_delay_seconds(event_ts, ingestion_ts)
            delays.append(delay)

            if tracker.is_late(event_ts):
                late_out.write(json.dumps(event, default=_json_default) + "\n")
                late_count += 1
            else:
                tracker.update(event_ts)
                on_time_out.write(json.dumps(event, default=_json_default) + "\n")
                on_time_count += 1

    delays.sort()
    p95 = delays[int(len(delays) * 0.95)] if delays else 0

    return {
        "total": on_time_count + late_count,
        "on_time": on_time_count,
        "late": late_count,
        "p95_processing_delay_seconds": round(p95, 2),
    }


if __name__ == "__main__":
    summary = run_watermark_stage(
        input_path="./data/valid_events.jsonl",
        on_time_output_path="./data/on_time_events.jsonl",
        late_output_path="./data/late_events.jsonl",
        allowed_lateness_seconds=300.0,
        simulate_late_event_probability=0.05,  # 5% events artificially aged for testing
        seed=42,
    )
    print(summary)