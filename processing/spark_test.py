from pyspark.sql import SparkSession

def main():
    spark = SparkSession.builder \
        .appName("OrbitalisSparkTest") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")  # kam verbose logs, sirf warnings/errors dikhega

    # Local JSONL file padhte hain (Module 2 ka simulator output)
    df = spark.read.json("./data/valid_events.jsonl")

    print("\n=== Schema ===")
    df.printSchema()

    print("\n=== Row count ===")
    print(f"Total events: {df.count()}")

    print("\n=== Sample rows ===")
    df.select("satellite_id", "battery_voltage", "communication_status").show(5)

    print("\n=== Average battery voltage per satellite ===")
    df.groupBy("satellite_id").avg("battery_voltage").show()

    spark.stop()


if __name__ == "__main__":
    main()