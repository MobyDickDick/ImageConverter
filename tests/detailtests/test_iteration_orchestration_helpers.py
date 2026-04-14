from src.iCCModules import imageCompositeConverterIterationOrchestration as helpers


def test_prepare_iteration_mode_runtime_impl_applies_visual_override_then_builds_runners() -> None:
    captured: dict[str, object] = {}

    def _looks_like_elongated_foreground_rect_fn(image):
        captured["elongated_input"] = image
        return {"elongated": True}

    def _apply_semantic_visual_override_fn(**kwargs):
        captured["visual_override_kwargs"] = kwargs
        params = dict(kwargs["params"])
        params["mode"] = "semantic_badge"
        return params, True

    def _build_iteration_mode_runners_fn(**kwargs):
        captured["mode_runner_kwargs"] = kwargs
        return {"run_semantic_badge_iteration": "runner"}

    result = helpers.prepareIterationModeRuntimeImpl(
        perception_image="pixel-grid",
        params={"mode": "composite"},
        stripe_strategy="gradient_stripe",
        looks_like_elongated_foreground_rect_fn=_looks_like_elongated_foreground_rect_fn,
        apply_semantic_visual_override_fn=_apply_semantic_visual_override_fn,
        build_iteration_mode_runners_fn=_build_iteration_mode_runners_fn,
        mode_runner_dependencies={"dep": 1},
    )

    assert captured["elongated_input"] == "pixel-grid"
    assert captured["visual_override_kwargs"]["elongated_rect_geometry"] == {"elongated": True}
    assert captured["mode_runner_kwargs"] == {"dep": 1}
    assert result["params"]["mode"] == "semantic_badge"
    assert result["semantic_mode_visual_override"] is True
    assert result["mode_runners"]["run_semantic_badge_iteration"] == "runner"
