"""Generalized dual-arrow badge helpers (vertical stems + triangular heads)."""

from __future__ import annotations

from typing import Any


def looksLikeDualArrowDescriptionImpl(desc: str) -> bool:
    normalized = " ".join(str(desc or "").lower().split())
    if not normalized:
        return False
    required_tokens = ("zwei", "vertikale", "blau", "rot", "dreieck")
    if not all(token in normalized for token in required_tokens):
        return False
    return "spitze nach unten" in normalized and "spitze nach oben" in normalized


def detectDualArrowBadgeParamsFromImageImpl(
    img,
    *,
    np_module: Any,
) -> dict[str, Any] | None:
    np = np_module
    if img is None or getattr(img, "size", 0) == 0:
        return None
    h, w = img.shape[:2]
    if h <= 0 or w <= 0:
        return None

    # Cast to signed ints before channel-delta comparisons. With uint8,
    # expressions like ``r + 18`` wrap at 255 and can classify bright
    # background pixels as colored foreground.
    b = img[:, :, 0].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    r = img[:, :, 2].astype(np.int16)
    blue_mask = (b > 90) & (b > r + 18) & (b > g + 10)
    red_mask = (r > 90) & (r > b + 18) & (r > g + 10)
    if int(np.count_nonzero(blue_mask)) < 8 or int(np.count_nonzero(red_mask)) < 8:
        return None

    left = _fitArrowFromMask(blue_mask, np_module=np)
    right = _fitArrowFromMask(red_mask, np_module=np)
    if left is None or right is None:
        return None
    if _arrowPointsDown(left) == _arrowPointsDown(right):
        # Dual-arrow badges encode opposite directions. If both detections
        # collapse to the same orientation (common with compressed tips),
        # keep the right/red arrow and mirror the left/blue arrow.
        left = _flipArrowDirection(left)
    left, right = _normalizeDualArrowPairGeometry(left, right, h)

    return {
        "mode": "dual_arrow_badge",
        "base_name": "DUAL_ARROW",
        "variant_name": "",
        "left": left,
        "right": right,
    }


def _fitArrowFromMask(mask, *, np_module: Any) -> dict[str, float] | None:
    np = np_module
    ys, xs = np.where(mask)
    if len(xs) < 8:
        return None
    y_min = int(np.min(ys))
    y_max = int(np.max(ys))
    if y_max <= y_min:
        return None

    row_widths: list[tuple[int, int]] = []
    for y in range(y_min, y_max + 1):
        row_widths.append((y, int(np.count_nonzero(mask[y, :]))))
    non_zero = [w for _y, w in row_widths if w > 0]
    if not non_zero:
        return None
    center_x = float(np.mean(xs))
    stem_w = max(1.0, float(np.percentile(non_zero, 20)))
    tri_threshold = max(2.0, stem_w * 1.7)
    top_w = row_widths[0][1]
    bottom_w = row_widths[-1][1]
    down = bool(bottom_w > top_w)
    if top_w == bottom_w:
        # Some JPEG-compressed arrow tips are only one pixel wide at both ends.
        # In those cases, infer direction from where wider rows cluster.
        y_mid = (y_min + y_max) / 2.0
        weighted_sum = 0.0
        weight_total = 0.0
        for y, width in row_widths:
            if width <= 1:
                continue
            weight = float(width - 1)
            weighted_sum += float(y) * weight
            weight_total += weight
        if weight_total > 0:
            down = (weighted_sum / weight_total) > y_mid
    splits = [y for y, width in row_widths if width >= tri_threshold]
    if down:
        split = splits[0] if splits else int((y_min + y_max) / 2)
        line_y1 = float(y_min)
        line_y2 = float(max(y_min, split))
        tip_y = float(y_max)
        base_y = float(split)
    else:
        split = splits[-1] if splits else int((y_min + y_max) / 2)
        line_y1 = float(min(y_max, split))
        line_y2 = float(y_max)
        tip_y = float(y_min)
        base_y = float(split)

    return {
        "center_x": center_x,
        "line_y1": line_y1,
        "line_y2": line_y2,
        "line_width": float(stem_w),
        "triangle_tip_y": tip_y,
        "triangle_base_y": base_y,
        "triangle_half_width": float(max(non_zero)) / 2.0,
    }


def _arrowPointsDown(arrow: dict[str, float]) -> bool:
    return float(arrow["triangle_tip_y"]) > float(arrow["triangle_base_y"])


def _flipArrowDirection(arrow: dict[str, float]) -> dict[str, float]:
    flipped = dict(arrow)
    line_y1 = float(arrow["line_y1"])
    line_y2 = float(arrow["line_y2"])
    y_min = min(line_y1, line_y2, float(arrow["triangle_tip_y"]), float(arrow["triangle_base_y"]))
    y_max = max(line_y1, line_y2, float(arrow["triangle_tip_y"]), float(arrow["triangle_base_y"]))
    base_y = float(arrow["triangle_base_y"])
    if _arrowPointsDown(arrow):
        flipped["triangle_tip_y"] = y_min
        flipped["line_y1"] = min(y_max, base_y)
        flipped["line_y2"] = y_max
    else:
        flipped["triangle_tip_y"] = y_max
        flipped["line_y1"] = y_min
        flipped["line_y2"] = max(y_min, base_y)
    return flipped


def _normalizeDualArrowPairGeometry(
    left: dict[str, float],
    right: dict[str, float],
    height: int,
) -> tuple[dict[str, float], dict[str, float]]:
    normalized_left = dict(left)
    normalized_right = dict(right)

    line_top = float(min(left["line_y1"], right["line_y1"]))
    gap = 1.0
    left_base = float(left["triangle_base_y"])
    right_base = float(right["triangle_base_y"])
    triangle_top = float(max(0.0, min(left_base, right_base)))
    line_bottom = float(max(line_top, triangle_top - gap))

    tri_heights = [
        abs(float(left["triangle_tip_y"]) - float(left["triangle_base_y"])),
        abs(float(right["triangle_tip_y"]) - float(right["triangle_base_y"])),
    ]
    shared_tri_height = float(max(2.0, min(tri_heights)))
    shared_tri_height = float(min(shared_tri_height, max(2.0, float(height) * 0.22)))

    shared_half_width = (float(left["triangle_half_width"]) + float(right["triangle_half_width"])) / 2.0
    shared_line_width = (float(left["line_width"]) + float(right["line_width"])) / 2.0

    normalized_left["line_y1"] = line_top
    normalized_left["line_y2"] = line_bottom
    normalized_left["line_width"] = shared_line_width
    normalized_left["triangle_tip_y"] = triangle_top
    normalized_left["triangle_base_y"] = triangle_top + shared_tri_height
    normalized_left["triangle_half_width"] = shared_half_width

    normalized_right["line_y1"] = line_top
    normalized_right["line_y2"] = line_bottom
    normalized_right["line_width"] = shared_line_width
    normalized_right["triangle_base_y"] = triangle_top
    normalized_right["triangle_tip_y"] = triangle_top + shared_tri_height
    normalized_right["triangle_half_width"] = shared_half_width

    return normalized_left, normalized_right


def generateDualArrowBadgeSvgImpl(
    w: int,
    h: int,
    params: dict[str, Any],
) -> str:
    left = dict(params.get("left", {}))
    right = dict(params.get("right", {}))
    left.setdefault("center_x", float(w) * 0.33)
    right.setdefault("center_x", float(w) * 0.67)
    left.setdefault("line_y1", 0.0)
    left.setdefault("line_y2", float(h) * 0.45)
    right.setdefault("line_y1", float(h) * 0.55)
    right.setdefault("line_y2", float(h))
    left.setdefault("line_width", 1.0)
    right.setdefault("line_width", 1.0)
    left.setdefault("triangle_tip_y", float(h))
    left.setdefault("triangle_base_y", float(h) * 0.52)
    right.setdefault("triangle_tip_y", 0.0)
    right.setdefault("triangle_base_y", float(h) * 0.48)
    left.setdefault("triangle_half_width", max(1.0, float(w) * 0.14))
    right.setdefault("triangle_half_width", max(1.0, float(w) * 0.14))
    left_color = str(params.get("left_color", "#2f6bff"))
    right_color = str(params.get("right_color", "#e53935"))
    return (
        f'<svg width="{w}px" height="{h}px" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  <line x1="{float(left["center_x"]):.4f}" y1="{float(left["line_y1"]):.4f}" '
        f'x2="{float(left["center_x"]):.4f}" y2="{float(left["line_y2"]):.4f}" '
        f'stroke="{left_color}" stroke-width="{float(left["line_width"]):.4f}" stroke-linecap="butt"/>\n'
        f'  <polygon points="{float(left["center_x"]):.4f},{float(left["triangle_tip_y"]):.4f} '
        f'{float(left["center_x"]) - float(left["triangle_half_width"]):.4f},{float(left["triangle_base_y"]):.4f} '
        f'{float(left["center_x"]) + float(left["triangle_half_width"]):.4f},{float(left["triangle_base_y"]):.4f}" '
        f'fill="{left_color}"/>\n'
        f'  <line x1="{float(right["center_x"]):.4f}" y1="{float(right["line_y1"]):.4f}" '
        f'x2="{float(right["center_x"]):.4f}" y2="{float(right["line_y2"]):.4f}" '
        f'stroke="{right_color}" stroke-width="{float(right["line_width"]):.4f}" stroke-linecap="butt"/>\n'
        f'  <polygon points="{float(right["center_x"]):.4f},{float(right["triangle_tip_y"]):.4f} '
        f'{float(right["center_x"]) - float(right["triangle_half_width"]):.4f},{float(right["triangle_base_y"]):.4f} '
        f'{float(right["center_x"]) + float(right["triangle_half_width"]):.4f},{float(right["triangle_base_y"]):.4f}" '
        f'fill="{right_color}"/>\n'
        "</svg>\n"
    )
