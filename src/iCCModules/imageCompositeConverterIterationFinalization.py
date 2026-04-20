from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def _extractCompositeBestError(mode_result: Any) -> float | None:
    if not isinstance(mode_result, Sequence) or isinstance(mode_result, (str, bytes)):
        return None
    # Legacy composite result shape: (filename, description, params, best_iter, best_error)
    if len(mode_result) >= 5:
        return float(mode_result[4])
    # Current composite result shape: (best_iter, best_error)
    if len(mode_result) >= 2:
        return float(mode_result[1])
    return None


def finalizeIterationResultImpl(*, mode: str, mode_result: Any, math_module) -> Any:
    if mode_result is None:
        return None
    if mode != "composite":
        return mode_result
    best_error = _extractCompositeBestError(mode_result)
    if best_error is None or not math_module.isfinite(best_error):
        return None
    return mode_result
