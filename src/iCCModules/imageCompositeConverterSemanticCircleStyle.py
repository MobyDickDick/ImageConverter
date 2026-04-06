from __future__ import annotations


def normalizeLightCircleColorsImpl(
    params: dict,
    *,
    light_circle_fill_gray: int,
    light_circle_stroke_gray: int,
    light_circle_text_gray: int,
) -> dict:
    params["fill_gray"] = light_circle_fill_gray
    params["stroke_gray"] = light_circle_stroke_gray
    if params.get("stem_enabled"):
        params["stem_gray"] = light_circle_stroke_gray
    if params.get("draw_text", True) and "text_gray" in params:
        params["text_gray"] = light_circle_text_gray
    return params


def normalizeAc08LineWidthsImpl(
    params: dict,
    *,
    ac08_stroke_width_px: float,
    light_circle_stroke_gray: int,
) -> dict:
    """For AC08xx symbols: prefer a uniform 1px circle/connector stroke."""
    p = dict(params)
    prev_circle_stroke = float(p.get("stroke_circle", ac08_stroke_width_px))
    p["stroke_circle"] = ac08_stroke_width_px
    if bool(p.pop("preserve_outer_diameter_on_stroke_normalization", False)) and p.get(
        "circle_enabled",
        True,
    ) and "r" in p and prev_circle_stroke > 0.0:
        # Keep the visual outer diameter stable when normalizing to the
        # canonical AC08 1px stroke. Otherwise tiny plain-ring badges can
        # lose more than a pixel of diameter even if the fitted geometry
        # correctly reached the canvas border.
        outer_radius = float(p["r"]) + (prev_circle_stroke / 2.0)
        p["r"] = max(1.0, outer_radius - (ac08_stroke_width_px / 2.0))
    # Keep semantic AC08xx families on their canonical stroke thickness.
    # The later pixel-error bracketing step can otherwise over-fit anti-aliased
    # ring edges and inflate widths (e.g. 1px -> 6px for tiny circles).
    p["lock_stroke_widths"] = True
    if p.get("arm_enabled"):
        p["arm_stroke"] = ac08_stroke_width_px
    if p.get("stem_enabled"):
        p["stem_width"] = ac08_stroke_width_px
        if "cx" in p:
            p["stem_x"] = float(p["cx"]) - (ac08_stroke_width_px / 2.0)
        p["stem_gray"] = int(p.get("stroke_gray", light_circle_stroke_gray))
    return p


def estimateBorderBackgroundGrayImpl(gray, *, np_module) -> float:
    """Estimate badge background tone from the outer image border pixels."""
    if gray.size == 0:
        return 255.0
    h, w = gray.shape
    if h < 2 or w < 2:
        return float(np_module.median(gray))
    border = np_module.concatenate((gray[0, :], gray[h - 1, :], gray[:, 0], gray[:, w - 1]))
    return float(np_module.median(border))


def estimateCircleTonesAndStrokeImpl(
    gray,
    cx: float,
    cy: float,
    r: float,
    stroke_hint: float,
    *,
    np_module,
) -> tuple[float, float, float]:
    """Estimate fill/ring grayscale and stroke width for circular ring-like badges."""
    yy, xx = np_module.indices(gray.shape)
    dist = np_module.sqrt((xx - float(cx)) ** 2 + (yy - float(cy)) ** 2)

    inner_mask = dist <= max(1.0, float(r) * 0.78)
    fill_gray = float(np_module.median(gray[inner_mask])) if np_module.any(inner_mask) else float(np_module.median(gray))

    search_band = max(2.0, min(float(r) * 0.30, 5.0))
    ring_search = np_module.abs(dist - float(r)) <= search_band
    ring_vals = gray[ring_search] if np_module.any(ring_search) else gray
    ring_gray = float(np_module.median(ring_vals))

    # Prefer the darker contour around the estimated radius when present.
    dark_cut = fill_gray - 2.0
    dark_ring = ring_search & (gray <= dark_cut)
    if np_module.any(dark_ring):
        ring_gray = float(np_module.median(gray[dark_ring]))
        d = np_module.abs(dist - float(r))[dark_ring]
        stroke_est = float(max(1.0, min(6.0, np_module.percentile(d, 72) * 2.0)))
    else:
        stroke_est = float(max(1.0, min(6.0, stroke_hint)))

    return fill_gray, ring_gray, stroke_est
