"""AC0811 semantic badge helper block extracted from imageCompositeConverter."""

from __future__ import annotations


def defaultEdgeAnchoredCircleGeometryImpl(
    w: int,
    h: int,
    *,
    anchor: str,
    radius_ratio: float = 0.43,
    stroke_divisor: float = 15.0,
    edge_clearance_ratio: float = 0.08,
    edge_clearance_stroke_factor: float = 0.75,
) -> dict[str, float]:
    """Return circle geometry for connector badges anchored near one canvas edge."""
    narrow = float(min(w, h))
    stroke_circle = max(0.9, narrow / stroke_divisor)
    r = narrow * radius_ratio
    cx = float(w) / 2.0
    cy = float(h) / 2.0
    edge_clearance = max(stroke_circle * edge_clearance_stroke_factor, narrow * edge_clearance_ratio)

    anchor_key = anchor.lower()
    if anchor_key == "top":
        cy = r + edge_clearance
    elif anchor_key == "bottom":
        cy = float(h) - (r + edge_clearance)
    elif anchor_key == "left":
        cx = r + edge_clearance
    elif anchor_key == "right":
        cx = float(w) - (r + edge_clearance)
    else:
        raise ValueError(f"Unsupported anchor: {anchor}")

    return {
        "cx": cx,
        "cy": cy,
        "r": r,
        "stroke_circle": stroke_circle,
    }


def defaultAc0811ParamsImpl(
    w: int,
    h: int,
    *,
    default_ac081x_shared,
    default_edge_anchored_circle_geometry,
    normalize_light_circle_colors,
    light_circle_stroke_gray: int,
    light_circle_fill_gray: int,
) -> dict:
    """AC0811 is vertically elongated: circle sits in the upper square area."""
    if w <= 0 or h <= 0:
        return default_ac081x_shared(w, h)

    circle = default_edge_anchored_circle_geometry(w, h, anchor="top")
    cx = float(circle["cx"])
    cy = float(circle["cy"])
    r = float(circle["r"])
    stroke_circle = float(circle["stroke_circle"])
    stem_width = max(1.0, float(w) * 0.10)
    stem_width_max = max(1.0, float(w) * 0.105)
    stem_len = max(2.0, float(h) - (cy + r))

    return normalize_light_circle_colors(
        {
            "cx": cx,
            "cy": cy,
            "r": r,
            "stroke_circle": stroke_circle,
            "stroke_gray": light_circle_stroke_gray,
            "fill_gray": light_circle_fill_gray,
            "draw_text": False,
            "stem_enabled": True,
            "stem_width": stem_width,
            "stem_width_max": stem_width_max,
            "stem_x": cx - (stem_width / 2.0),
            "stem_top": cy + r,
            "stem_bottom": min(float(h), (cy + r) + stem_len),
            "stem_gray": light_circle_stroke_gray,
        }
    )


def estimateUpperCircleFromForegroundImpl(
    img,
    defaults: dict,
    *,
    cv2_module,
    np_module,
    clip_scalar_fn,
) -> tuple[float, float, float] | None:
    """Estimate circle geometry from the upper symbol region."""
    gray = cv2_module.cvtColor(img, cv2_module.COLOR_BGR2GRAY)
    h, w = gray.shape
    if h <= 0 or w <= 0:
        return None

    _, fg = cv2_module.threshold(gray, 0, 255, cv2_module.THRESH_BINARY_INV + cv2_module.THRESH_OTSU)
    top_limit = int(round(min(float(h), float(defaults.get("cy", h / 2.0)) + float(defaults.get("r", w / 3.0)) * 1.15)))
    top_limit = max(3, min(h, top_limit))
    roi = fg[:top_limit, :]
    if roi.size == 0:
        return None

    contours, _ = cv2_module.findContours(roi, cv2_module.RETR_EXTERNAL, cv2_module.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    best = None
    for cnt in contours:
        area = float(cv2_module.contourArea(cnt))
        if area < 8.0:
            continue
        perimeter = float(cv2_module.arcLength(cnt, True))
        if perimeter <= 0.0:
            continue
        circularity = 4.0 * np_module.pi * area / max(1e-6, perimeter * perimeter)
        if circularity < 0.35:
            continue
        score = area * (0.5 + circularity)
        if best is None or score > best[0]:
            best = (score, cnt)

    if best is None:
        return None

    (_score, cnt) = best
    (cx, cy), r = cv2_module.minEnclosingCircle(cnt)
    min_r = max(2.0, float(w) * 0.24)
    max_r = min(float(w) * 0.52, float(top_limit) * 0.58)
    if max_r < min_r:
        max_r = min_r
    r = float(clip_scalar_fn(r, min_r, max_r))
    cx = float(clip_scalar_fn(cx, 0.0, float(w - 1)))
    cy = float(clip_scalar_fn(cy, 0.0, float(h - 1)))
    return cx, cy, r


def fitAc0811ParamsFromImageImpl(
    img,
    defaults: dict,
    *,
    fit_semantic_badge_from_image_fn,
    estimate_upper_circle_from_foreground_fn,
    clip_scalar_fn,
    normalize_light_circle_colors_fn,
    persist_connector_length_floor_fn,
) -> dict:
    """Fit AC0811 while keeping the vertical stem anchored to the lower edge."""
    params = fit_semantic_badge_from_image_fn(img, defaults)
    h, w = img.shape[:2]

    raw_stem_width = float(params.get("stem_width", defaults.get("stem_width", max(1.0, float(w) * 0.10))))
    cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
    cy = float(params.get("cy", defaults.get("cy", float(w) / 2.0)))
    r = float(params.get("r", defaults.get("r", float(w) * 0.4)))
    stroke_circle = float(params.get("stroke_circle", defaults.get("stroke_circle", max(0.9, float(w) / 15.0))))
    aspect_ratio = (float(h) / float(w)) if w > 0 else 1.0
    elongated_plain_badge = aspect_ratio >= 1.60 and not bool(params.get("draw_text", False))

    allow_upper_circle_estimate = str(params.get("text_mode", "")).lower() not in {"voc", "co2"}
    upper_circle = estimate_upper_circle_from_foreground_fn(img, defaults) if allow_upper_circle_estimate else None
    if upper_circle is not None:
        ecx, ecy, er = upper_circle
        trust = 0.85 if w <= 18 else 0.55
        cx = (cx * (1.0 - trust)) + (ecx * trust)
        cy = (cy * (1.0 - trust)) + (ecy * trust)
        r = (r * (1.0 - trust)) + (er * trust)
        params["cx"] = cx
        params["cy"] = cy
        params["r"] = r

    if w <= 18:
        default_cx = float(defaults.get("cx", float(w) / 2.0))
        default_cy = float(defaults.get("cy", float(w) / 2.0))
        radius_limit_x = max(1.0, min(default_cx, float(w) - default_cx) - (stroke_circle / 2.0))
        radius_limit_y = max(1.0, min(default_cy, float(h) - default_cy) - (stroke_circle / 2.0))
        r = float(min(r, radius_limit_x, radius_limit_y))

        params["cx"] = default_cx
        params["cy"] = cy
        params["r"] = r
        params["lock_circle_cx"] = True
        params["lock_stem_center_to_circle"] = True

    if elongated_plain_badge:
        default_cx = float(defaults.get("cx", cx))
        default_cy = float(defaults.get("cy", cy))
        default_r = float(defaults.get("r", r))
        params["cx"] = default_cx
        params["cy"] = float(clip_scalar_fn(cy, default_cy - 1.0, default_cy + 1.0))
        r = float(max(r, default_r * 0.97))
        params["r"] = r
        params["lock_circle_cx"] = True
        params["lock_circle_cy"] = True
        params["lock_stem_center_to_circle"] = True
        params["stem_len_min_ratio"] = float(max(float(params.get("stem_len_min_ratio", 0.0) or 0.0), 0.80))
        cx = float(params["cx"])
        cy = float(params["cy"])

    if str(params.get("text_mode", "")).lower() in {"voc", "co2"}:
        default_r = float(defaults.get("r", r))
        r = float(clip_scalar_fn(r, default_r * 0.95, default_r * 1.08))
        params["r"] = r

    min_stem_width = max(1.0, stroke_circle * 0.72)
    default_stem_width_max = max(min_stem_width, min(float(w) * 0.12, stroke_circle * 1.35))
    max_stem_width = max(
        min_stem_width,
        min(float(defaults.get("stem_width_max", default_stem_width_max)), default_stem_width_max),
    )
    stem_width = max(min_stem_width, min(raw_stem_width, max_stem_width))

    params["stem_enabled"] = True
    params["stem_width"] = stem_width
    params["stem_width_max"] = max_stem_width
    params["stem_x"] = cx - (params["stem_width"] / 2.0)
    min_stem_len = 1.0 if h <= 18 else 2.0
    max_r_for_visible_stem = max(1.0, float(h) - cy - min_stem_len)
    if r > max_r_for_visible_stem:
        r = max_r_for_visible_stem
        params["r"] = r
    stem_top = cy + r
    stem_top = max(0.0, min(float(h) - min_stem_len, stem_top))
    params["stem_top"] = stem_top
    params["stem_bottom"] = float(h)
    params["stem_gray"] = int(round(params.get("stroke_gray", defaults.get("stroke_gray", 152))))
    if elongated_plain_badge:
        params["stem_len_min_ratio"] = float(max(float(params.get("stem_len_min_ratio", 0.0) or 0.0), 0.80))
        persist_connector_length_floor_fn(params, "stem", default_ratio=0.80)

    # AC0811 now runs permanently without geometry lock restrictions.
    for key in (
        "lock_circle_cx",
        "lock_circle_cy",
        "lock_stem_center_to_circle",
        "lock_arm_center_to_circle",
        "lock_stem",
        "lock_arm",
        "lock_text_position",
        "lock_text_scale",
        "lock_stroke_widths",
    ):
        if key in params:
            params[key] = False
    params["stem_len_min_ratio"] = 0.0
    params["ac0811_no_restrictions"] = True

    return normalize_light_circle_colors_fn(params)
