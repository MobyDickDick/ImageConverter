            cx_candidates = [float(current_cx)]
        else:
            cx_candidates = [
                float(Action._clip_scalar(current_cx + offset, 0.0, float(w - 1)))
                for offset in (-shift, -fine_shift, 0.0, fine_shift, shift)
            ]
        if lock_cy:
            cy_candidates = [float(current_cy)]
        else:
            cy_candidates = [
                float(Action._clip_scalar(current_cy + offset, 0.0, float(h - 1)))
                for offset in (-shift, -fine_shift, 0.0, fine_shift, shift)
            ]

        r_candidates = [
            float(Action._clip_scalar(current_r + offset, min_r, max_r))
            for offset in (-radius_span, -fine_radius, 0.0, fine_radius, radius_span)
        ]

        evaluations: dict[tuple[float, float, float], float] = {}

        def eval_pose(cx: float, cy: float, rad: float) -> float:
            key = (cx, cy, rad)
            if key not in evaluations:
                evaluations[key] = float(
                    Action._element_error_for_circle_pose(
                        img_orig,
                        params,
                        cx_value=cx,
                        cy_value=cy,
                        radius_value=rad,
                    )
                )
            return evaluations[key]

        best = (float(current_cx), float(current_cy), float(current_r))
        best_err = eval_pose(*best)

        for cx in cx_candidates:
            for cy in cy_candidates:
                for rad in r_candidates:
                    err = eval_pose(cx, cy, rad)
                    if math.isfinite(err) and err + 0.05 < best_err:
                        best = (cx, cy, rad)
                        best_err = err

        best_cx, best_cy, best_r = best
        if (
            abs(best_cx - current_cx) < 0.02
            and abs(best_cy - current_cy) < 0.02
            and abs(best_r - current_r) < 0.02
        ):
            logs.append(
                f"circle: Joint-Multistart keine relevante Änderung (cx={current_cx:.3f}, cy={current_cy:.3f}, r={current_r:.3f}, best_err={best_err:.3f})"
            )
            return False

        params["cx"] = best_cx
        params["cy"] = best_cy
        params["r"] = best_r
        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, best_r)
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + best_r
            if bool(params.get("lock_stem_center_to_circle", False)):
                stem_w = float(params.get("stem_width", 1.0))
                params["stem_x"] = Action._snap_half(max(0.0, min(float(w) - stem_w, best_cx - (stem_w / 2.0))))

        logs.append(
            f"circle: Joint-Multistart cx {current_cx:.3f}->{best_cx:.3f}, cy {current_cy:.3f}->{best_cy:.3f}, r {current_r:.3f}->{best_r:.3f} (best_err={best_err:.3f})"
        )

        at_boundary = (
            (not lock_cx and (best_cx <= 0.01 or best_cx >= float(w - 1) - 0.01))
            or (not lock_cy and (best_cy <= 0.01 or best_cy >= float(h - 1) - 0.01))
            or abs(best_r - min_r) <= 0.01
            or abs(best_r - max_r) <= 0.01
        )
        if at_boundary:
            logs.append("circle: Joint-Multistart liegt am Rand; starte adaptive Domain-Suche")
            improved = Action._optimize_circle_pose_adaptive_domain(img_orig, params, logs)
            if not improved:
                logs.append("circle: Adaptive-Domain-Suche ohne Gewinn; fallback auf stochastic survivor")
                Action._optimize_circle_pose_stochastic_survivor(img_orig, params, logs)
        return True

    @staticmethod
    def _element_error_for_extent(img_orig: np.ndarray, params: dict, element: str, extent_value: float) -> float:
        h, w = img_orig.shape[:2]
        probe = dict(params)

        if element == "stem" and probe.get("stem_enabled"):
            min_len = 1.0
            max_len = float(h)
            new_len = float(Action._clip_scalar(extent_value, min_len, max_len))
            center = (float(probe.get("stem_top", 0.0)) + float(probe.get("stem_bottom", 0.0))) / 2.0
            half = new_len / 2.0
            probe["stem_top"] = float(Action._clip_scalar(center - half, 0.0, float(h - 1)))
            probe["stem_bottom"] = float(Action._clip_scalar(center + half, probe["stem_top"] + 1.0, float(h)))

