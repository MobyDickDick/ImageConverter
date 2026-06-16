from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("numpy")

import numpy as np

from src.iCCModules.imageCompositeConverterGeometryIr import renderGeometryIrToSvgImpl
from tools.perception_detection_contract import (
    PerceptionPrimitiveCandidate,
    merge_perception_candidates_into_geometry_ir,
)


def _candidate(kind: str, geometry: dict[str, Any], *, color: dict[str, Any] | None = None) -> PerceptionPrimitiveCandidate:
    return PerceptionPrimitiveCandidate(
        schema_version="perception_primitive_candidate_v1",
        kind=kind,
        bbox={"x": 10.0, "y": 12.0, "width": 30.0, "height": 24.0},
        center={"x": 25.0, "y": 24.0},
        geometry=geometry,
        color={
            "fill_rgb": None,
            "stroke_rgb": None,
            "fill_hex": None,
            "stroke_hex": None,
            "fill_confidence": 0.0,
            "stroke_confidence": 0.0,
            **(color or {}),
        },
        confidence=0.91,
        roi={"type": "image", "hint": "synthetic", "bbox": {"x": 0, "y": 0, "width": 100, "height": 80}},
        evidence={"detector": f"synthetic_{kind}_detector"},
        source="ido07_synthetic_roundtrip",
    )


@pytest.mark.parametrize(
    ("kind", "geometry", "expected_ir_kind", "expected_svg"),
    [
        (
            "circle",
            {"geometry_ir_bbox": [0.25, 0.2, 0.35, 0.35], "stroke_width_px": 2.0},
            "CircleBackground",
            "<ellipse",
        ),
        (
            "line",
            {"orientation": "vertical", "stroke_width_px": 2.0},
            "OrthogonalPolyline",
            "<path",
        ),
        ("rectangle", {"width_px": 30.0, "height_px": 24.0}, "RectBorder", "<rect"),
        (
            "polygon",
            {"points": [[0.2, 0.2], [0.8, 0.25], [0.5, 0.75]]},
            "PolygonPath",
            "<path",
        ),
        (
            "path",
            {"points": [[0.1, 0.4], [0.5, 0.2], [0.9, 0.6]]},
            "PolygonPath",
            "<path",
        ),
        ("text_glyph", {"text": "M", "glyph": "M"}, "TextGlyph", ">M</text>"),
        ("text_area", {"text": "VOC"}, "TextGlyph", ">VOC</text>"),
        ("color", {}, "ColorPatch", "<rect"),
    ],
)
def test_ido07_supported_perception_candidate_roundtrips_to_geometry_ir_and_svg(
    kind: str, geometry: dict[str, Any], expected_ir_kind: str, expected_svg: str
) -> None:
    image = np.full((80, 100, 3), 255, dtype=np.uint8)
    candidate = _candidate(
        kind,
        geometry,
        color={"fill_hex": "#abcdef", "stroke_hex": "#123456"},
    )

    geometry_ir = merge_perception_candidates_into_geometry_ir(image, [candidate], [])
    matching = [element for element in geometry_ir if element.get("kind") == expected_ir_kind]

    assert matching, geometry_ir
    assert matching[0]["perception_seed"]["kind"] == kind
    assert matching[0]["perception_seed"]["candidate_schema_version"] == "perception_primitive_candidate_v1"

    svg = renderGeometryIrToSvgImpl(100, 80, geometry_ir)
    assert expected_svg in svg
    assert "ido07_synthetic_roundtrip" not in svg
