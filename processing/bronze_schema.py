"""
Explicit schema for streaming reads. Structured Streaming (unlike batch
read) cannot auto-infer JSON schema — it must be told upfront, since it
needs to know the schema before any data has arrived.
"""

from pyspark.sql.types import StructType, StructField, StringType, DoubleType

BRONZE_SCHEMA = StructType([
    StructField("event_id", StringType()),
    StructField("satellite_id", StringType()),
    StructField("event_timestamp", StringType()),
    StructField("latitude", DoubleType()),
    StructField("longitude", DoubleType()),
    StructField("altitude_km", DoubleType()),
    StructField("velocity_kmh", DoubleType()),
    StructField("battery_voltage", DoubleType()),
    StructField("battery_temperature", DoubleType()),
    StructField("solar_current", DoubleType()),
    StructField("fuel_level", DoubleType()),
    StructField("radiation_level", DoubleType()),
    StructField("gyro_x", DoubleType()),
    StructField("gyro_y", DoubleType()),
    StructField("gyro_z", DoubleType()),
    StructField("signal_strength", DoubleType()),
    StructField("communication_status", StringType()),
    StructField("schema_version", StringType()),
])