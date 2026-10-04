"""Detect and register two flat nested rectangles from raster evidence."""
from __future__ import annotations

import cv2
import numpy as np


def fit_nested_panel(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not any(word in text for word in ('quadrat', 'rechteck', 'panel', 'fläche', 'flaeche')):
        return None
    # A panel fit must not erase explicitly described foreground objects.
    if any(word in text for word in ('kreis', 'kelle', 'text', 'beschrift', 'linie', 'streifen', 'diagonal', 'kreuz', 'plus', 'minus', 'pfeil', 'verlauf')):
        return None
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape != (height, width, 3) or min(width, height) < 7:
        return None
    pixels = arr.astype(np.float32)
    bins, counts = np.unique(arr.reshape(-1, 3) // 16, axis=0, return_counts=True)
    regions = []
    for mode in bins[np.argsort(counts)[-3:]]:
        seed_color = np.median(pixels[np.all(arr // 16 == mode, axis=2)], axis=0)
        mask = (np.max(np.abs(pixels - seed_color), axis=2) < 16).astype(np.uint8)
        opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        count, labels, stats, _ = cv2.connectedComponentsWithStats(opened)
        for label in range(1, count):
            x, y, w, h, area = map(int, stats[label])
            if x > 0 and y > 0 and x+w < width and y+h < height:
                regions.append((area, x, y, w, h, pixels[labels == label]))
    if not regions:
        return None
    area, x, y, w, h, region_pixels = max(regions, key=lambda row: row[0])
    if area < width*height*.2 or area/(w*h) < .97:
        return None
    inside = np.zeros((height, width), dtype=bool)
    inside[y:y+h, x:x+w] = True
    interior_color = np.median(region_pixels, axis=0)
    # Exclude the transition band (JPEG ringing/antialiasing) when sampling
    # the exterior; otherwise a bright edge is mistaken for another object.
    exterior_core = ~cv2.dilate(inside.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    if exterior_core.sum() < width*height*.03:
        exterior_core = ~inside
    exterior_color = np.median(pixels[exterior_core], axis=0)
    if np.max(np.abs(interior_color - exterior_color)) < 20:
        return None
    # Flatness and rectangular occupancy are evidence requirements, not a
    # shortcut based on a catalog name. Text/holes invalidate this hypothesis.
    inner_deviation = np.max(np.abs(pixels[y+1:y+h-1, x+1:x+w-1] - interior_color), axis=2)
    outer_deviation = np.max(np.abs(pixels[exterior_core] - exterior_color), axis=1)
    if np.percentile(inner_deviation, 99) > 20 or np.percentile(outer_deviation, 80) > 25:
        return None

    def color(value):
        return '#' + ''.join(f'{int(round(v)):02x}' for v in value[::-1])

    def svg(p):
        px, py, pw, ph, radius, outer_radius = p
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
            f'  <rect id="panel_exterior" width="{width}" height="{height}" rx="{outer_radius:g}" fill="{color(exterior_color)}"/>\n'
            f'  <rect id="panel_interior" x="{px:g}" y="{py:g}" width="{pw:g}" height="{ph:g}" rx="{radius:g}" fill="{color(interior_color)}"/>\n'
            '</svg>\n'
        )

    parameters = [float(x), float(y), float(w), float(h), 0., 0.]

    def measure(p):
        content = svg(p)
        rendered = render_fn(content, width, height)
        return None if rendered is None else (float(error_fn(image, rendered)), content, rendered)

    best = measure(parameters)
    if best is None:
        return None
    initial_error = best[0]
    # Register boundaries only after the two-object topology is established.
    for step in (1., .5):
        for index in range(6):
            for direction in (-2., -1., 1., 2.):
                candidate = parameters.copy()
                candidate[index] += direction * step
                px, py, pw, ph, radius, outer_radius = candidate
                if min(px, py, pw, ph) <= 0 or px+pw >= width or py+ph >= height:
                    continue
                if not (0 <= radius <= min(pw, ph)/4 and 0 <= outer_radius <= min(width, height)/4):
                    continue
                measured = measure(candidate)
                if measured is not None and measured[0] < best[0] - 1e-9:
                    parameters, best = candidate, measured
    return {'svg': best[1], 'rendered': best[2], 'error': best[0],
            'initial_error': initial_error, 'parameters': parameters,
            'kind': 'nested', 'source': 'raster_nested_rectangles_v1'}
