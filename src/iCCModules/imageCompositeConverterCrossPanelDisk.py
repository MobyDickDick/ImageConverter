"""Register an enclosed rectilinear cross, rectangular panel and gradient disk."""
from __future__ import annotations

from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description, gradient_direction

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def fit_cross_panel_disk(width, height, *, description, image, render_fn, error_fn):
    text = normalize_description(description, orientations=True).casefold()
    if not gradient_direction(text, 'senkrecht'):
        return None
    if not all(word in text for word in ('kreis', 'verlauf', 'senkrecht', 'rechteck',
                                         'kreuz', 'gefüllt', 'balken', 'innerhalb')):
        return None
    if re.search(r'\b(?:ohne|kein|keine|nicht|zwei|zusätzlich|dreieck|diagonal|schriftzeichen)\b',
                 text.replace('keine schriftzeichen', '')):
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
    contour = cv2.findContours((labels == index).astype(np.uint8), cv2.RETR_EXTERNAL,
                              cv2.CHAIN_APPROX_NONE)[0][0][:, 0].astype(float)+.5
    coefficients = np.linalg.lstsq(np.c_[2*contour, np.ones(len(contour))],
                                   np.sum(contour**2, axis=1), rcond=None)[0]
    cx, cy = coefficients[:2]
    radius = float(np.sqrt(max(0., coefficients[2]+cx*cx+cy*cy)))
    if radius < 7 or np.mean(np.abs(np.linalg.norm(contour-[cx, cy], axis=1)-radius)) > max(.7, radius*.04):
        return None
    yy, xx = np.indices((height, width), dtype=float)
    distance = np.hypot(xx+.5-cx, yy+.5-cy)
    t = (yy+.5-(cy-radius))/(2*radius)
    exposed = (distance < radius*.85) & (np.abs(yy+.5-cy) > radius*.62)
    if exposed.sum() < 12:
        return None
    colors = np.linalg.lstsq(np.c_[1-t[exposed], t[exposed]], pixels[exposed], rcond=None)[0]
    if np.max(np.abs(colors[0]-colors[1])) < 8:
        return None
    field = (1-t[..., None])*colors[0]+t[..., None]*colors[1]
    contrast = (np.max(np.abs(pixels-field), axis=2) > 40) & (distance < radius*.92)
    count, panel_labels, panel_stats, _ = cv2.connectedComponentsWithStats(contrast.astype(np.uint8))
    if count < 2:
        return None
    index = 1+int(np.argmax(panel_stats[1:, cv2.CC_STAT_AREA]))
    bx, by, bw, bh, panel_area = panel_stats[index]
    if not (bw > bh >= 8 and panel_area > .88*bw*bh):
        return None
    panel = panel_labels == index
    if sum(panel_stats[i, cv2.CC_STAT_AREA] for i in range(1, count) if i != index) > max(3, panel_area*.01):
        return None
    # A blended cross edge can match the disk color and leave tiny interior
    # holes in the contrast mask. Use only the observed outer silhouette for
    # the sampling region; the output still uses an analytic rectangle.
    boundary = cv2.findContours(panel.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    silhouette = np.zeros_like(mask)
    cv2.drawContours(silhouette, boundary, -1, 1, cv2.FILLED)
    panel = silhouette.astype(bool)
    # JPEG ringing around the colored panel is brighter than its solid fill.
    # Keep the cross detector away from that boundary.
    inset = max(1, min(2, round(min(bw, bh)*.055)))
    core = cv2.erode(panel.astype(np.uint8), np.ones((2*inset+1, 2*inset+1), np.uint8)).astype(bool)
    fill = np.median(pixels[core], axis=0)
    mark = core & (np.mean(pixels-fill, axis=2) > 55)
    count, mark_labels, mark_stats, _ = cv2.connectedComponentsWithStats(mark.astype(np.uint8))
    if count != 2:
        return None
    mx, my, mw, mh, mark_area = mark_stats[1]
    if min(mw, mh) < 5:
        return None
    mark = mark_labels == 1
    rows = mark[my:my+mh, mx:mx+mw].sum(axis=1)
    cols = mark[my:my+mh, mx:mx+mw].sum(axis=0)
    # Subpixel antialiasing can shorten an arm by one pixel on each side.
    # Distinguish the broad middle runs from the narrow free arms.
    full_rows, full_cols = np.flatnonzero(rows >= mw*.75), np.flatnonzero(cols >= mh*.75)
    if not len(full_rows) or not len(full_cols):
        return None
    if (full_rows[0] < 1 or full_rows[-1] >= mh-1 or full_cols[0] < 1 or full_cols[-1] >= mw-1
            or np.any(np.diff(full_rows) != 1) or np.any(np.diff(full_cols) != 1)):
        return None
    kx, ky = mx+mw/2, my+mh/2
    hx, hy = mw/2, mh/2
    vx, vy = len(full_cols)/2, len(full_rows)/2
    expected = ((np.abs(xx+.5-kx) <= vx) & (np.abs(yy+.5-ky) <= hy)) | (
                (np.abs(xx+.5-kx) <= hx) & (np.abs(yy+.5-ky) <= vy))
    union = (expected | mark).sum()
    if not union or (expected & mark).sum()/union < .85:
        return None
    mark_color = np.median(pixels[cv2.erode(mark.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)], axis=0)
    if not np.isfinite(mark_color).all():
        return None
    clean_panel = core & ~cv2.dilate(mark.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    if not clean_panel.any():
        return None
    fill = np.median(pixels[clean_panel], axis=0)
    outside = (distance < radius*.88) & ~cv2.dilate(panel.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    if not outside.any() or np.percentile(np.max(np.abs(pixels[outside]-field[outside]), axis=1), 95) > 25:
        return None
    if np.percentile(np.max(np.abs(pixels[clean_panel]-fill), axis=1), 95) > 30:
        return None
    rim = np.median(pixels[(distance > radius*.94) & (distance < radius*1.01)], axis=0)
    panel_edge = panel & ~core
    edge = np.median(pixels[panel_edge], axis=0)
    # Circle/rim, panel/outline, and six independent cross dimensions.
    p = np.r_[cx, cy, radius-.3, 1., bx, by, bw, bh, .6, kx, ky, hx, hy, vx, vy,
              colors.ravel(), rim, fill, edge, mark_color]

    def build(p):
        cx, cy, r, sw, x, y, w, h, outline, kx, ky, hx, hy, vx, vy = p[:15]
        top, bottom, rim, fill, edge, cross = p[15:].reshape(-1, 3)
        points = [(kx-vx,ky-hy),(kx+vx,ky-hy),(kx+vx,ky-vy),(kx+hx,ky-vy),
                  (kx+hx,ky+vy),(kx+vx,ky+vy),(kx+vx,ky+hy),(kx-vx,ky+hy),
                  (kx-vx,ky+vy),(kx-hx,ky+vy),(kx-hx,ky-vy),(kx-vx,ky-vy)]
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                '<defs><linearGradient id="disk_color" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{_hex(top)}"/><stop offset="1" stop-color="{_hex(bottom)}"/>'
                '</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="url(#disk_color)" stroke="{_hex(rim)}" stroke-width="{sw:.4f}"/>'
                f'<rect x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}" fill="{_hex(fill)}" stroke="{_hex(edge)}" stroke-width="{outline:.4f}"/>'
                '<polygon points="'+' '.join(f'{x:.4f},{y:.4f}' for x,y in points)+f'" fill="{_hex(cross)}"/></svg>\n')

    def valid(p):
        cx, cy, r, sw, x, y, w, h, outline, kx, ky, hx, hy, vx, vy = p[:15]
        return (np.isfinite(p).all() and r > 5 and .1 <= sw <= 3 and .1 <= outline <= 2.5
                and w > h > 5 and hx > vx >= 1 and hy > vy >= 1
                and 0 <= cx-r-sw/2 and cx+r+sw/2 <= width
                and 0 <= cy-r-sw/2 and cy+r+sw/2 <= height
                and x+outline/2 < kx-hx < kx+hx < x+w-outline/2
                and y+outline/2 < ky-hy < ky+hy < y+h-outline/2
                and all((px-cx)**2+(py-cy)**2 < (r-sw)**2
                        for px in (x,x+w) for py in (y,y+h)))

    return _register(p, 15, build, valid, pixels.astype(np.uint8), render_fn, error_fn,
                     'raster_cross_panel_disk_registration')
