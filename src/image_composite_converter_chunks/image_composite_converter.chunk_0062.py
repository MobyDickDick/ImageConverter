        if element == "circle" and params.get("circle_enabled", True):
            if lock_strokes:
                fixed = float(Action.AC08_STROKE_WIDTH_PX)
                return "stroke_circle", fixed, fixed
            low = max(0.8, float(params.get("stroke_circle", 1.0)) * 0.6)
            high = max(low, min(float(min(w, h)) * 0.22, float(params.get("r", min(w, h))) * 0.9))
            return "stroke_circle", low, high
        if element == "text" and params.get("draw_text", True):
            mode = str(params.get("text_mode", "")).lower()
            if mode == "voc":
                cur = float(params.get("voc_font_scale", 0.52))
                if bool(params.get("lock_text_scale", False)):
                    return "voc_font_scale", cur, cur
                # Start with broad generic bounds so the optimizer can follow
                # text-mask error rather than artificial variant caps.
                low = max(0.30, min(cur * 0.60, 0.45))
                # Keep a broad generic search window unless a specific badge
                # family constrains it via explicit min/max overrides.
                high = 1.60
                if img_orig is not None:
                    text_mask = Action.extract_badge_element_mask(img_orig, params, "text")
                    bbox = Action._mask_bbox(text_mask) if text_mask is not None else None
                    if bbox is not None:
                        x1, y1, x2, y2 = bbox
                        text_w = max(1.0, (float(x2) - float(x1)) + 1.0)
                        text_h = max(1.0, (float(y2) - float(y1)) + 1.0)
                        implied_scale = max(
                            text_w / max(1.0, float(w) * 0.38),
                            text_h / max(1.0, float(h) * 0.18),
                            text_w / max(1.0, float(params.get("r", min_dim)) * 2.8),
                        )
                        low = max(low, min(0.90, implied_scale * 0.70))
                        high = max(high, min(2.40, implied_scale * 1.35))
                if "voc_font_scale_min" in params:
                    low = max(low, float(params["voc_font_scale_min"]))
                if "voc_font_scale_max" in params:
                    high = min(high, float(params["voc_font_scale_max"]))
                return "voc_font_scale", low, max(low, high)
            if mode == "co2":
                cur = float(params.get("co2_font_scale", 0.82))
                if bool(params.get("lock_text_scale", False)):
                    return "co2_font_scale", cur, cur
                # CO₂ labels in large variants can require a noticeably larger font
                # than the historical cap of 1.20 to match the source symbol.
                low = max(0.45, cur * 0.72)
                high = min(1.55, cur * 1.45)
                if "co2_font_scale_min" in params:
                    low = max(low, float(params["co2_font_scale_min"]))
                if "co2_font_scale_max" in params:
                    high = min(high, float(params["co2_font_scale_max"]))
                return "co2_font_scale", low, max(low, high)
        return None

    @staticmethod
    def _element_error_for_width(img_orig: np.ndarray, params: dict, element: str, width_value: float) -> float:
        h, w = img_orig.shape[:2]
        probe = dict(params)
        info = Action._element_width_key_and_bounds(element, probe, w, h, img_orig=img_orig)
        if info is None:
            return float("inf")
        key, low, high = info
        probe[key] = float(Action._clip_scalar(width_value, low, high))
        if key == "stem_width" and probe.get("stem_enabled"):
            probe["stem_x"] = float(probe.get("cx", probe.get("stem_x", 0.0))) - (probe["stem_width"] / 2.0)
        elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(probe, element))
        elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")
        mask_orig = Action.extract_badge_element_mask(img_orig, probe, element)
        if mask_orig is None:
            return float("inf")
        return Action._element_match_error(img_orig, elem_render, probe, element, mask_orig=mask_orig)

    @staticmethod
    def _element_error_for_circle_radius(img_orig: np.ndarray, params: dict, radius_value: float) -> float:
        h, w = img_orig.shape[:2]
        if not params.get("circle_enabled", True):
            return float("inf")

        probe = dict(params)
        min_r = float(
            max(
                1.0,
                float(probe.get("min_circle_radius", 1.0)),
                float(probe.get("circle_radius_lower_bound_px", 1.0)),
            )
        )
        max_r = max(min_r, (float(min(w, h)) * 0.48))
        if bool(probe.get("allow_circle_overflow", False)):
            max_r = max(max_r, float(max(w, h)) * 1.25, min_r + 0.5)
        probe["r"] = float(Action._clip_scalar(radius_value, min_r, max_r))
        probe = Action._clamp_circle_inside_canvas(probe, w, h)

        if probe.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(probe, float(probe["r"]))

        if probe.get("stem_enabled"):
            probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

        elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(probe, "circle"))
