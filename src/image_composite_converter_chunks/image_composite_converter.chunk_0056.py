                improved = True
                stable_rounds = 0
            else:
                stable_rounds += 1

            span = max(0.2, span * 0.90)
            if stable_rounds >= 6:
                break

        return best_value, best_err, improved

    @staticmethod
    def _optimize_circle_pose_stochastic_survivor(
        img_orig: np.ndarray,
        params: dict,
        logs: list[str],
        *,
        iterations: int = 24,
    ) -> bool:
        """Stochastic 3-candidate survivor search for circle pose.

        Draw 3 random candidates per round, discard the worst, and continue from
        the best survivor with shrinking perturbation.
        """
        if not params.get("circle_enabled", True):
            return False

        h, w = img_orig.shape[:2]
        Action._log_global_parameter_vector(logs, params, w, h, label="circle: survivor-start")
        x_low, x_high, y_low, y_high, r_low, r_high = Action._circle_bounds(params, w, h)
        current = (
            Action._snap_half(float(params.get("cx", (w - 1) / 2.0))),
            Action._snap_half(float(params.get("cy", (h - 1) / 2.0))),
            Action._snap_half(float(params.get("r", max(1.0, min(w, h) * 0.3)))),
        )
        lock_cx = bool(params.get("lock_circle_cx", False))
        lock_cy = bool(params.get("lock_circle_cy", False))
        rng = Action._make_rng(835 + int(Action.STOCHASTIC_RUN_SEED) + int(Action.STOCHASTIC_SEED_OFFSET))

        def eval_pose(candidate: tuple[float, float, float]) -> float:
            cx, cy, rad = candidate
            return float(
                Action._element_error_for_circle_pose(
                    img_orig,
                    params,
                    cx_value=cx,
                    cy_value=cy,
                    radius_value=rad,
                )
            )

        best = current
        best_err = eval_pose(best)
        if not math.isfinite(best_err):
            return False

        spread_xy = max(1.0, float(min(w, h)) * 0.10)
        spread_r = max(0.6, float(best[2]) * 0.18)
        improved = False
        stable_rounds = 0

        for _ in range(max(1, iterations)):
            candidates: list[tuple[tuple[float, float, float], float]] = [(best, best_err)]
            for _j in range(2):
                if lock_cx:
                    cx = best[0]
                else:
                    cx = Action._snap_half(float(Action._clip_scalar(rng.normal(best[0], spread_xy), x_low, x_high)))
                if lock_cy:
                    cy = best[1]
                else:
                    cy = Action._snap_half(float(Action._clip_scalar(rng.normal(best[1], spread_xy), y_low, y_high)))
                rad = Action._snap_half(float(Action._clip_scalar(rng.normal(best[2], spread_r), r_low, r_high)))
                cand = (cx, cy, rad)
                candidates.append((cand, eval_pose(cand)))

            finite = [pair for pair in candidates if math.isfinite(pair[1])]
            if not finite:
                continue
            finite.sort(key=lambda item: item[1])
            round_best, round_err = finite[0]
            if round_err + 0.05 < best_err:
                best, best_err = round_best, round_err
                improved = True
                stable_rounds = 0
            else:
                stable_rounds += 1

            spread_xy = max(0.4, spread_xy * 0.92)
            spread_r = max(0.35, spread_r * 0.90)
            if stable_rounds >= 7:
                break

        if not improved:
            logs.append("circle: Stochastic-Survivor keine relevante Verbesserung")
            return False

        updated_vector = GlobalParameterVector.from_params(params)
        updated_vector = dataclasses.replace(updated_vector, cx=best[0], cy=best[1], r=best[2])
        params.update(updated_vector.apply_to_params(params))
