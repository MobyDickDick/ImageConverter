            old_bottom = float(params["stem_bottom"])

            stem_cx = old_x + (old_w / 2.0)
            if bool(params.get("lock_stem_center_to_circle", False)):
                stem_cx = float(params.get("cx", stem_cx))
            else:
                stem_cx = float(Action._clip_scalar(stem_cx + center_dx * 0.75, 0.0, float(w - 1)))
            new_w = float(Action._clip_scalar(old_w * scale, 1.0, float(w) * 0.22))
            params["stem_width"] = new_w
            params["stem_x"] = float(Action._clip_scalar(stem_cx - (new_w / 2.0), 0.0, float(w) - new_w))
            params["stem_top"] = float(Action._clip_scalar(old_top + center_dy * 0.45, 0.0, float(h - 2)))
            params["stem_bottom"] = float(Action._clip_scalar(old_bottom + center_dy * 0.25, params["stem_top"] + 1.0, float(h - 1)))
            changed = (
                abs(params["stem_x"] - old_x) > 0.02
                or abs(params["stem_width"] - old_w) > 0.02
                or abs(params["stem_top"] - old_top) > 0.02
                or abs(params["stem_bottom"] - old_bottom) > 0.02
            )

        elif element == "arm" and params.get("arm_enabled"):
            old_x1 = float(params["arm_x1"])
            old_x2 = float(params["arm_x2"])
            old_y1 = float(params["arm_y1"])
            old_y2 = float(params["arm_y2"])
            old_stroke = float(params.get("arm_stroke", params.get("stem_or_arm", 1.0)))

            ax1 = old_x1 + center_dx * 0.75
            ax2 = old_x2 + center_dx * 0.75
            ay1 = old_y1 + center_dy * 0.75
            ay2 = old_y2 + center_dy * 0.75
            acx = (ax1 + ax2) / 2.0
            acy = (ay1 + ay2) / 2.0
            vx = (ax2 - ax1) * scale
            vy = (ay2 - ay1) * scale

            params["arm_x1"] = float(Action._clip_scalar(acx - (vx / 2.0), 0.0, float(w - 1)))
            params["arm_x2"] = float(Action._clip_scalar(acx + (vx / 2.0), 0.0, float(w - 1)))
            params["arm_y1"] = float(Action._clip_scalar(acy - (vy / 2.0), 0.0, float(h - 1)))
            params["arm_y2"] = float(Action._clip_scalar(acy + (vy / 2.0), 0.0, float(h - 1)))
            params["arm_stroke"] = float(Action._clip_scalar(old_stroke * scale, 1.0, float(min(w, h)) * 0.18))
            changed = (
                abs(params["arm_x1"] - old_x1) > 0.02
                or abs(params["arm_x2"] - old_x2) > 0.02
                or abs(params["arm_y1"] - old_y1) > 0.02
                or abs(params["arm_y2"] - old_y2) > 0.02
                or abs(params["arm_stroke"] - old_stroke) > 0.02
            )

        elif element == "text" and params.get("draw_text", True):
            mode = str(params.get("text_mode", "")).lower()
            r = max(1.0, float(params.get("r", min(w, h) * 0.45)))

            # Keep text alignment iterative on the vertical axis so badges such as
            # AC0820_L can converge against the source when "CO" drifts too high.
            if mode == "co2":
                old_dy = float(params.get("co2_dy", 0.0))
                params["co2_dy"] = float(Action._clip_scalar(old_dy + center_dy * 0.75, -0.45 * r, 0.45 * r))
                changed = abs(params["co2_dy"] - old_dy) > 0.02
            elif mode == "voc":
                old_dy = float(params.get("voc_dy", 0.0))
                params["voc_dy"] = float(Action._clip_scalar(old_dy + center_dy * 0.75, -0.45 * r, 0.45 * r))
                changed = abs(params["voc_dy"] - old_dy) > 0.02
            elif "ty" in params:
                old_ty = float(params.get("ty", 0.0))
                params["ty"] = float(Action._clip_scalar(old_ty + center_dy * 0.75, 0.0, float(h - 1)))
                changed = abs(params["ty"] - old_ty) > 0.02

        return changed

    @staticmethod
    def _estimate_vertical_stem_from_mask(
        mask: np.ndarray,
        expected_cx: float,
        y_start: int,
        y_end: int,
    ) -> tuple[float, float] | None:
        """Estimate stem center/width from foreground mask rows.

        The estimate is intentionally iterative: we repeatedly reject outliers around
        the running median width so anti-aliased pixels at the circle junction do not
        inflate the final width.
        """
        h, w = mask.shape[:2]
        y1 = max(0, min(h, int(y_start)))
        y2 = max(y1, min(h, int(y_end)))
        if y2 <= y1:
            return None

        # The rows directly below the circle/stem junction are frequently widened
        # by anti-aliased ring pixels. Bias the estimator towards the lower stem
        # segment so thin stems (e.g. tall AC0811 variants) are not over-thickened.
        span = y2 - y1
        if span >= 8:
            y1 = min(y2 - 1, y1 + int(round(span * 0.25)))

        widths: list[float] = []
        centers: list[float] = []
        cx_idx = int(round(expected_cx))

        for y in range(y1, y2):
