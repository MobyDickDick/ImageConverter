from __future__ import annotations

from src.iCCModules import imageCompositeConverterOptimizationGlobalSearch as helpers


class _Image:
    def __init__(self, h: int, w: int):
        self.shape = (h, w)


def test_full_badge_error_for_params_returns_inf_when_render_is_none() -> None:
    img = _Image(6, 6)

    result = helpers.fullBadgeErrorForParamsImpl(
        img,
        {"cx": 3.0},
        fit_to_original_size_fn=lambda _img_orig, _render: None,
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        generate_badge_svg_fn=lambda _w, _h, _params: "<svg/>",
        calculate_error_fn=lambda _a, _b: 0.0,
    )

    assert result == float("inf")


def test_full_badge_error_for_params_uses_render_pipeline_result() -> None:
    img = _Image(4, 4)

    result = helpers.fullBadgeErrorForParamsImpl(
        img,
        {"cx": 2.0},
        fit_to_original_size_fn=lambda _img_orig, render: render,
        render_svg_to_numpy_fn=lambda _svg, _w, _h: {"render": "ok"},
        generate_badge_svg_fn=lambda w, h, params: f"<svg w='{w}' h='{h}' cx='{params['cx']}'/>",
        calculate_error_fn=lambda _a, b: 1.0 if b == {"render": "ok"} else 5.0,
    )

    assert result == 1.0
