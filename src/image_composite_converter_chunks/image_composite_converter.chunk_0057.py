        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, best[2])
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + best[2]
        Action._log_global_parameter_vector(logs, params, w, h, label="circle: survivor-final")
        logs.append(
            f"circle: Stochastic-Survivor übernommen (cx={best[0]:.3f}, cy={best[1]:.3f}, r={best[2]:.3f}, err={best_err:.3f})"
        )
        return True

    @staticmethod
    def _optimize_circle_pose_adaptive_domain(
        img_orig: np.ndarray,
        params: dict,
        logs: list[str],
        *,
        rounds: int = 4,
        samples_per_round: int = 18,
    ) -> bool:
        """Adaptive random-domain search with iterative domain shrinking.

        Strategy:
        1) Start from a broad but plausible 3D domain (cx, cy, r).
        2) Evaluate random samples and keep a near-optimal plateau.
        3) Estimate a surrogate minimum from the plateau center and best sample.
        4) Shrink the domain and repeat.
        """
        if not params.get("circle_enabled", True):
            return False

        h, w = img_orig.shape[:2]
        Action._log_global_parameter_vector(logs, params, w, h, label="circle: adaptive-start")
        x_low, x_high, y_low, y_high, r_low, r_high = Action._circle_bounds(params, w, h)
        lock_cx = bool(params.get("lock_circle_cx", False))
        lock_cy = bool(params.get("lock_circle_cy", False))

        current = (
            Action._snap_half(float(params.get("cx", (w - 1) / 2.0))),
            Action._snap_half(float(params.get("cy", (h - 1) / 2.0))),
            Action._snap_half(float(params.get("r", max(1.0, min(w, h) * 0.3)))),
        )

        def clamp_pose(candidate: tuple[float, float, float]) -> tuple[float, float, float]:
            cx, cy, rad = candidate
            if lock_cx:
                cx = current[0]
            else:
                cx = Action._snap_half(float(Action._clip_scalar(cx, x_low, x_high)))
            if lock_cy:
                cy = current[1]
            else:
                cy = Action._snap_half(float(Action._clip_scalar(cy, y_low, y_high)))
            rad = Action._snap_half(float(Action._clip_scalar(rad, r_low, r_high)))
            return cx, cy, rad

        cache: dict[tuple[float, float, float], float] = {}

        def eval_pose(candidate: tuple[float, float, float]) -> float:
            pose = clamp_pose(candidate)
            if pose not in cache:
                cache[pose] = float(
                    Action._element_error_for_circle_pose(
                        img_orig,
                        params,
                        cx_value=pose[0],
                        cy_value=pose[1],
                        radius_value=pose[2],
                    )
                )
            return cache[pose]

        best = clamp_pose(current)
        best_err = eval_pose(best)
        if not math.isfinite(best_err):
            return False

        domain = {
            "cx_low": x_low,
            "cx_high": x_high,
            "cy_low": y_low,
            "cy_high": y_high,
            "r_low": r_low,
            "r_high": r_high,
        }

        rng = Action._make_rng(2027 + int(Action.STOCHASTIC_RUN_SEED) + int(Action.STOCHASTIC_SEED_OFFSET))
        improved = False
        flat_plateau_hits = 0

        logs.append(
            (
                "circle: Adaptive-Domain-Suche gestartet "
                f"(Möglichkeitsraum: cx=[{domain['cx_low']:.2f},{domain['cx_high']:.2f}], "
                f"cy=[{domain['cy_low']:.2f},{domain['cy_high']:.2f}], "
                f"r=[{domain['r_low']:.2f},{domain['r_high']:.2f}], "
                f"samples_pro_runde={max(8, int(samples_per_round))})"
            )
        )

        for _round in range(max(1, rounds)):
