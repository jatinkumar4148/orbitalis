import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.telemetry_schema import TelemetryEvent, CommunicationStatus


def valid_event_kwargs(**overrides):
    base = dict(
        satellite_id="SAT-001",
        event_timestamp=datetime.now(timezone.utc),
        latitude=28.6139,
        longitude=77.2090,
        altitude_km=421.7,
        velocity_kmh=27600,
        battery_voltage=29.4,
        battery_temperature=34.7,
        solar_current=8.42,
        fuel_level=72.5,
        radiation_level=0.31,
        gyro_x=0.013,
        gyro_y=-0.004,
        gyro_z=0.008,
        signal_strength=-71,
        communication_status=CommunicationStatus.CONNECTED,
    )
    base.update(overrides)
    return base


def test_valid_event_passes():
    event = TelemetryEvent(**valid_event_kwargs())
    assert event.satellite_id == "SAT-001"
    assert event.schema_version == "1.0"


def test_latitude_out_of_range_rejected():
    with pytest.raises(ValidationError):
        TelemetryEvent(**valid_event_kwargs(latitude=400))


def test_negative_fuel_rejected():
    with pytest.raises(ValidationError):
        TelemetryEvent(**valid_event_kwargs(fuel_level=-5))


def test_future_timestamp_rejected():
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    with pytest.raises(ValidationError):
        TelemetryEvent(**valid_event_kwargs(event_timestamp=future))


def test_missing_required_field_rejected():
    kwargs = valid_event_kwargs()
    del kwargs["battery_temperature"]
    with pytest.raises(ValidationError):
        TelemetryEvent(**kwargs)