from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("numpy")

from tools.perception_detection_contract import (
    PLAN_B_PERCEPTION_TARGETS,
    build_plan_b_perception_linkage_record,
    run_plan_b_perception_linkage_report,
)


def test_plan_b_perception_targets_only_include_active_candidates() -> None:
    assert PLAN_B_PERCEPTION_TARGETS == []


def test_run_plan_b_perception_linkage_report_writes_json_and_csv(
    tmp_path: Path,
) -> None:
    summary = run_plan_b_perception_linkage_report(tmp_path)

    assert summary["samples"] == 0
    assert summary["evaluated_samples"] == 0
    assert summary["all_have_perception_lerneffekt"] is True

    json_report = tmp_path / "plan_b_perception_linkage_report_v1.json"
    csv_report = tmp_path / "plan_b_perception_linkage_samples_v1.csv"
    assert json_report.exists()
    assert csv_report.exists()

    report = json.loads(json_report.read_text(encoding="utf-8"))
    assert report["schema_version"] == "plan_b_perception_linkage_report_v1"
    assert report["metrics"]["all_have_perception_lerneffekt"] is True
    assert report["records"] == []

    rows = list(csv.DictReader(csv_report.open(encoding="utf-8")))
    assert rows == []
