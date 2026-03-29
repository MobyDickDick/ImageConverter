                contour = max(contours, key=cv2.contourArea)
                x, y, tw, th = cv2.boundingRect(contour)
                if tw > 2 and th > 2:
                    t_width_units = 1636 - Action.T_XMIN
                    t_height_units = Action.T_YMAX
                    sx = tw / t_width_units
                    sy = th / t_height_units
                    s = float(max(0.004, min(0.04, (sx + sy) / 2.0)))
                    params["s"] = s
                    params["text_gray"] = int(np.median(gray[text_mask_u8 > 0]))

            Action._center_glyph_bbox(params)

            params["fill_gray"] = int(np.median(inner_vals))

        if np.any(ring_mask):
            params["stroke_gray"] = int(np.median(gray[ring_mask]))

        return params

    @staticmethod
    def _fit_semantic_badge_from_image(img: np.ndarray, defaults: dict) -> dict:
        """Fit common semantic badge primitives (circle/stem/arm) directly from image content."""
        params = dict(defaults)
        if "r" in params and "template_circle_radius" not in params:
            params["template_circle_radius"] = float(params["r"])
        if "cx" in params and "template_circle_cx" not in params:
            params["template_circle_cx"] = float(params["cx"])
        if "cy" in params and "template_circle_cy" not in params:
            params["template_circle_cy"] = float(params["cy"])
        if "stem_top" in params and "template_stem_top" not in params:
            params["template_stem_top"] = float(params["stem_top"])
        if "stem_bottom" in params and "template_stem_bottom" not in params:
            params["template_stem_bottom"] = float(params["stem_bottom"])
        if "arm_x1" in params and "template_arm_x1" not in params:
            params["template_arm_x1"] = float(params["arm_x1"])
        if "arm_y1" in params and "template_arm_y1" not in params:
            params["template_arm_y1"] = float(params["arm_y1"])
        if "arm_x2" in params and "template_arm_x2" not in params:
            params["template_arm_x2"] = float(params["arm_x2"])
        if "arm_y2" in params and "template_arm_y2" not in params:
            params["template_arm_y2"] = float(params["arm_y2"])
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        min_side = float(min(h, w))
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        circles = cv2.HoughCircles(
            blur,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=max(6.0, min_side * 0.35),
            param1=80,
            param2=9,
            minRadius=max(3, int(round(min_side * 0.14))),
            maxRadius=max(6, int(round(min_side * 0.60))),
        )

        if circles is not None and circles.size > 0:
            best = None
            template_cx = float(defaults.get("cx", params.get("cx", float(w) / 2.0)))
            template_cy = float(defaults.get("cy", params.get("cy", float(h) / 2.0)))
            template_r = float(defaults.get("r", params.get("r", max(1.0, min_side * 0.35))))
            max_center_offset = max(2.0, min_side * 0.42)
            max_radius_delta = max(2.0, template_r * 0.70)
            for c in circles[0]:
                cx, cy, r = float(c[0]), float(c[1]), float(c[2])
                center_offset = float(math.hypot(cx - template_cx, cy - template_cy))
                # Semantic AC08xx badges follow a fixed layout. Reject detections
                # that drift too far away from the expected template center; on
                # tiny CO₂/VOC symbols those are usually text blobs, not circles.
                if center_offset > max_center_offset:
                    continue
                yy, xx = np.indices(gray.shape)
                dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
                fill_mask = dist <= max(1.0, r * 0.82)
                ring_mask = np.abs(dist - r) <= max(1.0, params.get("stroke_circle", 1.2))
                if not np.any(fill_mask) or not np.any(ring_mask):
                    continue
                fill_gray = float(np.median(gray[fill_mask]))
                ring_gray = float(np.median(gray[ring_mask]))
                # Generalized scoring for circle+ring symbols:
                # - prefer ring darker than fill with clear contrast,
                # - keep geometric closeness to semantic template.
                contrast = fill_gray - ring_gray
                tone_penalty = 0.0
                if contrast < 4.0:
                    tone_penalty += (4.0 - contrast) * 4.0
                if ring_gray >= fill_gray:
                    tone_penalty += (ring_gray - fill_gray + 1.0) * 6.0
                score = tone_penalty
                # Prefer circles that stay close to the semantic template size/
                # position so all AC08xx variants remain stable across JPEG noise.
                score += (center_offset / max_center_offset) * 9.0
                score += (abs(r - template_r) / max_radius_delta) * 6.0
                if best is None or score < best[0]:
                    best = (score, cx, cy, r, fill_gray, ring_gray)

            if best is not None:
                _, cx, cy, r, fill_gray, ring_gray = best
