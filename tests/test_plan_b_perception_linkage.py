from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("numpy")

from tools.perception_detection_contract import (
    PLAN_B_PERCEPTION_TARGETS,
    run_plan_b_perception_linkage_report,
)


ACTIVE_VARIANTS: list[str] = ["GE1001_M", "GE9021_7M"]


def test_plan_b_perception_targets_match_quality_triage() -> None:
    assert [target["variant"] for target in PLAN_B_PERCEPTION_TARGETS] == ACTIVE_VARIANTS

    triage_path = Path(
        "artifacts/evaluation/conversion_quality_review_v2/plan_b_candidate_triage_v1.csv"
    )
    rows = list(csv.DictReader(triage_path.open(encoding="utf-8")))
    assert [row["variant"] for row in rows] == ACTIVE_VARIANTS


def test_run_plan_b_perception_linkage_report_writes_json_and_csv(
    tmp_path: Path,
) -> None:
    summary = run_plan_b_perception_linkage_report(tmp_path)

    assert summary["samples"] == len(ACTIVE_VARIANTS)
    assert summary["evaluated_samples"] == len(ACTIVE_VARIANTS)
    assert summary["all_have_perception_lerneffekt"] is True

    json_report = tmp_path / "plan_b_perception_linkage_report_v1.json"
    csv_report = tmp_path / "plan_b_perception_linkage_samples_v1.csv"
    assert json_report.exists()
    assert csv_report.exists()

    report = json.loads(json_report.read_text(encoding="utf-8"))
    assert report["schema_version"] == "plan_b_perception_linkage_report_v1"
    assert report["metrics"]["all_have_perception_lerneffekt"] is True
    assert [record["variant"] for record in report["records"]] == ACTIVE_VARIANTS

    with csv_report.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert len(rows) == len(ACTIVE_VARIANTS)
    assert {"variant", "decision", "next_action"} <= set(reader.fieldnames or [])
