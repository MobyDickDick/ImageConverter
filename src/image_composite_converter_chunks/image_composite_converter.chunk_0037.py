        if w <= 15 and not bool(params.get("draw_text", True)):
            # Tiny plain connector badges can lose roughly one anti-aliased ring
            # pixel in contour/Hough fitting; keep them near template size.
            r = max(r, default_r * 0.98)

        elongated_plain_badge = aspect_ratio >= 1.60 and w >= 20 and not bool(params.get("draw_text", True))
        if elongated_plain_badge:
            # AC0813_L-like forms are the vertical counterpart of AC0812_L/AC0814_L:
            # JPEG antialiasing around the top connector often biases the detected
            # ring inward, so preserve a tighter semantic radius floor here too.
            r = max(r, default_r * 0.95)
            params["min_circle_radius"] = float(max(float(params.get("min_circle_radius", 1.0)), default_r * 0.95))

        params["r"] = r

        # Tiny vertical badges with text overlays (e.g. AC0833_S / AC0838_S)
        # tend to be over-influenced by anti-aliased text pixels during contour
        # fitting. This can pull the circle downward and shrink its radius, which
        # shortens the visible top connector. Keep small variants close to the
        # semantic template geometry and only allow minimal vertical drift.
        if w <= 15 and bool(params.get("draw_text", False)):
            default_cx = float(defaults.get("cx", float(w) / 2.0))
            default_cy = float(defaults.get("cy", float(h) - (float(w) / 2.0)))
            default_r = float(defaults.get("r", float(w) * 0.4))
            params["cx"] = default_cx
            params["cy"] = float(Action._clip_scalar(cy, default_cy - 0.8, default_cy + 0.8))
            params["r"] = max(r, default_r * 0.94)
            params["lock_circle_cx"] = True
            params["lock_circle_cy"] = True
            params["lock_arm_center_to_circle"] = True
            cx = float(params["cx"])
            cy = float(params["cy"])
            r = float(params["r"])

        params["arm_enabled"] = True
        params["arm_stroke"] = arm_stroke
        params["arm_x1"] = cx
        params["arm_y1"] = 0.0
        params["arm_x2"] = cx
        params["arm_y2"] = max(0.0, cy - r)
        return Action._normalize_light_circle_colors(params)

    @staticmethod
    def _rotate_semantic_badge_clockwise(params: dict, w: int, h: int) -> dict:
        cx = float(w) / 2.0
        cy = float(h) / 2.0

        def rotate_clockwise(x: float, y: float) -> tuple[float, float]:
            # image-space clockwise description maps to mathematically counter-clockwise
            # because y grows downward in raster coordinates.
            return cx - (y - cy), cy + (x - cx)

        rotated = dict(params)
        rotated["cx"], rotated["cy"] = rotate_clockwise(float(params["cx"]), float(params["cy"]))
        rotated["arm_x1"], rotated["arm_y1"] = rotate_clockwise(float(params["arm_x1"]), float(params["arm_y1"]))
        rotated["arm_x2"], rotated["arm_y2"] = rotate_clockwise(float(params["arm_x2"]), float(params["arm_y2"]))
        return rotated

    @staticmethod
    def _default_ac0814_params(w: int, h: int) -> dict:
        """AC0814 is horizontally elongated: circle on the left, arm to the right."""
        if w <= 0 or h <= 0:
            return Action._default_ac081x_shared(w, h)

        # AC0814_L-like originals use a noticeably larger ring than the earlier
        # generic AC081x template and keep a visible left margin before the
        # circle. A tighter template gets much closer to the hand-traced sample.
        r = float(h) * 0.46
        stroke_circle = max(0.9, float(h) / 25.0)
        left_margin = max(stroke_circle * 0.5, float(h) * 0.18)
        cx = r + left_margin
        cy = float(h) / 2.0
        arm_stroke = max(1.0, stroke_circle)

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
                "arm_x1": min(float(w), cx + r),
                "arm_y1": cy,
                "arm_x2": float(w),
                "arm_y2": cy,
                "arm_stroke": arm_stroke,
                "arm_len_min": max(1.0, (float(w) - min(float(w), cx + r)) * 0.75),
                "arm_len_min_ratio": 0.75,
            }
        )

    @staticmethod
    def _fit_ac0814_params_from_image(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0814 while keeping the horizontal arm anchored to the right edge."""
        params = Action._fit_semantic_badge_from_image(img, defaults)
        h, w = img.shape[:2]
        aspect_ratio = (float(w) / float(h)) if h > 0 else 1.0
