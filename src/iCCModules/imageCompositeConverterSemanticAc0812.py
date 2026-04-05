"""AC0812 semantic badge helper block extracted from imageCompositeConverter."""

from __future__ import annotations

import math


def defaultAc0812ParamsImpl(
    w: int,
    h: int,
    *,
    default_ac081x_shared,
    normalize_light_circle_colors_fn,
    light_circle_stroke_gray: int,
    light_circle_fill_gray: int,
) -> dict:
    """AC0812 is horizontally elongated: left arm, circle on the right."""
    if w <= 0 or h <= 0:
        return default_ac081x_shared(w, h)

    r = float(h) * 0.36
    stroke_circle = max(0.9, float(h) / 15.0)
    cx = float(w) - (float(h) / 2.0)
    cy = float(h) / 2.0
    arm_stroke = max(1.0, float(h) * 0.10)

    return normalize_light_circle_colors_fn(
        {
            "cx": cx,
            "cy": cy,
            "r": r,
            "stroke_circle": stroke_circle,
            "stroke_gray": light_circle_stroke_gray,
            "fill_gray": light_circle_fill_gray,
            "draw_text": False,
            "arm_enabled": True,
            "arm_x1": 0.0,
            "arm_y1": cy,
            "arm_x2": max(0.0, cx - r - (arm_stroke / 2.0)),
            "arm_y2": cy,
            "arm_stroke": arm_stroke,
            "arm_len_min_ratio": 0.75,
        }
    )


def fitAc0812ParamsFromImageImpl(
    img,
    defaults: dict,
    *,
    fit_semantic_badge_from_image_fn,
    max_circle_radius_inside_canvas_fn,
    normalize_light_circle_colors_fn,
) -> dict:
    """Fit AC0812 while keeping the horizontal arm anchored to the left edge."""
    params = fit_semantic_badge_from_image_fn(img, defaults)
    h, w = img.shape[:2]
    aspect_ratio = (float(w) / float(h)) if h > 0 else 1.0

    raw_arm_stroke = float(params.get("arm_stroke", defaults.get("arm_stroke", max(1.0, float(h) * 0.10))))
    cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
    cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
    r = float(params.get("r", defaults.get("r", float(h) * 0.4)))
    stroke_circle = float(params.get("stroke_circle", defaults.get("stroke_circle", max(0.9, float(h) / 15.0))))

    min_arm_stroke = max(1.0, stroke_circle * 0.75)
    max_arm_stroke = max(min_arm_stroke, min(float(h) * 0.14, stroke_circle * 1.6))
    arm_stroke = max(min_arm_stroke, min(raw_arm_stroke, max_arm_stroke))

    default_r = float(defaults.get("r", float(h) * 0.4))
    canvas_r_limit = max_circle_radius_inside_canvas_fn(cx, cy, w, h, stroke_circle)
    max_r = max(default_r * 1.45, default_r + 3.0)
    max_r = min(max_r, canvas_r_limit)
    r = min(r, max_r)

    if h <= 15 and not bool(params.get("draw_text", True)):
        r = max(r, default_r * 0.98)

    if aspect_ratio >= 1.60 and h >= 20 and not bool(params.get("draw_text", True)):
        r = max(r, default_r * 0.95)

    params["r"] = r

    params["arm_enabled"] = True
    params["arm_stroke"] = arm_stroke
    params["arm_x1"] = 0.0
    params["arm_y1"] = cy
    attach_offset = max(0.0, arm_stroke / 2.0)
    params["arm_x2"] = max(0.0, cx - r - attach_offset)
    params["arm_y2"] = cy
    current_arm_len = float(math.hypot(params["arm_x2"] - params["arm_x1"], params["arm_y2"] - params["arm_y1"]))
    default_arm_len = max(
        0.0,
        float(defaults.get("cx", float(w) / 2.0)) - float(defaults.get("r", float(h) * 0.4)),
    )
    semantic_arm_len_min = max(1.0, default_arm_len * 0.75)
    params["arm_len_min"] = max(1.0, current_arm_len * 0.75, semantic_arm_len_min)
    min_arm_len_ratio = 0.75
    if aspect_ratio >= 1.60 and h >= 20 and not bool(params.get("draw_text", True)):
        min_arm_len_ratio = 0.82
    params["arm_len_min_ratio"] = float(max(float(params.get("arm_len_min_ratio", min_arm_len_ratio)), min_arm_len_ratio))
    params["arm_len_min"] = max(
        float(params["arm_len_min"]),
        max(1.0, current_arm_len * float(params["arm_len_min_ratio"]), semantic_arm_len_min),
    )

    max_r_from_arm_span = max(1.0, cx - params["arm_len_min"])
    params["max_circle_radius"] = float(min(canvas_r_limit, max_r_from_arm_span))
    return normalize_light_circle_colors_fn(params)
