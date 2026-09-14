"""
Builds the 3 Gold tables from the Silver Iceberg table.

Gold tables:
    - satellite_health_daily
    - satellite_anomalies
    - satellite_orbit_summary

Rule-based thresholds:
    - Battery < 28V  -> WARNING
    - Battery < 24V  -> CRITICAL
    - Temperature > 70C -> CRITICAL
    - Fuel < 10% -> WARNING
"""

import os

# ============================================================
# PYTHON ENVIRONMENT
# ============================================================

os.environ["PYSPARK_PYTHON"] = (
    r"C:\Users\User\orbitalis\venv_spark35\Scripts\python.exe"
)

os.environ["PYSPARK_DRIVER_PYTHON"] = (
    r"C:\Users\User\orbitalis\venv_spark35\Scripts\python.exe"
)


# ============================================================
# IMPORTS
# ============================================================

from pyspark.sql import SparkSession

from pyspark.sql.functions import (
    col,
    to_date,
    avg,
    min as spark_min,
    max as spark_max,
    count,
    when,
    lit,
)


# ============================================================
# CONFIGURATION
# ============================================================

BUCKET = "orbitalis-data-jatin2026"

WAREHOUSE_PATH = f"s3a://{BUCKET}/iceberg_warehouse/"


# ============================================================
# CREATE SPARK SESSION
# ============================================================

def get_spark():

    spark = (
        SparkSession.builder

        # Windows local Spark
        .master("local[2]")

        .appName("OrbitalisGoldTables")

        # Fix Spark driver networking on Windows
        .config(
            "spark.driver.host",
            "127.0.0.1"
        )

        .config(
            "spark.driver.bindAddress",
            "127.0.0.1"
        )

        # Fixed temporary directory
        # Prevents Windows Spark JAR staging problems
        .config(
            "spark.local.dir",
            "C:/spark-temp"
        )

        # ====================================================
        # REQUIRED JARS
        # ====================================================

        .config(
            "spark.jars.packages",
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.786",
        )

        # ====================================================
        # ICEBERG CONFIGURATION
        # ====================================================

        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
        )

        .config(
            "spark.sql.catalog.orbitalis",
            "org.apache.iceberg.spark.SparkCatalog"
        )

        .config(
            "spark.sql.catalog.orbitalis.type",
            "hadoop"
        )

        .config(
            "spark.sql.catalog.orbitalis.warehouse",
            WAREHOUSE_PATH
        )

        # ====================================================
        # AWS S3 CONFIGURATION
        # ====================================================

        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "com.amazonaws.auth.DefaultAWSCredentialsProviderChain"
        )

        .config(
            "spark.hadoop.fs.s3a.endpoint",
            "s3.ap-south-1.amazonaws.com"
        )

        # ====================================================
        # PERFORMANCE
        # ====================================================

        .config(
            "spark.sql.shuffle.partitions",
            "4"
        )

        .getOrCreate()
    )

    return spark


# ============================================================
# GOLD TABLE 1
# SATELLITE HEALTH DAILY
# ============================================================

def build_health_daily(spark, silver_df):

    print()
    print("=" * 60)
    print("BUILDING: satellite_health_daily")
    print("=" * 60)

    # Convert timestamp into date
    daily = (
        silver_df

        .withColumn(
            "event_date",
            to_date(col("event_timestamp"))
        )

        # Group by satellite and date
        .groupBy(
            "satellite_id",
            "event_date"
        )

        # Daily health metrics
        .agg(

            avg(
                "battery_voltage"
            ).alias(
                "avg_battery_voltage"
            ),

            spark_min(
                "battery_voltage"
            ).alias(
                "min_battery_voltage"
            ),

            spark_max(
                "battery_temperature"
            ).alias(
                "max_temperature"
            ),

            avg(
                "battery_temperature"
            ).alias(
                "avg_temperature"
            ),

            avg(
                "signal_strength"
            ).alias(
                "avg_signal_strength"
            ),

            count("*").alias(
                "event_count"
            ),
        )
    )

    print()
    print("Writing satellite_health_daily...")

    daily.writeTo(
        "orbitalis.orbitalis_db.satellite_health_daily"
    ).createOrReplace()

    print(
        "satellite_health_daily: WRITE SUCCESS"
    )


# ============================================================
# GOLD TABLE 2
# SATELLITE ANOMALIES
# ============================================================

def build_anomalies(spark, silver_df):

    print()
    print("=" * 60)
    print("BUILDING: satellite_anomalies")
    print("=" * 60)

    anomalies = (
        silver_df

        # Select only required columns
        .select(
            "satellite_id",
            "event_timestamp",
            "battery_voltage",
            "battery_temperature",
            "fuel_level",
        )

        # Determine anomaly type
        .withColumn(

            "anomaly_type",

            when(
                col("battery_voltage") < 24,
                lit("BATTERY_CRITICAL")
            )

            .when(
                col("battery_voltage") < 28,
                lit("BATTERY_WARNING")
            )

            .when(
                col("battery_temperature") > 70,
                lit("TEMPERATURE_CRITICAL")
            )

            .when(
                col("fuel_level") < 10,
                lit("FUEL_WARNING")
            )

            .otherwise(
                lit(None)
            )
        )

        # Keep only anomalous records
        .filter(
            col("anomaly_type").isNotNull()
        )

        # Determine severity
        .withColumn(

            "severity",

            when(

                col("anomaly_type").isin(
                    "BATTERY_CRITICAL",
                    "TEMPERATURE_CRITICAL",
                ),

                lit("CRITICAL")
            )

            .otherwise(
                lit("WARNING")
            )
        )
    )

    print()
    print("Writing satellite_anomalies...")

    anomalies.writeTo(
        "orbitalis.orbitalis_db.satellite_anomalies"
    ).createOrReplace()

    print(
        "satellite_anomalies: WRITE SUCCESS"
    )


# ============================================================
# GOLD TABLE 3
# SATELLITE ORBIT SUMMARY
# ============================================================

def build_orbit_summary(spark, silver_df):

    print()
    print("=" * 60)
    print("BUILDING: satellite_orbit_summary")
    print("=" * 60)

    orbit = (
        silver_df

        # Convert timestamp to date
        .withColumn(
            "event_date",
            to_date(col("event_timestamp"))
        )

        # Group by satellite and date
        .groupBy(
            "satellite_id",
            "event_date"
        )

        # Orbit metrics
        .agg(

            avg(
                "altitude_km"
            ).alias(
                "avg_altitude"
            ),

            spark_min(
                "altitude_km"
            ).alias(
                "min_altitude"
            ),

            spark_max(
                "altitude_km"
            ).alias(
                "max_altitude"
            ),

            avg(
                "velocity_kmh"
            ).alias(
                "avg_velocity"
            ),
        )
    )

    print()
    print("Writing satellite_orbit_summary...")

    orbit.writeTo(
        "orbitalis.orbitalis_db.satellite_orbit_summary"
    ).createOrReplace()

    print(
        "satellite_orbit_summary: WRITE SUCCESS"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("ORBITALIS - GOLD TABLE BUILD")
    print("=" * 60)

    spark = get_spark()

    # Reduce unnecessary Spark logs
    spark.sparkContext.setLogLevel("WARN")

    print()
    print("Spark version:", spark.version)

    # ========================================================
    # READ SILVER ICEBERG TABLE
    # ========================================================

    print()
    print("Reading Silver Iceberg table...")

    silver_df = spark.table(
        "orbitalis.orbitalis_db.silver_telemetry"
    )

    print(
        "Silver Iceberg table loaded successfully."
    )

    # IMPORTANT:
    # Do NOT call silver_df.count() here.
    # Windows Spark previously crashed during count().
    #
    # The table can be resolved/read successfully without
    # performing this diagnostic action.

    # ========================================================
    # BUILD GOLD TABLE 1
    # ========================================================

    build_health_daily(
        spark,
        silver_df
    )

    # ========================================================
    # BUILD GOLD TABLE 2
    # ========================================================

    build_anomalies(
        spark,
        silver_df
    )

    # ========================================================
    # BUILD GOLD TABLE 3
    # ========================================================

    build_orbit_summary(
        spark,
        silver_df
    )

    # ========================================================
    # SAMPLE ANOMALIES
    # ========================================================

    print()
    print("=" * 60)
    print("SAMPLE FROM satellite_anomalies")
    print("=" * 60)

    spark.sql(
        """
        SELECT *
        FROM orbitalis.orbitalis_db.satellite_anomalies
        LIMIT 10
        """
    ).show(
        truncate=False
    )

    # ========================================================
    # SUCCESS
    # ========================================================

    print()
    print("=" * 60)
    print("ALL 3 GOLD TABLES CREATED SUCCESSFULLY")
    print("=" * 60)

    # ========================================================
    # STOP SPARK
    # ========================================================

    spark.stop()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()