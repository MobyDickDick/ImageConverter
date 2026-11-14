"""Register an unlabelled circle and one axial handle from observed pixels."""
from __future__ import annotations

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def stem_disk_direction(description):
    text = ' '.join(str(description or '').casefold().split())
    # A reference introduces prose only; it never supplies geometry or paint.
    text = re.sub(r'^wie \w+:\s*', '', text)
    match = re.fullmatch(
        r'(?:kelle, ohne text kreis oben, griff nach (links|rechts|oben|unten)'
        r'(?: \((?:dunkelgraue|graue) li+ne\))?'
        r'|ein unbeschrifteter kreis mit einem geraden griff nach (links|rechts|oben|unten))'
        r'\.?\s*(?:der griff liegt auf einer symmetrieachse des kreises\.?)?', text)
    return next((value for value in match.groups() if value), None) if match else None


def fit_stem_disk(width, height, *, description, image, render_fn, error_fn):
    direction = stem_disk_direction(description)
    pixels = _image(width, height, image)
    if direction is None or pixels is None:
        return None
    # Rotate coordinates into a left-handle frame for measurement only. Output
    # retains a native circle and exactly one line in the original coordinates.
    turns = {'links': 0, 'rechts': 2, 'oben': 1, 'unten': 3}[direction]
    canonical = np.rot90(pixels, turns)
    ch, cw = canonical.shape[:2]
    border = np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]))
    background = np.median(border, axis=0)
    mask = (np.max(abs(canonical-background), axis=2) > 25).astype('uint8')
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if not contours:
        return None
    outline = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(outline)
    points = outline[:, 0].astype(float)+.5
    # Top, bottom and right arc identify the head independently of handle length.
    approx_cx, approx_cy = x+w-h/2, y+h/2
    arc = points[(points[:, 0] > approx_cx) | (abs(points[:, 1]-approx_cy) > h*.2)]
    if len(arc) < 12:
        return None
    coef = np.linalg.lstsq(np.c_[2*arc, np.ones(len(arc))], (arc**2).sum(axis=1), rcond=None)[0]
    cx, cy = coef[:2]
    outer = float(np.sqrt(max(0, coef[2]+cx*cx+cy*cy)))
    if outer < 4 or np.abs(np.linalg.norm(arc-[cx, cy], axis=1)-outer).mean() > max(.6, outer*.035):
        return None
    end = int(np.floor(cx-outer-1))
    sy, sx = np.where(mask[:, :end])
    if end < 2 or len(sx) < 2:
        return None
    left, top, bottom = sx.min(), sy.min(), sy.max()+1
    stem_width = bottom-top
    if (stem_width > outer*.45 or abs((top+bottom)/2-cy) > max(1, outer*.08)
            or not np.array_equal(np.unique(sx), np.arange(left, end))
            or mask[top:bottom, left:end].mean() < .8):
        return None
    yy, xx = np.indices((ch, cw), dtype=float)
    radial = np.hypot(xx+.5-cx, yy+.5-cy)
    core = radial < outer*.65
    fill = np.median(canonical[core], axis=0)
    if np.max(abs(canonical[core]-fill)) > 25:
        return None
    rim = np.percentile(canonical[(radial > outer*.8)&(radial < outer+1)], 10, axis=0)
    stem = np.percentile(canonical[top:bottom, left:end].reshape(-1, 3), 10, axis=0)
    if np.mean(fill-rim) < 15:
        return None
    p = np.r_[cx, cy, outer-.4, max(.7, outer*.07), float(left), min(float(stem_width), outer*.3),
              fill, rim, stem, background]

    def original(x, y):
        if turns == 0:
            return x, y
        if turns == 1:
            return width-y, x
        if turns == 2:
            return width-x, height-y
        return y, height-x

    def build(p):
        cx, cy, r, sw, endpoint, line_width = p[:6]
        ox, oy = original(cx, cy)
        ax, ay = original(endpoint, cy)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<rect width="{width}" height="{height}" fill="{_hex(p[15:18])}"/>'
                f'<line x1="{ax:.4f}" y1="{ay:.4f}" x2="{ox:.4f}" y2="{oy:.4f}" '
                f'stroke="{_hex(p[12:15])}" stroke-width="{line_width:.4f}"/>'
                f'<circle cx="{ox:.4f}" cy="{oy:.4f}" r="{r:.4f}" stroke-width="{sw:.4f}" '
                f'fill="{_hex(p[6:9])}" stroke="{_hex(p[9:12])}"/></svg>')

    def valid(p):
        cx, cy, r, sw, endpoint, line_width = p[:6]
        return (np.isfinite(p).all() and r >= 3 and .3 <= sw <= r*.3
                and .3 <= line_width <= r*.45 and 0 <= endpoint < cx-r-1
                and r+sw/2 <= min(cx, cy, cw-cx, ch-cy)+.5
                and np.linalg.norm(p[:2]-[coef[0], coef[1]]) <= 2
                and abs(r-(outer-.4)) <= 2 and np.all((p[6:] >= 0)&(p[6:] <= 255)))

    def details(p, rendered):
        output = np.rot90(np.asarray(rendered, dtype=float), turns)
        distance = np.hypot(xx+.5-p[0], yy+.5-p[1])
        # Check every exposed interior/background pixel, including small marks
        # that a whole-image average could hide. Leave only AA boundary bands.
        interior = distance < p[2]-p[3]/2-1.5
        handle = (xx+.5 >= p[4]-1.5)&(xx+.5 <= p[0])&(abs(yy+.5-p[1]) <= p[5]/2+1.5)
        outside = (distance > p[2]+p[3]/2+1.5)&~handle
        exposed = interior|outside
        return bool(exposed.any() and np.max(abs(canonical[exposed]-output[exposed])) <= 25)

    fitted = _register(p, 6, build, valid, image, render_fn, error_fn, 'stem_disk_v1',
                       satisfactory_fn=lambda p, measured: details(p, measured[3]))
    if fitted is None:
        return None
    quality = pixel_quality(image, fitted['rendered'])
    if not quality or not quality['passed'] or not details(fitted['parameters'], fitted['rendered']):
        return None
    fitted.update(quality=quality, direction=direction)
    return fitted
