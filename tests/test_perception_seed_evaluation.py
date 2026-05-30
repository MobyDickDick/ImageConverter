from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("numpy")

from tools.perception_detection_contract import (
    build_perception_seed_evaluation_record,
    run_perception_seed_evaluation_report,
)
from tools.shape_detection_eval import make_synthetic_image


def test_build_perception_seed_evaluation_record_tracks_metrics() -> None:
    image = make_synthetic_image("rectangle", "synthetic")

    record = build_perception_seed_evaluation_record(
        image,
        sample_id="rectangle_pf5_synthetic",
        description="",
        expected_family="rectangle",
        expected_candidate_kinds={"rectangle"},
        expected_seed_kinds={"RectBorder", "HalfDoubleRectBorder"},
    )

    assert record["expected_family"] == "rectangle"
    assert record["detection_match"] is True
    assert record["seed_match"] is True
    assert record["matching_confidences"]
    assert record["runtime_status"] == "non_composite_perception_seeded_geometry_ir"
    assert "error_before_seed" in record
    assert "error_after_seed" in record


def test_run_perception_seed_evaluation_report_writes_metrics(tmp_path: Path) -> None:
    summary = run_perception_seed_evaluation_report(tmp_path)

    assert summary["samples"] >= 3
    assert set(summary["families"]) == {"circle_ring", "minus_line", "rectangle"}
    assert summary["overall_detection_recall"] == 1.0
    assert summary["overall_seed_recall"] == 1.0

    json_report = tmp_path / "perception_seed_evaluation_report_v1.json"
    csv_report = tmp_path / "perception_seed_evaluation_samples_v1.csv"
    assert json_report.exists()
    assert csv_report.exists()

    report = json.loads(json_report.read_text(encoding="utf-8"))
    assert report["schema_version"] == "perception_seed_evaluation_report_v1"
    assert report["metrics"]["overall"]["all_detection_matched"] is True
    assert report["metrics"]["overall"]["all_seed_matched"] is True
    assert report["metrics"]["by_family"]["minus_line"]["confidence"]["count"] >= 1
    assert report["open_real_image_cases"][0]["family"] == "rectangle"

    rows = list(csv.DictReader(csv_report.open(encoding="utf-8")))
    assert rows
    assert {
        "sample_id",
        "expected_family",
        "top_candidate_family",
        "detection_match",
        "seed_match",
        "error_delta_before_minus_after",
    } <= set(rows[0])
