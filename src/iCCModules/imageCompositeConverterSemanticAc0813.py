"""AC0813/AC0814 semantic badge helper block extracted from imageCompositeConverter."""

from __future__ import annotations

import math


def defaultAc0813ParamsImpl(
    w: int,
    h: int,
    *,
    default_ac081x_shared,
    default_edge_anchored_circle_geometry_fn,
    normalize_light_circle_colors_fn,
    light_circle_stroke_gray: int,
    light_circle_fill_gray: int,
) -> dict:
    """AC0813 is AC0812 rotated 90° clockwise (vertical arm from top to circle)."""
    if w <= 0 or h <= 0:
        return default_ac081x_shared(w, h)

    circle = default_edge_anchored_circle_geometry_fn(w, h, anchor="bottom")
    cx = float(circle["cx"])
    cy = float(circle["cy"])
    r = float(circle["r"])
    stroke_circle = float(circle["stroke_circle"])
    arm_stroke = max(1.0, float(w) * 0.10)

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
            "arm_x1": cx,
            "arm_y1": 0.0,
            "arm_x2": cx,
            "arm_y2": max(0.0, cy - r),
            "arm_stroke": arm_stroke,
        }
    )


def fitAc0813ParamsFromImageImpl(
    img,
    defaults: dict,
    *,
    fit_semantic_badge_from_image_fn,
    clip_scalar_fn,
    normalize_light_circle_colors_fn,
) -> dict:
    """Fit AC0813 while keeping the vertical arm anchored to the upper edge."""
    params = fit_semantic_badge_from_image_fn(img, defaults)
    h, w = img.shape[:2]
    aspect_ratio = (float(h) / float(w)) if w > 0 else 1.0

    raw_arm_stroke = float(params.get("arm_stroke", defaults.get("arm_stroke", max(1.0, float(w) * 0.10))))
    cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
    cy = float(params.get("cy", defaults.get("cy", float(h) - (float(w) / 2.0))))
    r = float(params.get("r", defaults.get("r", float(w) * 0.4)))
    stroke_circle = float(params.get("stroke_circle", defaults.get("stroke_circle", max(0.9, float(w) / 15.0))))
    default_r = float(defaults.get("r", float(w) * 0.4))

    min_arm_stroke = max(1.0, stroke_circle * 0.75)
    max_arm_stroke = max(min_arm_stroke, min(float(w) * 0.14, stroke_circle * 1.6))
    arm_stroke = max(min_arm_stroke, min(raw_arm_stroke, max_arm_stroke))

    if w <= 15 and not bool(params.get("draw_text", True)):
        r = max(r, default_r * 0.98)

    elongated_plain_badge = aspect_ratio >= 1.60 and w >= 20 and not bool(params.get("draw_text", True))
    if elongated_plain_badge:
        r = max(r, default_r * 0.95)
        params["min_circle_radius"] = float(max(float(params.get("min_circle_radius", 1.0)), default_r * 0.95))

    params["r"] = r

    if w <= 15 and bool(params.get("draw_text", False)):
        default_cx = float(defaults.get("cx", float(w) / 2.0))
        default_cy = float(defaults.get("cy", float(h) - (float(w) / 2.0)))
        default_r = float(defaults.get("r", float(w) * 0.4))
        params["cx"] = default_cx
        params["cy"] = float(clip_scalar_fn(cy, default_cy - 0.8, default_cy + 0.8))
        params["r"] = max(r, default_r * 0.94)
        params["lock_circle_cx"] = True
        params["lock_circle_cy"] = True
        params["lock_arm_center_to_circle"] = True
        cx = float(params["cx"])
        cy = float(params["cy"])
        r = float(params["r"])

    params["arm_enabled"] = True
    params["arm_stroke"] = arm_stroke
    params["arm_x1"] = cx
    params["arm_y1"] = 0.0
    params["arm_x2"] = cx
    params["arm_y2"] = max(0.0, cy - r)
    return normalize_light_circle_colors_fn(params)


def defaultAc0814ParamsImpl(
    w: int,
    h: int,
    *,
    default_ac081x_shared,
    normalize_light_circle_colors_fn,
    light_circle_stroke_gray: int,
    light_circle_fill_gray: int,
) -> dict:
    """AC0814 is horizontally elongated: circle on the left, arm to the right."""
    if w <= 0 or h <= 0:
        return default_ac081x_shared(w, h)

    r = float(h) * 0.46
    stroke_circle = max(0.9, float(h) / 25.0)
    left_margin = max(stroke_circle * 0.5, float(h) * 0.18)
    cx = r + left_margin
    cy = float(h) / 2.0
    arm_stroke = max(1.0, stroke_circle)

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
            "arm_x1": min(float(w), cx + r),
            "arm_y1": cy,
            "arm_x2": float(w),
            "arm_y2": cy,
            "arm_stroke": arm_stroke,
            "arm_len_min": max(1.0, (float(w) - min(float(w), cx + r)) * 0.75),
            "arm_len_min_ratio": 0.75,
        }
    )


def fitAc0814ParamsFromImageImpl(
    img,
    defaults: dict,
    *,
    fit_semantic_badge_from_image_fn,
    clip_scalar_fn,
    normalize_light_circle_colors_fn,
) -> dict:
    """Fit AC0814 while keeping the horizontal arm anchored to the right edge."""
    params = fit_semantic_badge_from_image_fn(img, defaults)
    h, w = img.shape[:2]
    aspect_ratio = (float(w) / float(h)) if h > 0 else 1.0

    raw_arm_stroke = float(params.get("arm_stroke", defaults.get("arm_stroke", max(1.0, float(h) * 0.10))))
    cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
    cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
    r = float(params.get("r", defaults.get("r", float(h) * 0.4)))
    stroke_circle = float(params.get("stroke_circle", defaults.get("stroke_circle", max(0.9, float(h) / 15.0))))
    default_r = float(defaults.get("r", float(h) * 0.4))

    min_arm_stroke = max(1.0, stroke_circle * 0.75)
    max_arm_stroke = max(min_arm_stroke, min(float(h) * 0.14, stroke_circle * 1.6))
    arm_stroke = max(min_arm_stroke, min(raw_arm_stroke, max_arm_stroke))

    cx = float(params.get("cx", defaults.get("cx", float(h) / 2.0)))
    cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
    r = float(params.get("r", defaults.get("r", float(h) * 0.4)))

    tiny_plain_badge = h <= 18 and not bool(params.get("draw_text", True))
    if tiny_plain_badge:
        r = max(r, default_r * 0.98)
        default_cx = float(defaults.get("cx", float(w) / 2.0))
        default_cy = float(defaults.get("cy", float(h) / 2.0))
        params["cx"] = default_cx
        params["cy"] = float(clip_scalar_fn(cy, default_cy - 0.5, default_cy + 0.5))
        params["lock_circle_cx"] = True
        params["lock_circle_cy"] = True
        params["lock_arm_center_to_circle"] = True
        cx = float(params["cx"])
        cy = float(params["cy"])

    elongated_plain_badge = aspect_ratio >= 1.60 and h >= 20 and not bool(params.get("draw_text", True))
    if elongated_plain_badge:
        r = max(r, default_r * 0.95)
        params["min_circle_radius"] = float(max(float(params.get("min_circle_radius", 1.0)), default_r * 0.95))

        default_cx = float(defaults.get("cx", float(w) / 2.0))
        default_cy = float(defaults.get("cy", float(h) / 2.0))
        medium_plain_canvas = h <= 22 and w <= 38
        max_left_correction = max(0.0, default_r * 0.14) if medium_plain_canvas else 0.0
        corrected_cx = default_cx
        if max_left_correction > 0.0:
            corrected_cx = float(clip_scalar_fn(cx, default_cx - max_left_correction, default_cx))
        params["cx"] = corrected_cx
        if medium_plain_canvas:
            params["template_circle_cx"] = corrected_cx
        params["cy"] = float(clip_scalar_fn(cy, default_cy - 0.6, default_cy + 0.6))
        params["lock_circle_cx"] = True
        params["lock_circle_cy"] = True
        params["lock_arm_center_to_circle"] = True
        cx = float(params["cx"])
        cy = float(params["cy"])

    params["r"] = r

    params["arm_enabled"] = True
    params["arm_stroke"] = arm_stroke
    params["arm_x1"] = min(float(w), cx + r)
    params["arm_y1"] = cy
    params["arm_x2"] = float(w)
    params["arm_y2"] = cy
    current_arm_len = float(math.hypot(params["arm_x2"] - params["arm_x1"], params["arm_y2"] - params["arm_y1"]))
    default_arm_len = max(
        0.0,
        float(w) - (float(defaults.get("cx", float(h) / 2.0)) + float(defaults.get("r", float(h) * 0.4))),
    )
    semantic_arm_len_min = max(1.0, default_arm_len * 0.75)
    min_arm_len_ratio = 0.75
    if elongated_plain_badge:
        min_arm_len_ratio = 0.82
    params["arm_len_min_ratio"] = float(max(float(params.get("arm_len_min_ratio", min_arm_len_ratio)), min_arm_len_ratio))
    params["arm_len_min"] = max(
        1.0,
        current_arm_len * float(params["arm_len_min_ratio"]),
        semantic_arm_len_min,
    )
    return normalize_light_circle_colors_fn(params)


def defaultAc0810ParamsImpl(
    w: int,
    h: int,
    *,
    default_ac0814_params_fn,
) -> dict:
    """AC0810 uses the same right-arm geometry as AC0814 (circle on the left)."""
    return default_ac0814_params_fn(w, h)


def fitAc0810ParamsFromImageImpl(
    img,
    defaults: dict,
    *,
    fit_ac0814_params_from_image_fn,
) -> dict:
    """Fit AC0810 with the same right-anchored arm behavior as AC0814."""
    return fit_ac0814_params_from_image_fn(img, defaults)
