            fill_ratio = area / max(1.0, circle_area)
            if fill_ratio < 0.30:
                continue
            bins = 12
            coverage_bins = np.zeros(bins, dtype=np.uint8)
            for px, py in cnt[:, 0, :]:
                ang = math.atan2(float(py) - cy, float(px) - cx)
                idx = int(((ang + math.pi) / (2.0 * math.pi)) * bins) % bins
                coverage_bins[idx] = 1
            coverage = int(np.sum(coverage_bins))
            if coverage < 6:
                continue

            bbox_fill_ratio = area / max(1.0, float(bw * bh))
            # Favor thin ring-like circles or broadly circular contour support.
            if bbox_fill_ratio > 0.82 and radial_residual > max(1.0, radius * 0.22):
                continue

            score = radial_residual + abs(1.0 - aspect) * 3.0 + max(0, 7 - coverage) * 0.75
            if best is None or score < best[0]:
                best = (score, float(cx), float(cy), radius)

        if best is None:
            return None
        return best[1], best[2], best[3]

    @staticmethod
    def _mask_supports_circle(mask: np.ndarray | None) -> bool:
        if mask is None:
            return False
        pixel_count = int(np.count_nonzero(mask))
        if pixel_count < 4:
            return False

        bbox = Action._mask_bbox(mask)
        if bbox is None:
            return False
        x1, y1, x2, y2 = bbox
        width = max(1.0, (x2 - x1) + 1.0)
        height = max(1.0, (y2 - y1) + 1.0)
        if not (0.60 <= (width / height) <= 1.40):
            return False

        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        approx_radius = max(1.0, (width + height) * 0.25)
        area = width * height
        density = float(pixel_count) / max(1.0, area)
        if density < 0.04:
            return False

        ys, xs = np.where(mask)
        bins = 12
        coverage_bins = np.zeros(bins, dtype=np.uint8)
        ring_tol = max(1.2, approx_radius * 0.45)
        near_ring = 0
        for py, px in zip(ys, xs, strict=False):
            dist = math.hypot(float(px) - cx, float(py) - cy)
            if abs(dist - approx_radius) > ring_tol:
                continue
            near_ring += 1
            ang = math.atan2(float(py) - cy, float(px) - cx)
            idx = int(((ang + math.pi) / (2.0 * math.pi)) * bins) % bins
            coverage_bins[idx] = 1

        coverage = int(np.sum(coverage_bins))
        if coverage >= 4 and near_ring >= max(4, int(round(pixel_count * 0.35))):
            return True

        mask_u8 = (mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False
        cnt = max(contours, key=cv2.contourArea)
        perimeter = float(cv2.arcLength(cnt, True))
        if perimeter <= 0.0:
            return False
        contour_area = float(cv2.contourArea(cnt))
        circularity = (4.0 * math.pi * contour_area) / max(1e-6, perimeter * perimeter)
        return circularity >= 0.28 and density <= 0.72

    @staticmethod
    def extract_badge_element_mask(img_orig: np.ndarray, params: dict, element: str) -> np.ndarray | None:
        h, w = img_orig.shape[:2]
        region_mask = Action._element_region_mask(h, w, params, element)
        if region_mask is None:
            return None

        fg_bool = Action._foreground_mask(img_orig)
        mask = fg_bool & region_mask

        dilate_px = int(params.get("validation_mask_dilate_px", 0) or 0)
        if dilate_px > 0 and bool(params.get("ac08_small_variant_mode", False)):
            kernel_size = max(2, (dilate_px * 2) + 1)
            kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
            mask = cv2.dilate(mask.astype(np.uint8) * 255, kernel, iterations=1) > 0
            mask &= region_mask

        if int(mask.sum()) < 3:
            return None
