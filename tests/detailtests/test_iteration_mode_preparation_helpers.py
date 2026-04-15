from src.iCCModules import imageCompositeConverterIterationModePreparation as helpers


class _SemanticVisualOverrideHelpers:
    def __init__(self):
        self.calls = []

    def applySemanticVisualOverrideImpl(self, **kwargs):
        self.calls.append(kwargs)
        return {"params": kwargs["params"], "semantic_mode_visual_override": True}


def test_prepare_iteration_mode_runtime_for_run_impl_wires_dependencies_and_extracts_bindings() -> None:
    captured: dict[str, object] = {}

    class _ModeDependencySetupHelpers:
        @staticmethod
        def buildIterationModeRunnerDependenciesForRunImpl(**kwargs):
            captured["dependency_kwargs"] = kwargs
            return {"deps": "payload"}

    class _IterationOrchestrationHelpers:
        @staticmethod
        def prepareIterationModeRuntimeImpl(**kwargs):
            captured["orchestration_kwargs"] = kwargs
            kwargs["apply_semantic_visual_override_fn"](params={"mode": "semantic_badge"}, stripe_strategy="gradient")
            return {"params": {"mode": "semantic_badge"}, "semantic_mode_visual_override": True, "mode_runners": {"run": object()}}

    class _IterationModeRuntimeHelpers:
        @staticmethod
        def buildIterationModeRunnersImpl(**_kwargs):
            return {"runner": object()}

    class _IterationContextHelpers:
        @staticmethod
        def extractIterationModeRuntimeBindingsImpl(*, mode_runtime):
            captured["mode_runtime"] = mode_runtime
            return mode_runtime

    semantic_visual_helpers = _SemanticVisualOverrideHelpers()

    result = helpers.prepareIterationModeRuntimeForRunImpl(
        np_module="np",
        action_cls="Action",
        params={"mode": "semantic_badge"},
        perception_image=[[0]],
        stripe_strategy="gradient",
        looks_like_elongated_foreground_rect_fn=lambda *_args, **_kwargs: False,
        semantic_visual_override_helpers=semantic_visual_helpers,
        iteration_mode_dependency_setup_helpers=_ModeDependencySetupHelpers,
        iteration_mode_runtime_helpers=_IterationModeRuntimeHelpers,
        iteration_orchestration_helpers=_IterationOrchestrationHelpers,
        iteration_context_helpers=_IterationContextHelpers,
        mode_dependency_helper_modules={"semantic_mismatch_reporting_helpers": "mismatch"},
        semantic_audit_record_fn=repr,
        semantic_quality_flags_fn=str,
        render_embedded_raster_svg_fn=bytes,
        print_fn=print,
    )

    dependency_kwargs = captured["dependency_kwargs"]
    assert dependency_kwargs["np_module"] == "np"
    assert dependency_kwargs["action_cls"] == "Action"
    assert dependency_kwargs["semantic_mismatch_reporting_helpers"] == "mismatch"
    assert dependency_kwargs["semantic_audit_record_fn"] is repr

    assert captured["orchestration_kwargs"]["mode_runner_dependencies"] == {"deps": "payload"}
    assert semantic_visual_helpers.calls[0]["print_fn"] is print
    assert result["semantic_mode_visual_override"] is True
