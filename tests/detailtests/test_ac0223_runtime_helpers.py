from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticAc0223Runtime as helpers


def test_finalize_ac0223_badge_params_impl_applies_valve_head_defaults() -> None:
    badge_params = {
        "cx": 10.0,
        "cy": 20.0,
        "r": 5.0,
    }

    updated = helpers.finalizeAc0223BadgeParamsImpl(
        base_name="AC0223",
        filename="AC0223_L.jpg",
        width=50,
        height=75,
        badge_params=badge_params,
    )

    assert updated is badge_params
    assert updated["variant_name"] == "AC0223_L"
    assert updated["head_style"] == "ac0223_triple_valve"
    assert updated["arm_enabled"] is True
    assert updated["arm_x1"] == 10.0
    assert updated["arm_x2"] == 10.0
    assert updated["arm_y2"] == updated["head_hub_cy"]
    assert updated["arm_y1"] >= updated["arm_y2"]


def test_finalize_ac0223_badge_params_impl_is_noop_for_other_families() -> None:
    badge_params = {"cx": 1.0}

    updated = helpers.finalizeAc0223BadgeParamsImpl(
        base_name="AC0811",
        filename="AC0811_L.jpg",
        width=50,
        height=75,
        badge_params=badge_params,
    )

    assert updated == {"cx": 1.0}
