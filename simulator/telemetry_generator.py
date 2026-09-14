from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Iterator

from simulator.satellite import Satellite
from simulator.anomaly_generator import AnomalyEngine, AnomalyType


class SimulatorEngine:
    def __init__(
        self,
        num_satellites: int = 10,
        anomaly_injection_enabled: bool = True,
        anomaly_injection_probability: float = 0.001,
        seed: int | None = None,
    ):
        self.rng = random.Random(seed)
        self.anomaly_injection_enabled = anomaly_injection_enabled
        self.anomaly_injection_probability = anomaly_injection_probability

        self.satellites: dict[str, Satellite] = {
            f"SAT-{i+1:03d}": Satellite(f"SAT-{i+1:03d}", seed=self.rng.randint(0, 10_000))
            for i in range(num_satellites)
        }
        self.anomaly_engines: dict[str, AnomalyEngine] = {
            sat_id: AnomalyEngine(random.Random(self.rng.randint(0, 10_000)))
            for sat_id in self.satellites
        }

    def tick_all(self) -> list[dict]:
        events = []
        for sat_id, sat in self.satellites.items():
            engine = self.anomaly_engines[sat_id]

            sat.tick()

            active_this_tick = None
            if self.anomaly_injection_enabled:
                engine.maybe_start_anomaly(self.anomaly_injection_probability)
                active_this_tick = engine.active
                engine.apply(sat)

            event = sat.to_event_dict()
            event["event_id"] = f"EVT-{uuid.uuid4().hex[:12]}"
            event["schema_version"] = "1.0"

            if active_this_tick == AnomalyType.MISSING_FIELD:
                event.pop("battery_temperature", None)

            events.append(event)
        return events

    def run(self, num_ticks: int | None = None) -> Iterator[list[dict]]:
        tick = 0
        while num_ticks is None or tick < num_ticks:
            yield self.tick_all()
            tick += 1