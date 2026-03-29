        if p.get("stem_enabled"):
            p["stem_len_min_ratio"] = float(max(float(p.get("stem_len_min_ratio", 0.65)), 0.70))
            Action._persist_connector_length_floor(p, "stem", default_ratio=0.70)

        text_mode = str(p.get("text_mode", "")).lower()
        if text_mode == "co2":
            base_scale = float(p.get("co2_font_scale", 0.82))
            p["lock_text_scale"] = False
            p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.74, base_scale * 0.92)))
            p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.18)), min(1.10, base_scale * 1.12)))
            p["co2_subscript_offset_scale"] = float(min(float(p.get("co2_subscript_offset_scale", 0.24)), 0.24))
        elif text_mode == "voc":
            base_scale = float(p.get("voc_font_scale", 0.52))
            p["lock_text_scale"] = False
            p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.46, base_scale * 0.92)))
            p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.96)), min(0.96, base_scale * 1.10)))
        return p

    @staticmethod
    def _enforce_template_circle_edge_extent(params: dict, w: int, h: int, *, anchor: str, retain_ratio: float = 0.97) -> dict:
        """Keep edge-anchored circles close to template edge reach.

        Generic safeguard for all edge-anchored connector families:
        if optimization shortens the anchored side too much (e.g. right arc on
        AC0812-like badges), raise `min_circle_radius` so the anchored contour
        keeps at least `retain_ratio` of the template extent.
        """
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
        canvas_cap = float(Action._max_circle_radius_inside_canvas(cx, float(p.get("cy", float(h) / 2.0)), w, h, stroke))

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


    @staticmethod
    def _tune_ac08_left_connector_family(name: str, params: dict) -> dict:
        """Apply shared guardrails for left-connector AC08 families.

        Aufgabe 4.1 groups AC0812, AC0832, AC0837 and AC0882 because they all
        combine a circle on the right with a left-facing horizontal connector.
        The shared failure modes are:
        - the circle drifting left into the connector,
        - the arm collapsing until it becomes barely visible, and
        - text badges shrinking/offsetting once the circle geometry drifts.

        Keep those families on a common semantic baseline before variant-specific
        fine-tuning runs.
        """
        p = dict(params)
        symbol_name = get_base_name_from_file(str(name)).upper().split("_", 1)[0]
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
