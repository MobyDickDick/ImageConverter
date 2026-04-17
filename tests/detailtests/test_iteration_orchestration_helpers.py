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


def test_run_iteration_pipeline_orchestration_impl_wires_prepare_and_dispatch() -> None:
    captured: dict[str, object] = {}

    def _ensure_conversion_runtime_dependencies_fn(**kwargs):
        captured["dependencies"] = kwargs

    def _build_prepare_run_locals_for_run_call_kwargs_fn(**kwargs):
        captured["prepare_builder_kwargs"] = kwargs
        return {"prepared": "builder-kwargs"}

    def _prepare_run_locals_for_run_fn(**kwargs):
        captured["prepare_run_kwargs"] = kwargs
        return {"run_locals": "prepared"}

    def _build_run_iteration_pipeline_for_run_call_kwargs_fn(**kwargs):
        captured["dispatch_builder_kwargs"] = kwargs
        return {"dispatch": "builder-kwargs"}

    def _run_iteration_pipeline_for_run_fn(**kwargs):
        captured["dispatch_run_kwargs"] = kwargs
        return {"status": "ok"}

    result = helpers.runIterationPipelineOrchestrationImpl(
        img_path="img.jpg",
        csv_path="meta.csv",
        max_iterations=12,
        svg_out_dir="svg-out",
        diff_out_dir="diff-out",
        reports_out_dir="reports",
        debug_ac0811_dir="ac0811-debug",
        debug_element_diff_dir="element-debug",
        badge_validation_rounds=7,
        ensure_conversion_runtime_dependencies_fn=_ensure_conversion_runtime_dependencies_fn,
        cv2_module="cv2",
        np_module="np",
        fitz_module="fitz",
        prepare_run_locals_for_run_fn=_prepare_run_locals_for_run_fn,
        build_prepare_run_locals_for_run_call_kwargs_fn=_build_prepare_run_locals_for_run_call_kwargs_fn,
        build_run_iteration_pipeline_for_run_call_kwargs_fn=_build_run_iteration_pipeline_for_run_call_kwargs_fn,
        run_iteration_pipeline_for_run_fn=_run_iteration_pipeline_for_run_fn,
        run_seed=11,
        pass_seed_offset=22,
        action_cls="Action",
        perception_cls="Perception",
        reflection_cls="Reflection",
        get_base_name_from_file_fn="get_base_name",
        semantic_audit_record_fn="semantic_audit_record",
        semantic_quality_flags_fn="semantic_quality_flags",
        looks_like_elongated_foreground_rect_fn="looks_like_rect",
        render_embedded_raster_svg_fn="render_raster",
        print_fn="print",
        time_ns_fn="time_ns",
        calculate_error_fn="calculate_error",
        build_prepared_mode_builder_kwargs_fn="build_prepared_mode_builder_kwargs",
        run_prepared_iteration_and_finalize_fn="run_prepared_iteration_and_finalize",
        build_prepared_iteration_mode_kwargs_fn="build_prepared_iteration_mode_kwargs",
        run_prepared_iteration_mode_fn="run_prepared_iteration_mode",
        finalize_iteration_result_fn="finalize_iteration_result",
        math_module="math",
        iteration_run_preparation_helpers="iteration_run_preparation_helpers",
        iteration_bindings_helpers="iteration_bindings_helpers",
        iteration_initialization_helpers="iteration_initialization_helpers",
        iteration_setup_helpers="iteration_setup_helpers",
        iteration_runtime_helpers="iteration_runtime_helpers",
        iteration_mode_runtime_preparation_helpers="iteration_mode_runtime_preparation_helpers",
        iteration_mode_setup_helpers="iteration_mode_setup_helpers",
        iteration_mode_preparation_helpers="iteration_mode_preparation_helpers",
        iteration_mode_dependency_setup_helpers="iteration_mode_dependency_setup_helpers",
        iteration_mode_dependency_helpers="iteration_mode_dependency_helpers",
        iteration_mode_runtime_helpers="iteration_mode_runtime_helpers",
        iteration_orchestration_helpers="iteration_orchestration_helpers",
        iteration_context_helpers="iteration_context_helpers",
        iteration_preparation_helpers="iteration_preparation_helpers",
        gradient_stripe_strategy_helpers="gradient_stripe_strategy_helpers",
        semantic_audit_bootstrap_helpers="semantic_audit_bootstrap_helpers",
        semantic_audit_logging_helpers="semantic_audit_logging_helpers",
        semantic_audit_runtime_helpers="semantic_audit_runtime_helpers",
        semantic_mismatch_reporting_helpers="semantic_mismatch_reporting_helpers",
        semantic_validation_logging_helpers="semantic_validation_logging_helpers",
        semantic_mismatch_runtime_helpers="semantic_mismatch_runtime_helpers",
        semantic_validation_context_helpers="semantic_validation_context_helpers",
        semantic_validation_runtime_helpers="semantic_validation_runtime_helpers",
        semantic_post_validation_helpers="semantic_post_validation_helpers",
        semantic_validation_finalization_helpers="semantic_validation_finalization_helpers",
        semantic_iteration_finalization_helpers="semantic_iteration_finalization_helpers",
        semantic_ac0223_runtime_helpers="semantic_ac0223_runtime_helpers",
        semantic_visual_override_helpers="semantic_visual_override_helpers",
        non_composite_runtime_helpers="non_composite_runtime_helpers",
        conversion_composite_helpers="conversion_composite_helpers",
        semantic_badge_runtime_helpers="semantic_badge_runtime_helpers",
        dual_arrow_badge_helpers="dual_arrow_badge_helpers",
        dual_arrow_runtime_helpers="dual_arrow_runtime_helpers",
    )

    assert captured["dependencies"] == {
        "cv2_module": "cv2",
        "np_module": "np",
        "fitz_module": "fitz",
    }
    assert captured["prepare_run_kwargs"] == {"prepared": "builder-kwargs"}
    assert captured["dispatch_builder_kwargs"]["run_locals"] == {"run_locals": "prepared"}
    assert captured["dispatch_run_kwargs"] == {"dispatch": "builder-kwargs"}
    assert result == {"status": "ok"}


def test_build_prepare_run_locals_for_run_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"img_path": "img.jpg", "run_seed": 7}

    result = helpers.buildPrepareRunLocalsForRunCallKwargsImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_build_run_iteration_pipeline_orchestration_kwargs_for_run_impl_returns_copy() -> None:
    kwargs = {"img_path": "img.jpg", "max_iterations": 7}

    result = helpers.buildRunIterationPipelineOrchestrationKwargsForRunImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_build_ensure_conversion_runtime_dependencies_kwargs_impl_returns_copy() -> None:
    kwargs = {"cv2_module": "cv2", "np_module": "np", "fitz_module": "fitz"}

    result = helpers.buildEnsureConversionRuntimeDependenciesKwargsImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_build_run_iteration_pipeline_dispatch_kwargs_impl_returns_copy() -> None:
    kwargs = {"img_path": "img.jpg", "max_iterations": 5}

    result = helpers.buildRunIterationPipelineDispatchKwargsImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_execute_ensure_conversion_runtime_dependencies_impl_delegates_runner() -> None:
    captured: dict[str, object] = {}

    def _ensure_conversion_runtime_dependencies_fn(**kwargs):
        captured["kwargs"] = kwargs

    helpers.executeEnsureConversionRuntimeDependenciesImpl(
        ensure_dependency_kwargs={"cv2_module": "cv2", "np_module": "np", "fitz_module": "fitz"},
        ensure_conversion_runtime_dependencies_fn=_ensure_conversion_runtime_dependencies_fn,
    )

    assert captured["kwargs"] == {"cv2_module": "cv2", "np_module": "np", "fitz_module": "fitz"}


def test_execute_run_iteration_pipeline_dispatch_impl_delegates_builder_then_runner() -> None:
    captured: dict[str, object] = {}

    def _build_run_iteration_pipeline_for_run_call_kwargs_fn(**kwargs):
        captured["builder_kwargs"] = kwargs
        return {"dispatch": "kwargs"}

    def _run_iteration_pipeline_for_run_fn(**kwargs):
        captured["runner_kwargs"] = kwargs
        return {"result": "ok"}

    result = helpers.executeRunIterationPipelineDispatchImpl(
        run_iteration_dispatch_kwargs={"run_locals": "prepared", "max_iterations": 6},
        build_run_iteration_pipeline_for_run_call_kwargs_fn=_build_run_iteration_pipeline_for_run_call_kwargs_fn,
        run_iteration_pipeline_for_run_fn=_run_iteration_pipeline_for_run_fn,
    )

    assert captured["builder_kwargs"] == {"run_locals": "prepared", "max_iterations": 6}
    assert captured["runner_kwargs"] == {"dispatch": "kwargs"}
    assert result == {"result": "ok"}


def test_execute_prepare_run_locals_for_run_impl_delegates_builder_then_runner() -> None:
    captured: dict[str, object] = {}

    def _build_prepare_run_locals_for_run_call_kwargs_fn(**kwargs):
        captured["builder_kwargs"] = kwargs
        return {"prepared": "kwargs"}

    def _prepare_run_locals_for_run_fn(**kwargs):
        captured["runner_kwargs"] = kwargs
        return {"run_locals": "prepared"}

    result = helpers.executePrepareRunLocalsForRunImpl(
        prepare_run_locals_call_kwargs={"img_path": "img.jpg", "run_seed": 7},
        build_prepare_run_locals_for_run_call_kwargs_fn=_build_prepare_run_locals_for_run_call_kwargs_fn,
        prepare_run_locals_for_run_fn=_prepare_run_locals_for_run_fn,
    )

    assert captured["builder_kwargs"] == {"img_path": "img.jpg", "run_seed": 7}
    assert captured["runner_kwargs"] == {"prepared": "kwargs"}
    assert result == {"run_locals": "prepared"}


def test_execute_run_iteration_pipeline_orchestration_for_run_impl_delegates_builder_then_runner() -> None:
    captured: dict[str, object] = {}

    def _build_run_iteration_pipeline_orchestration_kwargs_for_run_fn(**kwargs):
        captured["builder_kwargs"] = kwargs
        return {"orchestration": "kwargs"}

    def _run_iteration_pipeline_orchestration_fn(**kwargs):
        captured["runner_kwargs"] = kwargs
        return {"result": "ok"}

    result = helpers.executeRunIterationPipelineOrchestrationForRunImpl(
        run_iteration_pipeline_orchestration_kwargs={"img_path": "img.jpg", "max_iterations": 7},
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
            _build_run_iteration_pipeline_orchestration_kwargs_for_run_fn
        ),
        run_iteration_pipeline_orchestration_fn=_run_iteration_pipeline_orchestration_fn,
    )

    assert captured["builder_kwargs"] == {"img_path": "img.jpg", "max_iterations": 7}
    assert captured["runner_kwargs"] == {"orchestration": "kwargs"}
    assert result == {"result": "ok"}


def test_run_iteration_pipeline_via_orchestration_for_run_impl_delegates_executor() -> None:
    captured: dict[str, object] = {}

    def _execute_run_iteration_pipeline_orchestration_for_run_fn(**kwargs):
        captured["executor_kwargs"] = kwargs
        return {"status": "ok"}

    result = helpers.runIterationPipelineViaOrchestrationForRunImpl(
        run_iteration_pipeline_orchestration_kwargs={"img_path": "img.jpg"},
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn="builder",
        run_iteration_pipeline_orchestration_fn="runner",
        execute_run_iteration_pipeline_orchestration_for_run_fn=(
            _execute_run_iteration_pipeline_orchestration_for_run_fn
        ),
    )

    assert captured["executor_kwargs"] == {
        "run_iteration_pipeline_orchestration_kwargs": {"img_path": "img.jpg"},
        "build_run_iteration_pipeline_orchestration_kwargs_for_run_fn": "builder",
        "run_iteration_pipeline_orchestration_fn": "runner",
    }
    assert result == {"status": "ok"}


def test_build_run_iteration_pipeline_via_orchestration_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"run_iteration_pipeline_orchestration_kwargs": {"img_path": "img.jpg"}}

    result = helpers.buildRunIterationPipelineViaOrchestrationCallKwargsImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_execute_run_iteration_pipeline_via_orchestration_impl_delegates_executor() -> None:
    captured: dict[str, object] = {}

    def _execute_run_iteration_pipeline_orchestration_for_run_fn(**kwargs):
        captured["executor_kwargs"] = kwargs
        return {"status": "ok"}

    result = helpers.executeRunIterationPipelineViaOrchestrationImpl(
        run_iteration_pipeline_via_orchestration_call_kwargs={"mapped": "kwargs"},
        execute_run_iteration_pipeline_orchestration_for_run_fn=(
            _execute_run_iteration_pipeline_orchestration_for_run_fn
        ),
    )

    assert captured["executor_kwargs"] == {"mapped": "kwargs"}
    assert result == {"status": "ok"}


def test_build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"run_iteration_pipeline_orchestration_kwargs": {"img_path": "img.jpg"}}

    result = helpers.buildRunIterationPipelineViaOrchestrationForRunCallKwargsImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_impl_returns_copy() -> None:
    kwargs = {"run_iteration_pipeline_orchestration_kwargs": {"img_path": "img.jpg"}}

    result = helpers.buildRunIterationPipelineFromInputsViaOrchestrationKwargsImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_run_iteration_pipeline_from_inputs_via_orchestration_impl_delegates_builder_then_runner() -> None:
    captured: dict[str, object] = {}

    def _build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn(**kwargs):
        captured["builder_kwargs"] = kwargs
        return {"via_orchestration": "kwargs"}

    def _run_iteration_pipeline_via_orchestration_for_run_fn(**kwargs):
        captured["runner_kwargs"] = kwargs
        return {"status": "ok"}

    result = helpers.runIterationPipelineFromInputsViaOrchestrationImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_kwargs={"img_path": "img.jpg"},
        build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn=(
            _build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn
        ),
        run_iteration_pipeline_via_orchestration_for_run_fn=(
            _run_iteration_pipeline_via_orchestration_for_run_fn
        ),
    )

    assert captured["builder_kwargs"] == {"img_path": "img.jpg"}
    assert captured["runner_kwargs"] == {"via_orchestration": "kwargs"}
    assert result == {"status": "ok"}


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"run_iteration_pipeline_from_inputs_via_orchestration_kwargs": {"img_path": "img.jpg"}}

    result = helpers.buildRunIterationPipelineFromInputsViaOrchestrationCallKwargsImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_execute_run_iteration_pipeline_from_inputs_via_orchestration_impl_delegates_runner() -> None:
    captured: dict[str, object] = {}

    def _run_iteration_pipeline_from_inputs_via_orchestration_fn(**kwargs):
        captured["runner_kwargs"] = kwargs
        return {"status": "ok"}

    result = helpers.executeRunIterationPipelineFromInputsViaOrchestrationImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs={"mapped": "kwargs"},
        run_iteration_pipeline_from_inputs_via_orchestration_fn=(
            _run_iteration_pipeline_from_inputs_via_orchestration_fn
        ),
    )

    assert captured["runner_kwargs"] == {"mapped": "kwargs"}
    assert result == {"status": "ok"}


def test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_impl_delegates_executor() -> None:
    captured: dict[str, object] = {}

    def _execute_run_iteration_pipeline_from_inputs_via_orchestration_fn(**kwargs):
        captured["executor_kwargs"] = kwargs
        return {"status": "ok"}

    result = helpers.runIterationPipelineFromInputsViaOrchestrationForRunImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_kwargs={"img_path": "img.jpg"},
        build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn="builder",
        run_iteration_pipeline_via_orchestration_for_run_fn="runner",
        run_iteration_pipeline_from_inputs_via_orchestration_fn="from_inputs_runner",
        execute_run_iteration_pipeline_from_inputs_via_orchestration_fn=(
            _execute_run_iteration_pipeline_from_inputs_via_orchestration_fn
        ),
    )

    assert captured["executor_kwargs"] == {
        "run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs": {
            "run_iteration_pipeline_from_inputs_via_orchestration_kwargs": {"img_path": "img.jpg"},
            "build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn": "builder",
            "run_iteration_pipeline_via_orchestration_for_run_fn": "runner",
        },
        "run_iteration_pipeline_from_inputs_via_orchestration_fn": "from_inputs_runner",
    }
    assert result == {"status": "ok"}


def test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_impl_returns_copy() -> None:
    kwargs = {"run_iteration_pipeline_from_inputs_via_orchestration_kwargs": {"img_path": "img.jpg"}}

    result = helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl(**kwargs)

    assert result == kwargs
    assert result is not kwargs


def test_execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_impl_delegates_runner() -> None:
    captured: dict[str, object] = {}

    def _run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn(**kwargs):
        captured["runner_kwargs"] = kwargs
        return {"status": "ok"}

    result = helpers.executeRunIterationPipelineFromInputsViaOrchestrationForRunImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs={"mapped": "kwargs"},
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
            _run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn
        ),
    )

    assert captured["runner_kwargs"] == {"mapped": "kwargs"}
    assert result == {"status": "ok"}


def test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_impl_delegates_builder_then_executor() -> None:
    captured: dict[str, object] = {}

    def _build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn(**kwargs):
        captured["builder_kwargs"] = kwargs
        return {"for_run": "call_kwargs"}

    def _execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn(**kwargs):
        captured["executor_kwargs"] = kwargs
        return {"status": "ok"}

    result = helpers.runIterationPipelineFromInputsViaOrchestrationForRunCallImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_kwargs={"img_path": "img.jpg"},
        build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn="via_builder",
        run_iteration_pipeline_via_orchestration_for_run_fn="via_runner",
        run_iteration_pipeline_from_inputs_via_orchestration_fn="from_inputs_runner",
        execute_run_iteration_pipeline_from_inputs_via_orchestration_fn="from_inputs_executor",
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
            _build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn="for_run_runner",
        execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
            _execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn
        ),
    )

    assert captured["builder_kwargs"] == {
        "run_iteration_pipeline_from_inputs_via_orchestration_kwargs": {"img_path": "img.jpg"},
        "build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn": "via_builder",
        "run_iteration_pipeline_via_orchestration_for_run_fn": "via_runner",
        "run_iteration_pipeline_from_inputs_via_orchestration_fn": "from_inputs_runner",
        "execute_run_iteration_pipeline_from_inputs_via_orchestration_fn": "from_inputs_executor",
    }
    assert captured["executor_kwargs"] == {
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs": {
            "for_run": "call_kwargs"
        },
        "run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn": "for_run_runner",
    }
    assert result == {"status": "ok"}
