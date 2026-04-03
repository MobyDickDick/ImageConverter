"""Stochastic/adaptive circle-search helper extraction."""

from __future__ import annotations

import dataclasses
import math


def stochasticSurvivorScalarImpl(
    current_value: float,
    low: float,
    high: float,
    evaluate,
    *,
    snap,
    seed: int,
    make_rng_fn,
    clip_scalar_fn,
    stochastic_seed_offset: int,
    iterations: int = 20,
) -> tuple[float, float, bool]:
    """Random 3-candidate survivor search for a scalar parameter."""
    cur = float(snap(float(clip_scalar_fn(current_value, low, high))))
    best_value = cur
    best_err = float(evaluate(best_value))
    if not math.isfinite(best_err):
        return best_value, best_err, False

    rng = make_rng_fn(int(seed) + int(stochastic_seed_offset))
    span = max(0.5, abs(high - low) * 0.22)
    improved = False
    stable_rounds = 0

    for _ in range(max(1, iterations)):
        candidates = [best_value]
        for _ in range(2):
            sample = float(clip_scalar_fn(rng.normal(best_value, span), low, high))
            candidates.append(float(snap(sample)))

        scored: list[tuple[float, float]] = []
        for cand in candidates:
            err = float(evaluate(cand))
            if math.isfinite(err):
                scored.append((cand, err))
        if not scored:
            continue
        scored.sort(key=lambda pair: pair[1])
        cand_best, cand_err = scored[0]
        if cand_err + 0.05 < best_err:
            best_value, best_err = cand_best, cand_err
            improved = True
            stable_rounds = 0
        else:
            stable_rounds += 1

        span = max(0.2, span * 0.90)
        if stable_rounds >= 6:
            break

    return best_value, best_err, improved


def optimizeCirclePoseStochasticSurvivorImpl(
    img_orig,
    params: dict,
    logs: list[str],
    *,
    snap_half_fn,
    clip_scalar_fn,
    make_rng_fn,
    circle_bounds_fn,
    element_error_for_circle_pose_fn,
    log_global_parameter_vector_fn,
    global_parameter_vector_cls,
    reanchor_arm_to_circle_edge_fn,
    stochastic_run_seed: int,
    stochastic_seed_offset: int,
    iterations: int = 24,
) -> bool:
    """Stochastic 3-candidate survivor search for circle pose."""
    if not params.get("circle_enabled", True):
        return False

    h, w = img_orig.shape[:2]
    log_global_parameter_vector_fn(logs, params, w, h, label="circle: survivor-start")
    x_low, x_high, y_low, y_high, r_low, r_high = circle_bounds_fn(params, w, h)
    current = (
        snap_half_fn(float(params.get("cx", (w - 1) / 2.0))),
        snap_half_fn(float(params.get("cy", (h - 1) / 2.0))),
        snap_half_fn(float(params.get("r", max(1.0, min(w, h) * 0.3)))),
    )
    lock_cx = bool(params.get("lock_circle_cx", False))
    lock_cy = bool(params.get("lock_circle_cy", False))
    rng = make_rng_fn(835 + int(stochastic_run_seed) + int(stochastic_seed_offset))

    def eval_pose(candidate: tuple[float, float, float]) -> float:
        cx, cy, rad = candidate
        return float(
            element_error_for_circle_pose_fn(
                img_orig,
                params,
                cx_value=cx,
                cy_value=cy,
                radius_value=rad,
            )
        )

    best = current
    best_err = eval_pose(best)
    if not math.isfinite(best_err):
        return False

    spread_xy = max(1.0, float(min(w, h)) * 0.10)
    spread_r = max(0.6, float(best[2]) * 0.18)
    improved = False
    stable_rounds = 0

    for _ in range(max(1, iterations)):
        candidates: list[tuple[tuple[float, float, float], float]] = [(best, best_err)]
        for _ in range(2):
            if lock_cx:
                cx = best[0]
            else:
                cx = snap_half_fn(float(clip_scalar_fn(rng.normal(best[0], spread_xy), x_low, x_high)))
            if lock_cy:
                cy = best[1]
            else:
                cy = snap_half_fn(float(clip_scalar_fn(rng.normal(best[1], spread_xy), y_low, y_high)))
            rad = snap_half_fn(float(clip_scalar_fn(rng.normal(best[2], spread_r), r_low, r_high)))
            cand = (cx, cy, rad)
            candidates.append((cand, eval_pose(cand)))

        finite = [pair for pair in candidates if math.isfinite(pair[1])]
        if not finite:
            continue
        finite.sort(key=lambda item: item[1])
        round_best, round_err = finite[0]
        if round_err + 0.05 < best_err:
            best, best_err = round_best, round_err
            improved = True
            stable_rounds = 0
        else:
            stable_rounds += 1

        spread_xy = max(0.4, spread_xy * 0.92)
        spread_r = max(0.35, spread_r * 0.90)
        if stable_rounds >= 7:
            break

    if not improved:
        logs.append("circle: Stochastic-Survivor keine relevante Verbesserung")
        return False

    updated_vector = global_parameter_vector_cls.fromParams(params)
    updated_vector = dataclasses.replace(updated_vector, cx=best[0], cy=best[1], r=best[2])
    params.update(updated_vector.applyToParams(params))
    if params.get("arm_enabled"):
        reanchor_arm_to_circle_edge_fn(params, best[2])
    if params.get("stem_enabled"):
        params["stem_top"] = float(params.get("cy", 0.0)) + best[2]
    log_global_parameter_vector_fn(logs, params, w, h, label="circle: survivor-final")
    logs.append(
        f"circle: Stochastic-Survivor übernommen (cx={best[0]:.3f}, cy={best[1]:.3f}, r={best[2]:.3f}, err={best_err:.3f})"
    )
    return True


def optimizeCirclePoseAdaptiveDomainImpl(
    img_orig,
    params: dict,
    logs: list[str],
    *,
    snap_half_fn,
    clip_scalar_fn,
    make_rng_fn,
    circle_bounds_fn,
    element_error_for_circle_pose_fn,
    log_global_parameter_vector_fn,
    global_parameter_vector_cls,
    reanchor_arm_to_circle_edge_fn,
    stochastic_run_seed: int,
    stochastic_seed_offset: int,
    rounds: int = 4,
    samples_per_round: int = 18,
) -> bool:
    """Adaptive random-domain search with iterative domain shrinking."""
    if not params.get("circle_enabled", True):
        return False

    h, w = img_orig.shape[:2]
    log_global_parameter_vector_fn(logs, params, w, h, label="circle: adaptive-start")
    x_low, x_high, y_low, y_high, r_low, r_high = circle_bounds_fn(params, w, h)
    lock_cx = bool(params.get("lock_circle_cx", False))
    lock_cy = bool(params.get("lock_circle_cy", False))

    current = (
        snap_half_fn(float(params.get("cx", (w - 1) / 2.0))),
        snap_half_fn(float(params.get("cy", (h - 1) / 2.0))),
        snap_half_fn(float(params.get("r", max(1.0, min(w, h) * 0.3)))),
    )

    def clamp_pose(candidate: tuple[float, float, float]) -> tuple[float, float, float]:
        cx, cy, rad = candidate
        if lock_cx:
            cx = current[0]
        else:
            cx = snap_half_fn(float(clip_scalar_fn(cx, x_low, x_high)))
        if lock_cy:
            cy = current[1]
        else:
            cy = snap_half_fn(float(clip_scalar_fn(cy, y_low, y_high)))
        rad = snap_half_fn(float(clip_scalar_fn(rad, r_low, r_high)))
        return cx, cy, rad

    cache: dict[tuple[float, float, float], float] = {}

    def eval_pose(candidate: tuple[float, float, float]) -> float:
        pose = clamp_pose(candidate)
        if pose not in cache:
            cache[pose] = float(
                element_error_for_circle_pose_fn(
                    img_orig,
                    params,
                    cx_value=pose[0],
                    cy_value=pose[1],
                    radius_value=pose[2],
                )
            )
        return cache[pose]

    best = clamp_pose(current)
    best_err = eval_pose(best)
    if not math.isfinite(best_err):
        return False

    domain = {
        "cx_low": x_low,
        "cx_high": x_high,
        "cy_low": y_low,
        "cy_high": y_high,
        "r_low": r_low,
        "r_high": r_high,
    }

    rng = make_rng_fn(2027 + int(stochastic_run_seed) + int(stochastic_seed_offset))
    improved = False
    flat_plateau_hits = 0

    logs.append(
        (
            "circle: Adaptive-Domain-Suche gestartet "
            f"(Möglichkeitsraum: cx=[{domain['cx_low']:.2f},{domain['cx_high']:.2f}], "
            f"cy=[{domain['cy_low']:.2f},{domain['cy_high']:.2f}], "
            f"r=[{domain['r_low']:.2f},{domain['r_high']:.2f}], "
            f"samples_pro_runde={max(8, int(samples_per_round))})"
        )
    )

    for round_index in range(max(1, rounds)):
        samples: list[tuple[tuple[float, float, float], float]] = [(best, best_err)]
        for _ in range(max(8, int(samples_per_round))):
            if lock_cx:
                cx = current[0]
            else:
                cx = float(rng.uniform(domain["cx_low"], domain["cx_high"]))
            if lock_cy:
                cy = current[1]
            else:
                cy = float(rng.uniform(domain["cy_low"], domain["cy_high"]))
            rad = float(rng.uniform(domain["r_low"], domain["r_high"]))
            pose = clamp_pose((cx, cy, rad))
            samples.append((pose, eval_pose(pose)))

        finite = [pair for pair in samples if math.isfinite(pair[1])]
        if not finite:
            continue
        finite.sort(key=lambda item: item[1])
        round_best, round_best_err = finite[0]

        plateau_eps = max(0.06, round_best_err * 0.02)
        plateau = [pose for pose, err in finite if err <= round_best_err + plateau_eps]
        if len(plateau) >= 4:
            flat_plateau_hits += 1

        plateau_points = plateau if plateau else [round_best]
        pmin_cx = min(p[0] for p in plateau_points)
        pmin_cy = min(p[1] for p in plateau_points)
        pmin_r = min(p[2] for p in plateau_points)
        pmax_cx = max(p[0] for p in plateau_points)
        pmax_cy = max(p[1] for p in plateau_points)
        pmax_r = max(p[2] for p in plateau_points)
        plateau_mid = clamp_pose(((pmin_cx + pmax_cx) / 2.0, (pmin_cy + pmax_cy) / 2.0, (pmin_r + pmax_r) / 2.0))
        plateau_mid_err = eval_pose(plateau_mid)

        candidate_best = round_best
        candidate_err = round_best_err
        if math.isfinite(plateau_mid_err) and plateau_mid_err < candidate_err:
            candidate_best = plateau_mid
            candidate_err = plateau_mid_err

        if candidate_err + 0.05 < best_err:
            best = candidate_best
            best_err = candidate_err
            improved = True

        logs.append(
            (
                f"circle: Runde {round_index + 1} random-samples={len(samples) - 1}, "
                f"Error-Minimum={best_err:.3f} bei "
                f"(cx={best[0]:.3f}, cy={best[1]:.3f}, r={best[2]:.3f})"
            )
        )
        round_vector = global_parameter_vector_cls.fromParams(params)
        round_vector = dataclasses.replace(round_vector, cx=best[0], cy=best[1], r=best[2])
        round_params = round_vector.applyToParams(params)
        log_global_parameter_vector_fn(logs, round_params, w, h, label=f"circle: Runde {round_index + 1}")

        shrink = 0.58
        if not lock_cx:
            half_span = max(0.5, float((domain["cx_high"] - domain["cx_low"]) * shrink * 0.5))
            focus = float(best[0] if len(plateau) <= 1 else (pmin_cx + pmax_cx) / 2.0)
            domain["cx_low"] = max(x_low, focus - half_span)
            domain["cx_high"] = min(x_high, focus + half_span)
        if not lock_cy:
            half_span = max(0.5, float((domain["cy_high"] - domain["cy_low"]) * shrink * 0.5))
            focus = float(best[1] if len(plateau) <= 1 else (pmin_cy + pmax_cy) / 2.0)
            domain["cy_low"] = max(y_low, focus - half_span)
            domain["cy_high"] = min(y_high, focus + half_span)
        half_span_r = max(0.5, float((domain["r_high"] - domain["r_low"]) * shrink * 0.5))
        focus_r = float(best[2] if len(plateau) <= 1 else (pmin_r + pmax_r) / 2.0)
        domain["r_low"] = max(r_low, focus_r - half_span_r)
        domain["r_high"] = min(r_high, focus_r + half_span_r)

        logs.append(
            (
                f"circle: Runde {round_index + 1} Möglichkeitsraum eingegrenzt auf "
                f"cx=[{domain['cx_low']:.2f},{domain['cx_high']:.2f}], "
                f"cy=[{domain['cy_low']:.2f},{domain['cy_high']:.2f}], "
                f"r=[{domain['r_low']:.2f},{domain['r_high']:.2f}]"
            )
        )

    if not improved:
        logs.append("circle: Adaptive-Domain-Suche keine relevante Verbesserung")
        return False

    updated_vector = global_parameter_vector_cls.fromParams(params)
    updated_vector = dataclasses.replace(updated_vector, cx=best[0], cy=best[1], r=best[2])
    params.update(updated_vector.applyToParams(params))
    if params.get("arm_enabled"):
        reanchor_arm_to_circle_edge_fn(params, best[2])
    if params.get("stem_enabled"):
        params["stem_top"] = float(params.get("cy", 0.0)) + best[2]
    log_global_parameter_vector_fn(logs, params, w, h, label="circle: adaptive-final")

    boundary_hit = (
        (not lock_cx and (abs(best[0] - x_low) <= 0.01 or abs(best[0] - x_high) <= 0.01))
        or (not lock_cy and (abs(best[1] - y_low) <= 0.01 or abs(best[1] - y_high) <= 0.01))
        or abs(best[2] - r_low) <= 0.01
        or abs(best[2] - r_high) <= 0.01
    )
    flat_hint = flat_plateau_hits >= 2
    logs.append(
        "circle: Adaptive-Domain-Suche übernommen "
        f"(cx={best[0]:.3f}, cy={best[1]:.3f}, r={best[2]:.3f}, err={best_err:.3f}, "
        f"rand_optimum={'ja' if boundary_hit else 'nein'}, flaches_optimum={'ja' if flat_hint else 'nein'})"
    )
    return True
