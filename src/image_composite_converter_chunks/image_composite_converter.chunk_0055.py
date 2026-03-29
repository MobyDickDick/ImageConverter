    @staticmethod
    def _global_parameter_vector_bounds(params: dict, w: int, h: int) -> dict[str, tuple[float, float, bool, str]]:
        """Return central bounds/lock metadata for the shared optimization vector."""
        x_low, x_high, y_low, y_high, r_low, r_high = Action._circle_bounds(params, w, h)
        max_x = float(max(0, w - 1))
        max_y = float(max(0, h - 1))
        text_scale = float(params.get("text_scale", 1.0))
        text_scale_min = float(params.get("text_scale_min", max(0.2, text_scale * 0.5)))
        text_scale_max = float(params.get("text_scale_max", max(text_scale_min, text_scale * 1.8)))
        return {
            "cx": (x_low, x_high, bool(params.get("lock_circle_cx", False)), "canvas"),
            "cy": (y_low, y_high, bool(params.get("lock_circle_cy", False)), "canvas"),
            "r": (r_low, r_high, False, "template/semantic"),
            "arm_x1": (0.0, max_x, bool(params.get("lock_arm", False)), "canvas"),
            "arm_y1": (0.0, max_y, bool(params.get("lock_arm", False)), "canvas"),
            "arm_x2": (0.0, max_x, bool(params.get("lock_arm", False)), "template"),
            "arm_y2": (0.0, max_y, bool(params.get("lock_arm", False)), "template"),
            "arm_stroke": (1.0, max(1.0, min(float(min(w, h)) * 0.20, float(params.get("r", min(w, h))) * 0.9)), bool(params.get("lock_stroke_widths", False)), "semantic"),
            "stem_x": (0.0, max_x, bool(params.get("lock_stem", False)), "template"),
            "stem_top": (0.0, max_y, bool(params.get("lock_stem", False)), "template"),
            "stem_bottom": (0.0, max_y, bool(params.get("lock_stem", False)), "template"),
            "stem_width": (1.0, max(1.0, min(float(w) * 0.25, float(params.get("stem_width_max", float(w) * 0.25)))), bool(params.get("lock_stroke_widths", False)), "semantic"),
            "text_x": (0.0, max_x, bool(params.get("lock_text_position", False)), "template"),
            "text_y": (0.0, max_y, bool(params.get("lock_text_position", False)), "template"),
            "text_scale": (text_scale_min, text_scale_max, bool(params.get("lock_text_scale", False)), "semantic"),
        }

    @staticmethod
    def _log_global_parameter_vector(logs: list[str], params: dict, w: int, h: int, *, label: str) -> None:
        vector = GlobalParameterVector.from_params(params)
        bounds = Action._global_parameter_vector_bounds(params, w, h)

        def _fmt_value(value: float | None) -> str:
            return "-" if value is None else f"{float(value):.3f}"

        entries = []
        for name in (
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
        ):
            low, high, locked, source = bounds[name]
            value = getattr(vector, name)
            entries.append(
                f"{name}={_fmt_value(value)} [{low:.2f},{high:.2f}] lock={'ja' if locked else 'nein'} src={source}"
            )
        logs.append(f"{label}: global_vector " + "; ".join(entries))

    @staticmethod
    def _stochastic_survivor_scalar(
        current_value: float,
        low: float,
        high: float,
        evaluate,
        *,
        snap,
        seed: int,
        iterations: int = 20,
    ) -> tuple[float, float, bool]:
        """Random 3-candidate survivor search for a scalar parameter."""
        cur = float(snap(float(Action._clip_scalar(current_value, low, high))))
        best_value = cur
        best_err = float(evaluate(best_value))
        if not math.isfinite(best_err):
            return best_value, best_err, False

        rng = Action._make_rng(int(seed) + int(Action.STOCHASTIC_SEED_OFFSET))
        span = max(0.5, abs(high - low) * 0.22)
        improved = False
        stable_rounds = 0

        for _ in range(max(1, iterations)):
            candidates = [best_value]
            for _j in range(2):
                sample = float(Action._clip_scalar(rng.normal(best_value, span), low, high))
                candidates.append(float(snap(sample)))

            scored: list[tuple[float, float]] = []
            for cand in candidates:
                err = float(evaluate(cand))
                if math.isfinite(err):
                    scored.append((cand, err))
            if not scored:
                continue
            scored.sort(key=lambda pair: pair[1])
            cand_best, cand_err = scored[0]
            if cand_err + 0.05 < best_err:
                best_value, best_err = cand_best, cand_err
