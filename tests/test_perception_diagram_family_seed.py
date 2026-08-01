from __future__ import annotations

import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir_helpers
from tools.perception_detection_contract import (
    build_diagonal_circle_cross_diagram_geometry_ir,
    build_perception_seeded_geometry_ir,
    detect_diagonal_circle_cross_diagram_geometry_ir,
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


@pytest.mark.parametrize("sample", ["AC0502_1L_sia", "AC0502_1M_sia"])
def test_diagonal_circle_cross_detector_builds_seed_from_real_raster(
    sample: str,
) -> None:
    cv2 = pytest.importorskip("cv2")
    image = cv2.imread(f"artifacts/images_to_convert/{sample}.jpg")

    geometry_ir = detect_diagonal_circle_cross_diagram_geometry_ir(image)

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
    assert all(
        element["perception_seed"]["source"] == "raster_diagonal_circle_cross_detector"
        for element in geometry_ir
    )


def test_diagonal_circle_cross_detector_rejects_field_without_topology() -> None:
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    image = np.full((40, 80, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (56, 10), (75, 29), (72, 31, 223), thickness=-1)

    assert detect_diagonal_circle_cross_diagram_geometry_ir(image) == []


def test_generic_perception_pipeline_selects_detected_diagram_family() -> None:
    cv2 = pytest.importorskip("cv2")
    image = cv2.imread("artifacts/images_to_convert/AC0502_1L_sia.jpg")

    geometry_ir = build_perception_seeded_geometry_ir(image)

    assert geometry_ir[0]["id"] == "diagram_diagonal_connector"
    assert geometry_ir[-1]["id"] == "diagram_circle_anchor"
