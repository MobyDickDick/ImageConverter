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


def test_build_run_iteration_pipeline_orchestration_kwargs_for_run_from_inputs_impl_delegates_mapping_and_execution() -> None:
    calls: dict[str, object] = {}

    def _build_orchestration_call_kwargs(**kwargs):
        calls["build_orchestration_call_kwargs"] = kwargs
        return {"mapped": "orchestration"}

    def _execute_orchestration_kwargs_builder(**kwargs):
        calls["execute_orchestration_kwargs_builder"] = kwargs
        builder_fn = kwargs["build_run_iteration_pipeline_orchestration_kwargs_for_run_fn"]
        calls["builder_result"] = builder_fn(
            **kwargs["run_iteration_pipeline_orchestration_call_kwargs"]
        )
        return {"orchestration": "final"}

    def _build_orchestration_kwargs(**kwargs):
        calls["build_orchestration_kwargs"] = kwargs
        return {"orchestration": "built"}

    result = helpers.buildRunIterationPipelineOrchestrationKwargsForRunFromInputsImpl(
        img_path="img.png",
        csv_path="meta.csv",
        max_iterations=8,
        svg_out_dir="svg",
        diff_out_dir="diff",
        reports_out_dir="reports",
        debug_ac0811_dir="debug-ac0811",
        debug_element_diff_dir="debug-element",
        badge_validation_rounds=5,
        ensure_conversion_runtime_dependencies_fn="ensure_deps",
        cv2_module="cv2",
        np_module="np",
        fitz_module="fitz",
        iteration_run_preparation_helpers=type("RunPrep", (), {
            "prepareRunIterationPipelineLocalsForRunImpl": staticmethod(lambda **_: None),
            "buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl": staticmethod(lambda **_: None),
        })(),
        iteration_execution_context_helpers=type("ExecCtx", (), {
            "buildRunIterationPipelineForRunCallKwargsImpl": staticmethod(lambda **_: None),
            "runIterationPipelineForRunImpl": staticmethod(lambda **_: None),
        })(),
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
        iteration_execution_helpers=type("ExecHelpers", (), {
            "buildPreparedModeBuilderKwargsImpl": staticmethod(lambda **_: None),
            "runPreparedIterationAndFinalizeImpl": staticmethod(lambda **_: None),
        })(),
        iteration_context_helpers=type("IterCtx", (), {
            "buildPreparedIterationModeKwargsImpl": staticmethod(lambda **_: None)
        })(),
        iteration_dispatch_helpers=type("Dispatch", (), {
            "runPreparedIterationModeImpl": staticmethod(lambda **_: None)
        })(),
        iteration_finalization_helpers=type("Final", (), {
            "finalizeIterationResultImpl": staticmethod(lambda **_: None)
        })(),
        math_module="math",
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
        iteration_orchestration_helpers="orchestration_helpers",
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
        build_run_iteration_pipeline_orchestration_call_kwargs_fn=_build_orchestration_call_kwargs,
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=_build_orchestration_kwargs,
        execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=_execute_orchestration_kwargs_builder,
    )

    assert calls["build_orchestration_call_kwargs"]["img_path"] == "img.png"
    assert calls["execute_orchestration_kwargs_builder"] == {
        "run_iteration_pipeline_orchestration_call_kwargs": {"mapped": "orchestration"},
        "build_run_iteration_pipeline_orchestration_kwargs_for_run_fn": _build_orchestration_kwargs,
    }
    assert calls["build_orchestration_kwargs"] == {"mapped": "orchestration"}
    assert calls["builder_result"] == {"orchestration": "built"}
    assert result == {"orchestration": "final"}


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


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_for_run_impl_returns_copy() -> None:
    kwargs = {"run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs": {"alpha": 1}}

    result = helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsForRunImpl(
        **kwargs
    )

    assert result == kwargs
    assert result is not kwargs


def test_build_run_iteration_pipeline_orchestration_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"img_path": "img.png", "csv_path": "meta.csv"}

    result = helpers.buildRunIterationPipelineOrchestrationCallKwargsImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs": {"alpha": 1}}

    result = helpers.buildRunIterationPipelineFromInputsViaOrchestrationCallKwargsImpl(
        **kwargs
    )

    assert result == kwargs
    assert result is not kwargs


def test_execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_impl_delegates_builder() -> None:
    calls: dict[str, object] = {}

    def _builder(**kwargs):
        calls["builder_kwargs"] = kwargs
        return {"orchestration": "built"}

    result = helpers.executeBuildRunIterationPipelineOrchestrationKwargsForRunImpl(
        run_iteration_pipeline_orchestration_call_kwargs={"img_path": "img.png"},
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=_builder,
    )

    assert calls["builder_kwargs"] == {"img_path": "img.png"}
    assert result == {"orchestration": "built"}


def test_execute_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_builder_for_run_impl_delegates_builder() -> None:
    calls: dict[str, object] = {}

    def _builder(**kwargs):
        calls["builder_kwargs"] = kwargs
        return {"from_inputs": "built"}

    result = helpers.executeRunIterationPipelineFromInputsViaOrchestrationKwargsBuilderForRunImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs={"payload": "raw"},
        build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_fn=_builder,
    )

    assert calls["builder_kwargs"] == {"payload": "raw"}
    assert result == {"from_inputs": "built"}


def test_run_iteration_pipeline_orchestration_kwargs_for_run_impl_delegates_executor() -> None:
    calls: dict[str, object] = {}

    def _executor(**kwargs):
        calls["executor_kwargs"] = kwargs
        return {"orchestration": "built"}

    result = helpers.runIterationPipelineOrchestrationKwargsForRunImpl(
        run_iteration_pipeline_orchestration_call_kwargs={"img_path": "img.png"},
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn="builder",
        execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=_executor,
    )

    assert calls["executor_kwargs"] == {
        "run_iteration_pipeline_orchestration_call_kwargs": {"img_path": "img.png"},
        "build_run_iteration_pipeline_orchestration_kwargs_for_run_fn": "builder",
    }
    assert result == {"orchestration": "built"}


def test_run_iteration_pipeline_orchestration_kwargs_for_run_call_impl_delegates_builder_then_executor() -> None:
    calls: dict[str, object] = {}

    def _build_call_kwargs(**kwargs):
        calls["build_call_kwargs"] = kwargs
        return {"img_path": "mapped.png"}

    def _build_kwargs(**kwargs):
        calls["build_kwargs"] = kwargs
        return {"orchestration": "built"}

    result = helpers.runIterationPipelineOrchestrationKwargsForRunCallImpl(
        build_run_iteration_pipeline_orchestration_call_kwargs_fn=_build_call_kwargs,
        run_iteration_pipeline_orchestration_call_kwargs={"img_path": "raw.png"},
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=_build_kwargs,
        execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
            helpers.executeBuildRunIterationPipelineOrchestrationKwargsForRunImpl
        ),
    )

    assert calls["build_call_kwargs"] == {"img_path": "raw.png"}
    assert calls["build_kwargs"] == {"img_path": "mapped.png"}
    assert result == {"orchestration": "built"}


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_impl_delegates_mapping_and_builder_execution() -> None:
    calls: dict[str, object] = {}

    def _build_call_kwargs(**kwargs):
        calls["build_call_kwargs"] = kwargs
        return {"payload": "mapped"}

    def _build_kwargs(**kwargs):
        calls["build_kwargs"] = kwargs
        return {"from_inputs": "built"}

    def _execute_kwargs_builder_for_run(**kwargs):
        calls["execute_kwargs_builder_for_run"] = kwargs
        build_fn = kwargs["build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_fn"]
        calls["build_kwargs_result"] = build_fn(
            **kwargs["run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs"]
        )
        return {"from_inputs": "final"}

    result = helpers.buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunImpl(
        run_iteration_pipeline_orchestration_kwargs={"orchestration": "kwargs"},
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn="orchestration_builder",
        run_iteration_pipeline_orchestration_fn="orchestration_runner",
        execute_run_iteration_pipeline_orchestration_for_run_fn="orchestration_executor",
        build_run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs_fn=_build_call_kwargs,
        execute_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_builder_for_run_fn=_execute_kwargs_builder_for_run,
        build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_fn=_build_kwargs,
    )

    assert calls["build_call_kwargs"] == {
        "run_iteration_pipeline_orchestration_kwargs": {"orchestration": "kwargs"},
        "build_run_iteration_pipeline_orchestration_kwargs_for_run_fn": "orchestration_builder",
        "run_iteration_pipeline_orchestration_fn": "orchestration_runner",
        "execute_run_iteration_pipeline_orchestration_for_run_fn": "orchestration_executor",
    }
    assert calls["execute_kwargs_builder_for_run"] == {
        "run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs": {
            "payload": "mapped"
        },
        "build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_fn": _build_kwargs,
    }
    assert calls["build_kwargs"] == {"payload": "mapped"}
    assert calls["build_kwargs_result"] == {"from_inputs": "built"}
    assert result == {"from_inputs": "final"}




def test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs_impl_returns_copy() -> None:
    kwargs = {"run_iteration_pipeline_orchestration_kwargs": {"orchestration": "kwargs"}}

    result = (
        helpers.buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsKwargsImpl(
            **kwargs
        )
    )

    assert result == kwargs
    assert result is not kwargs


def test_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_impl_delegates_builder_then_runner() -> None:
    calls: dict[str, object] = {}

    def _build_call_kwargs(**kwargs):
        calls["build_call_kwargs"] = kwargs
        return {"mapped": "kwargs"}

    def _run_from_inputs_kwargs(**kwargs):
        calls["run_from_inputs_kwargs"] = kwargs
        return {"status": "ok"}

    result = (
        helpers.runIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsImpl(
            build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs_fn=_build_call_kwargs,
            run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs={
                "alpha": 1,
                "beta": "two",
            },
            build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_fn=_run_from_inputs_kwargs,
        )
    )

    assert calls["build_call_kwargs"] == {"alpha": 1, "beta": "two"}
    assert calls["run_from_inputs_kwargs"] == {"mapped": "kwargs"}
    assert result == {"status": "ok"}


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs_fn": "builder"}

    result = (
        helpers.buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsCallKwargsImpl(
            **kwargs
        )
    )

    assert result == kwargs
    assert result is not kwargs


def test_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_call_impl_delegates_builder_then_runner() -> None:
    calls: dict[str, object] = {}

    def _build_call_kwargs(**kwargs):
        calls["build_call_kwargs"] = kwargs
        return {"mapped": "call"}

    def _run_kwargs_for_run_from_inputs(**kwargs):
        calls["run_kwargs_for_run_from_inputs"] = kwargs
        return {"status": "ok"}

    result = helpers.runIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsCallImpl(
        build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_call_kwargs_fn=_build_call_kwargs,
        run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_call_kwargs={
            "alpha": 1,
            "beta": "two",
        },
        run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_fn=_run_kwargs_for_run_from_inputs,
    )

    assert calls["build_call_kwargs"] == {"alpha": 1, "beta": "two"}
    assert calls["run_kwargs_for_run_from_inputs"] == {"mapped": "call"}
    assert result == {"status": "ok"}


def test_execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_impl_delegates_builder_then_runner() -> None:
    calls: dict[str, object] = {}

    def _builder(**kwargs):
        calls["builder_kwargs"] = kwargs
        return {"payload": "built"}

    def _runner(**kwargs):
        calls["runner_kwargs"] = kwargs
        return {"status": "ok"}

    result = helpers.executeRunIterationPipelineFromInputsViaOrchestrationForRunCallImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs={
            "payload": "raw"
        },
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=_builder,
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=_runner,
    )

    assert calls["builder_kwargs"] == {"payload": "raw"}
    assert calls["runner_kwargs"] == {"payload": "built"}
    assert result == {"status": "ok"}


def test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_impl_delegates_executor() -> None:
    calls: dict[str, object] = {}

    def _executor(**kwargs):
        calls["executor_kwargs"] = kwargs
        return {"status": "executed"}

    result = helpers.runIterationPipelineFromInputsViaOrchestrationForRunCallForRunImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs={
            "payload": "call"
        },
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn="builder",
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn="runner",
        execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=_executor,
    )

    assert calls["executor_kwargs"] == {
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs": {
            "payload": "call"
        },
        "build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn": "builder",
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn": "runner",
    }
    assert result == {"status": "executed"}


def test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_kwargs_impl_delegates_builder() -> None:
    result = (
        helpers.runIterationPipelineFromInputsViaOrchestrationForRunCallForRunKwargsImpl(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs={
                "payload": "call"
            },
            build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
                "builder"
            ),
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn="runner",
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
                "executor"
            ),
        )
    )

    assert result == {
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs": {
            "payload": "call"
        },
        "build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn": "builder",
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn": "runner",
        "execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn": "executor",
    }


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"alpha": 1, "beta": "two"}

    result = (
        helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallKwargsImpl(
            **kwargs
        )
    )

    assert result == kwargs
    assert result is not kwargs


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_kwargs_for_run_impl_returns_mapping() -> None:
    result = (
        helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallKwargsForRunImpl(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs={
                "payload": "run-call"
            },
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
                "run_for_run_call_fn"
            ),
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
                "execute_for_run_call_fn"
            ),
        )
    )

    assert result == {
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs": {
            "payload": "run-call"
        },
        "build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn": (
            helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl
        ),
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn": (
            "run_for_run_call_fn"
        ),
        "execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn": (
            "execute_for_run_call_fn"
        ),
    }


def test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_impl_delegates_builder_then_runner() -> None:
    calls: dict[str, object] = {}

    def _builder(**kwargs):
        calls["builder_kwargs"] = kwargs
        return {"payload": "built"}

    def _runner(**kwargs):
        calls["runner_kwargs"] = kwargs
        return {"status": "ok"}

    result = (
        helpers.runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallImpl(
            build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_kwargs_fn=_builder,
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_kwargs={
                "payload": "raw"
            },
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_fn=_runner,
        )
    )

    assert calls["builder_kwargs"] == {"payload": "raw"}
    assert calls["runner_kwargs"] == {"payload": "built"}
    assert result == {"status": "ok"}


def test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_for_run_impl_delegates_builder_then_runner() -> None:
    calls: dict[str, object] = {}

    def _run_for_run_call(**kwargs):
        calls["run_for_run_call_kwargs"] = kwargs
        return {"status": "ok"}

    result = (
        helpers.runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallForRunImpl(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs={
                "payload": "raw"
            },
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
                _run_for_run_call
            ),
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
                helpers.executeRunIterationPipelineFromInputsViaOrchestrationForRunCallImpl
            ),
        )
    )

    assert calls["run_for_run_call_kwargs"] == {"payload": "raw"}
    assert result == {"status": "ok"}


def test_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_call_impl_delegates_builder() -> None:
    result = (
        helpers.runIterationPipelineFromInputsViaOrchestrationKwargsForRunCallImpl(
            run_iteration_pipeline_from_inputs_via_orchestration_kwargs={
                "from_inputs": "kwargs"
            },
            build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn="build_via",
            run_iteration_pipeline_via_orchestration_for_run_fn="run_via",
            run_iteration_pipeline_from_inputs_via_orchestration_fn="run_from_inputs",
            execute_run_iteration_pipeline_from_inputs_via_orchestration_fn=(
                "execute_from_inputs"
            ),
            build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
                "build_for_run"
            ),
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn="run_for_run",
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
                "execute_for_run"
            ),
        )
    )

    assert result == {
        "run_iteration_pipeline_from_inputs_via_orchestration_kwargs": {
            "from_inputs": "kwargs"
        },
        "build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn": "build_via",
        "run_iteration_pipeline_via_orchestration_for_run_fn": "run_via",
        "run_iteration_pipeline_from_inputs_via_orchestration_fn": "run_from_inputs",
        "execute_run_iteration_pipeline_from_inputs_via_orchestration_fn": "execute_from_inputs",
        "build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn": "build_for_run",
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn": "run_for_run",
        "execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn": "execute_for_run",
    }


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_kwargs_impl_delegates_builder() -> None:
    result = (
        helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallKwargsImpl(
            run_iteration_pipeline_from_inputs_via_orchestration_kwargs={
                "from_inputs": "kwargs"
            },
            build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn=(
                "build_via"
            ),
            run_iteration_pipeline_via_orchestration_for_run_fn="run_via",
            run_iteration_pipeline_from_inputs_via_orchestration_fn="run_from_inputs",
            execute_run_iteration_pipeline_from_inputs_via_orchestration_fn=(
                "execute_from_inputs"
            ),
            build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
                "build_for_run"
            ),
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn="run_for_run",
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
                "execute_for_run"
            ),
        )
    )

    assert result == {
        "run_iteration_pipeline_from_inputs_via_orchestration_kwargs": {
            "from_inputs": "kwargs"
        },
        "build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn": "build_via",
        "run_iteration_pipeline_via_orchestration_for_run_fn": "run_via",
        "run_iteration_pipeline_from_inputs_via_orchestration_fn": "run_from_inputs",
        "execute_run_iteration_pipeline_from_inputs_via_orchestration_fn": "execute_from_inputs",
        "build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn": "build_for_run",
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn": "run_for_run",
        "execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn": "execute_for_run",
    }


def test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_impl_delegates_builder_then_runner() -> None:
    calls: dict[str, object] = {}

    def _run_for_run_call_for_run(**kwargs):
        calls["runner_kwargs"] = kwargs
        return {"status": "ok"}

    result = helpers.runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_kwargs={
            "from_inputs": "kwargs"
        },
        build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn="build_via",
        run_iteration_pipeline_via_orchestration_for_run_fn="run_via",
        run_iteration_pipeline_from_inputs_via_orchestration_fn="run_from_inputs",
        execute_run_iteration_pipeline_from_inputs_via_orchestration_fn="execute_from_inputs",
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
            "build_for_run"
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn="run_for_run",
        execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
            "execute_for_run"
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
            "run_for_run_call"
        ),
        execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
            _run_for_run_call_for_run
        ),
    )

    assert calls["runner_kwargs"] == {
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs": {
            "run_iteration_pipeline_from_inputs_via_orchestration_kwargs": {
                "from_inputs": "kwargs"
            },
            "build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn": "build_via",
            "run_iteration_pipeline_via_orchestration_for_run_fn": "run_via",
            "run_iteration_pipeline_from_inputs_via_orchestration_fn": "run_from_inputs",
            "execute_run_iteration_pipeline_from_inputs_via_orchestration_fn": "execute_from_inputs",
            "build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn": "build_for_run",
            "run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn": "run_for_run",
            "execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn": "execute_for_run",
        },
        "build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn": (
            helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl
        ),
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn": "run_for_run_call",
    }
    assert result == {"status": "ok"}


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_call_for_run_impl_delegates_sequence() -> None:
    stub = _OrchestrationHelpersStub()

    result = (
        helpers.buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsCallForRunImpl(
            orchestration_kwargs={"orchestration": "kwargs"},
            iteration_orchestration_helpers=stub,
        )
    )

    assert stub.captured["from_inputs_builder_kwargs"] == {
        "run_iteration_pipeline_orchestration_kwargs": {"orchestration": "kwargs"},
        "build_run_iteration_pipeline_orchestration_kwargs_for_run_fn": (
            stub.buildRunIterationPipelineOrchestrationKwargsForRunImpl
        ),
        "run_iteration_pipeline_orchestration_fn": (
            stub.runIterationPipelineOrchestrationImpl
        ),
        "execute_run_iteration_pipeline_orchestration_for_run_fn": (
            stub.executeRunIterationPipelineOrchestrationForRunImpl
        ),
    }
    assert result == {"from_inputs": "kwargs"}


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"alpha": 1, "beta": "two"}

    result = (
        helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallKwargsImpl(
            **kwargs
        )
    )

    assert result == kwargs
    assert result is not kwargs


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_kwargs_for_run_impl_returns_copy() -> None:
    kwargs = {"alpha": 1, "beta": "two"}

    result = (
        helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallKwargsForRunImpl(
            **kwargs
        )
    )

    assert result == kwargs
    assert result is not kwargs


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_kwargs_impl_returns_copy() -> None:
    kwargs = {"alpha": 1, "beta": "two"}

    result = (
        helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunKwargsImpl(
            **kwargs
        )
    )

    assert result == kwargs
    assert result is not kwargs


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_for_run_kwargs_impl_delegates_wiring() -> None:
    stub = _OrchestrationHelpersStub()

    result = (
        helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallForRunKwargsImpl(
            run_iteration_pipeline_from_inputs_via_orchestration_kwargs={
                "orchestration": "kwargs"
            },
            iteration_orchestration_helpers=stub,
        )
    )

    assert result == {
        "run_iteration_pipeline_from_inputs_via_orchestration_kwargs": {
            "orchestration": "kwargs"
        },
        "build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn": (
            stub.buildRunIterationPipelineViaOrchestrationForRunCallKwargsImpl
        ),
        "run_iteration_pipeline_via_orchestration_for_run_fn": (
            stub.runIterationPipelineViaOrchestrationForRunImpl
        ),
        "run_iteration_pipeline_from_inputs_via_orchestration_fn": (
            stub.runIterationPipelineFromInputsViaOrchestrationImpl
        ),
        "execute_run_iteration_pipeline_from_inputs_via_orchestration_fn": (
            stub.executeRunIterationPipelineFromInputsViaOrchestrationImpl
        ),
        "build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn": (
            stub.buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl
        ),
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn": (
            stub.runIterationPipelineFromInputsViaOrchestrationForRunImpl
        ),
        "execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn": (
            stub.executeRunIterationPipelineFromInputsViaOrchestrationForRunImpl
        ),
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn": (
            stub.runIterationPipelineFromInputsViaOrchestrationForRunCallImpl
        ),
        "execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn": (
            helpers.executeRunIterationPipelineFromInputsViaOrchestrationForRunCallImpl
        ),
    }


def test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_impl_delegates_builder_then_runner() -> None:
    calls: dict[str, object] = {}

    def _builder(**kwargs):
        calls["builder_kwargs"] = kwargs
        return {"mapped": "call"}

    def _runner(**kwargs):
        calls["runner_kwargs"] = kwargs
        return {"status": "ok"}

    result = (
        helpers.runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunImpl(
            build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_kwargs_fn=_builder,
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_kwargs={
                "alpha": 1,
                "beta": "two",
            },
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_fn=_runner,
        )
    )

    assert calls["builder_kwargs"] == {"alpha": 1, "beta": "two"}
    assert calls["runner_kwargs"] == {"mapped": "call"}
    assert result == {"status": "ok"}


def test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_for_run_impl_delegates_builder_then_runner() -> None:
    calls: dict[str, object] = {}

    def _builder(**kwargs):
        calls["builder_kwargs"] = kwargs
        return {"mapped": "for-run-call"}

    def _runner(**kwargs):
        calls["runner_kwargs"] = kwargs
        return {"status": "ok"}

    result = (
        helpers.runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallForRunImpl(
            build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_kwargs_fn=_builder,
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_kwargs={
                "alpha": 1,
                "beta": "two",
            },
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_fn=_runner,
        )
    )

    assert calls["builder_kwargs"] == {"alpha": 1, "beta": "two"}
    assert calls["runner_kwargs"] == {"mapped": "for-run-call"}
    assert result == {"status": "ok"}
