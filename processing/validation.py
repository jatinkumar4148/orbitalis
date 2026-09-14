from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def check_required_fields(event: dict) -> Optional[str]:
    """Return error reason if a required field is missing, else None."""
    required = {
        "event_id", "satellite_id", "event_timestamp",
        "latitude", "longitude", "altitude_km", "velocity_kmh",
        "battery_voltage", "battery_temperature", "solar_current",
        "fuel_level", "radiation_level",
        "gyro_x", "gyro_y", "gyro_z",
        "signal_strength", "communication_status",
    }
    missing = required - event.keys()
    if missing:
        return f"missing_fields: {sorted(missing)}"
    return None


def check_ranges(event: dict) -> Optional[str]:
    """Return error reason if any field is out of realistic range, else None."""
    checks = [
        ("latitude", -90, 90),
        ("longitude", -180, 180),
        ("altitude_km", 0, 2000),
        ("velocity_kmh", 0, 40000),
        ("battery_voltage", 0, 50),
        ("battery_temperature", -50, 150),
        ("solar_current", 0, 50),
        ("fuel_level", 0, 100),
        ("radiation_level", 0, 10),
        ("signal_strength", -150, 0),
    ]
    for field, lo, hi in checks:
        value = event.get(field)
        if value is None:
            continue  # already caught by check_required_fields
        if not (lo <= value <= hi):
            return f"{field}_out_of_range: {value} not in [{lo}, {hi}]"
    return None


def check_timestamp_not_future(event: dict) -> Optional[str]:
    """Return error reason if event_timestamp is unrealistically in the future."""
    ts = event.get("event_timestamp")
    if ts is None:
        return None
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    now = datetime.now(timezone.utc)
    if (ts - now).total_seconds() > 5:
        return "event_timestamp_in_future"
    return None


def validate_event(event: dict) -> Optional[str]:
    """
    Run all validation rules on one event.
    Returns None if valid, or the FIRST error reason found if invalid.
    """
    for check_fn in (check_required_fields, check_ranges, check_timestamp_not_future):
        error = check_fn(event)
        if error:
            return error
    return None