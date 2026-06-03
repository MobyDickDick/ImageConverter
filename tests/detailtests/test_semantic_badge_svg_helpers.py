from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticBadgeSvg as semantic_badge_svg_helpers


def test_generate_badge_svg_impl_renders_co2_with_subscript() -> None:
    svg = semantic_badge_svg_helpers.generateBadgeSvgImpl(
        30,
        30,
        {"cx": 15.0, "cy": 15.0, "r": 10.0, "stroke_circle": 1.2, "fill_gray": 220, "stroke_gray": 152, "draw_text": True, "text_mode": "co2", "text_gray": 152},
        align_stem_to_circle_center_fn=lambda p: dict(p),
        quantize_badge_params_fn=lambda p, _w, _h: dict(p),
        clip_scalar_fn=lambda value, lower, upper: min(max(value, lower), upper),
        grayhex_fn=lambda _value: "#808080",
        co2_layout_fn=lambda _p: {
            "font_size": 8.0,
            "y_base": 15.0,
            "width_scale": 1.0,
            "co_x": 15.0,
            "subscript_x": 18.0,
            "subscript_y": 17.0,
            "sub_font_px": 5.0,
        },
        t_path_d="T",
        t_xmin=0.0,
        t_ymax=0.0,
        m_path_d="M",
        m_xmin=0.0,
        m_ymax=0.0,
    )

    assert ">CO</text>" in svg
    assert ">2</text>" in svg


def test_generate_badge_svg_impl_renders_voc_text() -> None:
    svg = semantic_badge_svg_helpers.generateBadgeSvgImpl(
        40,
        40,
        {"cx": 20.0, "cy": 20.0, "r": 10.0, "stroke_circle": 1.2, "fill_gray": 220, "stroke_gray": 152, "draw_text": True, "text_mode": "voc", "text_gray": 152},
        align_stem_to_circle_center_fn=lambda p: dict(p),
        quantize_badge_params_fn=lambda p, _w, _h: dict(p),
        clip_scalar_fn=lambda value, lower, upper: min(max(value, lower), upper),
        grayhex_fn=lambda _value: "#808080",
        co2_layout_fn=lambda _p: {},
        t_path_d="T",
        t_xmin=0.0,
        t_ymax=0.0,
        m_path_d="M",
        m_xmin=0.0,
        m_ymax=0.0,
    )

    assert ">VOC</text>" in svg


def test_generate_badge_svg_impl_strips_stale_connectors_for_ac0835() -> None:
    svg = semantic_badge_svg_helpers.generateBadgeSvgImpl(
        15,
        15,
        {
            "badge_symbol_name": "AC0835",
            "cx": 7.5,
            "cy": 7.5,
            "r": 6.0,
            "stroke_circle": 1.0,
            "fill_gray": 242,
            "stroke_gray": 127,
            "draw_text": True,
            "text_mode": "voc",
            "text_gray": 127,
            "arm_enabled": True,
            "arm_x1": 14.5,
            "arm_y1": 7.5,
            "arm_x2": 15.0,
            "arm_y2": 7.5,
            "arm_stroke": 1.0,
        },
        align_stem_to_circle_center_fn=lambda p: dict(p),
        quantize_badge_params_fn=lambda p, _w, _h: dict(p),
        clip_scalar_fn=lambda value, lower, upper: min(max(value, lower), upper),
        grayhex_fn=lambda _value: "#808080",
        co2_layout_fn=lambda _p: {},
        t_path_d="T",
        t_xmin=0.0,
        t_ymax=0.0,
        m_path_d="M",
        m_xmin=0.0,
        m_ymax=0.0,
    )

    assert "<line" not in svg
    assert ">VOC</text>" in svg


def test_generate_badge_svg_impl_suppresses_degenerate_arm_probe() -> None:
    svg = semantic_badge_svg_helpers.generateBadgeSvgImpl(
        15,
        15,
        {
            "cx": 7.5,
            "cy": 7.5,
            "r": 6.0,
            "stroke_circle": 1.0,
            "fill_gray": 242,
            "stroke_gray": 127,
            "draw_text": True,
            "text_mode": "voc",
            "text_gray": 127,
            "arm_enabled": True,
            "arm_x1": 14.5,
            "arm_y1": 7.5,
            "arm_x2": 15.0,
            "arm_y2": 7.5,
            "arm_stroke": 1.0,
        },
        align_stem_to_circle_center_fn=lambda p: dict(p),
        quantize_badge_params_fn=lambda p, _w, _h: dict(p),
        clip_scalar_fn=lambda value, lower, upper: min(max(value, lower), upper),
        grayhex_fn=lambda _value: "#808080",
        co2_layout_fn=lambda _p: {},
        t_path_d="T",
        t_xmin=0.0,
        t_ymax=0.0,
        m_path_d="M",
        m_xmin=0.0,
        m_ymax=0.0,
    )

    assert "<line" not in svg
    assert ">VOC</text>" in svg


def test_generate_badge_svg_impl_renders_rf_text() -> None:
    svg = semantic_badge_svg_helpers.generateBadgeSvgImpl(
        40,
        40,
        {"cx": 20.0, "cy": 20.0, "r": 10.0, "stroke_circle": 1.2, "fill_gray": 220, "stroke_gray": 152, "draw_text": True, "text_mode": "rf", "text_gray": 152, "label": "rF"},
        align_stem_to_circle_center_fn=lambda p: dict(p),
        quantize_badge_params_fn=lambda p, _w, _h: dict(p),
        clip_scalar_fn=lambda value, lower, upper: min(max(value, lower), upper),
        grayhex_fn=lambda _value: "#808080",
        co2_layout_fn=lambda _p: {},
        t_path_d="T",
        t_xmin=0.0,
        t_ymax=0.0,
        m_path_d="M",
        m_xmin=0.0,
        m_ymax=0.0,
    )

    assert ">rF</text>" in svg
