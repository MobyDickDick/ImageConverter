"""Helpers for the remaining runIterationPipeline orchestration block."""

from __future__ import annotations


def prepareIterationModeRuntimeImpl(
    *,
    perception_image,
    params,
    stripe_strategy: str,
    looks_like_elongated_foreground_rect_fn,
    apply_semantic_visual_override_fn,
    build_iteration_mode_runners_fn,
    mode_runner_dependencies: dict[str, object],
) -> dict[str, object]:
    """Prepare visual override state and mode runners for iteration dispatch."""

    elongated_rect_geometry = looks_like_elongated_foreground_rect_fn(perception_image)
    updated_params, semantic_mode_visual_override = apply_semantic_visual_override_fn(
        params=params,
        stripe_strategy=stripe_strategy,
        elongated_rect_geometry=elongated_rect_geometry,
    )
    mode_runners = build_iteration_mode_runners_fn(**mode_runner_dependencies)
    return {
        "params": updated_params,
        "semantic_mode_visual_override": semantic_mode_visual_override,
        "mode_runners": mode_runners,
    }


def runIterationPipelineOrchestrationImpl(
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
    prepare_run_locals_for_run_fn,
    build_prepare_run_locals_for_run_call_kwargs_fn,
    build_run_iteration_pipeline_for_run_call_kwargs_fn,
    run_iteration_pipeline_for_run_fn,
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
    build_prepared_mode_builder_kwargs_fn,
    run_prepared_iteration_and_finalize_fn,
    build_prepared_iteration_mode_kwargs_fn,
    run_prepared_iteration_mode_fn,
    finalize_iteration_result_fn,
    math_module,
    iteration_run_preparation_helpers,
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
    iteration_context_helpers,
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
):
    """Run dependency bootstrap + run-locals preparation + execution dispatch."""

    ensure_dependency_kwargs = buildEnsureConversionRuntimeDependenciesKwargsImpl(
        cv2_module=cv2_module,
        np_module=np_module,
        fitz_module=fitz_module,
    )
    executeEnsureConversionRuntimeDependenciesImpl(
        ensure_dependency_kwargs=ensure_dependency_kwargs,
        ensure_conversion_runtime_dependencies_fn=ensure_conversion_runtime_dependencies_fn,
    )

    prepare_run_locals_call_kwargs = buildPrepareRunLocalsForRunCallKwargsImpl(
        img_path=img_path,
        csv_path=csv_path,
        reports_out_dir=reports_out_dir,
        svg_out_dir=svg_out_dir,
        diff_out_dir=diff_out_dir,
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
        np_module=np_module,
        cv2_module=cv2_module,
        print_fn=print_fn,
        time_ns_fn=time_ns_fn,
        iteration_run_preparation_helpers=iteration_run_preparation_helpers,
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
        iteration_context_helpers=iteration_context_helpers,
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
    )
    run_locals = executePrepareRunLocalsForRunImpl(
        prepare_run_locals_call_kwargs=prepare_run_locals_call_kwargs,
        build_prepare_run_locals_for_run_call_kwargs_fn=build_prepare_run_locals_for_run_call_kwargs_fn,
        prepare_run_locals_for_run_fn=prepare_run_locals_for_run_fn,
    )
    run_iteration_dispatch_kwargs = buildRunIterationPipelineDispatchKwargsImpl(
        run_locals=run_locals,
        img_path=img_path,
        max_iterations=max_iterations,
        badge_validation_rounds=badge_validation_rounds,
        debug_element_diff_dir=debug_element_diff_dir,
        debug_ac0811_dir=debug_ac0811_dir,
        calculate_error_fn=calculate_error_fn,
        print_fn=print_fn,
        build_prepared_mode_builder_kwargs_fn=build_prepared_mode_builder_kwargs_fn,
        run_prepared_iteration_and_finalize_fn=run_prepared_iteration_and_finalize_fn,
        build_prepared_iteration_mode_kwargs_fn=build_prepared_iteration_mode_kwargs_fn,
        run_prepared_iteration_mode_fn=run_prepared_iteration_mode_fn,
        finalize_iteration_result_fn=finalize_iteration_result_fn,
        math_module=math_module,
    )
    return executeRunIterationPipelineDispatchImpl(
        run_iteration_dispatch_kwargs=run_iteration_dispatch_kwargs,
        build_run_iteration_pipeline_for_run_call_kwargs_fn=build_run_iteration_pipeline_for_run_call_kwargs_fn,
        run_iteration_pipeline_for_run_fn=run_iteration_pipeline_for_run_fn,
    )


def buildRunIterationPipelineOrchestrationKwargsForRunImpl(**kwargs) -> dict[str, object]:
    """Return the input mapping for the top-level orchestration call."""

    return dict(kwargs)


def buildPrepareRunLocalsForRunCallKwargsImpl(**kwargs) -> dict[str, object]:
    """Return the input mapping for run-locals call-kwargs builders."""

    return dict(kwargs)


def buildEnsureConversionRuntimeDependenciesKwargsImpl(**kwargs) -> dict[str, object]:
    """Return the input mapping for dependency-bootstrap call-kwargs builders."""

    return dict(kwargs)


def buildRunIterationPipelineDispatchKwargsImpl(**kwargs) -> dict[str, object]:
    """Return the input mapping for run-dispatch call-kwargs builders."""

    return dict(kwargs)


def executeEnsureConversionRuntimeDependenciesImpl(
    *,
    ensure_dependency_kwargs: dict[str, object],
    ensure_conversion_runtime_dependencies_fn,
) -> None:
    """Execute runtime dependency bootstrap with the prepared kwargs mapping."""

    ensure_conversion_runtime_dependencies_fn(**ensure_dependency_kwargs)


def executePrepareRunLocalsForRunImpl(
    *,
    prepare_run_locals_call_kwargs: dict[str, object],
    build_prepare_run_locals_for_run_call_kwargs_fn,
    prepare_run_locals_for_run_fn,
):
    """Build run-local kwargs and execute run-local preparation."""

    return prepare_run_locals_for_run_fn(
        **build_prepare_run_locals_for_run_call_kwargs_fn(**prepare_run_locals_call_kwargs)
    )


def executeRunIterationPipelineDispatchImpl(
    *,
    run_iteration_dispatch_kwargs: dict[str, object],
    build_run_iteration_pipeline_for_run_call_kwargs_fn,
    run_iteration_pipeline_for_run_fn,
):
    """Build run-dispatch call kwargs and execute the run-dispatch function."""

    return run_iteration_pipeline_for_run_fn(
        **build_run_iteration_pipeline_for_run_call_kwargs_fn(**run_iteration_dispatch_kwargs)
    )


def executeRunIterationPipelineOrchestrationForRunImpl(
    *,
    run_iteration_pipeline_orchestration_kwargs: dict[str, object],
    build_run_iteration_pipeline_orchestration_kwargs_for_run_fn,
    run_iteration_pipeline_orchestration_fn,
):
    """Build top-level orchestration kwargs and execute the orchestration call."""

    return run_iteration_pipeline_orchestration_fn(
        **build_run_iteration_pipeline_orchestration_kwargs_for_run_fn(
            **run_iteration_pipeline_orchestration_kwargs
        )
    )




def buildRunIterationPipelineViaOrchestrationForRunCallKwargsImpl(**kwargs) -> dict[str, object]:
    """Return the input mapping for the run-level via-orchestration call."""

    return dict(kwargs)
def runIterationPipelineViaOrchestrationForRunImpl(
    *,
    run_iteration_pipeline_orchestration_kwargs: dict[str, object],
    build_run_iteration_pipeline_orchestration_kwargs_for_run_fn,
    run_iteration_pipeline_orchestration_fn,
    execute_run_iteration_pipeline_orchestration_for_run_fn,
):
    """Execute the full top-level orchestration flow for runIterationPipeline."""

    via_orchestration_call_kwargs = buildRunIterationPipelineViaOrchestrationCallKwargsImpl(
        run_iteration_pipeline_orchestration_kwargs=run_iteration_pipeline_orchestration_kwargs,
        build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
            build_run_iteration_pipeline_orchestration_kwargs_for_run_fn
        ),
        run_iteration_pipeline_orchestration_fn=run_iteration_pipeline_orchestration_fn,
    )
    return executeRunIterationPipelineViaOrchestrationImpl(
        run_iteration_pipeline_via_orchestration_call_kwargs=via_orchestration_call_kwargs,
        execute_run_iteration_pipeline_orchestration_for_run_fn=(
            execute_run_iteration_pipeline_orchestration_for_run_fn
        ),
    )


def buildRunIterationPipelineViaOrchestrationCallKwargsImpl(**kwargs) -> dict[str, object]:
    """Return the input mapping for the via-orchestration executor call."""

    return dict(kwargs)


def executeRunIterationPipelineViaOrchestrationImpl(
    *,
    run_iteration_pipeline_via_orchestration_call_kwargs: dict[str, object],
    execute_run_iteration_pipeline_orchestration_for_run_fn,
):
    """Execute the via-orchestration flow with prepared executor kwargs."""

    return execute_run_iteration_pipeline_orchestration_for_run_fn(
        **run_iteration_pipeline_via_orchestration_call_kwargs
    )
