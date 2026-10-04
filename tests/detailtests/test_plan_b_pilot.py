import pytest

from tools.evaluate_satisfaction_gate import BASELINE_SCHEMA_VERSION, seal_baseline_manifest
from tools.run_plan_b_pilot import build_envelope_svg, run_pilot


def test_envelope_primitive_scales_without_a_catalog_name():
    large = build_envelope_svg(80, 40)
    renamed_holdout = build_envelope_svg(60, 30)
    assert 'points="0,20.8 36.8,2 80,20.8"' in large
    assert 'points="0,15.6 27.6,1.5 60,15.6"' in renamed_holdout
    assert "<image" not in large


def test_pilot_requires_a_holdout(tmp_path):
    with pytest.raises(ValueError, match="holdout"):
        run_pilot({"cases": []}, tmp_path, tmp_path / "out")


def test_holdout_regression_prevents_positive_result(monkeypatch, tmp_path):
    for name in ("target.jpg", "foreign-name.jpg"):
        (tmp_path / name).write_bytes(b"input")
    metrics = {"error_per_pixel": .02, "edge_alignment": .9, "object_mask_iou": 1,
               "connector_continuity": 1, "semantic_score": 1, "dimension_match": 1}
    baseline = seal_baseline_manifest({"schema_version": BASELINE_SCHEMA_VERSION,
        "provenance": {"commit": "x", "seed": 0, "toolchain": {}, "input_hashes": {}},
        "cases": {name: {"dimensions": {"width": 10, "height": 10}, "metrics": metrics}
                  for name in ("target", "holdout")}})
    monkeypatch.setattr("tools.run_plan_b_pilot._dimensions", lambda path: (10, 10))
    values = iter((dict(metrics, error_per_pixel=.01), dict(metrics, edge_alignment=.8)))
    monkeypatch.setattr("tools.run_plan_b_pilot._render_metrics", lambda image, svg: next(values))
    report = run_pilot({"baseline": baseline, "cases": [
        {"case_id": "target", "role": "target", "image_path": "target.jpg", "description": "x"},
        {"case_id": "holdout", "role": "holdout", "image_path": "foreign-name.jpg", "description": "x"}]}, tmp_path, tmp_path / "svg")
    assert report["positive_result"] is False
    assert report["satisfaction_gate"]["cases"][0]["regressed_metrics"] == ["edge_alignment"]
