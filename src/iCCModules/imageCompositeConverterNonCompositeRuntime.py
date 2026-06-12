from __future__ import annotations

import os
import re
from pathlib import Path
import numpy as np

from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir_helpers
from src.iCCModules import imageCompositeConverterGeometryIrOptimizer as geometry_ir_optimizer
from tools.perception_detection_contract import build_perception_seeded_geometry_ir


def _build_vector_placeholder_svg(width: int, height: int, *, description: str = "") -> str:
    safe_w = max(1, int(width or 1))
    safe_h = max(1, int(height or 1))
    desc = (description or "Automatisch erzeugte Platzhalter-Vektorgrafik").strip()
    escaped_desc = (
        desc.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" viewBox="0 0 {safe_w} {safe_h}">\n'
        f'  <desc>{escaped_desc}</desc>\n'
        '  <defs>\n'
        '    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="0%">\n'
        '      <stop offset="0%" stop-color="#6d6d6d"/>\n'
        '      <stop offset="50%" stop-color="#d7d7d7"/>\n'
        '      <stop offset="100%" stop-color="#6d6d6d"/>\n'
        '    </linearGradient>\n'
        '  </defs>\n'
        f'  <rect x="0" y="0" width="{safe_w}" height="{safe_h}" fill="url(#bg)"/>\n'
        f'  <line x1="0" y1="0" x2="{safe_w}" y2="{safe_h}" stroke="#8e8e8e" stroke-width="1"/>\n'
        f'  <line x1="{safe_w}" y1="0" x2="0" y2="{safe_h}" stroke="#8e8e8e" stroke-width="1"/>\n'
        f'  <rect x="{max(1, safe_w//4)}" y="{max(1, safe_h//10)}" width="{max(2, safe_w//2)}" height="{max(2, safe_h//8)}" fill="#4a4a4a" rx="1"/>\n'
        f'  <line x1="{max(2, safe_w//2 - safe_w//8)}" y1="{max(2, safe_h//6)}" x2="{max(3, safe_w//2 - safe_w//20)}" y2="{max(2, safe_h//6)}" stroke="#f2f2f2" stroke-width="1"/>\n'
        f'  <line x1="{max(2, safe_w//2 + safe_w//20)}" y1="{max(2, safe_h//6)}" x2="{max(3, safe_w//2 + safe_w//8)}" y2="{max(2, safe_h//6)}" stroke="#f2f2f2" stroke-width="1"/>\n'
        '</svg>\n'
    )


def _description_requests_diagonal_band(description: str) -> bool:
    text = (description or "").lower()
    return "diagon" in text and "links unten" in text and "rechts oben" in text


def _build_diagonal_band_svg(width: int, height: int, *, stroke_width: float, description: str = "") -> str:
    safe_w = max(1, int(width or 1))
    safe_h = max(1, int(height or 1))
    margin = 0.5
    x1, y1 = margin, safe_h - margin
    x2, y2 = safe_w - margin, margin
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" viewBox="0 0 {safe_w} {safe_h}">\n'
        '  <defs>\n'
        '    <linearGradient id="bg" x1="100%" y1="0%" x2="0%" y2="0%">\n'
        '      <stop offset="0%" stop-color="#b4b4b4"/>\n'
        '      <stop offset="30%" stop-color="#fbfbfb"/>\n'
        '      <stop offset="37%" stop-color="#fbfbfb"/>\n'
        '      <stop offset="100%" stop-color="#b4b4b4"/>\n'
        '    </linearGradient>\n'
        f'    <clipPath id="innerRect"><rect x="{margin}" y="{margin}" width="{safe_w-1}" height="{safe_h-1}"/></clipPath>\n'
        '  </defs>\n'
        f'  <rect x="{margin}" y="{margin}" width="{safe_w-1}" height="{safe_h-1}" fill="url(#bg)" stroke="#adadad" stroke-width="1"/>\n'
        f'  <path d="M {x1} {y1} L {x2} {y2}" fill="none" stroke="#8f8f8f" stroke-width="{stroke_width:.3f}" stroke-linecap="butt" clip-path="url(#innerRect)"/>\n'
        '</svg>\n'
    )


def _fit_diagonal_band_iterative(*, width: int, height: int, description: str, perc_img, render_svg_to_numpy_fn, calculate_error_fn):
    ratios = (0.08, 0.11, 0.14, 0.17, 0.20, 0.23, 0.26)
    scale = max(2.0, min(width, height))
    best = None
    for ratio in ratios:
        stroke_w = max(1.0, scale * ratio)
        svg = _build_diagonal_band_svg(width, height, stroke_width=stroke_w, description=description)
        rendered = render_svg_to_numpy_fn(svg, width, height)
        if rendered is None:
            continue
        err = calculate_error_fn(perc_img, rendered)
        if best is None or err < best[0]:
            best = (err, svg, rendered, stroke_w)
    return best


def _gray_hex(value: float) -> str:
    gray = int(max(0, min(255, round(float(value)))))
    return f"#{gray:02x}{gray:02x}{gray:02x}"


def _color_hex(value: float | str) -> str:
    text = str(value or "").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", text):
        return text.lower()
    return _gray_hex(float(value))


def _rgb_hex(values) -> str:
    channels = [int(max(0, min(255, round(float(channel))))) for channel in values[:3]]
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def _gradient_band_svg_rects(
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    edge_hex: str,
    mid_hex: str,
    center_percent: float,
    bands: int = 48,
) -> str:
    def _rgb(color: str, fallback: int) -> np.ndarray:
        value = str(color or "").strip().lstrip("#")
        if len(value) >= 6:
            try:
                return np.asarray([int(value[index:index + 2], 16) for index in (0, 2, 4)], dtype=np.float32)
            except ValueError:
                pass
        return np.asarray([fallback, fallback, fallback], dtype=np.float32)

    edge = _rgb(edge_hex, 0x8F)
    mid = _rgb(mid_hex, 0xDE)
    safe_bands = max(4, int(bands))
    center = max(1.0, min(99.0, float(center_percent))) / 100.0
    parts: list[str] = []
    for index in range(safe_bands):
        t = (index + 0.5) / safe_bands
        if t <= center:
            ratio = t / center
            color = edge * (1.0 - ratio) + mid * ratio
        else:
            ratio = (t - center) / (1.0 - center)
            color = mid * (1.0 - ratio) + edge * ratio
        band_x = x + width * index / safe_bands
        band_w = width / safe_bands + max(0.02, width * 0.001)
        parts.append(
            f'  <rect x="{band_x:.3f}" y="{y:.3f}" width="{band_w:.3f}" height="{height:.3f}" '
            f'fill="{_rgb_hex(color)}" stroke="none"/>')
    return "\n".join(parts) + ("\n" if parts else "")


def _build_structured_symbol_svg(
    width: int,
    height: int,
    *,
    border_thickness: float,
    gradient_center: float,
    gradient_edge: str,
    gradient_mid: str,
    diag1_width: float,
    diag2_width: float,
    plus_width: float,
    minus_width: float,
    plus_x_ratio: float,
    glyph_y_ratio: float,
    plus_half_ratio: float,
    minus_gap_ratio: float,
    diagonal_inset_ratio: float = 0.0,
    center_dot_radius: float = 0.0,
    center_dot_gray: float | str = 79.0,
    glyph_gray: float | str = 241.0,
    diag_gray: float | str = 143.0,
    border_gray: float | str = 154.0,
    chevron_width: float = 0.0,
    chevron_inset_ratio: float = 0.0,
    chevron_center_x_ratio: float = 0.5,
    chevron_peak_x_ratio: float = 1.0,
    chevron_peak_y_ratio: float = 0.5,
) -> str:
    safe_w = max(1, int(width or 1))
    safe_h = max(1, int(height or 1))
    inset = 0.5
    plus_cx = safe_w * float(plus_x_ratio)
    plus_cy = safe_h * float(glyph_y_ratio)
    plus_half = max(2.0, min(safe_w, safe_h) * float(plus_half_ratio))
    minus_y = plus_cy
    minus_half = max(2.0, min(safe_w, safe_h) * 0.07)
    minus_start_x = plus_cx + plus_half * float(minus_gap_ratio)
    diagonal_inset = max(0.0, min(0.45, float(diagonal_inset_ratio)))
    diag_x0 = inset + (safe_w - 1 - 2 * inset) * diagonal_inset
    diag_x1 = safe_w - 1 - (safe_w - 1 - 2 * inset) * diagonal_inset
    diag_y0 = inset + (safe_h - 1 - 2 * inset) * diagonal_inset
    diag_y1 = safe_h - 1 - (safe_h - 1 - 2 * inset) * diagonal_inset
    chevron_inset = max(0.0, min(0.40, float(chevron_inset_ratio)))
    chevron_x0 = safe_w * max(0.0, min(1.0, float(chevron_center_x_ratio)))
    chevron_x1 = inset + (safe_w - 1 - inset) * max(0.5, min(1.0, float(chevron_peak_x_ratio)))
    chevron_peak_y = safe_h * max(0.0, min(1.0, float(chevron_peak_y_ratio)))
    chevron_y0 = inset + (safe_h - 1 - 2 * inset) * chevron_inset
    chevron_y1 = safe_h - 1 - (safe_h - 1 - 2 * inset) * chevron_inset
    gradient_rects = _gradient_band_svg_rects(
        x=inset,
        y=inset,
        width=safe_w - 1,
        height=safe_h - 1,
        edge_hex=gradient_edge,
        mid_hex=gradient_mid,
        center_percent=gradient_center,
        bands=max(16, min(64, safe_w * 2)),
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" viewBox="0 0 {safe_w} {safe_h}">\n'
        '  <defs>\n'
        f'    <clipPath id="innerRect"><rect x="{inset}" y="{inset}" width="{safe_w-1}" height="{safe_h-1}"/></clipPath>\n'
        '  </defs>\n'
        f'{gradient_rects}'
        f'  <rect x="{inset}" y="{inset}" width="{safe_w-1}" height="{safe_h-1}" fill="none" stroke="{_color_hex(border_gray)}" stroke-width="{border_thickness:.2f}"/>\n'
        + (f'  <line x1="{diag_x1:g}" y1="{diag_y0:g}" x2="{diag_x0:g}" y2="{diag_y1:g}" stroke="{_color_hex(diag_gray)}" stroke-width="{diag1_width:.2f}" clip-path="url(#innerRect)"/>\n' if diag1_width > 0 else '')
        + (f'  <line x1="{diag_x0:g}" y1="{diag_y0:g}" x2="{diag_x1:g}" y2="{diag_y1:g}" stroke="{_color_hex(diag_gray)}" stroke-width="{diag2_width:.2f}" clip-path="url(#innerRect)"/>\n' if diag2_width > 0 else '')
        + (f'  <path d="M {chevron_x0:g} {chevron_y0:g} L {chevron_x1:g} {chevron_peak_y:g} L {chevron_x0:g} {chevron_y1:g}" fill="none" stroke="{_color_hex(diag_gray)}" stroke-width="{chevron_width:.2f}" stroke-linejoin="round" stroke-linecap="butt" clip-path="url(#innerRect)"/>\n' if chevron_width > 0 else '')
        + (f'  <line x1="{plus_cx-plus_half:.2f}" y1="{plus_cy:.2f}" x2="{plus_cx+plus_half:.2f}" y2="{plus_cy:.2f}" stroke="{_color_hex(glyph_gray)}" stroke-width="{plus_width:.2f}" stroke-linecap="round"/>\n' if plus_width > 0 else '')
        + (f'  <line x1="{plus_cx:.2f}" y1="{plus_cy-plus_half:.2f}" x2="{plus_cx:.2f}" y2="{plus_cy+plus_half:.2f}" stroke="{_color_hex(glyph_gray)}" stroke-width="{plus_width:.2f}" stroke-linecap="round"/>\n' if plus_width > 0 else '')
        + (f'  <line x1="{minus_start_x:.2f}" y1="{minus_y:.2f}" x2="{minus_start_x+minus_half*1.8:.2f}" y2="{minus_y:.2f}" stroke="{_color_hex(glyph_gray)}" stroke-width="{minus_width:.2f}" stroke-linecap="round"/>\n' if minus_width > 0 else '')
        + (f'  <circle cx="{safe_w * 0.5:.2f}" cy="{safe_h * 0.5:.2f}" r="{center_dot_radius:.2f}" fill="{_color_hex(center_dot_gray)}"/>\n' if center_dot_radius > 0 else '')
        + '</svg>\n'
    )


def _estimate_symbol_glyph_geometry_from_luminance(lum: np.ndarray) -> dict[str, float]:
    h, w = lum.shape[:2]
    if h <= 0 or w <= 0:
        return {"plus_x_ratio": 0.16, "glyph_y_ratio": 0.12, "plus_half_ratio": 0.08}

    top_limit = max(1, min(h, int(round(h * 0.45))))
    left_limit = max(1, min(w, int(round(w * 0.65))))
    roi = lum[:top_limit, :left_limit]
    contrast = max(1.0, float(np.nanpercentile(lum, 90) - np.nanpercentile(lum, 10)))
    high_threshold = max(
        float(np.nanpercentile(lum, 97)),
        float(np.nanmean(lum) + np.nanstd(lum) * 1.2),
        float(np.nanmax(roi) - max(6.0, contrast * 0.18)),
    )
    mask = roi >= high_threshold
    if int(mask.sum()) < 2:
        return {"plus_x_ratio": 0.16, "glyph_y_ratio": 0.12, "plus_half_ratio": 0.08}

    ys, xs = np.nonzero(mask)
    weights = np.maximum(roi[ys, xs].astype(np.float32) - high_threshold + 1.0, 1.0)
    plus_x = float(np.average(xs, weights=weights))
    plus_y = float(np.average(ys, weights=weights))
    span_x = float(np.nanpercentile(xs, 90) - np.nanpercentile(xs, 10) + 1.0)
    span_y = float(np.nanpercentile(ys, 90) - np.nanpercentile(ys, 10) + 1.0)
    scale = max(1.0, min(float(w), float(h)))
    half = max(span_x, span_y) / (2.0 * scale)
    return {
        "plus_x_ratio": max(0.05, min(0.50, plus_x / max(1.0, float(w)))),
        "glyph_y_ratio": max(0.05, min(0.45, plus_y / max(1.0, float(h)))),
        "plus_half_ratio": max(0.04, min(0.16, half)),
    }


def _derive_symbol_params_from_raster(*, width: int, height: int, perc_img) -> dict[str, float | str]:
    # Data-driven estimation from the actual raster instead of per-figure hardcoded sweeps.
    arr = np.asarray(perc_img) if perc_img is not None else None
    if arr is None or arr.ndim < 2:
        raise ValueError("invalid raster input")
    # Runtime rasters originate from OpenCV (BGR); SVG colors are RGB.
    color = arr[..., :3][..., ::-1].astype(np.float32) if arr.ndim == 3 else None
    if color is not None:
        lum = color.mean(axis=2)
    else:
        lum = arr.astype(np.float32)
    h, w = lum.shape[:2]
    mid = lum[:, w // 2]
    left = lum[:, max(0, int(w * 0.1))]
    right = lum[:, min(w - 1, int(w * 0.9))]
    center_is_brighter = float(np.nanmean(mid)) > float((np.nanmean(left) + np.nanmean(right)) * 0.5)
    grad_center = 50.0 if center_is_brighter else 45.0
    contrast = max(1.0, float(np.nanpercentile(lum, 90) - np.nanpercentile(lum, 10)))
    # Estimate the horizontal background from robust column medians. This
    # rejects thin diagonals and glyphs and works for both dark and light
    # symbol families without imposing the former 190..250 midpoint clamp.
    inner = lum[1:-1, 1:-1] if h > 2 and w > 2 else lum
    column_profile = np.nanmedian(inner, axis=0)
    flank_count = max(1, int(round(column_profile.size * 0.20)))
    edge = int(round(float(np.nanmedian(np.concatenate((column_profile[:flank_count], column_profile[-flank_count:]))))))
    midc = int(round(float(np.nanmax(column_profile))))
    edge = max(0, min(255, edge))
    midc = max(0, min(255, midc))
    edge_color = _gray_hex(edge)
    mid_color = _gray_hex(midc)
    if color is not None:
        color_inner = color[1:-1, 1:-1] if h > 2 and w > 2 else color
        color_profile = np.nanmedian(color_inner, axis=0)
        flank_colors = np.concatenate((color_profile[:flank_count], color_profile[-flank_count:]), axis=0)
        edge_color = _rgb_hex(np.nanmedian(flank_colors, axis=0))
        # The SVG frame and a bright chevron can dominate the absolute
        # brightest column.  Estimate the light gradient stop from the central
        # band instead, where a dark-light-dark horizontal gradient declares
        # its midpoint.  This preserves saturated source colours instead of
        # accidentally promoting a white border to the background midpoint.
        center_start = max(0, int(round(color_profile.shape[0] * 0.35)))
        center_end = min(color_profile.shape[0], int(round(color_profile.shape[0] * 0.65)))
        center_colors = color_profile[center_start:center_end]
        if center_colors.size:
            mid_color = _rgb_hex(np.nanmedian(center_colors, axis=0))
        else:
            mid_color = _rgb_hex(color_profile[color_profile.shape[0] // 2])
    dark_ratio = float((lum < np.nanpercentile(lum, 35)).mean())
    light_ratio = float((lum > np.nanpercentile(lum, 70)).mean())
    scale = max(1.0, min(width, height))
    background = np.broadcast_to(column_profile.reshape(1, -1), inner.shape)
    bright_residual = inner - background
    bright_cutoff = max(15.0, float(np.nanpercentile(bright_residual, 94)))
    bright_y, bright_x = np.nonzero(bright_residual >= bright_cutoff)
    diagonal_inset_ratio = 0.0
    diagonal_gray: float | str = float(np.nanpercentile(lum, 25))
    if bright_x.size >= 4:
        x_span = int(bright_x.max() - bright_x.min())
        y_span = int(bright_y.max() - bright_y.min())
        if x_span >= max(2, inner.shape[1] // 4) and y_span >= max(2, inner.shape[0] // 4):
            x_margin = min(float(bright_x.min()), float(inner.shape[1] - 1 - bright_x.max())) / max(1.0, float(inner.shape[1] - 1))
            y_margin = min(float(bright_y.min()), float(inner.shape[0] - 1 - bright_y.max())) / max(1.0, float(inner.shape[0] - 1))
            diagonal_inset_ratio = max(0.0, min(0.40, (x_margin + y_margin) * 0.5))
            if color is not None:
                diagonal_gray = _rgb_hex(np.nanmedian(color_inner[bright_y, bright_x], axis=0))
            else:
                diagonal_gray = float(np.nanmedian(inner[bright_y, bright_x]))
    glyph_geometry = _estimate_symbol_glyph_geometry_from_luminance(lum)
    return {
        "border_thickness": max(0.8, min(1.8, 0.9 + dark_ratio * 1.8)),
        "gradient_center": grad_center,
        "gradient_edge": edge_color,
        "gradient_mid": mid_color,
        "diag1_width": max(1.0, min(2.8, 1.0 + dark_ratio * scale * 0.02)),
        "diag2_width": 0.0,
        "diagonal_inset_ratio": diagonal_inset_ratio,
        "plus_width": max(0.8, min(2.2, 0.8 + light_ratio * scale * 0.012)),
        "minus_width": 0.0,
        "plus_x_ratio": glyph_geometry["plus_x_ratio"],
        "glyph_y_ratio": glyph_geometry["glyph_y_ratio"],
        "plus_half_ratio": glyph_geometry["plus_half_ratio"],
        "minus_gap_ratio": 1.8,
        "center_dot_radius": 0.0,
        "center_dot_gray": max(30.0, min(180.0, float(np.nanpercentile(lum, 10)))),
        "glyph_gray": max(55.0, min(180.0, float(np.nanpercentile(lum[: max(1, int(h * 0.18)), : max(1, int(w * 0.40))], 15)))),
        "diag_gray": diagonal_gray if isinstance(diagonal_gray, str) else max(30.0, min(245.0, diagonal_gray)),
        "border_gray": max(80.0, min(180.0, float(np.nanpercentile(lum, 30)))),
    }


def _candidate_window(
    current_value: float,
    offsets: tuple[float, ...],
    *,
    minimum: float,
    maximum: float,
    include_limits: bool = True,
) -> tuple[float, ...]:
    values = [minimum, maximum] if include_limits else []
    for offset in offsets:
        values.append(max(minimum, min(maximum, float(current_value) + offset)))
    values.append(max(minimum, min(maximum, float(current_value))))
    return tuple(sorted({round(value, 4) for value in values}))


def _weighted_symbol_candidate_error(
    perc_img,
    rendered,
    *,
    base_error: float,
    key: str,
) -> float:
    if key not in {"plus_x_ratio", "glyph_y_ratio", "plus_half_ratio", "plus_width", "minus_gap_ratio", "minus_width", "glyph_gray"}:
        return float(base_error)
    try:
        target = np.asarray(perc_img, dtype=np.float32)
        candidate = np.asarray(rendered, dtype=np.float32)
    except (TypeError, ValueError):
        return float(base_error)
    if target.shape[:2] != candidate.shape[:2] or target.size == 0 or candidate.size == 0:
        return float(base_error)
    h, w = target.shape[:2]
    y_end = max(1, min(h, int(round(h * 0.24))))
    x_end = max(1, min(w, int(round(w * 0.58))))
    target_roi = target[:y_end, :x_end]
    candidate_roi = candidate[:y_end, :x_end]
    if target_roi.size == 0 or candidate_roi.size == 0:
        return float(base_error)
    roi_error = float(np.mean(np.abs(target_roi - candidate_roi)))
    return float(base_error) + roi_error * 1.6


def _fit_symbol_element_by_element(
    *,
    width: int,
    height: int,
    description: str = "",
    perc_img,
    render_svg_to_numpy_fn,
    calculate_error_fn,
) -> tuple[float, str, object, dict[str, float | str], list[str]] | None:
    current = _derive_symbol_params_from_raster(width=width, height=height, perc_img=perc_img)
    description_text = (description or "").casefold()
    glyph_is_top = any(token in description_text for token in ("oben links", "top left", "top-left"))
    has_plus = "plus" in description_text or "+" in description_text
    has_minus = "minus" in description_text
    has_center_dot = "punkt" in description_text and any(
        token in description_text for token in ("mitte", "mittig", "zentrum", "center")
    )
    has_both_diagonals = any(
        token in description_text
        for token in ("beide diagonalen", "beiden diagonalen", "andreaskreuz", "diagonalkreuz")
    )
    diagonal_tl_br = bool(re.search(r"oben\s+links.*unten\s+rechts|unten\s+rechts.*oben\s+links", description_text))
    diagonal_tr_bl = bool(re.search(r"oben\s+rechts.*unten\s+links|unten\s+links.*oben\s+rechts", description_text))
    quarter_turn = bool(
        re.search(
            r"(?:90\s*°?|90\s*grad|vierteldrehung).*?(?:gedreht|drehung)|"
            r"(?:gedreht|drehung).*?(?:90\s*°?|90\s*grad|vierteldrehung)",
            description_text,
        )
    )
    if quarter_turn and diagonal_tl_br != diagonal_tr_bl:
        # A quarter turn swaps the two diagonal axes.  Family descriptions
        # commonly state the base orientation first and append the geometric
        # variant afterwards, so the rendered direction must follow the
        # transformed image rather than the unrotated wording.
        diagonal_tl_br, diagonal_tr_bl = diagonal_tr_bl, diagonal_tl_br
    if "diagon" in description_text:
        current["diag1_width"] = float(current["diag1_width"]) if (diagonal_tr_bl or not diagonal_tl_br) else 0.0
        current["diag2_width"] = float(current["diag1_width"] or 1.4) if (diagonal_tl_br or has_both_diagonals) else 0.0
    else:
        current["diag1_width"] = 0.0
        current["diag2_width"] = 0.0
    has_right_chevron = bool(
        re.search(r"oben[-\s]*mitte.*rechts[-\s]*mitte.*unten[-\s]*mitte", description_text)
    )
    current.setdefault("diagonal_inset_ratio", 0.0)
    current.setdefault("chevron_inset_ratio", float(current["diagonal_inset_ratio"]))
    current.setdefault("chevron_center_x_ratio", 0.5)
    current.setdefault("chevron_peak_x_ratio", 1.0)
    current.setdefault("chevron_peak_y_ratio", 0.5)
    current["chevron_width"] = float(current["diag1_width"]) if has_right_chevron else 0.0
    current.setdefault("center_dot_radius", 0.0)
    current.setdefault("center_dot_gray", 79.0)
    current["plus_width"] = float(current["plus_width"]) if has_plus else 0.0
    current["minus_width"] = 1.0 if has_minus else 0.0
    current["center_dot_radius"] = max(1.0, min(width, height) * 0.12) if has_center_dot else 0.0
    if glyph_is_top and float(current["glyph_y_ratio"]) > 0.30:
        # A bright gradient highlight can otherwise be mistaken for the glyph.
        # Keep the raster-derived x/size estimates, but restore the semantic
        # top region before pixel fitting refines the exact placement.
        current["glyph_y_ratio"] = 0.15
    glyph_y_maximum = 0.30 if glyph_is_top else 0.45
    # Element-wise refinement order requested by project idea.  Position and
    # size windows are centered on raster measurements so AC0100-like variants
    # are fitted from the image evidence instead of from one fixed sample pose.
    gradient_edge_seed = float(int(str(current["gradient_edge"])[1:3], 16))
    gradient_mid_seed = float(int(str(current["gradient_mid"])[1:3], 16))
    diagonal_gray_seed = current["diag_gray"]
    refinement_steps: list[tuple[str, tuple[float | str, ...]]] = [
        ("border_thickness", (0.8, 1.0, 1.2, 1.4, 1.8)),
        ("gradient_center", (40.0, 45.0, 50.0, 55.0, 60.0)),
        ("diag1_width", (0.8, 1.0, 1.4, 1.8, 2.2, 2.8) if float(current["diag1_width"]) > 0 else (0.0,)),
        ("diag2_width", (0.8, 1.0, 1.4, 1.8, 2.2, 2.8) if float(current["diag2_width"]) > 0 else (0.0,)),
        (
            "diagonal_inset_ratio",
            _candidate_window(float(current["diagonal_inset_ratio"]), (-0.08, -0.04, 0.0, 0.04, 0.08), minimum=0.0, maximum=0.40, include_limits=False)
            if (float(current["diag1_width"]) > 0 or float(current["diag2_width"]) > 0)
            else (0.0,),
        ),
        ("chevron_width", (0.8, 1.0, 1.4, 1.8, 2.2, 2.8) if has_right_chevron else (0.0,)),
        (
            "chevron_inset_ratio",
            _candidate_window(
                float(current["chevron_inset_ratio"]),
                (-0.06, -0.03, 0.0, 0.03, 0.06),
                minimum=0.0,
                maximum=0.24,
                include_limits=True,
            ) if has_right_chevron else (0.0,),
        ),
        ("chevron_center_x_ratio", (0.44, 0.46, 0.48, 0.50, 0.52) if has_right_chevron else (0.5,)),
        ("chevron_peak_x_ratio", (0.88, 0.92, 0.96, 1.0) if has_right_chevron else (1.0,)),
        ("chevron_peak_y_ratio", (0.46, 0.48, 0.50, 0.52, 0.54) if has_right_chevron else (0.5,)),
        (
            "plus_x_ratio",
            _candidate_window(float(current["plus_x_ratio"]), (-0.08, -0.04, 0.0, 0.04, 0.08), minimum=0.05, maximum=0.55, include_limits=False),
        ),
        (
            "glyph_y_ratio",
            _candidate_window(
                float(current["glyph_y_ratio"]),
                (-0.08, -0.04, 0.0, 0.04, 0.08),
                minimum=0.05,
                maximum=glyph_y_maximum,
                include_limits=False,
            ),
        ),
        (
            "plus_half_ratio",
            _candidate_window(float(current["plus_half_ratio"]), (-0.03, -0.015, 0.0, 0.015, 0.03), minimum=0.04, maximum=0.16, include_limits=False),
        ),
        ("plus_width", (0.8, 1.0, 1.2, 1.6, 2.2) if has_plus else (0.0,)),
        ("minus_gap_ratio", (1.5, 1.8, 2.1)),
        ("minus_width", (0.8, 1.0, 1.2, 1.6, 2.2) if has_minus else (0.0,)),
        ("center_dot_radius", (0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2) if has_center_dot else (0.0,)),
        ("center_dot_gray", (40.0, 55.0, 70.0, 80.0, 95.0, 110.0, 130.0, 150.0) if has_center_dot else (float(current["center_dot_gray"]),)),
        ("glyph_gray", (55.0, 70.0, 85.0, 100.0, 115.0, 130.0, 150.0, 180.0, 210.0, 241.0)),
        ("diag_gray", (diagonal_gray_seed, 70.0, 95.0, 120.0, 145.0, 170.0, 195.0, 220.0, 241.0)),
        ("border_gray", (90.0, 110.0, 130.0, 154.0, 170.0, 190.0)),
        ("gradient_edge", (str(current["gradient_edge"]),) + tuple(_gray_hex(v) for v in sorted({70.0, 85.0, 100.0, 120.0, 150.0, gradient_edge_seed}))),
        ("gradient_mid", (str(current["gradient_mid"]),) + tuple(_gray_hex(v) for v in sorted({100.0, 120.0, 140.0, 170.0, 190.0, 220.0, 245.0, gradient_mid_seed}))),
    ]
    step_logs: list[str] = []
    best: tuple[float, str, object] | None = None
    for key, candidates in refinement_steps:
        local_best = None
        for candidate_value in candidates:
            candidate = dict(current)
            candidate[key] = candidate_value
            svg = _build_structured_symbol_svg(width, height, **candidate)
            rendered = render_svg_to_numpy_fn(svg, width, height)
            if rendered is None:
                continue
            err = calculate_error_fn(perc_img, rendered)
            score = _weighted_symbol_candidate_error(perc_img, rendered, base_error=err, key=key)
            if local_best is None or score < local_best[0]:
                local_best = (score, err, candidate_value, svg, rendered)
        if local_best is None:
            continue
        current[key] = local_best[2]
        step_logs.append(f"step_{key}={local_best[2]}")
        best = (local_best[1], local_best[3], local_best[4])
    if best is None:
        return None
    return best[0], best[1], best[2], current, step_logs


DESCRIPTION_DRIVEN_GEOMETRY_IR_KINDS = {
    "HorizontalRule",
    "HorizontalRuleSet",
    "OrthogonalPolyline",
    "HalfDoubleRectBorder",
    "LabelBox",
    "TextGlyph",
    "CircleBackground",
    "HorizontalGradient",
    "DiagonalBand",
    "PlusGlyph",
    "MinusGlyph",
    "RectBorder",
    "UpwardCompressorGlyph",
    "RightwardCompressorGlyph",
    "MainDiagonalMirroredCompressorGlyph",
    "VerticalTwoWayValveMotorGlyph",
    "LeftRotatedTwoWayValveMotorGlyph",
    "Rotated180TwoWayValveMotorGlyph",
    "TopKelleThreeWayValveGlyph",
    "LeftRotatedTopKelleThreeWayValveGlyph",
    "RightRotatedTopKelleThreeWayValveGlyph",
    "Rotated180TopKelleThreeWayValveGlyph",
    "MainDiagonalMirroredTopKelleThreeWayValveGlyph",
    "LeftRotatedCircularDamperGlyph",
    "RightRotatedSquareKellePGlyph",
    "RightFacingSquareKellePGlyph",
    "LeftRotatedSquareKelleTGlyph",
    "VerticallyMirroredSquareKelleTGlyph",
}


SEMANTIC_GEOMETRY_IR_KINDS = {
    "VerticalTwoWayValveMotorGlyph",
    "LeftRotatedTwoWayValveMotorGlyph",
    "Rotated180TwoWayValveMotorGlyph",
    "TopKelleThreeWayValveGlyph",
    "LeftRotatedTopKelleThreeWayValveGlyph",
    "RightRotatedTopKelleThreeWayValveGlyph",
    "Rotated180TopKelleThreeWayValveGlyph",
    "MainDiagonalMirroredTopKelleThreeWayValveGlyph",
    "LeftRotatedCircularDamperGlyph",
    "RightRotatedSquareKellePGlyph",
    "RightFacingSquareKellePGlyph",
    "LeftRotatedSquareKelleTGlyph",
    "VerticallyMirroredSquareKelleTGlyph",
}


def _apply_image_variant_geometry(
    geometry_ir: list[dict[str, object]], *, base_name: str
) -> list[dict[str, object]]:
    """Add image-specific geometry omitted by family-level descriptions."""

    normalized_name = Path(str(base_name or "")).stem.upper()
    if not (normalized_name.startswith("AC0224_") and normalized_name.endswith("_SIA")):
        return geometry_ir

    for element in geometry_ir:
        if element.get("kind") == "RightRotatedTopKelleThreeWayValveGlyph":
            element["handle_shape"] = "crossed_square"
            # The SIA handle is a compact crossed square, not the enlarged
            # unlabelled circle used by the regular AC0224 variants.
            element["circle"] = [0.235, 0.500, 0.225]
            element["connector"][0] = [0.450, 0.500]
    return geometry_ir


def _prefer_semantic_description_geometry(geometry_ir: list[dict[str, object]]) -> bool:
    kinds = {str(element.get("kind", "")) for element in geometry_ir}
    return bool(SEMANTIC_GEOMETRY_IR_KINDS & kinds)


def _try_build_description_geometry_ir_svg(width: int, height: int, *, description: str) -> str | None:
    geometry_ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description)
    if not geometry_ir:
        return None
    kinds = {str(element.get("kind", "")) for element in geometry_ir}
    if not (DESCRIPTION_DRIVEN_GEOMETRY_IR_KINDS & kinds):
        return None
    return geometry_ir_helpers.renderGeometryIrToSvgImpl(width, height, geometry_ir)


def _try_build_perception_seeded_geometry_ir_svg(
    width: int,
    height: int,
    *,
    description: str,
    perc_img,
) -> tuple[str, list[dict[str, object]], int] | None:
    if not hasattr(perc_img, "shape"):
        return None
    try:
        image = np.asarray(perc_img)
    except (TypeError, ValueError):
        return None
    if image.ndim < 2 or image.size == 0:
        return None
    try:
        geometry_ir = build_perception_seeded_geometry_ir(
            image,
            description=description,
            source="non_composite_perception_seed",
        )
    except (RuntimeError, TypeError, ValueError, AttributeError):
        return None
    if not geometry_ir:
        return None
    seeded_elements = [
        element
        for element in geometry_ir
        if isinstance(element, dict) and element.get("perception_seed")
    ]
    if not seeded_elements:
        return None
    kinds = {str(element.get("kind", "")) for element in geometry_ir}
    if not (DESCRIPTION_DRIVEN_GEOMETRY_IR_KINDS & kinds):
        return None
    return (
        geometry_ir_helpers.renderGeometryIrToSvgImpl(width, height, geometry_ir),
        geometry_ir,
        len(seeded_elements),
    )


def _contains_svg_image_tag(svg_content: str) -> bool:
    lowered = svg_content.lower()
    return "<image" in lowered and ('href="data:image' in lowered or 'xlink:href="data:image' in lowered)


def _build_sample_candidates(base_name: str) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        if name and name not in seen:
            seen.add(name)
            candidates.append(name)

    _add(base_name)
    root, sep, size_suffix = base_name.rpartition("_")
    if sep:
        _add(root)
        for alt_suffix in ("L", "M", "S"):
            _add(f"{root}_{alt_suffix}")
    else:
        for alt_suffix in ("L", "M", "S"):
            _add(f"{base_name}_{alt_suffix}")

    family_name = root if sep else base_name

    if family_name.startswith("AC") and len(family_name) > 2:
        se_alias = f"SE{family_name[2:]}"
        _add(se_alias)
        for alt_suffix in ("L", "M", "S"):
            _add(f"{se_alias}_{alt_suffix}")
    if family_name.startswith("SE") and len(family_name) > 2:
        ac_alias = f"AC{family_name[2:]}"
        _add(ac_alias)
        for alt_suffix in ("L", "M", "S"):
            _add(f"{ac_alias}_{alt_suffix}")

    return candidates


def _extract_reference_family_from_description(description: str) -> str | None:
    text = (description or "").strip()
    if not text:
        return None
    match = re.search(r"\bwie\s+((?:AC|SE)\d{4})\b", text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).upper()


def _prepend_reference_candidates(candidates: list[str], reference_family: str) -> list[str]:
    preferred: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        if name and name not in seen:
            seen.add(name)
            preferred.append(name)

    _add(reference_family)
    for size in ("L", "M", "S"):
        _add(f"{reference_family}_{size}")

    for existing in candidates:
        _add(existing)
    return preferred


def _is_inkscape_svg(svg_content: str) -> bool:
    lowered = svg_content.lower()
    return "inkscape:" in lowered or "sodipodi:" in lowered or "created with inkscape" in lowered


def _sanitize_sample_svg(svg_content: str) -> str:
    # Remove editor-specific metadata that can break strict SVG parsers when
    # namespace declarations are missing in curated sample assets.
    sanitized = re.sub(r"<\/?(?:sodipodi|inkscape):[^>]*?>", "", svg_content, flags=re.IGNORECASE)
    sanitized = re.sub(r"\sxmlns:(?:inkscape|sodipodi)=\"[^\"]*\"", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\sxmlns:(?:inkscape|sodipodi)='[^']*'", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\s(?:sodipodi|inkscape):[\w.-]+=\"[^\"]*\"", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\s(?:sodipodi|inkscape):[\w.-]+='[^']*'", "", sanitized, flags=re.IGNORECASE)
    return sanitized


def _try_load_sample_svg(*, img_path: str, base_name: str, description: str = ""):
    local_samples_dir = os.path.join(os.path.dirname(img_path), "samples")
    fallback_dirs: list[str] = [local_samples_dir]
    env_dirs = os.environ.get("IMAGE_CONVERTER_SAMPLE_SVG_DIRS", "")
    for raw in env_dirs.split(os.pathsep):
        candidate = raw.strip()
        if candidate:
            fallback_dirs.append(candidate)
    repo_default = Path(__file__).resolve().parents[2] / "artifacts" / "images_to_convert" / "samples"
    fallback_dirs.append(str(repo_default))

    # de-duplicate and keep existing dirs only
    samples_dirs: list[str] = []
    seen_dirs: set[str] = set()
    for raw_dir in fallback_dirs:
        normalized = os.path.abspath(raw_dir)
        if normalized in seen_dirs or not os.path.isdir(normalized):
            continue
        seen_dirs.add(normalized)
        samples_dirs.append(normalized)

    sample_candidates = _build_sample_candidates(base_name)
    reference_family = _extract_reference_family_from_description(description)
    if reference_family and reference_family != base_name.upper():
        sample_candidates = _prepend_reference_candidates(sample_candidates, reference_family)
    for samples_dir in samples_dirs:
        for sample_name in sample_candidates:
            sample_svg_path = os.path.join(samples_dir, f"{sample_name}.svg")
            if not os.path.exists(sample_svg_path):
                continue
            with open(sample_svg_path, "r", encoding="utf-8") as handle:
                original_svg = handle.read()
            sanitized_svg = _sanitize_sample_svg(original_svg)
            if _is_inkscape_svg(original_svg) and sanitized_svg != original_svg:
                Path(sample_svg_path).write_text(sanitized_svg, encoding="utf-8")
            return sample_svg_path, sanitized_svg
    return None


def runNonCompositeIterationImpl(
    *,
    mode: str,
    params: dict[str, object],
    stripe_strategy: dict[str, object] | None,
    semantic_mode_visual_override: bool,
    width: int,
    height: int,
    base_name: str,
    description: str,
    perc_img,
    img_path: str,
    print_fn,
    render_embedded_raster_svg_fn,
    build_gradient_stripe_svg_fn,
    build_gradient_stripe_validation_log_lines_fn,
    write_validation_log_fn,
    render_svg_to_numpy_fn,
    record_render_failure_fn,
    write_attempt_artifacts_fn,
    calculate_error_fn,
    image_variant_name: str | None = None,
) -> tuple[str, str, dict[str, object], int, float] | None:
    sample_svg = _try_load_sample_svg(img_path=img_path, base_name=base_name, description=description)

    if mode == "manual_review":
        generated_svg_content = None
        generated_rendered = None
        generated_err = float("inf")
        generated_status = "manual_review_generated_vector_placeholder"

        if _description_requests_diagonal_band(description):
            print_fn("  -> Plan B Grundsatz: Diagonalbreite wird iterativ bestimmt (kein Fixwert).")
            best_diagonal = _fit_diagonal_band_iterative(
                width=width,
                height=height,
                description=description,
                perc_img=perc_img,
                render_svg_to_numpy_fn=render_svg_to_numpy_fn,
                calculate_error_fn=calculate_error_fn,
            )
            if best_diagonal is not None:
                generated_err, generated_svg_content, generated_rendered, stroke_w = best_diagonal
                generated_status = "manual_review_iterative_diagonal_band"
                generated_log_lines = [
                    "status=manual_review_iterative_diagonal_band",
                    f"iterative_stroke_width={stroke_w:.6f}",
                ]
            else:
                generated_log_lines = ["status=manual_review_iterative_diagonal_band_render_failed"]
        elif stripe_strategy:
            print_fn("  -> Plan B aktiv: nutze erkannte Gradient-Stripe-Strategie trotz Manual-Review.")
            generated_svg_content = build_gradient_stripe_svg_fn(width, height, stripe_strategy)
            strategy_stop_count = len(list(stripe_strategy.get("stops", [])))
            generated_rendered = render_svg_to_numpy_fn(generated_svg_content, width, height)
            if generated_rendered is None:
                record_render_failure_fn(
                    "manual_review_gradient_stripe_render_failed",
                    svg_content=generated_svg_content,
                    params_snapshot=params,
                )
            else:
                generated_err = calculate_error_fn(perc_img, generated_rendered)
                generated_status = "manual_review_gradient_stripe"
                generated_log_lines = build_gradient_stripe_validation_log_lines_fn(
                    semantic_mode_visual_override=semantic_mode_visual_override,
                    strategy_stop_count=strategy_stop_count,
                )
        else:
            print_fn("  -> Plan B aktiv: elementweise iterative Annäherung aus Rasterbild.")
            try:
                best_structured = _fit_symbol_element_by_element(
                    width=width,
                    height=height,
                    description=description,
                    perc_img=perc_img,
                    render_svg_to_numpy_fn=render_svg_to_numpy_fn,
                    calculate_error_fn=calculate_error_fn,
                )
                if best_structured is not None:
                    generated_err, generated_svg_content, generated_rendered, fitted_params, step_logs = best_structured
                else:
                    generated_rendered = None
            except Exception:
                generated_rendered = None
            if generated_rendered is not None and generated_svg_content is not None:
                generated_status = "manual_review_elementwise_symbol_fit"
                generated_log_lines = [
                    "status=manual_review_elementwise_symbol_fit",
                    *step_logs,
                    *[f"fit_{k}={v}" for k, v in sorted(fitted_params.items())],
                ]
            else:
                generated_svg_content = _build_vector_placeholder_svg(width, height, description=description)
                generated_rendered = render_svg_to_numpy_fn(generated_svg_content, width, height)
                if generated_rendered is None:
                    record_render_failure_fn(
                        "manual_review_vector_placeholder_render_failed",
                        svg_content=generated_svg_content,
                        params_snapshot=params,
                    )
                else:
                    generated_err = calculate_error_fn(perc_img, generated_rendered)
                generated_log_lines = ["status=manual_review_generated_vector_placeholder"]

        if sample_svg:
            sample_svg_path, sample_svg_content = sample_svg
            sample_rendered = render_svg_to_numpy_fn(sample_svg_content, width, height)
            if sample_rendered is None:
                record_render_failure_fn(
                    "manual_review_plan_b_render_failed",
                    svg_content=sample_svg_content,
                    params_snapshot=params,
                )
            else:
                sample_err = calculate_error_fn(perc_img, sample_rendered)
                if sample_err + 1e-6 < generated_err:
                    print_fn(
                        "  -> Plan B Vergleich aktiv: verwende vorhandene Sample-SVG "
                        f"{sample_svg_path} (sample={sample_err:.3f}, generated={generated_err:.3f})."
                    )
                    write_validation_log_fn(
                        [
                            "status=manual_review_plan_b_sample_svg",
                            f"sample_svg_path={sample_svg_path}",
                            f"sample_error={sample_err:.6f}",
                            f"generated_error={generated_err:.6f}",
                            f"generated_status={generated_status}",
                        ]
                    )
                    write_attempt_artifacts_fn(sample_svg_content, sample_rendered)
                    return base_name, description, params, 1, sample_err

        if generated_rendered is not None and generated_svg_content is not None:
            print_fn(
                "  -> Plan B Vergleich aktiv: verwende generierte Vektor-Lösung "
                f"(status={generated_status}, err={generated_err:.3f})."
            )
            write_validation_log_fn(generated_log_lines)
            write_attempt_artifacts_fn(generated_svg_content, generated_rendered)
            return base_name, description, params, 1, generated_err

        reason = str(params.get("review_reason", "Manuelle Prüfung erforderlich.")).strip()
        print_fn(f"  -> Überspringe Bild: {reason}")
        write_validation_log_fn(
            [
                "status=skipped_manual_review",
                f"manual_review_reason={reason}",
            ]
        )
        return None

    description_driven_algorithm_available = False
    if stripe_strategy:
        print_fn("  -> Fallback aktiv: verwende Gradient-Stripe-Strategie.")
        svg_content = build_gradient_stripe_svg_fn(width, height, stripe_strategy)
        strategy_stop_count = len(list(stripe_strategy.get("stops", [])))
        write_validation_log_fn(
            build_gradient_stripe_validation_log_lines_fn(
                semantic_mode_visual_override=semantic_mode_visual_override,
                strategy_stop_count=strategy_stop_count,
            )
        )
    else:
        print_fn("  -> Fallback aktiv: elementweise iterative Annäherung aus Rasterbild.")
        perception_seeded = _try_build_perception_seeded_geometry_ir_svg(
            width, height, description=description, perc_img=perc_img
        )
        description_geometry_ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description)
        resolved_variant_name = str(
            image_variant_name or params.get("variant_name") or Path(img_path).stem or base_name
        )
        description_geometry_ir = _apply_image_variant_geometry(
            description_geometry_ir, base_name=resolved_variant_name
        )
        geometry_ir_svg = (
            geometry_ir_helpers.renderGeometryIrToSvgImpl(width, height, description_geometry_ir)
            if description_geometry_ir
            and (
                DESCRIPTION_DRIVEN_GEOMETRY_IR_KINDS
                & {str(element.get("kind", "")) for element in description_geometry_ir}
            )
            else None
        )
        description_driven_algorithm_available = geometry_ir_svg is not None
        if perception_seeded is not None or geometry_ir_svg is not None:
            candidates: list[dict[str, object]] = []
            if perception_seeded is not None:
                seeded_svg, seeded_ir, perception_seed_count = perception_seeded
                seeded_rendered = render_svg_to_numpy_fn(seeded_svg, width, height)
                if seeded_rendered is None:
                    record_render_failure_fn(
                        "non_composite_perception_seeded_geometry_ir_render_failed",
                        svg_content=seeded_svg,
                        params_snapshot=params,
                    )
                else:
                    candidates.append(
                        {
                            "status": "non_composite_perception_seeded_geometry_ir",
                            "svg": seeded_svg,
                            "rendered": seeded_rendered,
                            "error": calculate_error_fn(perc_img, seeded_rendered),
                            "geometry_ir": seeded_ir,
                            "perception_seed_count": perception_seed_count,
                        }
                    )
            if geometry_ir_svg is not None:
                description_rendered = render_svg_to_numpy_fn(geometry_ir_svg, width, height)
                if description_rendered is None:
                    record_render_failure_fn(
                        "non_composite_geometry_ir_render_failed",
                        svg_content=geometry_ir_svg,
                        params_snapshot=params,
                    )
                else:
                    description_error = calculate_error_fn(perc_img, description_rendered)
                    optimizer_result = None
                    if hasattr(perc_img, "shape"):
                        optimizer_result = geometry_ir_optimizer.optimizeGeometryIrRegistrationImpl(
                            description_geometry_ir,
                            render_fn=lambda candidate_ir: render_svg_to_numpy_fn(
                                geometry_ir_helpers.renderGeometryIrToSvgImpl(width, height, candidate_ir),
                                width,
                                height,
                            ),
                            error_fn=lambda rendered: calculate_error_fn(perc_img, rendered),
                        )
                        if float(optimizer_result["final_error"]) < float(description_error):
                            description_geometry_ir = optimizer_result["geometry_ir"]
                            description_rendered = optimizer_result["rendered"]
                            description_error = float(optimizer_result["final_error"])
                            geometry_ir_svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(
                                width, height, description_geometry_ir
                            )
                            params["optimized_geometry_ir"] = description_geometry_ir
                        params["geometry_ir_optimizer_result"] = {
                            key: value
                            for key, value in optimizer_result.items()
                            if key not in {"geometry_ir", "rendered"}
                        }
                    candidates.append(
                        {
                            "status": "non_composite_description_geometry_ir",
                            "svg": geometry_ir_svg,
                            "rendered": description_rendered,
                            "error": description_error,
                            "geometry_ir": description_geometry_ir,
                            "perception_seed_count": 0,
                            "optimizer_result": optimizer_result,
                        }
                    )
            try:
                best_structured = _fit_symbol_element_by_element(
                    width=width,
                    height=height,
                    description=description,
                    perc_img=perc_img,
                    render_svg_to_numpy_fn=render_svg_to_numpy_fn,
                    calculate_error_fn=calculate_error_fn,
                )
            except Exception:
                best_structured = None
            if best_structured is not None:
                structured_err, structured_svg, structured_rendered, fitted_params, step_logs = best_structured
                candidates.append(
                    {
                        "status": "non_composite_elementwise_symbol_fit",
                        "svg": structured_svg,
                        "rendered": structured_rendered,
                        "error": structured_err,
                        "geometry_ir": [],
                        "perception_seed_count": 0,
                        "fit_params": fitted_params,
                        "step_logs": step_logs,
                    }
                )
            if not candidates:
                return None
            semantic_description_candidate = next(
                (
                    candidate
                    for candidate in candidates
                    if candidate["status"] == "non_composite_description_geometry_ir"
                    and _prefer_semantic_description_geometry(candidate["geometry_ir"])
                ),
                None,
            )
            if semantic_description_candidate is not None:
                best_geometry_candidate = semantic_description_candidate
                selection_reason = "semantic_description_geometry"
            else:
                best_geometry_candidate = min(candidates, key=lambda candidate: float(candidate["error"]))
                selection_reason = "best_pixel_error"
            svg_content = str(best_geometry_candidate["svg"])
            svg_rendered = best_geometry_candidate["rendered"]
            svg_err = float(best_geometry_candidate["error"])
            geometry_ir = best_geometry_candidate["geometry_ir"]
            perception_seed_count = int(best_geometry_candidate["perception_seed_count"])
            status = str(best_geometry_candidate["status"])
            log_lines = [f"status={status}"]
            if status == "non_composite_elementwise_symbol_fit":
                log_lines.extend(str(line) for line in best_geometry_candidate.get("step_logs", []))
                fit_params = best_geometry_candidate.get("fit_params", {})
                if isinstance(fit_params, dict):
                    log_lines.extend(f"fit_{k}={v}" for k, v in sorted(fit_params.items()))
            else:
                if perception_seed_count:
                    log_lines.extend(
                        [
                            f"perception_seeded_geometry_ir=1",
                            f"perception_seed_count={perception_seed_count}",
                        ]
                    )
                optimizer_result = best_geometry_candidate.get("optimizer_result")
                if isinstance(optimizer_result, dict):
                    log_lines.extend(
                        [
                            "geometry_ir_raster_registration=1",
                            f"geometry_ir_registration_initial_error={float(optimizer_result['initial_error']):.6f}",
                            f"geometry_ir_registration_final_error={float(optimizer_result['final_error']):.6f}",
                            *(
                                f"geometry_ir_registration_{key}={float(value):.6f}"
                                for key, value in optimizer_result["parameters"].items()
                            ),
                        ]
                    )
                    element_refinement = optimizer_result.get("element_refinement")
                    if isinstance(element_refinement, dict) and element_refinement.get("steps"):
                        log_lines.extend(
                            [
                                "geometry_ir_element_refinement=1",
                                f"geometry_ir_element_refinement_initial_error={float(element_refinement['initial_error']):.6f}",
                                f"geometry_ir_element_refinement_final_error={float(element_refinement['final_error']):.6f}",
                                f"geometry_ir_element_refinement_steps={len(element_refinement['steps'])}",
                            ]
                        )
                log_lines.extend(
                    [
                        f"geometry_ir_element_count={len(geometry_ir)}",
                        *(
                            f"geometry_ir_element_{idx}={element.get('kind')}"
                            for idx, element in enumerate(geometry_ir, start=1)
                        ),
                        *(
                            f"geometry_ir_handle_shape_{idx}={element.get('handle_shape')}"
                            for idx, element in enumerate(geometry_ir, start=1)
                            if element.get("handle_shape")
                        ),
                    ]
                )
            if len(candidates) > 1:
                log_lines.append(f"non_composite_selection={selection_reason}")
                for candidate in candidates:
                    log_lines.append(
                        f"non_composite_candidate_error_{candidate['status']}={float(candidate['error']):.6f}"
                    )
            write_validation_log_fn(log_lines)
        else:
            description_driven_algorithm_available = False
            try:
                best_structured = _fit_symbol_element_by_element(
                    width=width,
                    height=height,
                    description=description,
                    perc_img=perc_img,
                    render_svg_to_numpy_fn=render_svg_to_numpy_fn,
                    calculate_error_fn=calculate_error_fn,
                )
            except Exception:
                best_structured = None
            if best_structured is not None:
                svg_err, svg_content, svg_rendered, fitted_params, step_logs = best_structured
                write_validation_log_fn(
                    [
                        "status=non_composite_elementwise_symbol_fit",
                        *step_logs,
                        *[f"fit_{k}={v}" for k, v in sorted(fitted_params.items())],
                    ]
                )
            else:
                print_fn("  -> Fallback aktiv: verwende reine SVG-Platzhalter-Konvertierung (kein eingebettetes Raster).")
                svg_content = _build_vector_placeholder_svg(width, height, description=description)
                write_validation_log_fn(["status=non_composite_pure_svg_placeholder_vector"])
                svg_rendered = render_svg_to_numpy_fn(svg_content, width, height)
                if svg_rendered is None:
                    record_render_failure_fn(
                        "non_composite_pure_svg_render_failed",
                        svg_content=svg_content,
                        params_snapshot=params,
                    )
                    return None
                svg_err = calculate_error_fn(perc_img, svg_rendered)
                # continue with plan-b sample comparison below using placeholder baseline

    if stripe_strategy:
        svg_rendered = render_svg_to_numpy_fn(svg_content, width, height)
        if svg_rendered is None:
            record_render_failure_fn(
                "non_composite_pure_svg_render_failed",
                svg_content=svg_content,
                params_snapshot=params,
            )
            return None
        svg_err = calculate_error_fn(perc_img, svg_rendered)

    if sample_svg and not description_driven_algorithm_available:
        sample_svg_path, sample_svg_content = sample_svg
        sample_rendered = render_svg_to_numpy_fn(sample_svg_content, width, height)
        if sample_rendered is not None:
            sample_err = calculate_error_fn(perc_img, sample_rendered)
            baseline_is_embedded_raster = _contains_svg_image_tag(svg_content)
            # Favor curated sample SVGs only when they materially improve the
            # current algorithmic result (or replace an embedded raster).  This
            # keeps samples as fallback evidence, not as per-symbol fixed output.
            sample_preference_factor = 1.08 if baseline_is_embedded_raster else 1.25
            sample_improvement_ratio = (svg_err / sample_err) if sample_err > 0 else float("inf")
            prefer_sample_svg = (
                baseline_is_embedded_raster
                or sample_improvement_ratio >= sample_preference_factor
            )
            if prefer_sample_svg:
                decision_note = ""
                if baseline_is_embedded_raster and sample_err > svg_err:
                    decision_note = " (Vector-Sample gegenüber Embedded-Raster bevorzugt)"
                print_fn(
                    "  -> Plan B Vergleich aktiv: nutze Sample-SVG "
                    f"{sample_svg_path} (err={sample_err:.3f}, baseline={svg_err:.3f})."
                    f"{decision_note}"
                )
                write_validation_log_fn(
                    [
                        "status=non_composite_plan_b_sample_svg_selected",
                        f"sample_svg_path={sample_svg_path}",
                        f"sample_error={sample_err:.6f}",
                        f"baseline_error={svg_err:.6f}",
                        f"baseline_is_embedded_raster={int(baseline_is_embedded_raster)}",
                        f"sample_preference_factor={sample_preference_factor:.2f}",
                        f"sample_improvement_ratio={sample_improvement_ratio:.6f}",
                        "sample_selection_policy=algorithmic_threshold",
                    ]
                )
                write_attempt_artifacts_fn(sample_svg_content, sample_rendered)
                return base_name, description, params, 1, sample_err
        else:
            if _contains_svg_image_tag(svg_content):
                print_fn(
                    "  -> Plan B Vergleich aktiv: nutze Sample-SVG "
                    f"{sample_svg_path} trotz fehlendem Raster-Render (Embedded-Raster vermeiden)."
                )
                write_validation_log_fn(
                    [
                        "status=non_composite_plan_b_sample_svg_selected",
                        f"sample_svg_path={sample_svg_path}",
                        "sample_render_failed=1",
                        f"baseline_error={svg_err:.6f}",
                        "baseline_is_embedded_raster=1",
                        "sample_preference_factor=forced",
                    ]
                )
                write_attempt_artifacts_fn(sample_svg_content, None)
                return base_name, description, params, 1, svg_err

    write_attempt_artifacts_fn(svg_content, svg_rendered)
    return base_name, description, params, 1, svg_err
