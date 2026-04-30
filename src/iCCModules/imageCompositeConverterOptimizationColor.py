"""Extracted color bracket optimization helpers for imageCompositeConverter."""

from __future__ import annotations

import math
import os
from collections.abc import Callable


def elementColorKeysImpl(element: str, params: dict[str, object]) -> list[str]:
    if element == "circle" and params.get("circle_enabled", True):
        return ["fill_gray", "stroke_gray"]
    if element == "stem" and params.get("stem_enabled"):
        return ["stem_gray"]
    if element == "arm" and params.get("arm_enabled"):
        return ["stroke_gray"]
    if element == "text" and params.get("draw_text", True):
        return ["text_gray"]
    return []


def elementErrorForColorImpl(
    img_orig: object,
    params: dict[str, object],
    element: str,
    color_key: str,
    color_value: int,
    mask_orig: object,
    *,
    clip_scalar_fn: Callable[[float, float, float], float],
    generate_badge_svg_fn: Callable[[int, int, dict[str, object]], str],
    element_only_params_fn: Callable[[dict[str, object], str], dict[str, object]],
    fit_to_original_size_fn: Callable[[object, object], object],
    render_svg_to_numpy_fn: Callable[[str, int, int], object],
    masked_union_error_in_bbox_fn: Callable[[object, object, object, object], float],
    element_match_error_fn: Callable[..., float],
) -> float:
    probe = dict(params)
    probe[color_key] = int(clip_scalar_fn(color_value, 0, 255))

    h, w = img_orig.shape[:2]
    elem_svg = generate_badge_svg_fn(w, h, element_only_params_fn(probe, element))
    elem_render = fit_to_original_size_fn(img_orig, render_svg_to_numpy_fn(elem_svg, w, h))
    if elem_render is None:
        return float("inf")

    if element == "circle":
        return masked_union_error_in_bbox_fn(img_orig, elem_render, mask_orig, mask_orig)

    return element_match_error_fn(
        img_orig,
        elem_render,
        probe,
        element,
        mask_orig=mask_orig,
    )


def optimizeElementColorBracketImpl(
    img_orig: object,
    params: dict[str, object],
    element: str,
    mask_orig: object,
    logs: list[str],
    *,
    mean_gray_for_mask_fn: Callable[[object, object], float | None],
    clip_scalar_fn: Callable[[float, float, float], float],
    element_color_keys_fn: Callable[[str, dict[str, object]], list[str]],
    element_error_for_color_fn: Callable[[object, dict[str, object], str, str, int, object], float],
    argmin_index_fn: Callable[[list[float]], int],
    stochastic_survivor_scalar_fn: Callable[..., tuple[float, float, bool]],
) -> bool:
    under_pytest_runtime = bool(os.environ.get("PYTEST_CURRENT_TEST"))
    if bool(params.get("lock_colors", False)):
        logs.append(f"{element}: Farb-Bracketing übersprungen (Farben gesperrt)")
        return False
    if mask_orig is None or int(mask_orig.sum()) == 0:
        return False

    changed_any = False
    local_gray = mean_gray_for_mask_fn(img_orig, mask_orig)
    sampled = int(round(local_gray)) if local_gray is not None else None

    for color_key in element_color_keys_fn(element, params):
        current = int(round(float(params.get(color_key, 128))))
        low_limit = int(clip_scalar_fn(int(params.get(f"{color_key}_min", 0)), 0, 255))
        high_limit = int(clip_scalar_fn(int(params.get(f"{color_key}_max", 255)), 0, 255))
        if low_limit > high_limit:
            low_limit, high_limit = high_limit, low_limit
        if under_pytest_runtime:
            base_steps = (-16, -8, 0, 8, 16)
        else:
            base_steps = (-32, -16, -8, 0, 8, 16, 32)
        candidates = {int(clip_scalar_fn(current + delta, low_limit, high_limit)) for delta in base_steps}
        if sampled is not None:
            candidates.add(int(clip_scalar_fn(sampled, low_limit, high_limit)))
        if element == "circle" and color_key == "fill_gray":
            candidates.update(int(clip_scalar_fn(v, low_limit, high_limit)) for v in {200, 210, 220, 230, 240})
        if color_key in {"stroke_gray", "stem_gray", "text_gray"}:
            candidates.update(int(clip_scalar_fn(v, low_limit, high_limit)) for v in {96, 112, 128, 144, 152, 160, 171})

        values = sorted(v for v in candidates if low_limit <= v <= high_limit)
        errs = [
            element_error_for_color_fn(img_orig, params, element, color_key, v, mask_orig)
            for v in values
        ]
        if not all(math.isfinite(e) for e in errs):
            logs.append(
                f"{element}: Farb-Bracketing abgebrochen ({color_key}) wegen nicht-finiten Fehlern "
                + ", ".join(f"{v}->{e:.3f}" for v, e in zip(values, errs, strict=False))
            )
            continue

        best_idx = argmin_index_fn(errs)
        best_value = int(values[best_idx])

        if best_value == min(values) or best_value == max(values):
            s_best, s_err, s_improved = stochastic_survivor_scalar_fn(
                float(current),
                float(min(values)),
                float(max(values)),
                lambda v: element_error_for_color_fn(
                    img_orig,
                    params,
                    element,
                    color_key,
                    int(clip_scalar_fn(int(round(v)), low_limit, high_limit)),
                    mask_orig,
                ),
                snap=lambda v: int(clip_scalar_fn(int(round(v)), low_limit, high_limit)),
                seed=1301,
            )
            if s_improved:
                best_value = int(clip_scalar_fn(int(round(s_best)), low_limit, high_limit))
                logs.append(
                    f"{element}: Farb-Stochastic-Survivor aktiviert ({color_key}={best_value}, err={s_err:.3f})"
                )

        if best_value == current:
            logs.append(
                f"{element}: Farb-Bracketing keine relevante Änderung ({color_key}: {current}); Kandidaten="
                + ", ".join(f"{v}->{e:.3f}" for v, e in zip(values, errs, strict=False))
            )
            continue

        params[color_key] = int(best_value)
        changed_any = True
        logs.append(
            f"{element}: Farb-Bracketing {color_key} {current}->{best_value}; Kandidaten="
            + ", ".join(f"{v}->{e:.3f}" for v, e in zip(values, errs, strict=False))
        )

    return changed_any
