            samples: list[tuple[tuple[float, float, float], float]] = [(best, best_err)]
            for _ in range(max(8, int(samples_per_round))):
                if lock_cx:
                    cx = current[0]
                else:
                    cx = float(rng.uniform(domain["cx_low"], domain["cx_high"]))
                if lock_cy:
                    cy = current[1]
                else:
                    cy = float(rng.uniform(domain["cy_low"], domain["cy_high"]))
                rad = float(rng.uniform(domain["r_low"], domain["r_high"]))
                pose = clamp_pose((cx, cy, rad))
                samples.append((pose, eval_pose(pose)))

            finite = [pair for pair in samples if math.isfinite(pair[1])]
            if not finite:
                continue
            finite.sort(key=lambda item: item[1])
            round_best, round_best_err = finite[0]

            # Build a near-optimal plateau and use its center as a smooth surrogate.
            plateau_eps = max(0.06, round_best_err * 0.02)
            plateau = [pose for pose, err in finite if err <= round_best_err + plateau_eps]
            if len(plateau) >= 4:
                flat_plateau_hits += 1

            plateau_points = plateau if plateau else [round_best]
            pmin_cx = min(p[0] for p in plateau_points)
            pmin_cy = min(p[1] for p in plateau_points)
            pmin_r = min(p[2] for p in plateau_points)
            pmax_cx = max(p[0] for p in plateau_points)
            pmax_cy = max(p[1] for p in plateau_points)
            pmax_r = max(p[2] for p in plateau_points)
            plateau_mid = clamp_pose(((pmin_cx + pmax_cx) / 2.0, (pmin_cy + pmax_cy) / 2.0, (pmin_r + pmax_r) / 2.0))
            plateau_mid_err = eval_pose(plateau_mid)

            candidate_best = round_best
            candidate_err = round_best_err
            if math.isfinite(plateau_mid_err) and plateau_mid_err < candidate_err:
                candidate_best = plateau_mid
                candidate_err = plateau_mid_err

            if candidate_err + 0.05 < best_err:
                best = candidate_best
                best_err = candidate_err
                improved = True

            logs.append(
                (
                    f"circle: Runde {_round + 1} random-samples={len(samples) - 1}, "
                    f"Error-Minimum={best_err:.3f} bei "
                    f"(cx={best[0]:.3f}, cy={best[1]:.3f}, r={best[2]:.3f})"
                )
            )
            round_vector = GlobalParameterVector.from_params(params)
            round_vector = dataclasses.replace(round_vector, cx=best[0], cy=best[1], r=best[2])
            round_params = round_vector.apply_to_params(params)
            Action._log_global_parameter_vector(logs, round_params, w, h, label=f"circle: Runde {_round + 1}")

            # Iteratively shrink domain around the stable near-optimal region.
            shrink = 0.58
            if not lock_cx:
                half_span = max(0.5, float((domain["cx_high"] - domain["cx_low"]) * shrink * 0.5))
                focus = float(best[0] if len(plateau) <= 1 else (pmin_cx + pmax_cx) / 2.0)
                domain["cx_low"] = max(x_low, focus - half_span)
                domain["cx_high"] = min(x_high, focus + half_span)
            if not lock_cy:
                half_span = max(0.5, float((domain["cy_high"] - domain["cy_low"]) * shrink * 0.5))
                focus = float(best[1] if len(plateau) <= 1 else (pmin_cy + pmax_cy) / 2.0)
                domain["cy_low"] = max(y_low, focus - half_span)
                domain["cy_high"] = min(y_high, focus + half_span)
            half_span_r = max(0.5, float((domain["r_high"] - domain["r_low"]) * shrink * 0.5))
            focus_r = float(best[2] if len(plateau) <= 1 else (pmin_r + pmax_r) / 2.0)
            domain["r_low"] = max(r_low, focus_r - half_span_r)
            domain["r_high"] = min(r_high, focus_r + half_span_r)

            logs.append(
                (
                    f"circle: Runde {_round + 1} Möglichkeitsraum eingegrenzt auf "
                    f"cx=[{domain['cx_low']:.2f},{domain['cx_high']:.2f}], "
                    f"cy=[{domain['cy_low']:.2f},{domain['cy_high']:.2f}], "
                    f"r=[{domain['r_low']:.2f},{domain['r_high']:.2f}]"
                )
            )

        if not improved:
            logs.append("circle: Adaptive-Domain-Suche keine relevante Verbesserung")
            return False

        updated_vector = GlobalParameterVector.from_params(params)
        updated_vector = dataclasses.replace(updated_vector, cx=best[0], cy=best[1], r=best[2])
        params.update(updated_vector.apply_to_params(params))
        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, best[2])
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + best[2]
        Action._log_global_parameter_vector(logs, params, w, h, label="circle: adaptive-final")

        boundary_hit = (
            (not lock_cx and (abs(best[0] - x_low) <= 0.01 or abs(best[0] - x_high) <= 0.01))
