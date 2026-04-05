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


def test_tune_ac0831_co2_badge_enforces_vertical_cluster_defaults() -> None:
    tuned = semantic_label_helpers.tuneAc0831Co2BadgeImpl(
        {"r": 7.0, "width": 15.0, "height": 15.0, "co2_dy": 0.0},
        ac08_stroke_width_px=1,
    )

    assert tuned["co2_anchor_mode"] == "cluster"
    assert tuned["co2_index_mode"] == "superscript"
    assert float(tuned["co2_dy"]) >= 0.35
    assert float(tuned["co2_superscript_min_gap_scale"]) >= 0.19


def test_tune_ac0834_co2_badge_keeps_tiny_geometry_centered() -> None:
    tuned = semantic_label_helpers.tuneAc0834Co2BadgeImpl(
        {"cx": 8.0, "r": 2.0},
        16,
        12,
        light_circle_stroke_gray=152,
        ac08_stroke_width_px=1,
    )

    assert tuned["cy"] == 6.0
    assert float(tuned["r"]) >= 12 * 0.4 * 0.95
    assert tuned["arm_y1"] == 6.0
    assert tuned["arm_x2"] == 16.0


def test_default_ac0834_params_impl_delegates_in_sequence() -> None:
    calls: list[str] = []

    def _default_ac0814_params(w: int, h: int) -> dict:
        calls.append(f"default:{w}x{h}")
        return {"base": True}

    def _apply_co2_label(params: dict) -> dict:
        calls.append("apply")
        updated = dict(params)
        updated["co2"] = True
        return updated

    def _tune_ac0834(params: dict, w: int, h: int) -> dict:
        calls.append(f"tune:{w}x{h}")
        updated = dict(params)
        updated["tuned"] = True
        return updated

    result = semantic_label_helpers.defaultAc0834ParamsImpl(
        25,
        15,
        default_ac0814_params_fn=_default_ac0814_params,
        apply_co2_label_fn=_apply_co2_label,
        tune_ac0834_co2_badge_fn=_tune_ac0834,
    )

    assert result == {"base": True, "co2": True, "tuned": True}
    assert calls == ["default:25x15", "apply", "tune:25x15"]
