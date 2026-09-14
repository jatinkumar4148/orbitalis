from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from processing.validation import validate_event


def _json_default(o):
    if isinstance(o, datetime):
        return o.isoformat()
    return str(o)


def run_quality_gate(
    input_path: str,
    valid_output_path: str,
    rejected_output_path: str,
    pipeline_version: str = "0.1.0",
) -> dict:
    """
    Reads raw events from input_path (JSONL), validates each one,
    and writes them to either valid_output_path or rejected_output_path.
    Returns a summary dict with counts.
    """
    Path(valid_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(rejected_output_path).parent.mkdir(parents=True, exist_ok=True)

    valid_count = 0
    rejected_count = 0

    with open(input_path, "r") as infile, \
         open(valid_output_path, "w") as valid_out, \
         open(rejected_output_path, "w") as rejected_out:

        for line in infile:
            line = line.strip()
            if not line:
                continue

            event = json.loads(line)
            error_reason = validate_event(event)

            if error_reason is None:
                valid_out.write(json.dumps(event, default=_json_default) + "\n")
                valid_count += 1
            else:
                rejected_record = {
                    "original_event": event,
                    "error_reason": error_reason,
                    "validation_timestamp": datetime.now(timezone.utc),
                    "pipeline_version": pipeline_version,
                }
                rejected_out.write(json.dumps(rejected_record, default=_json_default) + "\n")
                rejected_count += 1

    return {
        "total": valid_count + rejected_count,
        "valid": valid_count,
        "rejected": rejected_count,
    }


if __name__ == "__main__":
    summary = run_quality_gate(
        input_path="./data/local_events.jsonl",
        valid_output_path="./data/valid_events.jsonl",
        rejected_output_path="./data/rejected_events.jsonl",
    )
    print(f"Total: {summary['total']}, Valid: {summary['valid']}, Rejected: {summary['rejected']}")