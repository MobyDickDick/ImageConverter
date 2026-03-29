        if roi.size == 0:
            return None

        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        best = None
        for cnt in contours:
            area = float(cv2.contourArea(cnt))
            if area < 8.0:
                continue
            perimeter = float(cv2.arcLength(cnt, True))
            if perimeter <= 0.0:
                continue
            circularity = 4.0 * np.pi * area / max(1e-6, perimeter * perimeter)
            if circularity < 0.35:
                continue
            score = area * (0.5 + circularity)
            if best is None or score > best[0]:
                best = (score, cnt)

        if best is None:
            return None

        (_score, cnt) = best
        (cx, cy), r = cv2.minEnclosingCircle(cnt)
        min_r = max(2.0, float(w) * 0.24)
        max_r = min(float(w) * 0.52, float(top_limit) * 0.58)
        if max_r < min_r:
            max_r = min_r
        r = float(Action._clip_scalar(r, min_r, max_r))
        cx = float(Action._clip_scalar(cx, 0.0, float(w - 1)))
        cy = float(Action._clip_scalar(cy, 0.0, float(h - 1)))
        return cx, cy, r

    @staticmethod
    def _fit_ac0811_params_from_image(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0811 while keeping the vertical stem anchored to the lower edge.

        AC0811 source symbols are noisy for thin vertical lines. Generic stem fitting can
        under-segment the line so the generated SVG misses parts of the lower connector.
        For this family we therefore fit the circle/tones from the image, but keep the stem
        geometry constrained to the semantic template (centered under the circle, extending
        to the image bottom).
        """
        params = Action._fit_semantic_badge_from_image(img, defaults)
        h, w = img.shape[:2]

        raw_stem_width = float(params.get("stem_width", defaults.get("stem_width", max(1.0, float(w) * 0.10))))
        cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
        cy = float(params.get("cy", defaults.get("cy", float(w) / 2.0)))
        r = float(params.get("r", defaults.get("r", float(w) * 0.4)))
        stroke_circle = float(params.get("stroke_circle", defaults.get("stroke_circle", max(0.9, float(w) / 15.0))))
        aspect_ratio = (float(h) / float(w)) if w > 0 else 1.0
        elongated_plain_badge = aspect_ratio >= 1.60 and not bool(params.get("draw_text", False))

        # Foreground contour estimation helps stem-only badges, but for VOC/CO2
        # labels it can lock onto text blobs and shrink the fitted circle.
        allow_upper_circle_estimate = str(params.get("text_mode", "")).lower() not in {"voc", "co2"}
        upper_circle = Action._estimate_upper_circle_from_foreground(img, defaults) if allow_upper_circle_estimate else None
        if upper_circle is not None:
            ecx, ecy, er = upper_circle
            # Prefer robust foreground estimate for tiny/narrow AC0811 variants.
            trust = 0.85 if w <= 18 else 0.55
            cx = (cx * (1.0 - trust)) + (ecx * trust)
            cy = (cy * (1.0 - trust)) + (ecy * trust)
            r = (r * (1.0 - trust)) + (er * trust)
            params["cx"] = cx
            params["cy"] = cy
            params["r"] = r

        if w <= 18:
            default_cx = float(defaults.get("cx", float(w) / 2.0))
            default_cy = float(defaults.get("cy", float(w) / 2.0))

            # Ensure the fitted circle remains fully inside the canvas with stroke taken
            # into account so it is not clipped at the edges.
            radius_limit_x = max(1.0, min(default_cx, float(w) - default_cx) - (stroke_circle / 2.0))
            radius_limit_y = max(1.0, min(default_cy, float(h) - default_cy) - (stroke_circle / 2.0))
            r = float(min(r, radius_limit_x, radius_limit_y))

            params["cx"] = default_cx
            params["cy"] = cy
            params["r"] = r
            # Keep tiny AC0811 variants horizontally anchored; anti-aliased
            # min-rect alignment can otherwise pull circle/stem to one side.
            params["lock_circle_cx"] = True
            params["lock_stem_center_to_circle"] = True

        # Keep elongated plain AC0811 variants close to their semantic template.
        # The stem occupies only a thin column of dark pixels, so the generic
        # circle/stem error tends to over-value shorter stems once the circle is
        # nudged downward. Re-anchor the circle vertically and persist a stronger
        # template-based stem floor so AC0811_L keeps a visibly long connector.
        if elongated_plain_badge:
            default_cx = float(defaults.get("cx", cx))
            default_cy = float(defaults.get("cy", cy))
            default_r = float(defaults.get("r", r))
            params["cx"] = default_cx
