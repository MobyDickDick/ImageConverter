            or (not lock_cy and (abs(best[1] - y_low) <= 0.01 or abs(best[1] - y_high) <= 0.01))
            or abs(best[2] - r_low) <= 0.01
            or abs(best[2] - r_high) <= 0.01
        )
        flat_hint = flat_plateau_hits >= 2
        logs.append(
            "circle: Adaptive-Domain-Suche übernommen "
            f"(cx={best[0]:.3f}, cy={best[1]:.3f}, r={best[2]:.3f}, err={best_err:.3f}, "
            f"rand_optimum={'ja' if boundary_hit else 'nein'}, flaches_optimum={'ja' if flat_hint else 'nein'})"
        )
        return True

    @staticmethod
    def _full_badge_error_for_params(img_orig: np.ndarray, params: dict) -> float:
        """Evaluate full-image error for an already prepared badge parameter dict."""
        h, w = img_orig.shape[:2]
        render = Action._fit_to_original_size(
            img_orig,
            Action.render_svg_to_numpy(Action.generate_badge_svg(w, h, params), w, h),
        )
        if render is None:
            return float("inf")
        return float(Action.calculate_error(img_orig, render))

    @staticmethod
    def _optimize_global_parameter_vector_sampling(
        img_orig: np.ndarray,
        params: dict,
        logs: list[str],
        *,
        rounds: int = 3,
        samples_per_round: int = 16,
    ) -> bool:
        """Global multi-parameter baseline search over the shared vector."""
        if not bool(params.get("enable_global_search_mode", False)):
            return False

        near_optimum_eps_floor = 0.06
        near_optimum_eps_rel = 0.02

        h, w = img_orig.shape[:2]
        bounds = Action._global_parameter_vector_bounds(params, w, h)
        vector = GlobalParameterVector.from_params(params)

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
            logs.append(
                "global-search: übersprungen (zu wenige aktive Parameter; benötigt >=4)"
            )
            return False

        def clamp_vector(candidate: GlobalParameterVector) -> GlobalParameterVector:
            data = dataclasses.asdict(candidate)
            for key in active_keys:
                low, high, _locked, _source = bounds[key]
                current_value = float(data[key])
                clipped = float(Action._clip_scalar(current_value, low, high))
                if key in {"cx", "cy", "r", "stem_x", "stem_width", "text_x", "text_y"}:
                    clipped = float(Action._snap_half(clipped))
                data[key] = clipped
            return GlobalParameterVector(**data)

        def eval_vector(candidate: GlobalParameterVector) -> float:
            probe = candidate.apply_to_params(params)
            if probe.get("arm_enabled"):
                Action._reanchor_arm_to_circle_edge(probe, float(probe.get("r", 0.0)))
            if probe.get("stem_enabled"):
                probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe.get("r", 0.0))
                if bool(probe.get("lock_stem_center_to_circle", False)):
                    stem_w = float(probe.get("stem_width", 1.0))
                    probe["stem_x"] = Action._snap_half(
                        max(0.0, min(float(w) - stem_w, float(probe.get("cx", 0.0)) - (stem_w / 2.0)))
                    )
            return Action._full_badge_error_for_params(img_orig, probe)

        def within_hard_bounds(candidate: GlobalParameterVector) -> tuple[bool, str]:
            for key in active_keys:
                low, high, _locked, _source = bounds[key]
                value = float(getattr(candidate, key))
                if value < low - 1e-6 or value > high + 1e-6:
                    return False, f"{key}={value:.3f} außerhalb [{low:.3f}, {high:.3f}]"
            return True, "ok"

        rng = Action._make_rng(4099 + int(Action.STOCHASTIC_RUN_SEED) + int(Action.STOCHASTIC_SEED_OFFSET))
        best = clamp_vector(vector)
        best_err = eval_vector(best)
        if not math.isfinite(best_err):
            return False
        improved = False

        spans = {key: max(0.25, float(bounds[key][1] - bounds[key][0]) * 0.20) for key in active_keys}
