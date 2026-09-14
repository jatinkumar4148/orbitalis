"""
Converts the existing Silver JSON files (written by M06's streaming
pipeline) into a proper Iceberg table.

This is a ONE-TIME batch conversion of what's already in S3 — it reads
the plain JSON Silver output and writes it into the Iceberg table
defined in iceberg_silver_schema.py. Going forward, M06's streaming
pipeline could be pointed to write directly into this Iceberg table
instead of plain JSON (a future improvement, not required for this
module's goal of proving Iceberg works end-to-end on our real data).
"""

import os

os.environ["PYSPARK_PYTHON"] = (
    r"C:\Users\User\orbitalis\venv_spark35\Scripts\python.exe"
)

os.environ["PYSPARK_DRIVER_PYTHON"] = (
    r"C:\Users\User\orbitalis\venv_spark35\Scripts\python.exe"
)

from pyspark.sql import SparkSession
from pyspark.sql.functions import to_timestamp

from processing.iceberg_silver_schema import SILVER_TABLE_DDL


BUCKET = "orbitalis-data-jatin2026"

SILVER_JSON_PATH = f"s3a://{BUCKET}/silver/telemetry/"

WAREHOUSE_PATH = f"s3a://{BUCKET}/iceberg_warehouse/"


def main():

    # ─────────────────────────────────────────────────────────
    # Spark + Iceberg Configuration
    # ─────────────────────────────────────────────────────────

    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("OrbitalisSilverToIceberg")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config(
            "spark.jars.packages",
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.786",
        )
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config(
            "spark.sql.catalog.orbitalis",
            "org.apache.iceberg.spark.SparkCatalog",
        )
        .config(
            "spark.sql.catalog.orbitalis.type",
            "hadoop",
        )
        .config(
            "spark.sql.catalog.orbitalis.warehouse",
            WAREHOUSE_PATH,
        )
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
        )
        .config(
            "spark.hadoop.fs.s3a.endpoint",
            "s3.ap-south-1.amazonaws.com",
        )
        .config(
            "spark.sql.shuffle.partitions",
            "4",
        )
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    # ─────────────────────────────────────────────────────────
    # Step 1: Create Database + Iceberg Table
    # ─────────────────────────────────────────────────────────

    spark.sql(
        "CREATE DATABASE IF NOT EXISTS orbitalis.orbitalis_db"
    )

    spark.sql(SILVER_TABLE_DDL)

    # ─────────────────────────────────────────────────────────
    # Step 2: Read Existing Silver JSON
    # ─────────────────────────────────────────────────────────

    print(
        f"\nReading Silver JSON from: {SILVER_JSON_PATH}"
    )

    df = spark.read.json(SILVER_JSON_PATH)

    total = df.count()

    print(
        f"Total Silver records found: {total}"
    )

    # ingestion_timestamp comes in as a string from JSON.
    # Convert it to a real Spark TIMESTAMP.
    df = df.withColumn(
        "ingestion_timestamp",
        to_timestamp("ingestion_timestamp"),
    )

    # ─────────────────────────────────────────────────────────
    # Step 3: Select Only Iceberg Silver Table Columns
    # ─────────────────────────────────────────────────────────
    #
    # The Silver JSON also contains partition/helper columns:
    #
    #   year
    #   month
    #   day
    #   hour
    #
    # These columns are NOT part of the Iceberg Silver schema.
    # Therefore, select only the 20 columns defined by the
    # Iceberg table before writing.
    # ─────────────────────────────────────────────────────────

    silver_columns = [
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
        "ingestion_timestamp",
        "processing_delay_seconds",
    ]

    df = df.select(silver_columns)

    print(
        f"Columns prepared for Iceberg: {len(df.columns)}"
    )

    print("Iceberg columns:")

    print(df.columns)

    # ─────────────────────────────────────────────────────────
    # Step 4: Write Into Iceberg Table
    # ─────────────────────────────────────────────────────────

    print(
        "\nWriting into Iceberg table "
        "orbitalis.orbitalis_db.silver_telemetry ..."
    )

    df.writeTo(
        "orbitalis.orbitalis_db.silver_telemetry"
    ).append()

    # ─────────────────────────────────────────────────────────
    # Step 5: Verify
    # ─────────────────────────────────────────────────────────

    result_count = (
        spark.sql(
            """
            SELECT COUNT(*) AS cnt
            FROM orbitalis.orbitalis_db.silver_telemetry
            """
        )
        .collect()[0]["cnt"]
    )

    print(
        f"\nRecords now in Iceberg table: {result_count}"
    )

    print("\nSample rows:")

    spark.sql(
        """
        SELECT
            satellite_id,
            battery_voltage,
            event_timestamp
        FROM orbitalis.orbitalis_db.silver_telemetry
        LIMIT 5
        """
    ).show()

    # ─────────────────────────────────────────────────────────
    # Stop Spark
    # ─────────────────────────────────────────────────────────

    spark.stop()


if __name__ == "__main__":
    main()
    