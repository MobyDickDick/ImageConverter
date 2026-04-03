from __future__ import annotations

from src.iCCModules import imageCompositeConverterOptimizationCircleGeometry as circle_geometry_helpers


class _FakeImage:
    def __init__(self, h: int, w: int) -> None:
        self.shape = (h, w, 3)


def test_reanchor_arm_to_circle_edge_keeps_horizontal_arm() -> None:
    params = {
        "arm_enabled": True,
        "cx": 10.0,
        "cy": 12.0,
        "arm_x1": 4.0,
        "arm_y1": 11.0,
        "arm_x2": 8.0,
        "arm_y2": 13.0,
        "arm_stroke": 2.0,
    }

    circle_geometry_helpers.reanchorArmToCircleEdgeImpl(params, radius=5.0)

    assert params["arm_y1"] == 12.0
    assert params["arm_y2"] == 12.0
    assert params["arm_x2"] == 4.0


def test_element_error_for_circle_pose_returns_inf_when_circle_disabled() -> None:
    img = _FakeImage(16, 16)
    params = {"circle_enabled": False}

    err = circle_geometry_helpers.elementErrorForCirclePoseImpl(
        img,
        params,
        cx_value=5.0,
        cy_value=5.0,
        radius_value=4.0,
        snap_half_fn=lambda value: round(float(value) * 2.0) / 2.0,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, float(value))),
        clamp_circle_inside_canvas_fn=lambda probe, _w, _h: probe,
        reanchor_arm_to_circle_edge_fn=lambda _probe, _radius: None,
        generate_badge_svg_fn=lambda _w, _h, _params: "<svg />",
        element_only_params_fn=lambda probe, _element: probe,
        fit_to_original_size_fn=lambda _orig, render: render,
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        extract_badge_element_mask_fn=lambda _img, _params, _element: object(),
        element_match_error_fn=lambda *_args, **_kwargs: 0.0,
    )

    assert err == float("inf")
