from src.iCCModules import imageCompositeConverterIterationPipeline as helpers


class _OrchestrationHelpersStub:
    def __init__(self) -> None:
        self.captured: dict[str, object] = {}

    def buildRunIterationPipelineOrchestrationKwargsForRunImpl(self, **kwargs):
        self.captured["orchestration_kwargs"] = kwargs
        return {"orchestration": "kwargs"}

    def buildRunIterationPipelineFromInputsViaOrchestrationKwargsImpl(self, **kwargs):
        self.captured["from_inputs_builder_kwargs"] = kwargs
        return {"from_inputs": "kwargs"}

    def runIterationPipelineFromInputsViaOrchestrationForRunCallImpl(self, **kwargs):
        self.captured["run_call_kwargs"] = kwargs
        return {"status": "ok"}

    def buildRunIterationPipelineViaOrchestrationForRunCallKwargsImpl(self):
        return "build_via"

    def runIterationPipelineViaOrchestrationForRunImpl(self):
        return "run_via"

    def runIterationPipelineFromInputsViaOrchestrationImpl(self):
        return "run_from_inputs"

    def executeRunIterationPipelineFromInputsViaOrchestrationImpl(self):
        return "execute_from_inputs"

    def buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl(self):
        return "build_from_inputs_for_run"

    def runIterationPipelineFromInputsViaOrchestrationForRunImpl(self):
        return "run_from_inputs_for_run"

    def executeRunIterationPipelineFromInputsViaOrchestrationForRunImpl(self):
        return "execute_from_inputs_for_run"

    def runIterationPipelineOrchestrationImpl(self):
        return "run_orchestration"

    def executeRunIterationPipelineOrchestrationForRunImpl(self):
        return "execute_orchestration"


def test_run_iteration_pipeline_impl_delegates_orchestration_wiring() -> None:
    stub = _OrchestrationHelpersStub()

    result = helpers.runIterationPipelineImpl(
        img_path="img.png",
        csv_path="meta.csv",
        max_iterations=8,
        svg_out_dir="svg",
        diff_out_dir="diff",
        reports_out_dir="reports",
        debug_ac0811_dir="debug-ac0811",
        debug_element_diff_dir="debug-diff",
        badge_validation_rounds=5,
        iteration_orchestration_helpers=stub,
        iteration_run_preparation_helpers=type("RunPrep", (), {
            "prepareRunIterationPipelineLocalsForRunImpl": staticmethod(lambda **_: None),
            "buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl": staticmethod(lambda **_: None),
        })(),
        iteration_execution_context_helpers=type("ExecCtx", (), {
            "buildRunIterationPipelineForRunCallKwargsImpl": staticmethod(lambda **_: None),
            "runIterationPipelineForRunImpl": staticmethod(lambda **_: None),
        })(),
        iteration_execution_helpers=type("ExecHelpers", (), {
            "buildPreparedModeBuilderKwargsImpl": staticmethod(lambda **_: None),
            "runPreparedIterationAndFinalizeImpl": staticmethod(lambda **_: None),
        })(),
        iteration_context_helpers=type("IterCtx", (), {"buildPreparedIterationModeKwargsImpl": staticmethod(lambda **_: None)})(),
        iteration_dispatch_helpers=type("Dispatch", (), {"runPreparedIterationModeImpl": staticmethod(lambda **_: None)})(),
        iteration_finalization_helpers=type("Final", (), {"finalizeIterationResultImpl": staticmethod(lambda **_: None)})(),
        iteration_bindings_helpers="bindings",
        iteration_initialization_helpers="initialization",
        iteration_setup_helpers="setup",
        iteration_runtime_helpers="runtime",
        iteration_mode_runtime_preparation_helpers="mode_runtime_prep",
        iteration_mode_setup_helpers="mode_setup",
        iteration_mode_preparation_helpers="mode_prep",
        iteration_mode_dependency_setup_helpers="mode_dep_setup",
        iteration_mode_dependency_helpers="mode_dep",
        iteration_mode_runtime_helpers="mode_runtime",
        iteration_preparation_helpers="iteration_prep",
        gradient_stripe_strategy_helpers="gradient",
        semantic_audit_bootstrap_helpers="audit_bootstrap",
        semantic_audit_logging_helpers="audit_logging",
        semantic_audit_runtime_helpers="audit_runtime",
        semantic_mismatch_reporting_helpers="mismatch_reporting",
        semantic_validation_logging_helpers="validation_logging",
        semantic_mismatch_runtime_helpers="mismatch_runtime",
        semantic_validation_context_helpers="validation_context",
        semantic_validation_runtime_helpers="validation_runtime",
        semantic_post_validation_helpers="post_validation",
        semantic_validation_finalization_helpers="validation_final",
        semantic_iteration_finalization_helpers="iteration_final",
        semantic_ac0223_runtime_helpers="ac0223_runtime",
        semantic_visual_override_helpers="visual_override",
        non_composite_runtime_helpers="non_composite",
        conversion_composite_helpers="conversion_composite",
        semantic_badge_runtime_helpers="badge_runtime",
        dual_arrow_badge_helpers="dual_arrow_badge",
        dual_arrow_runtime_helpers="dual_arrow_runtime",
        ensure_conversion_runtime_dependencies_fn="ensure_deps",
        cv2_module="cv2",
        np_module="np",
        fitz_module="fitz",
        run_seed=13,
        pass_seed_offset=21,
        action_cls="Action",
        perception_cls="Perception",
        reflection_cls="Reflection",
        get_base_name_from_file_fn="get_base",
        semantic_audit_record_fn="audit_record",
        semantic_quality_flags_fn="quality_flags",
        looks_like_elongated_foreground_rect_fn="looks_like_rect",
        render_embedded_raster_svg_fn="render_raster",
        print_fn="print",
        time_ns_fn="time_ns",
        calculate_error_fn="calculate_error",
        math_module="math",
    )

    assert stub.captured["orchestration_kwargs"]["img_path"] == "img.png"
    assert stub.captured["from_inputs_builder_kwargs"]["run_iteration_pipeline_orchestration_kwargs"] == {
        "orchestration": "kwargs"
    }
    assert stub.captured["run_call_kwargs"]["run_iteration_pipeline_from_inputs_via_orchestration_kwargs"] == {
        "from_inputs": "kwargs"
    }
    assert result == {"status": "ok"}


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"alpha": 1, "beta": "two"}

    result = helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_build_run_iteration_pipeline_orchestration_kwargs_for_run_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"img_path": "img.png", "max_iterations": 8}

    result = helpers.buildRunIterationPipelineOrchestrationKwargsForRunCallKwargsImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"run_iteration_pipeline_orchestration_kwargs": {"orchestration": "kwargs"}}

    result = helpers.buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunCallKwargsImpl(
        **kwargs
    )

    assert result == kwargs
    assert result is not kwargs
