"""Mask/geometry helper functions extracted from the monolith."""

from __future__ import annotations

import math


def fitToOriginalSizeImpl(img_orig, img_svg, cv2):
    if img_svg is None:
        return None
    if img_svg.shape[:2] == img_orig.shape[:2]:
        return img_svg
    return cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)


def maskCentroidRadiusImpl(mask) -> tuple[float, float, float] | None:
    ys, xs = mask.nonzero()
    if xs.size < 5:
        return None
    cx = float(xs.mean())
    cy = float(ys.mean())
    r = float((xs.size / math.pi) ** 0.5)
    return cx, cy, r


def maskBboxImpl(mask) -> tuple[float, float, float, float] | None:
    ys, xs = mask.nonzero()
    if xs.size < 3:
        return None
    x1, x2 = float(xs.min()), float(xs.max())
    y1, y2 = float(ys.min()), float(ys.max())
    return x1, y1, x2, y2


def maskCenterSizeImpl(mask, *, mask_bbox_fn) -> tuple[float, float, float] | None:
    bbox = mask_bbox_fn(mask)
    if bbox is None:
        return None
    x1, y1, x2, y2 = bbox
    width = max(1.0, (x2 - x1) + 1.0)
    height = max(1.0, (y2 - y1) + 1.0)
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    size = width * height
    return cx, cy, size


def maskMinRectCenterDiagImpl(mask, *, cv2) -> tuple[float, float, float] | None:
    mask_u8 = (mask.astype("uint8")) * 255
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    cnt = max(contours, key=cv2.contourArea)
    if cv2.contourArea(cnt) < 2.0:
        return None

    (cx, cy), (rw, rh), _angle = cv2.minAreaRect(cnt)
    diag = float(math.hypot(float(rw), float(rh)))
    if not math.isfinite(diag) or diag <= 0.0:
        return None
    return float(cx), float(cy), diag


def elementBboxChangeIsPlausibleImpl(mask_orig, mask_svg, *, mask_bbox_fn) -> tuple[bool, str | None]:
    """Reject clearly implausible box drifts between source and converted element."""
    orig_bbox = mask_bbox_fn(mask_orig)
    svg_bbox = mask_bbox_fn(mask_svg)
    if orig_bbox is None or svg_bbox is None:
        return True, None

    ox1, oy1, ox2, oy2 = orig_bbox
    sx1, sy1, sx2, sy2 = svg_bbox

    ow = max(1.0, (ox2 - ox1) + 1.0)
    oh = max(1.0, (oy2 - oy1) + 1.0)
    sw = max(1.0, (sx2 - sx1) + 1.0)
    sh = max(1.0, (sy2 - sy1) + 1.0)

    ocx = (ox1 + ox2) / 2.0
    ocy = (oy1 + oy2) / 2.0
    scx = (sx1 + sx2) / 2.0
    scy = (sy1 + sy2) / 2.0

    center_dist = float(math.hypot(scx - ocx, scy - ocy))
    orig_diag = float(math.hypot(ow, oh))
    max_center_dist = max(2.0, orig_diag * 0.42)

    w_ratio = sw / ow
    h_ratio = sh / oh
    area_ratio = (sw * sh) / max(1.0, ow * oh)

    if center_dist > max_center_dist:
        return (
            False,
            "Box-Check verworfen " f"(Δcenter={center_dist:.3f} > {max_center_dist:.3f})",
        )

    if not (0.55 <= w_ratio <= 1.85 and 0.55 <= h_ratio <= 1.85 and 0.40 <= area_ratio <= 2.40):
        return (
            False,
            "Box-Check verworfen " f"(w_ratio={w_ratio:.3f}, h_ratio={h_ratio:.3f}, area_ratio={area_ratio:.3f})",
        )

    return True, None
