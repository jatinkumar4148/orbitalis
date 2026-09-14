"""
Master Pipeline Runner
========================
Chains together the full LOCAL version of the Orbitalis pipeline:

  Simulator -> Quality Gate -> Watermark Stage -> Dedup Stage

This mirrors the real AWS flow (Kinesis -> Glue/Spark -> Iceberg Silver)
but runs entirely on local files, so we can demo and sanity-check the
whole thing end-to-end before wiring up any cloud service.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

from simulator.producer import LocalFileSink, run_simulation
from processing.run_quality_gate import run_quality_gate
from processing.run_watermark_stage import run_watermark_stage
from processing.run_dedup_stage import run_dedup_stage


def run_full_pipeline(clean_start: bool = True) -> None:
    load_dotenv()
    data_dir = Path("./data")

    if clean_start and data_dir.exists():
        print("Cleaning old ./data files for a fresh run...")
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    # ── Stage 1: Simulator ──────────────────────────────────
    print("\n[1/4] Running simulator...")
    sink = LocalFileSink("./data/local_events.jsonl")
    total_generated = run_simulation(
        num_satellites=int(os.getenv("NUM_SATELLITES", 10)),
        event_rate_per_satellite=float(os.getenv("EVENT_RATE_PER_SATELLITE", 100)),
        duration_seconds=float(os.getenv("SIM_DURATION_SECONDS", 5)),
        sink=sink,
        anomaly_injection_enabled=os.getenv("ANOMALY_INJECTION_ENABLED", "true").lower() == "true",
        anomaly_injection_probability=float(os.getenv("ANOMALY_INJECTION_PROBABILITY", 0.02)),
        seed=int(os.getenv("RANDOM_SEED")) if os.getenv("RANDOM_SEED") else None,
    )
    print(f"    Generated: {total_generated} events")

    # ── Stage 2: Data Quality ───────────────────────────────
    print("\n[2/4] Running quality gate...")
    quality_summary = run_quality_gate(
        input_path="./data/local_events.jsonl",
        valid_output_path="./data/valid_events.jsonl",
        rejected_output_path="./data/rejected_events.jsonl",
    )
    print(f"    {quality_summary}")

    # ── Stage 3: Event-Time / Watermarking ──────────────────
    print("\n[3/4] Running watermark stage...")
    watermark_summary = run_watermark_stage(
        input_path="./data/valid_events.jsonl",
        on_time_output_path="./data/on_time_events.jsonl",
        late_output_path="./data/late_events.jsonl",
        allowed_lateness_seconds=300.0,
        simulate_late_event_probability=0.05,
        seed=42,
    )
    print(f"    {watermark_summary}")

    # ── Stage 4: Deduplication ──────────────────────────────
    print("\n[4/4] Running dedup stage...")
    dedup_summary = run_dedup_stage(
        input_path="./data/on_time_events.jsonl",
        deduped_output_path="./data/deduped_events.jsonl",
        duplicates_output_path="./data/duplicate_events.jsonl",
        simulate_duplicate_probability=0.05,
        seed=42,
    )
    print(f"    {dedup_summary}")

    # ── Final summary ────────────────────────────────────────
    print("\n" + "=" * 50)
    print("PIPELINE COMPLETE — this is the current Silver layer output:")
    print(f"  Raw generated:        {total_generated}")
    print(f"  Valid (passed QC):    {quality_summary['valid']}")
    print(f"  Rejected (bad data):  {quality_summary['rejected']}")
    print(f"  On-time:              {watermark_summary['on_time']}")
    print(f"  Late (past watermark):{watermark_summary['late']}")
    print(f"  Final clean events:   {dedup_summary['deduped']}")
    print(f"  Duplicates removed:   {dedup_summary['duplicates_removed']}")
    print("=" * 50)


if __name__ == "__main__":
    run_full_pipeline()