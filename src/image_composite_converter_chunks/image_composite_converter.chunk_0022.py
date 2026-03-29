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

    @staticmethod
    def _enforce_vertical_connector_badge_geometry(params: dict, w: int, h: int) -> dict:
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
            stem_width = float(max(1.0, p.get("stem_width", p.get("stroke_circle", Action.AC08_STROKE_WIDTH_PX))))
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
            arm_stroke = float(max(1.0, p.get("arm_stroke", Action.AC08_STROKE_WIDTH_PX)))
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

    @staticmethod
    def _tune_ac08_vertical_connector_family(name: str, params: dict) -> dict:
        """Apply shared guardrails for AC08 families with vertical connectors.

        Aufgabe 4.3 groups AC0811, AC0813, AC0831, AC0833, AC0836 and AC0881 because
        they all depend on a vertical connector staying centered relative to the
        circle. Their main shared regressions are:
        - the stem/arm drifting sideways relative to the circle,
        - the vertical connector shrinking until the badge reads as plain circle,
        - text badges becoming top-heavy once circle and connector alignment drifts.
        """
        p = dict(params)
        symbol_name = get_base_name_from_file(str(name)).upper().split("_", 1)[0]
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
