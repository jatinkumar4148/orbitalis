"""
Checkpointed Structured Streaming pipeline — FULL version with
validate + watermark + dedup, all streaming-native.

Key differences from batch (run_s3_pipeline.py):

- Checkpointing means old Bronze files are never reprocessed.

- Dedup uses Spark's native streaming dedup (withWatermark +
  dropDuplicatesWithinWatermark), which SILENTLY drops duplicates —
  this matches real production streaming semantics. We don't get a
  separate "duplicates" file for free the way batch mode gave us;
  that would require custom state tracking, which is out of scope.

- Late-vs-on-time split is still a simple per-record filter (stateless,
  works fine per-microbatch).
"""

import os

os.environ["PYSPARK_PYTHON"] = r"C:\Users\User\orbitalis\venv\Scripts\python.exe"
os.environ["PYSPARK_DRIVER_PYTHON"] = r"C:\Users\User\orbitalis\venv\Scripts\python.exe"

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, to_timestamp, unix_timestamp

from processing.bronze_schema import BRONZE_SCHEMA
from processing.spark_validation import split_valid_invalid

# M14 Step 4 — CloudWatch custom metrics
from processing.cloudwatch_client import put_pipeline_metrics


BUCKET = "orbitalis-data-jatin2026"

BRONZE_PATH = f"s3a://{BUCKET}/bronze/telemetry/"
CHECKPOINT_PATH = f"s3a://{BUCKET}/checkpoints/bronze_to_silver/"
SILVER_PATH = f"s3a://{BUCKET}/silver/telemetry/"
REJECTED_PATH = f"s3a://{BUCKET}/rejected/telemetry/"
LATE_PATH = f"s3a://{BUCKET}/late/telemetry/"

ALLOWED_LATENESS_SECONDS = 300  # 5 minutes, same as before


def process_batch(batch_df, batch_id: int):
    """
    Called once per micro-batch of NEW, ALREADY-DEDUPED rows
    (dedup happens upstream, before foreachBatch, via the streaming
    dropDuplicatesWithinWatermark operator).
    """

    if batch_df.isEmpty():
        print(f"[batch {batch_id}] No new files. Skipping.")
        return

    total = batch_df.count()

    # ── Validate ──────────────────────────────────────────────
    valid_df, rejected_df = split_valid_invalid(batch_df)

    # ── Late vs on-time (simple stateless filter) ───────────────
    valid_df = valid_df.withColumn(
        "ingestion_timestamp",
        current_timestamp()
    )

    valid_df = valid_df.withColumn(
        "processing_delay_seconds",
        unix_timestamp(col("ingestion_timestamp"))
        - unix_timestamp(col("_event_ts"))
    )

    on_time_df = valid_df.filter(
        col("processing_delay_seconds") <= ALLOWED_LATENESS_SECONDS
    ).drop("_event_ts")

    late_df = valid_df.filter(
        col("processing_delay_seconds") > ALLOWED_LATENESS_SECONDS
    ).drop("_event_ts")

    valid_count = valid_df.count()
    rejected_count = rejected_df.count()
    on_time_count = on_time_df.count()
    late_count = late_df.count()

    print(
        f"[batch {batch_id}] New (post-dedup): {total} | Valid: {valid_count} | "
        f"Rejected: {rejected_count} | On-time: {on_time_count} | Late: {late_count}"
    )

    # ── M14 Step 4: Push batch metrics to CloudWatch ───────────
    put_pipeline_metrics(
        valid=valid_count,
        rejected=rejected_count,
        late=late_count,
        total=total
    )

    on_time_df.write.mode("append").json(SILVER_PATH)
    rejected_df.write.mode("append").json(REJECTED_PATH)
    late_df.write.mode("append").json(LATE_PATH)


def main():

    spark = SparkSession.builder \
        .appName("OrbitalisStreamingPipelineFull") \
        .config("spark.sql.shuffle.partitions", "4") \
        .config(
            "spark.jars.packages",
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.786"
        ) \
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "com.amazonaws.auth.DefaultAWSCredentialsProviderChain"
        ) \
        .config(
            "spark.hadoop.fs.s3a.endpoint",
            "s3.ap-south-1.amazonaws.com"
        ) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    bronze_stream = spark.readStream \
        .schema(BRONZE_SCHEMA) \
        .json(BRONZE_PATH)

    # Parse event_timestamp string into a real timestamp column,
    # set the watermark on it, then dedup by event_id WITHIN that
    # watermark window.
    #
    # This is Spark's native streaming dedup — duplicates outside the
    # watermark window are silently dropped, matching real production behavior.

    deduped_stream = bronze_stream \
        .withColumn(
            "_event_ts",
            to_timestamp(col("event_timestamp"))
        ) \
        .withWatermark(
            "_event_ts",
            f"{ALLOWED_LATENESS_SECONDS} seconds"
        ) \
        .dropDuplicatesWithinWatermark(["event_id"])

    query = deduped_stream.writeStream \
        .foreachBatch(process_batch) \
        .option(
            "checkpointLocation",
            CHECKPOINT_PATH
        ) \
        .trigger(availableNow=True) \
        .start()

    query.awaitTermination()

    print("\nStreaming run complete — all available new files processed.")

    spark.stop()


if __name__ == "__main__":
    main()