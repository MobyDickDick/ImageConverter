from __future__ import annotations

from src.iCCModules import imageCompositeConverterGeometryBrackets as bracket_helpers


class _FakeImage:
    def __init__(self, h: int, w: int) -> None:
        self.shape = (h, w, 3)


def test_optimize_circle_center_bracket_respects_radius_floor_clearance() -> None:
    img = _FakeImage(35, 20)
    params: dict[str, float | bool] = {
        "circle_enabled": True,
        "arm_enabled": True,
        "cx": 10.0,
        "cy": 24.8,
        "r": 7.4,
        "stroke_circle": 1.0,
        "circle_radius_lower_bound_px": 8.0,
    }
    logs: list[str] = []

    changed = bracket_helpers.optimizeCircleCenterBracketImpl(
        img,
        params,
        logs,
        snap_half_fn=lambda value: round(float(value) * 2.0) / 2.0,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, float(value))),
        element_error_for_circle_radius_fn=lambda _img, _probe, _radius: (
            (float(_probe["cx"]) - 19.0) ** 2 + (float(_probe["cy"]) - 23.0) ** 2
        ),
        reanchor_arm_to_circle_edge_fn=lambda _params, _radius: None,
    )

    assert changed is True
    assert float(params["cx"]) <= 11.5
    assert float(params["cy"]) >= 20.5
    assert any("Mittelpunkt-Bracketing" in entry for entry in logs)


def test_optimize_circle_center_bracket_allows_y_refine_when_text_window_collapses_x() -> None:
    img = _FakeImage(35, 20)
    params: dict[str, float | bool] = {
        "circle_enabled": True,
        "arm_enabled": True,
        "draw_text": True,
        "template_circle_cx": 10.0,
        "template_circle_cy": 25.0,
        "arm_x1": 10.0,
        "arm_x2": 10.0,
        "cx": 10.0,
        "cy": 23.0,
        "r": 9.0,
        "stroke_circle": 1.0,
        "circle_radius_lower_bound_px": 8.5,
    }
    logs: list[str] = []

    changed = bracket_helpers.optimizeCircleCenterBracketImpl(
        img,
        params,
        logs,
        snap_half_fn=lambda value: round(float(value) * 2.0) / 2.0,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, float(value))),
        element_error_for_circle_radius_fn=lambda _img, probe, _radius: abs(float(probe["cy"]) - 25.0),
        reanchor_arm_to_circle_edge_fn=lambda _params, _radius: None,
    )

    assert changed is True
    assert float(params["cx"]) == 10.0
    assert float(params["cy"]) >= 24.0
    assert any("Achse fixiert" in entry for entry in logs)
