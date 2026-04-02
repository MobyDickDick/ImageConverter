from __future__ import annotations

from src import imageCompositeConverterOptimizationWidth as width_helpers


class _FakeImage:
    def __init__(self, h: int, w: int) -> None:
        self.shape = (h, w, 3)


def test_element_width_key_and_bounds_locks_stem_width_by_default() -> None:
    params: dict[str, object] = {
        "stem_enabled": True,
        "lock_stroke_widths": True,
    }

    result = width_helpers.elementWidthKeyAndBoundsImpl(
        "stem",
        params,
        20,
        20,
        ac08_stroke_width_px=1.5,
        extract_badge_element_mask_fn=lambda *_args, **_kwargs: None,
        mask_bbox_fn=lambda _mask: None,
    )

    assert result == ("stem_width", 1.5, 1.5)


def test_element_error_for_width_returns_inf_if_element_is_not_supported() -> None:
    img = _FakeImage(16, 16)
    params: dict[str, object] = {
        "circle_enabled": True,
    }

    err = width_helpers.elementErrorForWidthImpl(
        img,
        params,
        "unknown",
        3.0,
        element_width_key_and_bounds_fn=lambda *_args, **_kwargs: None,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, float(value))),
        generate_badge_svg_fn=lambda _w, _h, _params: "<svg />",
        element_only_params_fn=lambda probe, _element: probe,
        fit_to_original_size_fn=lambda _orig, render: render,
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        extract_badge_element_mask_fn=lambda _img, _params, _element: object(),
        element_match_error_fn=lambda *_args, **_kwargs: 0.0,
    )

    assert err == float("inf")
