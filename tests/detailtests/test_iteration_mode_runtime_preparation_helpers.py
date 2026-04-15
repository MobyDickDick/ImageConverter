from src.iCCModules import imageCompositeConverterIterationModeRuntimePreparation as helpers


def test_prepare_iteration_mode_runtime_bindings_impl_builds_kwargs_and_extracts_bindings():
    captured = {}

    def _build_kwargs(**kwargs):
        captured["build_kwargs"] = kwargs
        return {"prepared": True, "value": 7}

    def _prepare_runtime(**kwargs):
        captured["prepare_kwargs"] = kwargs
        return {
            "params": {"mode": "semantic_badge"},
            "semantic_mode_visual_override": "override",
            "mode_runners": {"semantic_badge": object()},
            "ignored": "value",
        }

    result = helpers.prepareIterationModeRuntimeBindingsImpl(
        build_prepare_iteration_mode_runtime_for_run_kwargs_fn=_build_kwargs,
        prepare_iteration_mode_runtime_for_run_fn=_prepare_runtime,
        build_prepare_iteration_mode_runtime_for_run_kwargs_kwargs={"alpha": 1, "beta": 2},
    )

    assert captured["build_kwargs"] == {"alpha": 1, "beta": 2}
    assert captured["prepare_kwargs"] == {"prepared": True, "value": 7}
    assert result["params"] == {"mode": "semantic_badge"}
    assert result["semantic_mode_visual_override"] == "override"
    assert sorted(result["mode_runners"].keys()) == ["semantic_badge"]
