"""AC08 family-level semantic tuning helpers extracted from the converter monolith."""

from __future__ import annotations


def enforceTemplateCircleEdgeExtentImpl(
    params: dict,
    w: int,
    h: int,
    *,
    anchor: str,
    retain_ratio: float = 0.97,
    max_circle_radius_inside_canvas_fn,
) -> dict:
    """Keep edge-anchored circles close to the template edge reach."""
    p = dict(params)
    if not p.get("circle_enabled", True):
        return p
    if "cx" not in p or "r" not in p:
        return p
    if "template_circle_cx" not in p or "template_circle_radius" not in p:
        return p

    retain_ratio = float(max(0.90, min(1.00, retain_ratio)))
    cx = float(p["cx"])
    template_cx = float(p["template_circle_cx"])
    template_r = max(1.0, float(p["template_circle_radius"]))
    stroke = float(max(0.0, p.get("stroke_circle", 0.0)))
    canvas_cap = float(max_circle_radius_inside_canvas_fn(cx, float(p.get("cy", float(h) / 2.0)), w, h, stroke))

    if anchor == "right":
        template_extent = template_cx + template_r
        required_extent = template_extent * retain_ratio
        required_r = required_extent - cx
    elif anchor == "left":
        template_extent = template_cx - template_r
        required_extent = template_extent + ((1.0 - retain_ratio) * abs(template_extent))
        required_r = cx - required_extent
    else:
        return p

    required_r = float(max(1.0, min(canvas_cap, required_r)))
    if required_r > 1.0:
        p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), required_r))
    return p


def enforceVerticalConnectorBadgeGeometryImpl(
    params: dict,
    w: int,
    h: int,
    *,
    ac08_stroke_width_px: float,
) -> dict:
    """Ensure AC0811/AC0813-like badges keep a centered visible vertical connector."""
    p = dict(params)
    if not p.get("circle_enabled", True):
        return p
    if "cx" not in p or "cy" not in p or "r" not in p:
        return p

    cx = float(p["cx"])
    cy = float(p["cy"])
    r = float(p["r"])
    canvas_height = max(
        float(h),
        float(p.get("height", 0.0) or 0.0),
        float(p.get("badge_height", 0.0) or 0.0),
        float(p.get("stem_bottom", 0.0) or 0.0),
        cy + r,
    )

    if p.get("stem_enabled"):
        stem_width = float(max(1.0, p.get("stem_width", p.get("stroke_circle", ac08_stroke_width_px))))
        p["stem_enabled"] = True
        p["stem_width"] = stem_width
        p["stem_x"] = cx - (stem_width / 2.0)
        p["stem_top"] = cy + r - (stem_width * 0.55)
        p["stem_bottom"] = canvas_height
        stem_len = float(max(0.0, canvas_height - (cy + r)))
        ratio = float(max(0.0, min(1.0, float(p.get("stem_len_min_ratio", 0.65)))))
        p["stem_len_min_ratio"] = ratio
        p["stem_len_min"] = float(max(1.0, float(p.get("stem_len_min", 1.0)), stem_len * ratio))

    if p.get("arm_enabled"):
        arm_stroke = float(max(1.0, p.get("arm_stroke", ac08_stroke_width_px)))
        top_extent = max(0.0, cy - r)
        p["arm_enabled"] = True
        p["arm_stroke"] = arm_stroke
        p["arm_x1"] = cx
        p["arm_x2"] = cx
        p["arm_y1"] = 0.0
        p["arm_y2"] = top_extent
        arm_len = float(max(0.0, top_extent))
        ratio = float(max(0.0, min(1.0, float(p.get("arm_len_min_ratio", 0.75)))))
        p["arm_len_min_ratio"] = ratio
        p["arm_len_min"] = float(max(1.0, float(p.get("arm_len_min", 1.0)), arm_len * ratio))
    return p


def tuneAc08LeftConnectorFamilyImpl(
    name: str,
    params: dict,
    *,
    get_base_name_from_file_fn,
    is_ac08_small_variant_fn,
    enforce_template_circle_edge_extent_fn,
    enforce_left_arm_badge_geometry_fn,
    center_glyph_bbox_fn,
) -> dict:
    """Apply shared guardrails for left-connector AC08 families."""
    p = dict(params)
    symbol_name = get_base_name_from_file_fn(str(name)).upper().split("_", 1)[0]
    if symbol_name not in {"AC0812", "AC0832", "AC0837", "AC0882"}:
        return p

    p["connector_family_group"] = "ac08_left_connector"
    p["connector_family_direction"] = "left"
    p["lock_circle_cx"] = True
    p["lock_circle_cy"] = True
    if "template_circle_cx" in p:
        p["cx"] = float(p["template_circle_cx"])
    if "template_circle_cy" in p:
        p["cy"] = float(p["template_circle_cy"])

    has_text = bool(p.get("draw_text", False))
    text_mode = str(p.get("text_mode", "")).lower()
    is_small, _reason, min_dim = is_ac08_small_variant_fn(str(name), p)
    arm_ratio_floor = 0.82
    if has_text or text_mode == "path_t":
        arm_ratio_floor = 0.84
    if is_small:
        arm_ratio_floor = max(arm_ratio_floor, 0.86)
    p["arm_len_min_ratio"] = float(max(float(p.get("arm_len_min_ratio", arm_ratio_floor)), arm_ratio_floor))

    template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
    radius_floor_ratio = 0.95 if not has_text else 0.93
    if is_small:
        radius_floor_ratio = max(radius_floor_ratio, 0.96 if not has_text else 0.94)
    p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), template_r * radius_floor_ratio))
    p = enforce_template_circle_edge_extent_fn(
        p,
        int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
        int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
        anchor="right",
        retain_ratio=0.97 if not is_small else 0.96,
    )

    p = enforce_left_arm_badge_geometry_fn(
        p,
        int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
        int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
    )

    if p.get("arm_enabled") and "cx" in p:
        max_from_arm_floor = max(1.0, float(p["cx"]) - float(p.get("arm_len_min", 1.0)))
        existing_max = float(p.get("max_circle_radius", 0.0) or 0.0)
        if existing_max > 0.0:
            p["max_circle_radius"] = float(min(existing_max, max_from_arm_floor))
        else:
            p["max_circle_radius"] = float(max_from_arm_floor)

    text_mode = str(p.get("text_mode", "")).lower()
    if text_mode == "co2":
        base_scale = float(p.get("co2_font_scale", 0.82))
        p["lock_text_scale"] = False
        p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.78, base_scale * 0.94)))
        p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.12)), min(1.12, base_scale * 1.15)))
        p["co2_anchor_mode"] = str(p.get("co2_anchor_mode", "cluster"))
    elif text_mode == "voc":
        base_scale = float(p.get("voc_font_scale", 0.52))
        p["lock_text_scale"] = False
        p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.50, base_scale * 0.94)))
        p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.98)), min(0.98, base_scale * 1.14)))
    elif text_mode == "path_t":
        p["s"] = float(max(float(p.get("s", 0.0)), 0.0088 if min_dim >= 18.0 else 0.0082))
        center_glyph_bbox_fn(p)
    return p


def tuneAc08RightConnectorFamilyImpl(
    name: str,
    params: dict,
    *,
    get_base_name_from_file_fn,
    is_ac08_small_variant_fn,
    enforce_template_circle_edge_extent_fn,
    enforce_right_arm_badge_geometry_fn,
) -> dict:
    """Apply shared guardrails for mirrored right-connector AC08 families."""
    p = dict(params)
    symbol_name = get_base_name_from_file_fn(str(name)).upper().split("_", 1)[0]
    if symbol_name not in {"AC0810", "AC0814", "AC0834", "AC0838", "AC0839"}:
        return p

    p["connector_family_group"] = "ac08_right_connector"
    p["connector_family_direction"] = "right"
    p["lock_circle_cx"] = True
    p["lock_circle_cy"] = True
    if "template_circle_cx" in p:
        p["cx"] = float(p["template_circle_cx"])
    if "template_circle_cy" in p:
        p["cy"] = float(p["template_circle_cy"])

    has_text = bool(p.get("draw_text", False))
    text_mode = str(p.get("text_mode", "")).lower()
    is_small, _reason, _min_dim = is_ac08_small_variant_fn(str(name), p)
    arm_ratio_floor = 0.82
    if has_text or text_mode == "path_t":
        arm_ratio_floor = 0.84
    if is_small:
        arm_ratio_floor = max(arm_ratio_floor, 0.86)
    p["arm_len_min_ratio"] = float(max(float(p.get("arm_len_min_ratio", arm_ratio_floor)), arm_ratio_floor))

    template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
    radius_floor_ratio = 0.95 if not has_text else 0.93
    if is_small:
        radius_floor_ratio = max(radius_floor_ratio, 0.96 if not has_text else 0.94)
    p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), template_r * radius_floor_ratio))
    p = enforce_template_circle_edge_extent_fn(
        p,
        int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
        int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
        anchor="left",
        retain_ratio=0.97 if not is_small else 0.96,
    )

    p = enforce_right_arm_badge_geometry_fn(
        p,
        int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
        int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
    )

    if p.get("arm_enabled") and "cx" in p and "r" in p:
        canvas_width = float(p.get("width", 0.0) or p.get("badge_width", 0.0) or p.get("arm_x2", 0.0) or 1.0)
        right_extent = max(float(p["cx"]) + float(p["r"]), 0.0)
        max_from_arm_floor = max(1.0, canvas_width - float(p.get("arm_len_min", 1.0)) - float(p["cx"]))
        existing_max = float(p.get("max_circle_radius", 0.0) or 0.0)
        bounded_max = min(max_from_arm_floor, max(1.0, right_extent))
        if existing_max > 0.0:
            p["max_circle_radius"] = float(min(existing_max, bounded_max))
        else:
            p["max_circle_radius"] = float(bounded_max)

    text_mode = str(p.get("text_mode", "")).lower()
    if text_mode == "co2":
        base_scale = float(p.get("co2_font_scale", 0.82))
        p["lock_text_scale"] = False
        p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.78, base_scale * 0.94)))
        p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.12)), min(1.12, base_scale * 1.15)))
        p["co2_anchor_mode"] = str(p.get("co2_anchor_mode", "cluster"))
    elif text_mode == "voc":
        base_scale = float(p.get("voc_font_scale", 0.52))
        p["lock_text_scale"] = False
        p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.50, base_scale * 0.94)))
        p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.98)), min(0.98, base_scale * 1.14)))
    return p


def tuneAc08VerticalConnectorFamilyImpl(
    name: str,
    params: dict,
    *,
    get_base_name_from_file_fn,
    is_ac08_small_variant_fn,
    enforce_vertical_connector_badge_geometry_fn,
) -> dict:
    """Apply shared guardrails for AC08 families with vertical connectors."""
    p = dict(params)
    symbol_name = get_base_name_from_file_fn(str(name)).upper().split("_", 1)[0]
    if symbol_name not in {"AC0811", "AC0813", "AC0831", "AC0833", "AC0836", "AC0881"}:
        return p

    p["connector_family_group"] = "ac08_vertical_connector"
    p["connector_family_direction"] = "vertical"
    if symbol_name in {"AC0811", "AC0831", "AC0836", "AC0881"}:
        p["stem_enabled"] = True
        p.pop("arm_enabled", None)
    elif symbol_name in {"AC0813", "AC0833"}:
        p["arm_enabled"] = True
    p["lock_circle_cx"] = True
    p["lock_circle_cy"] = True
    p["lock_stem_center_to_circle"] = bool(p.get("stem_enabled", False))
    p["lock_arm_center_to_circle"] = bool(p.get("arm_enabled", False))
    if "template_circle_cx" in p:
        p["cx"] = float(p["template_circle_cx"])
    if "template_circle_cy" in p:
        p["cy"] = float(p["template_circle_cy"])

    has_text = bool(p.get("draw_text", False))
    is_small, _reason, min_dim = is_ac08_small_variant_fn(str(name), p)
    template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
    radius_floor_ratio = 0.95 if not has_text else 0.93
    if is_small:
        radius_floor_ratio = max(radius_floor_ratio, 0.96 if not has_text else 0.95)
    p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), template_r * radius_floor_ratio))

    if p.get("stem_enabled"):
        stem_ratio_floor = 0.70 if not has_text else 0.72
        if is_small:
            stem_ratio_floor = max(stem_ratio_floor, 0.74)
        p["stem_len_min_ratio"] = float(max(float(p.get("stem_len_min_ratio", stem_ratio_floor)), stem_ratio_floor))
    if p.get("arm_enabled"):
        arm_ratio_floor = 0.78 if not has_text else 0.80
        if is_small:
            arm_ratio_floor = max(arm_ratio_floor, 0.82)
        p["arm_len_min_ratio"] = float(max(float(p.get("arm_len_min_ratio", arm_ratio_floor)), arm_ratio_floor))

    p = enforce_vertical_connector_badge_geometry_fn(
        p,
        int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
        int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
    )

    text_mode = str(p.get("text_mode", "")).lower()
    if text_mode == "co2":
        base_scale = float(p.get("co2_font_scale", 0.82))
        p["lock_text_scale"] = False
        p["co2_anchor_mode"] = "cluster"
        p["co2_optical_bias"] = float(max(float(p.get("co2_optical_bias", 0.10)), 0.10))
        p["co2_dy"] = float(max(float(p.get("co2_dy", 0.0)), 0.05 * template_r if min_dim > 0.0 else 0.0))
        p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.78, base_scale * 0.94)))
        p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.12)), min(1.12, base_scale * 1.15)))
    elif text_mode == "voc":
        base_scale = float(p.get("voc_font_scale", 0.52))
        p["lock_text_scale"] = False
        p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.50, base_scale * 0.94)))
        p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.98)), min(0.98, base_scale * 1.14)))
    return p


def tuneAc08CircleTextFamilyImpl(
    name: str,
    params: dict,
    *,
    get_base_name_from_file_fn,
    max_circle_radius_inside_canvas_fn,
    center_glyph_bbox_fn,
) -> dict:
    """Apply shared guardrails for connector-free AC08 circle/text badges."""
    p = dict(params)
    symbol_name = get_base_name_from_file_fn(str(name)).upper().split("_", 1)[0]
    if symbol_name not in {"AC0820", "AC0835", "AC0870"}:
        return p

    p["connector_family_group"] = "ac08_circle_text"
    p["connector_family_direction"] = "centered"
    p["lock_circle_cx"] = True
    p["lock_circle_cy"] = True

    if "template_circle_cx" in p:
        p["cx"] = float(p["template_circle_cx"])
    if "template_circle_cy" in p:
        p["cy"] = float(p["template_circle_cy"])

    template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
    min_dim = float(
        min(
            float(p.get("width", 0.0) or 0.0),
            float(p.get("height", 0.0) or 0.0),
        )
    )
    if min_dim <= 0.0:
        min_dim = max(1.0, template_r * 2.0)

    text_mode = str(p.get("text_mode", "")).lower()
    radius_floor_ratio = 0.94 if text_mode in {"co2", "voc"} else 0.96
    p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), template_r * radius_floor_ratio))

    canvas_w = int(round(float(p.get("width", 0.0) or p.get("badge_width", 0.0) or min_dim)))
    canvas_h = int(round(float(p.get("height", 0.0) or p.get("badge_height", 0.0) or min_dim)))
    if canvas_w > 0 and canvas_h > 0 and "cx" in p and "cy" in p:
        canvas_cap = max_circle_radius_inside_canvas_fn(
            float(p["cx"]),
            float(p["cy"]),
            canvas_w,
            canvas_h,
            float(p.get("stroke_circle", 1.0)),
        )
        relaxed_cap = max(template_r * 1.08, float(p.get("max_circle_radius", 0.0) or 0.0))
        p["max_circle_radius"] = float(min(canvas_cap, relaxed_cap)) if canvas_cap > 0.0 else float(relaxed_cap)

    if text_mode == "co2":
        base_scale = float(p.get("co2_font_scale", 0.94 if symbol_name == "AC0820" else 0.88))
        p["lock_text_scale"] = False
        p["co2_anchor_mode"] = "cluster"
        p["co2_optical_bias"] = float(max(float(p.get("co2_optical_bias", 0.125)), 0.125 if symbol_name == "AC0820" else 0.10))
        p["co2_dy"] = float(max(-0.06 * template_r, min(0.16 * template_r, float(p.get("co2_dy", 0.03 * template_r)))))
        p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.84, base_scale * 0.92)))
        p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.12)), min(1.12, base_scale * 1.18)))
    elif text_mode == "voc":
        base_scale = float(p.get("voc_font_scale", 0.52))
        p["lock_text_scale"] = False
        p["voc_dy"] = float(max(-0.06 * template_r, min(0.08 * template_r, float(p.get("voc_dy", 0.0)))))
        if min_dim <= 15.5:
            p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.50, base_scale * 0.96)))
            p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.92)), min(0.92, max(base_scale, 0.52) * 1.05)))
        else:
            p["voc_font_scale"] = float(max(base_scale, 0.60))
            p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", p["voc_font_scale"])), 0.60))
            p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 1.02)), 1.02))
    else:
        p["s"] = float(max(float(p.get("s", 0.0100)), 0.0100))
        center_glyph_bbox_fn(p)

    return p
