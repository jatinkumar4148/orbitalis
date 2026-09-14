import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from processing.validation import (
    check_required_fields,
    check_ranges,
    check_timestamp_not_future,
    validate_event,
)


def valid_event(**overrides):
    base = {
        "event_id": "EVT-1",
        "satellite_id": "SAT-001",
        "event_timestamp": datetime.now(timezone.utc).isoformat(),
        "latitude": 28.6,
        "longitude": 77.2,
        "altitude_km": 420.0,
        "velocity_kmh": 27600.0,
        "battery_voltage": 29.4,
        "battery_temperature": 34.7,
        "solar_current": 8.4,
        "fuel_level": 72.5,
        "radiation_level": 0.31,
        "gyro_x": 0.01,
        "gyro_y": -0.01,
        "gyro_z": 0.01,
        "signal_strength": -71,
        "communication_status": "CONNECTED",
    }
    base.update(overrides)
    return base


def test_valid_event_passes():
    assert validate_event(valid_event()) is None


def test_missing_field_detected():
    event = valid_event()
    del event["battery_temperature"]
    error = validate_event(event)
    assert error is not None
    assert "missing_fields" in error


def test_gps_corruption_detected():
    event = valid_event(latitude=400.0)
    error = validate_event(event)
    assert error is not None
    assert "latitude_out_of_range" in error


def test_sensor_corruption_detected():
    event = valid_event(battery_temperature=9999.0)
    error = validate_event(event)
    assert error is not None
    assert "battery_temperature_out_of_range" in error


def test_future_timestamp_detected():
    future = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    event = valid_event(event_timestamp=future)
    error = validate_event(event)
    assert error is not None
    assert "future" in error


def test_range_check_ignores_missing_field():
    """check_ranges shouldn't crash if a field is already missing — that's check_required_fields's job."""
    event = valid_event()
    del event["latitude"]
    assert check_ranges(event) is None