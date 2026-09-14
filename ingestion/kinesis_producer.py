from __future__ import annotations

import json
import time
from datetime import datetime, date

import boto3
from botocore.exceptions import ClientError

from simulator.producer import EventSink


def _json_default(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    return str(o)


class KinesisSink(EventSink):
    """
    Sends events to a real AWS Kinesis Data Stream using PutRecords
    (batched, not single PutRecord — much better throughput).

    Partition key = satellite_id, per ADR / blueprint: this keeps all
    events for one satellite in the same shard, preserving order for
    that satellite's data.

    Failed records are retried with exponential backoff (per blueprint's
    retry design: retry 1 -> retry 2 -> retry 3 -> log permanent failure).
    """

    def __init__(self, stream_name: str, region: str = "ap-south-1", max_retries: int = 3):
        self.stream_name = stream_name
        self.max_retries = max_retries
        self.client = boto3.client("kinesis", region_name=region)
        self._permanently_failed: list[dict] = []

    def send_batch(self, events: list[dict]) -> None:
        records = [
            {
                "Data": json.dumps(event, default=_json_default).encode("utf-8"),
                "PartitionKey": event["satellite_id"],
            }
            for event in events
        ]

        self._put_with_retry(records)

    def _put_with_retry(self, records: list[dict], attempt: int = 1) -> None:
        if not records:
            return

        try:
            response = self.client.put_records(
                StreamName=self.stream_name,
                Records=records,
            )
        except ClientError as e:
            print(f"[KinesisSink] PutRecords call failed entirely (attempt {attempt}): {e}")
            if attempt <= self.max_retries:
                time.sleep(2 ** attempt)  # exponential backoff: 2s, 4s, 8s
                self._put_with_retry(records, attempt + 1)
            else:
                print(f"[KinesisSink] Giving up after {self.max_retries} attempts. "
                      f"{len(records)} records permanently failed.")
                self._permanently_failed.extend(records)
            return

        failed_count = response.get("FailedRecordCount", 0)
        if failed_count > 0:
            # Kinesis returns per-record results; pick out the ones that failed
            failed_records = [
                records[i] for i, r in enumerate(response["Records"]) if "ErrorCode" in r
            ]
            print(f"[KinesisSink] {failed_count} records failed in this batch (attempt {attempt}).")
            if attempt <= self.max_retries:
                time.sleep(2 ** attempt)
                self._put_with_retry(failed_records, attempt + 1)
            else:
                print(f"[KinesisSink] Giving up after {self.max_retries} attempts. "
                      f"{len(failed_records)} records permanently failed.")
                self._permanently_failed.extend(failed_records)

    def close(self) -> None:
        if self._permanently_failed:
            print(f"[KinesisSink] WARNING: {len(self._permanently_failed)} events were "
                  f"never delivered after all retries.")