import os
import sys
import pytest
from pyspark.sql import SparkSession
@pytest.fixture(scope="session")
def spark_session():
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("OrbitalisTest")
        .config("spark.pyspark.python", sys.executable)
        .config("spark.pyspark.driver.python", sys.executable)
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")

    yield spark

    spark.stop()


def valid_event():
    return {
        "event_id": "TEST-001",
        "satellite_id": "SAT-001",
        "event_timestamp": "2026-09-11T10:00:00",
        "latitude": 28.61,
        "longitude": 77.21,
        "altitude_km": 500.0,
        "velocity_kmh": 27000.0,
        "battery_voltage": 28.0,
        "battery_temperature": 25.0,
        "solar_current": 10.0,
        "fuel_level": 80.0,
        "radiation_level": 2.0,
        "gyro_x": 0.1,
        "gyro_y": 0.1,
        "gyro_z": 0.1,
        "signal_strength": -70.0,
        "communication_status": "OK",
        "schema_version": "1.0",
    }


def test_spark_validation_accepts_valid_event(spark_session):
    from processing.spark_validation import split_valid_invalid

    df = spark_session.createDataFrame([valid_event()])

    valid_df, rejected_df = split_valid_invalid(df)

    assert valid_df.count() == 1
    assert rejected_df.count() == 0


def test_spark_validation_rejects_out_of_range_latitude(spark_session):
    from processing.spark_validation import split_valid_invalid

    event = valid_event()
    event["latitude"] = 400.0

    df = spark_session.createDataFrame([event])

    valid_df, rejected_df = split_valid_invalid(df)

    assert valid_df.count() == 0
    assert rejected_df.count() == 1

    assert rejected_df.select("error_reason").first()[0] == "latitude_out_of_range"


def test_spark_validation_rejects_missing_required_field(spark_session):
    from processing.spark_validation import split_valid_invalid
    from processing.bronze_schema import BRONZE_SCHEMA

    event = valid_event()
    event["latitude"] = None

    df = spark_session.createDataFrame([event], schema=BRONZE_SCHEMA)

    valid_df, rejected_df = split_valid_invalid(df)

    assert valid_df.count() == 0
    assert rejected_df.count() == 1


def test_spark_event_time_splits_late_event(spark_session):
    from processing.spark_event_time import split_on_time_late

    events = [
        {
            **valid_event(),
            "event_id": "EVENT-1",
            "event_timestamp": "2026-09-11T10:00:00",
        },
        {
            **valid_event(),
            "event_id": "EVENT-2",
            "event_timestamp": "2026-09-11T09:00:00",
        },
    ]

    df = spark_session.createDataFrame(events)

    on_time_df, late_df = split_on_time_late(
        df,
        allowed_lateness_seconds=300,
    )

    assert on_time_df.count() == 1
    assert late_df.count() == 1


def test_spark_event_time_keeps_recent_event_on_time(spark_session):
    from processing.spark_event_time import split_on_time_late

    events = [
        {
            **valid_event(),
            "event_id": "EVENT-1",
            "event_timestamp": "2026-09-11T10:00:00",
        },
        {
            **valid_event(),
            "event_id": "EVENT-2",
            "event_timestamp": "2026-09-11T09:58:00",
        },
    ]

    df = spark_session.createDataFrame(events)

    on_time_df, late_df = split_on_time_late(
        df,
        allowed_lateness_seconds=300,
    )

    assert on_time_df.count() == 2
    assert late_df.count() == 0


def test_bronze_schema_has_expected_fields():
    from processing.bronze_schema import BRONZE_SCHEMA

    expected_fields = [
        "event_id",
        "satellite_id",
        "event_timestamp",
        "latitude",
        "longitude",
        "altitude_km",
        "velocity_kmh",
        "battery_voltage",
        "battery_temperature",
        "solar_current",
        "fuel_level",
        "radiation_level",
        "gyro_x",
        "gyro_y",
        "gyro_z",
        "signal_strength",
        "communication_status",
        "schema_version",
    ]

    assert BRONZE_SCHEMA.fieldNames() == expected_fields
    assert len(BRONZE_SCHEMA.fields) == 18