"""AC08 small-variant semantic tuning helpers extracted from imageCompositeConverter."""

from __future__ import annotations

import math


def persistConnectorLengthFloorImpl(params: dict, element: str, default_ratio: float) -> None:
    """Persist a robust minimum connector length for later validation stages."""
    if element == "stem":
        length = float(params.get("stem_bottom", 0.0)) - float(params.get("stem_top", 0.0))
        min_key = "stem_len_min"
        ratio_key = "stem_len_min_ratio"
        template_length = float(params.get("template_stem_bottom", 0.0)) - float(
            params.get("template_stem_top", 0.0)
        )
    elif element == "arm":
        x1 = float(params.get("arm_x1", 0.0))
        y1 = float(params.get("arm_y1", 0.0))
        x2 = float(params.get("arm_x2", 0.0))
        y2 = float(params.get("arm_y2", 0.0))
        length = float(math.hypot(x2 - x1, y2 - y1))
        min_key = "arm_len_min"
        ratio_key = "arm_len_min_ratio"
        tx1 = float(params.get("template_arm_x1", x1))
        ty1 = float(params.get("template_arm_y1", y1))
        tx2 = float(params.get("template_arm_x2", x2))
        ty2 = float(params.get("template_arm_y2", y2))
        template_length = float(math.hypot(tx2 - tx1, ty2 - ty1))
    else:
        return

    if length <= 0.0:
        return

    ratio = float(max(0.0, min(1.0, float(params.get(ratio_key, default_ratio)))))
    params[ratio_key] = ratio
    params[min_key] = float(max(float(params.get(min_key, 1.0)), length * ratio, template_length * ratio, 1.0))


def isAc08SmallVariantImpl(name: str, params: dict) -> tuple[bool, str, float]:
    """Classify tiny AC08 variants so validation can use tighter `_S` heuristics."""
    normalized_name = str(name).upper()
    min_dim = float(min(float(params.get("width", 0.0) or 0.0), float(params.get("height", 0.0) or 0.0)))
    if min_dim <= 0.0:
        min_dim = max(1.0, float(params.get("r", 1.0)) * 2.0)

    variant_suffix = normalized_name.endswith("_S")
    dimension_small = min_dim <= 15.5
    is_small = variant_suffix or dimension_small
    if variant_suffix and dimension_small:
        reason = "variant_suffix+min_dim"
    elif variant_suffix:
        reason = "variant_suffix"
    elif dimension_small:
        reason = "min_dim"
    else:
        reason = "standard"
    return is_small, reason, min_dim


def configureAc08SmallVariantModeImpl(
    name: str,
    params: dict,
    *,
    is_ac08_small_variant_fn,
    persist_connector_length_floor_fn,
) -> dict:
    """Apply `_S`-specific AC08 tuning for text, connector floors, and masks."""
    p = dict(params)
    is_small, reason, min_dim = is_ac08_small_variant_fn(name, p)
    p["ac08_small_variant_mode"] = bool(is_small)
    p["ac08_small_variant_reason"] = reason
    p["ac08_small_variant_min_dim"] = float(min_dim)
    if not is_small:
        return p

    p["validation_mask_dilate_px"] = int(max(1, int(p.get("validation_mask_dilate_px", 1))))
    p["small_variant_antialias_bias"] = float(max(0.0, float(p.get("small_variant_antialias_bias", 0.08))))

    if p.get("arm_enabled"):
        p["arm_len_min_ratio"] = float(max(float(p.get("arm_len_min_ratio", 0.75)), 0.78))
        persist_connector_length_floor_fn(p, "arm", default_ratio=0.78)
    if p.get("stem_enabled"):
        p["stem_len_min_ratio"] = float(max(float(p.get("stem_len_min_ratio", 0.65)), 0.70))
        persist_connector_length_floor_fn(p, "stem", default_ratio=0.70)

    text_mode = str(p.get("text_mode", "")).lower()
    if text_mode == "co2":
        base_scale = float(p.get("co2_font_scale", 0.82))
        p["lock_text_scale"] = False
        p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.74, base_scale * 0.92)))
        p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.18)), min(1.10, base_scale * 1.12)))
        p["co2_subscript_offset_scale"] = float(min(float(p.get("co2_subscript_offset_scale", 0.24)), 0.24))
    elif text_mode == "voc":
        base_scale = float(p.get("voc_font_scale", 0.52))
        p["lock_text_scale"] = False
        p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.46, base_scale * 0.92)))
        p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.96)), min(0.96, base_scale * 1.10)))
    return p
