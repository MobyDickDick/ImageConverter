        return Action._fit_ac0814_params_from_image(img, defaults)

    @staticmethod
    def _glyph_bbox(text_mode: str) -> tuple[int, int, int, int]:
        if text_mode == "path_t":
            return Action.T_XMIN, Action.T_YMIN, Action.T_XMAX, Action.T_YMAX
        return Action.M_XMIN, Action.M_YMIN, Action.M_XMAX, Action.M_YMAX

    @staticmethod
    def _center_glyph_bbox(params: dict) -> None:
        if "s" not in params or "cx" not in params or "cy" not in params:
            return
        xmin, ymin, xmax, ymax = Action._glyph_bbox(params.get("text_mode", "path"))
        glyph_width = (xmax - xmin) * params["s"]
        glyph_height = (ymax - ymin) * params["s"]
        params["tx"] = float(params["cx"] - (glyph_width / 2.0))
        params["ty"] = float(params["cy"] - (glyph_height / 2.0))

    @staticmethod
    def _stabilize_semantic_circle_pose(params: dict, defaults: dict, w: int, h: int) -> dict:
        """Bound fitted circle pose to semantic template geometry.

        Tiny, low-information raster variants are especially sensitive to JPEG
        edge artifacts. For connector-only badges without text, prefer the
        semantic template center and keep radius from collapsing.
        """
        if "r" not in defaults:
            return params

        default_cx = float(defaults.get("cx", float(w) / 2.0))
        default_cy = float(defaults.get("cy", float(h) / 2.0))
        default_r = float(defaults.get("r", 0.0))
        if default_r <= 0.0:
            return params

        has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
        has_text = bool(params.get("draw_text", False))
        if not has_connector:
            return params

        if not has_text and min(w, h) <= 16:
            params["r"] = max(float(params.get("r", default_r)), default_r * 0.96)
            params["lock_circle_cx"] = True
            params["lock_circle_cy"] = True
            return params

        # Keep semantic drift bounded, but allow enough travel that larger source
        # variants (especially AC081x line+circle symbols) can still land on the
        # visually correct center when Hough/contours detect a shifted ring.
        cx_tolerance = max(1.5, float(min(w, h)) * 0.18)
        cy_tolerance = max(1.5, float(min(w, h)) * 0.18)
        current_cx = float(params.get("cx", default_cx))
        current_cy = float(params.get("cy", default_cy))
        params["cx"] = float(max(default_cx - cx_tolerance, min(default_cx + cx_tolerance, current_cx)))
        params["cy"] = float(max(default_cy - cy_tolerance, min(default_cy + cy_tolerance, current_cy)))
        min_radius = max(1.0, default_r * 0.80)
        max_radius = max(min_radius, default_r * 1.45)
        current_r = float(params.get("r", default_r))
        params["r"] = float(max(min_radius, min(max_radius, current_r)))
        return params

    def _fit_ac0870_params_from_image(img: np.ndarray, defaults: dict) -> dict:
        params = dict(defaults)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        min_side = float(min(h, w))
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=max(8.0, min_side * 0.5),
            param1=100,
            param2=10,
            minRadius=max(4, int(round(min_side * 0.25))),
            maxRadius=max(6, int(round(min_side * 0.48))),
        )

        if circles is not None and circles.size > 0:
            c = circles[0][0]
            params["cx"] = float(c[0])
            params["cy"] = float(c[1])
            params["r"] = float(c[2])

        yy, xx = np.indices(gray.shape)
        dist = np.sqrt((xx - params["cx"]) ** 2 + (yy - params["cy"]) ** 2)
        inner_mask = dist <= params["r"] * 0.88
        ring_mask = np.abs(dist - params["r"]) <= max(1.0, params["stroke_circle"])

        if np.any(inner_mask):
            inner_vals = gray[inner_mask]
            text_threshold = min(150, int(np.percentile(inner_vals, 20) + 3))
            text_mask = (gray <= text_threshold) & inner_mask

            kernel = np.ones((2, 2), np.uint8)
            text_mask_u8 = cv2.morphologyEx(text_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(text_mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
