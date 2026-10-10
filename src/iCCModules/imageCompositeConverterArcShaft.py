"""Infer an open lower elliptical arc and a detached gradient shaft from pixels."""
from __future__ import annotations

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register


def fit_arc_shaft(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(token in text for token in ('u-bogen', 'oben offen', 'schaft', 'horizontal', 'verlauf')):
        return None
    if any(token in text for token in ('kreis geschlossen', 'dreieck', 'beschrift', 'zusätzlich', 'zwei bögen')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 8 or not np.isfinite(arr).all():
        return None
    pixels = arr.astype(float)
    mask = np.min(arr, axis=2) < 225
    occupied = np.flatnonzero(mask.any(axis=1))
    runs = np.split(occupied, np.flatnonzero(np.diff(occupied) > 1)+1)
    if len(runs) != 2 or any(len(run) < 3 for run in runs):
        return None
    head, shaft = runs
    top, base, start, bottom = head[0], head[-1]+1, shaft[0], shaft[-1]+1
    rows = mask[top:base]
    ys, xs = np.nonzero(rows)
    left, right = xs.min(), xs.max()+1
    cx = (left+right)/2
    # Open upper rows must have two arms separated by white pixels. The
    # lower arc must join them, rather than two bars or an extra object.
    upper = rows[:max(1, len(rows)//3)]
    if not (upper[:, :int(cx)].any() and upper[:, int(cx):].any()):
        return None
    if upper[:, max(0, int(cx)-1):int(cx)+1].any():
        return None
    count, _, stats, _ = cv2.connectedComponentsWithStats(rows.astype(np.uint8))
    if count != 2:
        return None
    lengths = [np.count_nonzero(row[:int(cx)]) for row in upper]
    stroke = float(np.median(lengths))
    rx = (right-left-stroke)/2
    cy = float(top)+.5
    ry = float(base)-cy-stroke/2
    if min(rx, ry, stroke) <= 0 or stroke >= min(rx, ry):
        return None
    columns = np.flatnonzero(mask[start:bottom].mean(axis=0) > .8)
    if len(columns) < 3:
        return None
    sx, ex = int(columns[0]), int(columns[-1])+1
    if not (left < sx < ex < right and abs((sx+ex)/2-cx) < (right-left)*.12):
        return None
    if mask[start:bottom, :sx].sum()+mask[start:bottom, ex:].sum() > max(2, (bottom-start)*.1):
        return None
    profile = np.median(pixels[start:bottom, sx:ex], axis=0)
    if np.percentile(np.max(np.abs(pixels[start:bottom, sx:ex]-profile), axis=2), 95) > 30:
        return None
    middle = len(profile)//2
    side_brightness = max(profile[:middle].mean(axis=1).min(), profile[middle+1:].mean(axis=1).min())
    if profile[middle].mean() < side_brightness+8:
        return None
    core = cv2.erode(rows.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0
    color = np.median(pixels[top:base][core if core.any() else rows], axis=0)
    indices = np.unique(np.rint(np.linspace(0, ex-sx-1, min(9, ex-sx))).astype(int))
    stops = [(float((i+.5)/(ex-sx)), profile[i]) for i in indices]

    def build(p):
        cx, cy, rx, ry, sw, x, y, w, h = p[:9]
        gradient = ''.join(f'<stop offset="{t:g}" stop-color="{_hex(c+p[12:15])}"/>' for t, c in stops)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="shaft_color" x1="0" y1="0" x2="1" y2="0">{gradient}</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<path d="M {cx-rx:g} {cy:g} A {rx:g} {ry:g} 0 0 0 {cx+rx:g} {cy:g}" '
                f'fill="none" stroke="{_hex(p[9:12])}" stroke-width="{sw:g}"/>'
                f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="url(#shaft_color)"/></svg>\n')

    def valid(p):
        cx, cy, rx, ry, sw, x, y, w, h = p[:9]
        return (np.isfinite(p).all() and min(rx, ry, sw, w, h) > 0
                and sw < min(rx, ry) and 0 <= cx-rx-sw/2 < cx+rx+sw/2 <= width
                and -.5 <= cy < cy+ry+sw/2 < y < y+h <= height
                and cx-rx < x < x+w < cx+rx and abs(x+w/2-cx) < rx*.24)

    parameters = [cx, cy, rx, ry, stroke, float(sx), float(start), float(ex-sx), float(bottom-start), *color, 0., 0., 0.]
    result = _register(parameters, 9, build, valid, arr, render_fn, error_fn, 'raster_arc_shaft_v1')
    if result is None:
        return None
    # The fitted analytic arc must explain its input; refinement may not erase
    # a square U, extra marks, or another topology into an approximate circle.
    fitted_mask = np.min(result['rendered'][:start], axis=2) < 225
    union = (fitted_mask | mask[:start]).sum()
    if union == 0 or (fitted_mask & mask[:start]).sum()/union < .7:
        return None
    return result
