"""Register a three-band rectangular panel enclosed by a gradient disk."""
from __future__ import annotations

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def fit_striped_panel_disk(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(word in text for word in ('kreis', 'verlauf', 'vertikal', 'rechteck',
                                         'drei', 'waagerecht', 'streifen', 'gefüllt', 'innerhalb')):
        return None
    if re.search(r'\b(?:ohne|kein|keine|nicht|zwei|vier|zusätzlich|dreieck|diagonal|schriftzeichen)\b',
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
    largest = np.max(panel_stats[1:, cv2.CC_STAT_AREA])
    components = [i for i in range(1, count) if panel_stats[i, cv2.CC_STAT_AREA] >= max(5, largest*.1)]
    bx = min(panel_stats[i, 0] for i in components)
    by = min(panel_stats[i, 1] for i in components)
    bw = max(panel_stats[i, 0]+panel_stats[i, 2] for i in components)-bx
    bh = max(panel_stats[i, 1]+panel_stats[i, 3] for i in components)-by
    panel_area = sum(panel_stats[i, cv2.CC_STAT_AREA] for i in components)
    if not (bw > bh >= 9 and panel_area > .88*bw*bh):
        return None
    if sum(panel_stats[i, cv2.CC_STAT_AREA] for i in range(1, count) if i not in components) > max(3, panel_area*.01):
        return None
    # Robust row colors locate the two transitions without assuming equal
    # stripe heights or a national palette. No measured contour is emitted.
    inset = max(1, round(bw*.1))
    region = pixels[by:by+bh, bx+inset:bx+bw-inset]
    rows = np.median(region, axis=1)
    best = None
    for first in range(3, bh-5):
        for second in range(first+3, bh-2):
            cuts = (0, first, second, bh)
            bands = [np.median(rows[a:b], axis=0) for a,b in zip(cuts, cuts[1:])]
            loss = sum(np.sum((rows[a:b]-color)**2) for a,b,color in zip(cuts, cuts[1:], bands))
            if best is None or loss < best[0]:
                best = (loss, first, second, bands)
    if best is None:
        return None
    _, first, second, bands = best
    if min(np.max(np.abs(a-b)) for a,b in zip(bands, bands[1:])) < 45:
        return None
    # Interiors must be uniform and rectangular. Reject marks, gaps and
    # slanted stripes instead of fitting away an incompatible scene.
    for a,b,color in zip((0, first, second), (first, second, bh), bands):
        edge_inset = 2 if b-a >= 6 else 1
        core = pixels[by+a+edge_inset:by+b-edge_inset, bx+2:bx+bw-2]
        if core.size == 0:
            return None
        if np.mean(np.max(np.abs(core-color), axis=2) > 32) > .02:
            return None
    outside = (distance < radius*.88) & ~((xx >= bx-2) & (xx <= bx+bw+1)
                                                 & (yy >= by-2) & (yy <= by+bh+1))
    if not outside.any() or np.mean(np.max(np.abs(pixels[outside]-field[outside]), axis=1) > 30) > .02:
        return None
    rim = np.median(pixels[(distance > radius*.94) & (distance < radius*1.01)], axis=0)
    p = np.r_[cx, cy, radius-.3, 1., bx, by, bw, bh, first, second,
              colors.ravel(), rim, np.asarray(bands).ravel()]

    def build(p):
        cx,cy,r,sw,x,y,w,h,first,second = p[:10]
        top,bottom,rim,*bands = p[10:].reshape(-1,3)
        stripes = ''.join(f'<rect x="{x:.4f}" y="{y+a:.4f}" width="{w:.4f}" height="{b-a:.4f}" fill="{_hex(color)}"/>'
                          for a,b,color in zip((0,first,second),(first,second,h),bands))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                '<defs><linearGradient id="disk_color" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{_hex(top)}"/><stop offset="1" stop-color="{_hex(bottom)}"/>'
                '</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="url(#disk_color)" stroke="{_hex(rim)}" stroke-width="{sw:.4f}"/>'
                +stripes+'</svg>\n')

    def valid(p):
        cx,cy,r,sw,x,y,w,h,first,second = p[:10]
        return (np.isfinite(p).all() and r > 5 and .1 <= sw <= 3 and w > h > 5
                and 1 < first < second-1 < h-2
                and 0 <= cx-r-sw/2 and cx+r+sw/2 <= width
                and 0 <= cy-r-sw/2 and cy+r+sw/2 <= height
                and all((px-cx)**2+(py-cy)**2 < (r-sw)**2 for px in (x,x+w) for py in (y,y+h)))

    return _register(p, 10, build, valid, pixels.astype(np.uint8), render_fn, error_fn,
                     'raster_striped_panel_disk_registration')
