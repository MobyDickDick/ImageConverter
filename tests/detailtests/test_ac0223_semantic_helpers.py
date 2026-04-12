from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticAc0223 as ac0223_helpers
from src.iCCModules import imageCompositeConverterSemanticBadgeSvg as badge_svg_helpers
from src.iCCModules import imageCompositeConverterOptimizationQuantization as quantization_helpers


class _FakeImage:
    def __init__(self, h: int, w: int) -> None:
        self.shape = (h, w, 3)


def test_fit_ac0223_params_keeps_valve_connector_anchored() -> None:
    defaults = {
        "cx": 25.0,
        "head_hub_cy": 25.153,
    }

    def fake_fit(_img, _defaults):
        return {
            "cy": 57.0,
            "r": 17.0,
            "head_hub_cy": 2.0,
        }

    params = ac0223_helpers.fitAc0223ParamsFromImageImpl(
        _FakeImage(75, 50),
        defaults,
        fit_ac0813_params_from_image_fn=fake_fit,
    )

    assert params["arm_y2"] == defaults["head_hub_cy"]
    assert params["arm_y1"] == 40.0


def test_generate_badge_svg_ac0223_polygon_uses_gradient_fill() -> None:
    svg = badge_svg_helpers.generateBadgeSvgImpl(
        50,
        75,
        {
            "cx": 25.0,
            "cy": 57.0,
            "r": 17.0,
            "fill_gray": 189,
            "stroke_gray": 96,
            "stroke_circle": 2.0,
            "head_style": "ac0223_triple_valve",
            "draw_text": False,
            "arm_enabled": False,
            "stem_enabled": False,
        },
        align_stem_to_circle_center_fn=lambda p: p,
        quantize_badge_params_fn=lambda p, _w, _h: p,
        clip_scalar_fn=lambda value, _lo, _hi: value,
        grayhex_fn=lambda gray: f"#{int(gray):02x}{int(gray):02x}{int(gray):02x}",
        co2_layout_fn=lambda _p: {},
        t_path_d="",
        t_xmin=0.0,
        t_ymax=0.0,
        m_path_d="",
        m_xmin=0.0,
        m_ymax=0.0,
    )

    assert 'fill="url(#ac0223ValveGradient)" stroke="#808080"' in svg
    assert 'fill="#d9d9d9" stroke="#808080"' not in svg


def test_generate_badge_svg_restores_ac0223_head_when_style_keys_missing() -> None:
    svg = badge_svg_helpers.generateBadgeSvgImpl(
        50,
        75,
        {
            "variant_name": "AC0223_L",
            "cx": 25.0,
            "cy": 57.0,
            "r": 16.5,
            "fill_gray": 235,
            "stroke_gray": 88,
            "stroke_circle": 3.0,
            "draw_text": False,
        },
        align_stem_to_circle_center_fn=lambda p: p,
        quantize_badge_params_fn=lambda p, _w, _h: p,
        clip_scalar_fn=lambda value, _lo, _hi: value,
        grayhex_fn=lambda gray: f"#{int(gray):02x}{int(gray):02x}{int(gray):02x}",
        co2_layout_fn=lambda _p: {},
        t_path_d="",
        t_xmin=0.0,
        t_ymax=0.0,
        m_path_d="",
        m_xmin=0.0,
        m_ymax=0.0,
    )

    assert "ac0223ValveGradient" in svg
    assert '<line x1="25.0000"' in svg
    assert 'stroke="#606060"' in svg
    assert "<circle" in svg
    assert svg.index("<line") < svg.index("<circle")
    assert "<line" in svg


def test_ac0223_symmetry_enforces_short_hub_connector() -> None:
    params = quantization_helpers.enforceCircleConnectorSymmetryImpl(
        {
            "head_style": "ac0223_triple_valve",
            "circle_enabled": True,
            "cx": 25.0,
            "cy": 57.5,
            "r": 16.0,
            "head_hub_cy": 25.153,
            "arm_enabled": True,
            "arm_x1": 24.0,
            "arm_x2": 26.0,
            "arm_y1": 40.5,
            "arm_y2": 0.0,
        },
        50,
        75,
    )

    assert params["arm_x1"] == 25.0
    assert params["arm_x2"] == 25.0
    assert params["arm_y2"] == 25.153
    assert params["arm_y1"] == 41.5
