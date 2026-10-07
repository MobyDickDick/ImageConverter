from __future__ import annotations

from pathlib import Path

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterStepDiagram import fit_step_diagram
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.run_plan_b_variations import measure_quality
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


def test_diagonal_circle_step_seed_accepts_guarded_raster_appearance() -> None:
    geometry_ir = build_diagonal_circle_step_diagram_geometry_ir(
        [0.7, 0.25, 0.25, 0.5],
        field_fill="#d02040",
        border_stroke="#777879",
        circle_bbox=[-2.0, 0.0, 0.9, 0.1],
    )

    assert geometry_ir[2]["fill"] == "#d02040"
    assert geometry_ir[4]["stroke"] == "#777879"
    assert geometry_ir[5]["bbox"] == [0.425, 0.35, 0.125, 0.125]


@pytest.mark.parametrize(
    "sample", ["AC0538_1L_sia", "AC0538_1M_sia", "AC0538_2L_sia"]
)
def test_step_detector_measures_appearance_across_size_and_color_variants(
    sample: str,
) -> None:
    cv2 = pytest.importorskip("cv2")
    image = cv2.imread(f"artifacts/images_to_convert/{sample}.jpg")

    geometry_ir = detect_diagonal_circle_step_diagram_geometry_ir(image)
    neutral = build_diagonal_circle_step_diagram_geometry_ir(geometry_ir[2]["bbox"])

    assert geometry_ir[2]["fill"] != neutral[2]["fill"]
    assert geometry_ir[4]["stroke"] != neutral[4]["stroke"]
    assert geometry_ir[5]["bbox"] != neutral[5]["bbox"]


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


# Raster registration and runtime generalization for the step diagram.
DESCRIPTION = ('Eine diagonale graue Verbindung von links unten nach rechts oben mit einem hellen Kreis. '
               'Eine horizontale Verbindung führt vom Kreis nach rechts zu einem farbigen, gerahmten '
               'Diagrammfeld mit weißer Stufenkurve und zwei senkrechten Endstücken.')
ROOT = Path(__file__).resolve().parents[1]


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def source(scale=1, color='#2768cc', offset=0):
    # Different field/circle separation, trace turns, stroke widths and pose
    # from the catalog task: the raster must determine each of these values.
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{110*scale}" height="{54*scale}">'
            f'<g transform="scale({scale}) translate({offset} 0)">'
            '<path d="M 34,23 H 70" stroke="#797979" stroke-width="1.7"/>'
            f'<rect x="70" y="9" width="24" height="24" fill="{color}" stroke="#797979" stroke-width="1.3"/>'
            '<polyline points="88,12.6 88,17.4 76,24.6 76,28.9" fill="none" stroke="white" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>'
            '<path d="M 17,40 L 51,6" stroke="#797979" stroke-width="2.4" stroke-linecap="round"/>'
            '<circle cx="34" cy="23" r="4" fill="#eeeeee" stroke="#797979" stroke-width="1.6"/>'
            '</g></svg>')


def fit(image, description=DESCRIPTION, render_fn=render, error_fn=None):
    h, w = image.shape[:2]
    return fit_step_diagram(w, h, description=description, image=image, render_fn=render_fn,
                            error_fn=error_fn or (lambda a, b: float(np.square(a.astype(float)-b).mean())))


@pytest.mark.parametrize('scale,color,offset', [(1, '#2768cc', 0), (2, '#339944', 4), (1, '#bc395a', -6)])
def test_raster_geometry_generalizes_independent_parts_size_pose_and_color(scale, color, offset):
    image = render(source(scale, color, offset), 110*scale, 54*scale)
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error'] < result['initial_error']
    assert result['evaluations'] <= 529
    assert measure_quality(image, result['svg'])['satisfactory']
    np.testing.assert_array_equal(image, original)
    assert '<image' not in result['svg']
    assert abs(result['parameters'][10]-(34+offset)*scale) < 1
    assert abs(result['parameters'][0]-(70+offset)*scale) < 1


@pytest.mark.parametrize('case', ['probe_04', 'probe_06'])
def test_diagonal_is_joined_across_occluding_circle(case):
    # Recreate the seeded raster, without depending on untracked run artifacts.
    from tools.run_plan_b_variations import make_variations
    svg = (ROOT/'artifacts/images_to_convert/samples/AC0538_1L_sia.svg').read_text(encoding='utf-8')
    cases = make_variations(svg, DESCRIPTION, 3948009396310964094)
    item = next(c for c in cases if c['case_id'] == case)
    image = render(item['svg'], item['width'], item['height'])
    result = fit(image)
    assert result is not None
    assert measure_quality(image, result['svg'])['satisfactory']
    assert result['parameters'][5] < result['parameters'][10] < result['parameters'][7]


def test_runtime_is_rename_invariant_and_bypasses_sample_and_embedding(monkeypatch):
    image = render(source(), 110, 54)
    outputs = []
    def forbidden(*args, **kwargs):
        pytest.fail('Diagram fitting must use only the raster and description')
    monkeypatch.setattr(runtime, '_try_load_sample_svg', forbidden)
    for name in ('task', 'anonymous_holdout'):
        logs = []
        result = runtime.runNonCompositeIterationImpl(
            mode='non_composite', params={}, stripe_strategy=None, semantic_mode_visual_override=False,
            width=110, height=54, base_name=name, description=DESCRIPTION, perc_img=image, img_path=name+'.png',
            print_fn=lambda *args: None, render_embedded_raster_svg_fn=forbidden,
            build_gradient_stripe_svg_fn=forbidden, build_gradient_stripe_validation_log_lines_fn=forbidden,
            write_validation_log_fn=logs.append, render_svg_to_numpy_fn=render,
            record_render_failure_fn=forbidden, write_attempt_artifacts_fn=lambda svg, raster: outputs.append(svg),
            calculate_error_fn=lambda a, b: float(np.square(a.astype(float)-b).mean()))
        assert result is not None
        assert logs == [['status=non_composite_raster_step_diagram']]
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize('description', ['Ein Kreis.', DESCRIPTION+' mit Text',
                                         DESCRIPTION+' mit Kreuz', DESCRIPTION+' Zusätzlich ein Quadrat',
                                         DESCRIPTION.replace('nach rechts zu', 'nach links zu'),
                                         DESCRIPTION.replace('links unten nach rechts oben', 'links oben nach rechts unten')])
def test_incompatible_descriptions_are_rejected(description):
    assert fit(render(source(), 110, 54), description) is None


@pytest.mark.parametrize('mutation', ['no_circle', 'no_diagonal', 'no_horizontal', 'cross', 'extra'])
def test_missing_topology_and_additional_objects_are_rejected(mutation):
    svg = source()
    if mutation == 'no_circle':
        import re
        svg = re.sub(r'<circle[^>]*/>', '', svg)
    elif mutation == 'no_diagonal':
        svg = svg.replace('M 17,40 L 51,6', 'M 17,40 L 17,6')
    elif mutation == 'no_horizontal':
        svg = svg.replace('M 34,23 H 70', 'M 34,23 H 35')
    elif mutation == 'cross':
        svg = svg.replace('88,12.6 88,17.4 76,24.6 76,28.9', '74,12 91,30 91,12 74,30')
    else:
        svg = svg.replace('</g>', '<rect x="4" y="4" width="6" height="6" fill="black"/></g>')
    assert fit(render(svg, 110, 54)) is None


@pytest.mark.parametrize('error', [42., float('inf'), float('nan')])
def test_non_improving_or_invalid_scores_are_rejected(error):
    assert fit(render(source(), 110, 54), error_fn=lambda a, b: error) is None


def test_invalid_image_and_renderer_are_rejected():
    assert fit_step_diagram(20, 20, description=DESCRIPTION, image=None,
                            render_fn=render, error_fn=lambda a, b: 0) is None
    assert fit(render(source(), 110, 54), render_fn=lambda *args: None) is None
