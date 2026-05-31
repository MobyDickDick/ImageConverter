from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("numpy")

from tools.perception_detection_contract import (
    _make_synthetic_glyph_image,
    build_text_glyph_evaluation_record,
    detect_text_glyph_candidates,
    run_text_glyph_evaluation_report,
)


def test_detect_text_glyph_candidates_matches_m_plus_minus_and_label() -> None:
    for glyph in ["M", "+", "-", "VOC"]:
        image = _make_synthetic_glyph_image(glyph)
        candidates = detect_text_glyph_candidates(
            image,
            description=f"mittig steht `{glyph}`",
            glyphs=[glyph],
            source="test_pf7_text_glyph",
        )

        assert candidates, glyph
        top = candidates[0].to_dict()
        assert top["kind"] == "text_glyph"
        assert top["geometry"]["text"] == glyph
        assert top["geometry"]["geometry_ir_kind"] == "TextGlyph"
        assert top["confidence"] >= 0.42
        assert top["evidence"]["detector"] == "template_match_text_glyph"
        assert "no_required_ocr_dependency" in top["evidence"]["dependency_policy"]


def test_build_text_glyph_evaluation_record_marks_match() -> None:
    image = _make_synthetic_glyph_image("M")

    record = build_text_glyph_evaluation_record(
        image,
        sample_id="glyph_m_pf7_synthetic",
        expected_text="M",
        description="mittig steht der Buchstabe `M`",
    )

    assert record["expected_text"] == "M"
    assert record["top_text"] == "M"
    assert record["match"] is True
    assert record["top_candidate"]["kind"] == "text_glyph"


def test_run_text_glyph_evaluation_report_writes_json_and_csv(tmp_path: Path) -> None:
    summary = run_text_glyph_evaluation_report(tmp_path)

    assert summary["samples"] >= 4
    assert summary["all_matched"] is True
    assert summary["match_rate"] == 1.0

    json_report = tmp_path / "perception_text_glyph_evaluation_report_v1.json"
    csv_report = tmp_path / "perception_text_glyph_evaluation_samples_v1.csv"
    assert json_report.exists()
    assert csv_report.exists()

    report = json.loads(json_report.read_text(encoding="utf-8"))
    assert report["schema_version"] == "perception_text_glyph_evaluation_report_v1"
    assert report["dependency_policy"].startswith("no_new_required_dependency")
    assert report["metrics"]["all_matched"] is True
    assert set(report["scope"]) == {"M", "+", "-", "short_label"}

    rows = list(csv.DictReader(csv_report.open(encoding="utf-8")))
    assert [row["expected_text"] for row in rows[:4]] == ["M", "+", "-", "VOC"]
    assert any(row["sample_type"] == "real" for row in rows)
