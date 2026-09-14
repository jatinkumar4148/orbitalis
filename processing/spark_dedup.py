"""
Spark version of M09 (Deduplication).

Uses Spark's window functions to keep only the FIRST occurrence of each
event_id (ordered by ingestion_timestamp), and routes any later
duplicates to a separate DataFrame — mirroring the local DeduplicationTracker
logic but expressed as a distributed operation.
"""

from pyspark.sql import DataFrame
from pyspark.sql import Window
from pyspark.sql.functions import col, row_number


def split_deduped_duplicates(df: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Returns (deduped_df, duplicates_df) based on event_id."""
    window_spec = Window.partitionBy("event_id").orderBy(col("ingestion_timestamp"))

    ranked_df = df.withColumn("_rank", row_number().over(window_spec))

    deduped_df = ranked_df.filter(col("_rank") == 1).drop("_rank")
    duplicates_df = ranked_df.filter(col("_rank") > 1).drop("_rank")

    return deduped_df, duplicates_df