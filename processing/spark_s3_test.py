"""
Test connecting Spark to real S3 Bronze data.
Reads whatever Firehose has written to s3://<bucket>/bronze/telemetry/...
"""

from pyspark.sql import SparkSession


def main():
    spark = SparkSession.builder \
        .appName("OrbitalisS3Test") \
        .config("spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.5.0,"
                "com.amazonaws:aws-java-sdk-bundle:1.12.786") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
        .config("spark.hadoop.fs.s3a.endpoint", "s3.ap-south-1.amazonaws.com") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Change this to YOUR actual bucket name
    bronze_path = "s3a://orbitalis-data-jatin2026/bronze/telemetry/*/*/*/*/"

    print(f"\nReading from: {bronze_path}")
    df = spark.read.json(bronze_path)

    print(f"\nTotal records in S3 Bronze: {df.count()}")
    df.printSchema()
    df.select("satellite_id", "battery_voltage", "event_timestamp").show(10)

    spark.stop()


if __name__ == "__main__":
    main()