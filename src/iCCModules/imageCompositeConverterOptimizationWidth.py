"""Extracted stroke/text-width helpers for imageCompositeConverter."""

from __future__ import annotations

from collections.abc import Callable


def elementWidthKeyAndBoundsImpl(
    element: str,
    params: dict[str, object],
    w: int,
    h: int,
    *,
    ac08_stroke_width_px: float,
    extract_badge_element_mask_fn: Callable[[object, dict[str, object], str], object],
    mask_bbox_fn: Callable[[object], tuple[float, float, float, float] | None],
    img_orig: object | None = None,
) -> tuple[str, float, float] | None:
    lock_strokes = bool(params.get("lock_stroke_widths"))
    min_dim = float(min(w, h))
    if element == "stem" and params.get("stem_enabled"):
        if lock_strokes:
            fixed = float(ac08_stroke_width_px)
            if not bool(params.get("allow_stem_width_tuning", False)):
                return "stem_width", fixed, fixed
            high = min(
                float(params.get("stem_width_max", fixed + 1.0)),
                max(fixed, fixed + float(params.get("stem_width_tuning_px", 1.0))),
            )
            return "stem_width", fixed, max(fixed, high)
        low = max(1.0, float(params.get("stroke_circle", 1.0)) * 0.65)
        high = max(low, min(float(w) * 0.25, float(params.get("stem_width_max", float(w) * 0.25))))
        return "stem_width", low, high
    if element == "arm" and params.get("arm_enabled"):
        if lock_strokes:
            fixed = float(ac08_stroke_width_px)
            return "arm_stroke", fixed, fixed
        low = max(1.0, float(params.get("stroke_circle", 1.0)) * 0.65)
        high = max(low, min(float(min(w, h)) * 0.20, float(params.get("r", min(w, h))) * 0.9))
        return "arm_stroke", low, high
    if element == "circle" and params.get("circle_enabled", True):
        if lock_strokes:
            fixed = float(ac08_stroke_width_px)
            return "stroke_circle", fixed, fixed
        low = max(0.8, float(params.get("stroke_circle", 1.0)) * 0.6)
        high = max(low, min(float(min(w, h)) * 0.22, float(params.get("r", min(w, h))) * 0.9))
        return "stroke_circle", low, high
    if element == "text" and params.get("draw_text", True):
        mode = str(params.get("text_mode", "")).lower()
        if mode == "voc":
            cur = float(params.get("voc_font_scale", 0.52))
            if bool(params.get("lock_text_scale", False)):
                return "voc_font_scale", cur, cur
            low = max(0.30, min(cur * 0.60, 0.45))
            high = 1.60
            if img_orig is not None:
                text_mask = extract_badge_element_mask_fn(img_orig, params, "text")
                bbox = mask_bbox_fn(text_mask) if text_mask is not None else None
                if bbox is not None:
                    x1, y1, x2, y2 = bbox
                    text_w = max(1.0, (float(x2) - float(x1)) + 1.0)
                    text_h = max(1.0, (float(y2) - float(y1)) + 1.0)
                    implied_scale = max(
                        text_w / max(1.0, float(w) * 0.38),
                        text_h / max(1.0, float(h) * 0.18),
                        text_w / max(1.0, float(params.get("r", min_dim)) * 2.8),
                    )
                    low = max(low, min(0.90, implied_scale * 0.70))
                    high = max(high, min(2.40, implied_scale * 1.35))
            if "voc_font_scale_min" in params:
                low = max(low, float(params["voc_font_scale_min"]))
            if "voc_font_scale_max" in params:
                high = min(high, float(params["voc_font_scale_max"]))
            return "voc_font_scale", low, max(low, high)
        if mode == "co2":
            cur = float(params.get("co2_font_scale", 0.82))
            if bool(params.get("lock_text_scale", False)):
                return "co2_font_scale", cur, cur
            low = max(0.45, cur * 0.72)
            high = min(1.55, cur * 1.45)
            if "co2_font_scale_min" in params:
                low = max(low, float(params["co2_font_scale_min"]))
            if "co2_font_scale_max" in params:
                high = min(high, float(params["co2_font_scale_max"]))
            return "co2_font_scale", low, max(low, high)
    return None


def elementErrorForWidthImpl(
    img_orig: object,
    params: dict[str, object],
    element: str,
    width_value: float,
    *,
    element_width_key_and_bounds_fn: Callable[[str, dict[str, object], int, int, object | None], tuple[str, float, float] | None],
    clip_scalar_fn: Callable[[float, float, float], float],
    generate_badge_svg_fn: Callable[[int, int, dict[str, object]], str],
    element_only_params_fn: Callable[[dict[str, object], str], dict[str, object]],
    fit_to_original_size_fn: Callable[[object, object], object],
    render_svg_to_numpy_fn: Callable[[str, int, int], object],
    extract_badge_element_mask_fn: Callable[[object, dict[str, object], str], object],
    element_match_error_fn: Callable[..., float],
) -> float:
    h, w = img_orig.shape[:2]
    probe = dict(params)
    info = element_width_key_and_bounds_fn(element, probe, w, h, img_orig)
    if info is None:
        return float("inf")
    key, low, high = info
    probe[key] = float(clip_scalar_fn(width_value, low, high))
    if key == "stem_width" and probe.get("stem_enabled"):
        probe["stem_x"] = float(probe.get("cx", probe.get("stem_x", 0.0))) - (probe["stem_width"] / 2.0)
    elem_svg = generate_badge_svg_fn(w, h, element_only_params_fn(probe, element))
    elem_render = fit_to_original_size_fn(img_orig, render_svg_to_numpy_fn(elem_svg, w, h))
    if elem_render is None:
        return float("inf")
    mask_orig = extract_badge_element_mask_fn(img_orig, probe, element)
    if mask_orig is None:
        return float("inf")
    return element_match_error_fn(img_orig, elem_render, probe, element, mask_orig=mask_orig)
