from __future__ import annotations

import pytest

from src.iCCModules import (
    imageCompositeConverterGeometryIrOptimizer as optimizer_helpers,
)


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
    assert set(result["steps"][0]) >= {
        "step_index",
        "element",
        "best_delta",
        "accepted",
    }


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


def test_default_optimizer_refines_rect_bbox_with_subpixel_probe() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head",
            "bbox": [0.10, 0.10, 0.80, 0.80],
            "fill": "#f2b8b4",
            "stroke": "#8a8a8a",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if abs(candidate_ir[0]["bbox"][0] - 0.105) < 1e-9 else 10.0
        ),
    )

    assert result["geometry_ir"][0]["bbox"][0] == pytest.approx(0.105)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_neutral_rect_fill_color() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "rect",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#b1c1cc" else 10.0
        ),
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
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f2b8b4" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f2b8b4"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_to_fine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f2b8b4",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f2bab6" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f2bab6"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_to_subfine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill_subfine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f2bab6",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f2bbb7" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f2bbb7"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_neutral_rect_to_green_tinted_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "background",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#ffffff",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#bfd4ba" else 10.0
        ),
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


def test_default_optimizer_refines_polygon_path_points_with_fine_local_probe() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "fine_checkmark",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["points"][1][1] == 0.71 else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][1][1] == pytest.approx(0.71)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_subpixel_probe() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "subpixel_triangle",
            "points": [[0.28, 0.16], [0.72, 0.16], [0.48, 0.50]],
            "fill": "#e10821",
            "stroke": "#343434",
            "stroke_width": 0.024,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["points"][2][0] == 0.485 else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.485)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_subfine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "subfine_subpixel_triangle",
            "points": [[0.28, 0.16], [0.72, 0.16], [0.48, 0.50]],
            "fill": "#e10821",
            "stroke": "#343434",
            "stroke_width": 0.024,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["points"][2][0] == pytest.approx(0.4825) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.4825)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_ultrafine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "ultrafine_subpixel_triangle",
            "points": [[0.28, 0.16], [0.72, 0.16], [0.48, 0.50]],
            "fill": "#e10821",
            "stroke": "#343434",
            "stroke_width": 0.024,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["points"][2][0] == pytest.approx(0.48125) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.48125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_microfine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "microfine_subpixel_triangle",
            "points": [[0.28, 0.16], [0.72, 0.16], [0.48, 0.50]],
            "fill": "#e10821",
            "stroke": "#343434",
            "stroke_width": 0.024,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["points"][2][0] == pytest.approx(0.480625) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.480625)
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
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke"] == "#969696" else 10.0
        ),
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
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#e3162a" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#e3162a"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_absolute_probe() -> (
    None
):
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
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke_width"] == 0.034 else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == 0.034
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_fine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "fine_antialias_sensitive_triangle",
            "points": [[0.28, 0.16], [0.72, 0.16], [0.48, 0.5]],
            "fill": "#e10821",
            "stroke": "#343434",
            "stroke_width": 0.024,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke_width"] == 0.029 else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.029)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_subfine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "subfine_antialias_sensitive_triangle",
            "points": [[0.28, 0.16], [0.72, 0.16], [0.48, 0.5]],
            "fill": "#e10821",
            "stroke": "#343434",
            "stroke_width": 0.024,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.0265) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0265)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_microfine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem",
            "bbox": [0.45, 0.64, 0.10, 0.34],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.055625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.055625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_nanofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem_nanofine",
            "bbox": [0.45, 0.64, 0.10, 0.34],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.0553125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0553125)
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
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["linejoin"] == "bevel"
            else (1.0 if candidate_ir[0]["linecap"] == "square" else 10.0)
        ),
    )

    assert result["geometry_ir"][0]["linejoin"] == "bevel"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_opacity() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "soft-checkmark",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_opacity": 1.0,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0].get("stroke_opacity") == 0.85 else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.85)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_gradient_stops() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "100%", "color": "#43ad49"},
                ],
            },
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_gradient"]["stops"][1]["color"] == "#8fc78e"
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_gradient"]["stops"][1]["color"] == "#8fc78e"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "55%", "color": "#43ad49"},
                    {"offset": "100%", "color": "#c8d0c3"},
                ],
            },
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_gradient"]["stops"][1]["offset"] == "50%"
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_gradient"]["stops"][1]["offset"] == "50%"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_fine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "52.5%", "color": "#43ad49"},
                    {"offset": "100%", "color": "#c8d0c3"},
                ],
            },
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_gradient"]["stops"][1]["offset"] == "50%"
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_gradient"]["stops"][1]["offset"] == "50%"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_subfine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-subfine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "51.25%", "color": "#43ad49"},
                    {"offset": "100%", "color": "#c8d0c3"},
                ],
            },
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_gradient"]["stops"][1]["offset"] == "50%"
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_gradient"]["stops"][1]["offset"] == "50%"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_ultrafine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-ultrafine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.625%", "color": "#43ad49"},
                    {"offset": "100%", "color": "#c8d0c3"},
                ],
            },
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_gradient"]["stops"][1]["offset"] == "50%"
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_gradient"]["stops"][1]["offset"] == "50%"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_select_geometry_ir_prefers_elementwise_result_and_requires_explicit_one_shot_emergency() -> (
    None
):
    optimized = [{"kind": "RectBorder", "id": "optimized"}]
    raw = [{"kind": "RectBorder", "id": "raw"}]
    emergency = [{"kind": "RectBorder", "id": "emergency"}]

    params = {"optimized_geometry_ir": optimized, "geometry_ir": raw}
    assert optimizer_helpers.selectGeometryIrForRenderingImpl(params) == optimized
    assert params["geometry_phase_mode"] == "elementwise_geometry_ir"

    params = {"one_shot_emergency_geometry_ir": emergency}
    assert optimizer_helpers.selectGeometryIrForRenderingImpl(params) == []
    assert params["geometry_phase_mode"] == "no_geometry_ir"

    params = {
        "one_shot_emergency_geometry_ir": emergency,
        "allow_one_shot_emergency": True,
    }
    assert optimizer_helpers.selectGeometryIrForRenderingImpl(params) == emergency
    assert params["geometry_phase_mode"] == "one_shot_emergency"


def test_transform_geometry_ir_preserves_semantics_and_transforms_supported_geometry() -> (
    None
):
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


def test_default_optimizer_refines_rect_border_stroke_with_neutral_palette() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_border",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
            "stroke": "#888888",
            "stroke_width": 0.04,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke"] == "#adadad" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke"] == "#adadad"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_bbox_with_fine_edge_probe() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "rect",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["bbox"] == [0.01, 0.0, 1.0, 1.0] else 10.0
        ),
    )

    assert result["geometry_ir"][0]["bbox"] == [0.01, 0.0, 1.0, 1.0]
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_width_with_fine_probe() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_border",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
            "stroke": "#8a8a8a",
            "stroke_width": 0.04,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.035) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.035)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_opacity_with_neutral_probe() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_square",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
            "stroke": "#8a8a8a",
            "fill_opacity": 1.0,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0].get("fill_opacity") == 0.95 else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.95)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_fine_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_light_grey_fill",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
            "fill_opacity": 0.95,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0].get("fill_opacity") == pytest.approx(0.925) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.925)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_fine_probe() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_outline",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "none",
            "stroke": "#8a8a8a",
            "stroke_opacity": 0.95,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.975)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.975)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_subfine_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_light_grey_fill_subfine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
            "fill_opacity": 0.95,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.9375)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.9375)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_subfine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_outline_subfine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "none",
            "stroke": "#8a8a8a",
            "stroke_opacity": 0.975,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.9875)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.9875)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True

def test_default_optimizer_refines_vertical_rule_stroke_width_with_fine_probe() -> None:
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem",
            "bbox": [0.46, 0.56, 0.08, 0.32],
            "stroke": "#666666",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.050) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.050)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_horizontal_rule_stroke_width_with_fine_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm",
            "bbox": [0.02, 0.48, 0.30, 0.08],
            "stroke": "#666666",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.060) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.060)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_bbox_with_subpixel_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "neutral_fill_patch",
            "bbox": [0.10, 0.20, 0.30, 0.40],
            "fill": "#e8e8e8",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["bbox"][1] == pytest.approx(0.1975) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["bbox"][1] == pytest.approx(0.1975)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_bbox_with_subpixel_probe() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "neutral_rect_border",
            "bbox": [0.10, 0.20, 0.30, 0.40],
            "fill": "#e8e8e8",
            "stroke": "#8a8a8a",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["bbox"][2] == pytest.approx(0.3025) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["bbox"][2] == pytest.approx(0.3025)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True

def test_default_optimizer_refines_vertical_rule_stroke_width_with_subfine_probe() -> (
    None
):
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem_subfine",
            "bbox": [0.46, 0.56, 0.08, 0.32],
            "stroke": "#666666",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.0525) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0525)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_horizontal_rule_stroke_width_with_subfine_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_subfine",
            "bbox": [0.02, 0.48, 0.30, 0.08],
            "stroke": "#666666",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.0575) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0575)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_vertical_rule_stroke_width_with_ultrafine_probe() -> (
    None
):
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem_ultrafine",
            "bbox": [0.46, 0.56, 0.08, 0.32],
            "stroke": "#666666",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.05375) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05375)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_horizontal_rule_stroke_width_with_ultrafine_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_ultrafine",
            "bbox": [0.02, 0.48, 0.30, 0.08],
            "stroke": "#666666",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.05625) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True

def test_default_optimizer_refines_color_patch_opacity_with_ultrafine_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_light_grey_fill_ultrafine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
            "fill_opacity": 0.95,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.94375)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.94375)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_ultrafine_probe() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_outline_ultrafine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "none",
            "stroke": "#8a8a8a",
            "stroke_opacity": 0.9875,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.98125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.98125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_bbox_with_ultrafine_subpixel_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "neutral_fill_patch_ultrafine",
            "bbox": [0.10, 0.20, 0.30, 0.40],
            "fill": "#e8e8e8",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["bbox"][0] == pytest.approx(0.10125) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["bbox"][0] == pytest.approx(0.10125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_bbox_with_ultrafine_subpixel_probe() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "neutral_rect_border_ultrafine",
            "bbox": [0.10, 0.20, 0.30, 0.40],
            "fill": "#e8e8e8",
            "stroke": "#8a8a8a",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["bbox"][3] == pytest.approx(0.39875) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["bbox"][3] == pytest.approx(0.39875)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_microfine_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_light_grey_fill_microfine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.915625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.915625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_microfine_probe() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_outline_microfine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "none",
            "stroke": "#8a8a8a",
            "stroke_opacity": 0.98125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.984375)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.984375)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_nanofine_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_light_grey_fill_nanofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.9140625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.9140625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_nanofine_probe() -> None:
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_outline_nanofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "none",
            "stroke": "#8a8a8a",
            "stroke_opacity": 0.98125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.9828125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.9828125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True
