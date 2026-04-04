"""Global-search optimization helpers for imageCompositeConverter."""

from __future__ import annotations

import dataclasses
import math


def optimizeGlobalParameterVectorSamplingImpl(
    img_orig,
    params: dict,
    logs: list[str],
    *,
    rounds: int,
    samples_per_round: int,
    global_parameter_vector_cls,
    global_parameter_vector_bounds_fn,
    clip_scalar_fn,
    snap_half_fn,
    make_rng_fn,
    reanchor_arm_to_circle_edge_fn,
    full_badge_error_for_params_fn,
    log_global_parameter_vector_fn,
    stochastic_run_seed: int,
    stochastic_seed_offset: int,
) -> bool:
    """Global multi-parameter baseline search over the shared vector."""
    if not bool(params.get("enable_global_search_mode", False)):
        return False

    near_optimum_eps_floor = 0.06
    near_optimum_eps_rel = 0.02

    h, w = img_orig.shape[:2]
    bounds = global_parameter_vector_bounds_fn(params, w, h)
    vector = global_parameter_vector_cls.fromParams(params)

    active_keys: list[str] = []
    for key in ("cx", "cy", "r", "stem_x", "stem_width", "text_x", "text_y", "text_scale"):
        value = getattr(vector, key)
        if value is None:
            continue
        _low, _high, locked, _source = bounds[key]
        if locked:
            continue
        active_keys.append(key)

    if len(active_keys) < 4:
        logs.append("global-search: übersprungen (zu wenige aktive Parameter; benötigt >=4)")
        return False

    def clampVector(candidate):
        data = dataclasses.asdict(candidate)
        for key in active_keys:
            low, high, _locked, _source = bounds[key]
            current_value = float(data[key])
            clipped = float(clip_scalar_fn(current_value, low, high))
            if key in {"cx", "cy", "r", "stem_x", "stem_width", "text_x", "text_y"}:
                clipped = float(snap_half_fn(clipped))
            data[key] = clipped
        return global_parameter_vector_cls(**data)

    def evalVector(candidate) -> float:
        probe = candidate.apply_to_params(params)
        if probe.get("arm_enabled"):
            reanchor_arm_to_circle_edge_fn(probe, float(probe.get("r", 0.0)))
        if probe.get("stem_enabled"):
            probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe.get("r", 0.0))
            if bool(probe.get("lock_stem_center_to_circle", False)):
                stem_w = float(probe.get("stem_width", 1.0))
                probe["stem_x"] = snap_half_fn(
                    max(0.0, min(float(w) - stem_w, float(probe.get("cx", 0.0)) - (stem_w / 2.0)))
                )
        return full_badge_error_for_params_fn(img_orig, probe)

    def withinHardBounds(candidate) -> tuple[bool, str]:
        for key in active_keys:
            low, high, _locked, _source = bounds[key]
            value = float(getattr(candidate, key))
            if value < low - 1e-6 or value > high + 1e-6:
                return False, f"{key}={value:.3f} außerhalb [{low:.3f}, {high:.3f}]"
        return True, "ok"

    seed = 4099 + int(stochastic_run_seed) + int(stochastic_seed_offset)
    rng = make_rng_fn(seed)
    start_vector = clampVector(vector)
    start_err = evalVector(start_vector)
    if not math.isfinite(start_err):
        return False

    def runStochasticTrack():
        best = start_vector
        best_err = start_err
        improved = False
        spans = {key: max(0.25, float(bounds[key][1] - bounds[key][0]) * 0.20) for key in active_keys}
        plateau_rounds: list[dict[str, float | int]] = []
        logs.append(
            f"global-search: gestartet (aktive_parameter={','.join(active_keys)}, samples_pro_runde={max(8, int(samples_per_round))}, start_err={best_err:.3f})"
        )
        logs.append(
            f"global-search: near-optimum-definition (err <= best_err + epsilon, epsilon=max({near_optimum_eps_floor:.2f}, best_err*{near_optimum_eps_rel:.2f}))"
        )

        for round_idx in range(max(1, int(rounds))):
            accepted = 0
            finite_round = [(best, best_err)]
            for _ in range(max(8, int(samples_per_round))):
                sample_data = dataclasses.asdict(best)
                for key in active_keys:
                    low, high, _locked, _source = bounds[key]
                    sigma = spans[key]
                    sample_data[key] = float(clip_scalar_fn(rng.normal(float(sample_data[key]), sigma), low, high))
                candidate = clampVector(global_parameter_vector_cls(**sample_data))
                candidate_err = evalVector(candidate)
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
                    centroid_raw = global_parameter_vector_cls(**weighted_data)
                    centroid = clampVector(centroid_raw)
                    centroid_safe, centroid_msg = withinHardBounds(centroid)
                    if not centroid_safe:
                        logs.append(
                            f"global-search: schwerpunkt verworfen (runde={round_idx + 1}, grund={centroid_msg})"
                        )
                    else:
                        centroid_err = evalVector(centroid)
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
                center_now = 0.0
                if plateau:
                    center_now = sum(
                        float(
                            getattr(plateau[0][0], key)
                            if len(plateau) == 1
                            else (min(float(getattr(cand, key)) for cand, _ in plateau) + max(float(getattr(cand, key)) for cand, _ in plateau)) / 2.0
                        )
                        for key in active_keys
                    ) / max(1, len(active_keys))
                center_shift = abs(center_now - prev_center)
                stability = "stabil" if center_shift <= 0.35 else "dynamisch"
                plateau_rounds.append({"size": len(plateau), "mean_span": mean_span, "center_mean": center_now})
            else:
                center_now = 0.0
                if plateau:
                    center_now = sum(
                        float(
                            getattr(plateau[0][0], key)
                            if len(plateau) == 1
                            else (min(float(getattr(cand, key)) for cand, _ in plateau) + max(float(getattr(cand, key)) for cand, _ in plateau)) / 2.0
                        )
                        for key in active_keys
                    ) / max(1, len(active_keys))
                plateau_rounds.append({"size": len(plateau), "mean_span": mean_span, "center_mean": center_now})
            for key in active_keys:
                spans[key] = max(0.12, spans[key] * 0.78)
            logs.append(
                f"global-search: Runde {round_idx + 1} best_err={best_err:.3f}, akzeptierte_kandidaten={accepted}, sigma_mittel={sum(spans.values()) / max(1, len(spans)):.3f}"
            )
            logs.append(
                "global-search: near-optimum-plateau "
                f"(runde={round_idx + 1}, punkte={len(plateau)}, epsilon={epsilon:.3f}, "
                f"mittlere_spannweite={mean_span:.3f}, stabilitaet={stability}, "
                f"spannweite={'; '.join(span_labels) if span_labels else 'n/a'})"
            )
            logs.append(
                "global-search: plateau-repräsentant "
                f"(runde={round_idx + 1}, kandidat={representative_source}, err={representative_err:.3f}, "
                f"begründung={representative_reason})"
            )
        return best, best_err, improved

    def runDeterministicTrack():
        best = start_vector
        best_err = start_err
        improved = False
        rounded_keys = {"cx", "cy", "r", "stem_x", "stem_width", "text_x", "text_y"}
        step_sizes = {
            key: max(0.10, (0.5 if key in rounded_keys else 0.10), float(bounds[key][1] - bounds[key][0]) * 0.18)
            for key in active_keys
        }
        logs.append(
            "global-search: deterministischer track gestartet "
            f"(seed={int(seed)}, schritte={max(2, int(rounds))}, start_err={best_err:.3f})"
        )
        for pass_idx in range(max(2, int(rounds))):
            pass_improved = 0
            for key in active_keys:
                step = step_sizes[key]
                if key in rounded_keys:
                    step = max(0.5, round(step * 2.0) / 2.0)
                else:
                    step = max(0.10, step)
                candidates = []
                for direction in (-1.0, 1.0):
                    cand_data = dataclasses.asdict(best)
                    cand_data[key] = float(cand_data[key]) + (direction * step)
                    cand = clampVector(global_parameter_vector_cls(**cand_data))
                    cand_err = evalVector(cand)
                    if math.isfinite(cand_err):
                        candidates.append((cand, cand_err))
                if not candidates:
                    continue
                cand_best, cand_best_err = min(candidates, key=lambda item: item[1])
                if cand_best_err + 0.01 < best_err:
                    best = cand_best
                    best_err = cand_best_err
                    improved = True
                    pass_improved += 1
                step_sizes[key] = max(
                    0.10 if key not in rounded_keys else 0.5,
                    step_sizes[key] * (0.70 if pass_improved else 0.82),
                )
            logs.append(
                "global-search: deterministischer track "
                f"(pass={pass_idx + 1}, verbesserungen={pass_improved}, best_err={best_err:.3f})"
            )
            if pass_improved == 0 and pass_idx >= 1:
                break
        return best, best_err, improved

    stochastic_best, stochastic_err, stochastic_improved = runStochasticTrack()
    deterministic_best, deterministic_err, deterministic_improved = runDeterministicTrack()

    winner_name = "stochastic"
    winner = stochastic_best
    winner_err = stochastic_err
    winner_improved = stochastic_improved
    if math.isfinite(deterministic_err) and (not math.isfinite(winner_err) or deterministic_err + 1e-6 < winner_err):
        winner_name = "deterministic"
        winner = deterministic_best
        winner_err = deterministic_err
        winner_improved = deterministic_improved

    logs.append(
        "global-search: track-vergleich "
        f"(stochastic_err={stochastic_err:.3f}, deterministic_err={deterministic_err:.3f}, gewählt={winner_name})"
    )

    if not winner_improved and winner_err >= start_err - 0.01:
        logs.append("global-search: keine relevante Verbesserung")
        return False

    old_values = {key: float(getattr(vector, key)) for key in active_keys}
    new_values = {key: float(getattr(winner, key)) for key in active_keys}
    params.update(winner.applyToParams(params))
    delta_labels = [
        f"{key} {old_values[key]:.3f}->{new_values[key]:.3f}"
        for key in active_keys
        if abs(new_values[key] - old_values[key]) >= 0.01
    ]
    if params.get("arm_enabled"):
        reanchor_arm_to_circle_edge_fn(params, float(params.get("r", 0.0)))
    if params.get("stem_enabled"):
        params["stem_top"] = float(params.get("cy", 0.0)) + float(params.get("r", 0.0))
    log_global_parameter_vector_fn(logs, params, w, h, label=f"global-search: final ({winner_name})")
    logs.append(
        "global-search: übernommen "
        f"(best_err={winner_err:.3f}, track={winner_name}, verbessert={', '.join(delta_labels) if delta_labels else 'keine sichtbare delta-liste'})"
    )
    return True
