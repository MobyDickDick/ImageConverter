    @staticmethod
    def _enforce_right_arm_badge_geometry(params: dict, w: int, h: int) -> dict:
        """Ensure AC0810/AC0814-like badges always keep a visible right connector arm."""
        p = dict(params)
        if not p.get("circle_enabled", True):
            return p
        if "cx" not in p or "cy" not in p or "r" not in p:
            return p

        cx = float(p["cx"])
        cy = float(p["cy"])
        r = float(p["r"])
        arm_stroke = float(max(1.0, p.get("arm_stroke", Action.AC08_STROKE_WIDTH_PX)))
        attach_offset = max(0.0, arm_stroke / 2.0)
        canvas_width = max(float(w), float(p.get("arm_x2", 0.0) or 0.0), float(p.get("width", 0.0) or 0.0), float(p.get("badge_width", 0.0) or 0.0), cx + r)
        ratio = float(max(0.0, min(1.0, float(p.get("arm_len_min_ratio", 0.75)))))
        requested_min_len = float(max(1.0, float(p.get("arm_len_min", 1.0))))
        requested_min_len = float(min(requested_min_len, canvas_width * 0.35))
        semantic_min_len = float(
            max(
                requested_min_len,
                ratio * max(1.0, canvas_width * 0.20),
            )
        )
        if str(p.get("text_mode", "")).lower() in {"co2", "voc"}:
            semantic_min_len = float(max(semantic_min_len, canvas_width * 0.20))
        arm_start = cx + r + attach_offset
        max_arm_start = max(0.0, canvas_width - semantic_min_len)
        if arm_start > max_arm_start:
            cx = max(r + attach_offset, cx - (arm_start - max_arm_start))
            p["cx"] = cx
        max_r_for_semantic_span = max(1.0, canvas_width - semantic_min_len - attach_offset - cx)
        if r > max_r_for_semantic_span:
            r = max_r_for_semantic_span
            p["r"] = r
        arm_x1 = min(canvas_width, cx + r + attach_offset)

        p["arm_enabled"] = True
        p["arm_x1"] = arm_x1
        p["arm_y1"] = cy
        p["arm_x2"] = canvas_width
        p["arm_y2"] = cy
        p["arm_stroke"] = arm_stroke

        arm_len = float(max(0.0, canvas_width - arm_x1))
        p["arm_len_min_ratio"] = ratio
        p["arm_len_min"] = float(max(semantic_min_len, arm_len * ratio))
        return p

    @staticmethod
    def _default_ac0813_params(w: int, h: int) -> dict:
        """AC0813 is AC0812 rotated 90° clockwise (vertical arm from top to circle)."""
        if w <= 0 or h <= 0:
            return Action._default_ac081x_shared(w, h)

        # Like other edge-anchored connector badges, size from the narrow side and
        # keep a small optical clearance from the anchored edge.
        circle = Action._default_edge_anchored_circle_geometry(w, h, anchor="bottom")
        cx = float(circle["cx"])
        cy = float(circle["cy"])
        r = float(circle["r"])
        stroke_circle = float(circle["stroke_circle"])
        arm_stroke = max(1.0, float(w) * 0.10)

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
                "arm_x1": cx,
                "arm_y1": 0.0,
                "arm_x2": cx,
                "arm_y2": max(0.0, cy - r),
                "arm_stroke": arm_stroke,
            }
        )

    @staticmethod
    def _fit_ac0813_params_from_image(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0813 while keeping the vertical arm anchored to the upper edge."""
        params = Action._fit_semantic_badge_from_image(img, defaults)
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

