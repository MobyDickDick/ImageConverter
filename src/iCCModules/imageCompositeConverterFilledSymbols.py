"""Register analytic filled symbols using description constraints and pixels."""
from __future__ import annotations

import cv2
import numpy as np


def _hex(bgr):
    return '#' + ''.join(f'{int(v):02x}' for v in np.clip(np.rint(bgr[::-1]), 0, 255))


def _register(parameters, geometry_count, build, valid, image, render_fn, error_fn, source):
    """Bounded coordinate descent; contours and reference vectors are never emitted."""
    height, width = image.shape[:2]
    evaluations = 0

    def measure(p):
        nonlocal evaluations
        if not valid(p):
            return None
        svg = build(p)
        evaluations += 1
        raster = render_fn(svg, width, height)
        if raster is None:
            return None
        error = float(error_fn(image, raster))
        loss = float(np.mean((image.astype(float)-np.asarray(raster, dtype=float))**2))
        return (loss, error, svg, raster) if np.isfinite(error) and np.isfinite(loss) else None

    parameters = np.asarray(parameters, dtype=float)
    best = measure(parameters)
    if best is None:
        return None
    initial_error = best[1]
    for step in (1., .5, .25, .125):
        for _ in range(2):
            improved = False
            for index in range(len(parameters)):
                for sign in (-1., 1.):
                    candidate = parameters.copy()
                    candidate[index] += sign*step*(4 if index >= geometry_count else 1)
                    measured = measure(candidate)
                    if measured is not None and measured[0] < best[0]-1e-9:
                        parameters, best, improved = candidate, measured, True
            if not improved:
                break
    if best[1] > initial_error+1e-9:
        return None
    return {'svg': best[2], 'rendered': best[3], 'error': best[1],
            'initial_error': initial_error, 'parameters': parameters.tolist(),
            'evaluations': evaluations, 'source': source}


def _image(width, height, image):
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 12:
        return None
    pixels = arr.astype(float)
    return pixels if np.isfinite(pixels).all() else None


def fit_disk_bar(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(token in text for token in ('kreis', 'balken', 'waagerecht', 'abgerundet', 'vertikal', 'verlauf')):
        return None
    if any(token in text for token in ('senkrechter balken', 'ohne balken', 'zwei', 'zusätzlich',
                                      'dreieck', 'griff', 'beschrift')):
        return None
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    mask = (np.min(pixels, axis=2) < 235).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if count < 2:
        return None
    index = 1+int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = stats[index]
    if sum(stats[i, cv2.CC_STAT_AREA] for i in range(1, count) if i != index) > max(3, area*.005):
        return None
    mask = (labels == index).astype(np.uint8)
    if not (.85 < w/h < 1.18 and area > .65*w*h):
        return None
    contour = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0][0][:, 0].astype(float)+.5
    coefficients = np.linalg.lstsq(np.c_[2*contour, np.ones(len(contour))],
                                   np.sum(contour**2, axis=1), rcond=None)[0]
    cx, cy = coefficients[:2]
    radius = float(np.sqrt(max(0., coefficients[2]+cx*cx+cy*cy)))
    if radius < 5 or np.mean(np.abs(np.linalg.norm(contour-[cx, cy], axis=1)-radius)) > max(.7, radius*.04):
        return None
    yy, xx = np.indices((height, width), dtype=float)
    distance = np.hypot(xx+.5-cx, yy+.5-cy)
    t = (yy+.5-(cy-radius))/(2*radius)
    # Exposed upper/lower disk regions establish the background color field.
    exposed = (distance < radius*.78) & (np.abs(yy+.5-cy) > radius*.28)
    if exposed.sum() < 12:
        return None
    weights = np.c_[1-t[exposed], t[exposed]]
    colors = np.linalg.lstsq(weights, pixels[exposed], rcond=None)[0]
    if colors[0].mean() <= colors[1].mean()+5:
        return None
    field = (1-t[..., None])*colors[0]+t[..., None]*colors[1]
    contrast = np.mean(field-pixels, axis=2)
    bar_mask = ((contrast > 35) & (distance < radius*.8)).astype(np.uint8)
    # A pale highlight can split an antialiased rounded end from its body.
    # Close only one-pixel gaps; the capsule residual still checks shape.
    bar_mask = cv2.morphologyEx(bar_mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    count, bar_labels, bar_stats, _ = cv2.connectedComponentsWithStats(bar_mask)
    if count < 2:
        return None
    index = 1+int(np.argmax(bar_stats[1:, cv2.CC_STAT_AREA]))
    bx, by, bw, bh, bar_area = bar_stats[index]
    if sum(bar_stats[i, cv2.CC_STAT_AREA] for i in range(1, count) if i != index) > max(2, bar_area*.01):
        return None
    bar_mask = (bar_labels == index).astype(np.uint8)
    if not (bw > 2*bh >= 6 and abs(by+bh/2-cy) < radius*.12
            and abs(bx+bw/2-cx) < radius*.12 and bar_area > bw*bh*.75):
        return None
    widths = bar_mask[by:by+bh, bx:bx+bw].sum(axis=1)
    if max(widths[0], widths[-1]) > widths[bh//2]-max(1., bh*.1):
        return None
    core = cv2.erode(bar_mask, np.ones((3, 3), np.uint8)).astype(bool)
    if not core.any():
        return None
    bar_color = np.median(pixels[core], axis=0)
    if np.percentile(np.max(np.abs(pixels[core]-bar_color), axis=1), 95) > 25:
        return None
    # Require one uniform capsule and a clean disk, rather than erasing marks.
    outside_bar = (distance < radius*.8) & (np.abs(yy+.5-cy) > bh*.8)
    if np.percentile(np.max(np.abs(pixels[outside_bar]-field[outside_bar]), axis=1), 95) > 25:
        return None
    bar_contour = cv2.findContours(bar_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0][0][:, 0].astype(float)+.5
    center_x, center_y = bx+bw/2, by+bh/2
    segment_half = (bw-bh)/2
    dx = np.maximum(np.abs(bar_contour[:, 0]-center_x)-segment_half, 0)
    residual = np.abs(np.hypot(dx, bar_contour[:, 1]-center_y)-bh/2)
    if residual.mean() > max(.8, bh*.12):
        return None
    rim = pixels[(distance > radius*.94) & (distance < radius*1.01)]
    rim_color = np.median(rim, axis=0)
    edge_region = (cv2.dilate(bar_mask, np.ones((3, 3), np.uint8))-bar_mask).astype(bool)
    edge_pixels = pixels[edge_region]
    if not len(edge_pixels):
        return None
    # Bright outline evidence, excluding the darker background color field.
    edge_pixels = edge_pixels[edge_pixels.mean(axis=1) >= np.percentile(edge_pixels.mean(axis=1), 70)]
    outline_color = np.median(edge_pixels, axis=0)
    # Geometry first, then two disk colors, rim, bar and its pale outline.
    p = np.r_[cx, cy, radius-.3, 1., bx, by, bw, bh, .8,
              colors.ravel(), rim_color, bar_color, outline_color]

    def build(p):
        cx, cy, r, sw, x, y, w, h, outline = p[:9]
        top, bottom, rim, bar, edge = p[9:].reshape(-1, 3)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="disk_color" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{_hex(top)}"/><stop offset="1" stop-color="{_hex(bottom)}"/>'
                '</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="url(#disk_color)" stroke="{_hex(rim)}" stroke-width="{sw:.4f}"/>'
                f'<rect x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}" rx="{h/2:.4f}" fill="{_hex(bar)}" stroke="{_hex(edge)}" stroke-width="{outline:.4f}"/></svg>\n')

    def valid(p):
        cx, cy, r, sw, x, y, w, h, outline = p[:9]
        return (r > 4 and .1 <= sw <= 3 and .1 <= outline <= 2.5 and w > 2*h >= 4
                and 0 <= cx-r-sw/2 and cx+r+sw/2 <= width
                and 0 <= cy-r-sw/2 and cy+r+sw/2 <= height
                and abs(x+w/2-cx) < r*.12 and abs(y+h/2-cy) < r*.12
                and all((px-cx)**2+(py-cy)**2 < (r-sw)**2 for px in (x, x+w) for py in (y, y+h)))

    return _register(p, 9, build, valid, image, render_fn, error_fn, 'raster_disk_bar_v1')


def fit_solid_arrow(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(token in text for token in ('pfeil', 'schaft', 'dreieck', 'ohne lücke', 'nach unten')):
        return None
    if any(token in text for token in ('kreis', 'verlauf', 'nach oben', 'zwei', 'zusätzlich', 'beschrift')):
        return None
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    mask = (np.min(pixels, axis=2) < 190).astype(np.uint8)
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    if count != 2:
        return None
    x, y, w, h, _ = stats[1]
    rows = np.arange(y, y+h)
    left = np.array([np.flatnonzero(mask[row])[0] for row in rows], dtype=float)
    right = np.array([np.flatnonzero(mask[row])[-1]+1 for row in rows], dtype=float)
    shoulder = int(np.argmax(right-left))
    if shoulder < 3 or h-shoulder < 4:
        return None
    stem_left, stem_right = np.median(left[:shoulder]), np.median(right[:shoulder])
    if max(np.max(np.abs(left[:shoulder]-stem_left)), np.max(np.abs(right[:shoulder]-stem_right))) > 1:
        return None
    indices = np.arange(shoulder+1, h-1)
    lfit, rfit = (np.polyfit(rows[indices]+.5, edge[indices], 1) for edge in (left, right))
    if not (lfit[0] > .1 and rfit[0] < -.1):
        return None
    if max(np.mean(np.abs(np.polyval(lfit, rows[indices]+.5)-left[indices])),
           np.mean(np.abs(np.polyval(rfit, rows[indices]+.5)-right[indices]))) > .8:
        return None
    tip_y = (rfit[1]-lfit[1])/(lfit[0]-rfit[0])
    cx = (stem_left+stem_right)/2
    sy = float(rows[shoulder])
    hw = (np.polyval(rfit, sy)-np.polyval(lfit, sy))/2
    core = cv2.erode(mask, np.ones((3, 3), np.uint8)).astype(bool)
    if not core.any():
        return None
    fill = np.median(pixels[core], axis=0)
    if np.percentile(np.max(np.abs(pixels[core]-fill), axis=1), 95) > 25:
        return None
    p = np.r_[cx, float(y), (stem_right-stem_left)/2, sy, hw, min(height-.2, tip_y), .3, fill, fill]

    def build(p):
        cx, top, half, sy, hw, tip, sw = p[:7]
        points = [(cx-half, top), (cx+half, top), (cx+half, sy), (cx+hw, sy),
                  (cx, tip), (cx-hw, sy), (cx-half, sy)]
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                '<polygon points="'+' '.join(f'{x:.4f},{y:.4f}' for x, y in points)+
                f'" fill="{_hex(p[7:10])}" stroke="{_hex(p[10:13])}" stroke-width="{sw:.4f}"/></svg>\n')

    def valid(p):
        cx, top, half, sy, hw, tip, sw = p[:7]
        return (1 < half < hw and 0 <= sw <= 2 and 0 <= top < sy < tip <= height
                and 0 <= cx-hw and cx+hw <= width)

    return _register(p, 7, build, valid, image, render_fn, error_fn, 'raster_solid_arrow_v1')
