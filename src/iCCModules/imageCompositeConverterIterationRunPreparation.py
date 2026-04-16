from __future__ import annotations

from typing import Any, Callable


def buildPrepareIterationInputRuntimeForRunKwargsImpl(
    *,
    img_path: str,
    csv_path: str,
    perception_cls,
    reflection_cls,
    detect_gradient_stripe_strategy_fn,
    build_pending_semantic_audit_row_fn,
    should_create_semantic_audit_for_base_name_fn,
    get_base_name_from_file_fn,
    build_semantic_audit_record_kwargs_fn,
    semantic_audit_record_fn,
    np_module,
    print_fn,
) -> dict[str, Any]:
    return {
        "img_path": img_path,
        "csv_path": csv_path,
        "perception_cls": perception_cls,
        "reflection_cls": reflection_cls,
        "detect_gradient_stripe_strategy_fn": detect_gradient_stripe_strategy_fn,
        "build_pending_semantic_audit_row_fn": build_pending_semantic_audit_row_fn,
        "should_create_semantic_audit_for_base_name_fn": should_create_semantic_audit_for_base_name_fn,
        "get_base_name_from_file_fn": get_base_name_from_file_fn,
        "build_semantic_audit_record_kwargs_fn": build_semantic_audit_record_kwargs_fn,
        "semantic_audit_record_fn": semantic_audit_record_fn,
        "np_module": np_module,
        "print_fn": print_fn,
    }


def buildPrepareIterationRuntimeCallbacksForRunKwargsImpl(
    *,
    filename: str,
    params: dict[str, Any],
    reports_out_dir: str | None,
    svg_out_dir: str,
    diff_out_dir: str,
    target_img,
    width: int,
    height: int,
    run_seed: int,
    pass_seed_offset: int,
    time_ns_fn,
    render_svg_to_numpy_fn,
    create_diff_image_fn,
    cv2_module,
    iteration_setup_helpers,
    iteration_runtime_helpers,
    print_fn,
) -> dict[str, Any]:
    return {
        "filename": filename,
        "params": params,
        "reports_out_dir": reports_out_dir,
        "svg_out_dir": svg_out_dir,
        "diff_out_dir": diff_out_dir,
        "target_img": target_img,
        "width": width,
        "height": height,
        "run_seed": run_seed,
        "pass_seed_offset": pass_seed_offset,
        "time_ns_fn": time_ns_fn,
        "render_svg_to_numpy_fn": render_svg_to_numpy_fn,
        "create_diff_image_fn": create_diff_image_fn,
        "cv2_module": cv2_module,
        "iteration_setup_helpers": iteration_setup_helpers,
        "iteration_runtime_helpers": iteration_runtime_helpers,
        "print_fn": print_fn,
    }


def prepareIterationInputRuntimeForRunImpl(
    *,
    prepare_iteration_inputs_fn: Callable[..., dict[str, Any] | None],
    extract_iteration_input_bindings_fn: Callable[..., dict[str, Any]],
    extract_iteration_input_runtime_fields_fn: Callable[..., dict[str, Any]],
    prepare_iteration_inputs_kwargs: dict[str, Any],
) -> dict[str, Any] | None:
    iteration_inputs = prepare_iteration_inputs_fn(**prepare_iteration_inputs_kwargs)
    if iteration_inputs is None:
        return None
    iteration_input_bindings = extract_iteration_input_bindings_fn(
        iteration_inputs=iteration_inputs,
    )
    return extract_iteration_input_runtime_fields_fn(
        iteration_input_bindings=iteration_input_bindings,
    )


def prepareIterationRuntimeCallbacksForRunImpl(
    *,
    prepare_iteration_runtime_fn: Callable[..., dict[str, Any]],
    extract_iteration_runtime_bindings_fn: Callable[..., dict[str, Any]],
    extract_iteration_runtime_callbacks_fn: Callable[..., dict[str, Any]],
    prepare_iteration_runtime_kwargs: dict[str, Any],
) -> dict[str, Any]:
    iteration_runtime_state = prepare_iteration_runtime_fn(
        **prepare_iteration_runtime_kwargs,
    )
    iteration_runtime_bindings = extract_iteration_runtime_bindings_fn(
        iteration_runtime_state=iteration_runtime_state,
    )
    return extract_iteration_runtime_callbacks_fn(
        iteration_runtime_bindings=iteration_runtime_bindings,
    )


def prepareRunIterationPipelineLocalsImpl(
    *,
    prepare_iteration_input_runtime_for_run_fn: Callable[..., dict[str, Any] | None],
    extract_iteration_input_runtime_locals_fn: Callable[..., dict[str, Any]],
    prepare_iteration_runtime_callbacks_for_run_fn: Callable[..., dict[str, Any]],
    extract_iteration_runtime_callback_locals_fn: Callable[..., dict[str, Any]],
    prepare_iteration_mode_runtime_locals_for_run_fn: Callable[..., dict[str, Any]],
    extract_run_iteration_pipeline_locals_fn: Callable[..., dict[str, Any]],
    prepare_iteration_input_runtime_for_run_kwargs: dict[str, Any],
    prepare_iteration_runtime_callbacks_for_run_kwargs_builder_fn: Callable[..., dict[str, Any]],
    prepare_iteration_runtime_callbacks_for_run_shared_kwargs: dict[str, Any],
    prepare_iteration_mode_runtime_locals_for_run_kwargs_builder_fn: Callable[..., dict[str, Any]],
    prepare_iteration_mode_runtime_locals_for_run_shared_kwargs: dict[str, Any],
) -> dict[str, Any] | None:
    iteration_input_runtime_fields = prepare_iteration_input_runtime_for_run_fn(
        **prepare_iteration_input_runtime_for_run_kwargs,
    )
    if iteration_input_runtime_fields is None:
        return None

    iteration_input_runtime_locals = extract_iteration_input_runtime_locals_fn(
        iteration_input_runtime_fields=iteration_input_runtime_fields,
    )
    iteration_runtime_callbacks = prepare_iteration_runtime_callbacks_for_run_fn(
        prepare_iteration_runtime_kwargs=prepare_iteration_runtime_callbacks_for_run_kwargs_builder_fn(
            filename=iteration_input_runtime_locals["filename"],
            params=iteration_input_runtime_locals["params"],
            target_img=iteration_input_runtime_locals["perception"].img,
            width=iteration_input_runtime_locals["width"],
            height=iteration_input_runtime_locals["height"],
            **prepare_iteration_runtime_callbacks_for_run_shared_kwargs,
        ),
    )
    iteration_runtime_callback_locals = extract_iteration_runtime_callback_locals_fn(
        iteration_runtime_callbacks=iteration_runtime_callbacks,
    )
    iteration_mode_runtime_locals = prepare_iteration_mode_runtime_locals_for_run_fn(
        **prepare_iteration_mode_runtime_locals_for_run_kwargs_builder_fn(
            params=iteration_input_runtime_locals["params"],
            perception_image=iteration_input_runtime_locals["perception"].img,
            stripe_strategy=iteration_input_runtime_locals["stripe_strategy"],
            **prepare_iteration_mode_runtime_locals_for_run_shared_kwargs,
        ),
    )
    return extract_run_iteration_pipeline_locals_fn(
        iteration_input_runtime_locals=iteration_input_runtime_locals,
        iteration_runtime_callback_locals=iteration_runtime_callback_locals,
        iteration_mode_runtime_locals=iteration_mode_runtime_locals,
    )


def buildPrepareRunIterationPipelineLocalsKwargsImpl(
    *,
    prepare_iteration_input_runtime_for_run_fn,
    extract_iteration_input_runtime_locals_fn,
    prepare_iteration_runtime_callbacks_for_run_fn,
    extract_iteration_runtime_callback_locals_fn,
    prepare_iteration_mode_runtime_locals_for_run_fn,
    extract_run_iteration_pipeline_locals_fn,
    prepare_iteration_input_runtime_for_run_kwargs,
    prepare_iteration_runtime_callbacks_for_run_kwargs_builder_fn,
    prepare_iteration_runtime_callbacks_for_run_shared_kwargs,
    prepare_iteration_mode_runtime_locals_for_run_kwargs_builder_fn,
    prepare_iteration_mode_runtime_locals_for_run_shared_kwargs,
) -> dict[str, Any]:
    return {
        "prepare_iteration_input_runtime_for_run_fn": prepare_iteration_input_runtime_for_run_fn,
        "extract_iteration_input_runtime_locals_fn": extract_iteration_input_runtime_locals_fn,
        "prepare_iteration_runtime_callbacks_for_run_fn": prepare_iteration_runtime_callbacks_for_run_fn,
        "extract_iteration_runtime_callback_locals_fn": extract_iteration_runtime_callback_locals_fn,
        "prepare_iteration_mode_runtime_locals_for_run_fn": prepare_iteration_mode_runtime_locals_for_run_fn,
        "extract_run_iteration_pipeline_locals_fn": extract_run_iteration_pipeline_locals_fn,
        "prepare_iteration_input_runtime_for_run_kwargs": prepare_iteration_input_runtime_for_run_kwargs,
        "prepare_iteration_runtime_callbacks_for_run_kwargs_builder_fn": prepare_iteration_runtime_callbacks_for_run_kwargs_builder_fn,
        "prepare_iteration_runtime_callbacks_for_run_shared_kwargs": prepare_iteration_runtime_callbacks_for_run_shared_kwargs,
        "prepare_iteration_mode_runtime_locals_for_run_kwargs_builder_fn": prepare_iteration_mode_runtime_locals_for_run_kwargs_builder_fn,
        "prepare_iteration_mode_runtime_locals_for_run_shared_kwargs": prepare_iteration_mode_runtime_locals_for_run_shared_kwargs,
    }


def buildPrepareRunIterationPipelineLocalsKwargsForRunImpl(
    *,
    img_path: str,
    csv_path: str,
    reports_out_dir: str | None,
    svg_out_dir: str,
    diff_out_dir: str,
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
    np_module,
    cv2_module,
    print_fn,
    time_ns_fn,
    iteration_run_preparation_helpers,
    iteration_bindings_helpers,
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
) -> dict[str, Any]:
    return buildPrepareRunIterationPipelineLocalsKwargsImpl(
        prepare_iteration_input_runtime_for_run_fn=iteration_run_preparation_helpers.prepareIterationInputRuntimeForRunImpl,
        extract_iteration_input_runtime_locals_fn=iteration_bindings_helpers.extractIterationInputRuntimeLocalsImpl,
        prepare_iteration_runtime_callbacks_for_run_fn=iteration_run_preparation_helpers.prepareIterationRuntimeCallbacksForRunImpl,
        extract_iteration_runtime_callback_locals_fn=iteration_bindings_helpers.extractIterationRuntimeCallbackLocalsImpl,
        prepare_iteration_mode_runtime_locals_for_run_fn=iteration_mode_runtime_preparation_helpers.prepareIterationModeRuntimeLocalsForRunImpl,
        extract_run_iteration_pipeline_locals_fn=iteration_bindings_helpers.extractRunIterationPipelineLocalsImpl,
        prepare_iteration_input_runtime_for_run_kwargs={
            "prepare_iteration_inputs_fn": iteration_preparation_helpers.prepareIterationInputsImpl,
            "extract_iteration_input_bindings_fn": iteration_context_helpers.extractIterationInputBindingsImpl,
            "extract_iteration_input_runtime_fields_fn": iteration_bindings_helpers.extractIterationInputRuntimeFieldsImpl,
            "prepare_iteration_inputs_kwargs": buildPrepareIterationInputRuntimeForRunKwargsImpl(
                img_path=img_path,
                csv_path=csv_path,
                perception_cls=perception_cls,
                reflection_cls=reflection_cls,
                detect_gradient_stripe_strategy_fn=gradient_stripe_strategy_helpers.detectGradientStripeStrategyImpl,
                build_pending_semantic_audit_row_fn=semantic_audit_bootstrap_helpers.buildPendingSemanticAuditRowImpl,
                should_create_semantic_audit_for_base_name_fn=semantic_audit_runtime_helpers.shouldCreateSemanticAuditForBaseNameImpl,
                get_base_name_from_file_fn=get_base_name_from_file_fn,
                build_semantic_audit_record_kwargs_fn=semantic_audit_runtime_helpers.buildSemanticAuditRecordKwargsImpl,
                semantic_audit_record_fn=semantic_audit_record_fn,
                np_module=np_module,
                print_fn=print_fn,
            ),
        },
        prepare_iteration_runtime_callbacks_for_run_kwargs_builder_fn=iteration_run_preparation_helpers.buildPrepareIterationRuntimeCallbacksForRunKwargsImpl,
        prepare_iteration_runtime_callbacks_for_run_shared_kwargs={
            "reports_out_dir": reports_out_dir,
            "svg_out_dir": svg_out_dir,
            "diff_out_dir": diff_out_dir,
            "run_seed": run_seed,
            "pass_seed_offset": pass_seed_offset,
            "time_ns_fn": time_ns_fn,
            "render_svg_to_numpy_fn": action_cls.render_svg_to_numpy,
            "create_diff_image_fn": action_cls.create_diff_image,
            "cv2_module": cv2_module,
            "iteration_setup_helpers": iteration_setup_helpers,
            "iteration_runtime_helpers": iteration_runtime_helpers,
            "print_fn": print_fn,
        },
        prepare_iteration_mode_runtime_locals_for_run_kwargs_builder_fn=iteration_mode_runtime_preparation_helpers.buildPrepareIterationModeRuntimeBindingsForRunKwargsImpl,
        prepare_iteration_mode_runtime_locals_for_run_shared_kwargs={
            "prepare_iteration_mode_runtime_bindings_for_run_fn": iteration_mode_runtime_preparation_helpers.prepareIterationModeRuntimeBindingsForRunImpl,
            "extract_iteration_mode_runtime_locals_fn": iteration_bindings_helpers.extractIterationModeRuntimeLocalsImpl,
            "build_prepare_iteration_mode_runtime_for_run_kwargs_fn": iteration_mode_setup_helpers.buildPrepareIterationModeRuntimeForRunKwargsImpl,
            "prepare_iteration_mode_runtime_for_run_fn": iteration_mode_preparation_helpers.prepareIterationModeRuntimeForRunImpl,
            "np_module": np_module,
            "action_cls": action_cls,
            "looks_like_elongated_foreground_rect_fn": looks_like_elongated_foreground_rect_fn,
            "semantic_visual_override_helpers": semantic_visual_override_helpers,
            "iteration_mode_dependency_setup_helpers": iteration_mode_dependency_setup_helpers,
            "iteration_mode_runtime_helpers": iteration_mode_runtime_helpers,
            "iteration_orchestration_helpers": iteration_orchestration_helpers,
            "iteration_context_helpers": iteration_context_helpers,
            "semantic_mismatch_reporting_helpers": semantic_mismatch_reporting_helpers,
            "semantic_validation_logging_helpers": semantic_validation_logging_helpers,
            "semantic_mismatch_runtime_helpers": semantic_mismatch_runtime_helpers,
            "semantic_audit_logging_helpers": semantic_audit_logging_helpers,
            "semantic_audit_runtime_helpers": semantic_audit_runtime_helpers,
            "semantic_validation_context_helpers": semantic_validation_context_helpers,
            "semantic_validation_runtime_helpers": semantic_validation_runtime_helpers,
            "semantic_post_validation_helpers": semantic_post_validation_helpers,
            "semantic_validation_finalization_helpers": semantic_validation_finalization_helpers,
            "semantic_iteration_finalization_helpers": semantic_iteration_finalization_helpers,
            "semantic_ac0223_runtime_helpers": semantic_ac0223_runtime_helpers,
            "dual_arrow_badge_helpers": dual_arrow_badge_helpers,
            "dual_arrow_runtime_helpers": dual_arrow_runtime_helpers,
            "gradient_stripe_strategy_helpers": gradient_stripe_strategy_helpers,
            "non_composite_runtime_helpers": non_composite_runtime_helpers,
            "conversion_composite_helpers": conversion_composite_helpers,
            "semantic_badge_runtime_helpers": semantic_badge_runtime_helpers,
            "build_iteration_mode_runner_dependencies_fn": iteration_mode_dependency_helpers.buildIterationModeRunnerDependenciesImpl,
            "semantic_audit_record_fn": semantic_audit_record_fn,
            "semantic_quality_flags_fn": semantic_quality_flags_fn,
            "render_embedded_raster_svg_fn": render_embedded_raster_svg_fn,
            "print_fn": print_fn,
        },
    )
