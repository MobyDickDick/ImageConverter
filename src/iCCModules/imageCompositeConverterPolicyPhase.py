"""Final policy-phase helpers for geometry-chain conversion decisions.

The geometry chain must run before aliases, sample/reference choices, and guards
are allowed to make the final rendering decision.  This module keeps those
late-stage decisions explicit in ``params`` instead of hiding them in individual
rendering branches.
"""

from __future__ import annotations

from typing import Any

GeometryIr = list[dict[str, object]]


def _as_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def summarizeGeometryPhaseResultImpl(params: dict[str, Any], geometry_ir: GeometryIr) -> dict[str, object]:
    """Build the stable geometry-phase summary consumed by final policies."""

    mode = str(params.get("geometry_phase_mode") or "no_geometry_ir")
    return {
        "mode": mode,
        "has_geometry_ir": bool(geometry_ir),
        "element_count": len(geometry_ir),
    }


def applyPolicyPhaseAfterGeometryImpl(params: dict[str, Any], geometry_ir: GeometryIr) -> GeometryIr:
    """Apply guards/reference policies after the geometry phase has completed.

    The function records three PR-R4 fields in ``params``:
    ``geometry_phase_result``, ``policy_phase_decision`` and
    ``override_reason``.  The returned IR is the geometry chain that remains
    eligible for rendering after the policy phase.
    """

    phase_result = summarizeGeometryPhaseResultImpl(params, geometry_ir)
    params["geometry_phase_result"] = phase_result

    guard_reason = params.get("policy_guard_block_reason")
    if not guard_reason and params.get("contract_status") == "insufficient_description":
        guard_reason = "description_contract_insufficient"
    if not guard_reason and params.get("mode") == "manual_review":
        guard_reason = "manual_review_guard"
    if guard_reason:
        params["policy_phase_decision"] = "guard_blocks"
        params["override_reason"] = str(guard_reason)
        return []

    comparison = params.get("policy_sample_comparison")
    if isinstance(comparison, dict):
        geometry_error = _as_float(comparison.get("geometry_error"))
        sample_error = _as_float(comparison.get("sample_error"))
        if sample_error is not None and geometry_error is not None and sample_error <= geometry_error:
            params["policy_phase_decision"] = "sample_wins"
            params["override_reason"] = "sample_error_not_worse_than_geometry"
            return []

    if params.get("prefer_sample_reference") is True and params.get("top_source_ref"):
        params["policy_phase_decision"] = "sample_wins"
        params["override_reason"] = "explicit_sample_reference_preference"
        return []

    if geometry_ir:
        params["policy_phase_decision"] = "geometry_wins"
        params["override_reason"] = None
        return geometry_ir

    params["policy_phase_decision"] = "no_geometry"
    params["override_reason"] = "no_geometry_ir_available"
    return []
