            default_r = float(h) * 0.4

            p["cy"] = default_cy
            p["r"] = max(default_r * 0.95, float(p.get("r", default_r)))
            cx = float(p.get("cx", float(h) / 2.0))
            p["arm_y1"] = default_cy
            p["arm_y2"] = default_cy
            p["arm_x1"] = min(float(w), cx + float(p["r"]))
            p["arm_x2"] = float(w)

            p["co2_font_scale"] = min(float(p.get("co2_font_scale", 0.82)), 0.86)
            p["co2_sub_font_scale"] = min(float(p.get("co2_sub_font_scale", 66.0)), 64.0)

        return p

    @staticmethod
    def _default_ac0834_params(w: int, h: int) -> dict:
        """Compatibility helper for AC0834 semantic tests and callers."""
        return Action._tune_ac0834_co2_badge(Action._apply_co2_label(Action._default_ac0814_params(w, h)), w, h)

    @staticmethod
    def _normalize_centered_co2_label(params: dict) -> dict:
        """Normalize CO₂ label sizing for plain circular badges.

        This keeps CO₂ text proportionate to the inner circle diameter for any
        centered (connector-free) semantic badge instead of tuning a single SKU.
        """
        p = dict(params)
        if str(p.get("text_mode", "")).lower() != "co2":
            return p
        if p.get("arm_enabled") or p.get("stem_enabled"):
            return p
        if not p.get("circle_enabled", True):
            return p

        r = max(1.0, float(p.get("r", 1.0)))
        stroke = max(0.8, float(p.get("stroke_circle", 1.0)))
        inner_diameter = max(2.0, (2.0 * r) - stroke)

        cur_scale = float(p.get("co2_font_scale", 0.82))
        cur_font = max(4.0, r * cur_scale)
        cur_width = cur_font * 1.45
        # Keep centered CO₂ labels readable but prevent oversized "CO" glyphs
        # that can visually rival the ring diameter on AC0820-like badges.
        target_width = inner_diameter * 0.68

        adjusted_scale = cur_scale * (target_width / max(1e-6, cur_width))
        min_scale = 0.72 if r >= 8.0 else 0.74
        p["co2_font_scale"] = float(max(min_scale, min(0.96, adjusted_scale)))
        p["co2_sub_font_scale"] = float(max(60.0, min(68.0, float(p.get("co2_sub_font_scale", 66.0)))))
        p["co2_dx"] = float(max(-0.18 * r, min(0.18 * r, float(p.get("co2_dx", -0.04 * r)))))
        p["co2_dy"] = float(max(-0.20 * r, min(0.20 * r, float(p.get("co2_dy", 0.03 * r)))))
        p["text_gray"] = int(round(p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY)))
        return p

    @staticmethod
    def _default_ac0812_params(w: int, h: int) -> dict:
        """AC0812 is horizontally elongated: left arm, circle on the right."""
        if w <= 0 or h <= 0:
            return Action._default_ac081x_shared(w, h)

        # Like AC0811/AC0813, size from the narrow side so tiny variants keep
        # the intended visual circle diameter.
        # AC0812 source rasters leave a slightly larger vertical margin around the
        # ring than AC0811/AC0813. Using 0.40*h tends to over-size the circle.
        r = float(h) * 0.36
        stroke_circle = max(0.9, float(h) / 15.0)
        cx = float(w) - (float(h) / 2.0)
        cy = float(h) / 2.0
        arm_stroke = max(1.0, float(h) * 0.10)

        return Action._normalize_light_circle_colors(
            {
                "cx": cx,
                "cy": cy,
                "r": r,
                "stroke_circle": stroke_circle,
                "stroke_gray": Action.LIGHT_CIRCLE_STROKE_GRAY,
                "fill_gray": Action.LIGHT_CIRCLE_FILL_GRAY,
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

    @staticmethod
    def _fit_ac0812_params_from_image(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0812 while keeping the horizontal arm anchored to the left edge."""
        params = Action._fit_semantic_badge_from_image(img, defaults)
        h, w = img.shape[:2]
        aspect_ratio = (float(w) / float(h)) if h > 0 else 1.0

        raw_arm_stroke = float(params.get("arm_stroke", defaults.get("arm_stroke", max(1.0, float(h) * 0.10))))
        cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
        cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
