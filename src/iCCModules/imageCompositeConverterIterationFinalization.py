from __future__ import annotations

from typing import Any


def finalizeIterationResultImpl(*, mode: str, mode_result: Any, math_module) -> Any:
    if mode_result is None:
        return None
    if mode != "composite":
        return mode_result
    best_error = mode_result[4]
    if not math_module.isfinite(float(best_error)):
        return None
    return mode_result
