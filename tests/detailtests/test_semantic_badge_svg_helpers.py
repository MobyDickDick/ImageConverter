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
