"""Extracted semantic connector enforcement helpers for imageCompositeConverter."""

from __future__ import annotations

from collections.abc import Callable


def enforceLeftArmBadgeGeometryImpl(
    params: dict[str, object],
    *,
    ac08_stroke_width_px: float,
) -> dict[str, object]:
    """Ensure AC0812-like badges always keep a visible left connector arm."""
    p = dict(params)
    if not p.get("circle_enabled", True):
        return p
    if "cx" not in p or "cy" not in p or "r" not in p:
        return p

    cx = float(p["cx"])
    cy = float(p["cy"])
    r = float(p["r"])
    arm_stroke = float(max(1.0, p.get("arm_stroke", ac08_stroke_width_px)))
    attach_offset = max(0.0, arm_stroke / 2.0)
    arm_x2 = max(0.0, cx - r - attach_offset)

    p["arm_enabled"] = True
    p["arm_x1"] = 0.0
    p["arm_y1"] = cy
    p["arm_x2"] = arm_x2
    p["arm_y2"] = cy
    p["arm_stroke"] = arm_stroke

    arm_len = float(max(0.0, arm_x2))
    ratio = float(max(0.0, min(1.0, float(p.get("arm_len_min_ratio", 0.75)))))
    p["arm_len_min_ratio"] = ratio
    p["arm_len_min"] = float(max(1.0, float(p.get("arm_len_min", 1.0)), arm_len * ratio))
    return p


def enforceRightArmBadgeGeometryImpl(
    params: dict[str, object],
    *,
    w: int,
    ac08_stroke_width_px: float,
) -> dict[str, object]:
    """Ensure AC0810/AC0814-like badges always keep a visible right connector arm."""
    p = dict(params)
    if not p.get("circle_enabled", True):
        return p
    if "cx" not in p or "cy" not in p or "r" not in p:
        return p

    cx = float(p["cx"])
    cy = float(p["cy"])
    r = float(p["r"])
    arm_stroke = float(max(1.0, p.get("arm_stroke", ac08_stroke_width_px)))
    attach_offset = max(0.0, arm_stroke / 2.0)
    canvas_width = max(
        float(w),
        float(p.get("arm_x2", 0.0) or 0.0),
        float(p.get("width", 0.0) or 0.0),
        float(p.get("badge_width", 0.0) or 0.0),
        cx + r,
    )
    ratio = float(max(0.0, min(1.0, float(p.get("arm_len_min_ratio", 0.75)))))
    requested_min_len = float(max(1.0, float(p.get("arm_len_min", 1.0))))
    requested_min_len = float(min(requested_min_len, canvas_width * 0.35))
    semantic_min_len = float(max(requested_min_len, ratio * max(1.0, canvas_width * 0.20)))
    if str(p.get("text_mode", "")).lower() in {"co2", "voc"}:
        semantic_min_len = float(max(semantic_min_len, canvas_width * 0.20))
    arm_start = cx + r + attach_offset
    max_arm_start = max(0.0, canvas_width - semantic_min_len)
    if arm_start > max_arm_start:
        cx = max(r + attach_offset, cx - (arm_start - max_arm_start))
        p["cx"] = cx
    max_r_for_semantic_span = max(1.0, canvas_width - semantic_min_len - attach_offset - cx)
    if r > max_r_for_semantic_span:
        r = max_r_for_semantic_span
        p["r"] = r
    arm_x1 = min(canvas_width, cx + r + attach_offset)

    p["arm_enabled"] = True
    p["arm_x1"] = arm_x1
    p["arm_y1"] = cy
    p["arm_x2"] = canvas_width
    p["arm_y2"] = cy
    p["arm_stroke"] = arm_stroke

    arm_len = float(max(0.0, canvas_width - arm_x1))
    p["arm_len_min_ratio"] = ratio
    p["arm_len_min"] = float(max(semantic_min_len, arm_len * ratio))
    return p


def enforceSemanticConnectorExpectationImpl(
    base_name: str,
    semantic_elements: list[str],
    params: dict[str, object],
    *,
    normalize_base_name_fn: Callable[[str], str],
    enforce_left_fn: Callable[[dict[str, object]], dict[str, object]],
    enforce_right_fn: Callable[[dict[str, object]], dict[str, object]],
) -> dict[str, object]:
    """Restore mandatory connector geometry for directional semantic badges."""
    normalized_base = normalize_base_name_fn(str(base_name)).upper()
    normalized_elements = [str(elem).lower() for elem in (semantic_elements or [])]
    expects_left_arm = any("waagrechter strich links" in elem for elem in normalized_elements)
    expects_right_arm = any("waagrechter strich rechts" in elem for elem in normalized_elements)

    if normalized_base in {"AC0812", "AC0837", "AC0882"} or expects_left_arm:
        return enforce_left_fn(params)
    if normalized_base in {"AC0810", "AC0814", "AC0834", "AC0838", "AC0839"} or expects_right_arm:
        return enforce_right_fn(params)
    return params
