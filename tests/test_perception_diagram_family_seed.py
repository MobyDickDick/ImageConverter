from __future__ import annotations

import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir_helpers
from tools.perception_detection_contract import (
    build_diagonal_circle_cross_diagram_geometry_ir,
    build_diagonal_circle_step_diagram_geometry_ir,
    build_perception_seeded_geometry_ir,
    detect_diagonal_circle_cross_diagram_geometry_ir,
    detect_diagonal_circle_step_diagram_geometry_ir,
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


def test_diagonal_circle_step_seed_uses_distinct_topology() -> None:
    geometry_ir = build_diagonal_circle_step_diagram_geometry_ir([0.7, 0.25, 0.25, 0.5])

    assert [element["id"] for element in geometry_ir] == [
        "diagram_diagonal_connector",
        "diagram_horizontal_connector",
        "diagram_red_field",
        "diagram_step_trace",
        "diagram_field_border",
        "diagram_circle_anchor",
    ]
    assert all(
        element["perception_seed"]["detector"] == "normalized_step_primitive_relations"
        for element in geometry_ir
    )


def test_diagonal_circle_step_seed_constrains_measured_trace_geometry() -> None:
    geometry_ir = build_diagonal_circle_step_diagram_geometry_ir(
        [0.7, 0.25, 0.25, 0.5],
        step_points=[[0.99, 0.01], [0.75, 0.41], [0.25, 0.59], [0.01, 0.99]],
        step_stroke_ratio=0.2,
    )

    trace = geometry_ir[3]
    assert trace["points"] == [
        [0.9325, 0.29],
        [0.8875, 0.455],
        [0.7625, 0.545],
        [0.7175, 0.71],
    ]
    assert trace["stroke_width"] == pytest.approx(0.0225)


def test_step_detector_classifies_real_raster_but_rejects_cross_family() -> None:
    cv2 = pytest.importorskip("cv2")
    step_image = cv2.imread("artifacts/images_to_convert/AC0538_1L_sia.jpg")
    cross_image = cv2.imread("artifacts/images_to_convert/AC0502_1L_sia.jpg")

    geometry_ir = detect_diagonal_circle_step_diagram_geometry_ir(step_image)

    assert geometry_ir[3]["id"] == "diagram_step_trace"
    neutral_trace = build_diagonal_circle_step_diagram_geometry_ir(
        geometry_ir[2]["bbox"]
    )[3]
    assert geometry_ir[3]["points"] != neutral_trace["points"]
    assert geometry_ir[3]["stroke_width"] != neutral_trace["stroke_width"]
    assert detect_diagonal_circle_step_diagram_geometry_ir(cross_image) == []


def test_generic_perception_pipeline_selects_step_diagram_family() -> None:
    cv2 = pytest.importorskip("cv2")
    image = cv2.imread("artifacts/images_to_convert/AC0538_1L_sia.jpg")

    geometry_ir = build_perception_seeded_geometry_ir(image)

    assert geometry_ir[3]["id"] == "diagram_step_trace"
