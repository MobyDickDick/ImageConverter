                    has_arm = True
                    horizontal_candidates += 1
                    strongest_horizontal = max(strongest_horizontal, dx)
                if is_vertical:
                    has_stem = True
                    vertical_candidates += 1
                    strongest_vertical = max(strongest_vertical, dy)
                if has_arm and has_stem:
                    break

        # Text cue: several small-ish connected components in center ROI.
        has_text = False
        x1 = max(0, int(round(float(w) * 0.15)))
        x2 = min(w, int(round(float(w) * 0.85)))
        y1 = max(0, int(round(float(h) * 0.20)))
        y2 = min(h, int(round(float(h) * 0.80)))
        roi = fg_mask[y1:y2, x1:x2]
        if roi.size > 0:
            n_labels, _labels, stats, _centroids = cv2.connectedComponentsWithStats(roi, connectivity=8)
            small_component_count = 0
            total_small_area = 0
            compact_component_count = 0
            max_small_area = max(3, int(round(float(roi.shape[0] * roi.shape[1]) * 0.12)))
            for label_idx in range(1, n_labels):
                area = int(stats[label_idx, cv2.CC_STAT_AREA])
                if 2 <= area <= max_small_area:
                    width = int(stats[label_idx, cv2.CC_STAT_WIDTH])
                    height = int(stats[label_idx, cv2.CC_STAT_HEIGHT])
                    aspect = float(width) / max(1.0, float(height))
                    if circle_geom is not None:
                        cx, cy, radius = circle_geom
                        comp_cx = x1 + float(stats[label_idx, cv2.CC_STAT_LEFT] + (width / 2.0))
                        comp_cy = y1 + float(stats[label_idx, cv2.CC_STAT_TOP] + (height / 2.0))
                        if math.hypot(comp_cx - cx, comp_cy - cy) > float(radius) * 0.72:
                            continue
                    small_component_count += 1
                    total_small_area += area
                    if 0.25 <= aspect <= 4.0:
                        compact_component_count += 1
            has_text = (
                small_component_count >= 2
                and compact_component_count >= 2
                and total_small_area >= max(6, int(round(float(min_side) * 0.45)))
            )

        connector_orientation = "none"
        if strongest_horizontal > 0 and strongest_vertical > 0:
            shorter = min(strongest_horizontal, strongest_vertical)
            longer = max(strongest_horizontal, strongest_vertical)
            if shorter / max(1.0, float(longer)) >= 0.75:
                connector_orientation = "ambiguous"
            elif strongest_vertical > strongest_horizontal:
                connector_orientation = "vertical"
            else:
                connector_orientation = "horizontal"
        elif strongest_vertical > 0:
            connector_orientation = "vertical"
        elif strongest_horizontal > 0:
            connector_orientation = "horizontal"

        return {
            "circle": bool(has_circle),
            "stem": bool(has_stem),
            "arm": bool(has_arm),
            "text": bool(has_text),
            "circle_detection_source": circle_detection_source,
            "connector_orientation": connector_orientation,
            "horizontal_line_candidates": int(horizontal_candidates),
            "vertical_line_candidates": int(vertical_candidates),
        }

    @staticmethod
    def validate_semantic_description_alignment(
        img_orig: np.ndarray,
        semantic_elements: list[str],
        badge_params: dict,
    ) -> list[str]:
        expected = Action._expected_semantic_presence(semantic_elements)
        expected_co2 = any("co_2" in str(elem).lower() or "co₂" in str(elem).lower() for elem in semantic_elements)
        try:
            structural = Action._detect_semantic_primitives(img_orig, badge_params)
        except TypeError:
            # Test doubles may still patch the legacy one-argument variant.
            structural = Action._detect_semantic_primitives(img_orig)
        circle_mask = Action.extract_badge_element_mask(img_orig, badge_params, "circle")
        stem_mask = Action.extract_badge_element_mask(img_orig, badge_params, "stem")
        arm_mask = Action.extract_badge_element_mask(img_orig, badge_params, "arm")
        text_mask = Action.extract_badge_element_mask(img_orig, badge_params, "text")

        def _mask_supports_element(mask: np.ndarray | None, element: str) -> bool:
            if mask is None:
                return False
            pixel_count = int(np.count_nonzero(mask))
            if pixel_count < 3:
                return False
            bbox = Action._mask_bbox(mask)
            if bbox is None:
                return False
            x1, y1, x2, y2 = bbox
            width = max(1.0, (x2 - x1) + 1.0)
