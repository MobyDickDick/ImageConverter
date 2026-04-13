from src.iCCModules import imageCompositeConverterSemanticVisualOverride as helpers


def test_apply_semantic_visual_override_impl_switches_mode_for_gradient_stripe() -> None:
    messages: list[str] = []
    params = {"mode": "semantic_badge", "elements": ["SEMANTIC: sample"]}

    updated, applied = helpers.applySemanticVisualOverrideImpl(
        params=params,
        stripe_strategy={"stops": 3},
        elongated_rect_geometry=False,
        print_fn=messages.append,
    )

    assert applied is True
    assert updated["mode"] == "non_composite_visual_override"
    assert updated["visual_override_reason"] == "gradient_stripe_geometry_detected"
    assert params["mode"] == "semantic_badge"
    assert messages and "Geometrie-Override" in messages[0]


def test_apply_semantic_visual_override_impl_keeps_params_when_not_needed() -> None:
    params = {"mode": "non_composite"}

    updated, applied = helpers.applySemanticVisualOverrideImpl(
        params=params,
        stripe_strategy=None,
        elongated_rect_geometry=False,
        print_fn=lambda _line: None,
    )

    assert applied is False
    assert updated is params
