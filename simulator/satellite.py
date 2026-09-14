from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone

from schemas.telemetry_schema import CommunicationStatus


@dataclass
class SatelliteState:
    satellite_id: str
    latitude: float
    longitude: float
    altitude_km: float
    velocity_kmh: float
    orbit_angle: float = 0.0

    battery_voltage: float = 29.5
    battery_temperature: float = 32.0
    solar_current: float = 8.4

    fuel_level: float = 85.0
    radiation_level: float = 0.3

    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0

    signal_strength: float = -70.0
    communication_status: CommunicationStatus = CommunicationStatus.CONNECTED


def _walk(rng: random.Random, value: float, step: float, lo: float, hi: float) -> float:
    """Chhota sa random nudge deta hai — isi se realistic drift banta hai."""
    value += rng.uniform(-step, step)
    return max(lo, min(hi, value))


class Satellite:
    def __init__(self, satellite_id: str, seed: int | None = None):
        rng = random.Random(seed)
        self.rng = rng
        self.state = SatelliteState(
            satellite_id=satellite_id,
            latitude=rng.uniform(-51.6, 51.6),
            longitude=rng.uniform(-180, 180),
            altitude_km=rng.uniform(400, 450),
            velocity_kmh=27600.0,
            orbit_angle=rng.uniform(0, 2 * math.pi),
        )

    def tick(self, dt_seconds: float = 1.0) -> None:
        s = self.state

        angular_speed = s.velocity_kmh / (2 * math.pi * (6371 + s.altitude_km)) * (2 * math.pi) / 3600
        s.orbit_angle = (s.orbit_angle + angular_speed * dt_seconds) % (2 * math.pi)
        s.latitude = 51.6 * math.sin(s.orbit_angle)
        s.longitude = ((s.longitude + (s.velocity_kmh * dt_seconds / 111)) + 180) % 360 - 180
        s.altitude_km = _walk(self.rng, s.altitude_km, 0.05, 380, 470)
        s.velocity_kmh = _walk(self.rng, s.velocity_kmh, 5, 27000, 28000)

        solar_factor = (math.sin(s.orbit_angle) + 1) / 2
        s.solar_current = _walk(self.rng, 0.5 + 8 * solar_factor, 0.1, 0, 9)
        charge_delta = (s.solar_current - 6.5) * 0.01
        s.battery_voltage = max(0, min(32, s.battery_voltage + charge_delta + self.rng.uniform(-0.02, 0.02)))
        s.battery_temperature = _walk(self.rng, s.battery_temperature, 0.3, 15, 45)

        s.fuel_level = max(0, s.fuel_level - abs(self.rng.uniform(0, 0.0005)))
        s.radiation_level = _walk(self.rng, s.radiation_level, 0.02, 0.05, 1.0)

        s.gyro_x = _walk(self.rng, s.gyro_x, 0.01, -0.5, 0.5)
        s.gyro_y = _walk(self.rng, s.gyro_y, 0.01, -0.5, 0.5)
        s.gyro_z = _walk(self.rng, s.gyro_z, 0.01, -0.5, 0.5)

        s.signal_strength = _walk(self.rng, s.signal_strength, 1.0, -90, -50)
        if s.communication_status == CommunicationStatus.CONNECTED and s.signal_strength < -85:
            s.communication_status = CommunicationStatus.DEGRADED
        elif s.communication_status == CommunicationStatus.DEGRADED and s.signal_strength > -80:
            s.communication_status = CommunicationStatus.CONNECTED

    def to_event_dict(self) -> dict:
        s = self.state
        return {
            "satellite_id": s.satellite_id,
            "event_timestamp": datetime.now(timezone.utc),
            "latitude": round(s.latitude, 4),
            "longitude": round(s.longitude, 4),
            "altitude_km": round(s.altitude_km, 2),
            "velocity_kmh": round(s.velocity_kmh, 2),
            "battery_voltage": round(s.battery_voltage, 2),
            "battery_temperature": round(s.battery_temperature, 2),
            "solar_current": round(s.solar_current, 2),
            "fuel_level": round(s.fuel_level, 2),
            "radiation_level": round(s.radiation_level, 3),
            "gyro_x": round(s.gyro_x, 4),
            "gyro_y": round(s.gyro_y, 4),
            "gyro_z": round(s.gyro_z, 4),
            "signal_strength": round(s.signal_strength, 1),
            "communication_status": s.communication_status,
        }