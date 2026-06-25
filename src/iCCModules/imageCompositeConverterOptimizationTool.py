"""Generic optimization tool primitives decoupled from image rendering."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class OptimizationVariable:
    """Single scalar search variable with inclusive bounds."""

    name: str
    low: float
    high: float
    current: float | None = None


@dataclass(frozen=True)
class OptimizationResult:
    """Best parameter set returned by the optimization tool."""

    parameters: dict[str, float]
    error: float
    evaluations: int
    converged: bool
    stop_reason: str


@dataclass(frozen=True)
class OptimizationProblem:
    """Pure optimization contract: variables plus an error function."""

    variables: tuple[OptimizationVariable, ...]
    error_fn: Callable[[dict[str, float]], float]
    max_evaluations: int | None = None
    improvement_epsilon: float = 0.0


def evaluateCandidateGridImpl(
    problem: OptimizationProblem,
    candidates_by_name: dict[str, Iterable[float]],
) -> OptimizationResult:
    """Evaluate a finite candidate grid and return the lowest finite error.

    The image/rendering layer remains outside this tool: callers provide an
    ``error_fn`` that can do any rendering or pixel comparison it needs.
    """

    if not problem.variables:
        raise ValueError("OptimizationProblem requires at least one variable")

    variable_names = [variable.name for variable in problem.variables]
    unknown = set(candidates_by_name) - set(variable_names)
    if unknown:
        raise ValueError(f"Unknown candidate variable(s): {', '.join(sorted(unknown))}")

    candidate_lists: list[list[float]] = []
    bounds: dict[str, tuple[float, float]] = {}
    for variable in problem.variables:
        low = float(variable.low)
        high = float(variable.high)
        if low > high:
            raise ValueError(f"Invalid bounds for {variable.name}: {low} > {high}")
        bounds[variable.name] = (low, high)
        raw_candidates = list(candidates_by_name.get(variable.name, ()))
        if variable.current is not None:
            raw_candidates.append(float(variable.current))
        if not raw_candidates:
            raise ValueError(f"No candidates supplied for {variable.name}")
        clipped = [min(high, max(low, float(value))) for value in raw_candidates]
        candidate_lists.append(sorted(set(clipped)))

    best_parameters: dict[str, float] | None = None
    best_error = float("inf")
    evaluations = 0
    max_evaluations = problem.max_evaluations

    def visit(index: int, current: dict[str, float]) -> None:
        nonlocal best_parameters, best_error, evaluations
        if max_evaluations is not None and evaluations >= max_evaluations:
            return
        if index == len(variable_names):
            evaluations += 1
            error = float(problem.error_fn(dict(current)))
            if math.isfinite(error) and error + float(problem.improvement_epsilon) < best_error:
                best_error = error
                best_parameters = dict(current)
            return
        name = variable_names[index]
        for value in candidate_lists[index]:
            current[name] = value
            visit(index + 1, current)

    visit(0, {})
    if best_parameters is None:
        return OptimizationResult({}, float("inf"), evaluations, False, "no_finite_candidate")
    stop_reason = "max_evaluations" if max_evaluations is not None and evaluations >= max_evaluations else "grid_exhausted"
    return OptimizationResult(best_parameters, best_error, evaluations, True, stop_reason)
