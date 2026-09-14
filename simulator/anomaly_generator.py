from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from simulator.satellite import Satellite
from schemas.telemetry_schema import CommunicationStatus


class AnomalyType(str, Enum):
    BATTERY_FAILURE = "BATTERY_FAILURE"
    TEMPERATURE_SPIKE = "TEMPERATURE_SPIKE"
    COMMUNICATION_LOSS = "COMMUNICATION_LOSS"
    SENSOR_CORRUPTION = "SENSOR_CORRUPTION"
    GPS_CORRUPTION = "GPS_CORRUPTION"
    MISSING_FIELD = "MISSING_FIELD"


@dataclass
class AnomalyProfile:
    duration_ticks_range: tuple[int, int]
    apply_fn_name: str


ANOMALY_PROFILES: dict[AnomalyType, AnomalyProfile] = {
    AnomalyType.BATTERY_FAILURE: AnomalyProfile((20, 60), "_apply_battery_failure"),
    AnomalyType.TEMPERATURE_SPIKE: AnomalyProfile((5, 15), "_apply_temperature_spike"),
    AnomalyType.COMMUNICATION_LOSS: AnomalyProfile((10, 40), "_apply_communication_loss"),
    AnomalyType.SENSOR_CORRUPTION: AnomalyProfile((1, 1), "_apply_sensor_corruption"),
    AnomalyType.GPS_CORRUPTION: AnomalyProfile((1, 1), "_apply_gps_corruption"),
    AnomalyType.MISSING_FIELD: AnomalyProfile((1, 1), "_noop"),
}


class AnomalyEngine:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.active: AnomalyType | None = None
        self.ticks_remaining: int = 0

    def maybe_start_anomaly(self, injection_probability: float) -> None:
        if self.active is not None:
            return
        if self.rng.random() < injection_probability:
            self.active = self.rng.choice(list(AnomalyType))
            lo, hi = ANOMALY_PROFILES[self.active].duration_ticks_range
            self.ticks_remaining = self.rng.randint(lo, hi)

    def apply(self, satellite: Satellite) -> None:
        if self.active is None:
            return
        fn = getattr(self, ANOMALY_PROFILES[self.active].apply_fn_name)
        fn(satellite)
        self.ticks_remaining -= 1
        if self.ticks_remaining <= 0:
            self.active = None

    def _apply_battery_failure(self, sat: Satellite) -> None:
        sat.state.battery_voltage = max(5.0, sat.state.battery_voltage - self.rng.uniform(0.15, 0.4))

    def _apply_temperature_spike(self, sat: Satellite) -> None:
        sat.state.battery_temperature = min(150.0, sat.state.battery_temperature * self.rng.uniform(1.08, 1.25))

    def _apply_communication_loss(self, sat: Satellite) -> None:
        sat.state.communication_status = CommunicationStatus.DISCONNECTED
        sat.state.signal_strength = -999

    def _apply_sensor_corruption(self, sat: Satellite) -> None:
        sat.state.battery_temperature = 9999.0

    def _apply_gps_corruption(self, sat: Satellite) -> None:
        sat.state.latitude = 400.0

    def _noop(self, sat: Satellite) -> None:
        pass