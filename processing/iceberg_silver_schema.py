"""
Defines the target Iceberg Silver table schema — mirrors TelemetryEvent
(schemas/telemetry_schema.py) plus the pipeline-added fields
(ingestion_timestamp, processing_delay_seconds) that M06 attaches.

Kept as a separate file (not reusing bronze_schema.py) because Silver
has EXTRA columns Bronze doesn't have — these are two different
contracts, even though most fields overlap.
"""

SILVER_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS orbitalis.orbitalis_db.silver_telemetry (
    event_id STRING,
    satellite_id STRING,
    event_timestamp STRING,
    latitude DOUBLE,
    longitude DOUBLE,
    altitude_km DOUBLE,
    velocity_kmh DOUBLE,
    battery_voltage DOUBLE,
    battery_temperature DOUBLE,
    solar_current DOUBLE,
    fuel_level DOUBLE,
    radiation_level DOUBLE,
    gyro_x DOUBLE,
    gyro_y DOUBLE,
    gyro_z DOUBLE,
    signal_strength DOUBLE,
    communication_status STRING,
    schema_version STRING,
    ingestion_timestamp TIMESTAMP,
    processing_delay_seconds BIGINT
) USING iceberg
PARTITIONED BY (satellite_id)
"""