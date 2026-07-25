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


def test_default_optimizer_refines_rect_to_nanofine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill_nanofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f2b8b4",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f2b8b5" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f2b8b5"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_to_femtofine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill_femtofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f2b9b5",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f3b9b5" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f3b9b5"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_to_picofine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill_picofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f2b9b6",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f2b9b7" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f2b9b7"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_to_femtofine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill_femtofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f2bab7",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f2bab8" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f2bab8"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_to_half_yoctofine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill_half_yoctofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f2bab8",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f3bab8" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f3bab8"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_to_quarter_yoctofine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill_quarter_yoctofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f3bab8",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f3bab9" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f3bab9"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_to_eighth_yoctofine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill_eighth_yoctofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f3bab9",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f3baba" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f3baba"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True



def test_default_optimizer_refines_rect_to_sixteenth_yoctofine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill_sixteenth_yoctofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f3baba",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f3babb" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f3babb"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True



def test_default_optimizer_refines_rect_to_thirtysecond_yoctofine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill_thirtysecond_yoctofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f3babb",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f3babc" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f3babc"
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_to_sixtyfourth_yoctofine_warm_light_fill() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_warm_fill_sixtyfourth_yoctofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f3babc",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["fill"] == "#f3babd" else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill"] == "#f3babd"
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


def test_default_optimizer_refines_polygon_path_by_whole_shape_translation() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "translated_checkmark",
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
            0.0
            if all(
                candidate_point[0] == pytest.approx(expected_x)
                for candidate_point, expected_x in zip(
                    candidate_ir[0]["points"], (0.21, 0.51, 0.81)
                )
            )
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][0] == pytest.approx([0.21, 0.50])
    assert result["geometry_ir"][0]["points"][1] == pytest.approx([0.51, 0.70])
    assert result["geometry_ir"][0]["points"][2] == pytest.approx([0.81, 0.10])
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


def test_default_optimizer_refines_polygon_path_points_with_nanofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "nanofine_subpixel_triangle",
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
            0.0 if candidate_ir[0]["points"][2][0] == pytest.approx(0.4803125) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.4803125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_picofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "picofine_subpixel_triangle",
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
            0.0
            if candidate_ir[0]["points"][2][0] == pytest.approx(0.48015625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.48015625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_femtofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "femtofine_subpixel_triangle",
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
            0.0
            if candidate_ir[0]["points"][2][0] == pytest.approx(0.480078125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.480078125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_attofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "attofine_subpixel_triangle",
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
            0.0
            if candidate_ir[0]["points"][2][0] == pytest.approx(0.4800390625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.4800390625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_zeptofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "zeptofine_subpixel_triangle",
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
            0.0
            if candidate_ir[0]["points"][2][0] == pytest.approx(0.48001953125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.48001953125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_yoctofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "yoctofine_subpixel_triangle",
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
            0.0
            if candidate_ir[0]["points"][2][0] == pytest.approx(0.480009765625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.480009765625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_half_yoctofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "half_yoctofine_subpixel_triangle",
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
            0.0
            if candidate_ir[0]["points"][2][0] == pytest.approx(0.4800048828125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.4800048828125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_quarter_yoctofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "quarter_yoctofine_subpixel_triangle",
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
            0.0
            if candidate_ir[0]["points"][2][0] == pytest.approx(0.48000244140625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.48000244140625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True



def test_default_optimizer_refines_polygon_path_points_with_sixteenth_yoctofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "sixteenth_yoctofine_subpixel_triangle",
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
            0.0
            if candidate_ir[0]["points"][2][0] == pytest.approx(0.480001220703125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.480001220703125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_sixtyfourth_yoctofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "sixtyfourth_yoctofine_subpixel_triangle",
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
            0.0
            if abs(candidate_ir[0]["points"][2][0] - 0.4800001525878906) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(0.4800001525878906)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True

def test_default_optimizer_refines_polygon_path_stroke_width_with_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "yoctofine_antialias_sensitive_triangle",
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
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.024009765625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.024009765625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_half_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "half_yoctofine_antialias_sensitive_triangle",
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
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.0240048828125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0240048828125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_quarter_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "quarter_yoctofine_antialias_sensitive_triangle",
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
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.02400244140625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.02400244140625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True



def test_default_optimizer_refines_polygon_path_stroke_width_with_sixteenth_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "sixteenth_yoctofine_antialias_sensitive_triangle",
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
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.024001220703125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.024001220703125)
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


def test_default_optimizer_refines_polygon_path_stroke_width_with_ultrafine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "ultrafine_antialias_sensitive_triangle",
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
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.02525) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.02525)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_microfine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "microfine_antialias_sensitive_triangle",
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
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.024625) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.024625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_nanofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "nanofine_antialias_sensitive_triangle",
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
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.0243125) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0243125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_picofine_absolute_probe() -> (
    None
):
    geometry_ir = [
        {
            "kind": "PolygonPath",
            "id": "picofine_antialias_sensitive_triangle",
            "points": [[0.1, 0.2], [0.8, 0.2], [0.4, 0.7]],
            "stroke_width": 0.024,
            "fill": "none",
            "stroke": "#24678d",
        }
    ]

    def error_fn(candidate_ir: list[dict[str, object]]) -> float:
        return (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.02415625)
            else 10.0
        )

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        geometry_ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=error_fn,
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.02415625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_femtofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "femtofine_antialias_sensitive_triangle",
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
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.024078125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.024078125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_attofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "attofine_antialias_sensitive_triangle",
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
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.0240390625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0240390625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_zeptofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "zeptofine_antialias_sensitive_triangle",
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
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.02401953125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.02401953125)
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
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.055625) else 10.0
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
            0.0 if candidate_ir[0]["stroke_width"] == pytest.approx(0.0553125) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0553125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_picofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_picofine",
            "bbox": [0.22, 0.24, 0.56, 0.08],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.05515625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05515625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_thirtysecond_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "thirtysecond_yoctofine_antialias_sensitive_triangle",
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
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.0240006103515625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0240006103515625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_sixtyfourth_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "sixtyfourth_yoctofine_antialias_sensitive_triangle",
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
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.02400030517578125) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.02400030517578125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True



def test_default_optimizer_refines_polygon_path_stroke_width_with_128th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "128th_yoctofine_antialias_sensitive_triangle",
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
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.024000152587890625) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.024000152587890625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_256th_yoctofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "256th_yoctofine_subpixel_triangle",
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
            0.0
            if abs(candidate_ir[0]["points"][2][0] - 0.4800000762939453) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(
        0.4800000762939453
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_256th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "256th_yoctofine_antialias_sensitive_triangle",
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
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.024000076293945313) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(
        0.024000076293945313
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_points_with_512th_yoctofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "512th_yoctofine_subpixel_triangle",
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
            0.0
            if abs(candidate_ir[0]["points"][2][0] - 0.4800000381469727) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(
        0.4800000381469727
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_512th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "512th_yoctofine_antialias_sensitive_triangle",
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
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.024000038146972657) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(
        0.024000038146972657
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True



def test_default_optimizer_refines_polygon_path_points_with_1024th_yoctofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "1024th_yoctofine_subpixel_triangle",
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
            0.0
            if abs(candidate_ir[0]["points"][2][0] - 0.4800000190734863) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(
        0.4800000190734863
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_1024th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "1024th_yoctofine_antialias_sensitive_triangle",
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
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.02400001907348633) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(
        0.02400001907348633
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True



def test_default_optimizer_refines_polygon_path_points_with_2048th_yoctofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "2048th_yoctofine_subpixel_triangle",
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
            0.0
            if abs(candidate_ir[0]["points"][2][0] - 0.4800000095367432) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(
        0.4800000095367432
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_2048th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "2048th_yoctofine_antialias_sensitive_triangle",
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
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.024000009536743166) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(
        0.024000009536743166
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True

def test_default_optimizer_refines_rect_border_stroke_width_with_half_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head_half_yoctofine",
            "bbox": [0.22, 0.08, 0.56, 0.44],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.05500244140625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05500244140625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_half_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_half_yoctofine",
            "bbox": [0.22, 0.24, 0.56, 0.08],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.05500244140625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05500244140625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True



def test_default_optimizer_refines_polygon_path_points_with_4096th_yoctofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "4096th_yoctofine_subpixel_triangle",
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
            0.0
            if abs(candidate_ir[0]["points"][2][0] - 0.4800000047683716) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["points"][2][0] == pytest.approx(
        0.4800000047683716
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_width_with_4096th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "4096th_yoctofine_antialias_sensitive_triangle",
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
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.024000004768371583) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(
        0.024000004768371583
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True

def test_default_optimizer_refines_rect_border_stroke_width_with_2048th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head_2048th_yoctofine",
            "bbox": [0.22, 0.08, 0.56, 0.44],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.05500000953674317) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(
        0.05500000953674317
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_2048th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem_2048th_yoctofine",
            "bbox": [0.44, 0.24, 0.08, 0.56],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.05500000953674317) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(
        0.05500000953674317
    )
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_microfine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-microfine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.3125%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_nanofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-nanofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.15625%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_picofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-picofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.078125%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_femtofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-femtofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.0390625%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_attofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-attofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.01953125%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_zeptofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-zeptofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.009765625%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.0048828125%", "color": "#43ad49"},
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


def test_default_optimizer_refines_rect_border_stroke_opacity_with_ultrafine_probe() -> (
    None
):
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


def test_default_optimizer_refines_color_patch_bbox_with_ultrafine_subpixel_probe() -> (
    None
):
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


def test_default_optimizer_refines_rect_border_bbox_with_ultrafine_subpixel_probe() -> (
    None
):
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


def test_default_optimizer_refines_color_patch_bbox_with_picofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "neutral_fill_patch_picofine",
            "bbox": [0.10, 0.20, 0.30, 0.40],
            "fill": "#e8e8e8",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["bbox"][1] == pytest.approx(0.200625) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["bbox"][1] == pytest.approx(0.200625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_bbox_with_picofine_subpixel_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "neutral_rect_border_picofine",
            "bbox": [0.10, 0.20, 0.30, 0.40],
            "fill": "#e8e8e8",
            "stroke": "#8a8a8a",
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0 if candidate_ir[0]["bbox"][2] == pytest.approx(0.299375) else 10.0
        ),
    )

    assert result["geometry_ir"][0]["bbox"][2] == pytest.approx(0.299375)
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


def test_default_optimizer_refines_rect_border_stroke_opacity_with_microfine_probe() -> (
    None
):
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


def test_default_optimizer_refines_rect_border_stroke_opacity_with_nanofine_probe() -> (
    None
):
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


def test_default_optimizer_refines_color_patch_opacity_with_picofine_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_light_grey_fill_picofine",
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
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.91328125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.91328125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_picofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_outline_picofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "none",
            "stroke": "#8a8a8a",
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.98359375)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.98359375)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_width_with_attofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_outline_attofine",
            "bbox": [0.16, 0.08, 0.68, 0.58],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.055078125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.055078125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_attofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem_attofine",
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
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.054921875)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.054921875)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_femtofine_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_light_grey_fill_femtofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.982421875)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.982421875)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_femtofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_outline_femtofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "none",
            "stroke": "#8a8a8a",
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.983203125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.983203125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_width_with_zeptofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_outline_zeptofine",
            "bbox": [0.16, 0.08, 0.68, 0.58],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.0550390625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0550390625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_zeptofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_zeptofine",
            "bbox": [0.10, 0.53, 0.36, 0.08],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.0549609375)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0549609375)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_attofine_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_light_grey_fill_attofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.9826171875)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.9826171875)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_attofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_outline_attofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "none",
            "stroke": "#8a8a8a",
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.9830078125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.9830078125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_width_with_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_outline_yoctofine",
            "bbox": [0.16, 0.08, 0.68, 0.58],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.05501953125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05501953125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_yoctofine",
            "bbox": [0.10, 0.53, 0.36, 0.08],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.05498046875)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05498046875)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True



def test_default_optimizer_refines_rect_border_stroke_width_with_half_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_outline_half_yoctofine",
            "bbox": [0.16, 0.08, 0.68, 0.58],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.055009765625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.055009765625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_half_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_half_yoctofine",
            "bbox": [0.10, 0.53, 0.36, 0.08],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.054990234375)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.054990234375)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_zeptofine_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_light_grey_fill_zeptofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.98271484375)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.98271484375)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_zeptofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_outline_zeptofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "none",
            "stroke": "#8a8a8a",
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.98291015625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.98291015625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_yoctofine_probe() -> None:
    ir = [
        {
            "kind": "ColorPatch",
            "id": "backbottom_light_grey_fill_yoctofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "fill": "#f0f0f0",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.982763671875)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.982763671875)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "backbottom_light_grey_outline_yoctofine",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "stroke": "#d0d0d0",
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.982861328125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.982861328125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_half_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_half_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e0e0e0",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.9827880859375)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.9827880859375)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_half_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_half_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#8a8a8a",
            "stroke_width": 0.04,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.9828369140625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.9828369140625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_half_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-half-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.00244140625%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_eighth_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-eighth-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.0006103515625%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_quarter_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-quarter-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.001220703125%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_sixteenth_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-sixteenth-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.00030517578125%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_thirtysecond_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-thirtysecond-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.000152587890625%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_sixtyfourth_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-sixtyfourth-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.0000762939453125%", "color": "#43ad49"},
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


def test_default_optimizer_refines_rect_border_stroke_width_with_quarter_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_outline_quarter_yoctofine",
            "bbox": [0.16, 0.08, 0.68, 0.58],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.0550048828125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0550048828125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_quarter_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_quarter_yoctofine",
            "bbox": [0.10, 0.53, 0.36, 0.08],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.0549951171875)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0549951171875)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_quarter_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_quarter_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e0e0e0",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.98280029296875)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.98280029296875)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_quarter_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_quarter_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#8a8a8a",
            "stroke_width": 0.04,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.98282470703125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.98282470703125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_eighth_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_eighth_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e0e0e0",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.982806396484375)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.982806396484375)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_eighth_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_eighth_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity") == pytest.approx(0.982818603515625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.982818603515625
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_width_with_quarter_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head_quarter_yoctofine",
            "bbox": [0.22, 0.08, 0.56, 0.44],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.055001220703125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.055001220703125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_quarter_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_quarter_yoctofine",
            "bbox": [0.22, 0.24, 0.56, 0.08],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.055001220703125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.055001220703125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_sixteenth_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_sixteenth_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.9828094482421875)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.9828094482421875)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_sixteenth_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_sixteenth_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.9828155517578125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.9828155517578125
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_thirtysecond_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_thirtysecond_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity") == pytest.approx(0.98281097412109375)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.98281097412109375)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_thirtysecond_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_thirtysecond_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.98281402587890625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.98281402587890625
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_128th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-128th-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.00003814697265625%", "color": "#43ad49"},
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


def test_default_optimizer_refines_rect_border_stroke_width_with_eighth_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head_eighth_yoctofine",
            "bbox": [0.22, 0.08, 0.56, 0.44],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.0550006103515625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0550006103515625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_eighth_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem_eighth_yoctofine",
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
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.0550006103515625)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0550006103515625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_sixtyfourth_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_sixtyfourth_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.982811737060546875, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(
        0.982811737060546875
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_sixtyfourth_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_sixtyfourth_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.982813262939453125, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.982813262939453125
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_256th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-256th-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.000019073486328125%", "color": "#43ad49"},
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


def test_default_optimizer_refines_rect_border_stroke_width_with_sixteenth_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head_sixteenth_yoctofine",
            "bbox": [0.22, 0.08, 0.56, 0.44],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.05500030517578125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05500030517578125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_sixteenth_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_sixteenth_yoctofine",
            "bbox": [0.22, 0.24, 0.56, 0.08],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0]["stroke_width"] == pytest.approx(0.05500030517578125)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05500030517578125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_width_with_128th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head_128th_yoctofine",
            "bbox": [0.22, 0.08, 0.56, 0.44],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.055000152587890625) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.055000152587890625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_128th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem_128th_yoctofine",
            "bbox": [0.48, 0.22, 0.08, 0.56],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.055000152587890625) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.055000152587890625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_width_with_256th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head_256th_yoctofine",
            "bbox": [0.22, 0.08, 0.56, 0.44],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.0550000762939453125) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0550000762939453125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_256th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_256th_yoctofine",
            "bbox": [0.22, 0.48, 0.56, 0.08],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.0550000762939453125) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.0550000762939453125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_width_with_512th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head_512th_yoctofine",
            "bbox": [0.22, 0.08, 0.56, 0.44],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.05500003814697265625) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05500003814697265625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_512th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem_512th_yoctofine",
            "bbox": [0.48, 0.22, 0.08, 0.56],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.05499996185302735) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05499996185302735)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_width_with_1024th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head_1024th_yoctofine",
            "bbox": [0.22, 0.08, 0.56, 0.44],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.05500001907348633) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05500001907348633)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_1024th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "HorizontalRule",
            "id": "square_badge_arm_1024th_yoctofine",
            "bbox": [0.22, 0.24, 0.56, 0.08],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.05499998092651367) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(0.05499998092651367)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_128th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_128th_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.9828121185302734375, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(
        0.9828121185302734375
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_128th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_128th_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.9828128814697265625, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.9828128814697265625
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_256th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_256th_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.98281230926513671875, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(
        0.98281230926513671875
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_256th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_256th_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.98281269073486328125, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.98281269073486328125
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_512th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_512th_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.982812404632568359375, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(
        0.982812404632568359375
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_512th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_512th_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.982812595367431640625, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.982812595367431640625
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_1024th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_1024th_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.9828124523162841796875, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(
        0.9828124523162841796875
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_1024th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_1024th_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.9828125476837158203125, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.9828125476837158203125
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_512th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-512th-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.0000095367431640625%", "color": "#43ad49"},
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


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_1024th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-1024th-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.00000476837158203125%", "color": "#43ad49"},
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

def test_default_optimizer_refines_color_patch_opacity_with_256th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_256th_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.98281247615814208984375, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(
        0.98281247615814208984375
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_256th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_256th_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.98281252384185791015625, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.98281252384185791015625
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_4096th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_4096th_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.982812488079071044921875, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(
        0.982812488079071044921875
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_4096th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_4096th_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.982812511920928955078125, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.982812511920928955078125
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_opacity_with_midpoint_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "generic_checkmark_midpoint_stroke_opacity",
            "points": [[0.20, 0.50], [0.45, 0.72], [0.82, 0.14]],
            "fill": "none",
            "stroke": "#43ad49",
            "stroke_width": 0.08,
            "stroke_opacity": 0.85,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.875, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.875)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_fill_opacity_with_midpoint_probe() -> None:
    ir = [
        {
            "kind": "PolygonPath",
            "id": "generic_filled_path_midpoint_opacity",
            "points": [[0.20, 0.20], [0.78, 0.20], [0.50, 0.78]],
            "fill": "#d9001b",
            "stroke": "none",
            "fill_opacity": 0.95,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.925, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.925)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_opacity_with_high_midpoint_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "generic_checkmark_high_midpoint_stroke_opacity",
            "points": [[0.20, 0.50], [0.45, 0.72], [0.82, 0.14]],
            "fill": "none",
            "stroke": "#43ad49",
            "stroke_width": 0.08,
            "stroke_opacity": 0.95,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.975, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.975)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_fill_opacity_with_high_midpoint_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "generic_filled_path_high_midpoint_opacity",
            "points": [[0.20, 0.20], [0.78, 0.20], [0.50, 0.78]],
            "fill": "#d9001b",
            "stroke": "none",
            "fill_opacity": 0.95,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.975, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.975)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_opacity_with_quarter_midpoint_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "generic_checkmark_quarter_midpoint_stroke_opacity",
            "points": [[0.20, 0.50], [0.45, 0.72], [0.82, 0.14]],
            "fill": "none",
            "stroke": "#43ad49",
            "stroke_width": 0.08,
            "stroke_opacity": 0.90,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.9125, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(0.9125)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_fill_opacity_with_quarter_midpoint_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "generic_filled_path_quarter_midpoint_opacity",
            "points": [[0.20, 0.20], [0.78, 0.20], [0.50, 0.78]],
            "fill": "#d9001b",
            "stroke": "none",
            "fill_opacity": 0.95,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.9625, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(0.9625)
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_width_with_4096th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head_4096th_yoctofine",
            "bbox": [0.22, 0.08, 0.56, 0.44],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.055000004768371586) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(
        0.055000004768371586
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_4096th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem_4096th_yoctofine",
            "bbox": [0.44, 0.24, 0.08, 0.56],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.055000004768371586) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(
        0.055000004768371586
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_8192th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_8192th_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.9828124940395355224609375, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(
        0.9828124940395355224609375
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_8192th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_8192th_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.9828125059604644775390625, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.9828125059604644775390625
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_16384th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_16384th_yoctofine_fill",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "fill": "#e8e8e8",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("fill_opacity")
            == pytest.approx(0.98281249701976776123046875, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(
        0.98281249701976776123046875
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_16384th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_16384th_yoctofine_outline",
            "bbox": [0.10, 0.15, 0.80, 0.70],
            "stroke": "#d0d0d0",
            "stroke_width": 0.02,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if candidate_ir[0].get("stroke_opacity")
            == pytest.approx(0.98281250298023223876953125, abs=1e-12)
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.98281250298023223876953125
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_polygon_path_stroke_gradient_offsets_with_2048th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "PolygonPath",
            "id": "gradient-checkmark-2048th-yoctofine",
            "points": [[0.20, 0.50], [0.50, 0.70], [0.80, 0.10]],
            "fill": "none",
            "stroke": "#3c9f44",
            "stroke_width": 0.08,
            "stroke_gradient": {
                "id": "green-gradient",
                "stops": [
                    {"offset": "0%", "color": "#176f28"},
                    {"offset": "50.000002384185791015625%", "color": "#43ad49"},
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


def test_default_optimizer_refines_rect_border_stroke_width_with_8192th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "square_badge_head_8192th_yoctofine",
            "bbox": [0.22, 0.08, 0.56, 0.44],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.05500000238418579) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(
        0.05500000238418579
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rule_stroke_width_with_8192th_yoctofine_absolute_probe() -> (
    None
):
    ir = [
        {
            "kind": "VerticalRule",
            "id": "square_badge_stem_8192th_yoctofine",
            "bbox": [0.44, 0.24, 0.08, 0.56],
            "stroke": "#8a8a8a",
            "stroke_width": 0.055,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_width"] - 0.05500000238418579) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_width"] == pytest.approx(
        0.05500000238418579
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_32768th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_32768th_yoctofine_fill",
            "bbox": [0.18, 0.56, 0.64, 0.24],
            "fill": "#f0f0f0",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["fill_opacity"] - 0.9828124985098839) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(
        0.9828124985098839
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_32768th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_32768th_yoctofine_outline",
            "bbox": [0.18, 0.56, 0.64, 0.24],
            "stroke": "#8a8a8a",
            "stroke_width": 0.04,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_opacity"] - 0.9828125014901161) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.9828125014901161
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_color_patch_opacity_with_65536th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "ColorPatch",
            "id": "back_bottom_65536th_yoctofine_fill",
            "bbox": [0.18, 0.56, 0.64, 0.24],
            "fill": "#f0f0f0",
            "fill_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["fill_opacity"] - 0.9828124992549419) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["fill_opacity"] == pytest.approx(
        0.9828124992549419
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True


def test_default_optimizer_refines_rect_border_stroke_opacity_with_65536th_yoctofine_probe() -> (
    None
):
    ir = [
        {
            "kind": "RectBorder",
            "id": "back_bottom_65536th_yoctofine_outline",
            "bbox": [0.18, 0.56, 0.64, 0.24],
            "stroke": "#8a8a8a",
            "stroke_width": 0.04,
            "stroke_opacity": 0.9828125,
        }
    ]

    result = optimizer_helpers.optimizeGeometryIrSequentiallyImpl(
        ir,
        render_fn=lambda candidate_ir: candidate_ir,
        error_fn=lambda candidate_ir: (
            0.0
            if abs(candidate_ir[0]["stroke_opacity"] - 0.9828125007450581) < 1e-15
            else 10.0
        ),
    )

    assert result["geometry_ir"][0]["stroke_opacity"] == pytest.approx(
        0.9828125007450581
    )
    assert result["final_error"] == 0.0
    assert result["steps"][0]["accepted"] is True
