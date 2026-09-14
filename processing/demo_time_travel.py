"""
Demonstrates Iceberg time-travel: querying the table as it existed
at a PAST snapshot, before the schema evolution / any later writes.
"""

import os
os.environ["PYSPARK_PYTHON"] = r"C:\Users\User\orbitalis\venv_spark35\Scripts\python.exe"
os.environ["PYSPARK_DRIVER_PYTHON"] = r"C:\Users\User\orbitalis\venv_spark35\Scripts\python.exe"

from pyspark.sql import SparkSession

BUCKET = "orbitalis-data-jatin2026"
WAREHOUSE_PATH = f"s3a://{BUCKET}/iceberg_warehouse/"


def main():
    spark = SparkSession.builder \
        .appName("OrbitalisTimeTravel") \
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

    print("All available snapshots:")
    history = spark.sql("SELECT * FROM orbitalis.orbitalis_db.silver_telemetry.history")
    history.show(truncate=False)

    # Grab the FIRST (oldest) snapshot id to time-travel to
    first_snapshot_id = history.orderBy("made_current_at").first()["snapshot_id"]
    print(f"\nQuerying table AS OF the first snapshot: {first_snapshot_id}")

    spark.sql(f"""
        SELECT COUNT(*) as row_count_at_first_snapshot
        FROM orbitalis.orbitalis_db.silver_telemetry VERSION AS OF {first_snapshot_id}
    """).show()

    print("Current row count (latest snapshot):")
    spark.sql("SELECT COUNT(*) as row_count_now FROM orbitalis.orbitalis_db.silver_telemetry").show()

    spark.stop()


if __name__ == "__main__":
    main()