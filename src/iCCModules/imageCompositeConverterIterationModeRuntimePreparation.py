from __future__ import annotations


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
