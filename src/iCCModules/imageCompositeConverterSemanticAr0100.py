"""AR0100 semantic badge-parameter helpers extracted from the converter monolith."""

from __future__ import annotations


def buildAr0100BadgeParamsImpl(
    w: int,
    h: int,
    *,
    ar0100_base: dict,
    center_glyph_bbox_fn,
) -> dict:
    """Build AR0100 default badge params with scale-adapted geometry and centered glyph bbox."""
    scale = min(w, h) / 25.0 if min(w, h) > 0 else 1.0
    b = ar0100_base
    params = {
        "cx": b["cx"] * scale,
        "cy": b["cy"] * scale,
        "r": b["r"] * scale,
        "stroke_circle": b["stroke_width"] * scale,
        "fill_gray": b["fill_gray"],
        "stroke_gray": b["stroke_gray"],
        "text_gray": b["text_gray"],
        "tx": b["tx"] * scale,
        "ty": b["ty"] * scale,
        "s": b["s"] * scale,
        "label": "M",
        "text_mode": "path",
    }
    center_glyph_bbox_fn(params)
    return params
