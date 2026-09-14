from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, date
from pathlib import Path

from simulator.telemetry_generator import SimulatorEngine


def _json_default(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    return str(o)


class EventSink(ABC):
    @abstractmethod
    def send_batch(self, events: list[dict]) -> None: ...

    def close(self) -> None:
        pass


class LocalFileSink(EventSink):
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "a")

    def send_batch(self, events: list[dict]) -> None:
        for e in events:
            self._fh.write(json.dumps(e, default=_json_default) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def build_sink_from_env() -> EventSink:
    sink_type = os.getenv("EVENT_SINK", "local_file")
    if sink_type == "local_file":
        return LocalFileSink(os.getenv("LOCAL_SINK_PATH", "./data/local_events.jsonl"))
    if sink_type == "kinesis":
        from ingestion.kinesis_producer import KinesisSink
        return KinesisSink(
            stream_name=os.getenv("KINESIS_STREAM_NAME", "orbitalis-telemetry-stream"),
            region=os.getenv("AWS_REGION", "ap-south-1"),
        )
    raise ValueError(f"Unknown EVENT_SINK: {sink_type}")


def run_simulation(
    num_satellites: int,
    event_rate_per_satellite: float,
    duration_seconds: float | None,
    sink: EventSink,
    anomaly_injection_enabled: bool = True,
    anomaly_injection_probability: float = 0.001,
    seed: int | None = None,
) -> int:
    engine = SimulatorEngine(
        num_satellites=num_satellites,
        anomaly_injection_enabled=anomaly_injection_enabled,
        anomaly_injection_probability=anomaly_injection_probability,
        seed=seed,
    )
    tick_interval = 1.0 / event_rate_per_satellite
    start = time.monotonic()
    total_sent = 0

    for events in engine.run():
        sink.send_batch(events)
        total_sent += len(events)

        if duration_seconds is not None and (time.monotonic() - start) >= duration_seconds:
            break
        time.sleep(tick_interval)

    sink.close()
    return total_sent


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    sink = build_sink_from_env()
    total = run_simulation(
        num_satellites=int(os.getenv("NUM_SATELLITES", 10)),
        event_rate_per_satellite=float(os.getenv("EVENT_RATE_PER_SATELLITE", 100)),
        duration_seconds=float(os.getenv("SIM_DURATION_SECONDS", 10)),
        sink=sink,
        anomaly_injection_enabled=os.getenv("ANOMALY_INJECTION_ENABLED", "true").lower() == "true",
        anomaly_injection_probability=float(os.getenv("ANOMALY_INJECTION_PROBABILITY", 0.001)),
        seed=int(os.getenv("RANDOM_SEED")) if os.getenv("RANDOM_SEED") else None,
    )
    print(f"Sent {total} events.")