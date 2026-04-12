"""Extracted quantization/symmetry helpers for imageCompositeConverter."""

from __future__ import annotations


def enforceCircleConnectorSymmetryImpl(params: dict, w: int, h: int) -> dict:
    """Keep circle+connector "lollipop" geometry centered around the connector axis."""
    p = dict(params)
    if not p.get("circle_enabled", True):
        return p
    if "cx" not in p or "cy" not in p or "r" not in p:
        return p

    cx = float(p["cx"])
    cy = float(p["cy"])
    r = float(p["r"])

    if p.get("stem_enabled") and "stem_width" in p:
        p["stem_x"] = cx - (float(p["stem_width"]) / 2.0)

    if p.get("arm_enabled") and all(k in p for k in ("arm_x1", "arm_y1", "arm_x2", "arm_y2")):
        x1 = float(p["arm_x1"])
        y1 = float(p["arm_y1"])
        x2 = float(p["arm_x2"])
        y2 = float(p["arm_y2"])

        vertical = abs(x2 - x1) <= abs(y2 - y1)
        if str(p.get("head_style", "")).lower() == "ac0223_triple_valve" and vertical:
            # AC0223 requires a short vertical connector between the circle top
            # and the valve hub. Keep it centered and clamp it to the canvas
            # so iterative searches cannot stretch it to y=0.
            p["arm_x1"] = cx
            p["arm_x2"] = cx
            scale_y = (float(h) / 75.0) if h > 0 else 1.0
            hub_y = float(p.get("head_hub_cy", p.get("arm_y2", 25.153 * scale_y)))
            hub_y = max(0.0, min(float(h), hub_y))
            if str(p.get("ac0223_handle_style", "")).lower() == "square_diagonals":
                circle_top = 41.518044 * scale_y
            else:
                circle_top = cy - r
            p["arm_y2"] = hub_y
            p["arm_y1"] = max(hub_y, min(float(h), circle_top))
            p["head_hub_cy"] = hub_y
        elif vertical:
            p["arm_x1"] = cx
            p["arm_x2"] = cx
            end_is_p2 = abs(y2 - cy) <= abs(y1 - cy)
            if end_is_p2:
                p["arm_y2"] = cy - r if y1 <= cy else cy + r
            else:
                p["arm_y1"] = cy - r if y2 <= cy else cy + r
        else:
            p["arm_y1"] = cy
            p["arm_y2"] = cy
            end_is_p2 = abs(x2 - cx) <= abs(x1 - cx)
            if end_is_p2:
                p["arm_x2"] = cx - r if x1 <= cx else cx + r
            else:
                p["arm_x1"] = cx - r if x2 <= cx else cx + r

    if "stem_x" in p and "stem_width" in p:
        p["stem_x"] = max(0.0, min(float(w) - float(p["stem_width"]), float(p["stem_x"])))
    for key in ("arm_x1", "arm_x2"):
        if key in p:
            p[key] = max(0.0, min(float(w), float(p[key])))
    for key in ("arm_y1", "arm_y2"):
        if key in p:
            p[key] = max(0.0, min(float(h), float(p[key])))
    return p


def quantizeBadgeParamsImpl(
    params: dict,
    w: int,
    h: int,
    *,
    snap_half_fn,
    snap_int_px_fn,
    enforce_circle_connector_symmetry_fn,
    clamp_circle_inside_canvas_fn,
    max_circle_radius_inside_canvas_fn,
) -> dict:
    """Quantize geometry for bitmap-like sources.

    - Coordinates/lengths use 0.5px steps.
    - Line widths use integer pixel steps.
    """
    p = dict(params)
    raw_circle_radius = float(p["r"]) if p.get("circle_enabled", True) and "r" in p else None

    half_keys = (
        "cx",
        "cy",
        "r",
        "stem_x",
        "stem_top",
        "stem_bottom",
        "arm_x1",
        "arm_y1",
        "arm_x2",
        "arm_y2",
        "tx",
        "ty",
        "co2_dy",
    )
    for key in half_keys:
        if key in p:
            p[key] = snap_half_fn(float(p[key]))

    int_width_keys = ("stroke_circle", "arm_stroke", "stem_width")
    for key in int_width_keys:
        if key in p:
            p[key] = snap_int_px_fn(float(p[key]), minimum=1.0)

    if "stem_width_max" in p:
        p["stem_width_max"] = max(1.0, snap_half_fn(float(p["stem_width_max"])))

    if p.get("stem_enabled") and "cx" in p and "stem_width" in p:
        p["stem_x"] = snap_half_fn(float(p["cx"]) - (float(p["stem_width"]) / 2.0))

    if "stem_x" in p and "stem_width" in p:
        p["stem_x"] = max(0.0, min(float(w) - float(p["stem_width"]), float(p["stem_x"])))
    if "stem_top" in p:
        p["stem_top"] = max(0.0, min(float(h), float(p["stem_top"])))
    if "stem_bottom" in p:
        p["stem_bottom"] = max(0.0, min(float(h), float(p["stem_bottom"])))

    p = enforce_circle_connector_symmetry_fn(p, w, h)
    p = clamp_circle_inside_canvas_fn(p, w, h)

    if (
        raw_circle_radius is not None
        and "cx" in p
        and "cy" in p
        and "r" in p
    ):
        canvas_fit_r = float(
            max_circle_radius_inside_canvas_fn(
                float(p["cx"]),
                float(p["cy"]),
                w,
                h,
                float(p.get("stroke_circle", 0.0)),
            )
        )
        snapped_canvas_fit_r = float(snap_half_fn(canvas_fit_r))
        radius_gap_to_canvas = canvas_fit_r - raw_circle_radius
        if (
            snapped_canvas_fit_r > float(p["r"])
            and radius_gap_to_canvas >= 0.0
            and radius_gap_to_canvas <= 0.5
            and (canvas_fit_r - float(p["r"])) <= 0.5
        ):
            p["r"] = float(
                max(
                    float(p.get("min_circle_radius", 1.0)),
                    min(snapped_canvas_fit_r, canvas_fit_r),
                )
            )

    # Symmetry enforcement may reintroduce non-snapped values.
    for key in half_keys:
        if key in p:
            p[key] = snap_half_fn(float(p[key]))

    return p
