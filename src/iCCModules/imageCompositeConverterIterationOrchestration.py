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
