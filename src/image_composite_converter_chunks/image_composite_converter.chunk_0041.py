                params["cx"] = cx
                params["cy"] = cy
                params["r"] = r
                est_fill, est_ring, est_stroke = Action._estimate_circle_tones_and_stroke(
                    gray,
                    cx,
                    cy,
                    r,
                    float(params.get("stroke_circle", defaults.get("stroke_circle", 1.2))),
                )
                params["fill_gray"] = int(round(est_fill))
                params["stroke_gray"] = int(round(est_ring))
                has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
                has_text = bool(params.get("draw_text", False))
                if not has_connector and not has_text:
                    params["stroke_circle"] = float(max(1.0, est_stroke))
                    bg_gray = Action._estimate_border_background_gray(gray)
                    if bg_gray >= 240.0:
                        params["background_fill"] = "#ffffff"

        if not bool(params.get("arm_enabled") or params.get("stem_enabled")) and not bool(params.get("draw_text", False)):
            fg_mask = Action._foreground_mask(img)
            edge_touch_min = max(2, int(round(min_side * 0.20)))
            touches_all_edges = all(
                int(np.count_nonzero(edge)) >= edge_touch_min
                for edge in (fg_mask[0, :], fg_mask[-1, :], fg_mask[:, 0], fg_mask[:, -1])
            )
            if not touches_all_edges:
                # JPEG-soft tiny rings may miss foreground pixels on one edge.
                # Use a grayscale border cue as permissive fallback.
                bg_gray = Action._estimate_border_background_gray(gray)
                edge_dark_min = 1
                touches_all_edges = all(
                    int(np.count_nonzero(edge <= (bg_gray - 6.0))) >= edge_dark_min
                    for edge in (gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1])
                )
            if touches_all_edges:
                # Border-touch fallback should recover the visual outer circle
                # extent, not the inner fill radius after stroke normalization.
                # For tiny plain rings (e.g. AC0800_S) this keeps the fitted
                # radius aligned with the expected canvas-fitting geometry.
                border_fit_r = max(1.0, (min_side / 2.0) - 0.5)
                if float(params.get("r", 0.0)) < (border_fit_r - 0.35):
                    params["cx"] = float(defaults.get("cx", float(w) / 2.0))
                    params["cy"] = float(defaults.get("cy", float(h) / 2.0))
                    params["r"] = float(border_fit_r)
                    params["preserve_outer_diameter_on_stroke_normalization"] = True

        # Keep contour/Hough noise from collapsing circles far below the semantic
        # template size. This was most visible for compact centered badges
        # (e.g. AC0820_M), but the guard is intentionally generic for the full
        # semantic badge family.
        if "r" in defaults and "r" in params:
            default_r = float(defaults.get("r", 0.0))
            if default_r > 0.0:
                has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
                has_text = bool(params.get("draw_text", False))
                min_ratio = 0.80
                if not has_connector:
                    min_ratio = 0.88
                if has_text and not has_connector:
                    min_ratio = 0.92

                cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
                cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
                stroke = max(0.0, float(params.get("stroke_circle", defaults.get("stroke_circle", 1.0))))
                radius_limit_x = max(1.0, min(cx, float(w) - cx) - (stroke / 2.0))
                radius_limit_y = max(1.0, min(cy, float(h) - cy) - (stroke / 2.0))
                max_r = max(1.0, min(radius_limit_x, radius_limit_y))
                min_r = min(max_r, max(1.0, default_r * min_ratio))
                params["r"] = float(Action._clip_scalar(float(params.get("r", default_r)), min_r, max_r))

        if params.get("stem_enabled"):
            dark = gray <= min(225, int(np.percentile(gray, 75)))
            x1 = max(0, int(round(params["cx"] - params["r"] * 0.8)))
            x2 = min(w, int(round(params["cx"] + params["r"] * 0.8)))
            y1 = max(0, int(round(params["cy"] + params["r"] * 0.45)))
            roi = dark[y1:h, x1:x2]
            if roi.size > 0:
                cnts, _ = cv2.findContours(roi.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                best_rect = None
                for cnt in cnts:
                    rx, ry, rw, rh = cv2.boundingRect(cnt)
                    if rw < 1 or rh < 2 or rh <= rw:
                        continue
                    area = rw * rh
                    if best_rect is None or area > best_rect[0]:
                        best_rect = (area, rx, ry, rw, rh)
                if best_rect is not None:
                    _, rx, ry, rw, rh = best_rect
                    params["stem_x"] = float(x1 + rx)
                    params["stem_top"] = float(y1 + ry)
                    params["stem_width"] = float(max(1, rw))
                    params["stem_bottom"] = float(min(h, y1 + ry + rh))
                    stem_mask = np.zeros_like(gray, dtype=bool)
                    sx1 = int(max(0, params["stem_x"]))
                    sx2 = int(min(w, params["stem_x"] + params["stem_width"]))
                    sy1 = int(max(0, params["stem_top"]))
                    sy2 = int(min(h, params["stem_bottom"]))
                    stem_mask[sy1:sy2, sx1:sx2] = True
