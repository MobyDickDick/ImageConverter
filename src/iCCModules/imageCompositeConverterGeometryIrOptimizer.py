"""Sequential Geometry-IR optimization helpers.

The optimizer is intentionally renderer-agnostic: callers provide a renderer and
an error function, while this module enforces the PR-R3 contract that IR elements
are fitted one after another and only strictly improving candidates are accepted.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterable
from typing import Any

GeometryIr = list[dict[str, object]]
RenderFn = Callable[[GeometryIr], object]
ErrorFn = Callable[[object], float]
CandidateProvider = Callable[[dict[str, object], GeometryIr, int], Iterable[dict[str, object]]]


def _element_name(element: dict[str, object]) -> str:
    return str(element.get("id") or element.get("kind") or "unknown")


def _clone_ir(geometry_ir: GeometryIr) -> GeometryIr:
    return copy.deepcopy(geometry_ir)


def _with_element(geometry_ir: GeometryIr, step_index: int, element: dict[str, object]) -> GeometryIr:
    candidate_ir = _clone_ir(geometry_ir)
    candidate_ir[step_index] = copy.deepcopy(element)
    return candidate_ir


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _default_candidate_provider(
    element: dict[str, object], _current_ir: GeometryIr, _step_index: int
) -> Iterable[dict[str, object]]:
    """Yield conservative local parameter probes for one IR element.

    The default provider is deliberately small and deterministic. Production
    callers can pass a richer provider, while tests can pass exact mock
    candidates. The current element is yielded first so a non-improving step can
    be logged without changing the IR.
    """

    yield copy.deepcopy(element)

    bbox = element.get("bbox")
    if isinstance(bbox, list) and len(bbox) == 4:
        probes = (
            (0, -0.02),
            (0, 0.02),
            (1, -0.02),
            (1, 0.02),
            (2, -0.02),
            (2, 0.02),
            (3, -0.02),
            (3, 0.02),
        )
        for idx, delta in probes:
            candidate = copy.deepcopy(element)
            candidate_bbox = [float(v) for v in bbox]
            candidate_bbox[idx] = _clamp01(candidate_bbox[idx] + delta)
            if candidate_bbox[2] > 0.01 and candidate_bbox[3] > 0.01:
                candidate["bbox"] = candidate_bbox
                yield candidate

    if "stroke_width" in element:
        stroke_width = max(0.001, float(element.get("stroke_width", 0.01)))
        for factor in (0.85, 1.15):
            candidate = copy.deepcopy(element)
            candidate["stroke_width"] = max(0.001, stroke_width * factor)
            yield candidate

    if element.get("kind") in {"PlusGlyph", "MinusGlyph"}:
        for delta in (-0.02, 0.02):
            candidate = copy.deepcopy(element)
            candidate["dy"] = float(element.get("dy", 0.0)) + delta
            yield candidate


def evaluateGeometryIrImpl(geometry_ir: GeometryIr, *, render_fn: RenderFn, error_fn: ErrorFn) -> float:
    """Render and score a Geometry-IR chain."""

    return float(error_fn(render_fn(_clone_ir(geometry_ir))))


def optimizeGeometryIrSequentiallyImpl(
    geometry_ir: GeometryIr,
    *,
    render_fn: RenderFn,
    error_fn: ErrorFn,
    candidate_provider: CandidateProvider | None = None,
    min_improvement: float = 1e-9,
) -> dict[str, Any]:
    """Optimize a Geometry-IR chain element by element.

    For each IR element all candidates are scored against the current accepted
    chain. Only the best strictly improving candidate is committed before moving
    to the next element; regressions and ties are rejected. The returned step log
    uses the stable PR-R3 fields ``step_index``, ``element``, ``best_delta`` and
    ``accepted``.
    """

    current_ir = _clone_ir(geometry_ir)
    provider = candidate_provider or _default_candidate_provider
    current_error = evaluateGeometryIrImpl(current_ir, render_fn=render_fn, error_fn=error_fn)
    initial_error = current_error
    steps: list[dict[str, object]] = []

    for step_index, element in enumerate(list(current_ir)):
        error_before = current_error
        best_error = current_error
        best_ir = current_ir

        for candidate_element in provider(copy.deepcopy(element), _clone_ir(current_ir), step_index):
            probe_ir = _with_element(current_ir, step_index, candidate_element)
            candidate_error = evaluateGeometryIrImpl(probe_ir, render_fn=render_fn, error_fn=error_fn)
            if candidate_error < best_error - min_improvement:
                best_error = candidate_error
                best_ir = probe_ir

        accepted = best_error < error_before - min_improvement
        if accepted:
            current_ir = best_ir
            current_error = best_error

        steps.append(
            {
                "step_index": step_index,
                "element": _element_name(element),
                "best_delta": float(error_before - best_error) if accepted else 0.0,
                "accepted": accepted,
                "error_before": float(error_before),
                "error_after": float(current_error),
            }
        )

    return {
        "mode": "elementwise_geometry_ir",
        "geometry_ir": current_ir,
        "initial_error": float(initial_error),
        "final_error": float(current_error),
        "steps": steps,
    }


def selectGeometryIrForRenderingImpl(params: dict[str, Any]) -> GeometryIr:
    """Return the IR chain that should be rendered by the standard path.

    Optimized elementwise results take precedence. A one-shot chain is accepted
    only when the caller explicitly marks it as an emergency mode, preventing
    implicit direct-SVG/one-shot behavior from becoming the default again.
    """

    optimized = params.get("optimized_geometry_ir")
    if isinstance(optimized, list) and optimized:
        params["geometry_phase_mode"] = "elementwise_geometry_ir"
        return optimized

    geometry_ir = params.get("geometry_ir")
    if isinstance(geometry_ir, list) and geometry_ir:
        params.setdefault("geometry_phase_mode", "elementwise_geometry_ir")
        return geometry_ir

    emergency_ir = params.get("one_shot_emergency_geometry_ir")
    if params.get("allow_one_shot_emergency") is True and isinstance(emergency_ir, list) and emergency_ir:
        params["geometry_phase_mode"] = "one_shot_emergency"
        return emergency_ir

    params.setdefault("geometry_phase_mode", "no_geometry_ir")
    return []
