from __future__ import annotations

from src import imageCompositeConverterOptimizationCircleRadius as circle_radius_helpers


class _FakeImage:
    def __init__(self, h: int, w: int) -> None:
        self.shape = (h, w, 3)


def test_element_error_for_circle_radius_returns_inf_without_circle() -> None:
    img = _FakeImage(16, 16)

    err = circle_radius_helpers.elementErrorForCircleRadiusImpl(
        img,
        {"circle_enabled": False},
        5.0,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, float(value))),
        clamp_circle_inside_canvas_fn=lambda probe, _w, _h: probe,
        reanchor_arm_to_circle_edge_fn=lambda *_args, **_kwargs: None,
        generate_badge_svg_fn=lambda _w, _h, _params: "<svg />",
        element_only_params_fn=lambda probe, _element: probe,
        fit_to_original_size_fn=lambda _orig, render: render,
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        extract_badge_element_mask_fn=lambda _img, _params, _element: object(),
        element_match_error_fn=lambda *_args, **_kwargs: 0.0,
    )

    assert err == float("inf")


def test_select_circle_radius_plateau_candidate_prefers_best_full_error() -> None:
    img = _FakeImage(24, 24)
    params: dict[str, object] = {}
    evaluations = {4.0: 1.0, 5.0: 1.01, 6.0: 1.02}

    radius, elem_err, full_err = circle_radius_helpers.selectCircleRadiusPlateauCandidateImpl(
        img,
        params,
        evaluations,
        current_radius=5.0,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, float(value))),
        snap_half_fn=lambda value: round(float(value) * 2.0) / 2.0,
        full_badge_error_for_circle_radius_fn=lambda _img, _params, r: {4.0: 3.0, 5.0: 1.0, 6.0: 2.0}[float(r)],
        element_error_for_circle_radius_fn=lambda _img, _params, r: float(r),
    )

    assert radius == 5.0
    assert elem_err == 1.01
    assert full_err == 1.0
