
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

CURRENT_SCHEMA_VERSION = "1.0"


class CommunicationStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    DEGRADED = "DEGRADED"


class TelemetryEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid4().hex[:12]}")
    satellite_id: str
    event_timestamp: datetime
    ingestion_timestamp: Optional[datetime] = None

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    altitude_km: float = Field(gt=0, le=2000)
    velocity_kmh: float = Field(gt=0, le=40000)

    battery_voltage: float = Field(ge=0, le=50)
    battery_temperature: float = Field(ge=-50, le=150)
    solar_current: float = Field(ge=0, le=50)

    fuel_level: float = Field(ge=0, le=100)
    radiation_level: float = Field(ge=0, le=10)

    gyro_x: float = Field(ge=-10, le=10)
    gyro_y: float = Field(ge=-10, le=10)
    gyro_z: float = Field(ge=-10, le=10)

    signal_strength: float = Field(ge=-150, le=0)
    communication_status: CommunicationStatus

    schema_version: str = CURRENT_SCHEMA_VERSION

    @field_validator("event_timestamp")
    @classmethod
    def not_in_future(cls, v: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        v_aware = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if (v_aware - now).total_seconds() > 5:
            raise ValueError("event_timestamp is in the future beyond allowed clock skew")
        return v

    model_config = ConfigDict(use_enum_values=True)


class RejectedEvent(BaseModel):
    original_event: dict
    error_reason: str
    validation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pipeline_version: str = "0.1.0"