from __future__ import annotations

from src.iCCModules import imageCompositeConverterOptimizationQuantization as quantization_helpers


def test_enforce_circle_connector_symmetry_vertical_arm_aligns_to_circle_axis() -> None:
    params = {
        "circle_enabled": True,
        "cx": 10.0,
        "cy": 8.0,
        "r": 4.0,
        "arm_enabled": True,
        "arm_x1": 1.0,
        "arm_y1": 1.0,
        "arm_x2": 2.0,
        "arm_y2": 15.0,
    }

    out = quantization_helpers.enforceCircleConnectorSymmetryImpl(params, 30, 30)

    assert out["arm_x1"] == 10.0
    assert out["arm_x2"] == 10.0
    assert out["arm_y2"] == 4.0


def test_quantize_badge_params_snaps_and_clamps_values() -> None:
    params = {
        "circle_enabled": True,
        "cx": 10.12,
        "cy": 8.37,
        "r": 4.19,
        "stroke_circle": 1.2,
        "stem_enabled": True,
        "stem_width": 1.7,
        "stem_top": -5.0,
        "stem_bottom": 99.0,
    }

    out = quantization_helpers.quantizeBadgeParamsImpl(
        params,
        20,
        16,
        snap_half_fn=lambda value: round(float(value) * 2.0) / 2.0,
        snap_int_px_fn=lambda value, minimum=1.0: max(float(minimum), float(round(value))),
        enforce_circle_connector_symmetry_fn=quantization_helpers.enforceCircleConnectorSymmetryImpl,
        clamp_circle_inside_canvas_fn=lambda probe, _w, _h: probe,
        max_circle_radius_inside_canvas_fn=lambda *_args, **_kwargs: 4.5,
    )

    assert out["cx"] == 10.0
    assert out["cy"] == 8.5
    assert out["stroke_circle"] == 1.0
    assert out["stem_top"] == 0.0
    assert out["stem_bottom"] == 16.0
