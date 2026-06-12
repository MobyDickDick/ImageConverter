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


ACTIVE_VARIANTS = [
    "AC0701_1_S",
    "AC0722_1_S",
    "AC0845_S",
]


def _target_by_variant(variant: str) -> dict[str, object]:
    return next(target for target in PLAN_B_PERCEPTION_TARGETS if target["variant"] == variant)


def test_build_plan_b_perception_linkage_record_has_lerneffekt_decision() -> None:
    record = build_plan_b_perception_linkage_record(_target_by_variant("AC0701_1_S"))

    assert record["schema_version"] == "plan_b_perception_linkage_record_v1"
    assert record["variant"] == "AC0701_1_S"
    lerneffekt = record["perception_lerneffekt"]
    assert lerneffekt["question"]
    assert lerneffekt["expected_first_primitive"] == "square_with_lower_vertical_connector"
    assert lerneffekt["decision"] == "noch nicht erkannt"
    assert lerneffekt["expected_candidate_kinds"] == ["line", "rectangle"]
    assert lerneffekt["matched_candidate_kinds"] == []
    assert lerneffekt["matched_seed_kinds"] == []
    assert lerneffekt["next_action"]


def test_ac0845_circle_seed_is_generalized_without_claiming_text_detection() -> None:
    record = build_plan_b_perception_linkage_record(_target_by_variant("AC0845_S"))

    assert record["variant"] == "AC0845_S"
    lerneffekt = record["perception_lerneffekt"]
    assert lerneffekt["decision"] == "generalisiert"
    assert lerneffekt["matched_candidate_kinds"] == ["circle"]
    assert lerneffekt["matched_seed_kinds"] == ["CircleBackground"]
    assert "text_glyph" in lerneffekt["expected_candidate_kinds"]


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

    rows = list(csv.DictReader(csv_report.open(encoding="utf-8")))
    assert len(rows) == len(ACTIVE_VARIANTS)
    assert {"variant", "decision", "next_action"} <= set(rows[0])
