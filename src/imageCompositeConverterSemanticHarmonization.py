"""Extracted semantic size-variant harmonization helpers for imageCompositeConverter."""

from __future__ import annotations

from collections.abc import Callable


def needsLargeCircleOverflowGuardImpl(params: dict) -> bool:
    """Return whether circle placement may intentionally exceed canvas bounds."""
    if not bool(params.get("circle_enabled", True)):
        return False
    if bool(params.get("arm_enabled") or params.get("stem_enabled")):
        return False
    if not bool(params.get("draw_text", False)):
        return False
    if str(params.get("text_mode", "")).lower() != "co2":
        return False

    template_r = float(params.get("template_circle_radius", params.get("r", 0.0)) or 0.0)
    current_r = float(params.get("r", 0.0) or 0.0)
    width = float(params.get("width", params.get("badge_width", 0.0)) or 0.0)

    large_template = template_r >= 10.0
    large_current = current_r >= 10.0
    wide_canvas = width >= 30.0
    return bool(large_template or large_current or wide_canvas)


def scaleBadgeParamsImpl(
    anchor: dict,
    anchor_w: int,
    anchor_h: int,
    target_w: int,
    target_h: int,
    *,
    clip_scalar_fn: Callable[[float, float, float], float],
    needs_large_circle_overflow_guard_fn: Callable[[dict], bool],
) -> dict:
    scaled = dict(anchor)
    scale = max(1e-6, float(min(target_w, target_h)) / max(1.0, float(min(anchor_w, anchor_h))))
    scale_x = max(1e-6, float(target_w) / max(1.0, float(anchor_w)))
    scale_y = max(1e-6, float(target_h) / max(1.0, float(anchor_h)))

    if scaled.get("circle_enabled", True):
        scaled["cx"] = float(anchor["cx"]) * scale_x
        scaled["cy"] = float(anchor["cy"]) * scale_y
        scaled["r"] = float(anchor["r"]) * scale
        # Intentionally preserve stroke thickness across size variants.
        scaled["stroke_circle"] = float(anchor["stroke_circle"])

    if scaled.get("stem_enabled"):
        scaled["stem_x"] = float(anchor["stem_x"]) * scale_x
        scaled["stem_width"] = float(anchor["stem_width"])
        scaled["stem_top"] = float(anchor["stem_top"]) * scale_y
        scaled["stem_bottom"] = float(anchor["stem_bottom"]) * scale_y

    if scaled.get("arm_enabled"):
        scaled["arm_x1"] = float(anchor["arm_x1"]) * scale_x
        scaled["arm_y1"] = float(anchor["arm_y1"]) * scale_y
        scaled["arm_x2"] = float(anchor["arm_x2"]) * scale_x
        scaled["arm_y2"] = float(anchor["arm_y2"]) * scale_y
        scaled["arm_stroke"] = float(anchor["arm_stroke"])

    template_scalars = {
        "template_circle_cx": scale_x,
        "template_circle_cy": scale_y,
        "template_circle_radius": scale,
        "template_stem_top": scale_y,
        "template_stem_bottom": scale_y,
        "template_arm_x1": scale_x,
        "template_arm_y1": scale_y,
        "template_arm_x2": scale_x,
        "template_arm_y2": scale_y,
        "stem_len_min": scale_y,
        "arm_len_min": max(scale_x, scale_y),
    }
    for key, factor in template_scalars.items():
        if key in scaled:
            scaled[key] = float(anchor[key]) * float(factor)

    if scaled.get("circle_enabled", True):
        overflow_guard = needs_large_circle_overflow_guard_fn(scaled)
        required_r = (float(target_w) / 2.0) + 0.5 if overflow_guard else 1.0
        if overflow_guard:
            scaled["allow_circle_overflow"] = True
            scaled["circle_radius_lower_bound_px"] = float(
                max(float(scaled.get("circle_radius_lower_bound_px", 1.0)), required_r)
            )
        stroke = max(0.0, float(scaled.get("stroke_circle", 1.0)))
        half_stroke = stroke / 2.0
        cx = float(scaled.get("cx", target_w / 2.0))
        cy = float(scaled.get("cy", target_h / 2.0))
        r = max(1.0, float(scaled.get("r", 1.0)), required_r)

        max_fit_r = max(1.0, (min(float(target_w), float(target_h)) / 2.0) - half_stroke)
        if not overflow_guard and r > max_fit_r:
            r = max_fit_r

        min_cx = r + half_stroke
        max_cx = float(target_w) - r - half_stroke
        min_cy = r + half_stroke
        max_cy = float(target_h) - r - half_stroke

        if min_cx > max_cx:
            cx = float(target_w) / 2.0 if not overflow_guard else float(clip_scalar_fn(cx, 0.0, float(target_w)))
        else:
            cx = float(clip_scalar_fn(cx, min_cx, max_cx))

        if min_cy > max_cy:
            cy = float(target_h) / 2.0 if not overflow_guard else float(clip_scalar_fn(cy, 0.0, float(target_h)))
        else:
            cy = float(clip_scalar_fn(cy, min_cy, max_cy))

        if scaled.get("stem_enabled") and "stem_width" in scaled:
            stem_width = max(1e-6, float(scaled["stem_width"]))
            scaled["stem_x"] = cx - (stem_width / 2.0)
            if "stem_top" in scaled:
                bottom_anchored = float(scaled.get("stem_bottom", 0.0)) >= (float(target_h) - 0.5)
                reanchored_top = cy + r - (stem_width * 0.55)
                if bottom_anchored:
                    scaled["stem_top"] = float(clip_scalar_fn(reanchored_top, 0.0, float(target_h)))
                    scaled["stem_bottom"] = float(target_h)
                else:
                    stem_len = max(
                        1.0,
                        float(scaled.get("stem_bottom", reanchored_top))
                        - float(scaled.get("stem_top", reanchored_top)),
                    )
                    scaled["stem_top"] = float(clip_scalar_fn(reanchored_top, 0.0, float(target_h - 1)))
                    scaled["stem_bottom"] = float(
                        clip_scalar_fn(
                            float(scaled["stem_top"]) + stem_len,
                            float(scaled["stem_top"]) + 1.0,
                            float(target_h),
                        )
                    )

        scaled["cx"] = cx
        scaled["cy"] = cy
        scaled["r"] = r

    return scaled


def harmonizationAnchorPriorityImpl(suffix: str, prefer_large: bool) -> int:
    """Return size-priority rank for L/M/S harmonization anchors."""
    if prefer_large:
        return {"L": 0, "M": 1, "S": 2}.get(str(suffix), 3)
    return {"M": 0, "L": 1, "S": 2}.get(str(suffix), 3)


def clipGrayImpl(value: float) -> int:
    return int(max(0, min(255, round(float(value)))))


def familyHarmonizedBadgeColorsImpl(variant_rows: list[dict[str, object]]) -> dict[str, int]:
    """Derive a family palette from L/M/S variants and slightly boost contrast."""
    buckets: dict[str, list[float]] = {
        "fill_gray": [],
        "stroke_gray": [],
        "text_gray": [],
        "stem_gray": [],
    }
    for row in variant_rows:
        params = dict(row["params"])
        for key in buckets:
            value = params.get(key)
            if value is None:
                continue
            try:
                buckets[key].append(float(value))
            except (TypeError, ValueError):
                continue

    fill_avg = sum(buckets["fill_gray"]) / max(1, len(buckets["fill_gray"]))
    stroke_avg = sum(buckets["stroke_gray"]) / max(1, len(buckets["stroke_gray"]))
    if fill_avg < stroke_avg:
        fill_avg, stroke_avg = stroke_avg, fill_avg

    center = (fill_avg + stroke_avg) / 2.0
    delta = abs(fill_avg - stroke_avg)
    boosted_delta = max(18.0, delta * 1.12)
    fill_gray = clipGrayImpl(center + (boosted_delta / 2.0))
    stroke_gray = clipGrayImpl(center - (boosted_delta / 2.0))
    if fill_gray <= stroke_gray:
        fill_gray = clipGrayImpl(max(fill_gray, stroke_gray + 1.0))

    colors = {
        "fill_gray": fill_gray,
        "stroke_gray": stroke_gray,
        "text_gray": stroke_gray,
        "stem_gray": stroke_gray,
    }

    if buckets["text_gray"]:
        text_avg = sum(buckets["text_gray"]) / float(len(buckets["text_gray"]))
        colors["text_gray"] = clipGrayImpl(min(text_avg, float(stroke_gray)))

    if buckets["stem_gray"]:
        stem_avg = sum(buckets["stem_gray"]) / float(len(buckets["stem_gray"]))
        colors["stem_gray"] = clipGrayImpl(min(stem_avg, float(stroke_gray)))

    return colors
