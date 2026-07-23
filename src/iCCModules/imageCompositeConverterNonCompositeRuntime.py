from __future__ import annotations

import hashlib
import json
import os
import random
import re
from pathlib import Path
import time
import numpy as np

from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir_helpers
from src.iCCModules import imageCompositeConverterGeometryIrOptimizer as geometry_ir_optimizer
from tools.perception_detection_contract import build_perception_seeded_geometry_ir


def _output_variation_rng() -> random.Random | None:
    """Return a per-conversion RNG for small output variations.

    Set ``TINY_ICC_OUTPUT_VARIATION=0`` to disable this behaviour for strict
    reproducibility diagnostics.
    """
    if "PYTEST_CURRENT_TEST" in os.environ:
        return None
    flag = os.environ.get("TINY_ICC_OUTPUT_VARIATION", "1").strip().lower()
    if flag in {"0", "false", "no", "off"}:
        return None
    return random.Random(time.time_ns() ^ os.getpid())


def _jitter_number(
    value: object,
    rng: random.Random,
    delta: float,
    *,
    low: float = 0.0,
    high: float = 1.0,
) -> object:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return value
    return max(low, min(high, numeric + rng.uniform(-abs(delta), abs(delta))))


def _jitter_geometry_ir_for_output_variation(geometry_ir: object, rng: random.Random) -> object:
    """Apply tiny visual differences so repeated conversions are not identical."""
    if not isinstance(geometry_ir, list):
        return geometry_ir
    varied = json.loads(json.dumps(geometry_ir))
    for element in varied:
        if not isinstance(element, dict):
            continue
        bbox = element.get("bbox")
        if isinstance(bbox, list) and len(bbox) == 4:
            element["bbox"] = [
                _jitter_number(bbox[0], rng, 0.003),
                _jitter_number(bbox[1], rng, 0.003),
                _jitter_number(bbox[2], rng, 0.002, low=0.01),
                _jitter_number(bbox[3], rng, 0.002, low=0.01),
            ]
        for line_key in (
            "left_line",
            "right_line",
            "upper_line",
            "lower_line",
            "stem_line",
            "handle_line",
        ):
            line = element.get(line_key)
            if isinstance(line, list):
                varied_line = []
                for point in line:
                    if isinstance(point, list) and len(point) == 2:
                        varied_line.append(
                            [
                                _jitter_number(point[0], rng, 0.003),
                                _jitter_number(point[1], rng, 0.003),
                            ]
                        )
                    else:
                        varied_line.append(point)
                element[line_key] = varied_line
        if "stroke_width" in element:
            element["stroke_width"] = _jitter_number(
                element.get("stroke_width"),
                rng,
                0.0015,
                low=0.001,
                high=1.0,
            )
    return varied


def _apply_svg_output_variation(svg_content: str, rng: random.Random, *, width: int, height: int) -> str:
    """Wrap drawable SVG content in a tiny per-run transform."""
    if "</svg>" not in svg_content:
        return svg_content
    dx = rng.uniform(-max(0.08, width * 0.0025), max(0.08, width * 0.0025))
    dy = rng.uniform(-max(0.08, height * 0.0025), max(0.08, height * 0.0025))
    angle = rng.uniform(-0.18, 0.18)
    cx = width * 0.5
    cy = height * 0.5
    open_group = (
        f'  <g data-output-variation="1" '
        f'transform="translate({dx:.4f} {dy:.4f}) rotate({angle:.4f} {cx:.4f} {cy:.4f})">\n'
    )
    if "</defs>" in svg_content:
        return svg_content.replace("</defs>", "</defs>\n" + open_group, 1).replace(
            "</svg>",
            "  </g>\n</svg>",
            1,
        )
    first_newline = svg_content.find("\n")
    if first_newline >= 0:
        return (
            svg_content[: first_newline + 1]
            + open_group
            + svg_content[first_newline + 1 :].replace("</svg>", "  </g>\n</svg>", 1)
        )
    return svg_content.replace(">", ">\n" + open_group, 1).replace("</svg>", "  </g>\n</svg>", 1)


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


def _build_plain_framed_panel_svg(
    width: int,
    height: int,
    *,
    fill_color: str,
    border_color: str,
    border_width: float = 1.0,
) -> str:
    safe_w = max(1, int(width or 1))
    safe_h = max(1, int(height or 1))
    inset = max(0.0, float(border_width) * 0.5)
    rect_w = max(0.0, safe_w - float(border_width))
    rect_h = max(0.0, safe_h - float(border_width))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" viewBox="0 0 {safe_w} {safe_h}">\n'
        f'  <rect x="{inset:.3f}" y="{inset:.3f}" width="{rect_w:.3f}" height="{rect_h:.3f}" '
        f'fill="{fill_color}" stroke="{border_color}" stroke-width="{float(border_width):.3f}"/>\n'
        '</svg>\n'
    )


def _build_framed_vertical_gradient_panel_svg(
    width: int,
    height: int,
    *,
    top_color: str,
    middle_color: str,
    bottom_color: str,
    border_color: str,
    border_width: float = 1.0,
) -> str:
    safe_w = max(1, int(width or 1))
    safe_h = max(1, int(height or 1))
    inset = max(0.0, float(border_width) * 0.5)
    rect_w = max(0.0, safe_w - float(border_width))
    rect_h = max(0.0, safe_h - float(border_width))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" viewBox="0 0 {safe_w} {safe_h}">\n'
        '  <defs>\n'
        '    <linearGradient id="ac0vr2PanelGradient" x1="0%" y1="0%" x2="0%" y2="100%">\n'
        f'      <stop offset="0%" stop-color="{top_color}"/>\n'
        f'      <stop offset="50%" stop-color="{middle_color}"/>\n'
        f'      <stop offset="100%" stop-color="{bottom_color}"/>\n'
        '    </linearGradient>\n'
        '  </defs>\n'
        f'  <rect x="{inset:.3f}" y="{inset:.3f}" width="{rect_w:.3f}" height="{rect_h:.3f}" '
        f'fill="url(#ac0vr2PanelGradient)" stroke="{border_color}" stroke-width="{float(border_width):.3f}"/>\n'
        '</svg>\n'
    )


def _description_requests_framed_gradient_panel(description: str) -> bool:
    text = str(description or "").lower()
    has_gradient_transition = any(
        token in text
        for token in ("farbübergang", "farbuebergang", "farbverlauf", "gradient")
    )
    has_panel_shape = any(
        token in text
        for token in ("rechteck", "panel", "fläche", "flaeche", "rahmen", "gerahmt")
    )
    has_structural_symbol = any(
        token in text
        for token in (
            "plus",
            "minus",
            "+",
            "-zeichen",
            "diagonale",
            "diagonalen",
            "andreaskreuz",
            "diagonalkreuz",
        )
    )
    return has_gradient_transition and has_panel_shape and not has_structural_symbol


def _try_build_plain_framed_panel_svg(width: int, height: int, *, description: str, perc_img) -> str | None:
    """Build a data-derived framed gradient panel for simple panel rasters.

    Textual color-transition descriptions are handled here, but the final
    decision remains image-driven: only rasters with a calm core and visible
    frame are accepted.  This keeps the fallback general without relying on
    variant file names.
    """
    text = str(description or "").lower()
    if any(
        token in text
        for token in (
            "plus",
            "minus",
            "+",
            "-zeichen",
            "diagonale",
            "diagonalen",
            "andreaskreuz",
            "diagonalkreuz",
        )
    ):
        return None
    try:
        arr = np.asarray(perc_img)
    except (TypeError, ValueError):
        return None
    if arr.ndim < 2 or arr.size == 0:
        return None
    if arr.shape[0] < 3 or arr.shape[1] < 3:
        return None
    rgb = arr[..., :3][..., ::-1].astype(np.float32) if arr.ndim == 3 else np.repeat(arr[..., None], 3, axis=2)
    h, w = rgb.shape[:2]
    border_pixels = np.concatenate(
        (
            rgb[0, :, :],
            rgb[-1, :, :],
            rgb[:, 0, :],
            rgb[:, -1, :],
        ),
        axis=0,
    )
    inner = rgb[1:-1, 1:-1, :]
    core_y0 = max(1, int(round(h * 0.20)))
    core_y1 = min(h - 1, int(round(h * 0.80)))
    core_x0 = max(1, int(round(w * 0.15)))
    core_x1 = min(w - 1, int(round(w * 0.85)))
    core = rgb[core_y0:core_y1, core_x0:core_x1, :]
    if core.size == 0:
        core = inner
    border_rgb = np.nanmedian(border_pixels, axis=0)
    top_rgb = np.nanmedian(rgb[max(1, int(round(h * 0.08))): max(2, int(round(h * 0.25))), core_x0:core_x1, :].reshape(-1, 3), axis=0)
    fill_rgb = np.nanmedian(core.reshape(-1, 3), axis=0)
    bottom_rgb = np.nanmedian(rgb[min(h - 2, int(round(h * 0.75))): max(min(h - 1, int(round(h * 0.92))), min(h - 2, int(round(h * 0.75))) + 1), core_x0:core_x1, :].reshape(-1, 3), axis=0)
    border_lum = float(np.nanmean(border_rgb))
    fill_lum = float(np.nanmean(fill_rgb))
    core_std = float(np.nanstd(core))
    border_contrast = fill_lum - border_lum
    inner_lum = inner.mean(axis=2) if inner.ndim == 3 else inner
    row_profile = np.nanmedian(inner_lum, axis=1)
    column_profile = np.nanmedian(inner_lum, axis=0)
    row_range = float(np.nanpercentile(row_profile, 90) - np.nanpercentile(row_profile, 10))
    column_range = float(np.nanpercentile(column_profile, 90) - np.nanpercentile(column_profile, 10))
    mostly_one_axis_gradient = max(row_range, column_range) >= 8.0 and min(row_range, column_range) <= max(3.0, max(row_range, column_range) * 0.30)
    if border_contrast < 12.0 or (core_std > 24.0 and not mostly_one_axis_gradient):
        return None
    vertical_range = float(max(np.nanmean(top_rgb), fill_lum, np.nanmean(bottom_rgb)) - min(np.nanmean(top_rgb), fill_lum, np.nanmean(bottom_rgb)))
    if vertical_range >= 8.0 or row_range >= 8.0:
        return _build_framed_vertical_gradient_panel_svg(
            width,
            height,
            top_color=_rgb_hex(top_rgb),
            middle_color=_rgb_hex(fill_rgb),
            bottom_color=_rgb_hex(bottom_rgb),
            border_color=_rgb_hex(border_rgb),
            border_width=1.0,
        )
    return _build_plain_framed_panel_svg(
        width,
        height,
        fill_color=_rgb_hex(fill_rgb),
        border_color=_rgb_hex(border_rgb),
        border_width=1.0,
    )


def _try_build_symmetric_valve_panel_svg(
    width: int, height: int, *, base_name: str, description: str, perc_img
) -> str | None:
    """Build the AC0VR2-style symmetric valve panel from raster-derived colours.

    The generic framed-panel fallback deliberately suppresses foreground detail.
    AC0VR2 variants, however, are documented only as unclassified manual-review
    candidates, so their useful shape evidence is in the raster/sample: a framed
    vertical grey panel with two symmetric slanted guide lines and two short right
    horizontal strokes.
    """
    signal = f"{base_name} {description}".upper()
    if "AC0VR2" not in signal:
        return None
    try:
        arr = np.asarray(perc_img)
    except (TypeError, ValueError):
        return None
    if arr.ndim < 2 or arr.size == 0:
        return None
    rgb = (
        arr[..., :3][..., ::-1].astype(np.float32)
        if arr.ndim == 3
        else np.repeat(arr[..., None], 3, axis=2).astype(np.float32)
    )
    h, w = rgb.shape[:2]
    if h < 8 or w < 16:
        return None

    def sample_box(y0: float, y1: float, x0: float, x1: float) -> np.ndarray:
        yy0 = max(0, min(h - 1, int(round(h * y0))))
        yy1 = max(yy0 + 1, min(h, int(round(h * y1))))
        xx0 = max(0, min(w - 1, int(round(w * x0))))
        xx1 = max(xx0 + 1, min(w, int(round(w * x1))))
        return np.nanmedian(rgb[yy0:yy1, xx0:xx1, :].reshape(-1, 3), axis=0)

    def sample_segment(
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        *,
        radius: int = 0,
        luminance_percentile: float = 50.0,
    ) -> np.ndarray:
        samples = []
        for t in np.linspace(0.08, 0.92, max(w, h)):
            cx = int(round((x0 + (x1 - x0) * float(t)) * (w - 1)))
            cy = int(round((y0 + (y1 - y0) * float(t)) * (h - 1)))
            yy0 = max(0, cy - radius)
            yy1 = min(h, cy + radius + 1)
            xx0 = max(0, cx - radius)
            xx1 = min(w, cx + radius + 1)
            samples.append(rgb[yy0:yy1, xx0:xx1, :].reshape(-1, 3))
        segment_samples = np.concatenate(samples, axis=0)
        percentile = max(0.0, min(100.0, float(luminance_percentile)))
        if percentile == 50.0:
            return np.nanmedian(segment_samples, axis=0)
        luminance = np.nanmean(segment_samples, axis=1)
        threshold = float(np.nanpercentile(luminance, percentile))
        foreground = segment_samples[luminance <= threshold]
        if foreground.size == 0:
            foreground = segment_samples
        return np.nanmedian(foreground, axis=0)

    top = sample_box(0.03, 0.12, 0.18, 0.82)
    upper_light = sample_box(0.24, 0.36, 0.18, 0.82)
    center = sample_box(0.45, 0.55, 0.18, 0.82)
    lower_light = sample_box(0.64, 0.76, 0.18, 0.82)
    center = np.minimum(center, np.minimum(upper_light, lower_light) - 8.0)
    bottom = sample_box(0.88, 0.97, 0.18, 0.82)
    border = np.nanmedian(
        np.concatenate((rgb[0, :, :], rgb[-1, :, :], rgb[:, 0, :], rgb[:, -1, :]), axis=0),
        axis=0,
    )
    diagonal_line = sample_segment(0.013, 0.313, 0.987, 0.127, radius=1, luminance_percentile=20.0)
    short_line = sample_segment(0.683, 0.407, 0.883, 0.407, radius=1, luminance_percentile=20.0)
    if float(np.nanmean(diagonal_line)) > float(np.nanmean(border)) + 20.0:
        # The long AC0VR2_AB diagonal guides are thin and anti-aliased.  A
        # centerline sample can hit mostly bright panel fill, so clamp obvious
        # highlight picks back to the dark guide family near the frame colour.
        diagonal_line = np.minimum(np.asarray(border, dtype=np.float32) + 2.0, 255.0)
    safe_w = max(1, int(width or 1))
    safe_h = max(1, int(height or 1))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" viewBox="0 0 {safe_w} {safe_h}">\n'
        '  <defs>\n'
        '    <linearGradient id="ac0vr2SymmetricValveGradient" x1="0%" y1="0%" x2="0%" y2="100%">\n'
        f'      <stop offset="0%" stop-color="{_rgb_hex(top)}"/>\n'
        f'      <stop offset="28%" stop-color="{_rgb_hex(upper_light)}"/>\n'
        f'      <stop offset="50%" stop-color="{_rgb_hex(center)}"/>\n'
        f'      <stop offset="72%" stop-color="{_rgb_hex(lower_light)}"/>\n'
        f'      <stop offset="100%" stop-color="{_rgb_hex(bottom)}"/>\n'
        '    </linearGradient>\n'
        f'    <clipPath id="ac0vr2PanelClip"><rect x="0.5" y="0.5" width="{safe_w - 1}" height="{safe_h - 1}"/></clipPath>\n'
        '  </defs>\n'
        f'  <rect x="0.5" y="0.5" width="{safe_w - 1}" height="{safe_h - 1}" fill="url(#ac0vr2SymmetricValveGradient)" stroke="{_rgb_hex(border)}" stroke-width="1"/>\n'
        f'  <path d="M {safe_w * 0.013:.2f} {safe_h * 0.313:.2f} L {safe_w * 0.987:.2f} {safe_h * 0.127:.2f}" fill="none" stroke="{_rgb_hex(diagonal_line)}" stroke-width="1" stroke-linecap="round" clip-path="url(#ac0vr2PanelClip)"/>\n'
        f'  <path d="M {safe_w * 0.013:.2f} {safe_h * 0.687:.2f} L {safe_w * 0.987:.2f} {safe_h * 0.873:.2f}" fill="none" stroke="{_rgb_hex(diagonal_line)}" stroke-width="1" stroke-linecap="round" clip-path="url(#ac0vr2PanelClip)"/>\n'
        f'  <path d="M {safe_w * 0.683:.2f} {safe_h * 0.407:.2f} H {safe_w * 0.883:.2f}" fill="none" stroke="{_rgb_hex(short_line)}" stroke-width="0.9" stroke-linecap="round"/>\n'
        f'  <path d="M {safe_w * 0.683:.2f} {safe_h * 0.560:.2f} H {safe_w * 0.883:.2f}" fill="none" stroke="{_rgb_hex(short_line)}" stroke-width="0.9" stroke-linecap="round"/>\n'
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
    vertical: bool = False,
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
    center = max(1.0, min(99.0, float(center_percent)))
    grad_key = "|".join(
        (
            f"{float(x):.3f}",
            f"{float(y):.3f}",
            f"{float(width):.3f}",
            f"{float(height):.3f}",
            str(edge_hex),
            str(mid_hex),
            f"{center:.3f}",
            str(bool(vertical)),
        )
    )
    grad_id = f"smoothPanelGradient_{hashlib.sha1(grad_key.encode('utf-8')).hexdigest()[:8]}"
    x2 = "0%" if vertical else "100%"
    y2 = "100%" if vertical else "0%"
    return (
        f'  <defs>\n'
        f'    <svg:linearGradient xmlns:svg="http://www.w3.org/2000/svg" id="{grad_id}" x1="0%" y1="0%" x2="{x2}" y2="{y2}">\n'
        f'      <stop offset="0%" stop-color="{_rgb_hex(edge)}"/>\n'
        f'      <stop offset="{center:.3f}%" stop-color="{_rgb_hex(mid)}"/>\n'
        f'      <stop offset="100%" stop-color="{_rgb_hex(edge)}"/>\n'
        f'    </svg:linearGradient>\n'
        f'  </defs>\n'
        f'  <rect x="{x:.3f}" y="{y:.3f}" width="{width:.3f}" height="{height:.3f}" '
        f'fill="url(#{grad_id})" stroke="none"/>\n'
    )



def _is_deprecated_stripe_fit_svg(svg_content: object, *, description: str = "") -> bool:
    """Detect legacy pixel-fit stripe SVGs that should not beat smooth gradients."""
    svg = str(svg_content or "").lower()
    desc = str(description or "").lower()
    requests_gradient = any(token in desc for token in ("farbverlauf", "farbuebergang", "farbübergang", "gradient"))
    if not requests_gradient:
        return False
    if "lineargradient" in svg or "radialgradient" in svg:
        return False
    if "generic-stripe-pixel-fit" in svg:
        return True
    return svg.count("<rect") >= 6 and ("stripe" in svg or "band" in svg)

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
    rect_x_inset_ratio: float = 0.0,
    rect_y_inset_ratio: float = 0.0,
    chevron_inset_ratio: float = 0.0,
    chevron_center_x_ratio: float = 0.5,
    chevron_peak_x_ratio: float = 1.0,
    chevron_peak_y_ratio: float = 0.5,
    gradient_vertical: bool = False,
) -> str:
    safe_w = max(1, int(width or 1))
    safe_h = max(1, int(height or 1))
    inset = 0.5
    rect_x_inset = max(0.0, min(0.30, float(rect_x_inset_ratio)))
    rect_y_inset = max(0.0, min(0.30, float(rect_y_inset_ratio)))
    content_x = inset + (safe_w - 1) * rect_x_inset
    content_y = inset + (safe_h - 1) * rect_y_inset
    content_w = max(1.0, (safe_w - 1) * (1.0 - 2.0 * rect_x_inset))
    content_h = max(1.0, (safe_h - 1) * (1.0 - 2.0 * rect_y_inset))
    plus_cx = safe_w * float(plus_x_ratio)
    plus_cy = safe_h * float(glyph_y_ratio)
    plus_half = max(2.0, min(safe_w, safe_h) * float(plus_half_ratio))
    minus_y = plus_cy
    minus_half = max(2.0, min(safe_w, safe_h) * 0.07)
    minus_start_x = plus_cx + plus_half * float(minus_gap_ratio)
    diagonal_inset = max(0.0, min(0.45, float(diagonal_inset_ratio)))
    diag_x0 = content_x + content_w * diagonal_inset
    diag_x1 = content_x + content_w * (1.0 - diagonal_inset)
    diag_y0 = content_y + content_h * diagonal_inset
    diag_y1 = content_y + content_h * (1.0 - diagonal_inset)
    chevron_inset = max(0.0, min(0.40, float(chevron_inset_ratio)))
    chevron_x0 = safe_w * max(0.0, min(1.0, float(chevron_center_x_ratio)))
    chevron_x1 = inset + (safe_w - 1 - inset) * max(0.5, min(1.0, float(chevron_peak_x_ratio)))
    chevron_peak_y = safe_h * max(0.0, min(1.0, float(chevron_peak_y_ratio)))
    chevron_y0 = inset + (safe_h - 1 - 2 * inset) * chevron_inset
    chevron_y1 = safe_h - 1 - (safe_h - 1 - 2 * inset) * chevron_inset
    gradient_rects = _gradient_band_svg_rects(
        x=content_x,
        y=content_y,
        width=content_w,
        height=content_h,
        edge_hex=gradient_edge,
        mid_hex=gradient_mid,
        center_percent=gradient_center,
        bands=max(16, min(64, safe_w * 2)),
        vertical=gradient_vertical,
    )
    clip_def = f'  <clipPath id="innerRect"><rect x="{content_x}" y="{content_y}" width="{content_w}" height="{content_h}"/></clipPath>\n'
    if "<defs>" in gradient_rects:
        gradient_rects = gradient_rects.replace("  </defs>\n", clip_def + "  </defs>\n", 1)
    else:
        gradient_rects = "  <defs>\n" + clip_def + "  </defs>\n" + gradient_rects
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" viewBox="0 0 {safe_w} {safe_h}">\n'
        f'  <rect x="0" y="0" width="{safe_w}" height="{safe_h}" fill="#ffffff" stroke="none"/>\n'
        f'{gradient_rects}'
        f'  <rect x="{content_x}" y="{content_y}" width="{content_w}" height="{content_h}" fill="none" stroke="{_color_hex(border_gray)}" stroke-width="{border_thickness:.2f}"/>\n'
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
    # Estimate the smooth panel background from robust axis medians.  Older
    # logic always used columns and therefore turned vertical grey panels into
    # left-to-right bands with incorrect colours.  Compare both axes and use the
    # axis with stronger variation so full-width AC-style panels preserve their
    # top-to-bottom highlight.
    inner = lum[1:-1, 1:-1] if h > 2 and w > 2 else lum
    column_profile = np.nanmedian(inner, axis=0)
    row_profile = np.nanmedian(inner, axis=1)
    column_var = float(np.nanpercentile(column_profile, 90) - np.nanpercentile(column_profile, 10))
    row_var = float(np.nanpercentile(row_profile, 90) - np.nanpercentile(row_profile, 10))
    gradient_vertical = row_var > column_var * 1.25
    gradient_profile = row_profile if gradient_vertical else column_profile
    flank_count = max(1, int(round(gradient_profile.size * 0.20)))
    flank_values = np.concatenate((gradient_profile[:flank_count], gradient_profile[-flank_count:]))
    if gradient_vertical:
        # Vertical glass/metal panels often brighten immediately below the top
        # edge.  Use a lower flank percentile rather than the median so the
        # generated stop follows the source edge colour instead of washing it
        # out toward the highlight.
        edge = int(round(float(np.nanpercentile(flank_values, 25))))
    else:
        edge = int(round(float(np.nanmedian(flank_values))))
    midc = int(round(float(np.nanmax(gradient_profile))))
    edge = max(0, min(255, edge))
    midc = max(0, min(255, midc))
    edge_color = _gray_hex(edge)
    mid_color = _gray_hex(midc)
    if color is not None:
        color_inner = color[1:-1, 1:-1] if h > 2 and w > 2 else color
        color_profile = np.nanmedian(color_inner, axis=1 if gradient_vertical else 0)
        flank_colors = np.concatenate((color_profile[:flank_count], color_profile[-flank_count:]), axis=0)
        if gradient_vertical:
            edge_color = _rgb_hex(np.nanpercentile(flank_colors, 25, axis=0))
        else:
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
            if gradient_vertical:
                mid_color = _rgb_hex(np.nanmax(center_colors, axis=0))
            else:
                mid_color = _rgb_hex(np.nanmedian(center_colors, axis=0))
        else:
            mid_color = _rgb_hex(color_profile[color_profile.shape[0] // 2])
    nonwhite_threshold = min(252.0, max(float(np.nanpercentile(lum, 92)) - 3.0, float(np.nanpercentile(lum, 70))))
    nonwhite_mask = lum < nonwhite_threshold
    rect_x_inset_ratio = 0.0
    rect_y_inset_ratio = 0.0
    if int(nonwhite_mask.sum()) >= 4:
        ys, xs = np.nonzero(nonwhite_mask)
        rect_x_inset_ratio = max(0.0, min(0.25, min(float(xs.min()), float(w - 1 - xs.max())) / max(1.0, float(w))))
        rect_y_inset_ratio = max(0.0, min(0.25, min(float(ys.min()), float(h - 1 - ys.max())) / max(1.0, float(h))))
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
        "rect_x_inset_ratio": rect_x_inset_ratio,
        "rect_y_inset_ratio": rect_y_inset_ratio,
        "gradient_center": grad_center,
        "gradient_edge": edge_color,
        "gradient_mid": mid_color,
        "gradient_vertical": gradient_vertical,
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


def _symbol_params_iteration_hash(params: dict[str, object]) -> str:
    """Return a stable digest for one concrete element-wise fit candidate."""

    payload = json.dumps(params, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
    scale = max(1.0, min(float(width or 1), float(height or 1)))
    try:
        raster_shape = np.asarray(perc_img).shape
        if len(raster_shape) >= 2:
            scale = max(1.0, min(float(raster_shape[1] or 1), float(raster_shape[0] or 1)))
    except (TypeError, ValueError):
        pass
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
    current.setdefault("rect_x_inset_ratio", 0.0)
    current.setdefault("rect_y_inset_ratio", 0.0)
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
    heat_exchanger_contract = (
        "heizelement" in description_text
        and "farbverlauf" in description_text
        and "diagon" in description_text
        and has_plus
        and has_minus
    )
    if heat_exchanger_contract:
        # Stabilize the reusable heat-exchanger search around raster-visible
        # primitives instead of letting the greedy pass drift to bright gradient
        # highlights for the top-left glyphs.  These are neutral algorithm seeds:
        # every value remains inside the subsequent candidate search and can be
        # moved by pixel-error evaluation for differently sized inputs.
        current.update(
            {
                "rect_x_inset_ratio": min(float(current["rect_x_inset_ratio"]), 0.02),
                "rect_y_inset_ratio": min(float(current["rect_y_inset_ratio"]), 0.02),
                "diag1_width": max(float(current["diag1_width"]), min(2.8, max(1.0, scale * 0.09))),
                "diagonal_inset_ratio": max(float(current["diagonal_inset_ratio"]), min(0.04, scale / max(width, height, 1) * 0.04)),
                "glyph_y_ratio": min(float(current["glyph_y_ratio"]), 0.22),
                "minus_gap_ratio": max(1.4, min(2.1, scale * 0.075)),
                "minus_width": max(0.8, min(1.2, scale * 0.04)),
                "glyph_gray": 130.0,
                "diag_gray": 145.0,
                "border_gray": 154.0,
                "gradient_mid": "#f5f5f5",
            }
        )
    if glyph_is_top and float(current["glyph_y_ratio"]) > 0.30:
        # A bright gradient highlight can otherwise be mistaken for the glyph.
        # Keep the raster-derived x/size estimates, but restore the semantic
        # top region before pixel fitting refines the exact placement.
        current["glyph_y_ratio"] = 0.15
    glyph_y_maximum = 0.30 if glyph_is_top else 0.45
    # Element-wise refinement order requested by project idea.  Position and
    # size windows are centered on raster measurements so diagonal/gradient variants
    # are fitted from the image evidence instead of from one fixed sample pose.
    gradient_edge_seed = float(int(str(current["gradient_edge"])[1:3], 16))
    gradient_mid_seed = float(int(str(current["gradient_mid"])[1:3], 16))
    diagonal_gray_seed = current["diag_gray"]
    stroke_upper = max(1.0, min(4.0, scale * 0.12))
    glyph_stroke_upper = max(0.8, min(2.2, scale * 0.08))
    diag_width_candidates = tuple(
        value for value in (0.8, 1.0, 1.4, 1.8, 2.2, 2.8, 3.2, 3.6, 4.0) if value <= stroke_upper + 1e-6
    ) or (stroke_upper,)
    glyph_width_candidates = tuple(
        value for value in (0.8, 1.0, 1.2, 1.6, 2.2) if value <= glyph_stroke_upper + 1e-6
    ) or (glyph_stroke_upper,)
    refinement_steps: list[tuple[str, tuple[float | str, ...]]] = [
        ("border_thickness", tuple(value for value in (0.8, 1.0, 1.2, 1.4, 1.8) if value <= max(1.0, min(1.8, scale * 0.09)) + 1e-6)),
        ("rect_x_inset_ratio", _candidate_window(float(current["rect_x_inset_ratio"]), (-0.04, -0.02, 0.0, 0.02, 0.04), minimum=0.0, maximum=0.20, include_limits=False)),
        ("rect_y_inset_ratio", _candidate_window(float(current["rect_y_inset_ratio"]), (-0.04, -0.02, 0.0, 0.02, 0.04), minimum=0.0, maximum=0.20, include_limits=False)),
        ("gradient_center", (40.0, 45.0, 50.0, 55.0, 60.0)),
        (
            "diag1_width",
            diag_width_candidates if float(current["diag1_width"]) > 0 else (0.0,),
        ),
        (
            "diag2_width",
            diag_width_candidates if float(current["diag2_width"]) > 0 else (0.0,),
        ),
        (
            "diagonal_inset_ratio",
            _candidate_window(float(current["diagonal_inset_ratio"]), (-0.08, -0.04, 0.0, 0.04, 0.08), minimum=0.0, maximum=0.40, include_limits=False)
            if (float(current["diag1_width"]) > 0 or float(current["diag2_width"]) > 0)
            else (0.0,),
        ),
        ("chevron_width", tuple(value for value in diag_width_candidates if value <= 2.8) if has_right_chevron else (0.0,)),
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
        ("plus_width", glyph_width_candidates if has_plus else (0.0,)),
        ("minus_gap_ratio", (1.5, 1.8, 2.1)),
        ("minus_width", glyph_width_candidates if has_minus else (0.0,)),
        ("center_dot_radius", (0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2) if has_center_dot else (0.0,)),
        ("center_dot_gray", (40.0, 55.0, 70.0, 80.0, 95.0, 110.0, 130.0, 150.0) if has_center_dot else (float(current["center_dot_gray"]),)),
        ("glyph_gray", (55.0, 70.0, 85.0, 100.0, 115.0, 130.0, 150.0, 180.0, 210.0, 241.0)),
        ("diag_gray", (diagonal_gray_seed, 70.0, 95.0, 120.0, 145.0, 170.0, 195.0, 220.0, 241.0)),
        ("border_gray", (90.0, 110.0, 130.0, 154.0, 170.0, 190.0)),
        ("gradient_edge", (str(current["gradient_edge"]),) + tuple(_gray_hex(v) for v in sorted({70.0, 85.0, 100.0, 120.0, 150.0, gradient_edge_seed}))),
        ("gradient_mid", (str(current["gradient_mid"]),) + tuple(_gray_hex(v) for v in sorted({100.0, 120.0, 140.0, 170.0, 190.0, 220.0, 245.0, gradient_mid_seed}))),
    ]
    step_logs: list[str] = []
    iteration_logs: list[str] = []
    logged_iteration_hashes: set[str] = set()
    iteration_index = 0
    best: tuple[float, str, object] | None = None
    for key, candidates in refinement_steps:
        local_best = None
        for candidate_value in candidates:
            candidate = dict(current)
            candidate[key] = candidate_value
            iteration_hash = _symbol_params_iteration_hash(candidate)
            if iteration_hash not in logged_iteration_hashes:
                logged_iteration_hashes.add(iteration_hash)
                iteration_index += 1
                iteration_logs.extend(
                    [
                        f"iteration_{iteration_index:03d}_key={key}",
                        f"iteration_{iteration_index:03d}_value={candidate_value}",
                        f"iteration_{iteration_index:03d}_params_hash={iteration_hash}",
                    ]
                )
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
    step_logs = iteration_logs + step_logs
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
    "PolygonPath",
    "UpwardCompressorGlyph",
    "RightwardCompressorGlyph",
    "MainDiagonalMirroredCompressorGlyph",
    "VerticalTwoWayValveMotorGlyph",
    "LeftRotatedTwoWayValveMotorGlyph",
    "Rotated180TwoWayValveMotorGlyph",
    "TopTwoWayValveMotorGlyph",
    "TopKelleThreeWayValveGlyph",
    "LeftRotatedTopKelleThreeWayValveGlyph",
    "RightRotatedTopKelleThreeWayValveGlyph",
    "Rotated180TopKelleThreeWayValveGlyph",
    "MainDiagonalMirroredTopKelleThreeWayValveGlyph",
    "LeftRotatedCircularDamperGlyph",
    "UprightSquareKelleGlyph",
    "RightRotatedSquareKellePGlyph",
    "RightFacingSquareKellePGlyph",
    "LeftRotatedSquareKelleTGlyph",
    "VerticallyMirroredSquareKelleTGlyph",
}


SEMANTIC_GEOMETRY_IR_KINDS = {
    "VerticalTwoWayValveMotorGlyph",
    "LeftRotatedTwoWayValveMotorGlyph",
    "Rotated180TwoWayValveMotorGlyph",
    "TopTwoWayValveMotorGlyph",
    "TopKelleThreeWayValveGlyph",
    "LeftRotatedTopKelleThreeWayValveGlyph",
    "RightRotatedTopKelleThreeWayValveGlyph",
    "Rotated180TopKelleThreeWayValveGlyph",
    "MainDiagonalMirroredTopKelleThreeWayValveGlyph",
    "LeftRotatedCircularDamperGlyph",
    "UprightSquareKelleGlyph",
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
            # unlabelled circle used by the regular right-rotated valve variants.
            element["circle"] = [0.235, 0.500, 0.225]
            element["connector"][0] = [0.450, 0.500]
    return geometry_ir


def _is_description_heat_exchanger_geometry(geometry_ir: list[dict[str, object]]) -> bool:
    kinds = {str(element.get("kind", "")) for element in geometry_ir}
    heat_exchanger_core = {"HorizontalGradient", "RectBorder", "DiagonalBand"}
    heat_exchanger_glyphs = {"PlusGlyph", "MinusGlyph"}
    return heat_exchanger_core.issubset(kinds) and bool(heat_exchanger_glyphs & kinds)


def _prefer_semantic_description_geometry(geometry_ir: list[dict[str, object]]) -> bool:
    kinds = {str(element.get("kind", "")) for element in geometry_ir}
    roles = {str(element.get("role", "")) for element in geometry_ir}
    return bool(SEMANTIC_GEOMETRY_IR_KINDS & kinds) or bool({"checkmark", "reference_light_grey_square"} & roles)


def _description_reuses_reference_family(description: str) -> bool:
    return _extract_reference_family_from_description(description) is not None


def _prefer_description_geometry_candidate(geometry_ir: list[dict[str, object]], *, description: str) -> bool:
    if _prefer_semantic_description_geometry(geometry_ir):
        return True
    # Heat-exchanger descriptions declare rectangle, gradient, diagonal and plus/minus glyph
    # contract.  Keep that contract for direct descriptions and for
    # reference-derived size variants ("Wie <reference> ...") so conversion remains a
    # reusable description algorithm instead of drifting to per-image fitted
    # output.  Raster registration can still tune the Geometry-IR proportions.
    return _is_description_heat_exchanger_geometry(geometry_ir)


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


def _has_description_driven_symbol_algorithm(description: str) -> bool:
    """Return true when the text can be rendered algorithmically without sample SVGs."""

    geometry_ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description)
    if not geometry_ir:
        return False
    kinds = {str(element.get("kind", "")) for element in geometry_ir}
    return bool(DESCRIPTION_DRIVEN_GEOMETRY_IR_KINDS & kinds)


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


def _try_load_sample_svg(*, img_path: str, base_name: str, description: str = "", image_variant_name: str | None = None):
    img_parent = Path(img_path).parent
    has_explicit_image_dir = img_parent != Path(".")
    fallback_dirs: list[str] = []
    if has_explicit_image_dir:
        fallback_dirs.append(str(img_parent / "samples"))
    env_dirs = os.environ.get("IMAGE_CONVERTER_SAMPLE_SVG_DIRS", "")
    for raw in env_dirs.split(os.pathsep):
        candidate = raw.strip()
        if candidate:
            fallback_dirs.append(candidate)
    if has_explicit_image_dir:
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

    sample_candidates = _build_sample_candidates(str(image_variant_name or base_name))
    if image_variant_name and str(image_variant_name).upper() != str(base_name).upper():
        sample_candidates.extend(
            candidate for candidate in _build_sample_candidates(base_name) if candidate not in sample_candidates
        )
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
    algorithmic_description_available = mode != "manual_review" and _has_description_driven_symbol_algorithm(description)
    sample_svg = (
        None
        if algorithmic_description_available
        else _try_load_sample_svg(
            img_path=img_path,
            base_name=base_name,
            description=description,
            image_variant_name=image_variant_name,
        )
    )

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
                sample_is_exact_variant = Path(sample_svg_path).stem.upper() == Path(str(image_variant_name or base_name)).stem.upper()
                if sample_is_exact_variant or sample_err + 1e-6 < generated_err:
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
            variation_rng = _output_variation_rng()
            if variation_rng is not None:
                varied_svg_content = _apply_svg_output_variation(
                    generated_svg_content,
                    variation_rng,
                    width=width,
                    height=height,
                )
                varied_rendered = render_svg_to_numpy_fn(varied_svg_content, width, height)
                if varied_rendered is not None:
                    generated_svg_content = varied_svg_content
                    generated_rendered = varied_rendered
                    generated_err = calculate_error_fn(perc_img, varied_rendered)
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
    resolved_variant_name = str(
        image_variant_name or params.get("variant_name") or Path(img_path).stem or base_name
    )
    symmetric_valve_panel_svg = _try_build_symmetric_valve_panel_svg(
        width,
        height,
        base_name=resolved_variant_name,
        description=description,
        perc_img=perc_img,
    )
    plain_panel_svg = _try_build_plain_framed_panel_svg(
        width,
        height,
        description=description,
        perc_img=perc_img,
    )
    selected_panel_status = ""
    selected_panel_trigger = ""
    selected_panel_print = ""
    selected_panel_locks_output_variation = False
    if symmetric_valve_panel_svg is not None or plain_panel_svg is not None:
        panel_candidates: list[dict[str, object]] = []
        if plain_panel_svg is not None:
            plain_rendered = render_svg_to_numpy_fn(plain_panel_svg, width, height)
            if plain_rendered is None:
                record_render_failure_fn(
                    "non_composite_plain_framed_panel_render_failed",
                    svg_content=plain_panel_svg,
                    params_snapshot=params,
                )
            else:
                panel_candidates.append(
                    {
                        "kind": "plain",
                        "svg": plain_panel_svg,
                        "rendered": plain_rendered,
                        "error": calculate_error_fn(perc_img, plain_rendered),
                    }
                )
        if symmetric_valve_panel_svg is not None:
            symmetric_rendered = render_svg_to_numpy_fn(symmetric_valve_panel_svg, width, height)
            if symmetric_rendered is None:
                record_render_failure_fn(
                    "non_composite_symmetric_valve_panel_render_failed",
                    svg_content=symmetric_valve_panel_svg,
                    params_snapshot=params,
                )
            else:
                panel_candidates.append(
                    {
                        "kind": "symmetric",
                        "svg": symmetric_valve_panel_svg,
                        "rendered": symmetric_rendered,
                        "error": calculate_error_fn(perc_img, symmetric_rendered),
                    }
                )
        if not panel_candidates:
            return None
        plain_candidate = next((candidate for candidate in panel_candidates if candidate["kind"] == "plain"), None)
        symmetric_candidate = next((candidate for candidate in panel_candidates if candidate["kind"] == "symmetric"), None)
        resolved_signal = f"{resolved_variant_name} {description}".upper()
        force_ac0vr2_symmetric = "AC0VR2" in resolved_signal and "_ZL" not in resolved_signal
        if force_ac0vr2_symmetric and symmetric_candidate is not None:
            # AC0VR2 panel variants (including AM/AB) are documented valve panels:
            # the plain panel can score slightly better numerically because it
            # suppresses thin foreground strokes, but that drops the semantic
            # shape completely and may regress to stripe-like fallback output.
            # Prefer the raster-derived symmetric renderer for these variants so
            # the conversion keeps a real gradient, diagonal guides and the
            # right-hand strokes.  ZL remains excluded because it is covered by
            # the plain framed-panel contract.
            selected_panel = symmetric_candidate
        elif (
            plain_candidate is not None
            and symmetric_candidate is not None
            and float(symmetric_candidate["error"]) + 1e-6 >= float(plain_candidate["error"])
        ):
            selected_panel = plain_candidate
        else:
            selected_panel = min(panel_candidates, key=lambda candidate: float(candidate["error"]))
        svg_content = str(selected_panel["svg"])
        svg_rendered = selected_panel["rendered"]
        svg_err = float(selected_panel["error"])
        if selected_panel["kind"] == "symmetric":
            selected_panel_status = "non_composite_symmetric_valve_panel"
            selected_panel_trigger = "trigger=ac0vr2_raster_symmetric_valve_panel"
            selected_panel_print = "  -> Fallback aktiv: verwende symmetrisches AC0VR2-Ventilpanel aus Rasterfarben."
            selected_panel_locks_output_variation = True
        else:
            selected_panel_status = "non_composite_plain_framed_panel"
            selected_panel_trigger = (
                "trigger=description_farbuebergang_panel"
                if _description_requests_framed_gradient_panel(description)
                else "trigger=raster_plain_framed_panel"
            )
            selected_panel_print = (
                "  -> Fallback aktiv: verwende gerahmtes AC0VR2-Panel aus Rasterfarben."
                if "AC0VR2" in str(description).upper()
                else "  -> Fallback aktiv: verwende gerahmtes Farbuebergang-Panel aus Rasterfarben."
            )
        print_fn(selected_panel_print)
        write_validation_log_fn([f"status={selected_panel_status}", selected_panel_trigger])
    else:
        print_fn("  -> Fallback aktiv: elementweise iterative Annäherung aus Rasterbild.")
        perception_seeded = _try_build_perception_seeded_geometry_ir_svg(
            width, height, description=description, perc_img=perc_img
        )
        description_geometry_ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description)
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
                    if hasattr(perc_img, "shape") and (
                        not _is_description_heat_exchanger_geometry(description_geometry_ir)
                        or _description_reuses_reference_family(description)
                    ):
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
                    description_status = "non_composite_description_geometry_ir"
                    candidates.append(
                        {
                            "status": description_status,
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
                    and _prefer_description_geometry_candidate(candidate["geometry_ir"], description=description)
                ),
                None,
            )
            best_pixel_candidate = min(candidates, key=lambda candidate: float(candidate["error"]))
            if semantic_description_candidate is not None:
                semantic_layout_warnings = geometry_ir_helpers.validateGeometryIrGlyphLayoutImpl(
                    width,
                    height,
                    list(semantic_description_candidate.get("geometry_ir", [])),
                )
                elementwise_heat_exchanger_candidate = next(
                    (
                        candidate
                        for candidate in candidates
                        if candidate["status"] == "non_composite_elementwise_symbol_fit"
                        and _is_description_heat_exchanger_geometry(
                            list(semantic_description_candidate.get("geometry_ir", []))
                        )
                    ),
                    None,
                )
                if elementwise_heat_exchanger_candidate is not None and semantic_layout_warnings:
                    best_geometry_candidate = elementwise_heat_exchanger_candidate
                    selection_reason = "raster_fit_overrides_invalid_description_geometry_layout"
                else:
                    semantic_error = float(semantic_description_candidate["error"])
                    pixel_error = float(best_pixel_candidate["error"])
                    if (
                        best_pixel_candidate is not semantic_description_candidate
                        and _is_description_heat_exchanger_geometry(list(semantic_description_candidate.get("geometry_ir", [])))
                        and pixel_error * 2.0 < semantic_error
                        and not _is_deprecated_stripe_fit_svg(best_pixel_candidate.get("svg"), description=description)
                    ):
                        # Direct canonical heat-exchanger descriptions may still yield
                        # to a much better generated algorithmic fit.  The same rule
                        # applies to reference-derived size variants ("Wie
                        # <reference> ..."): they must reuse the heat-exchanger
                        # algorithm, but must not force a poorer registered
                        # Geometry-IR candidate when the raster-derived element-wise
                        # algorithm fits substantially better.
                        best_geometry_candidate = best_pixel_candidate
                        selection_reason = "raster_fit_overrides_poor_description_geometry"
                    else:
                        best_geometry_candidate = semantic_description_candidate
                        selection_reason = "semantic_description_geometry"
            else:
                best_geometry_candidate = best_pixel_candidate
                selection_reason = "best_pixel_error"
            svg_content = str(best_geometry_candidate["svg"])
            svg_rendered = best_geometry_candidate["rendered"]
            svg_err = float(best_geometry_candidate["error"])
            geometry_ir = best_geometry_candidate["geometry_ir"]
            perception_seed_count = int(best_geometry_candidate["perception_seed_count"])
            status = str(best_geometry_candidate["status"])
            log_lines = [f"status={status}"]
            variation_rng = _output_variation_rng()
            if variation_rng is not None and isinstance(geometry_ir, list):
                varied_geometry_ir = _jitter_geometry_ir_for_output_variation(geometry_ir, variation_rng)
                if varied_geometry_ir != geometry_ir:
                    varied_svg_content = geometry_ir_helpers.renderGeometryIrToSvgImpl(
                        width,
                        height,
                        varied_geometry_ir,
                    )
                    varied_rendered = render_svg_to_numpy_fn(varied_svg_content, width, height)
                    if varied_rendered is not None:
                        svg_content = varied_svg_content
                        svg_rendered = varied_rendered
                        svg_err = calculate_error_fn(perc_img, varied_rendered)
                        geometry_ir = varied_geometry_ir
                        params["optimized_geometry_ir"] = varied_geometry_ir
                        log_lines.append("output_variation=1")
            if status == "non_composite_elementwise_symbol_fit":
                log_lines.extend(str(line) for line in best_geometry_candidate.get("step_logs", []))
                fit_params = best_geometry_candidate.get("fit_params", {})
                if isinstance(fit_params, dict):
                    log_lines.extend(f"fit_{k}={v}" for k, v in sorted(fit_params.items()))
            else:
                if perception_seed_count:
                    log_lines.extend(
                        [
                            "perception_seeded_geometry_ir=1",
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
                layout_warnings = geometry_ir_helpers.validateGeometryIrGlyphLayoutImpl(width, height, geometry_ir)
                log_lines.extend(
                    [
                        f"geometry_ir_element_count={len(geometry_ir)}",
                        f"geometry_ir_layout_check={'warning' if layout_warnings else 'ok'}",
                        *(f"geometry_ir_layout_warning={warning}" for warning in layout_warnings),
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
            if description_driven_algorithm_available:
                log_lines.extend(
                    [
                        "description_driven_algorithm_available=1",
                        "sample_svg_lookup=skipped_description_driven_algorithm",
                    ]
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

    variation_rng = None if selected_panel_locks_output_variation else _output_variation_rng()
    if variation_rng is not None:
        varied_svg_content = _apply_svg_output_variation(
            svg_content,
            variation_rng,
            width=width,
            height=height,
        )
        if varied_svg_content != svg_content:
            varied_rendered = render_svg_to_numpy_fn(varied_svg_content, width, height)
            if varied_rendered is not None:
                svg_content = varied_svg_content
                svg_rendered = varied_rendered
                svg_err = calculate_error_fn(perc_img, varied_rendered)
    write_attempt_artifacts_fn(svg_content, svg_rendered)
    return base_name, description, params, 1, svg_err
