"""Global-search optimization helpers for imageCompositeConverter."""

from __future__ import annotations

import dataclasses
import math
from collections import OrderedDict

_CROSS_ROUND_EVAL_CACHE_MAX = 4096
_CROSS_ROUND_EVAL_CACHE: OrderedDict[tuple[int, tuple], float] = OrderedDict()


def _freeze_eval_value(value):
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, int):
        return ("int", int(value))
    if isinstance(value, float):
        if math.isnan(value):
            return ("float", "nan")
        if math.isinf(value):
            return ("float", "inf" if value > 0 else "-inf")
        return ("float", round(value, 6))
    if isinstance(value, str):
        return ("str", value)
    return ("repr", repr(value))


def _probe_cache_key(probe: dict) -> tuple:
    return tuple(sorted((str(key), _freeze_eval_value(value)) for key, value in probe.items()))


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

    candidate_key_order = (
        "cx",
        "cy",
        "r",
        "arm_x1",
        "arm_y1",
        "arm_x2",
        "arm_y2",
        "arm_stroke",
        "stem_x",
        "stem_top",
        "stem_bottom",
        "stem_width",
        "text_x",
        "text_y",
        "text_scale",
    )

    def _key_applicable(key: str) -> bool:
        if key.startswith("arm_"):
            return bool(params.get("arm_enabled", False))
        if key.startswith("stem_"):
            return bool(params.get("stem_enabled", False))
        if key.startswith("text_"):
            return bool(params.get("draw_text", True))
        return True

    active_keys: list[str] = []
    for key in candidate_key_order:
        if key not in bounds or not hasattr(vector, key):
            continue
        if not _key_applicable(key):
            continue
        value = getattr(vector, key)
        if value is None:
            continue
        _low, _high, locked, _source = bounds[key]
        if locked:
            continue
        active_keys.append(key)

    active_key_set = set(active_keys)

    min_active_keys = 2
    search_mode = "voll" if len(active_keys) >= 4 else "reduziert"
    if len(active_keys) < min_active_keys:
        logs.append(
            "global-search: übersprungen "
            f"(zu wenige aktive Parameter; benötigt >={min_active_keys}, aktiv={len(active_keys)})"
        )
        return False

    effective_rounds = max(1, int(rounds))
    effective_samples_per_round = max(4, int(samples_per_round))
    if len(active_keys) <= 5:
        # For the current badge families we rarely need broad high-cost global
        # exploration in low-dimensional spaces. Use a tighter schedule to keep
        # validation responsive without disabling global search entirely.
        effective_rounds = min(effective_rounds, 2)
        effective_samples_per_round = min(effective_samples_per_round, 8)

    logs.append(
        "global-search: konfiguration "
        f"(modus={search_mode}, aktive_parameter={len(active_keys)}, rounds={effective_rounds}, "
        f"samples={effective_samples_per_round}, keys={','.join(active_keys)})"
    )
    eval_cache: dict[tuple, float] = {}
    eval_requests = 0
    eval_hits = 0

    def log_eval_telemetry():
        cache_hit_rate = (eval_hits / eval_requests) if eval_requests else 0.0
        logs.append(
            "global-search: evaluate-telemetrie "
            f"(requests={eval_requests}, cache_hits={eval_hits}, hit_rate={cache_hit_rate:.3f}, "
            f"render_aufrufe={eval_requests - eval_hits})"
        )

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
        nonlocal eval_hits, eval_requests
        eval_requests += 1
        probe = candidate.apply_to_params(params)
        if probe.get("arm_enabled"):
            reanchor_arm_to_circle_edge_fn(probe, float(probe.get("r", 0.0)))
        if probe.get("stem_enabled"):
            if "stem_top" not in active_key_set:
                probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe.get("r", 0.0))
            if bool(probe.get("lock_stem_center_to_circle", False)):
                stem_w = float(probe.get("stem_width", 1.0))
                probe["stem_x"] = snap_half_fn(
                    max(0.0, min(float(w) - stem_w, float(probe.get("cx", 0.0)) - (stem_w / 2.0)))
                )
        cache_key = _probe_cache_key(probe)
        cross_round_key = (id(img_orig), cache_key)
        cross_round_cached = _CROSS_ROUND_EVAL_CACHE.get(cross_round_key)
        if cross_round_cached is not None:
            eval_hits += 1
            _CROSS_ROUND_EVAL_CACHE.move_to_end(cross_round_key)
            eval_cache[cache_key] = cross_round_cached
            return cross_round_cached
        cached = eval_cache.get(cache_key)
        if cached is not None:
            eval_hits += 1
            return cached
        err = float(full_badge_error_for_params_fn(img_orig, probe))
        eval_cache[cache_key] = err
        _CROSS_ROUND_EVAL_CACHE[cross_round_key] = err
        _CROSS_ROUND_EVAL_CACHE.move_to_end(cross_round_key)
        if len(_CROSS_ROUND_EVAL_CACHE) > _CROSS_ROUND_EVAL_CACHE_MAX:
            _CROSS_ROUND_EVAL_CACHE.popitem(last=False)
        return err

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
        no_improvement_rounds = 0
        logs.append(
            "global-search: gestartet "
            f"(modus={search_mode}, aktive_parameter={','.join(active_keys)}, "
            f"samples_pro_runde={effective_samples_per_round}, start_err={best_err:.3f})"
        )
        logs.append(
            f"global-search: near-optimum-definition (err <= best_err + epsilon, epsilon=max({near_optimum_eps_floor:.2f}, best_err*{near_optimum_eps_rel:.2f}))"
        )

        for round_idx in range(effective_rounds):
            round_entry_best_err = best_err
            accepted = 0
            finite_round = [(best, best_err)]
            for _ in range(effective_samples_per_round):
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
            plateau_spans: dict[str, float] = {}
            if plateau:
                span_values: list[float] = []
                for key in active_keys:
                    key_values = [float(getattr(cand, key)) for cand, _err in plateau]
                    key_span = max(key_values) - min(key_values)
                    plateau_spans[key] = key_span
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
                    best_before = best_err
                    best = representative
                    best_err = representative_err
                    if best_err + 0.01 < best_before:
                        improved = True
                        no_improvement_rounds = 0
            elif representative_err + 0.01 < best_err:
                best = representative
                best_err = representative_err
                improved = True
                no_improvement_rounds = 0

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

            round_had_relevant_improvement = best_err + 0.01 < round_entry_best_err
            if (not round_had_relevant_improvement) and accepted == 0:
                no_improvement_rounds += 1
            else:
                no_improvement_rounds = 0

            for key in active_keys:
                local_floor = 0.12
                if key in plateau_spans:
                    local_floor = max(local_floor, float(plateau_spans[key]) * 0.35)
                if key in plateau_spans:
                    planned_span = (spans[key] * 0.72) + (float(plateau_spans[key]) * 0.40)
                else:
                    planned_span = spans[key] * 0.78
                spans[key] = max(local_floor, planned_span)
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
            should_stop_early = (
                round_idx >= 2
                and no_improvement_rounds >= 2
                and len(plateau) >= max(3, len(active_keys))
                and mean_span <= 0.40
            )
            if should_stop_early:
                logs.append(
                    "global-search: frühabbruch "
                    f"(runde={round_idx + 1}, grund=stabiles_plateau_ohne_relevante_verbesserung, "
                    f"no_improvement_rounds={no_improvement_rounds}, mean_span={mean_span:.3f})"
                )
                break
        return best, best_err, improved

    def runDeterministicTrack():
        best = start_vector
        best_err = start_err
        improved = False
        rounded_keys = {"cx", "cy", "r", "stem_x", "stem_width", "text_x", "text_y"}
        min_step_for_key = {key: (0.5 if key in rounded_keys else 0.10) for key in active_keys}
        step_sizes = {
            key: max(min_step_for_key[key], float(bounds[key][1] - bounds[key][0]) * 0.18)
            for key in active_keys
        }
        max_bisection_iters = 3
        logs.append(
            "global-search: deterministischer track gestartet "
            f"(modus={search_mode}, seed={int(seed)}, schritte={max(2, effective_rounds)}, start_err={best_err:.3f})"
        )
        for pass_idx in range(max(2, effective_rounds)):
            pass_improved = 0
            for key in active_keys:
                local_step = step_sizes[key]
                if key in rounded_keys:
                    local_step = max(0.5, round(local_step * 2.0) / 2.0)
                else:
                    local_step = max(0.10, local_step)

                key_improved = False
                bisection_iters = 0
                while bisection_iters < max_bisection_iters and local_step >= min_step_for_key[key] - 1e-9:
                    candidates = []
                    for direction in (-1.0, 1.0):
                        cand_data = dataclasses.asdict(best)
                        cand_data[key] = float(cand_data[key]) + (direction * local_step)
                        cand = clampVector(global_parameter_vector_cls(**cand_data))
                        cand_err = evalVector(cand)
                        if math.isfinite(cand_err):
                            candidates.append((cand, cand_err, direction))
                    if not candidates:
                        break

                    cand_best, cand_best_err, _best_dir = min(candidates, key=lambda item: item[1])
                    if cand_best_err + 0.01 < best_err:
                        best = cand_best
                        best_err = cand_best_err
                        improved = True
                        key_improved = True
                        pass_improved += 1
                        # Continue from improved point with same step before shrinking.
                        bisection_iters += 1
                        continue

                    if local_step <= min_step_for_key[key] + 1e-9:
                        break
                    local_step = max(min_step_for_key[key], local_step * 0.5)
                    bisection_iters += 1

                if not key_improved:
                    logs.append(
                        "global-search: intervallhalbierung "
                        f"(pass={pass_idx + 1}, key={key}, final_step={local_step:.3f}, iters={bisection_iters})"
                    )
                step_sizes[key] = max(min_step_for_key[key], local_step * (0.75 if key_improved else 0.90))

            logs.append(
                "global-search: deterministischer track "
                f"(pass={pass_idx + 1}, verbesserungen={pass_improved}, best_err={best_err:.3f})"
            )
            if pass_improved == 0 and pass_idx >= 1:
                break
        return best, best_err, improved


    stochastic_best, stochastic_err, stochastic_improved = runStochasticTrack()
    configured_rounds = max(1, int(rounds))
    skip_deterministic_track = bool(
        stochastic_improved and (start_err - stochastic_err) >= 0.10 and configured_rounds >= 3
    )
    if skip_deterministic_track:
        deterministic_best, deterministic_err, deterministic_improved = stochastic_best, float("inf"), False
        logs.append(
            "global-search: deterministischer track übersprungen "
            f"(grund=stochastic-konvergiert, delta_err={start_err - stochastic_err:.3f})"
        )
    else:
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
        log_eval_telemetry()
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
    if params.get("stem_enabled") and "stem_top" not in active_key_set:
        params["stem_top"] = float(params.get("cy", 0.0)) + float(params.get("r", 0.0))
    log_global_parameter_vector_fn(logs, params, w, h, label=f"global-search: final ({winner_name})")
    logs.append(
        "global-search: übernommen "
        f"(best_err={winner_err:.3f}, track={winner_name}, verbessert={', '.join(delta_labels) if delta_labels else 'keine sichtbare delta-liste'})"
    )
    log_eval_telemetry()
    return True


def fullBadgeErrorForParamsImpl(
    img_orig,
    params: dict,
    *,
    fit_to_original_size_fn,
    render_svg_to_numpy_fn,
    generate_badge_svg_fn,
    calculate_error_fn,
) -> float:
    """Evaluate full-image error for an already prepared badge parameter dict."""
    h, w = img_orig.shape[:2]
    render = fit_to_original_size_fn(
        img_orig,
        render_svg_to_numpy_fn(generate_badge_svg_fn(w, h, params), w, h),
    )
    if render is None:
        return float("inf")
    return float(calculate_error_fn(img_orig, render))
