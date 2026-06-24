import json
from pathlib import Path

from tools.evaluate_quality_complexity_gate import (
    analyze_svg_complexity,
    evaluate_quality_complexity_gate,
    write_quality_complexity_gate_report,
)

GOOD_METRICS = {
    "pixel_similarity": 0.91,
    "edge_alignment": 0.88,
    "structure_score": 0.9,
    "semantic_score": 1.0,
    "combined_score": 0.92,
}


def test_quality_complexity_gate_accepts_simple_vector_svg():
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="8" cy="8" r="6"/><line x1="0" y1="8" x2="2" y2="8"/></svg>'
    result = evaluate_quality_complexity_gate(GOOD_METRICS, svg)

    assert result["passed"] is True
    assert result["failures"] == []
    assert result["complexity"]["vector_element_count"] == 2


def test_quality_complexity_gate_rejects_embedded_raster_copy_even_when_pixel_near():
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,AAAA" width="16" height="16"/></svg>'
    result = evaluate_quality_complexity_gate(GOOD_METRICS, svg)

    assert result["passed"] is False
    assert "embedded_raster_copy" in result["failures"]


def test_quality_complexity_gate_rejects_unnecessary_path_complexity():
    commands = " ".join(f"L {idx} {idx % 7}" for idx in range(170))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg"><path d="M 0 0 {commands} Z"/></svg>'
    result = evaluate_quality_complexity_gate(GOOD_METRICS, svg)

    assert result["passed"] is False
    assert "path_command_count_above_max" in result["failures"]
    assert "path_complexity_ratio_above_max" in result["failures"]


def test_quality_complexity_gate_rejects_semantically_wrong_pixel_near_result():
    metrics = {**GOOD_METRICS, "pixel_similarity": 0.96, "semantic_score": 0.4, "combined_score": 0.86}
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="8" cy="8" r="6"/></svg>'
    result = evaluate_quality_complexity_gate(metrics, svg)

    assert result["passed"] is False
    assert "semantic_score_below_min" in result["failures"]
    assert "pixel_similarity_below_min" not in result["failures"]


def test_write_quality_complexity_gate_report_creates_machine_readable_contract(tmp_path: Path):
    output = tmp_path / "quality_gate.json"
    report = write_quality_complexity_gate_report(output)

    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == report
    assert report["schema_version"] == "quality_complexity_gate_v1"
    assert report["acceptance_contract"]["rejects_embedded_raster_copies"] is True
