            radius_floor_ratio = max(radius_floor_ratio, 0.96 if not has_text else 0.94)
        p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), template_r * radius_floor_ratio))
        p = Action._enforce_template_circle_edge_extent(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
            anchor="right",
            retain_ratio=0.97 if not is_small else 0.96,
        )

        p = Action._enforce_left_arm_badge_geometry(
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
        elif str(p.get("text_mode", "")).lower() == "path_t":
            p["s"] = float(max(float(p.get("s", 0.0)), 0.0088 if min_dim >= 18.0 else 0.0082))
            Action._center_glyph_bbox(p)
        return p

    @staticmethod
    def _tune_ac08_right_connector_family(name: str, params: dict) -> dict:
        """Apply shared guardrails for mirrored right-connector AC08 families.

        Aufgabe 4.2 groups AC0810, AC0814, AC0834, AC0838 and AC0839
        because they all place the circle on the left and extend the connector
        toward the right canvas edge. Their common regressions mirror the left
        connector family:
        - the circle drifts right into the connector span,
        - the arm collapses until the badge looks almost circular, and
        - tiny right-arm text badges drift down/right when text pixels dominate.

        Keep those mirrored families on one semantic baseline before applying
        family-specific CO₂/VOC or small-variant adjustments.
        """
        p = dict(params)
        symbol_name = get_base_name_from_file(str(name)).upper().split("_", 1)[0]
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
        is_small, _reason, min_dim = Action._is_ac08_small_variant(str(name), p)
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
        p = Action._enforce_template_circle_edge_extent(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
            anchor="left",
            retain_ratio=0.97 if not is_small else 0.96,
        )

        p = Action._enforce_right_arm_badge_geometry(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
        )

        if p.get("arm_enabled") and "cx" in p and "r" in p:
