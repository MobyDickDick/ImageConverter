from __future__ import annotations

import pytest

pytest.importorskip("cv2")
pytest.importorskip("numpy")

from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir_helpers
from tools.perception_detection_contract import (
    build_perception_seeded_geometry_ir,
    run_perception_seeded_geometry_ir_report,
)
from tools.shape_detection_eval import make_synthetic_image


def test_perception_seeded_geometry_ir_adds_horizontal_rule_before_symbol_fit() -> None:
    image = make_synthetic_image("minus", "synthetic")

    seeded_ir = build_perception_seeded_geometry_ir(
        image,
        description="oben mittig befindet sich eine Markierung",
        source="test_pf4_seed",
    )

    horizontal_rule = next(
        element for element in seeded_ir if element.get("kind") == "HorizontalRule"
    )
    assert horizontal_rule["perception_seed"]["kind"] == "horizontal_rule"
    assert horizontal_rule["perception_seed"]["source"] == "test_pf4_seed"
    assert len(horizontal_rule["bbox"]) == 4

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(120, 120, seeded_ir)
    assert 'id="perception_horizontal_rule"' in svg


def test_perception_seeded_geometry_ir_combines_description_and_circle_seed() -> None:
    image = make_synthetic_image("circle", "synthetic")

    seeded_ir = build_perception_seeded_geometry_ir(
        image,
        description="Kompressor grau nach rechts",
    )

    assert [element.get("kind") for element in seeded_ir][:2] == [
        "CircleBackground",
        "RightwardCompressorGlyph",
    ]
    assert seeded_ir[0]["perception_seed"]["kind"] == "circle"


def test_run_perception_seeded_geometry_ir_report_writes_json(tmp_path) -> None:
    summary = run_perception_seeded_geometry_ir_report(tmp_path)

    assert summary["samples"] == 2
    assert summary["all_matched"] is True
    assert (tmp_path / "perception_seeded_geometry_ir_report_v1.json").exists()
