from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from tools.check_report_consistency import evaluate_report_consistency


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_complete_fixture(root: Path) -> None:
    _write_json(
        root / "conversion_checkpoint.json",
        {
            "schema_version": "conversion_checkpoint_v1",
            "run_id": "run-1",
            "stage": "complete",
            "processed_result_count": 2,
        },
    )
    _write_json(root / "conversion_result_map.json", {"A.jpg": {}, "B.jpg": {}})
    _write_json(
        root / "conversion_run_manifest.json",
        {
            "schema_version": "conversion_run_manifest_v1",
            "run_id": "run-1",
            "input_count": 2,
            "processed_result_count": 2,
            "successful_count": 2,
            "failure_count": 0,
            "domain_failure_count": 0,
            "technical_failure_count": 0,
            "timeout_count": 0,
        },
    )
    (root / "chain_phase_telemetry_summary.txt").write_text("conversion_count=2\n", encoding="utf-8")


def test_complete_snapshot_has_required_provenance_fields(tmp_path: Path) -> None:
    _write_complete_fixture(tmp_path)

    report = evaluate_report_consistency(tmp_path)

    assert report["status"] == "complete"
    assert report["schema_version"] == "report_consistency_gate_v1"
    assert report["run_id"] == "run-1"
    assert report["input_count"] == report["processed_count"] == 2
    assert report["generated_at"]
    assert report["source_report"].endswith("conversion_checkpoint.json")


def test_partial_snapshot_is_incomplete_and_not_a_false_pass(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "conversion_checkpoint.json",
        {
            "schema_version": "conversion_checkpoint_v1",
            "run_id": "run-partial",
            "stage": "initial_pass",
            "processed_result_count": 1,
        },
    )
    _write_json(tmp_path / "conversion_result_map.json", {"A.jpg": {}})

    assert evaluate_report_consistency(tmp_path)["status"] == "incomplete"


def test_zero_chain_summary_for_results_is_stale_and_cli_fails(tmp_path: Path) -> None:
    _write_complete_fixture(tmp_path)
    (tmp_path / "chain_phase_telemetry_summary.txt").write_text("conversion_count=0\n", encoding="utf-8")

    report = evaluate_report_consistency(tmp_path)
    completed = subprocess.run(
        [sys.executable, "tools/check_report_consistency.py", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert report["status"] == "stale/mixed-run"
    assert "empty_chain_summary_for_nonempty_result_map" in report["stale_reasons"]
    assert completed.returncode == 1


def test_duplicate_filenames_and_missing_log_make_snapshot_invalid(tmp_path: Path) -> None:
    _write_complete_fixture(tmp_path)
    with (tmp_path / "batch_failure_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["filename", "status", "reason", "details", "log_file"])
        writer.writerow(["A.jpg", "semantic_mismatch", "circle", "", "missing.log"])
        writer.writerow(["A.jpg", "semantic_mismatch", "circle", "", ""])

    report = evaluate_report_consistency(tmp_path)

    assert report["status"] == "invalid"
    assert "duplicate_filename:batch_failure_summary.csv" in report["errors"]
    assert "missing_referenced_log:missing.log" in report["errors"]
