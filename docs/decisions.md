# Architecture Decision Records

## ADR-001: Adopt Terraform for Existing Orbitalis AWS Infrastructure

**Status:** Accepted  
**Date:** 2026-09-16

### Context

The Orbitalis project already has a working AWS-based telemetry data engineering infrastructure.

The infrastructure includes:

- Amazon S3 bucket for telemetry data
- Amazon Kinesis Data Stream for telemetry ingestion
- Amazon Kinesis Data Firehose for Bronze delivery
- AWS Glue Data Catalog database and Iceberg tables
- IAM least-privilege runtime policy
- Amazon CloudWatch dashboard and alarm
- Amazon SNS topic for pipeline alerts

The infrastructure was created and validated before Terraform was introduced.

The objective of Module 18 was therefore to introduce Infrastructure as Code (IaC) **without recreating, deleting, or replacing the existing AWS infrastructure**.

### Decision

Terraform was selected as the Infrastructure as Code tool for managing the existing Orbitalis AWS resources.

Terraform configuration is maintained under:

```text
infrastructure/terraform/