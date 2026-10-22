"""Register a three-band rectangular panel enclosed by a gradient disk."""
from __future__ import annotations

from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description, gradient_direction

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def fit_striped_panel_disk(width, height, *, description, image, render_fn, error_fn):
    text = normalize_description(description, orientations=True).casefold()
    if not gradient_direction(text, 'senkrecht'):
        return None
    # The disk gradient and panel orientation are independent of the bands.
    vertical = bool(re.search(r'senkrecht\w* (?:gefüllt\w* )?streifen', text))
    horizontal = bool(re.search(r'waagerecht\w* (?:gefüllt\w* )?streifen', text))
    if vertical == horizontal:
        return None
    if not all(word in text for word in ('kreis', 'verlauf', 'senkrecht', 'rechteck',
                                         'drei', 'waagerecht', 'streifen', 'gefüllt', 'innerhalb')):
        return None
    if re.search(r'\b(?:ohne|kein|keine|nicht|zwei|vier|zusätzlich|dreieck|diagonal|schriftzeichen)\b',
                 text.replace('keine schriftzeichen', '').replace('ohne lücke', '')):
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
    # Transpose only the panel measurements; the disk's gradient remains
    # vertical in the original raster and in the emitted SVG.
    panel_pixels = pixels.swapaxes(0, 1) if vertical else pixels
    if vertical:
        bx, by, bw, bh = by, bx, bh, bw
        inset = max(1, round(bw*.1))
    region = panel_pixels[by:by+bh, bx+inset:bx+bw-inset]
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
        # JPEG chroma ringing extends farther across vertical color edges.
        # Sample the solid interior, while keeping the same residual limit.
        if vertical and b-a >= 8:
            edge_inset = 3
        side_inset = 3 if vertical and bw >= 12 else 2
        core = panel_pixels[by+a+edge_inset:by+b-edge_inset, bx+side_inset:bx+bw-side_inset]
        if core.size == 0:
            return None
        if np.mean(np.max(np.abs(core-color), axis=2) > 32) > .02:
            return None
    panel_x, panel_y = (yy, xx) if vertical else (xx, yy)
    outside = (distance < radius*.88) & ~((panel_x >= bx-2) & (panel_x <= bx+bw+1)
                                                 & (panel_y >= by-2) & (panel_y <= by+bh+1))
    if not outside.any() or np.mean(np.max(np.abs(pixels[outside]-field[outside]), axis=1) > 30) > .02:
        return None
    rim = np.median(pixels[(distance > radius*.94) & (distance < radius*1.01)], axis=0)
    p = np.r_[cx, cy, radius-.3, 1., bx, by, bw, bh, first, second,
              colors.ravel(), rim, np.asarray(bands).ravel()]

    def build(p):
        cx,cy,r,sw,x,y,w,h,first,second = p[:10]
        top,bottom,rim,*bands = p[10:].reshape(-1,3)
        rectangles = [(y+a,x,b-a,w) if vertical else (x,y+a,w,b-a)
                      for a,b in zip((0,first,second),(first,second,h))]
        stripes = ''.join(f'<rect x="{sx:.4f}" y="{sy:.4f}" width="{sw:.4f}" height="{sh:.4f}" fill="{_hex(color)}"/>'
                          for (sx,sy,sw,sh),color in zip(rectangles,bands))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                '<defs><linearGradient id="disk_color" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{_hex(top)}"/><stop offset="1" stop-color="{_hex(bottom)}"/>'
                '</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="url(#disk_color)" stroke="{_hex(rim)}" stroke-width="{sw:.4f}"/>'
                +stripes+'</svg>\n')

    def valid(p):
        cx,cy,r,sw,x,y,w,h,first,second = p[:10]
        panel_cx, panel_cy = (cy,cx) if vertical else (cx,cy)
        aspect_ok = h > w > 5 if vertical else w > h > 5
        return (np.isfinite(p).all() and r > 5 and .1 <= sw <= 3 and aspect_ok
                and 1 < first < second-1 < h-2
                and 0 <= cx-r-sw/2 and cx+r+sw/2 <= width
                and 0 <= cy-r-sw/2 and cy+r+sw/2 <= height
                and all((px-panel_cx)**2+(py-panel_cy)**2 < (r-sw)**2 for px in (x,x+w) for py in (y,y+h)))

    return _register(p, 10, build, valid, pixels.astype(np.uint8), render_fn, error_fn,
                     'raster_striped_panel_disk_registration')
