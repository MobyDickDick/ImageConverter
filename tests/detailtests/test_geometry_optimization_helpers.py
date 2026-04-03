from __future__ import annotations

from src.iCCModules import imageCompositeConverterOptimizationGeometry as geometry_helpers


class _FakeImage:
    def __init__(self, h: int, w: int) -> None:
        self.shape = (h, w, 3)


def test_optimize_element_width_bracket_updates_stem_width_and_center() -> None:
    img = _FakeImage(20, 20)
    params: dict[str, float | bool] = {
        "stem_enabled": True,
        "stem_width": 2.0,
        "stem_x": 5.0,
        "cx": 10.0,
    }
    logs: list[str] = []

    changed = geometry_helpers.optimizeElementWidthBracketImpl(
        img,
        params,
        "stem",
        logs,
        element_width_key_and_bounds_fn=lambda _element, _params, _w, _h: ("stem_width", 1.0, 6.0),
        snap_half_fn=lambda value: round(float(value) * 2.0) / 2.0,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, float(value))),
        element_error_for_width_fn=lambda _img, _params, _element, value: abs(float(value) - 4.0),
        argmin_index_fn=lambda values: min(range(len(values)), key=lambda idx: values[idx]),
        stochastic_survivor_scalar_fn=lambda *args, **kwargs: (4.0, 0.0, False),
        snap_int_px_fn=lambda value: float(max(1, round(value))),
    )

    assert changed is True
    assert params["stem_width"] == 4.0
    assert params["stem_x"] == 8.0
    assert any("Breiten-Bracketing stem_width 2.000->4.000" in entry for entry in logs)


def test_element_error_for_extent_returns_inf_for_unknown_element() -> None:
    img = _FakeImage(12, 12)
    params = {"circle_enabled": True}

    err = geometry_helpers.elementErrorForExtentImpl(
        img,
        params,
        "text",
        3.0,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, float(value))),
        reanchor_arm_to_circle_edge_fn=lambda _params, _radius: None,
        generate_badge_svg_fn=lambda _w, _h, _params: "<svg />",
        element_only_params_fn=lambda p, _element: p,
        fit_to_original_size_fn=lambda _orig, render: render,
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        extract_badge_element_mask_fn=lambda _img, _params, _element: object(),
        element_match_error_fn=lambda *_args, **_kwargs: 0.0,
    )

    assert err == float("inf")
