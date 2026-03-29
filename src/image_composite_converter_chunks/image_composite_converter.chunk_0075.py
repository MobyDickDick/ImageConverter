        }
        issues: list[str] = []
        for key in ("circle", "stem", "arm", "text"):
            exp = bool(expected.get(key, False))
            obs = bool(observed.get(key, False))
            if exp and not obs:
                issues.append(f"Beschreibung erwartet {labels[key]}, im Bild aber nicht robust erkennbar")
            if obs and not exp:
                issues.append(f"Im Bild ist {labels[key]} erkennbar, aber nicht in der Beschreibung enthalten")
        return issues

    @staticmethod
    def _detect_semantic_primitives(
        img_orig: np.ndarray,
        badge_params: dict | None = None,
    ) -> dict[str, bool | int | str]:
        """Detect coarse semantic primitives directly from the raw bitmap.

        This guard is intentionally conservative: it should flag obvious non-badge
        inserts (e.g. arbitrary crossing lines) before we accept semantic badge
        reconstruction from templated defaults.
        """
        h, w = img_orig.shape[:2]
        if h <= 0 or w <= 0:
            return {
                "circle": False,
                "stem": False,
                "arm": False,
                "text": False,
                "circle_detection_source": "none",
                "connector_orientation": "none",
                "horizontal_line_candidates": 0,
                "vertical_line_candidates": 0,
            }

        gray = cv2.cvtColor(img_orig, cv2.COLOR_BGR2GRAY)
        fg_mask = Action._foreground_mask(img_orig).astype(np.uint8)
        min_side = max(1, min(h, w))
        small_variant = bool((badge_params or {}).get("ac08_small_variant_mode", False))
        symbol_hint = str((badge_params or {}).get("badge_symbol_name", "")).upper()
        circle_detection_source = "none"

        # Circle cue: require at least one plausible Hough circle.
        circles = cv2.HoughCircles(
            cv2.GaussianBlur(gray, (5, 5), 0),
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=max(8.0, min_side * 0.30),
            param1=90,
            param2=max(8, int(round(min_side * 0.22))),
            minRadius=max(3, int(round(min_side * 0.12))),
            maxRadius=max(8, int(round(min_side * 0.48))),
        )
        has_circle = False
        circle_geom: tuple[float, float, float] | None = None
        if circles is not None and circles.size > 0:
            circle_candidates = np.round(circles[0, :]).astype(int)
            for cx, cy, radius in circle_candidates:
                r = int(max(3, radius))
                yy, xx = np.ogrid[:h, :w]
                dist = np.sqrt((xx - int(cx)) ** 2 + (yy - int(cy)) ** 2)
                ring = np.abs(dist - float(r)) <= max(1.2, float(r) * 0.20)
                ring_count = int(np.sum(ring))
                if ring_count <= 0:
                    continue

                support = fg_mask[ring] > 0
                support_ratio = float(np.mean(support))
                if support_ratio < 0.24:
                    continue

                # Require broad angular coverage so tiny arcs/noisy crescents
                # cannot pass as semantic circles.
                bins = 12
                coverage_bins = np.zeros(bins, dtype=np.uint8)
                ring_coords = np.argwhere(ring)
                for py, px in ring_coords:
                    if fg_mask[py, px] <= 0:
                        continue
                    ang = math.atan2(float(py - cy), float(px - cx))
                    idx = int(((ang + math.pi) / (2.0 * math.pi)) * bins) % bins
                    coverage_bins[idx] = 1
                if int(np.sum(coverage_bins)) < 6:
                    continue

                has_circle = True
                circle_geom = (float(cx), float(cy), float(r))
                circle_detection_source = "hough"
                break

        if not has_circle:
            fallback_circle = Action._circle_from_foreground_mask(fg_mask > 0)
            if fallback_circle is not None:
                has_circle = True
                circle_geom = fallback_circle
                circle_detection_source = "foreground_mask"

        if not has_circle and badge_params:
            # `_S` AC08 families can keep a visually correct ring while Hough and
            # contour-only extraction both fail due to anti-aliased compression.
