"""
Spark version of M08 (Event-Time Engine).

Batch approximation of streaming watermarking: since this runs once
over a fixed S3 dataset (not a live stream), we compute the watermark
as (max event_timestamp in this batch - allowed_lateness), then split
on-time vs late relative to that single watermark.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, max as spark_max, current_timestamp, unix_timestamp, lit, to_timestamp


def split_on_time_late(df: DataFrame, allowed_lateness_seconds: int = 300) -> tuple[DataFrame, DataFrame]:
    """
    Adds ingestion_timestamp (= now, simulating pipeline arrival time),
    computes a single watermark for this batch, and splits into
    (on_time_df, late_df).
    """
    # Convert the ISO-8601 string field into a real Spark timestamp type first —
    # unix_timestamp()/comparisons need this, they don't parse ISO strings directly.
    df = df.withColumn("_event_ts", to_timestamp(col("event_timestamp")))
    df = df.withColumn("ingestion_timestamp", current_timestamp())

    # Find the latest event_timestamp seen in this batch
    max_event_time = df.select(spark_max(col("_event_ts"))).first()[0]

    watermark_expr = unix_timestamp(lit(max_event_time)) - allowed_lateness_seconds

    df = df.withColumn(
        "processing_delay_seconds",
        unix_timestamp(col("ingestion_timestamp")) - unix_timestamp(col("_event_ts"))
    )

    on_time_df = df.filter(unix_timestamp(col("_event_ts")) >= watermark_expr).drop("_event_ts")
    late_df = df.filter(unix_timestamp(col("_event_ts")) < watermark_expr).drop("_event_ts")

    return on_time_df, late_df