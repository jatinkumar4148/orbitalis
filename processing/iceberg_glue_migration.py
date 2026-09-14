"""
Migrates the Iceberg catalog from Hadoop-type (local metadata files on
S3) to Glue-type (AWS Glue Data Catalog) — required because Athena can
only discover Iceberg tables through Glue, not through a Hadoop catalog.

This does NOT copy or rewrite any data files — it registers the
EXISTING table (same S3 location, same data/metadata files) into the
new Glue catalog, using Iceberg's built-in migration procedure.
"""

import os

os.environ["PYSPARK_PYTHON"] = r"C:\Users\User\orbitalis\venv_spark35\Scripts\python.exe"
os.environ["PYSPARK_DRIVER_PYTHON"] = r"C:\Users\User\orbitalis\venv_spark35\Scripts\python.exe"

from pyspark.sql import SparkSession

BUCKET = "orbitalis-data-jatin2026"
WAREHOUSE_PATH = f"s3a://{BUCKET}/iceberg_warehouse/"


def main():
    spark = SparkSession.builder \
        .appName("OrbitalisGlueMigration") \
        .master("local[2]") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.jars.packages",
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,"
                "org.apache.hadoop:hadoop-aws:3.3.4,"
                "com.amazonaws:aws-java-sdk-bundle:1.12.786,"
                "org.apache.iceberg:iceberg-aws-bundle:1.6.1") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        \
        .config("spark.sql.catalog.orbitalis_hadoop", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.orbitalis_hadoop.type", "hadoop") \
        .config("spark.sql.catalog.orbitalis_hadoop.warehouse", WAREHOUSE_PATH) \
        \
        .config("spark.sql.catalog.orbitalis_glue", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.orbitalis_glue.type", "glue") \
        .config("spark.sql.catalog.orbitalis_glue.warehouse", WAREHOUSE_PATH) \
        \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
        .config("spark.hadoop.fs.s3a.endpoint", "s3.ap-south-1.amazonaws.com") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    tables_to_migrate = [
        "silver_telemetry",
        "satellite_health_daily",
        "satellite_anomalies",
        "satellite_orbit_summary",
    ]

    for table_name in tables_to_migrate:
        print(f"\nRegistering {table_name} into Glue catalog...")

        metadata_file = spark.sql(
            f"""
            SELECT file
            FROM orbitalis_hadoop.orbitalis_db.{table_name}.metadata_log_entries
            ORDER BY timestamp DESC
            LIMIT 1
            """
        ).collect()[0]["file"]

        spark.sql(f"""
            CALL orbitalis_glue.system.register_table(
                table => 'orbitalis_glue_db.{table_name}',
                metadata_file => '{metadata_file}'
            )
        """)

        print(f"  Registered: {table_name}")

    spark.stop()


if __name__ == "__main__":
    main()