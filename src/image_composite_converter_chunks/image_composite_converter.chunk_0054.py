        if img_svg is None:
            return float("inf")
        if img_svg.shape[:2] != img_orig.shape[:2]:
            img_svg = cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)

        local_mask_orig = mask_orig if mask_orig is not None else Action.extract_badge_element_mask(img_orig, params, element)
        local_mask_svg = mask_svg if mask_svg is not None else Action.extract_badge_element_mask(img_svg, params, element)
        if local_mask_orig is None or local_mask_svg is None:
            return float("inf")

        orig_area = float(np.sum(local_mask_orig))
        svg_area = float(np.sum(local_mask_svg))
        if orig_area <= 0.0 or svg_area <= 0.0:
            return float("inf")

        photo_err = float(Action._masked_union_error_in_bbox(img_orig, img_svg, local_mask_orig, local_mask_svg))
        if not math.isfinite(photo_err):
            return float("inf")

        inter = float(np.sum(local_mask_orig & local_mask_svg))
        union = float(np.sum(local_mask_orig | local_mask_svg))
        if union <= 0.0:
            return float("inf")

        miss = float(np.sum(local_mask_orig & (~local_mask_svg))) / orig_area
        extra = float(np.sum(local_mask_svg & (~local_mask_orig))) / orig_area
        if bool(params.get("ac08_small_variant_mode", False)):
            aa_bias = float(max(0.0, params.get("small_variant_antialias_bias", 0.0)))
            miss = max(0.0, miss - aa_bias)
            extra = max(0.0, extra - (aa_bias * 0.75))
        iou = inter / union

        # Normalize photometric term by source element area so comparisons stay
        # meaningful across sizes (S/M/L variants).
        photo_norm = photo_err / max(1.0, orig_area)

        # Circle optimization should prefer concentric matches and avoid shrinking
        # to the smallest ring that still overlaps the arm/label neighborhood.
        # The mask overlap terms above are necessary but can be too permissive
        # when anti-aliased JPEG edges blur circle/connector boundaries.
        if element == "circle" and apply_circle_geometry_penalty:
            src_circle = Action._mask_centroid_radius(local_mask_orig)
            cand_circle = Action._mask_centroid_radius(local_mask_svg)
            if src_circle is not None and cand_circle is not None:
                src_cx, src_cy, src_r = src_circle
                cand_cx, cand_cy, cand_r = cand_circle
                center_dist = float(math.hypot(cand_cx - src_cx, cand_cy - src_cy))
                center_norm = center_dist / max(1.0, src_r)
                # Penalize undersized rings more strongly than oversized ones so
                # AC0812-like badges keep a readable radius in optimization.
                undersize_ratio = max(0.0, (src_r - cand_r) / max(1.0, src_r))
                extra += undersize_ratio * 0.35
                miss += undersize_ratio * 0.45
                iou = max(0.0, iou - min(0.35, undersize_ratio * 0.55))
                photo_norm += center_norm * 2.8

        return float(photo_norm + (38.0 * miss) + (24.0 * extra) + (18.0 * (1.0 - iou)))

    @staticmethod
    def _capture_canonical_badge_colors(params: dict) -> dict:
        p = dict(params)
        p["target_fill_gray"] = int(round(float(p.get("fill_gray", Action.LIGHT_CIRCLE_FILL_GRAY))))
        p["target_stroke_gray"] = int(round(float(p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY))))
        if p.get("stem_enabled"):
            p["target_stem_gray"] = int(round(float(p.get("stem_gray", p["target_stroke_gray"]))))
        if p.get("draw_text", True) and "text_gray" in p:
            p["target_text_gray"] = int(round(float(p.get("text_gray", Action.LIGHT_CIRCLE_TEXT_GRAY))))
        return p

    @staticmethod
    def _apply_canonical_badge_colors(params: dict) -> dict:
        p = dict(params)
        if "target_fill_gray" in p:
            p["fill_gray"] = int(p["target_fill_gray"])
        if "target_stroke_gray" in p:
            p["stroke_gray"] = int(p["target_stroke_gray"])
        if p.get("stem_enabled") and "target_stem_gray" in p:
            p["stem_gray"] = int(p["target_stem_gray"])
        if p.get("draw_text", True) and "target_text_gray" in p:
            p["text_gray"] = int(p["target_text_gray"])
        return p

    @staticmethod
    def _circle_bounds(params: dict, w: int, h: int) -> tuple[float, float, float, float, float, float]:
        min_r = float(max(1.0, params.get("min_circle_radius", 1.0)))
        if "circle_radius_lower_bound_px" in params:
            min_r = float(max(min_r, float(params.get("circle_radius_lower_bound_px", min_r))))
        allow_overflow = bool(params.get("allow_circle_overflow", False))
        max_r = max(min_r, float(min(w, h)) * 0.48)
        cx = float(params.get("cx", float(w) / 2.0))
        cy = float(params.get("cy", float(h) / 2.0))
        stroke = float(params.get("stroke_circle", 0.0))
        if allow_overflow:
            max_r = max(max_r, float(max(w, h)) * 1.25, min_r + 0.5)
        else:
            max_r = min(max_r, Action._max_circle_radius_inside_canvas(cx, cy, w, h, stroke))
        if "max_circle_radius" in params:
            max_r = min(max_r, float(params.get("max_circle_radius", max_r)))
        return 0.0, float(w - 1), 0.0, float(h - 1), min_r, max_r

