from __future__ import annotations

import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir_helpers
from tools.perception_detection_contract import (
    build_diagonal_circle_cross_diagram_geometry_ir,
)


@pytest.mark.parametrize(
    ("viewport", "field_bbox"),
    [
        ((80, 40), [55.943359 / 80, 9.6748 / 40, 20 / 80, 20 / 40]),
        ((60, 30), [41.544163 / 60, 7.108537 / 30, 16 / 60, 16 / 30]),
    ],
)
def test_diagonal_circle_cross_seed_scales_from_the_detected_field(
    viewport: tuple[int, int], field_bbox: list[float]
) -> None:
    geometry_ir = build_diagonal_circle_cross_diagram_geometry_ir(field_bbox)

    assert [element["kind"] for element in geometry_ir] == [
        "PolygonPath",
        "PolygonPath",
        "ColorPatch",
        "PolygonPath",
        "PolygonPath",
        "RectBorder",
        "CircleBackground",
    ]
    assert all(
        element["perception_seed"]["detector"] == "normalized_primitive_relations"
        for element in geometry_ir
    )

    width, height = viewport
    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(width, height, geometry_ir)
    assert f'width="{width}"' in svg
    assert 'id="diagram_circle_anchor"' in svg
    assert 'id="diagram_cross_rising"' in svg


def test_diagonal_circle_cross_seed_rejects_invalid_field_geometry() -> None:
    with pytest.raises(ValueError, match="positive"):
        build_diagonal_circle_cross_diagram_geometry_ir([0.5, 0.5, 0.0, 0.2])
