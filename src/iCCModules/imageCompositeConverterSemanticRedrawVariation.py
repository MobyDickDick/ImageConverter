from __future__ import annotations

import copy


def applyRedrawVariationImpl(
    params: dict,
    w: int,
    h: int,
    *,
    stochastic_run_seed: int,
    stochastic_seed_offset: int,
    time_ns_fn,
    make_rng_fn,
    clamp_circle_inside_canvas_fn,
    reanchor_arm_to_circle_edge_fn,
) -> tuple[dict, list[str]]:
    """Apply a slight per-run redraw jitter and describe it for the log."""
    p = copy.deepcopy(params)
    variation_logs: list[str] = []
    if w <= 0 or h <= 0:
        return p, variation_logs

    seed = (
        int(stochastic_run_seed) * 1009
        + int(stochastic_seed_offset) * 101
        + int(time_ns_fn() % 1_000_000_007)
    )
    rng = make_rng_fn(seed)

    def _uniform(delta: float) -> float:
        return float(rng.uniform(-abs(float(delta)), abs(float(delta))))

    jitter_entries: list[str] = []

    def _applyNumericJitter(key: str, delta: float, *, minimum: float | None = None, maximum: float | None = None) -> None:
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

    _applyNumericJitter("cx", max(0.15, float(w) * 0.01), minimum=0.0, maximum=float(w))
    _applyNumericJitter("cy", max(0.15, float(h) * 0.01), minimum=0.0, maximum=float(h))
    _applyNumericJitter("r", max(0.10, float(min(w, h)) * 0.008), minimum=1.0)
    _applyNumericJitter("stroke_circle", 0.12, minimum=0.4)
    _applyNumericJitter("arm_len", max(0.12, float(w) * 0.012), minimum=0.5, maximum=float(max(w, h)))
    _applyNumericJitter("arm_stroke", 0.12, minimum=0.4)
    _applyNumericJitter("stem_height", max(0.12, float(h) * 0.012), minimum=0.5, maximum=float(max(w, h)))
    _applyNumericJitter("stem_width", 0.12, minimum=0.4, maximum=float(max(1, w)))
    _applyNumericJitter("text_scale", 0.03, minimum=0.35, maximum=4.0)
    _applyNumericJitter("text_x", max(0.10, float(w) * 0.01), minimum=0.0, maximum=float(w))
    _applyNumericJitter("text_y", max(0.10, float(h) * 0.01), minimum=0.0, maximum=float(h))
    _applyNumericJitter("co2_dx", 0.08)
    _applyNumericJitter("co2_dy", 0.08)
    _applyNumericJitter("voc_scale", 0.03, minimum=0.35, maximum=4.0)

    p = clamp_circle_inside_canvas_fn(p, w, h)
    if p.get("arm_enabled"):
        reanchor_arm_to_circle_edge_fn(p, float(p.get("r", 1.0)))
    if p.get("stem_enabled") and "cy" in p and "r" in p:
        p["stem_top"] = float(p.get("cy", 0.0)) + float(p.get("r", 0.0))

    if jitter_entries:
        variation_logs.append(
            "redraw_variation: seed="
            f"{seed} changed_params=" + " | ".join(jitter_entries)
        )
    return p, variation_logs
