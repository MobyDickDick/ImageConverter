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


def _target_by_variant(variant: str) -> dict[str, object]:
    return next(target for target in PLAN_B_PERCEPTION_TARGETS if target["variant"] == variant)


def test_build_plan_b_perception_linkage_record_has_lerneffekt_decision() -> None:
    record = build_plan_b_perception_linkage_record(_target_by_variant("AC0850_M"))

    assert record["schema_version"] == "plan_b_perception_linkage_record_v1"
    assert record["variant"] == "AC0850_M"
    lerneffekt = record["perception_lerneffekt"]
    assert lerneffekt["question"]
    assert lerneffekt["expected_first_primitive"] == "circle_ring_or_rf_label"
    assert lerneffekt["decision"] in {
        "generalisiert",
        "nur Sonderfall",
        "noch nicht erkannt",
    }
    assert lerneffekt["expected_candidate_kinds"] == ["circle", "ring", "text_glyph"]
    assert "circle" in lerneffekt["matched_candidate_kinds"]
    assert lerneffekt["next_action"]


def test_build_plan_b_perception_linkage_record_matches_rf_vertical_connector() -> None:
    record = build_plan_b_perception_linkage_record(_target_by_variant("AC0844_S"))

    assert record["variant"] == "AC0844_S"
    lerneffekt = record["perception_lerneffekt"]
    assert lerneffekt["expected_first_primitive"] == "circle_ring_or_rf_vertical_connector"
    assert "line" in lerneffekt["matched_candidate_kinds"]
    assert lerneffekt["top_candidate_kind"] in {"circle", "line"}
    assert record["candidate_count"] >= 1


def test_run_plan_b_perception_linkage_report_writes_json_and_csv(
    tmp_path: Path,
) -> None:
    summary = run_plan_b_perception_linkage_report(tmp_path)

    assert summary["samples"] == 3
    assert summary["evaluated_samples"] >= 1
    assert summary["all_have_perception_lerneffekt"] is True

    json_report = tmp_path / "plan_b_perception_linkage_report_v1.json"
    csv_report = tmp_path / "plan_b_perception_linkage_samples_v1.csv"
    assert json_report.exists()
    assert csv_report.exists()

    report = json.loads(json_report.read_text(encoding="utf-8"))
    assert report["schema_version"] == "plan_b_perception_linkage_report_v1"
    assert report["metrics"]["all_have_perception_lerneffekt"] is True
    assert {record["variant"] for record in report["records"]} == {
        "AC0836_S",
        "AC0844_S",
        "AC0850_M",
    }

    rows = list(csv.DictReader(csv_report.open(encoding="utf-8")))
    assert len(rows) == 3
    assert {"variant", "decision", "next_action"} <= set(rows[0])
