"""Circle-pose multistart optimization helper extraction."""

from __future__ import annotations

import math


def optimizeCirclePoseMultistartImpl(
    img_orig,
    params: dict,
    logs: list[str],
    *,
    clip_scalar_fn,
    snap_half_fn,
    circle_bounds_fn,
    element_error_for_circle_pose_fn,
    reanchor_arm_to_circle_edge_fn,
    optimize_circle_pose_adaptive_domain_fn,
    optimize_circle_pose_stochastic_survivor_fn,
) -> bool:
    """Jointly optimize circle center+radius via a compact multi-start grid."""
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

    shift = max(0.5, float(min(w, h)) * 0.08)
    radius_span = max(0.5, current_r * 0.12)
    _x_low, _x_high, _y_low, _y_high, min_r, max_r = circle_bounds_fn(params, w, h)

    fine_shift = min(1.0, shift)
    fine_radius = min(0.5, radius_span)

    if lock_cx:
        cx_candidates = [float(current_cx)]
    else:
        cx_candidates = [
            float(clip_scalar_fn(current_cx + offset, 0.0, float(w - 1)))
            for offset in (-shift, -fine_shift, 0.0, fine_shift, shift)
        ]
    if lock_cy:
        cy_candidates = [float(current_cy)]
    else:
        cy_candidates = [
            float(clip_scalar_fn(current_cy + offset, 0.0, float(h - 1)))
            for offset in (-shift, -fine_shift, 0.0, fine_shift, shift)
        ]

    r_candidates = [
        float(clip_scalar_fn(current_r + offset, min_r, max_r))
        for offset in (-radius_span, -fine_radius, 0.0, fine_radius, radius_span)
    ]

    evaluations: dict[tuple[float, float, float], float] = {}

    def evalPose(cx: float, cy: float, rad: float) -> float:
        key = (cx, cy, rad)
        if key not in evaluations:
            evaluations[key] = float(
                element_error_for_circle_pose_fn(
                    img_orig,
                    params,
                    cx_value=cx,
                    cy_value=cy,
                    radius_value=rad,
                )
            )
        return evaluations[key]

    best = (float(current_cx), float(current_cy), float(current_r))
    best_err = evalPose(*best)

    for cx in cx_candidates:
        for cy in cy_candidates:
            for rad in r_candidates:
                err = evalPose(cx, cy, rad)
                if math.isfinite(err) and err + 0.05 < best_err:
                    best = (cx, cy, rad)
                    best_err = err

    best_cx, best_cy, best_r = best
    if (
        abs(best_cx - current_cx) < 0.02
        and abs(best_cy - current_cy) < 0.02
        and abs(best_r - current_r) < 0.02
    ):
        logs.append(
            f"circle: Joint-Multistart keine relevante Änderung (cx={current_cx:.3f}, cy={current_cy:.3f}, r={current_r:.3f}, best_err={best_err:.3f})"
        )
        return False

    params["cx"] = best_cx
    params["cy"] = best_cy
    params["r"] = best_r
    if params.get("arm_enabled"):
        reanchor_arm_to_circle_edge_fn(params, best_r)
    if params.get("stem_enabled"):
        params["stem_top"] = float(params.get("cy", 0.0)) + best_r
        if bool(params.get("lock_stem_center_to_circle", False)):
            stem_w = float(params.get("stem_width", 1.0))
            params["stem_x"] = snap_half_fn(max(0.0, min(float(w) - stem_w, best_cx - (stem_w / 2.0))))

    logs.append(
        f"circle: Joint-Multistart cx {current_cx:.3f}->{best_cx:.3f}, cy {current_cy:.3f}->{best_cy:.3f}, r {current_r:.3f}->{best_r:.3f} (best_err={best_err:.3f})"
    )

    at_boundary = (
        (not lock_cx and (best_cx <= 0.01 or best_cx >= float(w - 1) - 0.01))
        or (not lock_cy and (best_cy <= 0.01 or best_cy >= float(h - 1) - 0.01))
        or abs(best_r - min_r) <= 0.01
        or abs(best_r - max_r) <= 0.01
    )
    if at_boundary:
        logs.append("circle: Joint-Multistart liegt am Rand; starte adaptive Domain-Suche")
        improved = optimize_circle_pose_adaptive_domain_fn(img_orig, params, logs)
        if not improved:
            logs.append("circle: Adaptive-Domain-Suche ohne Gewinn; fallback auf stochastic survivor")
            optimize_circle_pose_stochastic_survivor_fn(img_orig, params, logs)
    return True
