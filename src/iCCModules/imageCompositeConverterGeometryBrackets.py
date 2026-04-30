"""Extracted circle bracket optimization helpers for imageCompositeConverter."""

from __future__ import annotations

import math
from collections.abc import Callable

def optimizeCircleCenterBracketImpl(
    img_orig: object,
    params: dict[str, object],
    logs: list[str],
    *,
    snap_half_fn: Callable[[float], float],
    clip_scalar_fn: Callable[[float, float, float], float],
    element_error_for_circle_radius_fn: Callable[[object, dict[str, object], float], float],
    reanchor_arm_to_circle_edge_fn: Callable[[dict[str, object], float], None],
) -> bool:
    if not params.get("circle_enabled", True):
        return False

    h, w = img_orig.shape[:2]
    current_cx = float(params.get("cx", -1.0))
    current_cy = float(params.get("cy", -1.0))
    current_r = float(params.get("r", 0.0))
    if current_r <= 0.0 or current_cx < 0.0 or current_cy < 0.0:
        return False

    lock_cx = bool(params.get("lock_circle_cx", False))
    lock_cy = bool(params.get("lock_circle_cy", False))
    if lock_cx and lock_cy:
        return False
    effective_lock_cx = lock_cx
    effective_lock_cy = lock_cy
    collapsed_axis_reasons: list[str] = []

    max_shift = max(1.0, float(min(w, h)) * 0.16)
    x_low = snap_half_fn(max(0.0, current_cx - max_shift))
    x_high = snap_half_fn(min(float(w - 1), current_cx + max_shift))
    y_low = snap_half_fn(max(0.0, current_cy - max_shift))
    y_high = snap_half_fn(min(float(h - 1), current_cy + max_shift))

    # Keep center-search candidates compatible with the semantic radius floor.
    # Otherwise the center optimizer can drift toward an edge, and later
    # clamp-to-canvas steps will silently collapse the circle radius.
    stroke = max(0.0, float(params.get("stroke_circle", 0.0)))
    required_radius = float(
        max(
            1.0,
            float(params.get("min_circle_radius", 1.0)),
            float(params.get("circle_radius_lower_bound_px", 1.0)),
        )
    )
    has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
    if has_connector:
        required_radius = max(required_radius, current_r * 0.90)

    required_clearance = required_radius + (stroke / 2.0)
    if not bool(params.get("allow_circle_overflow", False)):
        cx_min = snap_half_fn(max(0.0, required_clearance))
        cx_max = snap_half_fn(min(float(w - 1), float(w) - required_clearance))
        cy_min = snap_half_fn(max(0.0, required_clearance))
        cy_max = snap_half_fn(min(float(h - 1), float(h) - required_clearance))
        x_low = max(x_low, cx_min)
        x_high = min(x_high, cx_max)
        y_low = max(y_low, cy_min)
        y_high = min(y_high, cy_max)
        if x_low >= x_high:
            effective_lock_cx = True
            collapsed_axis_reasons.append("x-axis collapsed after radius-clearance corridor")
        if y_low >= y_high:
            effective_lock_cy = True
            collapsed_axis_reasons.append("y-axis collapsed after radius-clearance corridor")
        if effective_lock_cx and effective_lock_cy:
            if collapsed_axis_reasons:
                logs.append("circle: Mittelpunkt-Bracketing abgebrochen (" + "; ".join(dict.fromkeys(collapsed_axis_reasons)) + ")")
            return False

    # Text-on-circle connector badges are especially sensitive to center drift:
    # keep the search localized around the template center when available.
    has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
    has_text = bool(params.get("draw_text", False))
    if has_connector and has_text and "template_circle_cx" in params and "template_circle_cy" in params:
        template_cx = float(params.get("template_circle_cx", current_cx))
        template_cy = float(params.get("template_circle_cy", current_cy))
        stroke = float(params.get("stroke_circle", 1.0))
        arm_x1 = float(params.get("arm_x1", template_cx))
        arm_x2 = float(params.get("arm_x2", template_cx))
        is_vertical_connector = abs(arm_x1 - arm_x2) <= max(0.25, stroke * 0.6)
        x_window = max(0.75, stroke * 1.5)
        y_window = max(0.75, stroke * 1.5)
        if is_vertical_connector:
            x_window = max(0.25, stroke * 0.25)
            y_window = max(0.75, stroke * 1.0)
        x_low = max(x_low, snap_half_fn(template_cx - x_window))
        x_high = min(x_high, snap_half_fn(template_cx + x_window))
        y_low = max(y_low, snap_half_fn(template_cy - y_window))
        y_high = min(y_high, snap_half_fn(template_cy + y_window))
        if x_low >= x_high:
            effective_lock_cx = True
            collapsed_axis_reasons.append("x-axis collapsed by template-centered window")
        if y_low >= y_high:
            effective_lock_cy = True
            collapsed_axis_reasons.append("y-axis collapsed by template-centered window")
        if effective_lock_cx and effective_lock_cy:
            if collapsed_axis_reasons:
                logs.append("circle: Mittelpunkt-Bracketing abgebrochen (" + "; ".join(dict.fromkeys(collapsed_axis_reasons)) + ")")
            return False

    if collapsed_axis_reasons:
        logs.append(
            "circle: Mittelpunkt-Bracketing Achse fixiert ("
            + "; ".join(dict.fromkeys(collapsed_axis_reasons))
            + ")"
        )

    evaluations: dict[tuple[float, float], float] = {}

    def eval_center(cx_value: float, cy_value: float) -> float:
        cx_snap = snap_half_fn(float(clip_scalar_fn(cx_value, 0.0, float(w - 1))))
        cy_snap = snap_half_fn(float(clip_scalar_fn(cy_value, 0.0, float(h - 1))))
        key = (cx_snap, cy_snap)
        if key not in evaluations:
            probe = dict(params)
            probe["cx"] = cx_snap
            probe["cy"] = cy_snap
            evaluations[key] = float(element_error_for_circle_radius_fn(img_orig, probe, current_r))
        return evaluations[key]

    def optimize_axis(low: float, high: float, fixed: float, axis: str) -> float:
        if high - low < 0.05:
            return snap_half_fn((low + high) / 2.0)
        mid = snap_half_fn((low + high) / 2.0)
        max_iterations = int(max(1, params.get("circle_center_bracket_iterations", 8)))
        for _ in range(max_iterations):
            if axis == "x":
                low_err = eval_center(low, fixed)
                mid_err = eval_center(mid, fixed)
                high_err = eval_center(high, fixed)
            else:
                low_err = eval_center(fixed, low)
                mid_err = eval_center(fixed, mid)
                high_err = eval_center(fixed, high)

            if not all(math.isfinite(v) for v in (low_err, mid_err, high_err)):
                return mid

            if mid_err <= low_err and mid_err <= high_err:
                if low_err <= high_err:
                    high = mid
                else:
                    low = mid
            elif low_err <= mid_err and low_err <= high_err:
                high = mid
            else:
                low = mid

            if high - low < 0.05:
                break
            next_mid = snap_half_fn((low + high) / 2.0)
            if abs(next_mid - mid) < 0.02:
                break
            mid = next_mid
        points = [low, mid, high]
        if axis == "x":
            return min(points, key=lambda v: eval_center(v, fixed))
        return min(points, key=lambda v: eval_center(fixed, v))

    best_cx = current_cx
    best_cy = current_cy
    if not effective_lock_cx:
        best_cx = optimize_axis(x_low, x_high, current_cy, "x")
    if not effective_lock_cy:
        best_cy = optimize_axis(y_low, y_high, best_cx, "y")

    best_err = eval_center(best_cx, best_cy)
    if not math.isfinite(best_err):
        logs.append("circle: Mittelpunkt-Bracketing abgebrochen wegen nicht-finitem Fehler")
        return False

    if abs(best_cx - current_cx) < 0.02 and abs(best_cy - current_cy) < 0.02:
        logs.append(
            f"circle: Mittelpunkt-Bracketing keine relevante Änderung (cx={current_cx:.3f}, cy={current_cy:.3f}, best_err={best_err:.3f})"
        )
        return False

    params["cx"] = best_cx
    params["cy"] = best_cy
    if params.get("arm_enabled"):
        reanchor_arm_to_circle_edge_fn(params, current_r)
    if params.get("stem_enabled"):
        params["stem_top"] = float(params.get("cy", 0.0)) + current_r
        if bool(params.get("lock_stem_center_to_circle", False)):
            stem_w = float(params.get("stem_width", 1.0))
            params["stem_x"] = snap_half_fn(max(0.0, min(float(w) - stem_w, best_cx - (stem_w / 2.0))))

    logs.append(
        f"circle: Mittelpunkt-Bracketing cx {current_cx:.3f}->{best_cx:.3f}, cy {current_cy:.3f}->{best_cy:.3f} (best_err={best_err:.3f})"
    )
    return True


def optimizeCircleRadiusBracketImpl(
    img_orig: object,
    params: dict[str, object],
    logs: list[str],
    *,
    clip_scalar_fn: Callable[[float, float, float], float],
    snap_half_fn: Callable[[float], float],
    element_error_for_circle_radius_fn: Callable[[object, dict[str, object], float], float],
    select_circle_radius_plateau_candidate_fn: Callable[
        [object, dict[str, object], dict[float, float], float], tuple[float, float, float]
    ],
    reanchor_arm_to_circle_edge_fn: Callable[[dict[str, object], float], None],
) -> bool:
    if not params.get("circle_enabled", True):
        return False

    h, w = img_orig.shape[:2]
    current = float(params.get("r", 0.0))
    if current <= 0.0:
        return False

    min_dim = float(min(w, h))
    low_bound = max(1.0, min_dim * 0.14)
    low_bound = max(low_bound, float(params.get("min_circle_radius", 1.0)))
    low_bound = max(low_bound, float(params.get("circle_radius_lower_bound_px", 1.0)))
    has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
    if has_connector:
        template_r = float(params.get("template_circle_radius", current))
        low_bound = max(low_bound, template_r * 0.88)
        low_bound = max(low_bound, current * 0.90)
    if min_dim <= 22.0:
        low_bound = max(low_bound, current * 0.9)
    allow_overflow = bool(params.get("allow_circle_overflow", False))
    high_bound = min_dim * 0.48
    if allow_overflow:
        high_bound = max(high_bound, float(max(w, h)) * 1.25, low_bound + 0.5)
    if "max_circle_radius" in params:
        high_bound = min(high_bound, float(params.get("max_circle_radius", high_bound)))
    if not has_connector:
        low_bound = max(low_bound, current - 1.0)
        high_bound = min(high_bound, current + 1.0)
    if not low_bound < high_bound:
        return False

    low = math.floor(low_bound * 2.0) / 2.0
    high = math.ceil(high_bound * 2.0) / 2.0
    low = float(clip_scalar_fn(low, low_bound, high_bound))
    high = float(clip_scalar_fn(high, low_bound, high_bound))
    mid = snap_half_fn(float(clip_scalar_fn(current, low, high)))
    mid = float(clip_scalar_fn(mid, low, high))
    if high - low < 0.05:
        return False

    evaluations: dict[float, float] = {}

    def eval_radius(radius: float) -> float:
        clipped = float(clip_scalar_fn(radius, low_bound, high_bound))
        snapped = float(round(clipped, 3))
        if snapped not in evaluations:
            try:
                evaluations[snapped] = float(element_error_for_circle_radius_fn(img_orig, params, snapped))
            except Exception:
                evaluations[snapped] = float("inf")
        return evaluations[snapped]

    for _ in range(12):
        low_err = eval_radius(low)
        mid_err = eval_radius(mid)
        high_err = eval_radius(high)
        if not all(math.isfinite(v) for v in (low_err, mid_err, high_err)):
            if not math.isfinite(high_err) and math.isfinite(mid_err):
                high = mid
                continue
            if not math.isfinite(low_err) and math.isfinite(mid_err):
                low = mid
                continue
            logs.append(
                "circle: Radius-Bracketing abgebrochen wegen nicht-finiten Fehlern "
                + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in sorted(evaluations.items()))
            )
            return False

        if mid_err <= low_err and mid_err <= high_err:
            if low_err <= high_err:
                high = mid
            else:
                low = mid
        elif low_err <= mid_err and low_err <= high_err:
            high = mid
        else:
            low = mid

        if high - low < 0.05:
            break
        next_mid = snap_half_fn((low + high) / 2.0)
        if abs(next_mid - mid) < 0.02:
            break
        mid = next_mid

    best_r, best_err, best_full_err = select_circle_radius_plateau_candidate_fn(img_orig, params, evaluations, current)
    candidate_dump = ", ".join(f"{v:.3f}->{e:.3f}" for v, e in sorted(evaluations.items()))
    if abs(best_r - current) < 0.02:
        logs.append(
            f"circle: Radius-Bracketing keine relevante Änderung (r: {current:.3f}, best_err={best_err:.3f}, full_err={best_full_err:.3f}); Kandidaten="
            + candidate_dump
        )
        return False

    old_r = current
    params["r"] = best_r
    if params.get("arm_enabled"):
        reanchor_arm_to_circle_edge_fn(params, best_r)
        ax1 = float(params.get("arm_x1", 0.0))
        ay1 = float(params.get("arm_y1", 0.0))
        ax2 = float(params.get("arm_x2", 0.0))
        ay2 = float(params.get("arm_y2", 0.0))
        if abs(ax1 - ax2) < 1e-6:
            cx = float(params.get("cx", ax1))
            cy = float(params.get("cy", 0.0))
            top_edge = cy - best_r
            bottom_edge = cy + best_r
            params["arm_x1"] = cx
            params["arm_x2"] = cx
            if ay1 <= ay2:
                params["arm_y2"] = top_edge
            else:
                params["arm_y1"] = bottom_edge
    if params.get("stem_enabled"):
        params["stem_top"] = float(params.get("cy", 0.0)) + best_r

    logs.append(
        f"circle: Radius-Bracketing r {old_r:.3f}->{best_r:.3f} (best_err={best_err:.3f}, full_err={best_full_err:.3f}); Kandidaten="
        + candidate_dump
    )
    return True
