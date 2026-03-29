    def _estimate_circle_tones_and_stroke(
        gray: np.ndarray,
        cx: float,
        cy: float,
        r: float,
        stroke_hint: float,
    ) -> tuple[float, float, float]:
        """Estimate fill/ring grayscale and stroke width for circular ring-like badges."""
        yy, xx = np.indices(gray.shape)
        dist = np.sqrt((xx - float(cx)) ** 2 + (yy - float(cy)) ** 2)

        inner_mask = dist <= max(1.0, float(r) * 0.78)
        fill_gray = float(np.median(gray[inner_mask])) if np.any(inner_mask) else float(np.median(gray))

        search_band = max(2.0, min(float(r) * 0.30, 5.0))
        ring_search = np.abs(dist - float(r)) <= search_band
        ring_vals = gray[ring_search] if np.any(ring_search) else gray
        ring_gray = float(np.median(ring_vals))

        # Prefer the darker contour around the estimated radius when present.
        dark_cut = fill_gray - 2.0
        dark_ring = ring_search & (gray <= dark_cut)
        if np.any(dark_ring):
            ring_gray = float(np.median(gray[dark_ring]))
            d = np.abs(dist - float(r))[dark_ring]
            stroke_est = float(max(1.0, min(6.0, np.percentile(d, 72) * 2.0)))
        else:
            stroke_est = float(max(1.0, min(6.0, stroke_hint)))

        return fill_gray, ring_gray, stroke_est

    @staticmethod
    def _persist_connector_length_floor(params: dict, element: str, default_ratio: float) -> None:
        """Persist a robust minimum connector length for later validation stages."""
        if element == "stem":
            length = float(params.get("stem_bottom", 0.0)) - float(params.get("stem_top", 0.0))
            min_key = "stem_len_min"
            ratio_key = "stem_len_min_ratio"
            template_length = float(params.get("template_stem_bottom", 0.0)) - float(params.get("template_stem_top", 0.0))
        elif element == "arm":
            x1 = float(params.get("arm_x1", 0.0))
            y1 = float(params.get("arm_y1", 0.0))
            x2 = float(params.get("arm_x2", 0.0))
            y2 = float(params.get("arm_y2", 0.0))
            length = float(math.hypot(x2 - x1, y2 - y1))
            min_key = "arm_len_min"
            ratio_key = "arm_len_min_ratio"
            tx1 = float(params.get("template_arm_x1", x1))
            ty1 = float(params.get("template_arm_y1", y1))
            tx2 = float(params.get("template_arm_x2", x2))
            ty2 = float(params.get("template_arm_y2", y2))
            template_length = float(math.hypot(tx2 - tx1, ty2 - ty1))
        else:
            return

        if length <= 0.0:
            return

        ratio = float(max(0.0, min(1.0, float(params.get(ratio_key, default_ratio)))))
        params[ratio_key] = ratio
        params[min_key] = float(max(float(params.get(min_key, 1.0)), length * ratio, template_length * ratio, 1.0))

    @staticmethod
    def _is_ac08_small_variant(name: str, params: dict) -> tuple[bool, str, float]:
        """Classify tiny AC08 variants so validation can use tighter `_S` heuristics."""
        normalized_name = str(name).upper()
        min_dim = float(min(float(params.get("width", 0.0) or 0.0), float(params.get("height", 0.0) or 0.0)))
        if min_dim <= 0.0:
            min_dim = max(1.0, float(params.get("r", 1.0)) * 2.0)

        variant_suffix = normalized_name.endswith("_S")
        dimension_small = min_dim <= 15.5
        is_small = variant_suffix or dimension_small
        if variant_suffix and dimension_small:
            reason = "variant_suffix+min_dim"
        elif variant_suffix:
            reason = "variant_suffix"
        elif dimension_small:
            reason = "min_dim"
        else:
            reason = "standard"
        return is_small, reason, min_dim

    @staticmethod
    def _configure_ac08_small_variant_mode(name: str, params: dict) -> dict:
        """Apply `_S`-specific AC08 tuning for text, connector floors, and masks."""
        p = dict(params)
        is_small, reason, min_dim = Action._is_ac08_small_variant(name, p)
        p["ac08_small_variant_mode"] = bool(is_small)
        p["ac08_small_variant_reason"] = reason
        p["ac08_small_variant_min_dim"] = float(min_dim)
        if not is_small:
            return p

        p["validation_mask_dilate_px"] = int(max(1, int(p.get("validation_mask_dilate_px", 1))))
        p["small_variant_antialias_bias"] = float(max(0.0, float(p.get("small_variant_antialias_bias", 0.08))))

        if p.get("arm_enabled"):
            p["arm_len_min_ratio"] = float(max(float(p.get("arm_len_min_ratio", 0.75)), 0.78))
            Action._persist_connector_length_floor(p, "arm", default_ratio=0.78)
