        if "template_circle_cy" in p:
            p["cy"] = float(p["template_circle_cy"])

        has_text = bool(p.get("draw_text", False))
        is_small, _reason, min_dim = Action._is_ac08_small_variant(str(name), p)
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

        p = Action._enforce_vertical_connector_badge_geometry(
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

    @staticmethod
    def _tune_ac08_circle_text_family(name: str, params: dict) -> dict:
        """Apply shared guardrails for connector-free AC08 circle/text badges.

        Aufgabe 4.4 groups AC0820, AC0835 and AC0870 because they all:
        - have no connector geometry that should influence circle fitting,
        - regress when text blobs pull the circle away from the semantic center,
        - need stable text scaling without letting the ring collapse or overgrow.
        """
        p = dict(params)
        symbol_name = get_base_name_from_file(str(name)).upper().split("_", 1)[0]
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
            canvas_cap = Action._max_circle_radius_inside_canvas(
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
