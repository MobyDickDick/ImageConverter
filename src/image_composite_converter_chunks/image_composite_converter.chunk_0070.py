            if forced_abs_min is not None:
                low_bound = max(low_bound, float(forced_abs_min))
            forced_min_ratio = params.get("arm_len_min_ratio")
            if forced_min_ratio is not None:
                min_ratio = float(max(0.0, min(1.0, float(forced_min_ratio))))
                low_bound = max(low_bound, current * min_ratio)
            # Keep edge-anchored connector variants (e.g. AC0832_S) from collapsing
            # to tiny stubs when element-only error masks under-segment thin lines.
            is_edge_anchored = any(
                (
                    float(params.get(key, 0.0)) <= 0.5
                    or float(params.get(key, 0.0)) >= float(limit) - 0.5
                )
                for key, limit in (
                    ("arm_x1", w),
                    ("arm_x2", w),
                    ("arm_y1", h),
                    ("arm_y2", h),
                )
            )
            if forced_min_ratio is None and is_edge_anchored and params.get("circle_enabled", True):
                min_ratio = float(params.get("arm_len_min_ratio", 0.75))
                low_bound = max(low_bound, current * max(0.0, min(1.0, min_ratio)))
        else:
            return False

        if current <= 0.0:
            return False

        low = float(low_bound)
        high = float(high_bound)
        if not (low < high):
            logs.append(
                f"{element}: Längen-Bracketing übersprungen ({key_label}: current={current:.3f}, "
                f"Range={low_bound:.3f}..{high_bound:.3f})"
            )
            return False

        candidates = sorted(
            {
                Action._snap_half(low),
                Action._snap_half(low + (high - low) * 0.25),
                Action._snap_half((low + high) / 2.0),
                Action._snap_half(low + (high - low) * 0.75),
                Action._snap_half(high),
                Action._snap_half(Action._clip_scalar(current, low, high)),
            }
        )
        candidate_errors = [Action._element_error_for_extent(img_orig, params, element, v) for v in candidates]
        if not all(math.isfinite(e) for e in candidate_errors):
            logs.append(
                f"{element}: Längen-Bracketing abgebrochen ({key_label}) wegen nicht-finiten Fehlern "
                + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
            )
            return False

        best_idx = Action._argmin_index(candidate_errors)
        best_len = float(candidates[best_idx])

        boundary_best = abs(best_len - low) < 0.02 or abs(best_len - high) < 0.02
        if boundary_best:
            s_best, s_err, s_improved = Action._stochastic_survivor_scalar(
                current,
                low,
                high,
                lambda v: Action._element_error_for_extent(img_orig, params, element, float(v)),
                snap=Action._snap_half,
                seed=1103 if element == "stem" else 1109,
            )
            if s_improved:
                best_len = float(s_best)
                logs.append(
                    f"{element}: Längen-Stochastic-Survivor aktiviert (best_len={best_len:.3f}, err={s_err:.3f})"
                )

        if abs(best_len - current) < 0.02:
            logs.append(
                f"{element}: Längen-Bracketing keine relevante Änderung ({key_label}: {current:.3f}); "
                f"Kandidaten="
                + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
            )
            return False

        if element == "stem":
            if params.get("circle_enabled", True) and all(k in params for k in ("cy", "r")):
                # Keep tiny bottom-anchored stems visibly long by preserving the
                # bottom anchor and moving the free top endpoint upward.
                is_bottom_anchored = float(params.get("stem_bottom", 0.0)) >= float(h) - 0.5
                if is_bottom_anchored and h <= 15 and not bool(params.get("draw_text", True)):
                    bottom = float(h)
                    top = float(Action._clip_scalar(bottom - best_len, 0.0, bottom - 1.0))
                    params["stem_top"] = top
                    params["stem_bottom"] = bottom
                else:
                    # Keep the stem attached to the circle edge and optimize only the free end.
                    top = float(Action._clip_scalar(float(params.get("cy", 0.0)) + float(params.get("r", 0.0)), 0.0, float(h - 1)))
                    params["stem_top"] = top
                    params["stem_bottom"] = float(Action._clip_scalar(top + best_len, top + 1.0, float(h)))
            else:
                center = (float(params.get("stem_top", 0.0)) + float(params.get("stem_bottom", 0.0))) / 2.0
