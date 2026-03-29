            # Validate the family template circle directly against foreground ring
            # support so the semantic gate can still accept robust circle evidence.
            if small_variant and symbol_hint in {"AC0811", "AC0814", "AC0870"}:
                exp_cx = float(badge_params.get("cx", float(w) / 2.0))
                exp_cy = float(badge_params.get("cy", float(h) / 2.0))
                exp_r = float(badge_params.get("r", max(2.0, float(min_side) * 0.28)))
                exp_r = float(Action._clip_scalar(exp_r, 2.0, float(min_side) * 0.60))
                yy, xx = np.ogrid[:h, :w]
                ring_tol = max(1.2, exp_r * 0.32)
                ring = np.abs(np.sqrt((xx - exp_cx) ** 2 + (yy - exp_cy) ** 2) - exp_r) <= ring_tol
                ring_count = int(np.count_nonzero(ring))
                if ring_count > 0:
                    support_ratio = float(np.mean(fg_mask[ring] > 0))
                    if support_ratio >= 0.18:
                        bins = 12
                        coverage_bins = np.zeros(bins, dtype=np.uint8)
                        ring_coords = np.argwhere(ring)
                        for py, px in ring_coords:
                            if fg_mask[py, px] <= 0:
                                continue
                            ang = math.atan2(float(py) - exp_cy, float(px) - exp_cx)
                            idx = int(((ang + math.pi) / (2.0 * math.pi)) * bins) % bins
                            coverage_bins[idx] = 1
                        if int(np.sum(coverage_bins)) >= 5:
                            has_circle = True
                            circle_geom = (exp_cx, exp_cy, exp_r)
                            circle_detection_source = "family_fallback"

        # Connector cues: long near-axis-aligned segment via probabilistic Hough.
        has_arm = False
        has_stem = False
        horizontal_candidates = 0
        vertical_candidates = 0
        strongest_horizontal = 0
        strongest_vertical = 0
        edges = cv2.Canny(gray, 45, 140)
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180.0,
            threshold=max(8, int(round(min_side * 0.28))),
            minLineLength=max(6, int(round(float(w) * 0.22))),
            maxLineGap=max(3, int(round(min_side * 0.06))),
        )
        if lines is not None:
            for seg in lines.reshape(-1, 4):
                x1, y1, x2, y2 = [int(v) for v in seg]
                dx = abs(x2 - x1)
                dy = abs(y2 - y1)
                is_horizontal = dx >= max(6, int(round(float(w) * 0.20))) and dy <= max(1, int(round(dx * 0.18)))
                is_vertical = dy >= max(6, int(round(float(h) * 0.20))) and dx <= max(1, int(round(dy * 0.18)))
                if not is_horizontal and not is_vertical:
                    continue
                if circle_geom is not None:
                    cx, cy, radius = circle_geom
                    endpoint_d1 = math.hypot(float(x1) - cx, float(y1) - cy)
                    endpoint_d2 = math.hypot(float(x2) - cx, float(y2) - cy)
                    expanded_r = float(radius) + max(1.5, float(radius) * 0.10)
                    # Ignore short bars that stay inside the circle (e.g. the top
                    # bar of a "T" glyph). A semantic arm must visibly leave the
                    # circle silhouette on at least one side.
                    if endpoint_d1 <= expanded_r and endpoint_d2 <= expanded_r:
                        continue
                    outside_len = 0.0
                    if endpoint_d1 > expanded_r:
                        outside_len += max(0.0, endpoint_d1 - expanded_r)
                    if endpoint_d2 > expanded_r:
                        outside_len += max(0.0, endpoint_d2 - expanded_r)
                    if outside_len < max(2.0, float(w) * 0.08):
                        continue
                    sample_count = max(8, max(dx, dy) + 1)
                    near_ring = 0
                    outside_samples = 0
                    for step in range(sample_count):
                        t = step / max(1, sample_count - 1)
                        sx = float(x1) + (float(x2) - float(x1)) * t
                        sy = float(y1) + (float(y2) - float(y1)) * t
                        dist = math.hypot(sx - cx, sy - cy)
                        if dist > expanded_r:
                            outside_samples += 1
                        if abs(dist - radius) <= max(1.2, float(radius) * 0.16):
                            near_ring += 1
                    # Tiny circle arcs can appear as horizontal line segments in
                    # HoughLinesP. Treat them as ring evidence, not as external arms,
                    # when most samples cling to the circle circumference and only a
                    # small fraction actually leaves the circle silhouette.
                    if near_ring >= int(round(sample_count * 0.55)) and outside_samples <= int(round(sample_count * 0.35)):
                        continue
                    if is_horizontal:
                        # Real semantic arms must sit mostly on one side of the circle.
                        mid_x = (float(x1) + float(x2)) / 2.0
                        if abs(mid_x - cx) < max(1.5, float(radius) * 0.35):
                            continue
                    if is_vertical:
                        # Real semantic stems/vertical arms must sit mostly above or
                        # below the circle rather than through its center.
                        mid_y = (float(y1) + float(y2)) / 2.0
                        if abs(mid_y - cy) < max(1.5, float(radius) * 0.35):
                            continue
                if is_horizontal:
