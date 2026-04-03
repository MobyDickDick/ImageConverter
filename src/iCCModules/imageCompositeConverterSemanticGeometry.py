"""Semantic geometry parsing/signature helpers for imageCompositeConverter."""

from __future__ import annotations

import os
import re


def readSvgGeometryImpl(svg_path: str, *, action_t_path_d: str) -> tuple[int, int, dict] | None:
    if not os.path.exists(svg_path):
        return None

    text = open(svg_path, "r", encoding="utf-8").read()

    svg_match = re.search(r"<svg[^>]*viewBox=\"0 0 (\d+) (\d+)\"", text)
    if not svg_match:
        return None
    w = int(svg_match.group(1))
    h = int(svg_match.group(2))

    def _grayFromHex(color: str, fallback: int) -> int:
        m = re.match(r"#([0-9a-fA-F]{6})", color.strip())
        if not m:
            return fallback
        hex_value = m.group(1)
        r = int(hex_value[0:2], 16)
        g = int(hex_value[2:4], 16)
        b = int(hex_value[4:6], 16)
        return int(round((r + g + b) / 3.0))

    params: dict[str, float | bool | int | str] = {
        "fill_gray": 220,
        "stroke_gray": 152,
        "text_gray": 98,
        "draw_text": False,
        "text_mode": "path",
        "circle_enabled": False,
        "stem_enabled": False,
        "arm_enabled": False,
    }

    circle_match = re.search(
        r"<circle[^>]*cx=\"([0-9.]+)\"[^>]*cy=\"([0-9.]+)\"[^>]*r=\"([0-9.]+)\"[^>]*stroke-width=\"([0-9.]+)\"",
        text,
    )
    if circle_match:
        params["circle_enabled"] = True
        params["cx"] = float(circle_match.group(1))
        params["cy"] = float(circle_match.group(2))
        params["r"] = float(circle_match.group(3))
        params["stroke_circle"] = float(circle_match.group(4))
        circle_tag_match = re.search(r"(<circle[^>]*>)", text)
        if circle_tag_match:
            circle_tag = circle_tag_match.group(1)
            fill_match = re.search(r'fill="(#[0-9a-fA-F]{6})"', circle_tag)
            stroke_match = re.search(r'stroke="(#[0-9a-fA-F]{6})"', circle_tag)
            if fill_match:
                params["fill_gray"] = _grayFromHex(fill_match.group(1), int(params["fill_gray"]))
            if stroke_match:
                params["stroke_gray"] = _grayFromHex(stroke_match.group(1), int(params["stroke_gray"]))

    rect_match = re.search(
        r"<rect[^>]*x=\"([0-9.]+)\"[^>]*y=\"([0-9.]+)\"[^>]*width=\"([0-9.]+)\"[^>]*height=\"([0-9.]+)\"",
        text,
    )
    if rect_match:
        x = float(rect_match.group(1))
        y = float(rect_match.group(2))
        width = float(rect_match.group(3))
        height = float(rect_match.group(4))
        params["stem_enabled"] = True
        params["stem_x"] = x
        params["stem_width"] = width
        params["stem_top"] = y
        params["stem_bottom"] = y + height
        rect_tag_match = re.search(r"(<rect[^>]*>)", text)
        if rect_tag_match:
            rect_fill_match = re.search(r'fill="(#[0-9a-fA-F]{6})"', rect_tag_match.group(1))
            if rect_fill_match:
                params["stem_gray"] = _grayFromHex(rect_fill_match.group(1), int(params["stroke_gray"]))
            else:
                params["stem_gray"] = int(params["stroke_gray"])
        else:
            params["stem_gray"] = int(params["stroke_gray"])

    line_match = re.search(
        r"<line[^>]*x1=\"([0-9.]+)\"[^>]*y1=\"([0-9.]+)\"[^>]*x2=\"([0-9.]+)\"[^>]*y2=\"([0-9.]+)\"[^>]*stroke-width=\"([0-9.]+)\"",
        text,
    )
    if line_match:
        params["arm_enabled"] = True
        params["arm_x1"] = float(line_match.group(1))
        params["arm_y1"] = float(line_match.group(2))
        params["arm_x2"] = float(line_match.group(3))
        params["arm_y2"] = float(line_match.group(4))
        params["arm_stroke"] = float(line_match.group(5))

    text_matches = re.findall(r"(<text[^>]*>)([^<]*)</text>", text)
    if text_matches:
        for text_tag, _text_content in text_matches:
            fill_match = re.search(r'fill="(#[0-9a-fA-F]{6})"', text_tag)
            if fill_match:
                params["text_gray"] = _grayFromHex(fill_match.group(1), int(params["text_gray"]))
                break

        text_tokens = [content.strip().upper() for _tag, content in text_matches if content and content.strip()]
        normalized_tokens = [token.replace("₂", "2").replace("^", "").replace("_", "") for token in text_tokens]
        merged_text = "".join(normalized_tokens)

        if any(token == "VOC" for token in normalized_tokens):
            params["draw_text"] = True
            params["text_mode"] = "voc"
        elif merged_text == "CO2" or any(token == "CO2" for token in normalized_tokens):
            # Support both single-node CO₂ labels (<text>CO2</text>, <text>CO₂</text>)
            # and split-node output (<text>CO</text><text>2</text>).
            params["draw_text"] = True
            params["text_mode"] = "co2"

    text_path_match = re.search(r"(<path[^>]*>)", text)
    if text_path_match:
        path_tag = text_path_match.group(1)
        fill_match = re.search(r'fill="(#[0-9a-fA-F]{6})"', path_tag)
        params["draw_text"] = True
        if fill_match:
            params["text_gray"] = _grayFromHex(fill_match.group(1), int(params["text_gray"]))
        if action_t_path_d in path_tag:
            params["text_mode"] = "path_t"
        else:
            params["text_mode"] = "path"

    if params.get("draw_text") and params.get("text_mode") in {"path", "path_t"} and (
        "tx" not in params or "ty" not in params or "s" not in params
    ):
        # Fallback for older path-glyph SVGs where we only need compositing geometry
        # during harmonization. Keep native <text>-based modes (CO₂/VOC) intact.
        params["draw_text"] = False

    return w, h, params


def normalizedGeometrySignatureImpl(w: int, h: int, params: dict) -> dict[str, float]:
    sig: dict[str, float] = {}
    scale = max(1.0, float(min(w, h)))

    if params.get("circle_enabled"):
        sig["cx"] = float(params["cx"]) / max(1.0, float(w))
        sig["cy"] = float(params["cy"]) / max(1.0, float(h))
        sig["r"] = float(params["r"]) / scale
        sig["stroke_circle"] = float(params["stroke_circle"]) / scale

    if params.get("stem_enabled"):
        sig["stem_x"] = float(params["stem_x"]) / max(1.0, float(w))
        sig["stem_width"] = float(params["stem_width"]) / max(1.0, float(w))
        sig["stem_top"] = float(params["stem_top"]) / max(1.0, float(h))
        sig["stem_bottom"] = float(params["stem_bottom"]) / max(1.0, float(h))

    if params.get("arm_enabled"):
        sig["arm_x1"] = float(params["arm_x1"]) / max(1.0, float(w))
        sig["arm_y1"] = float(params["arm_y1"]) / max(1.0, float(h))
        sig["arm_x2"] = float(params["arm_x2"]) / max(1.0, float(w))
        sig["arm_y2"] = float(params["arm_y2"]) / max(1.0, float(h))
        sig["arm_stroke"] = float(params["arm_stroke"]) / scale

    return sig


def maxSignatureDeltaImpl(sig_a: dict[str, float], sig_b: dict[str, float]) -> float:
    keys = sorted(set(sig_a.keys()).intersection(sig_b.keys()))
    if not keys:
        return 1.0
    return max(abs(sig_a[k] - sig_b[k]) for k in keys)
