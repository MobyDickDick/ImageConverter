"""Extracted semantic template-transfer helpers for imageCompositeConverter."""

from __future__ import annotations

import math
from collections.abc import Callable


def semanticTransferRotationsImpl(
    target_params: dict[str, object],
    donor_params: dict[str, object],
) -> tuple[int, ...]:
    """Rotation candidates for semantic transfer while preserving symbol semantics."""
    has_text = bool(target_params.get("draw_text", False) or donor_params.get("draw_text", False))
    has_connector = bool(
        target_params.get("arm_enabled", False)
        or target_params.get("stem_enabled", False)
        or donor_params.get("arm_enabled", False)
        or donor_params.get("stem_enabled", False)
    )
    if has_text or has_connector:
        # Directional semantic badges (e.g. AC0812 left arm) encode orientation in
        # geometry. Rotating donor templates can improve pixel error but flips the
        # meaning of connector-side symbols. Keep transfer upright/unrotated.
        return (0,)
    return (0, 90, 180, 270)


def connectorArmDirectionImpl(params: dict[str, object]) -> int | None:
    """Return horizontal arm side: -1 left of circle, +1 right, or None if unknown."""
    x1 = params.get("arm_x1")
    x2 = params.get("arm_x2")
    cx = params.get("cx")
    if x1 is not None and x2 is not None and cx is not None:
        mid = (float(x1) + float(x2)) * 0.5
        delta = mid - float(cx)
        if abs(delta) > 1e-3:
            return -1 if delta < 0.0 else 1

    if x1 is not None and cx is not None:
        delta = float(x1) - float(cx)
        if abs(delta) > 1e-3:
            return -1 if delta < 0.0 else 1
    return None


def connectorStemDirectionImpl(params: dict[str, object]) -> int | None:
    """Return vertical stem direction: -1 up, +1 down, or None if unknown."""
    y1 = params.get("arm_y1")
    y2 = params.get("arm_y2")
    if y1 is not None and y2 is not None:
        dy = float(y2) - float(y1)
        if abs(dy) > 1e-3:
            return -1 if dy < 0.0 else 1

    cy = params.get("cy")
    if y1 is not None and y2 is not None and cy is not None:
        mid = (float(y1) + float(y2)) * 0.5
        delta = mid - float(cy)
        if abs(delta) > 1e-3:
            return -1 if delta < 0.0 else 1
    return None


def semanticTransferIsCompatibleImpl(
    target_params: dict[str, object],
    donor_params: dict[str, object],
    *,
    connector_arm_direction_fn: Callable[[dict[str, object]], int | None],
    connector_stem_direction_fn: Callable[[dict[str, object]], int | None],
) -> bool:
    """Return whether donor semantics can preserve target semantic geometry."""
    target_has_arm = bool(target_params.get("arm_enabled", False))
    target_has_stem = bool(target_params.get("stem_enabled", False))
    donor_has_arm = bool(donor_params.get("arm_enabled", False))
    donor_has_stem = bool(donor_params.get("stem_enabled", False))

    # Keep connector type stable for directional symbols (arm vs stem).
    if target_has_arm != donor_has_arm:
        return False
    if target_has_stem != donor_has_stem:
        return False

    target_has_text = bool(target_params.get("draw_text", False))
    donor_has_text = bool(donor_params.get("draw_text", False))
    if target_has_text != donor_has_text:
        return False

    # If both carry labels, require same text mode (e.g. VOC vs CO₂ path families).
    if target_has_text and donor_has_text:
        target_mode = str(target_params.get("text_mode", "")).lower()
        donor_mode = str(donor_params.get("text_mode", "")).lower()
        if target_mode and donor_mode and target_mode != donor_mode:
            return False

    # Directional connector families (e.g. AC0810 right arm vs AC0812 left arm)
    # must keep side/orientation stable during semantic transfer.
    if target_has_arm and donor_has_arm:
        target_arm_dir = connector_arm_direction_fn(target_params)
        donor_arm_dir = connector_arm_direction_fn(donor_params)
        if target_arm_dir is not None and donor_arm_dir is not None and target_arm_dir != donor_arm_dir:
            return False

    if target_has_stem and donor_has_stem:
        target_stem_dir = connector_stem_direction_fn(target_params)
        donor_stem_dir = connector_stem_direction_fn(donor_params)
        if target_stem_dir is not None and donor_stem_dir is not None and target_stem_dir != donor_stem_dir:
            return False

    return True


def semanticTransferScaleCandidatesImpl(
    base_scale: float,
    *,
    template_transfer_scale_candidates_fn: Callable[[float], list[float]],
) -> list[float]:
    """Broader scale ladder for semantic badge transfer exploration."""
    core = template_transfer_scale_candidates_fn(base_scale)
    extra = [0.55, 0.65, 0.75, 0.85, 1.00, 1.15, 1.30, 1.50, 1.75, 2.00]
    values = []
    seen: set[float] = set()
    for v in [*core, *extra]:
        value = float(min(2.2, max(0.5, float(v))))
        key = round(value, 4)
        if key in seen:
            continue
        seen.add(key)
        values.append(key)
    return values


def semanticTransferBadgeParamsImpl(
    donor_params: dict[str, object],
    target_params: dict[str, object],
    *,
    target_w: int,
    target_h: int,
    rotation_deg: int,
    scale: float,
    light_circle_fill_gray: int,
    light_circle_stroke_gray: int,
    light_circle_text_gray: int,
    clip_scalar_fn: Callable[[float, float, float], float],
    finalize_ac08_style_fn: Callable[[str, dict[str, object]], dict[str, object]],
) -> dict[str, object]:
    """Rotate/scale connector geometry around circle center while preserving upright text."""
    p = dict(donor_params)
    cx = float(p.get("cx", target_w / 2.0))
    cy = float(p.get("cy", target_h / 2.0))
    tx = float(target_params.get("cx", target_w / 2.0))
    ty = float(target_params.get("cy", target_h / 2.0))

    # Always carry essential rendering colors from target/donor/defaults.
    p["fill_gray"] = int(round(float(target_params.get("fill_gray", p.get("fill_gray", light_circle_fill_gray)))))
    p["stroke_gray"] = int(round(float(target_params.get("stroke_gray", p.get("stroke_gray", light_circle_stroke_gray)))))
    if bool(target_params.get("draw_text", p.get("draw_text", False))) or bool(p.get("draw_text", False)):
        p["text_gray"] = int(round(float(target_params.get("text_gray", p.get("text_gray", light_circle_text_gray)))))
    if bool(target_params.get("stem_enabled", p.get("stem_enabled", False))) or bool(p.get("stem_enabled", False)):
        p["stem_gray"] = int(round(float(target_params.get("stem_gray", p.get("stem_gray", p["stroke_gray"])))))

    # Prefer target anchor so center alignment remains stable between variants.
    p["cx"] = tx
    p["cy"] = ty

    if p.get("circle_enabled", True):
        p["r"] = max(1.0, float(p.get("r", 1.0)) * float(scale))

    angle = math.radians(float(rotation_deg))
    ca = math.cos(angle)
    sa = math.sin(angle)

    def _rot_scale_point(x: float, y: float) -> tuple[float, float]:
        dx = (x - cx) * float(scale)
        dy = (y - cy) * float(scale)
        rx = (dx * ca) - (dy * sa)
        ry = (dx * sa) + (dy * ca)
        return tx + rx, ty + ry

    if p.get("arm_enabled"):
        x1, y1 = _rot_scale_point(float(p.get("arm_x1", tx)), float(p.get("arm_y1", ty)))
        x2, y2 = _rot_scale_point(float(p.get("arm_x2", tx)), float(p.get("arm_y2", ty)))
        p["arm_x1"] = float(clip_scalar_fn(x1, 0.0, max(0.0, float(target_w - 1))))
        p["arm_y1"] = float(clip_scalar_fn(y1, 0.0, max(0.0, float(target_h - 1))))
        p["arm_x2"] = float(clip_scalar_fn(x2, 0.0, max(0.0, float(target_w - 1))))
        p["arm_y2"] = float(clip_scalar_fn(y2, 0.0, max(0.0, float(target_h - 1))))

    if p.get("stem_enabled"):
        stem_x = float(p.get("stem_x", tx)) + (float(p.get("stem_width", 1.0)) / 2.0)
        top = float(p.get("stem_top", ty))
        bottom = float(p.get("stem_bottom", ty))
        x1, y1 = _rot_scale_point(stem_x, top)
        x2, y2 = _rot_scale_point(stem_x, bottom)
        p["stem_x"] = float(
            clip_scalar_fn((x1 + x2) / 2.0 - (float(p.get("stem_width", 1.0)) / 2.0), 0.0, float(target_w))
        )
        p["stem_top"] = float(clip_scalar_fn(min(y1, y2), 0.0, float(target_h)))
        p["stem_bottom"] = float(clip_scalar_fn(max(y1, y2), 0.0, float(target_h)))

    if bool(p.get("draw_text", False)):
        text_scale = max(0.5, min(1.8, float(scale)))
        text_adjust = max(0.90, min(1.18, text_scale**0.38))
        if "s" in p:
            p["s"] = float(max(1e-4, float(p.get("s", 0.01)) * text_adjust))
        if "co2_font_scale" in p:
            p["co2_font_scale"] = float(max(0.30, float(p.get("co2_font_scale", 0.82)) * text_adjust))
        if "voc_font_scale" in p:
            p["voc_font_scale"] = float(max(0.30, float(p.get("voc_font_scale", 0.52)) * text_adjust))

    symbol_name = str(target_params.get("label") or target_params.get("variant") or target_params.get("base") or "")
    if symbol_name:
        p = finalize_ac08_style_fn(symbol_name, p)
    return p
