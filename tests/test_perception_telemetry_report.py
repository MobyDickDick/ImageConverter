from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("numpy")

from tools.perception_detection_contract import (
    build_perception_telemetry_record,
    run_perception_telemetry_report,
)
from tools.shape_detection_eval import make_synthetic_image


def test_build_perception_telemetry_record_tracks_seed_decision_and_errors() -> None:
    image = make_synthetic_image("minus", "synthetic")

    record = build_perception_telemetry_record(
        image,
        sample_id="minus_pf6_synthetic",
        description='oben mittig ist ein "-"-Zeichen',
        source="test_pf6_telemetry",
    )

    assert record["schema_version"] == "perception_telemetry_record_v1"
    assert record["candidate_count"] >= 1
    assert record["accepted_candidate_count"] >= 1
    assert record["selected_geometry_ir_seed_count"] >= 1
    assert {"HorizontalRule", "MinusGlyph"} & set(record["geometry_ir_after_seed_kinds"])
    assert any(row["decision"] == "accepted" for row in record["candidates"])
    assert "error_before_seed" in record
    assert "error_after_seed" in record


def test_run_perception_telemetry_report_writes_json_and_csv(tmp_path: Path) -> None:
    summary = run_perception_telemetry_report(tmp_path)

    assert summary["samples"] == 1
    assert summary["accepted_candidates"] >= 1
    assert summary["all_have_selected_seed"] is True

    json_report = tmp_path / "perception_telemetry_report_v1.json"
    csv_report = tmp_path / "perception_telemetry_candidates_v1.csv"
    assert json_report.exists()
    assert csv_report.exists()

    report = json.loads(json_report.read_text(encoding="utf-8"))
    assert report["schema_version"] == "perception_telemetry_report_v1"
    assert report["records"][0]["runtime_status"] == "non_composite_perception_seeded_geometry_ir"
    assert report["records"][0]["selected_geometry_ir_seeds"]

    rows = list(csv.DictReader(csv_report.open(encoding="utf-8")))
    assert rows
    assert {"sample_id", "candidate_kind", "decision", "error_before_seed", "error_after_seed"} <= set(rows[0])
