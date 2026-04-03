"""Extracted circle-radius optimization helpers for imageCompositeConverter."""

from __future__ import annotations

import math
from collections.abc import Callable


def elementErrorForCircleRadiusImpl(
    img_orig: object,
    params: dict[str, object],
    radius_value: float,
    *,
    clip_scalar_fn: Callable[[float, float, float], float],
    clamp_circle_inside_canvas_fn: Callable[[dict[str, object], int, int], dict[str, object]],
    reanchor_arm_to_circle_edge_fn: Callable[[dict[str, object], float], None],
    generate_badge_svg_fn: Callable[[int, int, dict[str, object]], str],
    element_only_params_fn: Callable[[dict[str, object], str], dict[str, object]],
    fit_to_original_size_fn: Callable[[object, object], object],
    render_svg_to_numpy_fn: Callable[[str, int, int], object],
    extract_badge_element_mask_fn: Callable[[object, dict[str, object], str], object],
    element_match_error_fn: Callable[..., float],
) -> float:
    h, w = img_orig.shape[:2]
    if not params.get("circle_enabled", True):
        return float("inf")

    probe = dict(params)
    min_r = float(
        max(
            1.0,
            float(probe.get("min_circle_radius", 1.0)),
            float(probe.get("circle_radius_lower_bound_px", 1.0)),
        )
    )
    max_r = max(min_r, (float(min(w, h)) * 0.48))
    if bool(probe.get("allow_circle_overflow", False)):
        max_r = max(max_r, float(max(w, h)) * 1.25, min_r + 0.5)
    probe["r"] = float(clip_scalar_fn(radius_value, min_r, max_r))
    probe = clamp_circle_inside_canvas_fn(probe, w, h)

    if probe.get("arm_enabled"):
        reanchor_arm_to_circle_edge_fn(probe, float(probe["r"]))

    if probe.get("stem_enabled"):
        probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

    elem_svg = generate_badge_svg_fn(w, h, element_only_params_fn(probe, "circle"))
    elem_render = fit_to_original_size_fn(img_orig, render_svg_to_numpy_fn(elem_svg, w, h))
    if elem_render is None:
        return float("inf")

    source_mask_params = dict(params)
    source_mask_params["r"] = max(float(params.get("r", 0.0)), float(probe["r"]))
    if source_mask_params.get("arm_enabled"):
        reanchor_arm_to_circle_edge_fn(source_mask_params, float(source_mask_params["r"]))
    if source_mask_params.get("stem_enabled"):
        source_mask_params["stem_top"] = float(source_mask_params.get("cy", 0.0)) + float(source_mask_params["r"])

    mask_orig = extract_badge_element_mask_fn(img_orig, source_mask_params, "circle")
    if mask_orig is None:
        return float("inf")
    mask_svg = extract_badge_element_mask_fn(elem_render, probe, "circle")
    if mask_svg is None:
        return float("inf")

    return element_match_error_fn(
        img_orig,
        elem_render,
        probe,
        "circle",
        mask_orig=mask_orig,
        mask_svg=mask_svg,
    )


def fullBadgeErrorForCircleRadiusImpl(
    img_orig: object,
    params: dict[str, object],
    radius_value: float,
    *,
    clip_scalar_fn: Callable[[float, float, float], float],
    clamp_circle_inside_canvas_fn: Callable[[dict[str, object], int, int], dict[str, object]],
    reanchor_arm_to_circle_edge_fn: Callable[[dict[str, object], float], None],
    generate_badge_svg_fn: Callable[[int, int, dict[str, object]], str],
    fit_to_original_size_fn: Callable[[object, object], object],
    render_svg_to_numpy_fn: Callable[[str, int, int], object],
    calculate_error_fn: Callable[[object, object], float],
) -> float:
    h, w = img_orig.shape[:2]
    if not params.get("circle_enabled", True):
        return float("inf")

    probe = dict(params)
    min_r = float(
        max(
            1.0,
            float(probe.get("min_circle_radius", 1.0)),
            float(probe.get("circle_radius_lower_bound_px", 1.0)),
        )
    )
    max_r = max(min_r, (float(min(w, h)) * 0.48))
    if bool(probe.get("allow_circle_overflow", False)):
        max_r = max(max_r, float(max(w, h)) * 1.25, min_r + 0.5)
    probe["r"] = float(clip_scalar_fn(radius_value, min_r, max_r))
    probe = clamp_circle_inside_canvas_fn(probe, w, h)

    if probe.get("arm_enabled"):
        reanchor_arm_to_circle_edge_fn(probe, float(probe["r"]))

    if probe.get("stem_enabled"):
        probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

    render = fit_to_original_size_fn(img_orig, render_svg_to_numpy_fn(generate_badge_svg_fn(w, h, probe), w, h))
    if render is None:
        return float("inf")
    return float(calculate_error_fn(img_orig, render))


def selectCircleRadiusPlateauCandidateImpl(
    img_orig: object,
    params: dict[str, object],
    evaluations: dict[float, float],
    current_radius: float,
    *,
    clip_scalar_fn: Callable[[float, float, float], float],
    snap_half_fn: Callable[[float], float],
    full_badge_error_for_circle_radius_fn: Callable[[object, dict[str, object], float], float],
    element_error_for_circle_radius_fn: Callable[[object, dict[str, object], float], float],
) -> tuple[float, float, float]:
    finite = sorted((float(radius), float(err)) for radius, err in evaluations.items() if math.isfinite(err))
    if not finite:
        return current_radius, float("inf"), float("inf")

    best_radius, best_err = min(finite, key=lambda pair: pair[1])
    plateau_eps = max(0.06, best_err * 0.02)
    plateau = [(radius, err) for radius, err in finite if err <= best_err + plateau_eps]
    if not plateau:
        try:
            full_err = float(full_badge_error_for_circle_radius_fn(img_orig, params, best_radius))
        except Exception:
            full_err = float("inf")
        return best_radius, best_err, full_err

    plateau_mid = snap_half_fn((plateau[0][0] + plateau[-1][0]) / 2.0)
    candidate_radii = {best_radius, plateau_mid}
    if len(plateau) >= 2:
        candidate_radii.add(plateau[-1][0])

    min_r = float(
        max(
            1.0,
            params.get("min_circle_radius", 1.0),
            params.get("circle_radius_lower_bound_px", 1.0),
        )
    )
    max_r = float(params.get("max_circle_radius", max(radius for radius, _err in finite)))
    if bool(params.get("allow_circle_overflow", False)):
        max_r = max(max_r, min_r + 0.5)
    bounded_candidates = sorted(float(clip_scalar_fn(snap_half_fn(float(radius)), min_r, max_r)) for radius in candidate_radii)

    choice_pool: list[tuple[float, float, float, float]] = []
    for radius in bounded_candidates:
        if radius in evaluations:
            elem_err = float(evaluations[radius])
        else:
            try:
                elem_err = float(element_error_for_circle_radius_fn(img_orig, params, radius))
            except Exception:
                elem_err = float("inf")
        try:
            full_err = float(full_badge_error_for_circle_radius_fn(img_orig, params, radius))
        except Exception:
            full_err = float("inf")
        if not math.isfinite(elem_err) and not math.isfinite(full_err):
            continue
        distance_to_mid = abs(radius - plateau_mid)
        choice_pool.append((radius, elem_err, full_err, distance_to_mid))

    if not choice_pool:
        return current_radius, best_err, float("inf")

    chosen_radius, chosen_elem_err, chosen_full_err, _distance_to_mid = min(
        choice_pool,
        key=lambda item: (
            round(item[2], 6),
            round(item[1], 6),
            item[3],
            abs(item[0] - current_radius),
        ),
    )
    return chosen_radius, chosen_elem_err, chosen_full_err
