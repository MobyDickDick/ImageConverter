        plateau_rounds: list[dict[str, float | int]] = []
        logs.append(
            f"global-search: gestartet (aktive_parameter={','.join(active_keys)}, samples_pro_runde={max(8, int(samples_per_round))}, start_err={best_err:.3f})"
        )
        logs.append(
            f"global-search: near-optimum-definition (err <= best_err + epsilon, epsilon=max({near_optimum_eps_floor:.2f}, best_err*{near_optimum_eps_rel:.2f}))"
        )

        for round_idx in range(max(1, int(rounds))):
            accepted = 0
            finite_round: list[tuple[GlobalParameterVector, float]] = [(best, best_err)]
            for _ in range(max(8, int(samples_per_round))):
                sample_data = dataclasses.asdict(best)
                for key in active_keys:
                    low, high, _locked, _source = bounds[key]
                    sigma = spans[key]
                    sample_data[key] = float(Action._clip_scalar(rng.normal(float(sample_data[key]), sigma), low, high))
                candidate = clamp_vector(GlobalParameterVector(**sample_data))
                candidate_err = eval_vector(candidate)
                if math.isfinite(candidate_err):
                    finite_round.append((candidate, candidate_err))
                if math.isfinite(candidate_err) and candidate_err + 0.05 < best_err:
                    best = candidate
                    best_err = candidate_err
                    accepted += 1
                    improved = True

            round_best_err = min(err for _cand, err in finite_round)
            round_best = min(finite_round, key=lambda item: item[1])[0]
            epsilon = max(near_optimum_eps_floor, round_best_err * near_optimum_eps_rel)
            plateau = [(cand, err) for cand, err in finite_round if err <= round_best_err + epsilon]
            span_labels: list[str] = []
            mean_span = 0.0
            if plateau:
                span_values: list[float] = []
                for key in active_keys:
                    key_values = [float(getattr(cand, key)) for cand, _err in plateau]
                    key_span = max(key_values) - min(key_values)
                    span_values.append(key_span)
                    span_labels.append(f"{key}:{key_span:.3f}")
                mean_span = sum(span_values) / max(1, len(span_values))

            representative = round_best
            representative_err = round_best_err
            representative_source = "best_sample"
            representative_reason = "niedrigster Fehler in dieser Runde"

            if plateau:
                weighted_data = dataclasses.asdict(round_best)
                weight_sum = 0.0
                for cand, cand_err in plateau:
                    weight = 1.0 / (1.0 + max(0.0, float(cand_err) - round_best_err))
                    weight_sum += weight
                    for key in active_keys:
                        weighted_data[key] = float(weighted_data[key]) + (float(getattr(cand, key)) * weight)
                if weight_sum > 0.0:
                    for key in active_keys:
                        weighted_data[key] = float(weighted_data[key]) / (1.0 + weight_sum)
                    centroid_raw = GlobalParameterVector(**weighted_data)
                    centroid = clamp_vector(centroid_raw)
                    centroid_safe, centroid_msg = within_hard_bounds(centroid)
                    if not centroid_safe:
                        logs.append(
                            f"global-search: schwerpunkt verworfen (runde={round_idx + 1}, grund={centroid_msg})"
                        )
                    else:
                        centroid_err = eval_vector(centroid)
                        if math.isfinite(centroid_err):
                            near_best_margin = max(0.02, epsilon * 0.30)
                            if centroid_err <= round_best_err + near_best_margin and len(plateau) >= 3:
                                representative = centroid
                                representative_err = centroid_err
                                representative_source = "schwerpunkt"
                                representative_reason = (
                                    "nahe am Bestpunkt und robuster Zentrumskandidat des Plateau-Bereichs"
                                )
                            elif centroid_err < round_best_err:
                                representative = centroid
                                representative_err = centroid_err
                                representative_source = "schwerpunkt"
                                representative_reason = "geringerer Fehler als best_sample"
                        else:
                            logs.append(
                                "global-search: schwerpunkt verworfen "
                                f"(runde={round_idx + 1}, grund=fehlerbewertung nicht endlich)"
                            )

            if representative_source == "schwerpunkt":
                if representative_err <= best_err + 0.02:
                    best = representative
                    best_err = representative_err
                    improved = True
            elif representative_err + 0.01 < best_err:
                best = representative
                best_err = representative_err
                improved = True

            stability = "n/a"
            if plateau_rounds:
                prev_center = float(plateau_rounds[-1]["center_mean"])
