"""Geometry-IR helpers for deterministic composite symbol reconstruction."""

from __future__ import annotations

import html
import re
from collections.abc import Iterable


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def _has_any(text: str, tokens: Iterable[str]) -> bool:
    return any(token in text for token in tokens)


def buildGeometryIrFromDescriptionImpl(description: str) -> list[dict[str, object]]:
    """Map a normalized German image description to an ordered geometry IR chain.

    The IR intentionally stores normalized coordinates so later optimization can tune
    individual elements without depending on direct SVG snippets.
    """

    desc = _normalize_text(description)
    if not desc:
        return []

    elements: list[dict[str, object]] = []
    rect_hint = _has_any(desc, ("rechteck", "viereck", "kühlelement", "heizelement", "ac0120-bildbeschreibung"))
    gradient_hint = _has_any(desc, ("farbverlauf", "gradient")) and _has_any(desc, ("horizontal", "dunkel-hell-dunkel", "dunkel–hell–dunkel"))
    diagonal_hint = _has_any(desc, ("diagonal", "diagonale", "diagonalen", "andreaskreuz", "kreuz"))

    if gradient_hint:
        elements.append(
            {
                "kind": "HorizontalGradient",
                "id": "background_gradient",
                "bbox": [0.18, 0.24, 0.64, 0.56],
                "stops": ["#8f8f8f", "#dedede", "#8f8f8f"],
                "constraint": "inside_rect_border",
            }
        )

    if rect_hint:
        elements.append(
            {
                "kind": "RectBorder",
                "id": "main_rect",
                "bbox": [0.18, 0.24, 0.64, 0.56],
                "fill": "none" if gradient_hint else "#d8d8d8",
                "stroke": "#666666",
                "stroke_width": 0.035,
            }
        )

    directions: list[str] = []
    if diagonal_hint:
        both_diagonals = _has_any(desc, ("beiden diagonalen", "beide diagonalen", "andreaskreuz", "kreuz"))
        if both_diagonals or "ac0120-bildbeschreibung" in desc:
            directions = ["tl_br", "tr_bl"]
        elif re.search(r"oben\s+rechts.*unten\s+links|unten\s+links.*oben\s+rechts", desc):
            directions = ["tr_bl"]
        elif re.search(r"oben\s+links.*unten\s+rechts|unten\s+rechts.*oben\s+links", desc):
            directions = ["tl_br"]
        else:
            directions = ["tr_bl"]

    if _has_any(desc, ("zusätzliche", "zusätzlich", "dupliziert")) and "symmetrieachse" in desc and "tl_br" not in directions:
        directions.append("tl_br")

    for index, direction in enumerate(directions, start=1):
        elements.append(
            {
                "kind": "DiagonalBand",
                "id": f"diagonal_{index}_{direction}",
                "rect_ref": "main_rect",
                "direction": direction,
                "stroke": "#707070",
                "stroke_width": 0.045,
                "clip_to": "main_rect",
            }
        )

    glyph_position = "top_left" if "oben links" in desc else "top_center"
    has_plus = _has_any(desc, ("plus", "+", "plus-minus"))
    minus_count = len(re.findall(r'minus|["“]-["”]', desc))
    if has_plus:
        elements.append(
            {
                "kind": "PlusGlyph",
                "id": "plus_glyph",
                "position": glyph_position,
                "stroke": "#4f4f4f",
                "stroke_width": 0.025,
            }
        )
    if minus_count or _has_any(desc, ("plus-minus", "-zeichen")):
        elements.append(
            {
                "kind": "MinusGlyph",
                "id": "minus_glyph",
                "position": glyph_position,
                "stroke": "#4f4f4f",
                "stroke_width": 0.025,
            }
        )
        if "minus-minus" in desc:
            elements.append(
                {
                    "kind": "MinusGlyph",
                    "id": "minus_glyph_2",
                    "position": glyph_position,
                    "dy": 0.08,
                    "stroke": "#4f4f4f",
                    "stroke_width": 0.025,
                }
            )

    return elements


def _fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _scaled_bbox(element: dict[str, object], w: int, h: int) -> tuple[float, float, float, float]:
    raw_bbox = element.get("bbox", [0.18, 0.24, 0.64, 0.56])
    if not isinstance(raw_bbox, list) or len(raw_bbox) != 4:
        raw_bbox = [0.18, 0.24, 0.64, 0.56]
    x, y, bw, bh = [float(v) for v in raw_bbox]
    return x * w, y * h, bw * w, bh * h


def _find_rect(elements: list[dict[str, object]], w: int, h: int) -> tuple[float, float, float, float]:
    for element in elements:
        if element.get("kind") == "RectBorder":
            return _scaled_bbox(element, w, h)
    return 0.18 * w, 0.24 * h, 0.64 * w, 0.56 * h


def renderGeometryIrToSvgElementsImpl(w: int, h: int, geometry_ir: list[dict[str, object]]) -> list[str]:
    """Render geometry IR elements as SVG fragments in their declared order."""

    svg: list[str] = []
    rect_x, rect_y, rect_w, rect_h = _find_rect(geometry_ir, w, h)
    needs_gradient = any(element.get("kind") == "HorizontalGradient" for element in geometry_ir)
    if needs_gradient:
        svg.append("  <defs>")
        svg.append('    <linearGradient id="geometry-ir-horizontal-gradient" x1="0%" y1="0%" x2="100%" y2="0%">')
        svg.append('      <stop offset="0%" stop-color="#8f8f8f"/>')
        svg.append('      <stop offset="50%" stop-color="#dedede"/>')
        svg.append('      <stop offset="100%" stop-color="#8f8f8f"/>')
        svg.append("    </linearGradient>")
        svg.append("  </defs>")

    for element in geometry_ir:
        kind = str(element.get("kind", ""))
        element_id = html.escape(str(element.get("id", kind)))
        if kind == "HorizontalGradient":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            svg.append(
                f'  <rect id="{element_id}" x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(bw)}" height="{_fmt(bh)}" '
                'fill="url(#geometry-ir-horizontal-gradient)" stroke="none"/>'
            )
        elif kind == "RectBorder":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            fill = html.escape(str(element.get("fill", "none")))
            stroke = html.escape(str(element.get("stroke", "#666666")))
            sw = float(element.get("stroke_width", 0.035)) * min(w, h)
            svg.append(
                f'  <rect id="{element_id}" x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(bw)}" height="{_fmt(bh)}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
            )
        elif kind == "DiagonalBand":
            stroke = html.escape(str(element.get("stroke", "#707070")))
            sw = float(element.get("stroke_width", 0.045)) * min(w, h)
            direction = str(element.get("direction", "tr_bl"))
            inset = sw * 0.5
            if direction == "tl_br":
                x0, y0, x1, y1 = rect_x + inset, rect_y + inset, rect_x + rect_w - inset, rect_y + rect_h - inset
            else:
                x0, y0, x1, y1 = rect_x + rect_w - inset, rect_y + inset, rect_x + inset, rect_y + rect_h - inset
            svg.append(
                f'  <path id="{element_id}" d="M {_fmt(x0)} {_fmt(y0)} L {_fmt(x1)} {_fmt(y1)}" '
                f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="butt"/>'
            )
        elif kind in {"PlusGlyph", "MinusGlyph"}:
            stroke = html.escape(str(element.get("stroke", "#4f4f4f")))
            sw = float(element.get("stroke_width", 0.025)) * min(w, h)
            pos = str(element.get("position", "top_center"))
            dy = float(element.get("dy", 0.0)) * h
            if pos == "top_left":
                cx, cy = rect_x + rect_w * 0.18, rect_y - h * 0.08 + dy
            else:
                cx, cy = rect_x + rect_w * 0.50, rect_y - h * 0.08 + dy
            half = min(w, h) * 0.055
            if kind == "PlusGlyph":
                svg.append(
                    f'  <path id="{element_id}" d="M {_fmt(cx-half)} {_fmt(cy)} L {_fmt(cx+half)} {_fmt(cy)} '
                    f'M {_fmt(cx)} {_fmt(cy-half)} L {_fmt(cx)} {_fmt(cy+half)}" '
                    f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="square"/>'
                )
            else:
                svg.append(
                    f'  <path id="{element_id}" d="M {_fmt(cx-half)} {_fmt(cy)} L {_fmt(cx+half)} {_fmt(cy)}" '
                    f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="square"/>'
                )
    return svg


def renderGeometryIrToSvgImpl(w: int, h: int, geometry_ir: list[dict[str, object]]) -> str:
    svg = [
        (
            f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">'
        )
    ]
    svg.extend(renderGeometryIrToSvgElementsImpl(w, h, geometry_ir))
    svg.append("</svg>")
    return "\n".join(svg)
