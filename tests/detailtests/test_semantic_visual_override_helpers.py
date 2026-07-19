from src.iCCModules import imageCompositeConverterSemanticVisualOverride as helpers


def test_apply_semantic_visual_override_impl_ignores_gradient_stripe() -> None:
    messages: list[str] = []
    params = {"mode": "semantic_badge", "elements": ["SEMANTIC: sample"]}

    updated, applied = helpers.applySemanticVisualOverrideImpl(
        params=params,
        stripe_strategy={"stops": 3},
        elongated_rect_geometry=False,
        print_fn=messages.append,
    )

    assert applied is False
    assert updated is params
    assert messages == []


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
