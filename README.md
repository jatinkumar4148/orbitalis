# 🛰️ Orbitalis

**A production-grade, cloud-native data engineering pipeline for satellite telemetry — built end-to-end on AWS.**

![CI](https://github.com/jatinkumar4148/orbitalis/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10-blue)
![Spark](https://img.shields.io/badge/spark-3.5.3-orange)
![Iceberg](https://img.shields.io/badge/iceberg-1.6.1-teal)
![Terraform](https://img.shields.io/badge/terraform-managed-purple)
![License](https://img.shields.io/badge/license-MIT-green)

Orbitalis simulates a fleet of satellites, streams their telemetry through Kinesis, processes it with checkpointed Spark Structured Streaming, lands it in an Apache Iceberg lakehouse, and serves it through Athena and a live Streamlit dashboard — all monitored, secured, and provisioned as code.

---

## Overview


<img width="1672" height="941" alt="Architechture" src="https://github.com/user-attachments/assets/dbdc1943-b890-499c-bb07-08a74697f9bb" />


## 📐 Architecture


<img width="2752" height="1536" alt="Architechture of Orbitalis" src="https://github.com/user-attachments/assets/c2448c1d-bba3-4b44-95f8-efbf778c405d" />

---

## ✨ Highlights

This isn't a toy pipeline — every layer was built local-first, wired to real AWS, and stress-tested for real failure modes:

- 🔁 **Checkpointed Structured Streaming** prevents unbounded reprocessing — verified by running the pipeline twice and confirming zero duplicate work.
- 🧪 **Edge cases proven on real infrastructure** — a genuinely late event and a genuine duplicate were injected through the actual Kinesis → S3 path, not just mocked in unit tests.
- 🔐 **Security tested, not just configured** — the least-privilege IAM policy was proven to correctly block an unauthorized action even when Terraform tried to modify it.
- 🧊 **Apache Iceberg** with working schema evolution (add a column, zero rewrite) and time-travel (`VERSION AS OF`) queries.
- ⚙️ **CI/CD verified both ways** — a passing build and an intentionally-broken one were both pushed to confirm GitHub Actions genuinely catches failures.
- 🏗️ **Terraform manages all 12 AWS resources** via `import` (not recreation) — `terraform plan` reports zero drift.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Simulation | Python 3.10, Pydantic |
| Streaming | Amazon Kinesis Data Streams (on-demand) |
| Delivery | Kinesis Data Firehose |
| Storage | Amazon S3 (Bronze / Silver / Rejected / Late) |
| Processing | Apache Spark 3.5.3 (Structured Streaming) |
| Lakehouse | Apache Iceberg 1.6.1 (AWS Glue Catalog) |
| Query engine | Amazon Athena |
| Dashboard | Streamlit |
| Monitoring | Amazon CloudWatch, SNS |
| Security | IAM (least-privilege), AWS KMS |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Testing | pytest (unit, Spark, integration) |

---

## 🚀 Quickstart — local, no AWS required

```bash
git clone https://github.com/jatinkumar4148/orbitalis.git
cd orbitalis

python -m venv venv_spark35
venv_spark35\Scripts\activate        # Windows
# source venv_spark35/bin/activate   # macOS/Linux

pip install -r requirements.txt
pip install -r requirements-test.txt
cp .env.example .env

# Run the full local pipeline: Simulator → Quality Gate → Watermark → Dedup
python run_pipeline.py

# Run the test suite (fast, free — no AWS calls)
pytest tests/ -m "not aws" -v
```

## ☁️ Running against real AWS

Requires an AWS account and an IAM user configured via `aws configure`. Provision infrastructure with Terraform:

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

Then point the simulator at Kinesis:

```bash
# in .env: EVENT_SINK=kinesis
python -m simulator.producer
python -m processing.run_s3_streaming_pipeline
```

Launch the dashboard:

```bash
cd dashboard
streamlit run app.py
```

---

## 📁 Repository Structure

```
orbitalis/
├── simulator/            # Stateful satellite telemetry generator + 6 anomaly scenarios
├── schemas/               # Pydantic event schema + versioned JSON schemas
├── ingestion/             # Kinesis producer (boto3, retry with backoff)
├── processing/            # Validation, watermarking, dedup — local, Spark, and Iceberg versions
├── dashboard/              # Streamlit app + Athena query client
├── infrastructure/terraform/  # IaC — all 12 AWS resources, imported not recreated
├── tests/                  # pytest suite (unit, Spark, integration)
├── docs/decisions.md        # Full Architecture Decision Record (ADR) log
└── run_pipeline.py          # One-command local end-to-end pipeline runner
```

---

## Modules

| # | Module | Summary |
|---|--------|---------|
| M01 | Foundation | Repo structure, venv, dependency management |
| M02 | Satellite Simulator | Stateful, seeded telemetry + 6 injectable anomaly scenarios |
| M03 | Event Schema | Pydantic contract + versioned JSON schema |
| M04 | Kinesis Ingestion | Real-time ingestion, partitioned by `satellite_id` |
| M05 | Raw Data Lake (Bronze) | Firehose → partitioned S3 archive |
| M06 | Stream Processing | Checkpointed Spark Structured Streaming pipeline |
| M07 | Data Quality | Range/completeness/timestamp validation |
| M08 | Event-Time Engine | Watermarking, late-event routing |
| M09 | Dedup & Replay | Bounded-window deduplication |
| M10 | Iceberg Lakehouse | Silver + 3 Gold tables, schema evolution, time-travel |
| M11 | Anomaly Detection | Rule-based thresholds, delivered via Gold tables |
| M12 | Analytics (Athena) | Glue Catalog migration, SQL over Iceberg |
| M13 | Dashboard | 5-page Streamlit Mission Control |
| M14 | Monitoring | Custom CloudWatch metrics, dashboard, alarm + SNS |
| M15 | Security | Least-privilege IAM, KMS encryption at rest/in-transit |
| M16 | Testing | pytest suite with AWS-cost isolation via markers |
| M17 | CI/CD | GitHub Actions, verified with real pass/fail scenarios |
| M18 | Infrastructure as Code | Terraform-managed, zero-drift `plan` |

Full build log with every design decision, code walkthrough, and bug encountered is documented in [`docs/decisions.md`](docs/decisions.md).

---

## Final Output

<img width="1366" height="768" alt="Screenshot (1043)" src="https://github.com/user-attachments/assets/fd719314-dfe8-42e1-9e87-df4baf5b7518" />
<img width="1366" height="768" alt="Screenshot (1044)" src="https://github.com/user-attachments/assets/0eaef7e8-d531-4722-8ce1-c58e17175286" />
<img width="1366" height="768" alt="Screenshot (1045)" src="https://github.com/user-attachments/assets/c71d7b2a-e88a-4339-bc49-655d77ba3804" />
<img width="1366" height="768" alt="Screenshot (1046)" src="https://github.com/user-attachments/assets/f6ccf068-f156-4b8a-945b-7307e268fe53" />
<img width="1366" height="768" alt="Screenshot (1047)" src="https://github.com/user-attachments/assets/d120c31d-0a07-4439-b778-e07066536086" />
<img width="1366" height="768" alt="Screenshot (1048)" src="https://github.com/user-attachments/assets/eb4e0df4-a161-4823-9831-36917a8e0d86" />
<img width="1366" height="768" alt="Screenshot (1049)" src="https://github.com/user-attachments/assets/a2a061d5-42f7-4c3f-bb32-b0b6a45685b9" />
<img width="1366" height="768" alt="Screenshot (1050)" src="https://github.com/user-attachments/assets/af51d547-c243-4a28-b4a3-890d80be8fc9" />
<img width="1366" height="768" alt="Screenshot (1051)" src="https://github.com/user-attachments/assets/8ce4750e-056e-45e4-bcb0-a6521b2983f2" />

## 📄 License

MIT License — personal portfolio project.
