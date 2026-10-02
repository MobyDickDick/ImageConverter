from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.build_quality_queue import build_quality_queue


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _snapshot(root: Path, *, stage: str = "complete") -> None:
    results = {
        "AC5040_L.jpg": {"filename": "AC5040_L.jpg", "mean_delta2": 90, "spatial_quality_score": 30, "w": 4, "h": 5, "params": {"mode": "geometry_ir"}},
        "GE9011_2M.jpg": {"mean_delta2": 80, "w": 3, "h": 3},
        "GE9012_7M.jpg": {"mean_delta2": 70},
        "GE9013_1M.jpg": {"mean_delta2": 60},
        "GE0281.jpg": {"mean_delta2": 50, "diff_error_distribution_reason": "cluster"},
        "BAD.jpg": {"mean_delta2": 1000, "status": "semantic_mismatch"},
    }
    _write_json(root / "conversion_result_map.json", results)
    _write_json(root / "conversion_checkpoint.json", {"schema_version": "conversion_checkpoint_v1", "run_id": "run-ap3", "stage": stage, "processed_result_count": len(results)})
    if stage == "complete":
        _write_json(root / "conversion_run_manifest.json", {"schema_version": "conversion_run_manifest_v1", "run_id": "run-ap3", "input_count": 6, "processed_result_count": 6, "successful_count": 5, "failure_count": 1, "domain_failure_count": 1, "technical_failure_count": 0, "timeout_count": 0})


def test_queue_uses_only_complete_run_and_limits_family_concentration(tmp_path: Path) -> None:
    _snapshot(tmp_path)

    report = build_quality_queue(tmp_path)

    assert report["run_id"] == "run-ap3"
    assert report["candidate_count"] == 4
    assert [item["filename"] for item in report["candidates"]] == ["AC5040_L.jpg", "GE9011_2M.jpg", "GE9012_7M.jpg", "GE0281.jpg"]
    assert report["candidates"][0]["metrics"]["image_area"] == 20
    assert report["candidates"][-1]["dominant_residual_hypothesis"] == "structured_diff:cluster"
    assert report["excluded_results"] == [{"filename": "BAD.jpg", "reason": "semantic_status:semantic_mismatch"}]


def test_incomplete_run_cannot_create_queue(tmp_path: Path) -> None:
    _snapshot(tmp_path, stage="initial_pass")

    with pytest.raises(ValueError, match="requires a complete run"):
        build_quality_queue(tmp_path)

    completed = subprocess.run([sys.executable, "tools/build_quality_queue.py", str(tmp_path)], text=True, capture_output=True, check=False)
    assert completed.returncode == 2
    assert "requires a complete run" in completed.stderr
