            y1 = max(0.0, min(params.get("arm_y1", 0.0), params.get("arm_y2", 0.0)) - context_pad)
            y2 = min(float(h), max(params.get("arm_y1", 0.0), params.get("arm_y2", 0.0)) + context_pad)
            pad = max(1.0, params.get("arm_stroke", params.get("stem_or_arm", 1.0)) * 0.8)
            return (xx >= (x1 - pad)) & (xx <= (x2 + pad)) & (yy >= (y1 - pad)) & (yy <= (y2 + pad))
        if element == "text" and params.get("draw_text", True):
            x1, y1, x2, y2 = Action._text_bbox(params)
            x1 = max(0.0, x1 - context_pad)
            y1 = max(0.0, y1 - context_pad)
            x2 = min(float(w), x2 + context_pad)
            y2 = min(float(h), y2 + context_pad)
            return (xx >= x1) & (xx <= x2) & (yy >= y1) & (yy <= y2)
        return None

    @staticmethod
    def _text_bbox(params: dict) -> tuple[float, float, float, float]:
        """Approximate text bounding box for semantic badge text modes."""
        cx = float(params.get("cx", 0.0))
        cy = float(params.get("cy", 0.0))
        r = max(1.0, float(params.get("r", 1.0)))
        mode = str(params.get("text_mode", "")).lower()

        if mode == "voc":
            font_size = max(4.0, r * float(params.get("voc_font_scale", 0.52)))
            width = font_size * 1.95
            height = font_size * 0.90
            y = cy + float(params.get("voc_dy", 0.0))
            return (cx - (width / 2.0), y - (height / 2.0), cx + (width / 2.0), y + (height / 2.0))

        if mode == "co2":
            layout = Action._co2_layout(params)
            x1 = float(layout["x1"])
            x2 = float(layout["x2"])
            y = float(layout["y_base"])
            height = float(layout["height"])
            return (x1, y - (height / 2.0), x2, y + (height / 2.0))

        # path/path_t fallback via known glyph bounds.
        s = float(params.get("s", 0.0))
        tx = float(params.get("tx", cx))
        ty = float(params.get("ty", cy))
        xmin, ymin, xmax, ymax = Action._glyph_bbox(params.get("text_mode", "path"))
        x1 = tx + (xmin * s)
        y1 = ty + (ymin * s)
        x2 = tx + (xmax * s)
        y2 = ty + (ymax * s)
        return (x1, y1, x2, y2)

    @staticmethod
    def _foreground_mask(img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, fg_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Tiny anti-aliased badges can have only a few gray levels; a pure Otsu
        # split then frequently drops the ring entirely. Blend in a gentle local
        # contrast cue so faint circular strokes remain available to downstream
        # semantic checks without over-activating the white background.
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        local_contrast = cv2.absdiff(gray, blur)
        contrast_thresh = max(2, int(round(float(np.percentile(local_contrast, 82)))))
        fg_contrast = local_contrast >= contrast_thresh

        fg = (fg_otsu > 0) | fg_contrast
        fg_u8 = fg.astype(np.uint8) * 255
        kernel = np.ones((2, 2), dtype=np.uint8)
        fg_u8 = cv2.morphologyEx(fg_u8, cv2.MORPH_CLOSE, kernel, iterations=1)
        return fg_u8 > 0

    @staticmethod
    def _circle_from_foreground_mask(fg_mask: np.ndarray) -> tuple[float, float, float] | None:
        """Infer a coarse circle from the foreground mask when Hough is too brittle."""
        mask_u8 = (fg_mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        h, w = fg_mask.shape[:2]
        min_side = float(max(1, min(h, w)))
        best: tuple[float, float, float, float] | None = None

        for cnt in contours:
            area = float(cv2.contourArea(cnt))
            if area < max(4.0, min_side * 0.35):
                continue
            x, y, bw, bh = cv2.boundingRect(cnt)
            if bw < 3 or bh < 3:
                continue
            aspect = float(bw) / max(1.0, float(bh))
            if not (0.65 <= aspect <= 1.35):
                continue

            (cx, cy), radius = cv2.minEnclosingCircle(cnt)
            radius = float(radius)
            if radius < max(2.5, min_side * 0.10) or radius > max(8.0, min_side * 0.55):
                continue

            dist = np.sqrt((cnt[:, 0, 0].astype(np.float32) - cx) ** 2 + (cnt[:, 0, 1].astype(np.float32) - cy) ** 2)
            if dist.size == 0:
                continue
            radial_residual = float(np.mean(np.abs(dist - radius)))
            circle_area = math.pi * radius * radius
