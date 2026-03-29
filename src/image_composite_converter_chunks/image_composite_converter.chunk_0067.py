            low_err = eval_radius(low)
            mid_err = eval_radius(mid)
            high_err = eval_radius(high)
            if not all(math.isfinite(v) for v in (low_err, mid_err, high_err)):
                # Gracefully contract away from unsupported samples (e.g. in
                # tests that patch radius evaluators for a sparse subset).
                if not math.isfinite(high_err) and math.isfinite(mid_err):
                    high = mid
                    continue
                if not math.isfinite(low_err) and math.isfinite(mid_err):
                    low = mid
                    continue
                logs.append(
                    "circle: Radius-Bracketing abgebrochen wegen nicht-finiten Fehlern "
                    + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in sorted(evaluations.items()))
                )
                return False

            # Drei-Punkt-Bracketing: immer den besten Punkt und seinen besseren Nachbarn behalten.
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

        best_r, best_err, best_full_err = Action._select_circle_radius_plateau_candidate(img_orig, params, evaluations, current)
        candidate_dump = ", ".join(f"{v:.3f}->{e:.3f}" for v, e in sorted(evaluations.items()))
        if abs(best_r - current) < 0.02:
            logs.append(
                f"circle: Radius-Bracketing keine relevante Änderung (r: {current:.3f}, best_err={best_err:.3f}, full_err={best_full_err:.3f}); Kandidaten="
                + candidate_dump
            )
            return False

        old_r = current
        params["r"] = best_r
        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, best_r)
            # Preserve strictly vertical arm orientation for AC0813/AC0833-like
            # badges: the circle-side endpoint must stay exactly on the circle
            # edge after radius updates.
            ax1 = float(params.get("arm_x1", 0.0))
            ay1 = float(params.get("arm_y1", 0.0))
            ax2 = float(params.get("arm_x2", 0.0))
            ay2 = float(params.get("arm_y2", 0.0))
            if abs(ax1 - ax2) < 1e-6:
                cx = float(params.get("cx", ax1))
                cy = float(params.get("cy", 0.0))
                top_edge = cy - best_r
                bottom_edge = cy + best_r
                params["arm_x1"] = cx
                params["arm_x2"] = cx
                if ay1 <= ay2:
                    params["arm_y2"] = top_edge
                else:
                    params["arm_y1"] = bottom_edge
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + best_r

        logs.append(
            f"circle: Radius-Bracketing r {old_r:.3f}->{best_r:.3f} (best_err={best_err:.3f}, full_err={best_full_err:.3f}); Kandidaten="
            + candidate_dump
        )
        return True

    @staticmethod
    def _optimize_circle_pose_multistart(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
        """Jointly optimize circle center+radius via a compact multi-start grid."""
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

        shift = max(0.5, float(min(w, h)) * 0.08)
        radius_span = max(0.5, current_r * 0.12)
        _x_low, _x_high, _y_low, _y_high, min_r, max_r = Action._circle_bounds(params, w, h)

        fine_shift = min(1.0, shift)
        fine_radius = min(0.5, radius_span)

        if lock_cx:
