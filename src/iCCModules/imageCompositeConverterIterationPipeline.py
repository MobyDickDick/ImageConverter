from __future__ import annotations


def buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl(
    **kwargs,
) -> dict[str, object]:
    """Return the input mapping for the top-level from-inputs orchestration run call."""

    return dict(kwargs)


def buildRunIterationPipelineOrchestrationKwargsForRunCallKwargsImpl(
    **kwargs,
) -> dict[str, object]:
    """Return the input mapping for the top-level orchestration kwargs builder call."""

    return dict(kwargs)


def buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunCallKwargsImpl(
    **kwargs,
) -> dict[str, object]:
    """Return the input mapping for the from-inputs orchestration kwargs builder call."""

    return dict(kwargs)


def buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsForRunImpl(
    **kwargs,
) -> dict[str, object]:
    """Return the input mapping for the top-level from-inputs orchestration call wrapper."""

    return dict(kwargs)


def buildRunIterationPipelineOrchestrationCallKwargsImpl(
    **kwargs,
) -> dict[str, object]:
    """Return the input mapping for the top-level orchestration builder invocation."""

    return dict(kwargs)


def buildRunIterationPipelineFromInputsViaOrchestrationCallKwargsImpl(
    **kwargs,
) -> dict[str, object]:
    """Return the input mapping for the top-level from-inputs orchestration builder invocation."""

    return dict(kwargs)


def executeBuildRunIterationPipelineOrchestrationKwargsForRunImpl(
    *,
    run_iteration_pipeline_orchestration_call_kwargs: dict[str, object],
    build_run_iteration_pipeline_orchestration_kwargs_for_run_fn,
):
    """Build orchestration kwargs for the top-level run via delegated builder."""

    return build_run_iteration_pipeline_orchestration_kwargs_for_run_fn(
        **run_iteration_pipeline_orchestration_call_kwargs
    )


def executeRunIterationPipelineFromInputsViaOrchestrationKwargsBuilderForRunImpl(
    *,
    run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs: dict[str, object],
    build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_fn,
):
    """Build from-inputs orchestration kwargs for the top-level run via delegated builder."""

    return build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_fn(
        **run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs
    )


def runIterationPipelineOrchestrationKwargsForRunImpl(
    *,
    run_iteration_pipeline_orchestration_call_kwargs: dict[str, object],
    build_run_iteration_pipeline_orchestration_kwargs_for_run_fn,
    execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn,
):
    """Build top-level orchestration kwargs via delegated executor."""

    return execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn(
        run_iteration_pipeline_orchestration_call_kwargs=(
            run_iteration_pipeline_orchestration_call_kwargs
        ),
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
            build_run_iteration_pipeline_orchestration_kwargs_for_run_fn
        ),
    )


def runIterationPipelineOrchestrationKwargsForRunCallImpl(
    *,
    build_run_iteration_pipeline_orchestration_call_kwargs_fn,
    run_iteration_pipeline_orchestration_call_kwargs: dict[str, object],
    build_run_iteration_pipeline_orchestration_kwargs_for_run_fn,
    execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn,
):
    """Build and execute top-level orchestration kwargs resolution for the run entrypoint."""

    orchestration_call_kwargs = (
        build_run_iteration_pipeline_orchestration_call_kwargs_fn(
            **run_iteration_pipeline_orchestration_call_kwargs
        )
    )
    return runIterationPipelineOrchestrationKwargsForRunImpl(
        run_iteration_pipeline_orchestration_call_kwargs=orchestration_call_kwargs,
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
            build_run_iteration_pipeline_orchestration_kwargs_for_run_fn
        ),
        execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
            execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn
        ),
    )


def buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunImpl(
    *,
    run_iteration_pipeline_orchestration_kwargs: dict[str, object],
    build_run_iteration_pipeline_orchestration_kwargs_for_run_fn,
    run_iteration_pipeline_orchestration_fn,
    execute_run_iteration_pipeline_orchestration_for_run_fn,
    build_run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_builder_for_run_fn,
    build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_fn,
):
    """Build from-inputs orchestration kwargs for the top-level run via delegated mapping/execution helpers."""

    from_inputs_call_kwargs = (
        build_run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs_fn(
            run_iteration_pipeline_orchestration_kwargs=(
                run_iteration_pipeline_orchestration_kwargs
            ),
            build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
                build_run_iteration_pipeline_orchestration_kwargs_for_run_fn
            ),
            run_iteration_pipeline_orchestration_fn=(
                run_iteration_pipeline_orchestration_fn
            ),
            execute_run_iteration_pipeline_orchestration_for_run_fn=(
                execute_run_iteration_pipeline_orchestration_for_run_fn
            ),
        )
    )

    from_inputs_builder_call_kwargs = (
        buildRunIterationPipelineFromInputsViaOrchestrationCallKwargsImpl(
            run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs=from_inputs_call_kwargs,
            build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_fn=(
                build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_fn
            ),
        )
    )
    return execute_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_builder_for_run_fn(
        **from_inputs_builder_call_kwargs
    )




def buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsKwargsImpl(
    **kwargs,
) -> dict[str, object]:
    """Return the input mapping for the top-level from-inputs orchestration kwargs sequence."""

    return dict(kwargs)


def runIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsImpl(
    *,
    build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs: dict[
        str, object
    ],
    build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_fn,
):
    """Build and execute the top-level from-inputs orchestration kwargs sequence."""

    call_kwargs = (
        build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs_fn(
            **run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs
        )
    )
    return build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_fn(
        **call_kwargs
    )

def executeRunIterationPipelineFromInputsViaOrchestrationForRunCallImpl(
    *,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs: dict[str, object],
    build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn,
):
    """Build and execute the top-level from-inputs orchestration run call."""

    return run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn(
        **build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn(
            **run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs
        )
    )


def runIterationPipelineFromInputsViaOrchestrationForRunCallForRunImpl(
    *,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs: dict[str, object],
    build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn,
):
    """Execute the top-level from-inputs orchestration call via a delegated executor."""

    return execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn(
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs=(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs
        ),
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
            build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn
        ),
    )


def runIterationPipelineFromInputsViaOrchestrationForRunCallForRunKwargsImpl(
    *,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs: dict[
        str, object
    ],
    build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn,
):
    """Build top-level from-inputs for-run call kwargs for delegated execution."""

    return buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsForRunImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs=(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs
        ),
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
            build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn
        ),
        execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn
        ),
    )


def buildRunIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallKwargsImpl(
    **kwargs,
) -> dict[str, object]:
    """Return the input mapping for the top-level from-inputs for-run call sequence."""

    return dict(kwargs)


def buildRunIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallKwargsForRunImpl(
    *,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs: dict[
        str, object
    ],
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn,
) -> dict[str, object]:
    """Build the top-level from-inputs for-run call mapping for delegated execution."""

    return buildRunIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallKwargsImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs=(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs
        ),
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
            buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn
        ),
        execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn
        ),
    )


def runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallImpl(
    *,
    build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_kwargs_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_kwargs: dict[
        str, object
    ],
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_fn,
):
    """Build and execute the top-level from-inputs for-run call sequence."""

    call_kwargs = (
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_kwargs_fn(
            **run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_kwargs
        )
    )
    return run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_fn(
        **call_kwargs
    )


def runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallForRunImpl(
    *,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs: dict[
        str, object
    ],
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn,
):
    """Build and execute the top-level from-inputs for-run call sequence via delegated helpers."""

    run_for_run_call_kwargs = (
        buildRunIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallKwargsForRunImpl(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs=(
                run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs
            ),
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
                run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn
            ),
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
                execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn
            ),
        )
    )

    return runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallImpl(
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_kwargs_fn=(
            buildRunIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallKwargsImpl
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_kwargs=(
            run_for_run_call_kwargs
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_fn=(
            runIterationPipelineFromInputsViaOrchestrationForRunCallForRunImpl
        ),
    )


def runIterationPipelineFromInputsViaOrchestrationKwargsForRunCallImpl(
    *,
    run_iteration_pipeline_from_inputs_via_orchestration_kwargs: dict[str, object],
    build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn,
    run_iteration_pipeline_via_orchestration_for_run_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_fn,
    build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn,
):
    """Build top-level from-inputs orchestration run-call kwargs."""

    return buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_kwargs=(
            run_iteration_pipeline_from_inputs_via_orchestration_kwargs
        ),
        build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn=(
            build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn
        ),
        run_iteration_pipeline_via_orchestration_for_run_fn=(
            run_iteration_pipeline_via_orchestration_for_run_fn
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_fn=(
            run_iteration_pipeline_from_inputs_via_orchestration_fn
        ),
        execute_run_iteration_pipeline_from_inputs_via_orchestration_fn=(
            execute_run_iteration_pipeline_from_inputs_via_orchestration_fn
        ),
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
            build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn
        ),
        execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn
        ),
    )


def buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallKwargsImpl(
    *,
    run_iteration_pipeline_from_inputs_via_orchestration_kwargs: dict[str, object],
    build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn,
    run_iteration_pipeline_via_orchestration_for_run_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_fn,
    build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn,
):
    """Build top-level from-inputs run-call kwargs via delegated helper wiring."""

    return runIterationPipelineFromInputsViaOrchestrationKwargsForRunCallImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_kwargs=(
            run_iteration_pipeline_from_inputs_via_orchestration_kwargs
        ),
        build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn=(
            build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn
        ),
        run_iteration_pipeline_via_orchestration_for_run_fn=(
            run_iteration_pipeline_via_orchestration_for_run_fn
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_fn=(
            run_iteration_pipeline_from_inputs_via_orchestration_fn
        ),
        execute_run_iteration_pipeline_from_inputs_via_orchestration_fn=(
            execute_run_iteration_pipeline_from_inputs_via_orchestration_fn
        ),
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
            build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn
        ),
        execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn
        ),
    )


def runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl(
    *,
    run_iteration_pipeline_from_inputs_via_orchestration_kwargs: dict[str, object],
    build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn,
    run_iteration_pipeline_via_orchestration_for_run_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_fn,
    build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn,
    run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn,
    execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn,
):
    """Run top-level from-inputs call by building run-call kwargs and dispatching the runner."""

    run_call_kwargs = (
        buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallKwargsImpl(
            run_iteration_pipeline_from_inputs_via_orchestration_kwargs=(
                run_iteration_pipeline_from_inputs_via_orchestration_kwargs
            ),
            build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn=(
                build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn
            ),
            run_iteration_pipeline_via_orchestration_for_run_fn=(
                run_iteration_pipeline_via_orchestration_for_run_fn
            ),
            run_iteration_pipeline_from_inputs_via_orchestration_fn=(
                run_iteration_pipeline_from_inputs_via_orchestration_fn
            ),
            execute_run_iteration_pipeline_from_inputs_via_orchestration_fn=(
                execute_run_iteration_pipeline_from_inputs_via_orchestration_fn
            ),
            build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
                build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn
            ),
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
                run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn
            ),
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
                execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn
            ),
        )
    )

    return runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallForRunImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs=(
            run_call_kwargs
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
            run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn
        ),
        execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
            execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn
        ),
    )


def buildRunIterationPipelineOrchestrationKwargsForRunFromInputsImpl(
    *,
    img_path: str,
    csv_path: str,
    max_iterations: int,
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str | None,
    debug_ac0811_dir: str | None,
    debug_element_diff_dir: str | None,
    badge_validation_rounds: int,
    ensure_conversion_runtime_dependencies_fn,
    cv2_module,
    np_module,
    fitz_module,
    iteration_run_preparation_helpers,
    iteration_execution_context_helpers,
    run_seed: int,
    pass_seed_offset: int,
    action_cls,
    perception_cls,
    reflection_cls,
    get_base_name_from_file_fn,
    semantic_audit_record_fn,
    semantic_quality_flags_fn,
    looks_like_elongated_foreground_rect_fn,
    render_embedded_raster_svg_fn,
    print_fn,
    time_ns_fn,
    calculate_error_fn,
    iteration_execution_helpers,
    iteration_context_helpers,
    iteration_dispatch_helpers,
    iteration_finalization_helpers,
    math_module,
    iteration_bindings_helpers,
    iteration_initialization_helpers,
    iteration_setup_helpers,
    iteration_runtime_helpers,
    iteration_mode_runtime_preparation_helpers,
    iteration_mode_setup_helpers,
    iteration_mode_preparation_helpers,
    iteration_mode_dependency_setup_helpers,
    iteration_mode_dependency_helpers,
    iteration_mode_runtime_helpers,
    iteration_orchestration_helpers,
    iteration_preparation_helpers,
    gradient_stripe_strategy_helpers,
    semantic_audit_bootstrap_helpers,
    semantic_audit_logging_helpers,
    semantic_audit_runtime_helpers,
    semantic_mismatch_reporting_helpers,
    semantic_validation_logging_helpers,
    semantic_mismatch_runtime_helpers,
    semantic_validation_context_helpers,
    semantic_validation_runtime_helpers,
    semantic_post_validation_helpers,
    semantic_validation_finalization_helpers,
    semantic_iteration_finalization_helpers,
    semantic_ac0223_runtime_helpers,
    semantic_visual_override_helpers,
    non_composite_runtime_helpers,
    conversion_composite_helpers,
    semantic_badge_runtime_helpers,
    dual_arrow_badge_helpers,
    dual_arrow_runtime_helpers,
    build_run_iteration_pipeline_orchestration_call_kwargs_fn,
    build_run_iteration_pipeline_orchestration_kwargs_for_run_fn,
    execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn,
):
    """Build top-level orchestration kwargs from the run inputs via delegated mapping/execution helpers."""

    return runIterationPipelineOrchestrationKwargsForRunCallImpl(
        build_run_iteration_pipeline_orchestration_call_kwargs_fn=(
            build_run_iteration_pipeline_orchestration_call_kwargs_fn
        ),
        run_iteration_pipeline_orchestration_call_kwargs={
            "img_path": img_path,
            "csv_path": csv_path,
            "max_iterations": max_iterations,
            "svg_out_dir": svg_out_dir,
            "diff_out_dir": diff_out_dir,
            "reports_out_dir": reports_out_dir,
            "debug_ac0811_dir": debug_ac0811_dir,
            "debug_element_diff_dir": debug_element_diff_dir,
            "badge_validation_rounds": badge_validation_rounds,
            "ensure_conversion_runtime_dependencies_fn": ensure_conversion_runtime_dependencies_fn,
            "cv2_module": cv2_module,
            "np_module": np_module,
            "fitz_module": fitz_module,
            "prepare_run_locals_for_run_fn": (
                iteration_run_preparation_helpers.prepareRunIterationPipelineLocalsForRunImpl
            ),
            "build_prepare_run_locals_for_run_call_kwargs_fn": (
                iteration_run_preparation_helpers.buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl
            ),
            "build_run_iteration_pipeline_for_run_call_kwargs_fn": (
                iteration_execution_context_helpers.buildRunIterationPipelineForRunCallKwargsImpl
            ),
            "run_iteration_pipeline_for_run_fn": (
                iteration_execution_context_helpers.runIterationPipelineForRunImpl
            ),
            "run_seed": run_seed,
            "pass_seed_offset": pass_seed_offset,
            "action_cls": action_cls,
            "perception_cls": perception_cls,
            "reflection_cls": reflection_cls,
            "get_base_name_from_file_fn": get_base_name_from_file_fn,
            "semantic_audit_record_fn": semantic_audit_record_fn,
            "semantic_quality_flags_fn": semantic_quality_flags_fn,
            "looks_like_elongated_foreground_rect_fn": (
                looks_like_elongated_foreground_rect_fn
            ),
            "render_embedded_raster_svg_fn": render_embedded_raster_svg_fn,
            "print_fn": print_fn,
            "time_ns_fn": time_ns_fn,
            "calculate_error_fn": calculate_error_fn,
            "build_prepared_mode_builder_kwargs_fn": (
                iteration_execution_helpers.buildPreparedModeBuilderKwargsImpl
            ),
            "run_prepared_iteration_and_finalize_fn": (
                iteration_execution_helpers.runPreparedIterationAndFinalizeImpl
            ),
            "build_prepared_iteration_mode_kwargs_fn": (
                iteration_context_helpers.buildPreparedIterationModeKwargsImpl
            ),
            "run_prepared_iteration_mode_fn": (
                iteration_dispatch_helpers.runPreparedIterationModeImpl
            ),
            "finalize_iteration_result_fn": (
                iteration_finalization_helpers.finalizeIterationResultImpl
            ),
            "math_module": math_module,
            "iteration_run_preparation_helpers": iteration_run_preparation_helpers,
            "iteration_bindings_helpers": iteration_bindings_helpers,
            "iteration_initialization_helpers": iteration_initialization_helpers,
            "iteration_setup_helpers": iteration_setup_helpers,
            "iteration_runtime_helpers": iteration_runtime_helpers,
            "iteration_mode_runtime_preparation_helpers": (
                iteration_mode_runtime_preparation_helpers
            ),
            "iteration_mode_setup_helpers": iteration_mode_setup_helpers,
            "iteration_mode_preparation_helpers": iteration_mode_preparation_helpers,
            "iteration_mode_dependency_setup_helpers": (
                iteration_mode_dependency_setup_helpers
            ),
            "iteration_mode_dependency_helpers": iteration_mode_dependency_helpers,
            "iteration_mode_runtime_helpers": iteration_mode_runtime_helpers,
            "iteration_orchestration_helpers": iteration_orchestration_helpers,
            "iteration_context_helpers": iteration_context_helpers,
            "iteration_preparation_helpers": iteration_preparation_helpers,
            "gradient_stripe_strategy_helpers": gradient_stripe_strategy_helpers,
            "semantic_audit_bootstrap_helpers": semantic_audit_bootstrap_helpers,
            "semantic_audit_logging_helpers": semantic_audit_logging_helpers,
            "semantic_audit_runtime_helpers": semantic_audit_runtime_helpers,
            "semantic_mismatch_reporting_helpers": semantic_mismatch_reporting_helpers,
            "semantic_validation_logging_helpers": (
                semantic_validation_logging_helpers
            ),
            "semantic_mismatch_runtime_helpers": semantic_mismatch_runtime_helpers,
            "semantic_validation_context_helpers": (
                semantic_validation_context_helpers
            ),
            "semantic_validation_runtime_helpers": semantic_validation_runtime_helpers,
            "semantic_post_validation_helpers": semantic_post_validation_helpers,
            "semantic_validation_finalization_helpers": (
                semantic_validation_finalization_helpers
            ),
            "semantic_iteration_finalization_helpers": (
                semantic_iteration_finalization_helpers
            ),
            "semantic_ac0223_runtime_helpers": semantic_ac0223_runtime_helpers,
            "semantic_visual_override_helpers": semantic_visual_override_helpers,
            "non_composite_runtime_helpers": non_composite_runtime_helpers,
            "conversion_composite_helpers": conversion_composite_helpers,
            "semantic_badge_runtime_helpers": semantic_badge_runtime_helpers,
            "dual_arrow_badge_helpers": dual_arrow_badge_helpers,
            "dual_arrow_runtime_helpers": dual_arrow_runtime_helpers,
        },
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
            build_run_iteration_pipeline_orchestration_kwargs_for_run_fn
        ),
        execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
            execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn
        ),
    )


def runIterationPipelineImpl(
    *,
    img_path: str,
    csv_path: str,
    max_iterations: int,
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str | None,
    debug_ac0811_dir: str | None,
    debug_element_diff_dir: str | None,
    badge_validation_rounds: int,
    iteration_orchestration_helpers,
    iteration_run_preparation_helpers,
    iteration_execution_context_helpers,
    iteration_execution_helpers,
    iteration_context_helpers,
    iteration_dispatch_helpers,
    iteration_finalization_helpers,
    iteration_bindings_helpers,
    iteration_initialization_helpers,
    iteration_setup_helpers,
    iteration_runtime_helpers,
    iteration_mode_runtime_preparation_helpers,
    iteration_mode_setup_helpers,
    iteration_mode_preparation_helpers,
    iteration_mode_dependency_setup_helpers,
    iteration_mode_dependency_helpers,
    iteration_mode_runtime_helpers,
    iteration_preparation_helpers,
    gradient_stripe_strategy_helpers,
    semantic_audit_bootstrap_helpers,
    semantic_audit_logging_helpers,
    semantic_audit_runtime_helpers,
    semantic_mismatch_reporting_helpers,
    semantic_validation_logging_helpers,
    semantic_mismatch_runtime_helpers,
    semantic_validation_context_helpers,
    semantic_validation_runtime_helpers,
    semantic_post_validation_helpers,
    semantic_validation_finalization_helpers,
    semantic_iteration_finalization_helpers,
    semantic_ac0223_runtime_helpers,
    semantic_visual_override_helpers,
    non_composite_runtime_helpers,
    conversion_composite_helpers,
    semantic_badge_runtime_helpers,
    dual_arrow_badge_helpers,
    dual_arrow_runtime_helpers,
    ensure_conversion_runtime_dependencies_fn,
    cv2_module,
    np_module,
    fitz_module,
    run_seed: int,
    pass_seed_offset: int,
    action_cls,
    perception_cls,
    reflection_cls,
    get_base_name_from_file_fn,
    semantic_audit_record_fn,
    semantic_quality_flags_fn,
    looks_like_elongated_foreground_rect_fn,
    render_embedded_raster_svg_fn,
    print_fn,
    time_ns_fn,
    calculate_error_fn,
    math_module,
):
    orchestration_kwargs = buildRunIterationPipelineOrchestrationKwargsForRunFromInputsImpl(
        img_path=img_path,
        csv_path=csv_path,
        max_iterations=max_iterations,
        svg_out_dir=svg_out_dir,
        diff_out_dir=diff_out_dir,
        reports_out_dir=reports_out_dir,
        debug_ac0811_dir=debug_ac0811_dir,
        debug_element_diff_dir=debug_element_diff_dir,
        badge_validation_rounds=badge_validation_rounds,
        ensure_conversion_runtime_dependencies_fn=ensure_conversion_runtime_dependencies_fn,
        cv2_module=cv2_module,
        np_module=np_module,
        fitz_module=fitz_module,
        iteration_run_preparation_helpers=iteration_run_preparation_helpers,
        iteration_execution_context_helpers=iteration_execution_context_helpers,
        run_seed=run_seed,
        pass_seed_offset=pass_seed_offset,
        action_cls=action_cls,
        perception_cls=perception_cls,
        reflection_cls=reflection_cls,
        get_base_name_from_file_fn=get_base_name_from_file_fn,
        semantic_audit_record_fn=semantic_audit_record_fn,
        semantic_quality_flags_fn=semantic_quality_flags_fn,
        looks_like_elongated_foreground_rect_fn=looks_like_elongated_foreground_rect_fn,
        render_embedded_raster_svg_fn=render_embedded_raster_svg_fn,
        print_fn=print_fn,
        time_ns_fn=time_ns_fn,
        calculate_error_fn=calculate_error_fn,
        iteration_execution_helpers=iteration_execution_helpers,
        iteration_context_helpers=iteration_context_helpers,
        iteration_dispatch_helpers=iteration_dispatch_helpers,
        iteration_finalization_helpers=iteration_finalization_helpers,
        math_module=math_module,
        iteration_bindings_helpers=iteration_bindings_helpers,
        iteration_initialization_helpers=iteration_initialization_helpers,
        iteration_setup_helpers=iteration_setup_helpers,
        iteration_runtime_helpers=iteration_runtime_helpers,
        iteration_mode_runtime_preparation_helpers=iteration_mode_runtime_preparation_helpers,
        iteration_mode_setup_helpers=iteration_mode_setup_helpers,
        iteration_mode_preparation_helpers=iteration_mode_preparation_helpers,
        iteration_mode_dependency_setup_helpers=iteration_mode_dependency_setup_helpers,
        iteration_mode_dependency_helpers=iteration_mode_dependency_helpers,
        iteration_mode_runtime_helpers=iteration_mode_runtime_helpers,
        iteration_orchestration_helpers=iteration_orchestration_helpers,
        iteration_preparation_helpers=iteration_preparation_helpers,
        gradient_stripe_strategy_helpers=gradient_stripe_strategy_helpers,
        semantic_audit_bootstrap_helpers=semantic_audit_bootstrap_helpers,
        semantic_audit_logging_helpers=semantic_audit_logging_helpers,
        semantic_audit_runtime_helpers=semantic_audit_runtime_helpers,
        semantic_mismatch_reporting_helpers=semantic_mismatch_reporting_helpers,
        semantic_validation_logging_helpers=semantic_validation_logging_helpers,
        semantic_mismatch_runtime_helpers=semantic_mismatch_runtime_helpers,
        semantic_validation_context_helpers=semantic_validation_context_helpers,
        semantic_validation_runtime_helpers=semantic_validation_runtime_helpers,
        semantic_post_validation_helpers=semantic_post_validation_helpers,
        semantic_validation_finalization_helpers=semantic_validation_finalization_helpers,
        semantic_iteration_finalization_helpers=semantic_iteration_finalization_helpers,
        semantic_ac0223_runtime_helpers=semantic_ac0223_runtime_helpers,
        semantic_visual_override_helpers=semantic_visual_override_helpers,
        non_composite_runtime_helpers=non_composite_runtime_helpers,
        conversion_composite_helpers=conversion_composite_helpers,
        semantic_badge_runtime_helpers=semantic_badge_runtime_helpers,
        dual_arrow_badge_helpers=dual_arrow_badge_helpers,
        dual_arrow_runtime_helpers=dual_arrow_runtime_helpers,
        build_run_iteration_pipeline_orchestration_call_kwargs_fn=(
            buildRunIterationPipelineOrchestrationCallKwargsImpl
        ),
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
            iteration_orchestration_helpers.buildRunIterationPipelineOrchestrationKwargsForRunImpl
        ),
        execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
            executeBuildRunIterationPipelineOrchestrationKwargsForRunImpl
        ),
    )

    run_iteration_pipeline_from_inputs_via_orchestration_kwargs = (
        runIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsImpl(
            build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs_fn=(
                buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsKwargsImpl
            ),
            run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs={
                "run_iteration_pipeline_orchestration_kwargs": orchestration_kwargs,
                "build_run_iteration_pipeline_orchestration_kwargs_for_run_fn": (
                    iteration_orchestration_helpers.buildRunIterationPipelineOrchestrationKwargsForRunImpl
                ),
                "run_iteration_pipeline_orchestration_fn": (
                    iteration_orchestration_helpers.runIterationPipelineOrchestrationImpl
                ),
                "execute_run_iteration_pipeline_orchestration_for_run_fn": (
                    iteration_orchestration_helpers.executeRunIterationPipelineOrchestrationForRunImpl
                ),
                "build_run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs_fn": (
                    buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunCallKwargsImpl
                ),
                "execute_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_builder_for_run_fn": (
                    executeRunIterationPipelineFromInputsViaOrchestrationKwargsBuilderForRunImpl
                ),
                "build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_fn": (
                    iteration_orchestration_helpers.buildRunIterationPipelineFromInputsViaOrchestrationKwargsImpl
                ),
            },
            build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_fn=(
                buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunImpl
            ),
        )
    )

    return runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl(
        run_iteration_pipeline_from_inputs_via_orchestration_kwargs=(
            run_iteration_pipeline_from_inputs_via_orchestration_kwargs
        ),
        build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_fn=(
            iteration_orchestration_helpers.buildRunIterationPipelineViaOrchestrationForRunCallKwargsImpl
        ),
        run_iteration_pipeline_via_orchestration_for_run_fn=(
            iteration_orchestration_helpers.runIterationPipelineViaOrchestrationForRunImpl
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_fn=(
            iteration_orchestration_helpers.runIterationPipelineFromInputsViaOrchestrationImpl
        ),
        execute_run_iteration_pipeline_from_inputs_via_orchestration_fn=(
            iteration_orchestration_helpers.executeRunIterationPipelineFromInputsViaOrchestrationImpl
        ),
        build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_fn=(
            iteration_orchestration_helpers.buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
            iteration_orchestration_helpers.runIterationPipelineFromInputsViaOrchestrationForRunImpl
        ),
        execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_fn=(
            iteration_orchestration_helpers.executeRunIterationPipelineFromInputsViaOrchestrationForRunImpl
        ),
        run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
            iteration_orchestration_helpers.runIterationPipelineFromInputsViaOrchestrationForRunCallImpl
        ),
        execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_fn=(
            executeRunIterationPipelineFromInputsViaOrchestrationForRunCallImpl
        ),
    )
