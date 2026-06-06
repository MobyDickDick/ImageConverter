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


ACTIVE_VARIANTS: list[str] = []


def test_build_plan_b_perception_linkage_record_has_lerneffekt_decision() -> None:
    record = build_plan_b_perception_linkage_record(
        {
            "variant": "AC0130",
            "image_candidates": ["artifacts/images_to_convert/AC0130.jpg"],
            "plan_b_reason": "Abgeschlossener Regressionstest.",
            "perception_question": "Werden Rechteck, Diagonalen und Zeichen getrennt erkannt?",
            "expected_first_primitive": "rectangle_diagonals_and_top_glyph",
            "expected_candidate_kinds": {"rectangle", "line", "circle", "ring"},
            "expected_seed_kinds": {"CircleBackground"},
            "description": "Abgeschlossener AC0130-Perception-Lerneffekt.",
        }
    )

    assert record["schema_version"] == "plan_b_perception_linkage_record_v1"
    assert record["variant"] == "AC0130"
    lerneffekt = record["perception_lerneffekt"]
    assert lerneffekt["decision"] == "generalisiert"
    assert {"circle", "ring"} & set(lerneffekt["matched_candidate_kinds"])
    assert lerneffekt["matched_seed_kinds"] == ["CircleBackground"]


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
    assert [record["variant"] for record in report["records"]] == ACTIVE_VARIANTS

    rows = list(csv.DictReader(csv_report.open(encoding="utf-8")))
    assert rows == []
    assert {"variant", "decision", "next_action"} <= set(
        csv_report.read_text(encoding="utf-8").splitlines()[0].split(",")
    )
