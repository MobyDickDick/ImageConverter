"""Register nested upright flames: a polygonal crown and a cubic rounded bowl.

Raster boundaries initialize line regressions and bowl dimensions. The emitted
model has a bounded number of tongues, independent of raster resolution.
"""
from __future__ import annotations

from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description, gradient_direction

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def _component(mask, minimum=8, max_noise=3):
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    if count < 2:
        return None
    index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    area = stats[index, cv2.CC_STAT_AREA]
    if area < minimum or sum(stats[i, cv2.CC_STAT_AREA] for i in range(1, count)
                             if i != index) > max(max_noise, area*.002):
        return None
    return (labels == index).astype(np.uint8)


def _flame_model(mask):
    """Regress a small jagged crown; replace the lower silhouette by a bowl."""
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    x0, x1, top, bottom = xs.min(), xs.max()+1., ys.min(), ys.max()+1.
    if not (x1-x0 >= 5 and bottom-top >= 8 and .4 < (x1-x0)/(bottom-top) < 1.35):
        return None
    waist = int(top+(bottom-top)*.70)
    upper = mask.copy()
    upper[waist+1:] = 0
    contour = max(cv2.findContours(upper, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0],
                  key=cv2.contourArea)
    # Corner detection only segments the measurements. Each output edge is a
    # fitted line; no sampled contour is stored or serialized as an SVG path.
    tolerance = max(1.1, (bottom-top)*.035)
    samples = contour[:, 0].astype(float)+.5
    at_base = np.flatnonzero(samples[:, 1] == waist+.5)
    if len(at_base) < 2:
        return None
    left = at_base[np.argmin(samples[at_base, 0])]
    right = at_base[np.argmax(samples[at_base, 0])]
    chains = []
    for direction in (-1, 1):
        indices = [left]
        while indices[-1] != right and len(indices) <= len(samples):
            indices.append((indices[-1]+direction) % len(samples))
        chains.append(samples[indices])
    upper_chain = min(chains, key=lambda a: a[:, 1].min())
    for factor in (1., 1.3, 1.6):
        crown = cv2.approxPolyDP(upper_chain.astype(np.float32), tolerance*factor, False)[:, 0].astype(float)
        if len(crown) <= 15:
            tolerance *= factor
            break
    if not 5 <= len(crown) <= 15:
        return None
    highest = np.flatnonzero(crown[:, 1] <= crown[:, 1].min()+.6)
    if (1 < len(highest) <= 3 and np.all(np.diff(highest) == 1)
            and np.ptp(crown[highest, 0]) < (bottom-top)*.15):
        # A subpixel tip may occupy a short horizontal run. Regress one apex
        # from that run instead of interpreting its two pixel corners as tips.
        crown = np.concatenate([crown[:highest[0]], crown[highest].mean(axis=0)[None],
                                crown[highest[-1]+1:]])
    # At least two pointed tongues separated by a concavity distinguish a
    # flame crown from a triangle or a smooth teardrop.
    edges = np.diff(crown, axis=0)
    turns = edges[:-1, 0]*edges[1:, 1]-edges[:-1, 1]*edges[1:, 0]
    if not ((turns > .5).sum() >= 1 and (turns < -.5).sum() >= 2):
        return None
    pointed_top = False
    for i in range(1, len(crown)-1):
        if crown[i, 1] > crown[:, 1].min()+(bottom-top)*.08:
            continue
        a, b = crown[i-1]-crown[i], crown[i+1]-crown[i]
        if np.dot(a, b) > .2*np.linalg.norm(a)*np.linalg.norm(b):
            pointed_top = True
    if not pointed_top:
        return None
    samples = upper_chain
    lines = []
    for a, b in zip(crown, crown[1:]):
        delta = b-a
        length = np.linalg.norm(delta)
        if length < 1:
            return None
        direction = delta/length
        normal = np.array([-direction[1], direction[0]])
        along = (samples-a)@direction
        near = (np.abs((samples-a)@normal) < tolerance+1) & (along > .3) & (along < length-.3)
        points = samples[near]
        if len(points) >= 3:
            center = points.mean(axis=0)
            _, _, vectors = np.linalg.svd(points-center, full_matrices=False)
            n = vectors[-1]
            lines.append((n, float(n@center)))
        else:
            lines.append((normal, float(normal@((a+b)/2))))
    fitted = crown.copy()
    for i in range(1, len(crown)-1):
        matrix = np.array([lines[i-1][0], lines[i][0]])
        if abs(np.linalg.det(matrix)) > .15:
            point = np.linalg.solve(matrix, [lines[i-1][1], lines[i][1]])
            bound = .75 if crown[i, 1] <= crown[:, 1].min()+.6 else 2.
            if np.linalg.norm(point-crown[i]) < tolerance*bound:
                fitted[i] = point
    return np.r_[fitted.ravel(), (x0+x1)/2, bottom-.25]


def flame_parts(parameters, count, color):
    crown = parameters[:2*count].reshape(-1, 2)
    left, right = crown[0], crown[-1]
    bx, by = parameters[-2:]
    lx, ly = left; rx, ry = right
    points = ' '.join(f'{x:.4f},{y:.4f}' for x, y in crown)
    # Two quarter-ellipse cubics form the rounded lower bowl. An overlapping
    # chord avoids renderer seams with the separately filled polygonal crown.
    bowl = (f'M {lx:.4f} {ly-.15:.4f} L {lx:.4f} {ly:.4f} '
            f'C {lx:.4f} {ly+(by-ly)*.5523:.4f} {bx-(bx-lx)*.5523:.4f} {by:.4f} {bx:.4f} {by:.4f} '
            f'C {bx+(rx-bx)*.5523:.4f} {by:.4f} {rx:.4f} {ry+(by-ry)*.5523:.4f} {rx:.4f} {ry:.4f} '
            f'L {rx:.4f} {ry-.15:.4f} Z')
    return (f'<polygon points="{points}" fill="{color}"/>'
            f'<path d="{bowl}" fill="{color}"/>')


def _model_outline(model, count):
    crown = model[:2*count].reshape(-1, 2)
    left, right, bottom = crown[0], crown[-1], model[-2:]
    t = np.linspace(0, 1, 12)[:, None]
    def quarter(a, b, c, d):
        return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
    first = quarter(left, [left[0], left[1]+(bottom[1]-left[1])*.5523],
                    [bottom[0]-(bottom[0]-left[0])*.5523, bottom[1]], bottom)
    second = quarter(bottom, [bottom[0]+(right[0]-bottom[0])*.5523, bottom[1]],
                     [right[0], right[1]+(bottom[1]-right[1])*.5523], right)
    return np.concatenate([crown, second[::-1], first[::-1]]).astype(np.float32)


def fit_flame_disk(width, height, *, description, image, render_fn, error_fn):
    text = normalize_description(description, orientations=True).casefold()
    if not gradient_direction(text, 'senkrecht'):
        return None
    if not all(word in text for word in ('kreis', 'senkrecht', 'verlauf', 'flamme', 'aufrecht',
                                         'gefüllt', 'zungen', 'spitz', 'rund', 'inner', 'kleinere', 'helle')):
        return None
    if re.search(r'\b(?:ohne|kein\w*|nicht|zusätzlich|diagonal|umgekehrt|dreieck|schriftzeichen)\b',
                 text.replace('keine schriftzeichen', '')):
        return None
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    background = np.median(np.r_[pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]], axis=0)
    disk = _component(np.max(abs(pixels-background), axis=2) > 30, minimum=30)
    if disk is None:
        return None
    contour = max(cv2.findContours(disk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0].astype(float)+.5
    coefficients = np.linalg.lstsq(np.c_[2*contour, np.ones(len(contour))],
                                   np.sum(contour**2, axis=1), rcond=None)[0]
    cx, cy = coefficients[:2]
    radius = float(np.sqrt(max(0., coefficients[2]+cx*cx+cy*cy)))
    if radius < 10 or np.mean(np.abs(np.linalg.norm(contour-[cx, cy], axis=1)-radius)) > max(.7, radius*.035):
        return None
    yy, xx = np.indices((height, width), dtype=float)
    distance = np.hypot(xx+.5-cx, yy+.5-cy)
    t = (yy+.5-(cy-radius))/(2*radius)
    exposed = (distance < radius*.87) & (abs(xx+.5-cx) > radius*.67)
    if exposed.sum() < 12:
        return None
    colors = np.linalg.lstsq(np.c_[1-t[exposed], t[exposed]], pixels[exposed], rcond=None)[0]
    field = (1-t[..., None])*colors[0]+t[..., None]*colors[1]
    if np.max(abs(colors[0]-colors[1])) < 8:
        return None
    outer = _component((np.max(abs(pixels-field), axis=2) > 45) & (distance < radius*.95))
    if outer is None:
        return None
    core = cv2.erode(outer, np.ones((3, 3), np.uint8)).astype(bool)
    if core.sum() < 12:
        return None
    fill = np.median(pixels[core], axis=0)
    inner_region = cv2.erode(outer, np.ones((5, 5), np.uint8)).astype(bool)
    flame_rows = np.nonzero(outer)[0]
    lower_interior = yy+.5 > flame_rows.min()+(flame_rows.max()+1-flame_rows.min())*.33
    inner = _component(core & lower_interior & (np.mean(pixels-fill, axis=2) > 35), max_noise=8)
    if inner is None or inner.sum() > outer.sum()*.65:
        return None
    outer_p, inner_p = _flame_model(outer), _flame_model(inner)
    if outer_p is None or inner_p is None:
        return None
    clean = inner_region & ~cv2.dilate(inner, np.ones((3, 3), np.uint8)).astype(bool)
    inner_core = cv2.erode(inner, np.ones((3, 3), np.uint8)).astype(bool)
    outside = (distance < radius*.88) & ~cv2.dilate(outer, np.ones((3, 3), np.uint8)).astype(bool)
    if not clean.any() or not inner_core.any() or not outside.any():
        return None
    fill, light = np.median(pixels[clean], axis=0), np.median(pixels[inner_core], axis=0)
    if (np.percentile(np.max(abs(pixels[outside]-field[outside]), axis=1), 95) > 30
            or np.percentile(np.max(abs(pixels[clean]-fill), axis=1), 95) > 40):
        return None
    unexplained = inner_region & ~cv2.dilate(inner, np.ones((5, 5), np.uint8)).astype(bool)
    unexplained &= np.max(abs(pixels-fill), axis=2) > 80
    count, _, stats, _ = cv2.connectedComponentsWithStats(unexplained.astype(np.uint8))
    if count > 1 and stats[1:, cv2.CC_STAT_AREA].max() >= 3:
        return None
    rim = np.median(pixels[(distance > radius*.94) & (distance < radius*1.01)], axis=0)
    n, k = (len(outer_p)-2)//2, (len(inner_p)-2)//2
    geometry = 4+len(outer_p)+len(inner_p)
    p = np.r_[cx, cy, radius-.3, 1., outer_p, inner_p, colors.ravel(), rim, fill, light, background]

    def build(p):
        cx, cy, r, sw = p[:4]
        top, bottom, rim, fill, light, background = p[geometry:].reshape(-1, 3)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                '<defs><linearGradient id="disk_color" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{_hex(top)}"/><stop offset="1" stop-color="{_hex(bottom)}"/>'
                '</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="{_hex(background)}"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="url(#disk_color)" stroke="{_hex(rim)}" stroke-width="{sw:.4f}"/>'
                +flame_parts(p[4:4+len(outer_p)], n, _hex(fill))
                +flame_parts(p[4+len(outer_p):geometry], k, _hex(light))+'</svg>\n')

    def valid(p):
        cx, cy, r, sw = p[:4]
        if not (np.isfinite(p).all() and r > 8 and .1 <= sw <= 3
                and 0 <= cx-r-sw/2 and cx+r+sw/2 <= width
                and 0 <= cy-r-sw/2 and cy+r+sw/2 <= height):
            return False
        for model, count in ((p[4:4+len(outer_p)], n), (p[4+len(outer_p):geometry], k)):
            crown = model[:2*count].reshape(-1, 2)
            bx, by = model[-2:]
            if not (crown[0, 0] < bx < crown[-1, 0] and by > max(crown[0, 1], crown[-1, 1])
                    and np.all(np.linalg.norm(crown-[cx, cy], axis=1) < r-sw/2)
                    and np.hypot(bx-cx, by-cy) < r-sw/2):
                return False
        outside = _model_outline(p[4:4+len(outer_p)], n)
        inside = _model_outline(p[4+len(outer_p):geometry], k)
        return all(cv2.pointPolygonTest(outside, tuple(map(float, point)), False) > 0 for point in inside)

    return _register(p, geometry, build, valid, pixels.astype(np.uint8), render_fn, error_fn,
                     'raster_flame_disk_registration')
