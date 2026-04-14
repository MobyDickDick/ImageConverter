from __future__ import annotations

from typing import Any


def runPreparedIterationAndFinalizeImpl(
    *,
    params: dict[str, Any],
    prepared_mode_builder_kwargs: dict[str, Any],
    build_prepared_iteration_mode_kwargs_fn,
    run_prepared_iteration_mode_fn,
    finalize_iteration_result_fn,
    math_module,
) -> Any:
    prepared_mode_kwargs = build_prepared_iteration_mode_kwargs_fn(
        **prepared_mode_builder_kwargs,
    )
    mode_result = run_prepared_iteration_mode_fn(**prepared_mode_kwargs)
    return finalize_iteration_result_fn(
        mode=str(params.get("mode", "")),
        mode_result=mode_result,
        math_module=math_module,
    )
