"""Semantic label helper functions extracted from imageCompositeConverter."""

from __future__ import annotations


def applyCo2LabelImpl(
    params: dict,
    *,
    light_circle_stroke_gray: int,
    semantic_text_base_scale: float,
) -> dict:
    params["draw_text"] = True
    params["text_mode"] = "co2"
    params["text_gray"] = int(round(params.get("stroke_gray", light_circle_stroke_gray)))
    params["co2_font_scale"] = float(params.get("co2_font_scale", 0.82 * semantic_text_base_scale))
    params["co2_sub_font_scale"] = float(params.get("co2_sub_font_scale", 66.0))
    params["co2_dx"] = float(params.get("co2_dx", 0.0))
    params["co2_dy"] = float(params.get("co2_dy", 0.0))
    params["co2_inner_padding_px"] = float(params.get("co2_inner_padding_px", 0.35))
    params["co2_width_scale"] = float(params.get("co2_width_scale", 1.0))
    params["co2_anchor_mode"] = str(params.get("co2_anchor_mode", "center_co"))
    params["co2_index_mode"] = str(params.get("co2_index_mode", "subscript"))
    return params


def co2LayoutImpl(params: dict) -> dict[str, float | str]:
    """Compute renderer-independent CO₂ text metrics and placement."""
    cx = float(params.get("cx", 0.0))
    cy = float(params.get("cy", 0.0))
    r = max(1.0, float(params.get("r", 1.0)))
    stroke = max(0.8, float(params.get("stroke_circle", 1.0)))
    inner_diameter = max(2.0, (2.0 * r) - stroke)
    requested_font_size = max(4.0, r * float(params.get("co2_font_scale", 0.82)))
    max_font_size = max(
        4.0,
        inner_diameter * float(params.get("co2_max_inner_diameter_ratio", 0.50)),
    )
    inner_padding = max(0.0, float(params.get("co2_inner_padding_px", 0.35)))
    clear_span = max(1.0, inner_diameter - (2.0 * inner_padding))
    sub_scale = float(params.get("co2_sub_font_scale", 66.0))
    sub_ratio = max(0.20, sub_scale / 100.0)
    cluster_factor = 1.04 + 0.03 + (0.62 * sub_ratio)
    width_limited_font = clear_span / max(0.001, cluster_factor)
    height_limited_font = clear_span / max(0.95, 0.95 + (0.24 * sub_ratio) + (0.35 * sub_ratio))
    auto_font_size = min(width_limited_font, height_limited_font)
    font_size = min(max_font_size, max(requested_font_size, auto_font_size))
    sub_font_px = max(4.0, font_size * (sub_scale / 100.0))
    anchor_mode = str(params.get("co2_anchor_mode", "center_co")).lower()
    index_mode = str(params.get("co2_index_mode", "subscript")).lower()

    width_scale = float(params.get("co2_width_scale", 1.0))
    width_scale = float(max(0.78, min(1.12, width_scale)))
    symbol_hint = str(params.get("badge_symbol_name", "")).upper()
    if not symbol_hint:
        symbol_hint = str(params.get("variant_name", "")).upper().split("_", 1)[0]
    if symbol_hint == "AC0820":
        if r >= 10.0:
            width_scale = min(width_scale, 0.90)
        elif r >= 6.0:
            width_scale = min(width_scale, 0.92)
        else:
            width_scale = min(width_scale, 0.94)

    co_width = (font_size * 1.04) * width_scale
    gap = font_size * 0.03
    if index_mode == "superscript":
        superscript_min_gap = font_size * float(params.get("co2_superscript_min_gap_scale", 0.130))
        gap = max(gap, superscript_min_gap)
    sub_w = (sub_font_px * 0.62) * width_scale

    if anchor_mode in {"cluster", "co"}:
        cluster_shift = (gap + sub_w) / 2.0
        co_x = (cx + float(params.get("co2_dx", 0.0))) - cluster_shift
        x1 = co_x - (co_width / 2.0)
        subscript_x = co_x + (co_width / 2.0) + gap
        x2 = subscript_x + sub_w
    else:
        visual_sub_w = (sub_font_px * float(params.get("co2_subscript_visual_width_factor", 0.62))) * width_scale
        visual_cluster_shift = (gap + visual_sub_w) / 2.0
        center_co_bias = float(params.get("co2_center_co_bias", 0.0))
        co_x = (cx + float(params.get("co2_dx", 0.0))) + (visual_cluster_shift * center_co_bias)
        x1 = co_x - (co_width / 2.0)

        local_gap = gap
        local_sub_font_px = sub_font_px
        local_sub_w = sub_w
        subscript_x = co_x + (co_width / 2.0) + local_gap
        x2 = subscript_x + local_sub_w

        stroke = max(0.8, float(params.get("stroke_circle", 1.0)))
        inner_right = cx + max(1.0, r - stroke) - inner_padding
        inner_left = cx - max(1.0, r - stroke) + inner_padding

        overflow = x2 - inner_right
        if overflow > 0.0:
            min_gap = font_size * 0.005
            if index_mode == "superscript":
                min_gap = max(
                    min_gap,
                    font_size * float(params.get("co2_superscript_min_gap_scale", 0.130)),
                )
            shrink_gap = min(overflow, max(0.0, local_gap - min_gap))
            local_gap -= shrink_gap
            overflow -= shrink_gap

            if overflow > 0.0:
                min_sub_font_px = max(4.0, font_size * 0.42)
                max_shrink_px = max(0.0, local_sub_font_px - min_sub_font_px)
                shrink_px = min(max_shrink_px, overflow / 0.62)
                local_sub_font_px -= shrink_px
                local_sub_w = (local_sub_font_px * 0.62) * width_scale

            sub_font_px = local_sub_font_px
            subscript_x = co_x + (co_width / 2.0) + local_gap
            x2 = subscript_x + local_sub_w

            overflow = x2 - inner_right
            if overflow > 0.0:
                co_x -= overflow
                x1 -= overflow
                subscript_x -= overflow
                x2 -= overflow

        left_overflow = inner_left - x1
        if left_overflow > 0.0:
            co_x += left_overflow
            x1 += left_overflow
            subscript_x += left_overflow
            x2 += left_overflow

    optical_bias = float(params.get("co2_optical_bias", 0.090 + (0.015 * min(1.0, r / 12.0))))
    y_base = cy + float(params.get("co2_dy", 0.0)) + (font_size * optical_bias)
    subscript_offset = font_size * float(params.get("co2_subscript_offset_scale", 0.18))
    height = font_size * 0.95

    stroke = max(0.8, float(params.get("stroke_circle", 1.0)))
    inner_top = cy - max(1.0, r - stroke)
    inner_bottom = cy + max(1.0, r - stroke)
    top = y_base - (height / 2.0)
    bottom = y_base + (height / 2.0)
    if top < inner_top:
        delta = inner_top - top
        y_base += delta
    elif bottom > inner_bottom:
        delta = bottom - inner_bottom
        y_base -= delta

    if index_mode == "superscript":
        min_index_offset = font_size * 0.10
        max_index_offset = font_size * 0.34
        index_offset = float(max(min_index_offset, min(max_index_offset, font_size * float(params.get("co2_superscript_offset_scale", 0.22)))))
        subscript_y = y_base - index_offset
        sub_top = subscript_y - (sub_font_px * 0.60)
        if sub_top < inner_top:
            max_offset = max(min_index_offset, y_base - inner_top - (sub_font_px * 0.60))
            index_offset = float(max(min_index_offset, min(max_index_offset, max_offset)))
            subscript_y = y_base - index_offset
        sub_bottom = subscript_y + (sub_font_px * 0.35)
        if sub_bottom > inner_bottom:
            min_offset = y_base - inner_bottom + (sub_font_px * 0.35)
            index_offset = float(max(min_index_offset, min(max_index_offset, min_offset)))
            subscript_y = y_base - index_offset
    else:
        min_subscript_offset = font_size * 0.08
        max_subscript_offset = font_size * 0.24
        subscript_offset = float(max(min_subscript_offset, min(max_subscript_offset, subscript_offset)))
        subscript_y = y_base + subscript_offset
        sub_bottom = subscript_y + (sub_font_px * 0.35)
        if sub_bottom > inner_bottom:
            max_offset = inner_bottom - y_base - (sub_font_px * 0.35)
            subscript_offset = float(max(min_subscript_offset, min(max_subscript_offset, max_offset)))
            subscript_y = y_base + subscript_offset

        sub_top = subscript_y - (sub_font_px * 0.60)
        if sub_top < inner_top:
            min_offset = inner_top - y_base + (sub_font_px * 0.60)
            subscript_offset = float(max(min_subscript_offset, min(max_subscript_offset, min_offset)))
            subscript_y = y_base + subscript_offset

    return {
        "anchor_mode": anchor_mode,
        "index_mode": index_mode,
        "width_scale": width_scale,
        "font_size": font_size,
        "sub_scale": sub_scale,
        "sub_font_px": sub_font_px,
        "co_x": co_x,
        "y_base": y_base,
        "subscript_x": subscript_x,
        "subscript_y": subscript_y,
        "x1": x1,
        "x2": x2,
        "height": height,
    }


def applyVocLabelImpl(
    params: dict,
    *,
    light_circle_stroke_gray: int,
    semantic_text_base_scale: float,
) -> dict:
    params["draw_text"] = True
    params["text_mode"] = "voc"
    params["text_gray"] = int(round(params.get("stroke_gray", light_circle_stroke_gray)))
    params["voc_font_scale"] = float(params.get("voc_font_scale", 0.52 * semantic_text_base_scale))
    params["voc_dy"] = float(params.get("voc_dy", -0.01 * float(params.get("r", 0.0))))
    params["voc_weight"] = int(params.get("voc_weight", 600))
    return params


def normalizeCenteredCo2LabelImpl(params: dict) -> dict:
    """Normalize CO₂ label sizing for plain circular badges."""
    p = dict(params)
    if str(p.get("text_mode", "")).lower() != "co2":
        return p
    if p.get("arm_enabled") or p.get("stem_enabled"):
        return p
    if not p.get("circle_enabled", True):
        return p

    r = max(1.0, float(p.get("r", 1.0)))
    stroke = max(0.8, float(p.get("stroke_circle", 1.0)))
    inner_diameter = max(2.0, (2.0 * r) - stroke)

    cur_scale = float(p.get("co2_font_scale", 0.82))
    cur_font = max(4.0, r * cur_scale)
    cur_width = cur_font * 1.45
    target_width = inner_diameter * 0.68

    adjusted_scale = cur_scale * (target_width / max(1e-6, cur_width))
    min_scale = 0.72 if r >= 8.0 else 0.74
    p["co2_font_scale"] = float(max(min_scale, min(0.96, adjusted_scale)))
    p["co2_sub_font_scale"] = float(max(60.0, min(68.0, float(p.get("co2_sub_font_scale", 66.0)))))
    p["co2_dx"] = float(max(-0.18 * r, min(0.18 * r, float(p.get("co2_dx", -0.04 * r)))))
    p["co2_dy"] = float(max(-0.20 * r, min(0.20 * r, float(p.get("co2_dy", 0.03 * r)))))
    p["text_gray"] = int(round(p.get("stroke_gray", p.get("text_gray", 0))))
    return p
