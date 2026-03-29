        y1 = float(params.get("arm_y1", cy))
        x2 = float(params.get("arm_x2", cx))
        y2 = float(params.get("arm_y2", cy))
        arm_stroke = float(max(0.0, params.get("arm_stroke", 0.0)))
        attach_offset = arm_stroke / 2.0

        # Preserve dominant orientation (horizontal vs. vertical).
        is_horizontal = abs(x2 - x1) >= abs(y2 - y1)
        if is_horizontal:
            params["arm_y1"] = cy
            params["arm_y2"] = cy
            p1_dist = abs(x1 - cx)
            p2_dist = abs(x2 - cx)
            if p2_dist <= p1_dist:
                params["arm_x2"] = (cx - radius - attach_offset) if x1 <= cx else (cx + radius + attach_offset)
            else:
                params["arm_x1"] = (cx - radius - attach_offset) if x2 <= cx else (cx + radius + attach_offset)
        else:
            params["arm_x1"] = cx
            params["arm_x2"] = cx
            p1_dist = abs(y1 - cy)
            p2_dist = abs(y2 - cy)
            if p2_dist <= p1_dist:
                params["arm_y2"] = (cy - radius - attach_offset) if y1 <= cy else (cy + radius + attach_offset)
            else:
                params["arm_y1"] = (cy - radius - attach_offset) if y2 <= cy else (cy + radius + attach_offset)

    @staticmethod
    def _optimize_circle_center_bracket(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
        if not params.get("circle_enabled", True):
            return False

        h, w = img_orig.shape[:2]
        current_cx = float(params.get("cx", -1.0))
        current_cy = float(params.get("cy", -1.0))
        current_r = float(params.get("r", 0.0))
        if current_r <= 0.0 or current_cx < 0.0 or current_cy < 0.0:
            return False

        lock_cx = bool(params.get("lock_circle_cx", False))
        lock_cy = bool(params.get("lock_circle_cy", False))
        if lock_cx and lock_cy:
            return False

        max_shift = max(1.0, float(min(w, h)) * 0.16)
        x_low = Action._snap_half(max(0.0, current_cx - max_shift))
        x_high = Action._snap_half(min(float(w - 1), current_cx + max_shift))
        y_low = Action._snap_half(max(0.0, current_cy - max_shift))
        y_high = Action._snap_half(min(float(h - 1), current_cy + max_shift))

        evaluations: dict[tuple[float, float], float] = {}

        def eval_center(cx_value: float, cy_value: float) -> float:
            cx_snap = Action._snap_half(float(Action._clip_scalar(cx_value, 0.0, float(w - 1))))
            cy_snap = Action._snap_half(float(Action._clip_scalar(cy_value, 0.0, float(h - 1))))
            key = (cx_snap, cy_snap)
            if key not in evaluations:
                probe = dict(params)
                probe["cx"] = cx_snap
                probe["cy"] = cy_snap
                evaluations[key] = float(Action._element_error_for_circle_radius(img_orig, probe, current_r))
            return evaluations[key]

        def optimize_axis(low: float, high: float, fixed: float, axis: str) -> float:
            if high - low < 0.05:
                return Action._snap_half((low + high) / 2.0)
            mid = Action._snap_half((low + high) / 2.0)
            for _ in range(8):
                if axis == "x":
                    low_err = eval_center(low, fixed)
                    mid_err = eval_center(mid, fixed)
                    high_err = eval_center(high, fixed)
                else:
                    low_err = eval_center(fixed, low)
                    mid_err = eval_center(fixed, mid)
                    high_err = eval_center(fixed, high)

                if not all(math.isfinite(v) for v in (low_err, mid_err, high_err)):
                    return mid

                if mid_err <= low_err and mid_err <= high_err:
                    if low_err <= high_err:
                        high = mid
                    else:
                        low = mid
                elif low_err <= mid_err and low_err <= high_err:
                    high = mid
                else:
                    low = mid

                if high - low < 0.05:
                    break
                next_mid = Action._snap_half((low + high) / 2.0)
                if abs(next_mid - mid) < 0.02:
                    break
                mid = next_mid
            points = [low, mid, high]
            if axis == "x":
                return min(points, key=lambda v: eval_center(v, fixed))
            return min(points, key=lambda v: eval_center(fixed, v))
