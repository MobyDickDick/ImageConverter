"""Telemetry helpers for the geometry-chain conversion pipeline.

PR-R5 keeps runtime terminology and acceptance metrics in one place so callers
can distinguish the normal Geometry-IR chain from late policy choices and true
emergency/placeholder fallbacks.
"""

from __future__ import annotations

from typing import Any


_GEOMETRY_PHASE_LABELS = {
    "elementwise_geometry_ir": "geometry_chain.elementwise",
    "one_shot_emergency": "emergency.one_shot_geometry",
    "no_geometry_ir": "geometry_chain.unavailable",
}

_POLICY_PHASE_LABELS = {
    "geometry_wins": "policy.geometry_selected",
    "sample_wins": "policy.reference_selected",
    "guard_blocks": "policy.guard_blocked",
    "no_geometry": "policy.no_geometry_available",
}


def normalizeChainPhaseLabelImpl(phase: object, *, phase_type: str) -> str:
    """Return a stable, unambiguous label for a geometry-chain phase value."""

    raw = str(phase or "").strip()
    if phase_type == "geometry":
        return _GEOMETRY_PHASE_LABELS.get(raw, f"geometry_chain.{raw or 'unknown'}")
    if phase_type == "policy":
        return _POLICY_PHASE_LABELS.get(raw, f"policy.{raw or 'unknown'}")
    if phase_type == "fallback":
        lower = raw.lower()
        if "placeholder" in lower:
            return "emergency.placeholder_svg"
        if "sample" in lower or "reference" in lower:
            return "policy.reference_fallback"
        if lower:
            return f"emergency.{lower}"
        return "emergency.none"
    return raw or "unknown"


def _optimizer_steps(params: dict[str, Any], optimizer_result: dict[str, Any] | None) -> list[dict[str, object]]:
    if optimizer_result and isinstance(optimizer_result.get("steps"), list):
        return [step for step in optimizer_result["steps"] if isinstance(step, dict)]
    stored_result = params.get("geometry_ir_optimizer_result")
    if isinstance(stored_result, dict) and isinstance(stored_result.get("steps"), list):
        return [step for step in stored_result["steps"] if isinstance(step, dict)]
    stored_steps = params.get("geometry_ir_step_log")
    if isinstance(stored_steps, list):
        return [step for step in stored_steps if isinstance(step, dict)]
    return []


def _placeholder_emergency_used(params: dict[str, Any]) -> bool:
    if params.get("used_placeholder") is True or params.get("placeholder_emergency_used") is True:
        return True
    inspected_keys = (
        "status",
        "conversion_status",
        "fallback_render_mode",
        "render_mode",
        "override_reason",
        "policy_phase_decision",
    )
    return any("placeholder" in str(params.get(key, "")).lower() for key in inspected_keys)


def summarizeChainTelemetryImpl(
    params: dict[str, Any],
    optimizer_result: dict[str, Any] | None = None,
) -> dict[str, object]:
    """Summarize per-phase quality metrics for one conversion attempt.

    The returned payload is intentionally flat and JSON/log friendly.  Metrics
    include the elementwise step success rate, policy override state, and whether
    a placeholder emergency path was used.
    """

    steps = _optimizer_steps(params, optimizer_result)
    step_count = len(steps)
    accepted_count = sum(1 for step in steps if step.get("accepted") is True)
    step_success_rate = accepted_count / step_count if step_count else 0.0

    geometry_phase = str(params.get("geometry_phase_mode") or "no_geometry_ir")
    policy_decision = str(params.get("policy_phase_decision") or "no_geometry")
    override_reason = params.get("override_reason")
    placeholder_used = _placeholder_emergency_used(params)

    summary: dict[str, object] = {
        "geometry_phase": normalizeChainPhaseLabelImpl(geometry_phase, phase_type="geometry"),
        "geometry_phase_mode": geometry_phase,
        "policy_phase": normalizeChainPhaseLabelImpl(policy_decision, phase_type="policy"),
        "policy_phase_decision": policy_decision,
        "override_applied": bool(policy_decision and policy_decision != "geometry_wins"),
        "override_reason": None if override_reason is None else str(override_reason),
        "step_count": step_count,
        "step_accepted_count": accepted_count,
        "step_success_rate": round(step_success_rate, 6),
        "placeholder_emergency_used": placeholder_used,
    }

    if optimizer_result:
        for key in ("initial_error", "final_error"):
            if key in optimizer_result:
                summary[key] = float(optimizer_result[key])
    return summary


def aggregateChainTelemetryImpl(rows: list[dict[str, object]]) -> dict[str, object]:
    """Aggregate R5 acceptance metrics across multiple telemetry rows."""

    total = len(rows)
    if total == 0:
        return {
            "conversion_count": 0,
            "mean_step_success_rate": 0.0,
            "override_frequency": 0.0,
            "placeholder_emergency_rate": 0.0,
        }

    mean_success = sum(float(row.get("step_success_rate") or 0.0) for row in rows) / total
    override_count = sum(1 for row in rows if row.get("override_applied") is True)
    placeholder_count = sum(1 for row in rows if row.get("placeholder_emergency_used") is True)
    return {
        "conversion_count": total,
        "mean_step_success_rate": round(mean_success, 6),
        "override_frequency": round(override_count / total, 6),
        "placeholder_emergency_rate": round(placeholder_count / total, 6),
    }


def formatChainTelemetryLineImpl(telemetry: dict[str, object]) -> str:
    """Format a compact human-readable R5 telemetry log line."""

    fields = [
        ("geometry_phase", telemetry.get("geometry_phase")),
        ("policy_phase", telemetry.get("policy_phase")),
        ("step_success_rate", telemetry.get("step_success_rate")),
        ("overrides", telemetry.get("override_applied")),
        ("placeholder_emergency", telemetry.get("placeholder_emergency_used")),
    ]
    if telemetry.get("override_reason"):
        fields.append(("override_reason", telemetry.get("override_reason")))
    return "chain_telemetry: " + "; ".join(f"{key}={value}" for key, value in fields)
