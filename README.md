# 🛰️ Orbitalis — Satellite Telemetry Data Engineering Platform

![CI](https://github.com/jatinkumar4148/orbitalis/actions/workflows/ci.yml/badge.svg)

A cloud-native data engineering pipeline that simulates, ingests, validates, and analyzes satellite telemetry in real time — built on AWS (Kinesis, S3, Glue/Spark, Iceberg, Athena, CloudWatch) with Terraform-managed infrastructure.

---

## 📐 Architecture

```
Satellite Simulator (Python)
        ↓
Amazon Kinesis Data Streams (on-demand, KMS-encrypted)
        ↓
   ┌────┴─────┐
   ▼          ▼
Kinesis     AWS Glue / Spark Structured Streaming
Firehose         ↓
   ↓         Validate → Watermark → Dedup
S3 Bronze        ↓
(raw, partitioned) S3 Silver / Rejected / Late (checkpointed)
                  ↓
           Apache Iceberg (Silver + Gold tables)
                  ↓
           ┌──────┴──────┐
           ▼             ▼
      Gold Tables    Amazon Athena
   (health/anomalies/orbit)   ↓
           └──────┬──────┘
                  ▼
         Streamlit Mission Control Dashboard

Cross-cutting: CloudWatch (metrics/alarms) · IAM (least-privilege) ·
KMS (encryption at rest/in-transit) · Terraform (IaC) · GitHub Actions (CI/CD)
```

---

## ✅ Module Status (all 18 complete)

| # | Module | What it does |
|---|--------|--------------|
| M01 | Project Foundation | Repo structure, venv, dependency management |
| M02 | Satellite Simulator | Stateful, seeded, realistic telemetry with 6 injectable anomaly scenarios |
| M03 | Event Schema | Pydantic contract (`TelemetryEvent`) + versioned JSON schema |
| M04 | Kinesis Ingestion | Real-time streaming ingestion, partitioned by `satellite_id` |
| M05 | Raw Data Lake (Bronze) | Kinesis Firehose → partitioned S3 archive |
| M06 | Stream Processing | Checkpointed Spark Structured Streaming: validate, watermark, dedup |
| M07 | Data Quality | Range/completeness/timestamp rules — pure Python + Spark versions |
| M08 | Event-Time Engine | Watermarking, late-event handling (local + Spark batch + Spark streaming) |
| M09 | Dedup & Replay | Bounded-window deduplication, replay-from-Bronze capability |
| M10 | Iceberg Lakehouse | Silver + 3 Gold tables, schema evolution & time-travel verified |
| M11 | Anomaly Detection | Rule-based thresholds (battery/temperature/fuel) — delivered via Gold tables |
| M12 | Analytics (Athena) | Glue Catalog migration, SQL queries over Iceberg tables |
| M13 | Dashboard | 5-page Streamlit Mission Control (Overview, Detail, Trends, Anomalies, Pipeline Health) |
| M14 | Monitoring | Custom CloudWatch metrics, dashboard, alarm + SNS email alerts |
| M15 | Security | Least-privilege IAM, S3 + Kinesis KMS encryption |
| M16 | Testing | pytest suite (unit + Spark + integration), AWS tests isolated via markers |
| M17 | CI/CD | GitHub Actions — auto-test on every push, verified with real pass/fail scenarios |
| M18 | Infrastructure as Code | Terraform manages all 12 AWS resources via import (zero-drift plan) |

---

## 🧰 Tech Stack

- **Language:** Python 3.10
- **Streaming:** Amazon Kinesis Data Streams (on-demand)
- **Delivery:** Kinesis Data Firehose
- **Storage:** Amazon S3 (Bronze/Silver/Rejected/Late), partitioned by date
- **Processing:** Apache Spark 3.5.3 (Structured Streaming) on local dev, designed for AWS Glue
- **Lakehouse:** Apache Iceberg 1.6.1 (Hadoop catalog → migrated to AWS Glue Catalog)
- **Query engine:** Amazon Athena
- **Dashboard:** Streamlit
- **Monitoring:** Amazon CloudWatch (custom metrics, dashboard, alarms) + SNS
- **Security:** IAM least-privilege policies, KMS encryption (S3 + Kinesis)
- **IaC:** Terraform (imports existing infra — zero recreation)
- **CI/CD:** GitHub Actions
- **Testing:** pytest (unit, Spark, integration; AWS-dependent tests separated via markers)

---

## 🚀 Quickstart (local, no AWS required)

```bash
git clone https://github.com/jatinkumar4148/orbitalis.git
cd orbitalis

python -m venv venv_spark35
venv_spark35\Scripts\activate      # Windows
pip install -r requirements.txt
pip install -r requirements-test.txt

cp .env.example .env

# Run the full local pipeline: Simulator → Quality Gate → Watermark → Dedup
python run_pipeline.py

# Run tests (fast, free — no AWS calls)
pytest tests/ -m "not aws" -v
```

## ☁️ Running against real AWS

Requires an AWS account with an IAM user configured via `aws configure`, and the following resources (see `infrastructure/terraform/` to provision via Terraform, or create manually per `docs/decisions.md`):

- Kinesis stream: `orbitalis-telemetry-stream`
- S3 bucket for Bronze/Silver/Gold storage
- Kinesis Firehose delivery stream
- Glue database + Iceberg tables

```bash
# .env: set EVENT_SINK=kinesis
python -m simulator.producer
python -m processing.run_s3_streaming_pipeline
```

Dashboard:
```bash
cd dashboard
streamlit run app.py
```

---

## 📁 Repo Structure

```
orbitalis/
├── simulator/          # Satellite telemetry generator + anomaly injection
├── schemas/             # Pydantic event schema + versioned JSON schemas
├── ingestion/            # Kinesis producer (boto3)
├── processing/           # Validation, watermarking, dedup — local + Spark + Iceberg + CloudWatch
├── dashboard/            # Streamlit app + Athena query client
├── infrastructure/terraform/  # IaC — imports existing AWS resources
├── tests/                # pytest suite (unit, Spark, integration)
├── docs/decisions.md      # Architecture Decision Record (ADR) log
└── run_pipeline.py        # Local end-to-end pipeline runner
```

---

## 🏗️ Key Design Decisions

Full rationale for every major decision — local-first development, Firehose over custom ingestion, on-demand Kinesis capacity, bounded-window deduplication, Hadoop→Glue Iceberg catalog migration, Terraform import-not-recreate strategy, and more — is documented in [`docs/decisions.md`](docs/decisions.md).

---

## 📊 What Makes This Project Real (not just a tutorial)

- **Local-first, then AWS**: every module's logic was proven in pure Python before touching cloud services — a documented, deliberate cost/risk-reduction strategy.
- **Genuine bugs found and fixed**, not scripted: batch-mode reprocessing risk (caught before it became a production incident), Windows/PySpark subprocess issues, Iceberg/Spark version incompatibilities, IAM permission gaps — all diagnosed and resolved with verifiable evidence.
- **Edge cases tested on real infrastructure**, not just unit tests: late-arriving and duplicate events were injected through the actual Kinesis→Firehose→S3 path and confirmed correctly handled.
- **Security validated, not just configured**: Step 5 of the Terraform module deliberately proved that AWS blocks an unauthorized action from the least-privilege runtime identity — a positive security test, not a workaround.
- **CI/CD verified both ways**: a passing pipeline and an intentionally-broken one were both pushed to confirm GitHub Actions genuinely catches failures.

---

## 📄 License

Personal portfolio project — MIT License.
