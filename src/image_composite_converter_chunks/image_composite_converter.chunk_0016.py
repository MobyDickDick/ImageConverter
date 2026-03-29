        if not Action._is_circle_with_text(params):
            return float(radius)
        # Keep a tiny strict margin so the optimized radius remains strictly below w/2.
        width_cap = (float(w) / 2.0) - 1e-3
        return float(min(float(radius), width_cap))

    @staticmethod
    def _apply_circle_text_radius_floor(params: dict, radius: float) -> float:
        """Enforce CircleWithText lower bound: radius must exceed half text width."""
        if not Action._is_circle_with_text(params):
            return float(radius)
        x1, _y1, x2, _y2 = Action._text_bbox(params)
        text_width = max(0.0, float(x2) - float(x1))
        if text_width <= 0.0:
            return float(radius)
        # Keep strict inequality: radius > (text_width / 2).
        lower_bound = (text_width / 2.0) + 1e-3
        return float(max(float(radius), lower_bound))

    @staticmethod
    def _clamp_circle_inside_canvas(params: dict, w: int, h: int) -> dict:
        """Clamp circle center/radius so no part of the ring exceeds the viewport."""
        p = dict(params)
        if not p.get("circle_enabled", True):
            return p
        if "cx" not in p or "cy" not in p or "r" not in p:
            return p

        cx = float(max(0.0, min(float(w), float(p.get("cx", 0.0)))))
        cy = float(max(0.0, min(float(h), float(p.get("cy", 0.0)))))
        stroke = float(p.get("stroke_circle", 0.0))
        max_r = Action._max_circle_radius_inside_canvas(cx, cy, w, h, stroke)
        max_r = Action._apply_circle_text_width_constraint(p, max_r, w)
        min_r = float(
            max(
                1.0,
                float(p.get("min_circle_radius", 1.0)),
                float(p.get("circle_radius_lower_bound_px", 1.0)),
            )
        )
        min_r = Action._apply_circle_text_radius_floor(p, min_r)
        if not bool(p.get("allow_circle_overflow", False)):
            min_r = min(min_r, max_r)

        p["cx"] = cx
        p["cy"] = cy
        if bool(p.get("allow_circle_overflow", False)):
            p["r"] = float(max(min_r, float(p.get("r", min_r))))
        else:
            p["r"] = float(max(min_r, min(max_r, float(p.get("r", min_r)))))
        return p

    @staticmethod
    def apply_redraw_variation(params: dict, w: int, h: int) -> tuple[dict, list[str]]:
        """Apply a slight per-run redraw jitter and describe it for the log."""
        p = copy.deepcopy(params)
        variation_logs: list[str] = []
        if w <= 0 or h <= 0:
            return p, variation_logs

        seed = (
            int(Action.STOCHASTIC_RUN_SEED) * 1009
            + int(Action.STOCHASTIC_SEED_OFFSET) * 101
            + int(time.time_ns() % 1_000_000_007)
        )
        rng = Action._make_rng(seed)

        def _uniform(delta: float) -> float:
            return float(rng.uniform(-abs(float(delta)), abs(float(delta))))

        jitter_entries: list[str] = []

        def _apply_numeric_jitter(key: str, delta: float, *, minimum: float | None = None, maximum: float | None = None) -> None:
            if key not in p:
                return
            try:
                old_float = float(p.get(key))
            except (TypeError, ValueError):
                return
            new_value = old_float + _uniform(delta)
            if minimum is not None:
                new_value = max(float(minimum), new_value)
            if maximum is not None:
                new_value = min(float(maximum), new_value)
            p[key] = float(new_value)
            jitter_entries.append(f"{key}:{old_float:.3f}->{new_value:.3f}")

        _apply_numeric_jitter("cx", max(0.15, float(w) * 0.01), minimum=0.0, maximum=float(w))
        _apply_numeric_jitter("cy", max(0.15, float(h) * 0.01), minimum=0.0, maximum=float(h))
        _apply_numeric_jitter("r", max(0.10, float(min(w, h)) * 0.008), minimum=1.0)
        _apply_numeric_jitter("stroke_circle", 0.12, minimum=0.4)
        _apply_numeric_jitter("arm_len", max(0.12, float(w) * 0.012), minimum=0.5, maximum=float(max(w, h)))
        _apply_numeric_jitter("arm_stroke", 0.12, minimum=0.4)
        _apply_numeric_jitter("stem_height", max(0.12, float(h) * 0.012), minimum=0.5, maximum=float(max(w, h)))
        _apply_numeric_jitter("stem_width", 0.12, minimum=0.4, maximum=float(max(1, w)))
        _apply_numeric_jitter("text_scale", 0.03, minimum=0.35, maximum=4.0)
        _apply_numeric_jitter("text_x", max(0.10, float(w) * 0.01), minimum=0.0, maximum=float(w))
        _apply_numeric_jitter("text_y", max(0.10, float(h) * 0.01), minimum=0.0, maximum=float(h))
        _apply_numeric_jitter("co2_dx", 0.08)
        _apply_numeric_jitter("co2_dy", 0.08)
