                    focus_mask.astype(np.uint8),
                    (img_orig.shape[1], img_orig.shape[0]),
                    interpolation=cv2.INTER_NEAREST,
                )
            mask = focus_mask > 0
            norm = np.where(mask, norm, 0.0)

        # Base tone comes from the mean luminance of both pixels.
        # This keeps identical bright pixels white, while identical dark pixels
        # stay dark instead of being forced to black or white.
        mean_tone = np.mean(np.concatenate((orig, svg), axis=2), axis=2).astype(np.float32)
        magnitude = np.clip(np.abs(norm), 0.0, 1.0)
        positive = norm >= 0.0

        # Interpolate from grayscale base tone towards signed endpoint colors.
        up = mean_tone + magnitude * (255.0 - mean_tone)
        down = mean_tone * (1.0 - magnitude)

        diff = np.zeros_like(img_orig)
        diff[:, :, 0] = np.where(positive, up, down).astype(np.uint8)
        diff[:, :, 1] = np.where(positive, up, down).astype(np.uint8)
        diff[:, :, 2] = np.where(positive, down, up).astype(np.uint8)
        if mask is not None:
            diff = np.where(mask[:, :, None], diff, 0)
        return diff

    @staticmethod
    def calculate_error(img_orig: np.ndarray, img_svg: np.ndarray) -> float:
        if img_svg is None:
            return float("inf")
        if img_svg.shape[:2] != img_orig.shape[:2]:
            img_svg = cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)
        return float(np.mean(cv2.absdiff(img_orig, img_svg)))

    @staticmethod
    def calculate_delta2_stats(img_orig: np.ndarray, img_svg: np.ndarray) -> tuple[float, float]:
        """Return mean/std of per-pixel squared RGB deltas.

        Per-pixel metric:
            delta2 = (ΔR)^2 + (ΔG)^2 + (ΔB)^2
        """
        if img_svg is None:
            return float("inf"), float("inf")
        if img_svg.shape[:2] != img_orig.shape[:2]:
            img_svg = cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)
        diff = img_orig.astype(np.float32) - img_svg.astype(np.float32)
        delta2 = np.sum(diff * diff, axis=2)
        return float(np.mean(delta2)), float(np.std(delta2))

    @staticmethod
    def _fit_to_original_size(img_orig: np.ndarray, img_svg: np.ndarray | None) -> np.ndarray | None:
        if img_svg is None:
            return None
        if img_svg.shape[:2] == img_orig.shape[:2]:
            return img_svg
        return cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)

    @staticmethod
    def _mask_centroid_radius(mask: np.ndarray) -> tuple[float, float, float] | None:
        ys, xs = np.where(mask)
        if xs.size < 5:
            return None
        cx = float(np.mean(xs))
        cy = float(np.mean(ys))
        r = float(np.sqrt(xs.size / np.pi))
        return cx, cy, r

    @staticmethod
    def _mask_bbox(mask: np.ndarray) -> tuple[float, float, float, float] | None:
        ys, xs = np.where(mask)
        if xs.size < 3:
            return None
        x1, x2 = float(xs.min()), float(xs.max())
        y1, y2 = float(ys.min()), float(ys.max())
        return x1, y1, x2, y2

    @staticmethod
    def _mask_center_size(mask: np.ndarray) -> tuple[float, float, float] | None:
        bbox = Action._mask_bbox(mask)
        if bbox is None:
            return None
        x1, y1, x2, y2 = bbox
        width = max(1.0, (x2 - x1) + 1.0)
        height = max(1.0, (y2 - y1) + 1.0)
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        size = width * height
        return cx, cy, size

    @staticmethod
    def _mask_min_rect_center_diag(mask: np.ndarray) -> tuple[float, float, float] | None:
        mask_u8 = (mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        cnt = max(contours, key=cv2.contourArea)
        if cv2.contourArea(cnt) < 2.0:
            return None

        (cx, cy), (rw, rh), _angle = cv2.minAreaRect(cnt)
