"""
Demonstrates Iceberg's schema evolution: adding a new column to an
EXISTING table without rewriting any data files. This is one of
Iceberg's core selling points over plain Parquet/JSON.
"""

import os
os.environ["PYSPARK_PYTHON"] = r"C:\Users\User\orbitalis\venv_spark35\Scripts\python.exe"
os.environ["PYSPARK_DRIVER_PYTHON"] = r"C:\Users\User\orbitalis\venv_spark35\Scripts\python.exe"

from pyspark.sql import SparkSession

BUCKET = "orbitalis-data-jatin2026"
WAREHOUSE_PATH = f"s3a://{BUCKET}/iceberg_warehouse/"


def main():
    spark = SparkSession.builder \
        .appName("OrbitalisSchemaEvolution") \
        .config("spark.jars.packages",
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,"
                "org.apache.hadoop:hadoop-aws:3.3.4,"
                "com.amazonaws:aws-java-sdk-bundle:1.12.786") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.orbitalis", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.orbitalis.type", "hadoop") \
        .config("spark.sql.catalog.orbitalis.warehouse", WAREHOUSE_PATH) \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
        .config("spark.hadoop.fs.s3a.endpoint", "s3.ap-south-1.amazonaws.com") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    print("Schema BEFORE:")
    spark.sql("DESCRIBE orbitalis.orbitalis_db.silver_telemetry").show(50, truncate=False)

    print("\nAdding a new column 'data_quality_score' (no data rewrite happens)...")
    spark.sql("""
        ALTER TABLE orbitalis.orbitalis_db.silver_telemetry
        ADD COLUMN data_quality_score DOUBLE
    """)

    print("\nSchema AFTER:")
    spark.sql("DESCRIBE orbitalis.orbitalis_db.silver_telemetry").show(50, truncate=False)

    print("\nOld rows automatically show NULL for the new column (no rewrite needed):")
    spark.sql("""
        SELECT satellite_id, battery_voltage, data_quality_score
        FROM orbitalis.orbitalis_db.silver_telemetry
        LIMIT 5
    """).show()

    spark.stop()


if __name__ == "__main__":
    main()