"""Global optimization vector helper functions for imageCompositeConverter."""

from __future__ import annotations


def circleBoundsImpl(
    params: dict,
    w: int,
    h: int,
    *,
    max_circle_radius_inside_canvas_fn,
) -> tuple[float, float, float, float, float, float]:
    min_r = float(max(1.0, params.get("min_circle_radius", 1.0)))
    if "circle_radius_lower_bound_px" in params:
        min_r = float(max(min_r, float(params.get("circle_radius_lower_bound_px", min_r))))
    allow_overflow = bool(params.get("allow_circle_overflow", False))
    max_r = max(min_r, float(min(w, h)) * 0.48)
    cx = float(params.get("cx", float(w) / 2.0))
    cy = float(params.get("cy", float(h) / 2.0))
    stroke = float(params.get("stroke_circle", 0.0))
    if allow_overflow:
        max_r = max(max_r, float(max(w, h)) * 1.25, min_r + 0.5)
    else:
        max_r = min(max_r, max_circle_radius_inside_canvas_fn(cx, cy, w, h, stroke))
    if "max_circle_radius" in params:
        max_r = min(max_r, float(params.get("max_circle_radius", max_r)))
    return 0.0, float(w - 1), 0.0, float(h - 1), min_r, max_r


def globalParameterVectorBoundsImpl(
    params: dict,
    w: int,
    h: int,
    *,
    circle_bounds_fn,
) -> dict[str, tuple[float, float, bool, str]]:
    """Return central bounds/lock metadata for the shared optimization vector."""
    x_low, x_high, y_low, y_high, r_low, r_high = circle_bounds_fn(params, w, h)
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
        "arm_stroke": (
            1.0,
            max(1.0, min(float(min(w, h)) * 0.20, float(params.get("r", min(w, h))) * 0.9)),
            bool(params.get("lock_stroke_widths", False)),
            "semantic",
        ),
        "stem_x": (0.0, max_x, bool(params.get("lock_stem", False)), "template"),
        "stem_top": (0.0, max_y, bool(params.get("lock_stem", False)), "template"),
        "stem_bottom": (0.0, max_y, bool(params.get("lock_stem", False)), "template"),
        "stem_width": (
            1.0,
            max(1.0, min(float(w) * 0.25, float(params.get("stem_width_max", float(w) * 0.25)))),
            bool(params.get("lock_stroke_widths", False)),
            "semantic",
        ),
        "text_x": (0.0, max_x, bool(params.get("lock_text_position", False)), "template"),
        "text_y": (0.0, max_y, bool(params.get("lock_text_position", False)), "template"),
        "text_scale": (text_scale_min, text_scale_max, bool(params.get("lock_text_scale", False)), "semantic"),
    }


def logGlobalParameterVectorImpl(
    logs: list[str],
    params: dict,
    w: int,
    h: int,
    *,
    label: str,
    global_parameter_vector_cls,
    global_parameter_vector_bounds_fn,
) -> None:
    vector = global_parameter_vector_cls.fromParams(params)
    bounds = global_parameter_vector_bounds_fn(params, w, h)

    def _fmtValue(value: float | None) -> str:
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
            f"{name}={_fmtValue(value)} [{low:.2f},{high:.2f}] lock={'ja' if locked else 'nein'} src={source}"
        )
    logs.append(f"{label}: global_vector " + "; ".join(entries))
