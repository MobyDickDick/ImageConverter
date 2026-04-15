from __future__ import annotations

from typing import Any


def prepareIterationModeRuntimeForRunImpl(
    *,
    np_module,
    action_cls,
    params: dict[str, Any],
    perception_image,
    stripe_strategy: str,
    looks_like_elongated_foreground_rect_fn,
    semantic_visual_override_helpers,
    iteration_mode_dependency_setup_helpers,
    iteration_mode_runtime_helpers,
    iteration_orchestration_helpers,
    iteration_context_helpers,
    mode_dependency_helper_modules: dict[str, Any],
    semantic_audit_record_fn,
    semantic_quality_flags_fn,
    render_embedded_raster_svg_fn,
    print_fn,
) -> dict[str, Any]:
    mode_runner_dependencies = iteration_mode_dependency_setup_helpers.buildIterationModeRunnerDependenciesForRunImpl(
        np_module=np_module,
        action_cls=action_cls,
        semantic_audit_record_fn=semantic_audit_record_fn,
        semantic_quality_flags_fn=semantic_quality_flags_fn,
        render_embedded_raster_svg_fn=render_embedded_raster_svg_fn,
        print_fn=print_fn,
        **mode_dependency_helper_modules,
    )

    mode_runtime = iteration_orchestration_helpers.prepareIterationModeRuntimeImpl(
        perception_image=perception_image,
        params=params,
        stripe_strategy=stripe_strategy,
        looks_like_elongated_foreground_rect_fn=looks_like_elongated_foreground_rect_fn,
        apply_semantic_visual_override_fn=lambda **kwargs: semantic_visual_override_helpers.applySemanticVisualOverrideImpl(
            **kwargs,
            print_fn=print_fn,
        ),
        build_iteration_mode_runners_fn=iteration_mode_runtime_helpers.buildIterationModeRunnersImpl,
        mode_runner_dependencies=mode_runner_dependencies,
    )
    return iteration_context_helpers.extractIterationModeRuntimeBindingsImpl(
        mode_runtime=mode_runtime,
    )
