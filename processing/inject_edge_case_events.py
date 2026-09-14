"""
One-off script: sends a SMALL batch of deliberately late and duplicate
events through the REAL Kinesis -> Firehose -> S3 path, so we can verify
the watermark/dedup logic in run_s3_pipeline.py actually catches them
on real infrastructure — not just in local unit tests.

Run this once, wait ~5 min for Firehose to flush, then re-run
run_s3_pipeline.py and check the late/ and duplicates/ S3 folders.
"""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import boto3
from dotenv import load_dotenv


def build_event(satellite_id: str, event_timestamp: datetime, event_id: str | None = None) -> dict:
    return {
        "event_id": event_id or f"EVT-{uuid.uuid4().hex[:12]}",
        "satellite_id": satellite_id,
        "event_timestamp": event_timestamp.isoformat(),
        "latitude": 12.34,
        "longitude": 56.78,
        "altitude_km": 420.0,
        "velocity_kmh": 27600.0,
        "battery_voltage": 29.5,
        "battery_temperature": 31.0,
        "solar_current": 8.0,
        "fuel_level": 80.0,
        "radiation_level": 0.3,
        "gyro_x": 0.01,
        "gyro_y": 0.01,
        "gyro_z": 0.01,
        "signal_strength": -70.0,
        "communication_status": "CONNECTED",
        "schema_version": "1.0",
    }


def main():
    load_dotenv()
    stream_name = os.getenv("KINESIS_STREAM_NAME", "orbitalis-telemetry-stream")
    region = os.getenv("AWS_REGION", "ap-south-1")
    client = boto3.client("kinesis", region_name=region)

    now = datetime.now(timezone.utc)

    events = []

    # 1. A genuinely LATE event — timestamp 10 minutes in the past
    #    (watermark's allowed_lateness_seconds=300, i.e. 5 min, so this
    #    should land past the watermark)
    late_event = build_event("SAT-999", now - timedelta(minutes=10))
    events.append(late_event)
    print(f"Late event_id: {late_event['event_id']}")

    # 2. A normal on-time event, sent TWICE with the SAME event_id
    #    (simulates a network retry producing a duplicate)
    dup_event_id = f"EVT-{uuid.uuid4().hex[:12]}"
    dup_event_1 = build_event("SAT-998", now, event_id=dup_event_id)
    dup_event_2 = build_event("SAT-998", now, event_id=dup_event_id)
    events.append(dup_event_1)
    events.append(dup_event_2)
    print(f"Duplicate event_id (sent twice): {dup_event_id}")

    records = [
        {"Data": json.dumps(e).encode("utf-8"), "PartitionKey": e["satellite_id"]}
        for e in events
    ]

    response = client.put_records(StreamName=stream_name, Records=records)
    print(f"\nSent {len(records)} records. FailedRecordCount: {response['FailedRecordCount']}")


if __name__ == "__main__":
    main()