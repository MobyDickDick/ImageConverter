from __future__ import annotations


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
    orchestration_kwargs = iteration_orchestration_helpers.buildRunIterationPipelineOrchestrationKwargsForRunImpl(
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
        prepare_run_locals_for_run_fn=iteration_run_preparation_helpers.prepareRunIterationPipelineLocalsForRunImpl,
        build_prepare_run_locals_for_run_call_kwargs_fn=iteration_run_preparation_helpers.buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl,
        build_run_iteration_pipeline_for_run_call_kwargs_fn=iteration_execution_context_helpers.buildRunIterationPipelineForRunCallKwargsImpl,
        run_iteration_pipeline_for_run_fn=iteration_execution_context_helpers.runIterationPipelineForRunImpl,
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
        build_prepared_mode_builder_kwargs_fn=iteration_execution_helpers.buildPreparedModeBuilderKwargsImpl,
        run_prepared_iteration_and_finalize_fn=iteration_execution_helpers.runPreparedIterationAndFinalizeImpl,
        build_prepared_iteration_mode_kwargs_fn=iteration_context_helpers.buildPreparedIterationModeKwargsImpl,
        run_prepared_iteration_mode_fn=iteration_dispatch_helpers.runPreparedIterationModeImpl,
        finalize_iteration_result_fn=iteration_finalization_helpers.finalizeIterationResultImpl,
        math_module=math_module,
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

    run_iteration_pipeline_from_inputs_via_orchestration_kwargs = (
        iteration_orchestration_helpers.buildRunIterationPipelineFromInputsViaOrchestrationKwargsImpl(
            run_iteration_pipeline_orchestration_kwargs=orchestration_kwargs,
            build_run_iteration_pipeline_orchestration_kwargs_for_run_fn=(
                iteration_orchestration_helpers.buildRunIterationPipelineOrchestrationKwargsForRunImpl
            ),
            run_iteration_pipeline_orchestration_fn=(
                iteration_orchestration_helpers.runIterationPipelineOrchestrationImpl
            ),
            execute_run_iteration_pipeline_orchestration_for_run_fn=(
                iteration_orchestration_helpers.executeRunIterationPipelineOrchestrationForRunImpl
            ),
        )
    )

    return iteration_orchestration_helpers.runIterationPipelineFromInputsViaOrchestrationForRunCallImpl(
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
    )
