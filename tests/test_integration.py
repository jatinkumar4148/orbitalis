from pathlib import Path


def test_full_local_pipeline_runs_without_error():
    from run_pipeline import run_full_pipeline

    run_full_pipeline(clean_start=True)

    data_dir = Path("./data")

    expected_files = [
        "local_events.jsonl",
        "valid_events.jsonl",
        "rejected_events.jsonl",
        "on_time_events.jsonl",
        "late_events.jsonl",
        "deduped_events.jsonl",
        "duplicate_events.jsonl",
    ]

    for filename in expected_files:
        output_file = data_dir / filename

        assert output_file.exists(), f"Missing output file: {filename}"
        assert output_file.stat().st_size > 0, f"Output file is empty: {filename}"