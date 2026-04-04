"""Extracted element-mask and foreground helpers for imageCompositeConverter."""

from __future__ import annotations


def ringAndFillMasksImpl(h: int, w: int, params: dict, *, np_module) -> tuple:
    yy, xx = np_module.indices((h, w))
    dist = np_module.sqrt((xx - params["cx"]) ** 2 + (yy - params["cy"]) ** 2)
    ring_half = max(0.7, params["stroke_circle"])
    ring = np_module.abs(dist - params["r"]) <= ring_half
    fill = dist <= max(0.5, params["r"] - ring_half)
    return ring, fill


def meanGrayForMaskImpl(img, mask, *, cv2_module, np_module) -> float | None:
    if int(mask.sum()) == 0:
        return None
    gray = cv2_module.cvtColor(img, cv2_module.COLOR_BGR2GRAY)
    vals = gray[mask]
    if vals.size == 0:
        return None
    return float(np_module.mean(vals))


def elementRegionMaskImpl(
    h: int,
    w: int,
    params: dict,
    element: str,
    *,
    np_module,
    text_bbox_fn,
    apply_circle_geometry_penalty: bool = True,
):
    yy, xx = np_module.indices((h, w))
    context_pad = max(2.0, float(min(h, w)) * 0.12)
    if element == "circle" and apply_circle_geometry_penalty:
        radius_with_context = params["r"] + context_pad
        circle = (xx - params["cx"]) ** 2 + (yy - params["cy"]) ** 2 <= radius_with_context**2
        top = yy <= (params["cy"] + params["r"] + context_pad)
        return circle & top
    if element == "stem" and params.get("stem_enabled"):
        x1 = max(0.0, params["stem_x"] - context_pad)
        x2 = min(float(w), params["stem_x"] + params["stem_width"] + context_pad)
        y1 = max(0.0, params["stem_top"] - context_pad)
        y2 = min(float(h), params["stem_bottom"] + context_pad)
        return (xx >= x1) & (xx <= x2) & (yy >= y1) & (yy <= y2)
    if element == "arm" and params.get("arm_enabled"):
        x1 = max(0.0, min(params.get("arm_x1", 0.0), params.get("arm_x2", 0.0)) - context_pad)
        x2 = min(float(w), max(params.get("arm_x1", 0.0), params.get("arm_x2", 0.0)) + context_pad)
        y1 = max(0.0, min(params.get("arm_y1", 0.0), params.get("arm_y2", 0.0)) - context_pad)
        y2 = min(float(h), max(params.get("arm_y1", 0.0), params.get("arm_y2", 0.0)) + context_pad)
        pad = max(1.0, params.get("arm_stroke", params.get("stem_or_arm", 1.0)) * 0.8)
        return (xx >= (x1 - pad)) & (xx <= (x2 + pad)) & (yy >= (y1 - pad)) & (yy <= (y2 + pad))
    if element == "text" and params.get("draw_text", True):
        x1, y1, x2, y2 = text_bbox_fn(params)
        x1 = max(0.0, x1 - context_pad)
        y1 = max(0.0, y1 - context_pad)
        x2 = min(float(w), x2 + context_pad)
        y2 = min(float(h), y2 + context_pad)
        return (xx >= x1) & (xx <= x2) & (yy >= y1) & (yy <= y2)
    return None


def textBboxImpl(params: dict, *, co2_layout_fn, glyph_bbox_fn) -> tuple[float, float, float, float]:
    """Approximate text bounding box for semantic badge text modes."""
    cx = float(params.get("cx", 0.0))
    cy = float(params.get("cy", 0.0))
    r = max(1.0, float(params.get("r", 1.0)))
    mode = str(params.get("text_mode", "")).lower()

    if mode == "voc":
        font_size = max(4.0, r * float(params.get("voc_font_scale", 0.52)))
        width = font_size * 1.95
        height = font_size * 0.90
        y = cy + float(params.get("voc_dy", 0.0))
        return (cx - (width / 2.0), y - (height / 2.0), cx + (width / 2.0), y + (height / 2.0))

    if mode == "co2":
        layout = co2_layout_fn(params)
        x1 = float(layout["x1"])
        x2 = float(layout["x2"])
        y = float(layout["y_base"])
        height = float(layout["height"])
        return (x1, y - (height / 2.0), x2, y + (height / 2.0))

    s = float(params.get("s", 0.0))
    tx = float(params.get("tx", cx))
    ty = float(params.get("ty", cy))
    xmin, ymin, xmax, ymax = glyph_bbox_fn(params.get("text_mode", "path"))
    x1 = tx + (xmin * s)
    y1 = ty + (ymin * s)
    x2 = tx + (xmax * s)
    y2 = ty + (ymax * s)
    return (x1, y1, x2, y2)


def foregroundMaskImpl(img, *, cv2_module, np_module):
    gray = cv2_module.cvtColor(img, cv2_module.COLOR_BGR2GRAY)
    _, fg_otsu = cv2_module.threshold(gray, 0, 255, cv2_module.THRESH_BINARY_INV + cv2_module.THRESH_OTSU)

    blur = cv2_module.GaussianBlur(gray, (3, 3), 0)
    local_contrast = cv2_module.absdiff(gray, blur)
    contrast_thresh = max(2, int(round(float(np_module.percentile(local_contrast, 82)))))
    fg_contrast = local_contrast >= contrast_thresh

    fg = (fg_otsu > 0) | fg_contrast
    fg_u8 = fg.astype(np_module.uint8) * 255
    kernel = np_module.ones((2, 2), dtype=np_module.uint8)
    fg_u8 = cv2_module.morphologyEx(fg_u8, cv2_module.MORPH_CLOSE, kernel, iterations=1)
    return fg_u8 > 0


def circleFromForegroundMaskImpl(fg_mask, *, cv2_module, np_module, math_module):
    """Infer a coarse circle from the foreground mask when Hough is too brittle."""
    mask_u8 = (fg_mask.astype(np_module.uint8)) * 255
    contours, _ = cv2_module.findContours(mask_u8, cv2_module.RETR_EXTERNAL, cv2_module.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    h, w = fg_mask.shape[:2]
    min_side = float(max(1, min(h, w)))
    best: tuple[float, float, float, float] | None = None

    for cnt in contours:
        area = float(cv2_module.contourArea(cnt))
        if area < max(4.0, min_side * 0.35):
            continue
        x, y, bw, bh = cv2_module.boundingRect(cnt)
        if bw < 3 or bh < 3:
            continue
        aspect = float(bw) / max(1.0, float(bh))
        if not (0.65 <= aspect <= 1.35):
            continue

        (cx, cy), radius = cv2_module.minEnclosingCircle(cnt)
        radius = float(radius)
        if radius < max(2.5, min_side * 0.10) or radius > max(8.0, min_side * 0.55):
            continue

        dist = np_module.sqrt((cnt[:, 0, 0].astype(np_module.float32) - cx) ** 2 + (cnt[:, 0, 1].astype(np_module.float32) - cy) ** 2)
        if dist.size == 0:
            continue
        radial_residual = float(np_module.mean(np_module.abs(dist - radius)))
        circle_area = math_module.pi * radius * radius
        fill_ratio = area / max(1.0, circle_area)
        if fill_ratio < 0.30:
            continue
        bins = 12
        coverage_bins = np_module.zeros(bins, dtype=np_module.uint8)
        for px, py in cnt[:, 0, :]:
            ang = math_module.atan2(float(py) - cy, float(px) - cx)
            idx = int(((ang + math_module.pi) / (2.0 * math_module.pi)) * bins) % bins
            coverage_bins[idx] = 1
        coverage = int(np_module.sum(coverage_bins))
        if coverage < 6:
            continue

        bbox_fill_ratio = area / max(1.0, float(bw * bh))
        if bbox_fill_ratio > 0.82 and radial_residual > max(1.0, radius * 0.22):
            continue

        score = radial_residual + abs(1.0 - aspect) * 3.0 + max(0, 7 - coverage) * 0.75
        if best is None or score < best[0]:
            best = (score, float(cx), float(cy), radius)

    if best is None:
        return None
    return best[1], best[2], best[3]


def maskSupportsCircleImpl(
    mask,
    *,
    mask_bbox_fn,
    cv2_module,
    np_module,
    math_module,
) -> bool:
    if mask is None:
        return False
    pixel_count = int(np_module.count_nonzero(mask))
    if pixel_count < 4:
        return False

    bbox = mask_bbox_fn(mask)
    if bbox is None:
        return False
    x1, y1, x2, y2 = bbox
    width = max(1.0, (x2 - x1) + 1.0)
    height = max(1.0, (y2 - y1) + 1.0)
    if not (0.60 <= (width / height) <= 1.40):
        return False

    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    approx_radius = max(1.0, (width + height) * 0.25)
    area = width * height
    density = float(pixel_count) / max(1.0, area)
    if density < 0.04:
        return False

    ys, xs = np_module.where(mask)
    bins = 12
    coverage_bins = np_module.zeros(bins, dtype=np_module.uint8)
    ring_tol = max(1.2, approx_radius * 0.45)
    near_ring = 0
    for py, px in zip(ys, xs, strict=False):
        dist = math_module.hypot(float(px) - cx, float(py) - cy)
        if abs(dist - approx_radius) > ring_tol:
            continue
        near_ring += 1
        ang = math_module.atan2(float(py) - cy, float(px) - cx)
        idx = int(((ang + math_module.pi) / (2.0 * math_module.pi)) * bins) % bins
        coverage_bins[idx] = 1

    coverage = int(np_module.sum(coverage_bins))
    if coverage >= 4 and near_ring >= max(4, int(round(pixel_count * 0.35))):
        return True

    mask_u8 = (mask.astype(np_module.uint8)) * 255
    contours, _ = cv2_module.findContours(mask_u8, cv2_module.RETR_EXTERNAL, cv2_module.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False
    cnt = max(contours, key=cv2_module.contourArea)
    perimeter = float(cv2_module.arcLength(cnt, True))
    if perimeter <= 0.0:
        return False
    contour_area = float(cv2_module.contourArea(cnt))
    circularity = (4.0 * math_module.pi * contour_area) / max(1e-6, perimeter * perimeter)
    return circularity >= 0.28 and density <= 0.72
