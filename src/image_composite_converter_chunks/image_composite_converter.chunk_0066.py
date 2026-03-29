
        best_cx = current_cx
        best_cy = current_cy
        if not lock_cx:
            best_cx = optimize_axis(x_low, x_high, current_cy, "x")
        if not lock_cy:
            best_cy = optimize_axis(y_low, y_high, best_cx, "y")

        best_err = eval_center(best_cx, best_cy)
        if not math.isfinite(best_err):
            logs.append("circle: Mittelpunkt-Bracketing abgebrochen wegen nicht-finitem Fehler")
            return False

        if abs(best_cx - current_cx) < 0.02 and abs(best_cy - current_cy) < 0.02:
            logs.append(
                f"circle: Mittelpunkt-Bracketing keine relevante Änderung (cx={current_cx:.3f}, cy={current_cy:.3f}, best_err={best_err:.3f})"
            )
            return False

        params["cx"] = best_cx
        params["cy"] = best_cy
        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, current_r)
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + current_r
            if bool(params.get("lock_stem_center_to_circle", False)):
                stem_w = float(params.get("stem_width", 1.0))
                params["stem_x"] = Action._snap_half(max(0.0, min(float(w) - stem_w, best_cx - (stem_w / 2.0))))

        logs.append(
            f"circle: Mittelpunkt-Bracketing cx {current_cx:.3f}->{best_cx:.3f}, cy {current_cy:.3f}->{best_cy:.3f} (best_err={best_err:.3f})"
        )
        return True

    @staticmethod
    def _optimize_circle_radius_bracket(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
        if not params.get("circle_enabled", True):
            return False

        h, w = img_orig.shape[:2]
        current = float(params.get("r", 0.0))
        if current <= 0.0:
            return False

        min_dim = float(min(w, h))
        low_bound = max(1.0, min_dim * 0.14)
        low_bound = max(low_bound, float(params.get("min_circle_radius", 1.0)))
        low_bound = max(low_bound, float(params.get("circle_radius_lower_bound_px", 1.0)))
        has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
        if has_connector:
            # Connector badges (AC081x/AC083x families) are geometrically tied to
            # a semantic template. If radius bracketing can dive to the generic
            # min-dimension floor, the circle may detach from that template and
            # the connector degenerates into a tiny corner artifact.
            template_r = float(params.get("template_circle_radius", current))
            low_bound = max(low_bound, template_r * 0.88)
            # Also prevent one-shot collapses from noisy element masks.
            low_bound = max(low_bound, current * 0.90)
        # Tiny badges are especially sensitive to anti-aliasing noise in the
        # circle-only error mask. Prevent aggressive downward jumps that make
        # AC0800_S noticeably smaller than the medium/large variants.
        if min_dim <= 22.0:
            low_bound = max(low_bound, current * 0.9)
        allow_overflow = bool(params.get("allow_circle_overflow", False))
        high_bound = min_dim * 0.48
        if allow_overflow:
            high_bound = max(high_bound, float(max(w, h)) * 1.25, low_bound + 0.5)
        if "max_circle_radius" in params:
            high_bound = min(high_bound, float(params.get("max_circle_radius", high_bound)))
        if not has_connector:
            # Plain circles should use a local bracket around the current
            # estimate; broad global ranges are noisy on tiny crops.
            low_bound = max(low_bound, current - 1.0)
            high_bound = min(high_bound, current + 1.0)
        if not low_bound < high_bound:
            return False

        low = math.floor(low_bound * 2.0) / 2.0
        high = math.ceil(high_bound * 2.0) / 2.0
        low = float(Action._clip_scalar(low, low_bound, high_bound))
        high = float(Action._clip_scalar(high, low_bound, high_bound))
        mid = Action._snap_half(float(Action._clip_scalar(current, low, high)))
        mid = float(Action._clip_scalar(mid, low, high))
        if high - low < 0.05:
            return False

        evaluations: dict[float, float] = {}

        def eval_radius(radius: float) -> float:
            clipped = float(Action._clip_scalar(radius, low_bound, high_bound))
            snapped = float(round(clipped, 3))
            if snapped not in evaluations:
                try:
                    evaluations[snapped] = float(Action._element_error_for_circle_radius(img_orig, params, snapped))
                except Exception:
                    evaluations[snapped] = float("inf")
            return evaluations[snapped]

        max_rounds = 12
        for _ in range(max_rounds):
