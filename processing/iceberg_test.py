"""
Sanity check: can Spark talk to Iceberg tables on S3?

Uses a Hadoop-based Iceberg catalog (metadata stored directly on S3,
no AWS Glue Catalog needed) — simpler setup for now. See ADR in
docs/decisions.md for why, and how to upgrade to Glue Catalog later.
"""

import os
os.environ["PYSPARK_PYTHON"] = r"C:\Users\User\orbitalis\venv\Scripts\python.exe"
os.environ["PYSPARK_DRIVER_PYTHON"] = r"C:\Users\User\orbitalis\venv\Scripts\python.exe"

from pyspark.sql import SparkSession

BUCKET = "orbitalis-data-jatin2026"
WAREHOUSE_PATH = f"s3a://{BUCKET}/iceberg_warehouse/"


def main():
    spark = SparkSession.builder \
        .appName("OrbitalisIcebergTest") \
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

    print("\nCreating a test Iceberg table...")
    spark.sql("""
        CREATE TABLE IF NOT EXISTS orbitalis.test_db.sanity_check (
            id INT,
            message STRING
        ) USING iceberg
    """)

    print("Inserting a row...")
    spark.sql("INSERT INTO orbitalis.test_db.sanity_check VALUES (1, 'Iceberg is working')")

    print("\nReading it back:")
    spark.sql("SELECT * FROM orbitalis.test_db.sanity_check").show()

    print("\nTable history (Iceberg-specific metadata):")
    spark.sql("SELECT * FROM orbitalis.test_db.sanity_check.history").show()

    spark.stop()


if __name__ == "__main__":
    main()