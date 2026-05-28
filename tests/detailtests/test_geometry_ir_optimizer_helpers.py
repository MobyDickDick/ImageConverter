from __future__ import annotations

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
