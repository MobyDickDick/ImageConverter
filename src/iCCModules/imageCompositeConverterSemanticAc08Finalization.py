"""AC08 semantic-style finalization helpers extracted from the converter monolith."""

from __future__ import annotations


def finalizeAc08StyleImpl(
    name: str,
    params: dict,
    *,
    light_circle_stroke_gray: int,
    capture_canonical_badge_colors_fn,
    normalize_light_circle_colors_fn,
    normalize_ac08_line_widths_fn,
    normalize_centered_co2_label_fn,
    tune_ac0833_co2_badge_fn,
    needs_large_circle_overflow_guard_fn,
    align_stem_to_circle_center_fn,
    reanchor_arm_to_circle_edge_fn,
    persist_connector_length_floor_fn,
    configure_ac08_small_variant_mode_fn,
    clip_scalar_fn,
) -> dict:
    """Apply AC08xx palette/stroke conventions globally for semantic conversions."""
    canonical_name = str(name).upper()
    symbol_name = canonical_name.split("_", 1)[0]
    if not symbol_name.startswith("AC08"):
        return params
    p = capture_canonical_badge_colors_fn(normalize_light_circle_colors_fn(dict(params)))
    p["badge_symbol_name"] = symbol_name
    p.setdefault("enable_global_search_mode", True)
    p = normalize_ac08_line_widths_fn(p)
    p["lock_colors"] = True
    p = normalize_centered_co2_label_fn(p)
    if symbol_name == "AC0831" and str(p.get("text_mode", "")).lower() == "co2":
        p["fill_gray"] = 238
        p["stroke_gray"] = 155
        p["text_gray"] = 155
        if p.get("stem_enabled"):
            p["stem_gray"] = 155
    if symbol_name == "AC0833" and str(p.get("text_mode", "")).lower() == "co2":
        p = tune_ac0833_co2_badge_fn(p)
    if symbol_name == "AC0820" and str(p.get("text_mode", "")).lower() == "co2":
        p["co2_anchor_mode"] = str(p.get("co2_anchor_mode", "center_co"))
        p["co2_index_mode"] = "superscript"
        p["co2_superscript_offset_scale"] = float(min(float(p.get("co2_superscript_offset_scale", 0.16)), 0.18))
        p["co2_superscript_min_gap_scale"] = float(max(float(p.get("co2_superscript_min_gap_scale", 0.16)), 0.16))
        p["co2_optical_bias"] = 0.125
        r = max(1.0, float(p.get("r", 1.0)))
        if r >= 10.0:
            p["co2_font_scale"] = 0.82
        elif r >= 6.0:
            p["co2_font_scale"] = 0.84
        else:
            p["co2_font_scale"] = 0.86
        base_scale = float(p["co2_font_scale"])
        p["co2_font_scale_min"] = float(max(0.84, base_scale * 0.92))
        p["co2_font_scale_max"] = float(min(1.12, base_scale * 1.22))
        if r >= 10.0:
            p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.90)), 0.90))
        elif r >= 6.0:
            p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.92)), 0.92))
        else:
            p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.94)), 0.94))
        p["co2_sub_font_scale"] = float(p.get("co2_sub_font_scale", 66.0))
        p["co2_subscript_offset_scale"] = 0.27
        template_r = float(p.get("template_circle_radius", r))
        min_radius_ratio = 1.0 if template_r >= 10.0 else 0.95
        p["r"] = float(max(float(p.get("r", template_r)), template_r * min_radius_ratio))
        image_width = float(p.get("width", p.get("badge_width", 0.0)) or 0.0)
        large_centered_co2 = (
            bool(p.get("circle_enabled", True))
            and not bool(p.get("arm_enabled") or p.get("stem_enabled"))
            and str(p.get("co2_anchor_mode", "center_co")).lower() == "center_co"
            and template_r >= 10.0
        )
        if large_centered_co2:
            p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.89)), 0.89))
            p["co2_dy"] = float(max(float(p.get("co2_dy", 0.0)), 0.03 * template_r))
            p["co2_center_co_bias"] = float(min(float(p.get("co2_center_co_bias", -0.05)), -0.05))
        if needs_large_circle_overflow_guard_fn(p) and image_width > 0.0:
            required_r = (image_width / 4.0) + 1e-3
            p["r"] = float(max(float(p.get("r", template_r)), template_r * 0.98, required_r))
            p["circle_radius_lower_bound_px"] = float(max(float(p.get("circle_radius_lower_bound_px", 1.0)), required_r))
    if p.get("circle_enabled", True):
        has_connector = bool(p.get("arm_enabled") or p.get("stem_enabled"))
        has_text = bool(p.get("draw_text", False))
        aspect_ratio = 1.0
        badge_w = float(p.get("badge_width", 0.0))
        badge_h = float(p.get("badge_height", 0.0))
        if badge_w <= 0.0 or badge_h <= 0.0:
            circle_diameter = max(1.0, float(p.get("r", 1.0)) * 2.0)
            extent_w = circle_diameter
            extent_h = circle_diameter
            if p.get("stem_enabled"):
                stem_top = float(p.get("stem_top", float(p.get("cy", 0.0)) + float(p.get("r", 0.0))))
                stem_bottom = float(p.get("stem_bottom", stem_top))
                extent_h = max(extent_h, max(1.0, stem_bottom))
            if p.get("arm_enabled"):
                arm_x1 = float(p.get("arm_x1", float(p.get("cx", 0.0)) - float(p.get("r", 0.0))))
                arm_x2 = float(p.get("arm_x2", float(p.get("cx", 0.0)) + float(p.get("r", 0.0))))
                arm_y1 = float(p.get("arm_y1", float(p.get("cy", 0.0))))
                arm_y2 = float(p.get("arm_y2", float(p.get("cy", 0.0))))
                extent_w = max(extent_w, abs(arm_x2 - arm_x1), max(abs(arm_x1), abs(arm_x2)))
                extent_h = max(extent_h, abs(arm_y2 - arm_y1), max(abs(arm_y1), abs(arm_y2)))
            badge_w = extent_w
            badge_h = extent_h
        if badge_w > 0.0 and badge_h > 0.0:
            aspect_ratio = badge_w / badge_h

        template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
        current_r = float(p.get("r", template_r))
        base_r = max(1.0, template_r, current_r)
        min_ratio = 0.88
        if has_text:
            min_ratio = 0.92 if symbol_name == "AC0820" else 0.90
        elif has_connector and (aspect_ratio >= 1.60 or aspect_ratio <= (1.0 / 1.60)):
            min_ratio = 0.95
        p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), base_r * min_ratio))
        # Keep a generic, non-family-specific lower bound even when adaptive lock
        # keys are stripped below. This prevents underfitting rings in weak-mask
        # cases (e.g. thin anti-aliased circles) without reintroducing hard locks.
        # We intentionally use template-based geometry so it remains stable across
        # variants and image-specific outliers.
        template_floor_ratio = 0.90 if has_text else 0.92
        if has_connector:
            template_floor_ratio = max(template_floor_ratio, 0.93)
        width_fill_floor = 1.0
        if has_connector and has_text and p.get("arm_enabled"):
            # Vertical top/bottom connector families (e.g. AC0813/AC0833/AC0838)
            # usually use a near full-width circle. Enforce a geometric lower
            # bound from the available lateral clearance so weak-mask fits do not
            # collapse to undersized circles.
            arm_x1 = float(p.get("arm_x1", p.get("cx", 0.0)))
            arm_x2 = float(p.get("arm_x2", arm_x1))
            cx_now = float(p.get("cx", 0.0))
            cy_now = float(p.get("cy", 0.0))
            canvas_w = float(p.get("width", p.get("badge_width", 0.0)) or 0.0)
            canvas_h = float(p.get("height", p.get("badge_height", 0.0)) or 0.0)
            stroke = max(0.0, float(p.get("stroke_circle", 0.0)))
            is_vertical_connector = abs(arm_x1 - arm_x2) <= max(0.25, stroke * 0.6)
            if canvas_w <= 0.0:
                template_cx = float(p.get("template_circle_cx", cx_now))
                template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
                canvas_w = max(
                    0.0,
                    float(p.get("arm_x1", 0.0)),
                    float(p.get("arm_x2", 0.0)),
                    cx_now + template_r + (stroke / 2.0),
                    template_cx * 2.0,
                    cx_now * 2.0,
                )
            if canvas_h <= 0.0:
                template_cy = float(p.get("template_circle_cy", cy_now))
                template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
                arm_y1 = float(p.get("arm_y1", 0.0))
                arm_y2 = float(p.get("arm_y2", 0.0))
                canvas_h = max(
                    0.0,
                    cy_now + template_r + (stroke / 2.0),
                    template_cy + template_r + (stroke / 2.0),
                    arm_y1,
                    arm_y2,
                    max(arm_y1, arm_y2) + template_r,
                )
            if is_vertical_connector and canvas_w > 0.0 and canvas_h > 0.0 and cx_now > 0.0 and cy_now > 0.0:
                lateral_clearance = max(1.0, min(cx_now, canvas_w - cx_now) - (stroke / 2.0))
                vertical_clearance = max(1.0, min(cy_now, canvas_h - cy_now) - (stroke / 2.0))
                width_fill_floor = max(1.0, min(lateral_clearance, vertical_clearance))
        p["circle_radius_lower_bound_px"] = float(
            max(
                float(p.get("circle_radius_lower_bound_px", 1.0)),
                max(1.0, template_r * template_floor_ratio),
                width_fill_floor,
            )
        )
        if symbol_name == "AC0838" and str(p.get("text_mode", "")).lower() == "voc":
            # AC0838_M often underfits the ring to satisfy noisy masks around the
            # vertical connector. Keep the circle close to template scale so the
            # VOC badge does not collapse visibly below the source glyph.
            ac0838_radius_floor = max(1.0, template_r * 0.96)
            p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), ac0838_radius_floor))
            p["circle_radius_lower_bound_px"] = float(
                max(float(p.get("circle_radius_lower_bound_px", 1.0)), ac0838_radius_floor)
            )

        if not has_connector:
            p["lock_circle_cx"] = True
            p["lock_circle_cy"] = True

        if has_connector:
            p["lock_circle_cx"] = True
            p["lock_circle_cy"] = True
            if p.get("stem_enabled"):
                p["lock_stem_center_to_circle"] = True
                p["stem_center_lock_max_offset"] = float(max(0.35, float(p.get("stroke_circle", 1.0)) * 0.6))
                p["allow_stem_width_tuning"] = True
                p["stem_width_tuning_px"] = 1.0
            if p.get("arm_enabled"):
                p["lock_arm_center_to_circle"] = True

        geometry_reanchored_to_template = False
        if bool(p.get("lock_circle_cx", False)) and "template_circle_cx" in p:
            p["cx"] = float(p["template_circle_cx"])
            geometry_reanchored_to_template = True
        if bool(p.get("lock_circle_cy", False)) and "template_circle_cy" in p:
            p["cy"] = float(p["template_circle_cy"])
            geometry_reanchored_to_template = True
        if geometry_reanchored_to_template and p.get("circle_enabled", True):
            if p.get("stem_enabled"):
                p = align_stem_to_circle_center_fn(p)
            if p.get("arm_enabled"):
                reanchor_arm_to_circle_edge_fn(p, float(p.get("r", 0.0)))
    if p.get("stem_enabled"):
        persist_connector_length_floor_fn(p, "stem", default_ratio=0.65)
    if p.get("arm_enabled"):
        persist_connector_length_floor_fn(p, "arm", default_ratio=0.75)
    if str(p.get("text_mode", "")).lower() == "co2":
        min_dim = float(min(float(p.get("width", 0.0) or 0.0), float(p.get("height", 0.0) or 0.0)))
        if min_dim <= 0.0:
            min_dim = max(1.0, float(p.get("r", 1.0)) * 2.0)
        tiny_co2_variant = min_dim <= 15.5
        p["lock_text_scale"] = not (symbol_name == "AC0820" or tiny_co2_variant)
        if tiny_co2_variant:
            base_scale = float(p.get("co2_font_scale", 0.82))
            p["co2_font_scale_min"] = float(max(0.74, base_scale * 0.90))
            p["co2_font_scale_max"] = float(min(1.18, base_scale * 1.25))
    if str(p.get("text_mode", "")).lower() == "voc":
        min_dim = float(min(float(p.get("width", 0.0) or 0.0), float(p.get("height", 0.0) or 0.0)))
        if min_dim <= 0.0:
            min_dim = max(1.0, float(p.get("r", 1.0)) * 2.0)
        if symbol_name == "AC0835":
            p["lock_text_scale"] = False
            if min_dim <= 15.5:
                legacy_base_scale = 0.52
                p.setdefault("voc_font_scale_min", float(max(0.58, legacy_base_scale * 0.90)))
                p.setdefault("voc_font_scale_max", float(min(0.92, legacy_base_scale * 1.05)))
            else:
                p["voc_font_scale"] = float(max(float(p.get("voc_font_scale", 0.52)), 0.60))
                p.setdefault("voc_font_scale_min", 0.60)
                p.pop("voc_font_scale_max", None)
    p = configure_ac08_small_variant_mode_fn(name, p)
    preserve_plain_ring_geometry = symbol_name == "AC0800"
    preserved_plain_ring_keys = {
        key: p[key]
        for key in ("lock_circle_cx", "lock_circle_cy", "min_circle_radius", "max_circle_radius")
        if preserve_plain_ring_geometry and key in p
    }
    for key in (
        "lock_circle_cx",
        "lock_circle_cy",
        "lock_stem_center_to_circle",
        "lock_arm_center_to_circle",
        "lock_text_scale",
        "lock_colors",
        "min_circle_radius",
        "max_circle_radius",
        "co2_font_scale_min",
        "co2_font_scale_max",
        "voc_font_scale_min",
        "voc_font_scale_max",
        "fill_gray_min",
        "fill_gray_max",
        "stroke_gray_min",
        "stroke_gray_max",
        "stem_gray_min",
        "stem_gray_max",
        "text_gray_min",
        "text_gray_max",
        "arm_len_min",
        "arm_len_min_ratio",
        "connector_family_group",
        "connector_family_direction",
    ):
        p.pop(key, None)
    if preserve_plain_ring_geometry:
        p.update(preserved_plain_ring_keys)
        if "template_circle_cx" in p:
            p["cx"] = float(p["template_circle_cx"])
        if "template_circle_cy" in p:
            p["cy"] = float(p["template_circle_cy"])
        template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
        min_radius_ratio = 0.96
        if bool(p.get("ac08_small_variant_mode", False)):
            min_radius_ratio = 1.0
        p["min_circle_radius"] = float(max(1.0, template_r * min_radius_ratio))
        cx = float(p.get("cx", p.get("template_circle_cx", template_r)))
        cy = float(p.get("cy", p.get("template_circle_cy", template_r)))
        canvas_w = float(p.get("width", p.get("badge_width", 0.0)) or 0.0)
        canvas_h = float(p.get("height", p.get("badge_height", 0.0)) or 0.0)
        if canvas_w <= 0.0:
            canvas_w = max(float(cx * 2.0), template_r * 2.0)
        if canvas_h <= 0.0:
            canvas_h = max(float(cy * 2.0), template_r * 2.0)
        canvas_fit_r = max(1.0, min(cx, canvas_w - cx, cy, canvas_h - cy) - 0.5)
        if bool(p.get("ac08_small_variant_mode", False)):
            p["max_circle_radius"] = float(max(template_r, template_r * 1.15, canvas_fit_r))
        else:
            p["max_circle_radius"] = float(max(template_r, template_r * 1.15))
        min_r = float(max(1.0, p.get("min_circle_radius", 1.0)))
        max_r = float(max(min_r, p.get("max_circle_radius", min_r)))
        p["max_circle_radius"] = max_r
        p["r"] = float(clip_scalar_fn(float(p.get("r", template_r)), min_r, max_r))
    if p.get("draw_text", True) and "text_gray" in p:
        p["text_gray"] = int(p.get("stroke_gray", light_circle_stroke_gray))
    return p
