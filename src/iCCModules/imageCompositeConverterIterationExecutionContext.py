from __future__ import annotations

from typing import Any


def buildRunPreparedIterationAndFinalizeKwargsImpl(
    *,
    params: dict[str, Any],
    prepared_mode_builder_kwargs: dict[str, Any],
    build_prepared_iteration_mode_kwargs_fn,
    run_prepared_iteration_mode_fn,
    finalize_iteration_result_fn,
    math_module,
) -> dict[str, Any]:
    return {
        "params": params,
        "prepared_mode_builder_kwargs": prepared_mode_builder_kwargs,
        "build_prepared_iteration_mode_kwargs_fn": build_prepared_iteration_mode_kwargs_fn,
        "run_prepared_iteration_mode_fn": run_prepared_iteration_mode_fn,
        "finalize_iteration_result_fn": finalize_iteration_result_fn,
        "math_module": math_module,
    }
