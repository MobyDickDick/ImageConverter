            p["stem_width_max"] = max(1.0, Action._snap_half(float(p["stem_width_max"])))

        if p.get("stem_enabled") and "cx" in p and "stem_width" in p:
            p["stem_x"] = Action._snap_half(float(p["cx"]) - (float(p["stem_width"]) / 2.0))

        if "stem_x" in p and "stem_width" in p:
            p["stem_x"] = max(0.0, min(float(w) - float(p["stem_width"]), float(p["stem_x"])))
        if "stem_top" in p:
            p["stem_top"] = max(0.0, min(float(h), float(p["stem_top"])))
        if "stem_bottom" in p:
            p["stem_bottom"] = max(0.0, min(float(h), float(p["stem_bottom"])))

        p = Action._enforce_circle_connector_symmetry(p, w, h)
        p = Action._clamp_circle_inside_canvas(p, w, h)

        if (
            raw_circle_radius is not None
            and "cx" in p
            and "cy" in p
            and "r" in p
        ):
            canvas_fit_r = float(
                Action._max_circle_radius_inside_canvas(
                    float(p["cx"]),
                    float(p["cy"]),
                    w,
                    h,
                    float(p.get("stroke_circle", 0.0)),
                )
            )
            snapped_canvas_fit_r = float(Action._snap_half(canvas_fit_r))
            radius_gap_to_canvas = canvas_fit_r - raw_circle_radius
            if (
                snapped_canvas_fit_r > float(p["r"])
                and radius_gap_to_canvas >= 0.0
                and radius_gap_to_canvas <= 0.5
                and (canvas_fit_r - float(p["r"])) <= 0.5
            ):
                p["r"] = float(
                    max(
                        float(p.get("min_circle_radius", 1.0)),
                        min(snapped_canvas_fit_r, canvas_fit_r),
                    )
                )

        # Symmetry enforcement may reintroduce non-snapped values.
        for key in half_keys:
            if key in p:
                p[key] = Action._snap_half(float(p[key]))

        return p

    @staticmethod
    def _normalize_light_circle_colors(params: dict) -> dict:
        params["fill_gray"] = Action.LIGHT_CIRCLE_FILL_GRAY
        params["stroke_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        if params.get("stem_enabled"):
            params["stem_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        if params.get("draw_text", True) and "text_gray" in params:
            params["text_gray"] = Action.LIGHT_CIRCLE_TEXT_GRAY
        return params

    @staticmethod
    def _normalize_ac08_line_widths(params: dict) -> dict:
        """For AC08xx symbols: prefer a uniform 1px circle/connector stroke."""
        p = dict(params)
        prev_circle_stroke = float(p.get("stroke_circle", Action.AC08_STROKE_WIDTH_PX))
        p["stroke_circle"] = Action.AC08_STROKE_WIDTH_PX
        if bool(p.pop("preserve_outer_diameter_on_stroke_normalization", False)) and p.get("circle_enabled", True) and "r" in p and prev_circle_stroke > 0.0:
            # Keep the visual outer diameter stable when normalizing to the
            # canonical AC08 1px stroke. Otherwise tiny plain-ring badges can
            # lose more than a pixel of diameter even if the fitted geometry
            # correctly reached the canvas border.
            outer_radius = float(p["r"]) + (prev_circle_stroke / 2.0)
            p["r"] = max(1.0, outer_radius - (Action.AC08_STROKE_WIDTH_PX / 2.0))
        # Keep semantic AC08xx families on their canonical stroke thickness.
        # The later pixel-error bracketing step can otherwise over-fit anti-aliased
        # ring edges and inflate widths (e.g. 1px -> 6px for tiny circles).
        p["lock_stroke_widths"] = True
        if p.get("arm_enabled"):
            p["arm_stroke"] = Action.AC08_STROKE_WIDTH_PX
        if p.get("stem_enabled"):
            p["stem_width"] = Action.AC08_STROKE_WIDTH_PX
            if "cx" in p:
                p["stem_x"] = float(p["cx"]) - (Action.AC08_STROKE_WIDTH_PX / 2.0)
            p["stem_gray"] = int(p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY))
        return p

    @staticmethod
    def _estimate_border_background_gray(gray: np.ndarray) -> float:
        """Estimate badge background tone from the outer image border pixels."""
        if gray.size == 0:
            return 255.0
        h, w = gray.shape
        if h < 2 or w < 2:
            return float(np.median(gray))
        border = np.concatenate((gray[0, :], gray[h - 1, :], gray[:, 0], gray[:, w - 1]))
        return float(np.median(border))

    @staticmethod
