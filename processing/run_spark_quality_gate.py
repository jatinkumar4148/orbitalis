"""
Runs the Spark-based validation (M06) on local data, so we can verify
it produces the SAME results as the pure-Python quality gate (M07)
before ever pointing it at Kinesis/S3.
"""

from pyspark.sql import SparkSession

from processing.spark_validation import split_valid_invalid


def main():
    spark = SparkSession.builder.appName("OrbitalisSparkQualityGate").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # Read the RAW events (before quality filtering) — same input M07 uses
    df = spark.read.json("./data/local_events.jsonl")

    total = df.count()
    valid_df, rejected_df = split_valid_invalid(df)

    valid_count = valid_df.count()
    rejected_count = rejected_df.count()

    print(f"\nTotal: {total}, Valid: {valid_count}, Rejected: {rejected_count}")

    print("\n=== Sample of REJECTED rows with reasons ===")
    rejected_df.select("satellite_id", "error_reason").show(20, truncate=False)

    # Save results for comparison / next stages
    valid_df.write.mode("overwrite").json("./data/spark_valid_events")
    rejected_df.write.mode("overwrite").json("./data/spark_rejected_events")

    spark.stop()


if __name__ == "__main__":
    main()