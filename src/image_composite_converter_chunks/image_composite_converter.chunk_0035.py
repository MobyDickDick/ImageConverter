        r = float(params.get("r", defaults.get("r", float(h) * 0.4)))
        stroke_circle = float(params.get("stroke_circle", defaults.get("stroke_circle", max(0.9, float(h) / 15.0))))

        min_arm_stroke = max(1.0, stroke_circle * 0.75)
        max_arm_stroke = max(min_arm_stroke, min(float(h) * 0.14, stroke_circle * 1.6))
        arm_stroke = max(min_arm_stroke, min(raw_arm_stroke, max_arm_stroke))

        default_r = float(defaults.get("r", float(h) * 0.4))
        # Why circles can become too large here:
        # - AC0812 has a circle touching the right side and an extra left arm.
        # - On anti-aliased rasters, contour/Hough fitting may merge ring edge,
        #   arm and border pixels into one oversized blob.
        # Keep fitting adaptive, but bounded by generic geometric plausibility
        # instead of variant-specific hard caps. This keeps elongated connector
        # symbols (including AC0812_L-like forms) free to grow when needed while
        # still avoiding runaway radii from anti-aliased merged contours.
        canvas_r_limit = Action._max_circle_radius_inside_canvas(cx, cy, w, h, stroke_circle)
        max_r = max(default_r * 1.45, default_r + 3.0)
        max_r = min(max_r, canvas_r_limit)
        r = min(r, max_r)

        if h <= 15 and not bool(params.get("draw_text", True)):
            # Tiny plain connector badges can lose roughly one anti-aliased ring
            # pixel in contour/Hough fitting; keep them close to template size.
            r = max(r, default_r * 0.98)

        # Elongated connector badges are prone to under-estimating the ring when
        # the connector bleeds into the contour mask. Apply a generic floor for
        # broad, no-text forms rather than pinning a single SKU.
        if aspect_ratio >= 1.60 and h >= 20 and not bool(params.get("draw_text", True)):
            r = max(r, default_r * 0.95)

        params["r"] = r

        params["arm_enabled"] = True
        params["arm_stroke"] = arm_stroke
        params["arm_x1"] = 0.0
        params["arm_y1"] = cy
        attach_offset = max(0.0, arm_stroke / 2.0)
        params["arm_x2"] = max(0.0, cx - r - attach_offset)
        params["arm_y2"] = cy
        current_arm_len = float(math.hypot(params["arm_x2"] - params["arm_x1"], params["arm_y2"] - params["arm_y1"]))
        default_arm_len = max(
            0.0,
            float(defaults.get("cx", float(w) / 2.0)) - float(defaults.get("r", float(h) * 0.4)),
        )
        # Keep AC0812 connector geometry anchored to the semantic template. If we
        # derive the minimum arm length from an already-overgrown fitted circle,
        # later circle optimization can converge to the same unstable large-radius
        # solution. Use the template arm span as the lower bound baseline instead.
        semantic_arm_len_min = max(1.0, default_arm_len * 0.75)
        params["arm_len_min"] = max(1.0, current_arm_len * 0.75, semantic_arm_len_min)
        min_arm_len_ratio = 0.75
        # For elongated AC0812 variants (L-like forms), preserve a visibly long
        # connector arm so circle-fitting noise cannot eat too much horizontal
        # span. This keeps the left arm close to the semantic template.
        if aspect_ratio >= 1.60 and h >= 20 and not bool(params.get("draw_text", True)):
            min_arm_len_ratio = 0.82
        params["arm_len_min_ratio"] = float(max(float(params.get("arm_len_min_ratio", min_arm_len_ratio)), min_arm_len_ratio))
        params["arm_len_min"] = max(
            float(params["arm_len_min"]),
            max(1.0, current_arm_len * float(params["arm_len_min_ratio"]), semantic_arm_len_min),
        )

        # Expose a stable upper radius bound for later stochastic/adaptive circle
        # searches. This prevents left-arm AC0812 variants from re-growing the
        # circle and shortening the mandatory connector arm during optimization.
        max_r_from_arm_span = max(1.0, cx - params["arm_len_min"])
        params["max_circle_radius"] = float(min(canvas_r_limit, max_r_from_arm_span))
        return Action._normalize_light_circle_colors(params)

    @staticmethod
    def _enforce_left_arm_badge_geometry(params: dict, w: int, h: int) -> dict:
        """Ensure AC0812-like badges always keep a visible left connector arm."""
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
        arm_x2 = max(0.0, cx - r - attach_offset)

        p["arm_enabled"] = True
        p["arm_x1"] = 0.0
        p["arm_y1"] = cy
        p["arm_x2"] = arm_x2
        p["arm_y2"] = cy
        p["arm_stroke"] = arm_stroke

        arm_len = float(max(0.0, arm_x2))
        ratio = float(max(0.0, min(1.0, float(p.get("arm_len_min_ratio", 0.75)))))
        p["arm_len_min_ratio"] = ratio
        p["arm_len_min"] = float(max(1.0, float(p.get("arm_len_min", 1.0)), arm_len * ratio))
        return p

