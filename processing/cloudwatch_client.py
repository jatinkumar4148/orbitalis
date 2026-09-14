"""
Reusable helper to push custom pipeline metrics to CloudWatch.
Called from run_s3_streaming_pipeline.py's process_batch() after
each micro-batch completes.
"""

import boto3

CLOUDWATCH_NAMESPACE = "Orbitalis/Pipeline"
AWS_REGION = "ap-south-1"

_client = boto3.client("cloudwatch", region_name=AWS_REGION)


def put_pipeline_metrics(valid: int, rejected: int, late: int, total: int) -> None:
    """
    Pushes one data point per metric to CloudWatch. Called once per
    micro-batch — over time this builds a time-series we can graph
    and alarm on.
    """
    metrics = [
        {"MetricName": "ValidRecords", "Value": valid, "Unit": "Count"},
        {"MetricName": "RejectedRecords", "Value": rejected, "Unit": "Count"},
        {"MetricName": "LateRecords", "Value": late, "Unit": "Count"},
        {"MetricName": "TotalRecords", "Value": total, "Unit": "Count"},
    ]

    if total > 0:
        rejection_rate = (rejected / total) * 100
        metrics.append({"MetricName": "RejectionRatePercent", "Value": rejection_rate, "Unit": "Percent"})

    _client.put_metric_data(Namespace=CLOUDWATCH_NAMESPACE, MetricData=metrics)
    