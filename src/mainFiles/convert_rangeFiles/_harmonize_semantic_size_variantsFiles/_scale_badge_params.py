from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _scale_badge_params(
    anchor: dict,
    anchor_w: int,
    anchor_h: int,
    target_w: int,
    target_h: int,
    *,
    target_variant: str = "",
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
        overflow_guard = _needs_large_circle_overflow_guard(scaled)
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
            cx = float(target_w) / 2.0 if not overflow_guard else float(Action._clip_scalar(cx, 0.0, float(target_w)))
        else:
            cx = float(Action._clip_scalar(cx, min_cx, max_cx))

        if min_cy > max_cy:
            cy = float(target_h) / 2.0 if not overflow_guard else float(Action._clip_scalar(cy, 0.0, float(target_h)))
        else:
            cy = float(Action._clip_scalar(cy, min_cy, max_cy))

        if scaled.get("stem_enabled") and "stem_width" in scaled:
            stem_width = max(1e-6, float(scaled["stem_width"]))
            scaled["stem_x"] = cx - (stem_width / 2.0)
            if "stem_top" in scaled:
                bottom_anchored = float(scaled.get("stem_bottom", 0.0)) >= (float(target_h) - 0.5)
                reanchored_top = cy + r - (stem_width * 0.55)
                if bottom_anchored:
                    scaled["stem_top"] = float(Action._clip_scalar(reanchored_top, 0.0, float(target_h)))
                    scaled["stem_bottom"] = float(target_h)
                else:
                    stem_len = max(1.0, float(scaled.get("stem_bottom", reanchored_top)) - float(scaled.get("stem_top", reanchored_top)))
                    scaled["stem_top"] = float(Action._clip_scalar(reanchored_top, 0.0, float(target_h - 1)))
                    scaled["stem_bottom"] = float(
                        Action._clip_scalar(float(scaled["stem_top"]) + stem_len, float(scaled["stem_top"]) + 1.0, float(target_h))
                    )

        scaled["cx"] = cx
        scaled["cy"] = cy
        scaled["r"] = r

    return scaled
