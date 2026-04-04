from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticLabels as semantic_label_helpers


def test_apply_co2_label_sets_defaults() -> None:
    params = semantic_label_helpers.applyCo2LabelImpl(
        {"stroke_gray": 150},
        light_circle_stroke_gray=152,
        semantic_text_base_scale=1.0,
    )

    assert params["text_mode"] == "co2"
    assert params["text_gray"] == 150
    assert params["co2_anchor_mode"] == "center_co"
    assert params["co2_index_mode"] == "subscript"


def test_co2_layout_caps_width_scale_for_ac0820() -> None:
    layout = semantic_label_helpers.co2LayoutImpl(
        {
            "cx": 20.0,
            "cy": 20.0,
            "r": 12.0,
            "stroke_circle": 1.0,
            "co2_font_scale": 0.82,
            "co2_sub_font_scale": 66.0,
            "co2_width_scale": 1.1,
            "badge_symbol_name": "AC0820",
        }
    )

    assert float(layout["width_scale"]) <= 0.90


def test_normalize_centered_co2_label_adjusts_label_metrics() -> None:
    normalized = semantic_label_helpers.normalizeCenteredCo2LabelImpl(
        {
            "text_mode": "co2",
            "circle_enabled": True,
            "arm_enabled": False,
            "stem_enabled": False,
            "r": 9.0,
            "stroke_circle": 1.0,
            "co2_font_scale": 1.4,
            "co2_sub_font_scale": 72.0,
            "co2_dx": 8.0,
            "co2_dy": 5.0,
            "stroke_gray": 155,
        }
    )

    assert 0.72 <= float(normalized["co2_font_scale"]) <= 0.96
    assert 60.0 <= float(normalized["co2_sub_font_scale"]) <= 68.0
    assert abs(float(normalized["co2_dx"])) <= 0.18 * 9.0
    assert abs(float(normalized["co2_dy"])) <= 0.20 * 9.0
    assert normalized["text_gray"] == 155
