"""
Spark-based Data Quality (M06 + M07, Spark version)
======================================================
Same validation RULES as processing/validation.py, but expressed as
Spark DataFrame operations so they can run distributed, at scale, on
streaming data — not just a local Python loop over a file.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, when, lit, current_timestamp, unix_timestamp


# Same range rules as processing/validation.py — kept in sync manually for now.
# (In a bigger system we'd generate both from one source of truth; noted as
# a possible future improvement, not needed at this scale.)
RANGE_RULES = [
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

REQUIRED_FIELDS = [
    "event_id", "satellite_id", "event_timestamp",
    "latitude", "longitude", "altitude_km", "velocity_kmh",
    "battery_voltage", "battery_temperature", "solar_current",
    "fuel_level", "radiation_level",
    "gyro_x", "gyro_y", "gyro_z",
    "signal_strength", "communication_status",
]


def add_validation_column(df: DataFrame) -> DataFrame:
    """
    Adds an 'error_reason' column to the DataFrame — null if the row is
    valid, or a string describing the first problem found if not.

    Uses Spark's `when/otherwise` chain, which is the DataFrame-native
    equivalent of the if/elif chain in processing/validation.py.
    """
    error_col = lit(None).cast("string")

    # Check required fields (null check) — reverse order so the FIRST
    # rule in the list ends up evaluated first, matching validate_event()'s
    # "return the first error found" behavior.
    for field in reversed(REQUIRED_FIELDS):
        error_col = when(col(field).isNull(), lit(f"missing_field: {field}")).otherwise(error_col)

    # Check ranges
    for field, lo, hi in reversed(RANGE_RULES):
        error_col = when(
            col(field).isNotNull() & ((col(field) < lo) | (col(field) > hi)),
            lit(f"{field}_out_of_range")
        ).otherwise(error_col)

    return df.withColumn("error_reason", error_col)


def split_valid_invalid(df: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Returns (valid_df, rejected_df) based on the error_reason column."""
    validated = add_validation_column(df)
    valid_df = validated.filter(col("error_reason").isNull()).drop("error_reason")
    rejected_df = validated.filter(col("error_reason").isNotNull())
    return valid_df, rejected_df