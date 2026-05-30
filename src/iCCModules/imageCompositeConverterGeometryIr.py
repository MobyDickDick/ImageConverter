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
    differential_pressure_hint = _has_any(desc, ("differenzdruckmessung", "dp")) and "doppelten grauen rand" in desc
    compressor_hint = _has_any(desc, ("kompressor", "kopressor"))
    upward_compressor_hint = compressor_hint and _has_any(desc, ("nach oben", "oben", "aufwärts", "aufwaerts"))
    grey_background_compressor_hint = upward_compressor_hint and _has_any(
        desc, ("grauer hintergrund", "grauem hintergrund", "grau hintergrund")
    )
    rightward_compressor_hint = compressor_hint and _has_any(desc, ("nach rechts", "rechts"))
    main_diagonal_mirrored_compressor_hint = rightward_compressor_hint and _has_any(
        desc, ("hauptdiagonal gespiegelt", "diagonal gespiegelt", "gespiegelt")
    )
    two_way_vertical_valve_hint = _has_any(desc, ("2-weg ventil", "2 weg ventil")) and _has_any(
        desc, ("kelle mit kreis", "horizontale verbindungslinie", "zwei spitze dreiecke")
    )
    left_rotated_two_way_valve_hint = two_way_vertical_valve_hint and _has_any(
        desc, ("90° nach links", "90° links", "90 grad nach links", "nach links gedreht")
    )
    rotated_180_two_way_valve_hint = two_way_vertical_valve_hint and _has_any(
        desc, ("180° gedreht", "180 grad gedreht", "um 180°", "um 180 grad")
    )
    top_kelle_three_way_valve_hint = _has_any(desc, ("ac0231", "3-weg ventil", "3 wege ventil", "3. spitzes dreieck")) and _has_any(
        desc, ("ohne \"m\"", "ohne 'm'", "ohne m", "kein \"m\"", "kein m")
    ) and _has_any(desc, ("kelle oben", "kreis oben", "kelle mit kreis", "symmetrieachse des kreises"))

    if top_kelle_three_way_valve_hint:
        elements.append(
            {
                "kind": "TopKelleThreeWayValveGlyph",
                "id": "top_kelle_three_way_valve",
                "body_paths": [
                    [[0.500, 0.610], [0.020, 0.455], [0.020, 0.765]],
                    [[0.500, 0.610], [0.980, 0.455], [0.980, 0.765]],
                    [[0.500, 0.610], [0.333, 0.960], [0.667, 0.960]],
                ],
                "circle": [0.500, 0.235, 0.225],
                "connector": [[0.500, 0.450], [0.500, 0.610]],
                "label": "",
                "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                "stroke": "#969696",
                "connector_stroke": "#8f8f8f",
                "text_fill": "#666666",
                "stroke_width": 0.040,
                "connector_width": 0.075,
            }
        )
        return elements

    if two_way_vertical_valve_hint:
        if rotated_180_two_way_valve_hint:
            elements.append(
                {
                    "kind": "Rotated180TwoWayValveMotorGlyph",
                    "id": "rotated_180_two_way_valve_motor",
                    "body_path": [
                        [0.975, 0.980],
                        [0.616, 0.980],
                        [0.793, 0.491],
                        [0.616, 0.020],
                        [0.975, 0.020],
                        [0.793, 0.491],
                    ],
                    "circle": [0.279, 0.499, 0.263],
                    "connector": [[0.787, 0.499], [0.540, 0.499]],
                    "label": "M",
                    "label_center": [0.279, 0.593],
                    "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                    "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                    "stroke": "#969696",
                    "connector_stroke": "#8f8f8f",
                    "text_fill": "#666666",
                    "stroke_width": 0.040,
                    "connector_width": 0.060,
                    "font_size": 0.540,
                    "font_weight": "700",
                }
            )
            return elements
        if left_rotated_two_way_valve_hint:
            elements.append(
                {
                    "kind": "LeftRotatedTwoWayValveMotorGlyph",
                    "id": "left_rotated_two_way_valve_motor",
                    "body_path": [
                        [0.980, 0.025],
                        [0.980, 0.384],
                        [0.491, 0.207],
                        [0.020, 0.384],
                        [0.020, 0.025],
                        [0.491, 0.207],
                    ],
                    "circle": [0.499, 0.721, 0.263],
                    "connector": [[0.499, 0.213], [0.499, 0.460]],
                    "label": "M",
                    "label_center": [0.499, 0.815],
                    "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                    "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                    "stroke": "#969696",
                    "connector_stroke": "#8f8f8f",
                    "text_fill": "#666666",
                    "stroke_width": 0.040,
                    "connector_width": 0.060,
                    "font_size": 0.415,
                    "font_weight": "700",
                }
            )
            return elements
        elements.append(
            {
                "kind": "VerticalTwoWayValveMotorGlyph",
                "id": "vertical_two_way_valve_motor",
                "body_path": [[0.025, 0.020], [0.384, 0.020], [0.207, 0.509], [0.384, 0.980], [0.025, 0.980], [0.207, 0.509]],
                "circle": [0.721, 0.501, 0.263],
                "connector": [[0.213, 0.501], [0.460, 0.501]],
                "label": "M",
                "label_center": [0.721, 0.595],
                "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                "stroke": "#969696",
                "connector_stroke": "#8f8f8f",
                "text_fill": "#666666",
                "stroke_width": 0.040,
                "connector_width": 0.060,
                "font_size": 0.540,
                "font_weight": "700",
            }
        )
        return elements

    if upward_compressor_hint:
        circle_fill = "#d8d8d8" if grey_background_compressor_hint else "#45aa5e"
        glyph_stroke = "#666666" if grey_background_compressor_hint else "#d7d7d7"
        elements.extend(
            [
                {
                    "kind": "CircleBackground",
                    "id": "compressor_circle",
                    "bbox": [0.06, 0.06, 0.88, 0.88],
                    "fill": circle_fill,
                    "stroke": "#8d8d8d",
                    "stroke_width": 0.020,
                },
                {
                    "kind": "UpwardCompressorGlyph",
                    "id": "upward_compressor",
                    "circle_ref": "compressor_circle",
                    "left_line": [[0.28, 0.78], [0.42, 0.16]],
                    "right_line": [[0.72, 0.78], [0.58, 0.16]],
                    "stroke": glyph_stroke,
                    "stroke_width": 0.040,
                },
            ]
        )
        return elements

    if main_diagonal_mirrored_compressor_hint:
        elements.extend(
            [
                {
                    "kind": "CircleBackground",
                    "id": "compressor_circle",
                    "bbox": [0.06, 0.06, 0.88, 0.88],
                    "fill": "#df2249",
                    "stroke": "#8d8d8d",
                    "stroke_width": 0.020,
                },
                {
                    "kind": "MainDiagonalMirroredCompressorGlyph",
                    "id": "main_diagonal_mirrored_compressor",
                    "circle_ref": "compressor_circle",
                    "left_line": [[0.09, 0.22], [0.39, 1.01]],
                    "right_line": [[0.91, 0.22], [0.61, 1.01]],
                    "stroke": "#f4f4f4",
                    "stroke_width": 0.032,
                },
            ]
        )
        return elements

    if rightward_compressor_hint:
        elements.extend(
            [
                {
                    "kind": "CircleBackground",
                    "id": "compressor_circle",
                    "bbox": [0.06, 0.06, 0.88, 0.88],
                    "fill": "#45aa5e",
                    "stroke": "#8d8d8d",
                    "stroke_width": 0.020,
                },
                {
                    "kind": "RightwardCompressorGlyph",
                    "id": "rightward_compressor",
                    "circle_ref": "compressor_circle",
                    "upper_line": [[0.22, 0.09], [1.01, 0.39]],
                    "lower_line": [[0.22, 0.91], [1.01, 0.61]],
                    "stroke": "#f4f4f4",
                    "stroke_width": 0.032,
                },
            ]
        )
        return elements

    if differential_pressure_hint:
        elements.extend(
            [
                {
                    "kind": "HalfDoubleRectBorder",
                    "id": "half_double_rect",
                    "bbox": [0.22, 0.38, 0.56, 0.34],
                    "fill": "none",
                    "stroke": "#777777",
                    "stroke_width": 0.024,
                    "inner_inset": 0.075,
                    "open_side": "left",
                },
                {
                    "kind": "LabelBox",
                    "id": "dp_label_box",
                    "bbox": [0.35, 0.16, 0.30, 0.20],
                    "fill": "#d7d7d7",
                    "stroke": "#777777",
                    "stroke_width": 0.020,
                },
                {
                    "kind": "TextGlyph",
                    "id": "dp_label_text",
                    "text": "dp",
                    "bbox_ref": "dp_label_box",
                    "fill": "#555555",
                    "font_size": 0.105,
                    "font_weight": "600",
                },
            ]
        )
        return elements

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

    if rect_hint and "hochkant" in desc:
        for element in elements:
            if element.get("kind") == "HorizontalGradient":
                element["bbox"] = [0.32, 0.12, 0.36, 0.76]

    if rect_hint:
        rect_bbox = [0.32, 0.12, 0.36, 0.76] if "hochkant" in desc else [0.18, 0.24, 0.64, 0.56]
        elements.append(
            {
                "kind": "RectBorder",
                "id": "main_rect",
                "bbox": rect_bbox,
                "fill": "none" if gradient_hint else "#d8d8d8",
                "stroke": "#666666",
                "stroke_width": 0.035,
            }
        )

    has_horizontal_rules = _has_any(desc, ("horizontale linien", "horizontallinien")) or re.search(
        r"\bdrei\s+graue\s+horizontale\s+linien", desc
    )
    if has_horizontal_rules:
        elements.append(
            {
                "kind": "HorizontalRuleSet",
                "id": "horizontal_rule_set",
                "rect_ref": "main_rect",
                "positions": [0.30, 0.50, 0.70],
                "stroke": "#707070",
                "stroke_width": 0.026,
                "x_inset": 0.10,
            }
        )

    if re.search(r"oben[-\s]*mitte.*rechts[-\s]*mitte.*unten[-\s]*mitte", desc):
        elements.append(
            {
                "kind": "OrthogonalPolyline",
                "id": "right_side_orthogonal_line",
                "rect_ref": "main_rect",
                "points": [[0.50, 0.02], [1.02, 0.50], [0.50, 0.98]],
                "stroke": "#707070",
                "stroke_width": 0.034,
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


def _find_circle(elements: list[dict[str, object]], circle_id: str, w: int, h: int) -> tuple[float, float, float, float]:
    for element in elements:
        if element.get("kind") == "CircleBackground" and str(element.get("id", "")) == circle_id:
            return _scaled_bbox(element, w, h)
    for element in elements:
        if element.get("kind") == "CircleBackground":
            return _scaled_bbox(element, w, h)
    return 0.06 * w, 0.06 * h, 0.88 * w, 0.88 * h


def renderGeometryIrToSvgElementsImpl(w: int, h: int, geometry_ir: list[dict[str, object]]) -> list[str]:
    """Render geometry IR elements as SVG fragments in their declared order."""

    svg: list[str] = []
    rect_x, rect_y, rect_w, rect_h = _find_rect(geometry_ir, w, h)
    needs_gradient = any(element.get("kind") == "HorizontalGradient" for element in geometry_ir)
    valve_gradient_kinds = {
        "VerticalTwoWayValveMotorGlyph",
        "LeftRotatedTwoWayValveMotorGlyph",
        "Rotated180TwoWayValveMotorGlyph",
        "TopKelleThreeWayValveGlyph",
    }
    needs_vertical_valve_defs = any(element.get("kind") in valve_gradient_kinds for element in geometry_ir)
    if needs_gradient or needs_vertical_valve_defs:
        svg.append("  <defs>")
        if needs_gradient:
            svg.append('    <linearGradient id="geometry-ir-horizontal-gradient" x1="0%" y1="0%" x2="100%" y2="0%">')
            svg.append('      <stop offset="0%" stop-color="#8f8f8f"/>')
            svg.append('      <stop offset="50%" stop-color="#dedede"/>')
            svg.append('      <stop offset="100%" stop-color="#8f8f8f"/>')
            svg.append("    </linearGradient>")
        if needs_vertical_valve_defs:
            svg.append('    <linearGradient id="vertical-two-way-valve-body-gradient" x1="0%" y1="0%" x2="100%" y2="100%">')
            svg.append('      <stop offset="0%" stop-color="#a8a8a8"/>')
            svg.append('      <stop offset="100%" stop-color="#fbfbfb"/>')
            svg.append("    </linearGradient>")
            svg.append('    <linearGradient id="vertical-two-way-valve-circle-gradient" x1="0%" y1="0%" x2="100%" y2="100%">')
            svg.append('      <stop offset="0%" stop-color="#ffffff"/>')
            svg.append('      <stop offset="100%" stop-color="#f7f7f7"/>')
            svg.append("    </linearGradient>")
        svg.append("  </defs>")

    for element in geometry_ir:
        kind = str(element.get("kind", ""))
        element_id = html.escape(str(element.get("id", kind)))
        if kind in valve_gradient_kinds:
            stroke = html.escape(str(element.get("stroke", "#969696")))
            connector_stroke = html.escape(str(element.get("connector_stroke", "#8f8f8f")))
            text_fill = html.escape(str(element.get("text_fill", "#666666")))
            body_fill = html.escape(str(element.get("body_fill", "url(#vertical-two-way-valve-body-gradient)")))
            circle_fill = html.escape(str(element.get("circle_fill", "url(#vertical-two-way-valve-circle-gradient)")))
            sw = float(element.get("stroke_width", 0.040)) * min(w, h)
            connector_sw = float(element.get("connector_width", 0.060)) * min(w, h)
            raw_connector = element.get("connector", [[0.213, 0.501], [0.460, 0.501]])
            if isinstance(raw_connector, list) and len(raw_connector) == 2:
                points = []
                for raw_point in raw_connector:
                    if isinstance(raw_point, list) and len(raw_point) == 2:
                        points.append((float(raw_point[0]) * w, float(raw_point[1]) * h))
                if len(points) == 2:
                    (x0, y0), (x1, y1) = points
                    svg.append(
                        f'  <path id="{element_id}_connector" d="M {_fmt(x0)} {_fmt(y0)} L {_fmt(x1)} {_fmt(y1)}" '
                        f'stroke="{connector_stroke}" stroke-width="{_fmt(connector_sw)}" fill="none" stroke-linecap="butt"/>'
                    )
            raw_body_paths = element.get("body_paths")
            body_path_groups = raw_body_paths if isinstance(raw_body_paths, list) else [element.get("body_path", [])]
            for body_idx, raw_body in enumerate(body_path_groups, start=1):
                body_points: list[str] = []
                if isinstance(raw_body, list):
                    for raw_point in raw_body:
                        if isinstance(raw_point, list) and len(raw_point) == 2:
                            body_points.append(f"{_fmt(float(raw_point[0]) * w)} {_fmt(float(raw_point[1]) * h)}")
                if body_points:
                    body_id = f"{element_id}_body" if len(body_path_groups) == 1 else f"{element_id}_body_{body_idx}"
                    svg.append(
                        f'  <path id="{body_id}" d="M {" L ".join(body_points)} Z" '
                        f'fill="{body_fill}" stroke="{stroke}" stroke-width="{_fmt(sw)}" stroke-linejoin="miter"/>'
                    )
            raw_circle = element.get("circle", [0.721, 0.501, 0.263])
            if isinstance(raw_circle, list) and len(raw_circle) == 3:
                cx, cy, radius = [float(value) for value in raw_circle]
                svg.append(
                    f'  <circle id="{element_id}_circle" cx="{_fmt(cx * w)}" cy="{_fmt(cy * h)}" '
                    f'r="{_fmt(radius * min(w, h))}" fill="{circle_fill}" stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
                )
            label = html.escape(str(element.get("label", "M")))
            raw_label_center = element.get("label_center", [0.721, 0.595])
            if label and isinstance(raw_label_center, list) and len(raw_label_center) == 2:
                font_size = float(element.get("font_size", 0.540)) * min(w, h)
                font_weight = html.escape(str(element.get("font_weight", "700")))
                svg.append(
                    f'  <text id="{element_id}_label" x="{_fmt(float(raw_label_center[0]) * w)}" '
                    f'y="{_fmt(float(raw_label_center[1]) * h)}" fill="{text_fill}" '
                    f'font-family="Arial, Helvetica, sans-serif" font-size="{_fmt(font_size)}" font-weight="{font_weight}" '
                    f'text-anchor="middle" dominant-baseline="middle">{label}</text>'
                )
        elif kind == "CircleBackground":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            fill = html.escape(str(element.get("fill", "#45aa5e")))
            stroke = html.escape(str(element.get("stroke", "#8d8d8d")))
            sw = float(element.get("stroke_width", 0.020)) * min(w, h)
            svg.append(
                f'  <ellipse id="{element_id}" cx="{_fmt(x + bw * 0.5)}" cy="{_fmt(y + bh * 0.5)}" '
                f'rx="{_fmt(bw * 0.5)}" ry="{_fmt(bh * 0.5)}" fill="{fill}" stroke="{stroke}" '
                f'stroke-width="{_fmt(sw)}"/>'
            )
        elif kind in {
            "UpwardCompressorGlyph",
            "RightwardCompressorGlyph",
            "MainDiagonalMirroredCompressorGlyph",
        }:
            circle_ref = str(element.get("circle_ref", "compressor_circle"))
            circle_x, circle_y, circle_w, circle_h = _find_circle(geometry_ir, circle_ref, w, h)
            stroke = html.escape(str(element.get("stroke", "#d7d7d7")))
            sw = float(element.get("stroke_width", 0.040)) * min(w, h)
            if kind == "RightwardCompressorGlyph":
                line_specs = (
                    ("upper_line", "rightward_compressor_upper_line"),
                    ("lower_line", "rightward_compressor_lower_line"),
                )
            elif kind == "MainDiagonalMirroredCompressorGlyph":
                line_specs = (
                    ("left_line", "mirrored_compressor_left_line"),
                    ("right_line", "mirrored_compressor_right_line"),
                )
            else:
                line_specs = (
                    ("left_line", "upward_compressor_left_line"),
                    ("right_line", "upward_compressor_right_line"),
                )
            for line_key, stable_id in line_specs:
                raw_line = element.get(line_key, [])
                if not isinstance(raw_line, list) or len(raw_line) != 2:
                    continue
                points = []
                for raw_point in raw_line:
                    if isinstance(raw_point, list) and len(raw_point) == 2:
                        px = circle_x + circle_w * float(raw_point[0])
                        py = circle_y + circle_h * float(raw_point[1])
                        points.append((px, py))
                if len(points) == 2:
                    (x0, y0), (x1, y1) = points
                    svg.append(
                        f'  <path id="{stable_id}" d="M {_fmt(x0)} {_fmt(y0)} L {_fmt(x1)} {_fmt(y1)}" '
                        f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="round"/>'
                    )
        elif kind == "HorizontalGradient":
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
        elif kind == "HalfDoubleRectBorder":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            fill = html.escape(str(element.get("fill", "none")))
            stroke = html.escape(str(element.get("stroke", "#777777")))
            sw = float(element.get("stroke_width", 0.024)) * min(w, h)
            inset = float(element.get("inner_inset", 0.075)) * min(bw, bh)
            svg.append(
                f'  <rect id="{element_id}_outer" x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(bw)}" height="{_fmt(bh)}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
            )
            svg.append(
                f'  <rect id="{element_id}_inner" x="{_fmt(x + inset)}" y="{_fmt(y + inset)}" '
                f'width="{_fmt(max(0.0, bw - 2 * inset))}" height="{_fmt(max(0.0, bh - 2 * inset))}" '
                f'fill="none" stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
            )
            cut_w = max(sw * 1.6, bw * 0.20)
            svg.append(
                f'  <rect id="{element_id}_left_half_mask" x="{_fmt(x - sw)}" y="{_fmt(y - sw)}" '
                f'width="{_fmt(cut_w)}" height="{_fmt(bh + 2 * sw)}" fill="white" stroke="none"/>'
            )
        elif kind == "LabelBox":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            fill = html.escape(str(element.get("fill", "#d7d7d7")))
            stroke = html.escape(str(element.get("stroke", "#777777")))
            sw = float(element.get("stroke_width", 0.020)) * min(w, h)
            svg.append(
                f'  <rect id="{element_id}" x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(bw)}" height="{_fmt(bh)}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
            )
        elif kind == "TextGlyph":
            raw_text = html.escape(str(element.get("text", "")))
            ref_id = str(element.get("bbox_ref", ""))
            ref_element = next((candidate for candidate in geometry_ir if str(candidate.get("id", "")) == ref_id), None)
            x, y, bw, bh = _scaled_bbox(ref_element or element, w, h)
            fill = html.escape(str(element.get("fill", "#555555")))
            font_size = float(element.get("font_size", 0.105)) * min(w, h)
            font_weight = html.escape(str(element.get("font_weight", "600")))
            svg.append(
                f'  <text id="{element_id}" x="{_fmt(x + bw * 0.50)}" y="{_fmt(y + bh * 0.55)}" '
                f'fill="{fill}" font-family="Arial, Helvetica, sans-serif" font-size="{_fmt(font_size)}" '
                f'font-weight="{font_weight}" text-anchor="middle" dominant-baseline="middle">{raw_text}</text>'
            )
        elif kind == "HorizontalRuleSet":
            stroke = html.escape(str(element.get("stroke", "#707070")))
            sw = float(element.get("stroke_width", 0.026)) * min(w, h)
            x_inset = float(element.get("x_inset", 0.10)) * rect_w
            raw_positions = element.get("positions", [0.30, 0.50, 0.70])
            if not isinstance(raw_positions, list) or not raw_positions:
                raw_positions = [0.30, 0.50, 0.70]
            for rule_index, raw_pos in enumerate(raw_positions, start=1):
                y = rect_y + rect_h * float(raw_pos)
                svg.append(
                    f'  <path id="{element_id}_{rule_index}" d="M {_fmt(rect_x + x_inset)} {_fmt(y)} '
                    f'L {_fmt(rect_x + rect_w - x_inset)} {_fmt(y)}" '
                    f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="butt"/>'
                )
        elif kind == "OrthogonalPolyline":
            stroke = html.escape(str(element.get("stroke", "#707070")))
            sw = float(element.get("stroke_width", 0.034)) * min(w, h)
            raw_points = element.get("points", [])
            if not isinstance(raw_points, list) or len(raw_points) < 2:
                raw_points = [[0.50, 0.02], [1.02, 0.50], [0.50, 0.98]]
            points: list[str] = []
            for raw_point in raw_points:
                if isinstance(raw_point, list) and len(raw_point) == 2:
                    px = rect_x + rect_w * float(raw_point[0])
                    py = rect_y + rect_h * float(raw_point[1])
                    points.append(f"{_fmt(px)} {_fmt(py)}")
            if len(points) >= 2:
                path_points = " L ".join(points)
                svg.append(
                    f'  <path id="{element_id}" d="M {path_points}" '
                    f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" '
                    'stroke-linejoin="round" stroke-linecap="butt"/>'
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
