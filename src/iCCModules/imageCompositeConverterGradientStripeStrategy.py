"""Gradient stripe conversion strategy helpers."""

from __future__ import annotations

from typing import Any


def _to_hex(rgb_triplet) -> str:
    r, g, b = [int(max(0, min(255, round(float(v))))) for v in rgb_triplet]
    return f"#{r:02x}{g:02x}{b:02x}"


def detectGradientStripeStrategyImpl(
    img,
    *,
    np_module,
    white_threshold: int = 245,
    min_relative_width: float = 0.30,
    max_relative_height: float = 0.45,
    max_stops: int = 6,
    min_canvas_height: int = 8,
) -> dict[str, Any] | None:
    """Detect a mostly flat stripe and derive gradient stop colors + offsets."""
    if img is None:
        return None
    h, w = img.shape[:2]
    if h <= 0 or w <= 0:
        return None
    # Very short rasters (e.g. 6px height) tend to collapse into a few
    # quantized gradient stops and look like caricatures. For these tiny
    # canvases we keep the higher-fidelity embedded-raster fallback instead of
    # forcing a synthetic gradient stripe.
    if h < int(min_canvas_height):
        return None

    # BGR image: detect non-background region.
    mask = (img < int(white_threshold)).any(axis=2)
    ys, xs = np_module.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        return None

    x0 = int(xs.min())
    x1 = int(xs.max())
    y0 = int(ys.min())
    y1 = int(ys.max())
    bw = x1 - x0 + 1
    bh = y1 - y0 + 1
    if bw < max(3, int(w * float(min_relative_width))):
        return None
    if h > 24 and bh > max(2, int(h * float(max_relative_height))):
        return None
    if (float(bw) / float(max(1, bh))) < 4.0:
        return None

    crop = img[y0 : y1 + 1, x0 : x1 + 1]
    col_rgb = crop.mean(axis=0)[:, ::-1]  # average over y, convert BGR -> RGB
    row_rgb = crop.mean(axis=1)[:, ::-1]  # average over x, convert BGR -> RGB
    axis_x_var = float(np_module.mean(np_module.linalg.norm(col_rgb - col_rgb.mean(axis=0), axis=1)))
    axis_y_var = float(np_module.mean(np_module.linalg.norm(row_rgb - row_rgb.mean(axis=0), axis=1)))
    vertical = axis_y_var > axis_x_var
    samples = row_rgb if vertical else col_rgb

    min_step = max(1, len(samples) // 12)
    delta_threshold = 7.5
    stop_indexes = [0]
    anchor = samples[0]
    for idx in range(1, len(samples)):
        dist = float(np_module.linalg.norm(samples[idx] - anchor))
        if dist >= delta_threshold and idx - stop_indexes[-1] >= min_step:
            stop_indexes.append(idx)
            anchor = samples[idx]
    if stop_indexes[-1] != len(samples) - 1:
        stop_indexes.append(len(samples) - 1)

    if len(stop_indexes) > max_stops:
        step = (len(stop_indexes) - 1) / float(max(1, max_stops - 1))
        reduced = [stop_indexes[int(round(i * step))] for i in range(max_stops)]
        stop_indexes = sorted(set(reduced))
        if stop_indexes[0] != 0:
            stop_indexes = [0] + stop_indexes
        if stop_indexes[-1] != len(samples) - 1:
            stop_indexes.append(len(samples) - 1)
    if len(stop_indexes) < 2:
        stop_indexes = [0, len(samples) - 1]

    denom = float(max(1, len(samples) - 1))
    stops = [
        {
            "offset": float(idx / denom),
            "color": _to_hex(samples[idx]),
        }
        for idx in stop_indexes
    ]
    return {
        "bbox": {"x": float(x0), "y": float(y0), "width": float(bw), "height": float(bh)},
        "stops": stops,
        "vertical": bool(vertical),
    }


def buildGradientStripeSvgImpl(width: int, height: int, strategy: dict[str, Any]) -> str:
    bbox = strategy["bbox"]
    stops = strategy["stops"]
    vertical = bool(strategy.get("vertical", False))
    x2 = "0%" if vertical else "100%"
    y2 = "100%" if vertical else "0%"
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        (
            f'<svg width="{float(width):.6f}px" height="{float(height):.6f}px" '
            f'viewBox="0 0 {float(width):.6f} {float(height):.6f}" '
            'xmlns="http://www.w3.org/2000/svg">'
        ),
        "  <defs>",
        f'    <linearGradient id="detectedStripeGradient" x1="0%" y1="0%" x2="{x2}" y2="{y2}">',
    ]
    for stop in stops:
        lines.append(
            f'      <stop offset="{float(stop["offset"]) * 100.0:.3f}%" stop-color="{str(stop["color"])}"/>'
        )
    lines.extend(
        [
            "    </linearGradient>",
            "  </defs>",
            (
                f'  <rect x="{float(bbox["x"]):.4f}" y="{float(bbox["y"]):.4f}" '
                f'width="{float(bbox["width"]):.4f}" height="{float(bbox["height"]):.4f}" '
                'fill="url(#detectedStripeGradient)"/>'
            ),
            "</svg>",
        ]
    )
    return "\n".join(lines)
