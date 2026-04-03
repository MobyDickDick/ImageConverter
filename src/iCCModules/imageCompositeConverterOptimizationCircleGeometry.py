"""Circle pose/anchor optimization helper functions extracted from the monolith."""

from __future__ import annotations


def reanchorArmToCircleEdgeImpl(params: dict, radius: float) -> None:
    """Keep arm orientation but snap the circle-side endpoint to the new radius."""
    if not params.get("arm_enabled"):
        return
    if not all(k in params for k in ("arm_x1", "arm_y1", "arm_x2", "arm_y2", "cx", "cy")):
        return

    cx = float(params.get("cx", 0.0))
    cy = float(params.get("cy", 0.0))
    x1 = float(params.get("arm_x1", cx))
    y1 = float(params.get("arm_y1", cy))
    x2 = float(params.get("arm_x2", cx))
    y2 = float(params.get("arm_y2", cy))
    arm_stroke = float(max(0.0, params.get("arm_stroke", 0.0)))
    attach_offset = arm_stroke / 2.0

    is_horizontal = abs(x2 - x1) >= abs(y2 - y1)
    if is_horizontal:
        params["arm_y1"] = cy
        params["arm_y2"] = cy
        p1_dist = abs(x1 - cx)
        p2_dist = abs(x2 - cx)
        if p2_dist <= p1_dist:
            params["arm_x2"] = (cx - radius - attach_offset) if x1 <= cx else (cx + radius + attach_offset)
        else:
            params["arm_x1"] = (cx - radius - attach_offset) if x2 <= cx else (cx + radius + attach_offset)
    else:
        params["arm_x1"] = cx
        params["arm_x2"] = cx
        p1_dist = abs(y1 - cy)
        p2_dist = abs(y2 - cy)
        if p2_dist <= p1_dist:
            params["arm_y2"] = (cy - radius - attach_offset) if y1 <= cy else (cy + radius + attach_offset)
        else:
            params["arm_y1"] = (cy - radius - attach_offset) if y2 <= cy else (cy + radius + attach_offset)


def elementErrorForCirclePoseImpl(
    img_orig,
    params: dict,
    *,
    cx_value: float,
    cy_value: float,
    radius_value: float,
    snap_half_fn,
    clip_scalar_fn,
    clamp_circle_inside_canvas_fn,
    reanchor_arm_to_circle_edge_fn,
    generate_badge_svg_fn,
    element_only_params_fn,
    fit_to_original_size_fn,
    render_svg_to_numpy_fn,
    extract_badge_element_mask_fn,
    element_match_error_fn,
) -> float:
    h, w = img_orig.shape[:2]
    if not params.get("circle_enabled", True):
        return float("inf")

    probe = dict(params)
    max_r = max(1.0, (float(min(w, h)) * 0.48))
    probe["cx"] = snap_half_fn(float(clip_scalar_fn(cx_value, 0.0, float(w - 1))))
    probe["cy"] = snap_half_fn(float(clip_scalar_fn(cy_value, 0.0, float(h - 1))))
    min_r = float(max(1.0, probe.get("min_circle_radius", 1.0)))
    probe["r"] = snap_half_fn(float(clip_scalar_fn(radius_value, min_r, max_r)))
    probe = clamp_circle_inside_canvas_fn(probe, w, h)

    if probe.get("arm_enabled"):
        reanchor_arm_to_circle_edge_fn(probe, float(probe["r"]))

    if probe.get("stem_enabled"):
        probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

    elem_svg = generate_badge_svg_fn(w, h, element_only_params_fn(probe, "circle"))
    elem_render = fit_to_original_size_fn(img_orig, render_svg_to_numpy_fn(elem_svg, w, h))
    if elem_render is None:
        return float("inf")

    mask_orig = extract_badge_element_mask_fn(img_orig, params, "circle")
    if mask_orig is None:
        return float("inf")
    mask_svg = extract_badge_element_mask_fn(elem_render, probe, "circle")
    if mask_svg is None:
        return float("inf")

    return element_match_error_fn(
        img_orig,
        elem_render,
        probe,
        "circle",
        mask_orig=mask_orig,
        mask_svg=mask_svg,
    )
