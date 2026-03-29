
        raw_arm_stroke = float(params.get("arm_stroke", defaults.get("arm_stroke", max(1.0, float(h) * 0.10))))
        cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
        cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
        r = float(params.get("r", defaults.get("r", float(h) * 0.4)))
        stroke_circle = float(params.get("stroke_circle", defaults.get("stroke_circle", max(0.9, float(h) / 15.0))))
        default_r = float(defaults.get("r", float(h) * 0.4))

        min_arm_stroke = max(1.0, stroke_circle * 0.75)
        max_arm_stroke = max(min_arm_stroke, min(float(h) * 0.14, stroke_circle * 1.6))
        arm_stroke = max(min_arm_stroke, min(raw_arm_stroke, max_arm_stroke))

        cx = float(params.get("cx", defaults.get("cx", float(h) / 2.0)))
        cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
        r = float(params.get("r", defaults.get("r", float(h) * 0.4)))

        tiny_plain_badge = h <= 18 and not bool(params.get("draw_text", True))
        if tiny_plain_badge:
            # Tiny plain connector badges can lose roughly one anti-aliased ring
            # pixel in contour/Hough fitting; keep them near template size.
            r = max(r, default_r * 0.98)
            default_cx = float(defaults.get("cx", float(w) / 2.0))
            default_cy = float(defaults.get("cy", float(h) / 2.0))
            # AC0814_S has very little empty space around the ring. Even a
            # sub-pixel pose drift is visually obvious, so keep the traced circle
            # anchored to the semantic template and only allow a tiny vertical
            # correction for raster antialiasing.
            params["cx"] = default_cx
            params["cy"] = float(Action._clip_scalar(cy, default_cy - 0.5, default_cy + 0.5))
            params["lock_circle_cx"] = True
            params["lock_circle_cy"] = True
            params["lock_arm_center_to_circle"] = True
            cx = float(params["cx"])
            cy = float(params["cy"])

        elongated_plain_badge = aspect_ratio >= 1.60 and h >= 20 and not bool(params.get("draw_text", True))
        if elongated_plain_badge:
            # AC0814_L-like forms are the mirrored counterpart of AC0812_L: JPEG
            # antialiasing near the connector often makes the ring fit under-size.
            # Keep a tighter semantic floor so later validation cannot preserve an
            # already shrunken circle as the new optimum.
            r = max(r, default_r * 0.95)
            params["min_circle_radius"] = float(max(float(params.get("min_circle_radius", 1.0)), default_r * 0.95))

            default_cx = float(defaults.get("cx", float(w) / 2.0))
            default_cy = float(defaults.get("cy", float(h) / 2.0))
            # AC0814_M was hand-traced with a noticeably stable left circle margin
            # and a perfectly horizontal connector. In medium/large plain variants
            # the raster fit can still drift the ring toward the connector. Keep
            # the circle near the semantic template, but allow a bounded leftward
            # correction for medium canvases where the traced source circle sits
            # slightly further left than the generic template baseline.
            medium_plain_canvas = h <= 22 and w <= 38
            max_left_correction = max(0.0, default_r * 0.14) if medium_plain_canvas else 0.0
            corrected_cx = default_cx
            if max_left_correction > 0.0:
                corrected_cx = float(Action._clip_scalar(cx, default_cx - max_left_correction, default_cx))
            params["cx"] = corrected_cx
            if medium_plain_canvas:
                params["template_circle_cx"] = corrected_cx
            params["cy"] = float(Action._clip_scalar(cy, default_cy - 0.6, default_cy + 0.6))
            params["lock_circle_cx"] = True
            params["lock_circle_cy"] = True
            params["lock_arm_center_to_circle"] = True
            cx = float(params["cx"])
            cy = float(params["cy"])

        params["r"] = r

        params["arm_enabled"] = True
        params["arm_stroke"] = arm_stroke
        params["arm_x1"] = min(float(w), cx + r)
        params["arm_y1"] = cy
        params["arm_x2"] = float(w)
        params["arm_y2"] = cy
        current_arm_len = float(math.hypot(params["arm_x2"] - params["arm_x1"], params["arm_y2"] - params["arm_y1"]))
        default_arm_len = max(
            0.0,
            float(w) - (float(defaults.get("cx", float(h) / 2.0)) + float(defaults.get("r", float(h) * 0.4))),
        )
        semantic_arm_len_min = max(1.0, default_arm_len * 0.75)
        min_arm_len_ratio = 0.75
        if elongated_plain_badge:
            min_arm_len_ratio = 0.82
        params["arm_len_min_ratio"] = float(max(float(params.get("arm_len_min_ratio", min_arm_len_ratio)), min_arm_len_ratio))
        params["arm_len_min"] = max(
            1.0,
            current_arm_len * float(params["arm_len_min_ratio"]),
            semantic_arm_len_min,
        )
        return Action._normalize_light_circle_colors(params)

    @staticmethod
    def _default_ac0810_params(w: int, h: int) -> dict:
        """AC0810 uses the same right-arm geometry as AC0814 (circle on the left)."""
        return Action._default_ac0814_params(w, h)

    @staticmethod
    def _fit_ac0810_params_from_image(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0810 with the same right-anchored arm behavior as AC0814."""
