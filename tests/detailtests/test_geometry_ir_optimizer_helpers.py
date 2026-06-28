from __future__ import annotations

import pytest

from src.iCCModules import imageCompositeConverterGeometryIrOptimizer as optimizer_helpers


def test_sequential_optimizer_accepts_only_improving_element_candidates() -> None:
    ir = [
        {"kind": "RectBorder", "id": "rect", "bbox": [0.2, 0.2, 0.5, 0.5]},
        {"kind": "DiagonalBand", "id": "diag", "stroke_width": 0.08},
    ]

    def render_fn(candidate_ir):
        return candidate_ir

    def error_fn(candidate_ir):
        rect_x = candidate_ir[0]["bbox"][0]
        stroke_width = candidate_ir[1]["stroke_width"]
        return abs(rect_x - 0.3) + abs(stroke_width - 0.04)

    def candidates(element, _current_ir, step_index):
        if step_index == 0:
            yield {**element, "bbox": [0.1, 0.2, 0.5, 0.5]}
            yield {**element, "bbox": [0.3, 0.2, 0.5, 0.5]}
        else:
            yield {**element, "stroke_width": 0.12}
            yield {**element, "stroke_width": 0.04}

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=render_fn,
        error_fn=error_fn,
        candidate_provider=candidates,
    )

    assert result["mode"] == "elementwise_geometry_ir"
    assert result["geometry_ir"][0]["bbox"][0] == 0.3
    assert result["geometry_ir"][1]["stroke_width"] == 0.04
    assert result["final_error"] == 0.0
    assert [step["accepted"] for step in result["steps"]] == [True, True]
    assert set(result["steps"][0]) >= {"step_index", "element", "best_delta", "accepted"}


def test_sequential_optimizer_rejects_regression_and_keeps_current_ir() -> None:
    ir = [{"kind": "RectBorder", "id": "rect", "bbox": [0.3, 0.2, 0.5, 0.5]}]

    def candidates(element, _current_ir, _step_index):
        yield {**element, "bbox": [0.1, 0.2, 0.5, 0.5]}

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: abs(candidate_ir[0]["bbox"][0] - 0.3),
        candidate_provider=candidates,
    )

    assert result["geometry_ir"] == ir
    assert result["steps"] == [
        {
            "step_index": 0,
            "element": "rect",
            "best_delta": 0.0,
            "accepted": False,
            "error_before": 0.0,
            "error_after": 0.0,
        }
    ]


def test_default_optimizer_refines_neutral_rect_fill_color() -> None:
    ir = [{"kind": "RectBorder", "id": "rect", "bbox": [0.0, 0.0, 1.0, 1.0], "fill": "#e8e8e8"}]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: 0.0
        if candidate_ir[0]["fill"] == "#b1c1cc"
        else 10.0,
    )

    assert result["geometry_ir"][0]["fill"] == "#b1c1cc"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_neutral_rect_to_warm_light_fill() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_square",
            "role": "reference_light_grey_square",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: 0.0
        if candidate_ir[0]["fill"] == "#f2b8b4"
        else 10.0,
    )

    assert result["geometry_ir"][0]["fill"] == "#f2b8b4"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_neutral_rect_to_green_tinted_fill() -> None:
    ir = [{"kind": "ColorPatch", "id": "background", "bbox": [0.0, 0.0, 1.0, 1.0], "fill": "#ffffff"}]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: 0.0
        if candidate_ir[0]["fill"] == "#bfd4ba"
        else 10.0,
    )

    assert result["geometry_ir"][0]["fill"] == "#bfd4ba"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_locally() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "checkmark",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: abs(candidate_ir[0]["points"][1][1] - 0.72),
    )

    assert result["geometry_ir"][0]["points"][1][1] == pytest.approx(0.72)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_with_neutral_palette() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "checkmark_shadow",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#888888",
            "stroke_width": 0.08,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: 0.0
        if candidate_ir[0]["stroke"] == "#969696"
        else 10.0,
    )

    assert result["geometry_ir"][0]["stroke"] == "#969696"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_fill_with_chart_palette() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "upper_red_triangle",
            "points": [[0.28, 0.16], [0.72, 0.16], [0.48, 0.5]],
            "fill": "#e10821",
            "stroke": "#343434",
            "stroke_width": 0.024,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: 0.0
        if candidate_ir[0]["fill"] == "#e3162a"
        else 10.0,
    )

    assert result["geometry_ir"][0]["fill"] == "#e3162a"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_absolute_probe() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "antialias_sensitive_triangle",
            "points": [[0.28, 0.16], [0.72, 0.16], [0.48, 0.5]],
            "fill": "#e10821",
            "stroke": "#343434",
            "stroke_width": 0.024,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: 0.0
        if candidate_ir[0]["stroke_width"] == 0.034
        else 10.0,
    )

    assert result["geometry_ir"][0]["stroke_width"] == 0.034
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_linecap_and_linejoin() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "checkmark",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "linecap": "butt",
            "linejoin": "round",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: 0.0
        if candidate_ir[0]["linejoin"] == "bevel"
        else (1.0 if candidate_ir[0]["linecap"] == "square" else 10.0),
    )

    assert result["geometry_ir"][0]["linejoin"] == "bevel"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_select_geometry_ir_prefers_elementwise_result_and_requires_explicit_one_shot_emergency() -> None:
    optimized = [{"kind": "RectBorder", "id": "optimized"}]
    raw = [{"kind": "RectBorder", "id": "raw"}]
    emergency = [{"kind": "RectBorder", "id": "emergency"}]

    params = {"optimized_geometry_ir": optimized, "geometry_ir": raw}
    assert optimizer_helpers.selectGeometryIrForRenderingImpl(params) == optimized
    assert params["geometry_phase_mode"] == "elementwise_geometry_ir"

    params = {"one_shot_emergency_geometry_ir": emergency}
    assert optimizer_helpers.selectGeometryIrForRenderingImpl(params) == []
    assert params["geometry_phase_mode"] == "no_geometry_ir"

    params = {"one_shot_emergency_geometry_ir": emergency, "allow_one_shot_emergency": True}
    assert optimizer_helpers.selectGeometryIrForRenderingImpl(params) == emergency
    assert params["geometry_phase_mode"] == "one_shot_emergency"


def test_transform_geometry_ir_preserves_semantics_and_transforms_supported_geometry() -> None:
    ir = [
        {
            "kind": "ExampleGlyph",
            "id": "semantic-id",
            "body_paths": [[[0.2, 0.3], [0.4, 0.5]]],
            "body_bbox": [0.2, 0.3, 0.4, 0.5],
            "circle": [0.7, 0.6, 0.1],
            "connector": [[0.4, 0.5], [0.6, 0.5]],
            "blade_points": [[0.2, 0.5], [0.6, 0.2], [0.6, 0.8]],
            "label": "M",
            "font_size": 0.2,
            "stroke_width": 0.04,
            "connector_width": 0.06,
        }
    ]

    transformed = optimizer_helpers.transformGeometryIrImpl(
        ir,
        translate_x=0.1,
        translate_y=-0.1,
        scale_x=2.0,
        scale_y=0.5,
        stroke_scale=1.5,
    )

    assert transformed[0]["id"] == "semantic-id"
    assert transformed[0]["label"] == "M"
    assert transformed[0]["body_paths"][0][0] == pytest.approx([0.0, 0.3])
    assert transformed[0]["body_paths"][0][1] == pytest.approx([0.4, 0.4])
    assert transformed[0]["body_bbox"] == pytest.approx([0.0, 0.3, 0.8, 0.25])
    assert transformed[0]["circle"] == pytest.approx([1.0, 0.45, 0.05])
    assert transformed[0]["connector"][0] == pytest.approx([0.4, 0.4])
    assert transformed[0]["connector"][1] == pytest.approx([0.8, 0.4])
    assert transformed[0]["blade_points"][0] == pytest.approx([0.0, 0.4])
    assert transformed[0]["blade_points"][1] == pytest.approx([0.8, 0.25])
    assert transformed[0]["blade_points"][2] == pytest.approx([0.8, 0.55])
    assert transformed[0]["font_size"] == 0.1
    assert transformed[0]["stroke_width"] == 0.06
    assert transformed[0]["connector_width"] == 0.09
    assert ir[0]["circle"] == [0.7, 0.6, 0.1]


def test_registration_optimizer_reduces_error_without_changing_semantic_shape() -> None:
    ir = [
        {
            "kind": "CircleGlyph",
            "id": "circle",
            "circle": [0.3, 0.5, 0.2],
            "stroke_width": 0.04,
        }
    ]

    def error_fn(candidate_ir):
        circle = candidate_ir[0]["circle"]
        return (
            abs(circle[0] - 0.36)
            + abs(circle[1] - 0.48)
            + abs(circle[2] - 0.18)
            + abs(candidate_ir[0]["stroke_width"] - 0.05)
        )

    result = optimizer_helpers.optimizeGeometryIrRegistrationImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=error_fn,
    )

    assert result["final_error"] < result["initial_error"]
    assert result["geometry_ir"][0]["kind"] == "CircleGlyph"
    assert result["geometry_ir"][0]["id"] == "circle"
    assert result["steps"]
    assert set(result["parameters"]) == {
        "translate_x",
        "translate_y",
        "scale_x",
        "scale_y",
        "stroke_scale",
    }


def test_registration_optimizer_continues_coarse_stage_until_convergence() -> None:
    ir = [{"kind": "CircleGlyph", "id": "circle", "circle": [0.5, 0.5, 0.2]}]

    result = optimizer_helpers.optimizeGeometryIrRegistrationImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: abs(candidate_ir[0]["circle"][0] - 1.1),
    )

    assert result["final_error"] == pytest.approx(0.0)
    assert result["geometry_ir"][0]["circle"][0] == pytest.approx(1.1)
    translate_steps = [
        step for step in result["steps"] if step["parameter"] == "translate_x"
    ]
    assert len(translate_steps) > 4


def test_right_rotated_valve_refinement_fits_relative_geometry_and_palette() -> None:
    ir = [
        {
            "kind": "RightRotatedTopKelleThreeWayValveGlyph",
            "id": "right_rotated_top_kelle_three_way_valve",
            "body_paths": [
                [[0.61, 0.50], [0.455, 0.98], [0.765, 0.98]],
                [[0.61, 0.50], [0.455, 0.02], [0.765, 0.02]],
                [[0.61, 0.50], [0.96, 0.667], [0.96, 0.333]],
            ],
            "circle": [0.235, 0.50, 0.225],
            "connector": [[0.45, 0.50], [0.61, 0.50]],
            "body_fill": "url(#body)",
            "circle_fill": "url(#circle)",
            "stroke": "#969696",
            "connector_stroke": "#8f8f8f",
            "stroke_width": 0.04,
            "connector_width": 0.075,
        }
    ]

    def gray(value: str, fallback: int) -> int:
        return fallback if value.startswith("url(") else int(value[1:3], 16)

    def error_fn(candidate_ir):
        element = candidate_ir[0]
        return (
            abs(element["circle"][0] - 0.715)
            + abs(element["circle"][2] - 0.19)
            + abs(element["body_paths"][2][1][1] - 0.72)
            + abs(gray(element["body_fill"], 215) - 195) / 255.0
            + abs(gray(element["circle_fill"], 250) - 240) / 255.0
        )

    result = optimizer_helpers.refineRightRotatedValveGeometryImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=error_fn,
    )

    assert result["final_error"] < result["initial_error"]
    assert result["geometry_ir"][0]["kind"] == "RightRotatedTopKelleThreeWayValveGlyph"
    assert result["geometry_ir"][0]["circle"][0] == pytest.approx(0.715)
    assert result["geometry_ir"][0]["body_fill"] == "#c3c3c3"
    assert result["geometry_ir"][0]["circle_fill"] == "#f0f0f0"
    circle_x_steps = [
        step for step in result["steps"] if step["parameter"] == "circle_x"
    ]
    assert len(circle_x_steps) > 4


def test_default_optimizer_refines_rect_bbox_with_fine_edge_probe() -> None:
    ir = [{"kind": "RectBorder", "id": "rect", "bbox": [0.0, 0.0, 1.0, 1.0], "fill": "#e8e8e8"}]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: 0.0
        if candidate_ir[0]["bbox"] == [0.01, 0.0, 1.0, 1.0]
        else 10.0,
    )

    assert result["geometry_ir"][0]["bbox"] == [0.01, 0.0, 1.0, 1.0]
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True
