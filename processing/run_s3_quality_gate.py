"""
The REAL Module 6 end-to-end test:

  S3 Bronze  --(Spark reads)-->  Validation  --(Spark writes)-->  S3 Silver / Rejected

This is different from run_spark_quality_gate.py (which reads a LOCAL
file, kept only for quick local testing) and spark_s3_test.py (which
reads S3 but does not validate). This file does the full real thing.
"""

from pyspark.sql import SparkSession

from processing.spark_validation import split_valid_invalid


# CHANGE THIS to your actual bucket name
BUCKET = "orbitalis-data-jatin2026"
BRONZE_PATH = f"s3a://{BUCKET}/bronze/telemetry/*/*/*/*/"
SILVER_PATH = f"s3a://{BUCKET}/silver/telemetry/"
REJECTED_PATH = f"s3a://{BUCKET}/rejected/telemetry/"


def main():
    spark = SparkSession.builder \
        .appName("OrbitalisS3QualityGate") \
        .config("spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.5.0,"
                "com.amazonaws:aws-java-sdk-bundle:1.12.786") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
        .config("spark.hadoop.fs.s3a.endpoint", "s3.ap-south-1.amazonaws.com") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    print(f"\nReading Bronze from: {BRONZE_PATH}")
    df = spark.read.json(BRONZE_PATH)

    total = df.count()
    print(f"Total records read from S3 Bronze: {total}")

    valid_df, rejected_df = split_valid_invalid(df)
    valid_count = valid_df.count()
    rejected_count = rejected_df.count()

    print(f"\nValid: {valid_count}, Rejected: {rejected_count}")

    print("\n=== Rejected rows with reasons ===")
    rejected_df.select("satellite_id", "error_reason").show(50, truncate=False)

    # Write results BACK to S3 — this is the first real Silver layer output
    print(f"\nWriting valid events to: {SILVER_PATH}")
    valid_df.write.mode("overwrite").json(SILVER_PATH)

    print(f"Writing rejected events to: {REJECTED_PATH}")
    rejected_df.write.mode("overwrite").json(REJECTED_PATH)

    print("\nDone.")
    spark.stop()


if __name__ == "__main__":
    main()