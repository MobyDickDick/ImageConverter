"""Extracted geometric extent/width bracket helpers for imageCompositeConverter."""

from __future__ import annotations

import math
from collections.abc import Callable


def elementErrorForExtentImpl(
    img_orig: object,
    params: dict[str, object],
    element: str,
    extent_value: float,
    *,
    clip_scalar_fn: Callable[[float, float, float], float],
    reanchor_arm_to_circle_edge_fn: Callable[[dict[str, object], float], None],
    generate_badge_svg_fn: Callable[[int, int, dict[str, object]], str],
    element_only_params_fn: Callable[[dict[str, object], str], dict[str, object]],
    fit_to_original_size_fn: Callable[[object, object], object],
    render_svg_to_numpy_fn: Callable[[str, int, int], object],
    extract_badge_element_mask_fn: Callable[[object, dict[str, object], str], object],
    element_match_error_fn: Callable[..., float],
) -> float:
    h, w = img_orig.shape[:2]
    probe = dict(params)

    if element == "stem" and probe.get("stem_enabled"):
        min_len = 1.0
        max_len = float(h)
        new_len = float(clip_scalar_fn(extent_value, min_len, max_len))
        center = (float(probe.get("stem_top", 0.0)) + float(probe.get("stem_bottom", 0.0))) / 2.0
        half = new_len / 2.0
        probe["stem_top"] = float(clip_scalar_fn(center - half, 0.0, float(h - 1)))
        probe["stem_bottom"] = float(clip_scalar_fn(center + half, probe["stem_top"] + 1.0, float(h)))
    elif element == "arm" and probe.get("arm_enabled"):
        x1 = float(probe.get("arm_x1", 0.0))
        y1 = float(probe.get("arm_y1", 0.0))
        x2 = float(probe.get("arm_x2", 0.0))
        y2 = float(probe.get("arm_y2", 0.0))
        dx = x2 - x1
        dy = y2 - y1
        cur_len = float(math.hypot(dx, dy))
        if cur_len <= 1e-6:
            return float("inf")
        new_len = float(clip_scalar_fn(extent_value, 1.0, float(max(w, h))))
        ux = dx / cur_len
        uy = dy / cur_len

        if probe.get("circle_enabled", True) and all(k in probe for k in ("cx", "cy", "r")):
            reanchor_arm_to_circle_edge_fn(probe, float(probe.get("r", 0.0)))
            ax1 = float(probe.get("arm_x1", x1))
            ay1 = float(probe.get("arm_y1", y1))
            ax2 = float(probe.get("arm_x2", x2))
            ay2 = float(probe.get("arm_y2", y2))

            cx = float(probe.get("cx", 0.0))
            cy = float(probe.get("cy", 0.0))
            d1 = float(math.hypot(ax1 - cx, ay1 - cy))
            d2 = float(math.hypot(ax2 - cx, ay2 - cy))

            if d1 <= d2:
                ix, iy = ax1, ay1
                probe["arm_x2"] = float(clip_scalar_fn(ix + (ux * new_len), 0.0, float(w - 1)))
                probe["arm_y2"] = float(clip_scalar_fn(iy + (uy * new_len), 0.0, float(h - 1)))
            else:
                ix, iy = ax2, ay2
                probe["arm_x1"] = float(clip_scalar_fn(ix - (ux * new_len), 0.0, float(w - 1)))
                probe["arm_y1"] = float(clip_scalar_fn(iy - (uy * new_len), 0.0, float(h - 1)))
        else:
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            half = new_len / 2.0
            probe["arm_x1"] = float(clip_scalar_fn(cx - (ux * half), 0.0, float(w - 1)))
            probe["arm_y1"] = float(clip_scalar_fn(cy - (uy * half), 0.0, float(h - 1)))
            probe["arm_x2"] = float(clip_scalar_fn(cx + (ux * half), 0.0, float(w - 1)))
            probe["arm_y2"] = float(clip_scalar_fn(cy + (uy * half), 0.0, float(h - 1)))
    else:
        return float("inf")

    elem_svg = generate_badge_svg_fn(w, h, element_only_params_fn(probe, element))
    elem_render = fit_to_original_size_fn(img_orig, render_svg_to_numpy_fn(elem_svg, w, h))
    if elem_render is None:
        return float("inf")

    mask_orig = extract_badge_element_mask_fn(img_orig, probe, element)
    if mask_orig is None:
        return float("inf")

    return element_match_error_fn(img_orig, elem_render, probe, element, mask_orig=mask_orig)


def optimizeElementExtentBracketImpl(
    img_orig: object,
    params: dict[str, object],
    element: str,
    logs: list[str],
    *,
    clip_scalar_fn: Callable[[float, float, float], float],
    snap_half_fn: Callable[[float], float],
    element_error_for_extent_fn: Callable[[object, dict[str, object], str, float], float],
    argmin_index_fn: Callable[[list[float]], int],
    stochastic_survivor_scalar_fn: Callable[..., tuple[float, float, bool]],
    reanchor_arm_to_circle_edge_fn: Callable[[dict[str, object], float], None],
) -> bool:
    h, w = img_orig.shape[:2]
    if element == "stem" and params.get("stem_enabled"):
        current = float(params.get("stem_bottom", 0.0)) - float(params.get("stem_top", 0.0))
        key_label = "stem_len"
        low_bound = 1.0
        high_bound = float(h)
        forced_abs_min = params.get("stem_len_min")
        if forced_abs_min is not None:
            low_bound = max(low_bound, float(forced_abs_min))
        forced_min_ratio = params.get("stem_len_min_ratio")
        if forced_min_ratio is not None:
            min_ratio = float(max(0.0, min(1.0, float(forced_min_ratio))))
            low_bound = max(low_bound, current * min_ratio)
        if h <= 15 and not bool(params.get("draw_text", True)):
            low_bound = max(low_bound, 5.5)
        is_bottom_anchored = float(params.get("stem_bottom", 0.0)) >= float(h) - 0.5
        if (
            forced_min_ratio is None
            and is_bottom_anchored
            and params.get("circle_enabled", True)
            and all(k in params for k in ("cy", "r"))
        ):
            min_ratio = float(params.get("stem_len_min_ratio", 0.65))
            low_bound = max(low_bound, current * max(0.0, min(1.0, min_ratio)))
            if h <= 15 and not bool(params.get("draw_text", True)):
                low_bound = max(low_bound, 5.5)
    elif element == "arm" and params.get("arm_enabled"):
        dx = float(params.get("arm_x2", 0.0)) - float(params.get("arm_x1", 0.0))
        dy = float(params.get("arm_y2", 0.0)) - float(params.get("arm_y1", 0.0))
        current = float(math.hypot(dx, dy))
        key_label = "arm_len"
        low_bound = 1.0
        high_bound = float(max(w, h))
        forced_abs_min = params.get("arm_len_min")
        if forced_abs_min is not None:
            low_bound = max(low_bound, float(forced_abs_min))
        forced_min_ratio = params.get("arm_len_min_ratio")
        if forced_min_ratio is not None:
            min_ratio = float(max(0.0, min(1.0, float(forced_min_ratio))))
            low_bound = max(low_bound, current * min_ratio)
        is_edge_anchored = any(
            (
                float(params.get(key, 0.0)) <= 0.5
                or float(params.get(key, 0.0)) >= float(limit) - 0.5
            )
            for key, limit in (
                ("arm_x1", w),
                ("arm_x2", w),
                ("arm_y1", h),
                ("arm_y2", h),
            )
        )
        if forced_min_ratio is None and is_edge_anchored and params.get("circle_enabled", True):
            min_ratio = float(params.get("arm_len_min_ratio", 0.75))
            low_bound = max(low_bound, current * max(0.0, min(1.0, min_ratio)))
    else:
        return False

    if current <= 0.0:
        return False

    low = float(low_bound)
    high = float(high_bound)
    if not (low < high):
        logs.append(
            f"{element}: Längen-Bracketing übersprungen ({key_label}: current={current:.3f}, "
            f"Range={low_bound:.3f}..{high_bound:.3f})"
        )
        return False

    candidates = sorted(
        {
            snap_half_fn(low),
            snap_half_fn(low + (high - low) * 0.25),
            snap_half_fn((low + high) / 2.0),
            snap_half_fn(low + (high - low) * 0.75),
            snap_half_fn(high),
            snap_half_fn(clip_scalar_fn(current, low, high)),
        }
    )
    candidate_errors = [element_error_for_extent_fn(img_orig, params, element, v) for v in candidates]
    if not all(math.isfinite(e) for e in candidate_errors):
        logs.append(
            f"{element}: Längen-Bracketing abgebrochen ({key_label}) wegen nicht-finiten Fehlern "
            + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
        )
        return False

    best_idx = argmin_index_fn(candidate_errors)
    best_len = float(candidates[best_idx])
    boundary_best = abs(best_len - low) < 0.02 or abs(best_len - high) < 0.02
    if boundary_best:
        s_best, s_err, s_improved = stochastic_survivor_scalar_fn(
            current,
            low,
            high,
            lambda v: element_error_for_extent_fn(img_orig, params, element, float(v)),
            snap=snap_half_fn,
            seed=1103 if element == "stem" else 1109,
        )
        if s_improved:
            best_len = float(s_best)
            logs.append(f"{element}: Längen-Stochastic-Survivor aktiviert (best_len={best_len:.3f}, err={s_err:.3f})")

    if abs(best_len - current) < 0.02:
        logs.append(
            f"{element}: Längen-Bracketing keine relevante Änderung ({key_label}: {current:.3f}); "
            f"Kandidaten=" + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
        )
        return False

    if element == "stem":
        if params.get("circle_enabled", True) and all(k in params for k in ("cy", "r")):
            is_bottom_anchored = float(params.get("stem_bottom", 0.0)) >= float(h) - 0.5
            if is_bottom_anchored and h <= 15 and not bool(params.get("draw_text", True)):
                bottom = float(h)
                top = float(clip_scalar_fn(bottom - best_len, 0.0, bottom - 1.0))
                params["stem_top"] = top
                params["stem_bottom"] = bottom
            else:
                top = float(clip_scalar_fn(float(params.get("cy", 0.0)) + float(params.get("r", 0.0)), 0.0, float(h - 1)))
                params["stem_top"] = top
                params["stem_bottom"] = float(clip_scalar_fn(top + best_len, top + 1.0, float(h)))
        else:
            center = (float(params.get("stem_top", 0.0)) + float(params.get("stem_bottom", 0.0))) / 2.0
            half = best_len / 2.0
            params["stem_top"] = float(clip_scalar_fn(center - half, 0.0, float(h - 1)))
            params["stem_bottom"] = float(clip_scalar_fn(center + half, params["stem_top"] + 1.0, float(h)))
    else:
        x1 = float(params.get("arm_x1", 0.0))
        y1 = float(params.get("arm_y1", 0.0))
        x2 = float(params.get("arm_x2", 0.0))
        y2 = float(params.get("arm_y2", 0.0))
        dx = x2 - x1
        dy = y2 - y1
        cur_len = float(math.hypot(dx, dy))
        if cur_len <= 1e-6:
            return False
        ux = dx / cur_len
        uy = dy / cur_len

        if params.get("circle_enabled", True) and all(k in params for k in ("cx", "cy", "r")):
            reanchor_arm_to_circle_edge_fn(params, float(params.get("r", 0.0)))
            ax1 = float(params.get("arm_x1", x1))
            ay1 = float(params.get("arm_y1", y1))
            ax2 = float(params.get("arm_x2", x2))
            ay2 = float(params.get("arm_y2", y2))

            cx = float(params.get("cx", 0.0))
            cy = float(params.get("cy", 0.0))
            d1 = float(math.hypot(ax1 - cx, ay1 - cy))
            d2 = float(math.hypot(ax2 - cx, ay2 - cy))

            if d1 <= d2:
                ix, iy = ax1, ay1
                if abs(uy) <= 0.35:
                    iy = cy
                    ix = cx - float(params.get("r", 0.0)) if ix <= cx else cx + float(params.get("r", 0.0))
                params["arm_x2"] = float(clip_scalar_fn(ix + (ux * best_len), 0.0, float(w - 1)))
                params["arm_y2"] = float(clip_scalar_fn(iy + (uy * best_len), 0.0, float(h - 1)))
                params["arm_x1"] = float(ix)
                params["arm_y1"] = float(iy)
            else:
                ix, iy = ax2, ay2
                if abs(uy) <= 0.35:
                    iy = cy
                    ix = cx - float(params.get("r", 0.0)) if ix <= cx else cx + float(params.get("r", 0.0))
                params["arm_x1"] = float(clip_scalar_fn(ix - (ux * best_len), 0.0, float(w - 1)))
                params["arm_y1"] = float(clip_scalar_fn(iy - (uy * best_len), 0.0, float(h - 1)))
                params["arm_x2"] = float(ix)
                params["arm_y2"] = float(iy)
        else:
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            half = best_len / 2.0
            params["arm_x1"] = float(clip_scalar_fn(cx - (ux * half), 0.0, float(w - 1)))
            params["arm_y1"] = float(clip_scalar_fn(cy - (uy * half), 0.0, float(h - 1)))
            params["arm_x2"] = float(clip_scalar_fn(cx + (ux * half), 0.0, float(w - 1)))
            params["arm_y2"] = float(clip_scalar_fn(cy + (uy * half), 0.0, float(h - 1)))

    logs.append(
        f"{element}: Längen-Bracketing {key_label} {current:.3f}->{best_len:.3f}; Kandidaten="
        + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
    )
    return True


def optimizeElementWidthBracketImpl(
    img_orig: object,
    params: dict[str, object],
    element: str,
    logs: list[str],
    *,
    element_width_key_and_bounds_fn: Callable[[str, dict[str, object], int, int], tuple[str, float, float] | None],
    snap_half_fn: Callable[[float], float],
    clip_scalar_fn: Callable[[float, float, float], float],
    element_error_for_width_fn: Callable[[object, dict[str, object], str, float], float],
    argmin_index_fn: Callable[[list[float]], int],
    stochastic_survivor_scalar_fn: Callable[..., tuple[float, float, bool]],
    snap_int_px_fn: Callable[[float], float],
) -> bool:
    h, w = img_orig.shape[:2]
    info = element_width_key_and_bounds_fn(element, params, w, h)
    if info is None:
        return False

    key, low_bound, high_bound = info
    current = float(params.get(key, 0.0))
    if current <= 0.0:
        return False

    low = float(low_bound)
    high = float(high_bound)
    if not (low < high):
        logs.append(f"{element}: Breiten-Bracketing übersprungen ({key}: current={current:.3f}, Range={low_bound:.3f}..{high_bound:.3f})")
        return False

    if key.endswith("_font_scale"):
        candidates = sorted(
            {
                round(low, 3),
                round(low + (high - low) * 0.15, 3),
                round(low + (high - low) * 0.30, 3),
                round(low + (high - low) * 0.50, 3),
                round(low + (high - low) * 0.70, 3),
                round(low + (high - low) * 0.85, 3),
                round(high, 3),
                round(max(low, min(high, current * 0.85)), 3),
                round(max(low, min(high, current)), 3),
                round(max(low, min(high, current * 1.15)), 3),
            }
        )
    else:
        candidates = sorted(
            {
                snap_half_fn(low),
                snap_half_fn(low + (high - low) * 0.25),
                snap_half_fn((low + high) / 2.0),
                snap_half_fn(low + (high - low) * 0.75),
                snap_half_fn(high),
                snap_half_fn(clip_scalar_fn(current, low, high)),
            }
        )
    candidate_errors = [element_error_for_width_fn(img_orig, params, element, v) for v in candidates]
    if not all(math.isfinite(e) for e in candidate_errors):
        logs.append(
            f"{element}: Breiten-Bracketing abgebrochen ({key}) wegen nicht-finiten Fehlern "
            + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
        )
        return False

    best_idx = argmin_index_fn(candidate_errors)
    best_width = float(candidates[best_idx])
    boundary_best = abs(best_width - low) < 0.02 or abs(best_width - high) < 0.02
    if boundary_best:
        snap_fn = (lambda v: float(round(v, 3))) if key.endswith("_font_scale") else snap_half_fn
        s_best, s_err, s_improved = stochastic_survivor_scalar_fn(
            current,
            low,
            high,
            lambda v: element_error_for_width_fn(img_orig, params, element, float(v)),
            snap=snap_fn,
            seed=1201,
        )
        if s_improved:
            best_width = float(s_best)
            logs.append(f"{element}: Breiten-Stochastic-Survivor aktiviert ({key}={best_width:.3f}, err={s_err:.3f})")

    old = float(params.get(key, current))
    if abs(best_width - old) < 0.02:
        logs.append(
            f"{element}: Breiten-Bracketing keine relevante Änderung ({key}: {old:.3f}); Kandidaten="
            + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
        )
        return False

    if key in {"stroke_circle", "arm_stroke", "stem_width"}:
        best_width = snap_int_px_fn(best_width)
    elif key.endswith("_font_scale"):
        best_width = float(round(best_width, 3))
    else:
        best_width = snap_half_fn(best_width)

    params[key] = best_width
    if key == "stem_width" and params.get("stem_enabled"):
        params["stem_x"] = snap_half_fn(float(params.get("cx", params.get("stem_x", 0.0))) - (params["stem_width"] / 2.0))
    logs.append(
        f"{element}: Breiten-Bracketing {key} {old:.3f}->{best_width:.3f}; Kandidaten="
        + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
    )
    return True
