"""AC08 adaptive lock helpers extracted from the converter monolith."""

from __future__ import annotations

import math


_ADAPTIVE_STATE_KEY = "_ac08_adaptive_phase2_state"
_ADAPTIVE_CORRIDOR_KEYS = (
    "ac08_phase2_cx_min",
    "ac08_phase2_cx_max",
    "ac08_phase2_cy_min",
    "ac08_phase2_cy_max",
)


def activateAc08AdaptiveLocksImpl(
    params: dict,
    logs: list[str],
    *,
    full_err: float,
    reason: str,
) -> bool:
    """Activate a narrow AC0838 phase-2 unlock corridor when stagnation is detected."""
    symbol_name = str(params.get("badge_symbol_name", "")).upper()
    if symbol_name != "AC0838":
        return False
    if str(params.get("text_mode", "")).lower() != "voc":
        return False
    if not bool(params.get("circle_enabled", True)):
        return False
    if params.get(_ADAPTIVE_STATE_KEY):
        return False

    try:
        full_err_value = float(full_err)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(full_err_value) or full_err_value < 18.0:
        return False

    original_lock_cx = bool(params.get("lock_circle_cx", False))
    original_lock_cy = bool(params.get("lock_circle_cy", False))

    cx = float(params.get("cx", 0.0))
    cy = float(params.get("cy", 0.0))
    unlock_span = max(0.75, min(2.0, float(params.get("stroke_circle", 1.0)) * 1.5))
    corridor = {
        "ac08_phase2_cx_min": cx - unlock_span,
        "ac08_phase2_cx_max": cx + unlock_span,
        "ac08_phase2_cy_min": cy - unlock_span,
        "ac08_phase2_cy_max": cy + unlock_span,
    }
    params.update(corridor)
    params["lock_circle_cx"] = False
    params["lock_circle_cy"] = False
    params["cx"] = float(max(corridor["ac08_phase2_cx_min"], min(corridor["ac08_phase2_cx_max"], cx + 0.25)))
    params["cy"] = float(max(corridor["ac08_phase2_cy_min"], min(corridor["ac08_phase2_cy_max"], cy - 0.25)))

    original_lock_arm_center = bool(params.get("lock_arm_center_to_circle", False))
    if params.get("arm_enabled") and original_lock_arm_center:
        params["lock_arm_center_to_circle"] = False

    original_lock_stem_center = bool(params.get("lock_stem_center_to_circle", False))
    if params.get("stem_enabled") and original_lock_stem_center:
        params["lock_stem_center_to_circle"] = False

    params[_ADAPTIVE_STATE_KEY] = {
        "lock_circle_cx": original_lock_cx,
        "lock_circle_cy": original_lock_cy,
        "lock_arm_center_to_circle": original_lock_arm_center,
        "lock_stem_center_to_circle": original_lock_stem_center,
        "unlock_baseline_error": full_err_value,
    }
    logs.append(
        "adaptive_unlock_applied: phase=2 family=AC0838 "
        f"(reason={reason}, full_err={full_err_value:.3f}, "
        f"cx_range=[{corridor['ac08_phase2_cx_min']:.3f},{corridor['ac08_phase2_cx_max']:.3f}], "
        f"cy_range=[{corridor['ac08_phase2_cy_min']:.3f},{corridor['ac08_phase2_cy_max']:.3f}])"
    )
    return True


def releaseAc08AdaptiveLocksImpl(
    params: dict,
    logs: list[str],
    *,
    reason: str,
    current_error: float,
) -> bool:
    """Re-apply AC0838 phase-2 locks once the fallback round has completed."""
    state = params.get(_ADAPTIVE_STATE_KEY)
    if not isinstance(state, dict):
        return False

    baseline_error = state.get("unlock_baseline_error")
    try:
        baseline_error_value = float(baseline_error)
    except (TypeError, ValueError):
        baseline_error_value = float("inf")
    try:
        current_error_value = float(current_error)
    except (TypeError, ValueError):
        current_error_value = float("inf")

    relock_due_to_end = reason in {"validation_end", "best_state_restore"}
    relock_due_to_improvement = (
        math.isfinite(current_error_value)
        and math.isfinite(baseline_error_value)
        and current_error_value <= (baseline_error_value * 0.92)
    )
    if not relock_due_to_end and not relock_due_to_improvement:
        return False

    for key in ("lock_circle_cx", "lock_circle_cy", "lock_arm_center_to_circle", "lock_stem_center_to_circle"):
        if key in state:
            params[key] = bool(state.get(key, False))
    params.pop(_ADAPTIVE_STATE_KEY, None)
    for key in _ADAPTIVE_CORRIDOR_KEYS:
        params.pop(key, None)
    logs.append(
        "adaptive_relock_applied: phase=1 restored "
        f"(reason={reason}, current_error={current_error_value:.3f})"
    )
    return True
