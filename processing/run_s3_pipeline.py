"""
The FULL Module 6 pipeline on real S3 data:

  S3 Bronze
     -> Validate (M07 logic)          -> valid / rejected
     -> Watermark (M08 logic)          -> on-time / late
     -> Dedup (M09 logic)              -> deduped / duplicates
     -> S3 Silver (final clean output)

This is the batch-mode equivalent of what a continuous Glue Streaming
job would do on each micro-batch.
"""

from pyspark.sql import SparkSession

from processing.spark_validation import split_valid_invalid
from processing.spark_event_time import split_on_time_late
from processing.spark_dedup import split_deduped_duplicates


BUCKET = "orbitalis-data-jatin2026"
BRONZE_PATH = f"s3a://{BUCKET}/bronze/telemetry/*/*/*/*/"

SILVER_PATH = f"s3a://{BUCKET}/silver/telemetry/"
REJECTED_PATH = f"s3a://{BUCKET}/rejected/telemetry/"
LATE_PATH = f"s3a://{BUCKET}/late/telemetry/"
DUPLICATES_PATH = f"s3a://{BUCKET}/duplicates/telemetry/"


def main():
    spark = SparkSession.builder \
        .appName("OrbitalisFullS3Pipeline") \
        .config("spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.5.0,"
                "com.amazonaws:aws-java-sdk-bundle:1.12.786") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
        .config("spark.hadoop.fs.s3a.endpoint", "s3.ap-south-1.amazonaws.com") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # ── Stage 1: Read Bronze ──────────────────────────────────
    print(f"\n[1/4] Reading Bronze from: {BRONZE_PATH}")
    df = spark.read.json(BRONZE_PATH)
    total = df.count()
    print(f"    Total: {total}")

    # ── Stage 2: Validate ──────────────────────────────────────
    print("\n[2/4] Validating...")
    valid_df, rejected_df = split_valid_invalid(df)
    valid_count = valid_df.count()
    rejected_count = rejected_df.count()
    print(f"    Valid: {valid_count}, Rejected: {rejected_count}")

    # ── Stage 3: Watermark (on valid data only) ─────────────────
    print("\n[3/4] Applying watermark...")
    on_time_df, late_df = split_on_time_late(valid_df, allowed_lateness_seconds=300)
    on_time_count = on_time_df.count()
    late_count = late_df.count()
    print(f"    On-time: {on_time_count}, Late: {late_count}")

    # ── Stage 4: Dedup (on on-time data only) ───────────────────
    print("\n[4/4] Deduplicating...")
    deduped_df, duplicates_df = split_deduped_duplicates(on_time_df)
    deduped_count = deduped_df.count()
    duplicates_count = duplicates_df.count()
    print(f"    Deduped (final): {deduped_count}, Duplicates removed: {duplicates_count}")

    # ── Write all outputs to S3 ──────────────────────────────────
    print("\nWriting outputs to S3...")
    deduped_df.write.mode("overwrite").json(SILVER_PATH)
    rejected_df.write.mode("overwrite").json(REJECTED_PATH)
    late_df.write.mode("overwrite").json(LATE_PATH)
    duplicates_df.write.mode("overwrite").json(DUPLICATES_PATH)

    # ── Final summary ─────────────────────────────────────────
    print("\n" + "=" * 50)
    print("S3 PIPELINE COMPLETE")
    print(f"  Bronze (raw):          {total}")
    print(f"  Valid (passed QC):     {valid_count}")
    print(f"  Rejected:              {rejected_count}")
    print(f"  On-time:               {on_time_count}")
    print(f"  Late:                  {late_count}")
    print(f"  Final Silver (clean):  {deduped_count}")
    print(f"  Duplicates removed:    {duplicates_count}")
    print("=" * 50)

    spark.stop()


if __name__ == "__main__":
    main()