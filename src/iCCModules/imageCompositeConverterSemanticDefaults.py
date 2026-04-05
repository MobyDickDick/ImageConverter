"""Default semantic AC08 parameter helpers extracted from imageCompositeConverter."""

from __future__ import annotations


def defaultAc0870ParamsImpl(
    w: int,
    h: int,
    *,
    ac0870_base: dict[str, float | int | str],
    center_glyph_bbox,
    normalize_light_circle_colors,
) -> dict:
    scale = min(w, h) / 30.0 if min(w, h) > 0 else 1.0
    b = ac0870_base
    params = {
        "cx": float(b["cx"]) * scale,
        "cy": float(b["cy"]) * scale,
        "r": float(b["r"]) * scale,
        "stroke_circle": float(b["stroke_width"]) * scale,
        "fill_gray": int(b["fill_gray"]),
        "stroke_gray": int(b["stroke_gray"]),
        "text_gray": int(b["text_gray"]),
        "label": str(b["label"]),
        "tx": 8.7 * scale,
        "ty": 6.5 * scale,
        "s": 0.0100 * scale,
        "text_mode": "path_t",
    }
    center_glyph_bbox(params)
    return normalize_light_circle_colors(params)


def defaultAc0881ParamsImpl(w: int, h: int, *, default_ac0870_params) -> dict:
    params = default_ac0870_params(w, h)
    params["stem_enabled"] = True
    params["stem_width"] = max(1.0, params["r"] * 0.30)
    params["stem_x"] = params["cx"] - (params["stem_width"] / 2.0)
    params["stem_top"] = params["cy"] + (params["r"] * 0.60)
    params["stem_bottom"] = float(h)
    params["stem_gray"] = params["stroke_gray"]
    return params


def defaultAc0882ParamsImpl(
    w: int,
    h: int,
    *,
    default_ac081x_shared,
    center_glyph_bbox,
) -> dict:
    params = default_ac081x_shared(w, h)
    arm_x2 = params["cx"] - params["r"]
    arm_x1 = max(0.0, arm_x2 - params["stem_or_arm_len"])
    params.update(
        {
            "text_gray": 98,
            "label": "T",
            "text_mode": "path_t",
            "arm_enabled": True,
            "arm_x1": arm_x1,
            "arm_y1": params["cy"],
            "arm_x2": arm_x2,
            "arm_y2": params["cy"],
            "arm_stroke": params["stem_or_arm"],
            "s": 0.0088 * min(1.0, (min(w, h) / 25.0)) if min(w, h) > 0 else 0.0088,
        }
    )
    center_glyph_bbox(params)
    return params
