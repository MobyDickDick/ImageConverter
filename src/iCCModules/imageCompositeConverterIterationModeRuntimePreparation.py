from __future__ import annotations

from typing import Any


def prepareIterationModeRuntimeBindingsImpl(
    *,
    build_prepare_iteration_mode_runtime_for_run_kwargs_fn,
    prepare_iteration_mode_runtime_for_run_fn,
    build_prepare_iteration_mode_runtime_for_run_kwargs_kwargs: dict[str, object],
) -> dict[str, object]:
    iteration_mode_runtime_kwargs = build_prepare_iteration_mode_runtime_for_run_kwargs_fn(
        **build_prepare_iteration_mode_runtime_for_run_kwargs_kwargs,
    )
    iteration_mode_runtime_bindings = prepare_iteration_mode_runtime_for_run_fn(
        **iteration_mode_runtime_kwargs,
    )
    return {
        "params": iteration_mode_runtime_bindings["params"],
        "semantic_mode_visual_override": iteration_mode_runtime_bindings["semantic_mode_visual_override"],
        "mode_runners": iteration_mode_runtime_bindings["mode_runners"],
    }


def prepareIterationModeRuntimeBindingsForRunImpl(
    *,
    build_prepare_iteration_mode_runtime_for_run_kwargs_fn,
    prepare_iteration_mode_runtime_for_run_fn,
    np_module,
    action_cls,
    params: dict[str, object],
    perception_image,
    stripe_strategy,
    looks_like_elongated_foreground_rect_fn,
    semantic_visual_override_helpers,
    iteration_mode_dependency_setup_helpers,
    iteration_mode_runtime_helpers,
    iteration_orchestration_helpers,
    iteration_context_helpers,
    semantic_mismatch_reporting_helpers,
    semantic_validation_logging_helpers,
    semantic_mismatch_runtime_helpers,
    semantic_audit_logging_helpers,
    semantic_audit_runtime_helpers,
    semantic_validation_context_helpers,
    semantic_validation_runtime_helpers,
    semantic_post_validation_helpers,
    semantic_validation_finalization_helpers,
    semantic_iteration_finalization_helpers,
    semantic_ac0223_runtime_helpers,
    dual_arrow_badge_helpers,
    dual_arrow_runtime_helpers,
    gradient_stripe_strategy_helpers,
    non_composite_runtime_helpers,
    conversion_composite_helpers,
    semantic_badge_runtime_helpers,
    build_iteration_mode_runner_dependencies_fn,
    semantic_audit_record_fn,
    semantic_quality_flags_fn,
    render_embedded_raster_svg_fn,
    print_fn,
) -> dict[str, Any]:
    return prepareIterationModeRuntimeBindingsImpl(
        build_prepare_iteration_mode_runtime_for_run_kwargs_fn=build_prepare_iteration_mode_runtime_for_run_kwargs_fn,
        prepare_iteration_mode_runtime_for_run_fn=prepare_iteration_mode_runtime_for_run_fn,
        build_prepare_iteration_mode_runtime_for_run_kwargs_kwargs={
            "np_module": np_module,
            "action_cls": action_cls,
            "params": params,
            "perception_image": perception_image,
            "stripe_strategy": stripe_strategy,
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
            "build_iteration_mode_runner_dependencies_fn": build_iteration_mode_runner_dependencies_fn,
            "semantic_audit_record_fn": semantic_audit_record_fn,
            "semantic_quality_flags_fn": semantic_quality_flags_fn,
            "render_embedded_raster_svg_fn": render_embedded_raster_svg_fn,
            "print_fn": print_fn,
        },
    )
