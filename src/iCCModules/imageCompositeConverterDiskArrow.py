"""Fit a left arrow inside a gradient disk from description and raster evidence."""
from __future__ import annotations

import cv2
import numpy as np
import re

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def fit_disk_arrow(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    text = re.sub(r'\bnach (?:links|rechts|oben|unten)(?: und (?:links|rechts|oben|unten))?\s+'
                  r'(?:verschoben|versetzt)\b', 'verschoben', text)
    if not all(word in text for word in ('kreis', 'verlauf', 'waagerecht', 'pfeil',
                                         'nach links', 'schaft', 'dreieck', 'ohne lücke')):
        return None
    if any(word in text for word in ('nach rechts', 'nach oben', 'nach unten', 'zwei',
                                     'zusätzlich', 'ohne pfeil', 'beschriftung')):
        return None
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    mask = (np.min(pixels, axis=2) < 235).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if count < 2:
        return None
    index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = stats[index]
    if not (.85 < w/h < 1.18 and area > .65*w*h):
        return None
    if sum(stats[i, cv2.CC_STAT_AREA] for i in range(1, count) if i != index) > max(3, area*.005):
        return None
    disk_mask = (labels == index).astype(np.uint8)
    contour = cv2.findContours(disk_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0][0][:, 0].astype(float) + .5
    coefficients = np.linalg.lstsq(np.c_[2*contour, np.ones(len(contour))],
                                   np.sum(contour**2, axis=1), rcond=None)[0]
    cx, cy = coefficients[:2]
    radius = float(np.sqrt(max(0., coefficients[2]+cx*cx+cy*cy)))
    if radius < 5 or np.mean(np.abs(np.linalg.norm(contour-[cx, cy], axis=1)-radius)) > max(.7, radius*.04):
        return None
    yy, xx = np.indices((height, width), dtype=float)
    distance = np.hypot(xx+.5-cx, yy+.5-cy)
    t = (xx+.5-(cx-radius))/(2*radius)
    exposed = (distance < radius*.88) & (np.abs(yy+.5-cy) > radius*.64)
    if exposed.sum() < 12:
        return None
    colors = np.linalg.lstsq(np.c_[1-t[exposed], t[exposed]], pixels[exposed], rcond=None)[0]
    if colors[0].mean() <= colors[1].mean()+5:
        return None
    field = (1-t[..., None])*colors[0]+t[..., None]*colors[1]
    arrow_mask = ((np.mean(field-pixels, axis=2) > 35) & (distance < radius*.9)).astype(np.uint8)
    contrast_mask = arrow_mask.copy()
    # Pale antialiased outlines can isolate a one-pixel strip of the shaft.
    # Larger disconnected marks and gaps still fail the evidence checks.
    arrow_mask = cv2.morphologyEx(arrow_mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    count, arrow_labels, arrow_stats, _ = cv2.connectedComponentsWithStats(arrow_mask)
    if count < 2:
        return None
    index = 1 + int(np.argmax(arrow_stats[1:, cv2.CC_STAT_AREA]))
    bx, by, bw, bh, arrow_area = arrow_stats[index]
    if sum(arrow_stats[i, cv2.CC_STAT_AREA] for i in range(1, count) if i != index) > max(2, arrow_area*.01):
        return None
    arrow_mask = (arrow_labels == index).astype(np.uint8)
    columns = np.arange(bx, bx+bw)
    top = np.array([np.flatnonzero(arrow_mask[:, col])[0] for col in columns], dtype=float)
    bottom = np.array([np.flatnonzero(arrow_mask[:, col])[-1]+1 for col in columns], dtype=float)
    shoulder = int(np.argmax(bottom-top))
    if shoulder < 4 or bw-shoulder < 4:
        return None
    # Two sloped head edges meet at the left tip; the shaft has parallel edges.
    fit_indices = np.arange(1, shoulder)
    upper, lower = (np.polyfit(columns[fit_indices]+.5, edge[fit_indices], 1) for edge in (top, bottom))
    if not (upper[0] < -.2 and lower[0] > .2):
        return None
    if max(np.mean(np.abs(np.polyval(upper, columns[fit_indices]+.5)-top[fit_indices])),
           np.mean(np.abs(np.polyval(lower, columns[fit_indices]+.5)-bottom[fit_indices]))) > .8:
        return None
    tail_indices = np.arange(shoulder+2, bw-1)
    if len(tail_indices) < 2:
        return None
    shaft_top, shaft_bottom = (float(np.median(edge[tail_indices])) for edge in (top, bottom))
    if max(np.max(np.abs(top[tail_indices]-shaft_top)), np.max(np.abs(bottom[tail_indices]-shaft_bottom))) > 1:
        return None
    tip = (lower[1]-upper[1])/(upper[0]-lower[0])
    sy = (shaft_top+shaft_bottom)/2
    sx = float(columns[shoulder]+.5)
    head_half = (np.polyval(lower, sx)-np.polyval(upper, sx))/2
    shaft_half = (shaft_bottom-shaft_top)/2
    if not (head_half > shaft_half > 1 and abs(sy-cy) < radius*.18):
        return None
    core = cv2.erode(contrast_mask & arrow_mask, np.ones((3, 3), np.uint8)).astype(bool)
    if not core.any():
        return None
    fill = np.median(pixels[core], axis=0)
    if np.percentile(np.max(np.abs(pixels[core]-fill), axis=1), 95) > 25:
        return None
    outside = (distance < radius*.88) & ~cv2.dilate(arrow_mask, np.ones((5, 5), np.uint8)).astype(bool)
    if not outside.any() or np.percentile(np.max(np.abs(pixels[outside]-field[outside]), axis=1), 95) > 25:
        return None
    rim = np.median(pixels[(distance > radius*.94) & (distance < radius*1.01)], axis=0)
    edge = pixels[(cv2.dilate(arrow_mask, np.ones((3, 3), np.uint8))-arrow_mask).astype(bool)]
    outline = np.median(edge[edge.mean(axis=1) >= np.percentile(edge.mean(axis=1), 70)], axis=0)
    p = np.r_[cx, cy, radius-.3, 1., tip, sx, float(bx+bw), sy, head_half, shaft_half, .8,
              colors.ravel(), rim, fill, outline]

    def points(p):
        _, _, _, _, tip, shoulder, tail, center, head, shaft, _ = p[:11]
        return [(tip, center), (shoulder, center-head), (shoulder, center-shaft),
                (tail, center-shaft), (tail, center+shaft),
                (shoulder, center+shaft), (shoulder, center+head)]

    def build(p):
        cx, cy, r, sw = p[:4]
        light, dark, rim, fill, outline = p[11:].reshape(-1, 3)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                '<defs><linearGradient id="disk_color" x1="0" y1="0" x2="1" y2="0">'
                f'<stop offset="0" stop-color="{_hex(light)}"/><stop offset="1" stop-color="{_hex(dark)}"/>'
                '</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="url(#disk_color)" stroke="{_hex(rim)}" stroke-width="{sw:.4f}"/>'
                '<polygon points="'+' '.join(f'{x:.4f},{y:.4f}' for x, y in points(p))+
                f'" fill="{_hex(fill)}" stroke="{_hex(outline)}" stroke-width="{p[10]:.4f}"/></svg>\n')

    def valid(p):
        cx, cy, r, sw, tip, shoulder, tail, center, head, shaft, outline = p[:11]
        return (r > 4 and .1 <= sw <= 3 and .1 <= outline <= 2.5
                and tip < shoulder < tail and head > shaft > 1
                and 0 <= cx-r-sw/2 and cx+r+sw/2 <= width
                and 0 <= cy-r-sw/2 and cy+r+sw/2 <= height
                and abs(center-cy) < r*.18
                and all((x-cx)**2+(y-cy)**2 < (r-sw/2-outline/2)**2 for x, y in points(p)))

    return _register(p, 11, build, valid, image, render_fn, error_fn, 'raster_disk_arrow_v1')
