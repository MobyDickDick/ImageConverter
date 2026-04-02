from __future__ import annotations

from src import imageCompositeConverterSemanticHarmonization as semantic_harmonization_helpers


def test_needs_large_circle_overflow_guard_requires_large_co2_circle_without_connectors() -> None:
    assert semantic_harmonization_helpers.needsLargeCircleOverflowGuardImpl(
        {
            "circle_enabled": True,
            "draw_text": True,
            "text_mode": "co2",
            "template_circle_radius": 12.0,
            "arm_enabled": False,
            "stem_enabled": False,
        }
    )
    assert not semantic_harmonization_helpers.needsLargeCircleOverflowGuardImpl(
        {
            "circle_enabled": True,
            "draw_text": True,
            "text_mode": "co2",
            "template_circle_radius": 8.0,
            "arm_enabled": True,
            "stem_enabled": False,
        }
    )


def test_family_harmonized_badge_colors_boosts_contrast_and_caps_text_stem() -> None:
    colors = semantic_harmonization_helpers.familyHarmonizedBadgeColorsImpl(
        [
            {"params": {"fill_gray": 140, "stroke_gray": 120, "text_gray": 110, "stem_gray": 130}},
            {"params": {"fill_gray": 138, "stroke_gray": 118, "text_gray": 115, "stem_gray": 116}},
        ]
    )

    assert colors["fill_gray"] > colors["stroke_gray"]
    assert colors["text_gray"] <= colors["stroke_gray"]
    assert colors["stem_gray"] <= colors["stroke_gray"]


def test_scale_badge_params_enables_overflow_for_large_centered_co2_circle() -> None:
    scaled = semantic_harmonization_helpers.scaleBadgeParamsImpl(
        {
            "circle_enabled": True,
            "cx": 15.0,
            "cy": 15.0,
            "r": 12.0,
            "stroke_circle": 1.0,
            "draw_text": True,
            "text_mode": "co2",
            "arm_enabled": False,
            "stem_enabled": False,
        },
        anchor_w=30,
        anchor_h=30,
        target_w=40,
        target_h=40,
        clip_scalar_fn=lambda value, low, high: max(low, min(high, float(value))),
        needs_large_circle_overflow_guard_fn=semantic_harmonization_helpers.needsLargeCircleOverflowGuardImpl,
    )

    assert scaled["allow_circle_overflow"] is True
    assert float(scaled["circle_radius_lower_bound_px"]) >= 20.5
