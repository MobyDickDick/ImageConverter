from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("numpy")

from tools.perception_detection_contract import (
    build_circle_seeded_geometry_ir,
    detect_circle_ring_candidates,
    merge_circle_ring_candidates_into_geometry_ir,
    run_circle_ring_seed_report,
)
from tools.shape_detection_eval import make_synthetic_image


def test_circle_ring_candidates_expose_circle_background_seed_geometry() -> None:
    image = make_synthetic_image("ring", "synthetic")
    candidates = detect_circle_ring_candidates(image, source="test")

    ring_candidates = [
        candidate for candidate in candidates if candidate.kind == "ring"
    ]
    assert ring_candidates
    top = ring_candidates[0].to_dict()
    assert top["schema_version"] == "perception_primitive_candidate_v1"
    assert top["geometry"]["geometry_ir_kind"] == "CircleBackground"
    assert top["geometry"]["ring"] is True
    assert len(top["geometry"]["geometry_ir_bbox"]) == 4
    assert top["evidence"]["detector"] == "detect_circle_rings"


def test_circle_ring_candidate_merges_into_existing_circle_background() -> None:
    image = make_synthetic_image("circle", "synthetic")
    base_ir = [
        {
            "kind": "CircleBackground",
            "id": "compressor_circle",
            "bbox": [0.06, 0.06, 0.88, 0.88],
            "fill": "#45aa5e",
            "stroke": "#8d8d8d",
            "stroke_width": 0.02,
        },
        {"kind": "RightwardCompressorGlyph", "circle_ref": "compressor_circle"},
    ]

    merged = merge_circle_ring_candidates_into_geometry_ir(
        image, detect_circle_ring_candidates(image), base_ir
    )

    assert [element["kind"] for element in merged] == [
        "CircleBackground",
        "RightwardCompressorGlyph",
    ]
    circle = merged[0]
    assert circle["id"] == "compressor_circle"
    assert circle["perception_seed"]["kind"] == "circle"
    assert circle["perception_seed"]["detector"] == "detect_circle_rings"
    assert circle["bbox"] != [0.06, 0.06, 0.88, 0.88]


def test_build_circle_seeded_geometry_ir_adds_circle_background_to_description_ir() -> (
    None
):
    image = make_synthetic_image("ring", "synthetic")
    seeded_ir = build_circle_seeded_geometry_ir(
        image, description="Plain-Ring Kreis Hintergrund"
    )

    assert seeded_ir
    assert seeded_ir[0]["kind"] == "CircleBackground"
    assert seeded_ir[0]["perception_seed"]["kind"] == "ring"


def test_run_circle_ring_seed_report_writes_json_report(tmp_path: Path) -> None:
    summary = run_circle_ring_seed_report(tmp_path)
    assert summary["samples"] >= 2
    assert summary["all_matched"] is True
    assert (tmp_path / "perception_circle_ring_seed_report_v1.json").exists()
