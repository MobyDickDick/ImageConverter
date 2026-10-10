"""Register a circle, two converging chords and an interior T from pixels."""
from __future__ import annotations

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register


def _segment_distance(xx, yy, a, b):
    delta = np.asarray(b)-a
    t = np.clip(((xx-a[0])*delta[0]+(yy-a[1])*delta[1])/np.dot(delta, delta), 0, 1)
    return np.hypot(xx-a[0]-t*delta[0], yy-a[1]-t*delta[1])


def fit_circle_linework(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(token in text for token in ('kreis', 'zwei schräge linien', 'waagerecht', 'senkrecht', 'nach unten')):
        return None
    if any(token in text for token in ('dreieck', 'verlauf', 'zusätzlich', 'griff', 'nach oben', 'ohne t')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 16 or not np.isfinite(arr).all():
        return None
    pixels = arr.astype(float)
    mask = (np.min(arr, axis=2) < 210).astype(np.uint8)
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < width*height*.15 or len(contour) < 12:
        return None
    if sum(cv2.contourArea(c) for c in contours if c is not contour) > max(2, cv2.contourArea(contour)*.005):
        return None
    points = contour[:, 0].astype(float)+.5
    coefficients = np.linalg.lstsq(np.c_[2*points, np.ones(len(points))], np.sum(points**2, axis=1), rcond=None)[0]
    cx, cy = coefficients[:2]
    radius = float(np.sqrt(max(0, coefficients[2]+cx*cx+cy*cy)))
    if radius < 6 or np.percentile(np.abs(np.linalg.norm(points-[cx, cy], axis=1)-radius), 90) > max(.9, radius*.06):
        return None
    yy, xx = np.indices((height, width), dtype=float)
    xx += .5
    yy += .5
    radial = np.hypot(xx-cx, yy-cy)
    core = radial < radius*.88
    fill = np.median(pixels[core], axis=0)
    contrast = np.linalg.norm(pixels-fill, axis=2)
    strength = contrast*(radial < radius*.92)
    # A broad interior region is a different topology, not a set of strokes.
    cutoff = max(10., np.percentile(contrast[core], 95)*.32)
    ink = (strength > cutoff)
    if not .04 < ink[core].mean() < .5:
        return None
    upper = (yy < cy) & (np.abs(xx-cx) < radius*.67)
    profile = (strength*upper).sum(axis=1)
    row = int(np.argmax(profile))
    if profile[row] <= 0:
        return None
    band = ink & (np.abs(yy-(row+.5)) < max(1.1, radius*.07)) & (np.abs(xx-cx) < radius*.8)
    if band.sum() < 5:
        return None
    top = float(np.average(yy[band], weights=strength[band]))
    tx0, tx1 = float(xx[band].min()), float(xx[band].max())
    if tx1-tx0 < radius*.65:
        return None
    vertical = ink & (np.abs(xx-cx) < radius*.14) & (yy > top+radius*.12) & (radial < radius*.87)
    if vertical.sum() < 3:
        return None
    stem_x = float(np.average(xx[vertical], weights=strength[vertical]))
    stem_bottom = float(yy[vertical].max())
    if stem_bottom-top < radius*.65:
        return None
    slopes = []
    diagonals = []
    for sign in (-1, 1):
        region = ink & (sign*(xx-cx) > radius*.19) & (yy > top+radius*.14) & (radial < radius*.92)
        if region.sum() < 4 or np.ptp(yy[region]) < radius*.7:
            return None
        weights = np.sqrt(strength[region])
        a, b = np.linalg.lstsq(np.c_[yy[region]-cy, np.ones(region.sum())]*weights[:, None],
                               (xx[region]-cx)*weights, rcond=None)[0]
        if not .15 < -sign*a < .9:
            return None
        if np.average(np.abs(xx[region]-cx-a*(yy[region]-cy)-b), weights=strength[region]) > max(.8, radius*.06):
            return None
        slopes.extend([float(a), float(b)])
        diagonals.append(region)
    rim = (radial > radius*.94) & (radial < radius*1.02)
    rim_color = np.median(pixels[rim], axis=0)
    diagonal_region = diagonals[0] | diagonals[1]
    diagonal_color = np.median(pixels[diagonal_region & (contrast >= np.percentile(contrast[diagonal_region], 70))], axis=0)
    t_region = band | vertical
    t_color = np.median(pixels[t_region & (contrast >= np.percentile(contrast[t_region], 70))], axis=0)
    sw = max(.4, radius*.04)
    parameters = [cx, cy, radius, sw, *slopes, tx0, tx1, top, stem_x, stem_bottom, sw, sw,
                  *fill, *rim_color, *diagonal_color, *t_color]

    def segments(p):
        x, y, r = p[:3]
        result = []
        for a, b in (p[4:6], p[6:8]):
            roots = np.sort(np.roots([1+a*a, 2*a*b, b*b-r*r]))
            result.append([(x+a*v+b, y+v) for v in roots])
        return [*result, [(p[8], p[10]), (p[9], p[10])], [(p[11], p[10]), (p[11], p[12])]]

    def valid(p):
        x, y, r = p[:3]
        if not (np.isfinite(p).all() and r > 5 and 0 <= x-r < x+r <= width and 0 <= y-r < y+r <= height
                and min(p[3], p[13], p[14]) > 0 and max(p[3], p[13], p[14]) < r*.15
                and .15 < p[4] < .9 and -.9 < p[6] < -.15 and -r*.9 < p[5] < -r*.2 and r*.2 < p[7] < r*.9
                and x-r < p[8] < p[11] < p[9] < x+r and y-r < p[10] < y < p[12] < y+r
                and abs(p[11]-x) < r*.16):
            return False
        return all(np.hypot(px-x, py-y) < r for segment in segments(p)[2:] for px, py in segment)

    def build(p):
        lines = ''.join(f'<line x1="{a[0]:g}" y1="{a[1]:g}" x2="{b[0]:g}" y2="{b[1]:g}" '
                        f'stroke="{_hex(p[21:24] if i < 2 else p[24:27])}" stroke-width="{p[13] if i < 2 else p[14]:g}"/>'
                        for i, (a, b) in enumerate(segments(p)))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<circle cx="{p[0]:g}" cy="{p[1]:g}" r="{p[2]:g}" fill="{_hex(p[15:18])}" '
                f'stroke="{_hex(p[18:21])}" stroke-width="{p[3]:g}"/>{lines}</svg>\n')

    result = _register(parameters, 15, build, valid, arr, render_fn, error_fn, 'raster_circle_linework_v1')
    if result is None:
        return None
    # Each declared segment needs evidence, and all interior ink must be
    # explained. Refinement cannot accept a missing stroke or erase extra ink.
    distances = [_segment_distance(xx, yy, a, b) for a, b in segments(result['parameters'])]
    tolerance = max(.85, radius*.045)
    if np.mean(np.minimum.reduce(distances)[ink] < tolerance*1.7) < .9:
        return None
    nearest_ink = cv2.distanceTransform((~ink).astype(np.uint8), cv2.DIST_L2, 3)
    for a, b in segments(result['parameters']):
        # Sample along the segment, not across a fixed-width pixel band.
        # A one-pixel stroke centered on a pixel occupies one of three band
        # columns, whereas a half-pixel shift occupies two. Both have the
        # same longitudinal evidence and must receive the same decision.
        samples = np.linspace(a, b, max(12, int(np.linalg.norm(np.asarray(b)-a)*2)))
        samples = samples[np.linalg.norm(samples-[cx, cy], axis=1) < radius*.88]
        ix = np.clip(np.floor(samples[:, 0]).astype(int), 0, width-1)
        iy = np.clip(np.floor(samples[:, 1]).astype(int), 0, height-1)
        if not len(samples) or np.mean(nearest_ink[iy, ix] <= max(1.1, tolerance)) < .8:
            return None
    return result
