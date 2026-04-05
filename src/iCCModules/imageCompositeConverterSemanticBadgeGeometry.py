"""Semantic badge geometry helpers extracted from imageCompositeConverter."""

from __future__ import annotations


def rotateSemanticBadgeClockwiseImpl(params: dict, w: int, h: int) -> dict:
    cx = float(w) / 2.0
    cy = float(h) / 2.0

    def rotate_clockwise(x: float, y: float) -> tuple[float, float]:
        # image-space clockwise description maps to mathematically
        # counter-clockwise because y grows downward in raster coordinates.
        return cx - (y - cy), cy + (x - cx)

    rotated = dict(params)
    rotated["cx"], rotated["cy"] = rotate_clockwise(float(params["cx"]), float(params["cy"]))
    rotated["arm_x1"], rotated["arm_y1"] = rotate_clockwise(float(params["arm_x1"]), float(params["arm_y1"]))
    rotated["arm_x2"], rotated["arm_y2"] = rotate_clockwise(float(params["arm_x2"]), float(params["arm_y2"]))
    return rotated


def glyphBboxImpl(
    text_mode: str,
    *,
    t_xmin: int,
    t_ymin: int,
    t_xmax: int,
    t_ymax: int,
    m_xmin: int,
    m_ymin: int,
    m_xmax: int,
    m_ymax: int,
) -> tuple[int, int, int, int]:
    if text_mode == "path_t":
        return t_xmin, t_ymin, t_xmax, t_ymax
    return m_xmin, m_ymin, m_xmax, m_ymax


def centerGlyphBboxImpl(params: dict, *, glyph_bbox_fn) -> None:
    if "s" not in params or "cx" not in params or "cy" not in params:
        return
    xmin, ymin, xmax, ymax = glyph_bbox_fn(params.get("text_mode", "path"))
    glyph_width = (xmax - xmin) * params["s"]
    glyph_height = (ymax - ymin) * params["s"]
    params["tx"] = float(params["cx"] - (glyph_width / 2.0))
    params["ty"] = float(params["cy"] - (glyph_height / 2.0))
