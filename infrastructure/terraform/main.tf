terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-south-1"
}

# ============================================================
# S3
# ============================================================

resource "aws_s3_bucket" "orbitalis_data" {
  bucket = "orbitalis-data-jatin2026"
}

# ============================================================
# KINESIS
# ============================================================

resource "aws_kinesis_stream" "orbitalis_telemetry" {
  name = "orbitalis-telemetry-stream"

  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }

  retention_period = 24

  encryption_type = "KMS"
  kms_key_id      = "alias/aws/kinesis"
}

# ============================================================
# KINESIS FIREHOSE
# ============================================================

resource "aws_kinesis_firehose_delivery_stream" "orbitalis_bronze" {
  name        = "orbitalis-bronze-firehose"
  destination = "extended_s3"

  kinesis_source_configuration {
    kinesis_stream_arn = "arn:aws:kinesis:ap-south-1:390663897017:stream/orbitalis-telemetry-stream"

    role_arn = "arn:aws:iam::390663897017:role/service-role/KinesisFirehoseServiceRole-orbitalis-br-ap-south-1-1786871751427"
  }

  extended_s3_configuration {
    role_arn = "arn:aws:iam::390663897017:role/service-role/KinesisFirehoseServiceRole-orbitalis-br-ap-south-1-1786871751427"

    bucket_arn = "arn:aws:s3:::orbitalis-data-jatin2026"

    prefix = "bronze/telemetry/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"

    error_output_prefix = "bronze-errors/telemetry/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/!{firehose:error-output-type}/"

    buffering_size     = 5
    buffering_interval = 300

    compression_format = "UNCOMPRESSED"

    processing_configuration {
      enabled = true

      processors {
        type = "AppendDelimiterToRecord"
      }
    }

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = "/aws/kinesisfirehose/orbitalis-bronze-firehose"
      log_stream_name = "DestinationDelivery"
    }
  }
}

# ============================================================
# GLUE DATABASE
# ============================================================

resource "aws_glue_catalog_database" "orbitalis_glue_db" {
  name        = "orbitalis_glue_db"
  description = "AWS Glue Data Catalog database for Orbitalis Iceberg tables"
}

# ============================================================
# GLUE TABLE - SILVER TELEMETRY
# ============================================================

resource "aws_glue_catalog_table" "silver_telemetry" {
  database_name = aws_glue_catalog_database.orbitalis_glue_db.name
  name          = "silver_telemetry"
  table_type    = "EXTERNAL_TABLE"

  storage_descriptor {
    location      = "s3a://orbitalis-data-jatin2026/iceberg_warehouse/orbitalis_db/silver_telemetry"
    columns {
      name = "event_id"
      type = "string"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "1"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "satellite_id"
      type = "string"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "2"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "event_timestamp"
      type = "string"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "3"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "latitude"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "4"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "longitude"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "5"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "altitude_km"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "6"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "velocity_kmh"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "7"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "battery_voltage"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "8"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "battery_temperature"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "9"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "solar_current"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "10"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "fuel_level"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "11"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "radiation_level"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "12"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "gyro_x"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "13"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "gyro_y"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "14"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "gyro_z"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "15"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "signal_strength"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "16"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "communication_status"
      type = "string"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "17"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "schema_version"
      type = "string"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "18"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "ingestion_timestamp"
      type = "timestamp"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "19"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "processing_delay_seconds"
      type = "bigint"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "20"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "data_quality_score"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "21"
        "iceberg.field.optional" = "true"
      }
    }
  }

}

# ============================================================
# GLUE TABLE - SATELLITE HEALTH DAILY
# ============================================================

resource "aws_glue_catalog_table" "satellite_health_daily" {
  database_name = aws_glue_catalog_database.orbitalis_glue_db.name
  name          = "satellite_health_daily"
  table_type    = "EXTERNAL_TABLE"

  storage_descriptor {
    location = "s3a://orbitalis-data-jatin2026/iceberg_warehouse/orbitalis_db/satellite_health_daily"

    columns {
      name = "satellite_id"
      type = "string"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "1"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "event_date"
      type = "date"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "2"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "avg_battery_voltage"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "3"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "min_battery_voltage"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "4"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "max_temperature"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "5"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "avg_temperature"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "6"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "avg_signal_strength"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "7"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "event_count"
      type = "bigint"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "8"
        "iceberg.field.optional" = "true"
      }
    }
  }
}

# ============================================================
# GLUE TABLE - SATELLITE ANOMALIES
# ============================================================

resource "aws_glue_catalog_table" "satellite_anomalies" {
  database_name = aws_glue_catalog_database.orbitalis_glue_db.name
  name          = "satellite_anomalies"
  table_type    = "EXTERNAL_TABLE"

  storage_descriptor {
    location = "s3a://orbitalis-data-jatin2026/iceberg_warehouse/orbitalis_db/satellite_anomalies"

    columns {
      name = "satellite_id"
      type = "string"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "1"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "event_timestamp"
      type = "string"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "2"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "battery_voltage"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "3"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "battery_temperature"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "4"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "fuel_level"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "5"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "anomaly_type"
      type = "string"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "6"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "severity"
      type = "string"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "7"
        "iceberg.field.optional" = "true"
      }
    }
  }

}

# ============================================================
# GLUE TABLE - SATELLITE ORBIT SUMMARY
# ============================================================

resource "aws_glue_catalog_table" "satellite_orbit_summary" {
  database_name = aws_glue_catalog_database.orbitalis_glue_db.name
  name          = "satellite_orbit_summary"
  table_type    = "EXTERNAL_TABLE"

  storage_descriptor {
    location = "s3a://orbitalis-data-jatin2026/iceberg_warehouse/orbitalis_db/satellite_orbit_summary"

    columns {
      name = "satellite_id"
      type = "string"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "1"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "event_date"
      type = "date"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "2"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "avg_altitude"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "3"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "min_altitude"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "4"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "max_altitude"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "5"
        "iceberg.field.optional" = "true"
      }
    }

    columns {
      name = "avg_velocity"
      type = "double"
      parameters = {
        "iceberg.field.current"  = "true"
        "iceberg.field.id"       = "6"
        "iceberg.field.optional" = "true"
      }
    }
  }

}

# ============================================================
# IAM - ORBITALIS LEAST PRIVILEGE POLICY
# ============================================================

resource "aws_iam_policy" "orbitalis_least_privilege" {
  name        = "OrbitalisLeastPrivilegePolicy"
  description = "Least-privilege access policy for the Orbitalis telemetry pipeline."

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "OrbitalisS3ListAccess"
        Effect = "Allow"

        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]

        Resource = "arn:aws:s3:::orbitalis-data-jatin2026"
      },

      {
        Sid    = "OrbitalisS3ObjectAccess"
        Effect = "Allow"

        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]

        Resource = "arn:aws:s3:::orbitalis-data-jatin2026/*"
      },

      {
        Sid    = "OrbitalisKinesisAccess"
        Effect = "Allow"

        Action = [
          "kinesis:PutRecord",
          "kinesis:PutRecords",
          "kinesis:DescribeStreamSummary",
          "kinesis:GetRecords",
          "kinesis:GetShardIterator",
          "kinesis:ListShards"
        ]

        Resource = "arn:aws:kinesis:ap-south-1:*:stream/orbitalis-telemetry-stream"
      },

      {
        Sid    = "OrbitalisGlueAccess"
        Effect = "Allow"

        Action = [
          "glue:GetTable",
          "glue:GetDatabase",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:GetPartitions"
        ]

        Resource = "*"
      },

      {
        Sid    = "OrbitalisAthenaAccess"
        Effect = "Allow"

        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults"
        ]

        Resource = "*"
      },

      {
        Sid    = "OrbitalisCloudWatchAccess"
        Effect = "Allow"

        Action = [
          "cloudwatch:PutMetricData"
        ]

        Resource = "*"
      }
    ]
  })

  tags = {}
}

# ============================================================
# CLOUDWATCH DASHBOARD
# ============================================================

resource "aws_cloudwatch_dashboard" "orbitalis_pipeline" {
  dashboard_name = "Orbitalis-Pipeline-Monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 6
        height = 6

        properties = {
          view    = "timeSeries"
          stacked = false

          metrics = [
            ["Orbitalis/Pipeline", "TotalRecords"]
          ]

          region = "ap-south-1"
        }
      },

      {
        type   = "metric"
        x      = 6
        y      = 0
        width  = 6
        height = 6

        properties = {
          view    = "timeSeries"
          stacked = false

          metrics = [
            ["Orbitalis/Pipeline", "ValidRecords"]
          ]

          region = "ap-south-1"
        }
      },

      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 6
        height = 6

        properties = {
          view    = "timeSeries"
          stacked = false

          metrics = [
            ["Orbitalis/Pipeline", "RejectedRecords"]
          ]

          region = "ap-south-1"
        }
      },

      {
        type   = "metric"
        x      = 18
        y      = 0
        width  = 6
        height = 6

        properties = {
          view    = "timeSeries"
          stacked = false

          metrics = [
            ["Orbitalis/Pipeline", "LateRecords"]
          ]

          region = "ap-south-1"
        }
      },

      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 6
        height = 6

        properties = {
          view    = "timeSeries"
          stacked = false

          metrics = [
            ["Orbitalis/Pipeline", "RejectionRatePercent"]
          ]

          region = "ap-south-1"
        }
      },

      {
        type   = "metric"
        x      = 6
        y      = 6
        width  = 6
        height = 6

        properties = {
          view    = "timeSeries"
          stacked = false

          metrics = [
            [
              "AWS/Kinesis",
              "IncomingRecords",
              "StreamName",
              "orbitalis-telemetry-stream"
            ]
          ]

          region = "ap-south-1"
        }
      },

      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 6
        height = 6

        properties = {
          view    = "timeSeries"
          stacked = false

          metrics = [
            [
              "AWS/Kinesis",
              "IncomingBytes",
              "StreamName",
              "orbitalis-telemetry-stream"
            ]
          ]

          region = "ap-south-1"
        }
      }
    ]
  })
}

# ============================================================
# CLOUDWATCH ALARM
# ============================================================

resource "aws_cloudwatch_metric_alarm" "high_rejection_rate" {
  alarm_name        = "Orbitalis-High-Rejection-Rate"
  alarm_description = "Triggers when pipeline rejection rate exceeds 20 percent."

  comparison_operator = "GreaterThanThreshold"

  evaluation_periods  = 1
  datapoints_to_alarm = 1

  metric_name = "RejectionRatePercent"
  namespace   = "Orbitalis/Pipeline"

  statistic = "Average"
  period    = 300

  threshold = 20

  treat_missing_data = "missing"

  alarm_actions = [
    "arn:aws:sns:ap-south-1:390663897017:Orbitalis-Pipeline-Alerts"
  ]
}

# ============================================================
# SNS TOPIC
# ============================================================

resource "aws_sns_topic" "pipeline_alerts" {
  name = "Orbitalis-Pipeline-Alerts"
}