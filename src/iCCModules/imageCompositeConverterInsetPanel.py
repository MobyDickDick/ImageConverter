"""A rounded grey gradient panel with a white, square-cut inset.

The description fixes the two-object topology. Geometry and paint are fitted
from pixels, without catalogue identities, reference vectors or traced edges.
"""
from __future__ import annotations

import re

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality
from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register


def inset_panel_contract(description):
    text = re.sub(r'\s+', ' ', normalize_description(description).casefold().replace('weiß', 'weiss')).strip()
    return bool(re.fullmatch(
        r'im hintergrund liegt ein waagerechtes rechteck mit abgerundeten ecken und einem '
        r'vertikalen graustufenverlauf: oben leicht heller, unten etwas dunkler\. '
        r'davor liegt ein etwas kleineres weisses rechteck, dessen linke ecken abgerundet sind\. '
        r'das weisse vordergrundrechteck ist rechts bei ungefähr 90 prozent der breite des '
        r'hintergrundrechtecks senkrecht abgeschnitten\. dadurch bleiben oben, unten und links '
        r'schmale graue ränder sowie rechts ein breiterer grauer bereich sichtbar\. '
        r'keine beschriftung oder weiteren zeichen\.', text))


def inset_details(image, rendered, parameters):
    """Small corner/cut/paint regions must pass independently of global MSE."""
    x, y, X, Y, rx, ry, a, b, A, B, u, v = parameters[:12]
    h, w = image.shape[:2]
    regions = {}
    for name, cx, cy, dx, dy in (
        ('outer_top_left', x, y, 1, 1), ('outer_bottom_left', x, Y, 1, -1),
        ('outer_top_right', X, y, -1, 1), ('outer_bottom_right', X, Y, -1, -1),
        ('inner_top_left', a, b, 1, 1), ('inner_bottom_left', a, B, 1, -1),
        ('square_cut', A, (b+B)/2, 1, 1),
    ):
        sx, sy = max(3, int(np.ceil(rx))+1), max(3, int(np.ceil(ry))+1)
        if name == 'square_cut':
            left, right, top, bottom = A-2, A+3, b+1, B-1
        else:
            left, right = sorted((cx-1*dx, cx+sx*dx))
            top, bottom = sorted((cy-1*dy, cy+sy*dy))
        left, right = max(0, int(np.floor(left))), min(w, int(np.ceil(right)))
        top, bottom = max(0, int(np.floor(top))), min(h, int(np.ceil(bottom)))
        delta = abs(image[top:bottom, left:right].astype(float)-rendered[top:bottom, left:right])
        regions[name] = float(np.percentile(delta, 95)) if delta.size else float('inf')
    left, right = int(np.ceil(A))+2, int(np.floor(X-rx))-1
    top, bottom = int(np.ceil(y+ry))+1, int(np.floor(Y-ry))-1
    if right <= left or bottom <= top:
        return dict(passed=False, regions=regions)
    profile = np.median(image[top:bottom, left:right], axis=1)
    other = np.median(rendered[top:bottom, left:right], axis=1)
    regions['exposed_gradient'] = float(np.percentile(abs(profile.astype(float)-other), 95))
    white = image[int(np.ceil(b+v))+1:int(np.floor(B-v))-1,
                  int(np.ceil(a+u))+1:int(np.floor(A))-1]
    white_error = float(np.max(abs(white.astype(float)-255))) if white.size else float('inf')
    maximum_error = float(np.max(abs(image.astype(float)-rendered)))
    return dict(passed=bool(max(regions.values()) <= 12 and regions['exposed_gradient'] <= 3
                           and white_error <= 16 and maximum_error <= 32),
                regions=regions, white_error=white_error, maximum_error=maximum_error)


def fit_inset_panel(width, height, *, description, image, render_fn, error_fn):
    arr = np.asarray(image)
    session = current_search()
    if (not inset_panel_contract(description) or arr.shape != (height, width, 3)
            or min(width, height) < 12 or not np.isfinite(arr).all()
            or (session and session.time_reason())):
        return None
    pixels = arr.astype(float)
    yy, xx = np.nonzero(pixels.min(axis=2) < 240)
    if len(xx) < 60:
        return None
    x, y, X, Y = map(float, (xx.min(), yy.min(), xx.max()+1, yy.max()+1))
    if X-x < 3*(Y-y) or Y-y < 12 or np.percentile(np.ptp(pixels, axis=2), 99) > 12:
        return None
    # The largest enclosed white island supplies the inset, rather than the
    # surrounding canvas. JPEG ringing may puncture it but does not add shapes.
    white = (pixels.min(axis=2) > 245).astype(np.uint8)
    _, _, stats, _ = cv2.connectedComponentsWithStats(white)
    candidates = [s for s in stats[1:] if s[4] > (X-x)*(Y-y)*.3
                  and s[0] > x and s[1] > y and s[0]+s[2] < X and s[1]+s[3] < Y]
    if not candidates:
        return None
    a, b, iw, ih, _ = max(candidates, key=lambda s: s[4]).astype(float)
    A, B = a+iw, b+ih
    rx, ry = min(4., (Y-y)*.16), min(4., (Y-y)*.16)
    left, right = int(A)+2, int(X-rx)-1
    if right-left < 3:
        return None
    rows = np.arange(int(y)+2, int(Y)-2)
    profile = np.median(pixels[rows, left:right], axis=1)
    t = (rows+.5-y)/(Y-y)
    basis = np.column_stack((1-t, t))
    colors = np.linalg.lstsq(basis, profile, rcond=None)[0]
    if colors[0].mean() < colors[1].mean()+2:
        return None
    parameters = np.r_[x, y, X, Y, rx, ry, a, b, A, B, rx*.7, ry*.7, np.clip(colors, 0, 255).ravel()]

    def valid(p):
        x, y, X, Y, rx, ry, a, b, A, B, u, v = p[:12]
        return bool(np.isfinite(p).all() and -1 <= x < a < A < X <= width+1
            and -1 <= y < b < B < Y <= height+1 and X-x > 3*(Y-y)
            and .75 < (A-x)/(X-x) < .96
            and 0 < a-x < .25*(Y-y) and 0 < b-y < .25*(Y-y) and 0 < Y-B < .25*(Y-y)
            and .5 <= rx <= (X-x)/2 and .5 <= ry <= (Y-y)/2
            and .5 <= u <= (A-a)/2 and .5 <= v <= (B-b)/2
            and min(X-A-rx, Y-y-2*ry) > 3
            and np.all((p[12:] >= 0) & (p[12:] <= 255))
            and np.ptp(p[12:15]) <= 12 and np.ptp(p[15:18]) <= 12
            and p[12:15].mean() >= p[15:18].mean()+2)

    def build(p):
        x, y, X, Y, rx, ry, a, b, A, B, u, v = p[:12]
        # Only the two left corners are elliptical; the right edge is vertical.
        path = (f'M {a+u:.6f} {b:.6f} H {A:.6f} V {B:.6f} H {a+u:.6f} '
                f'A {u:.6f} {v:.6f} 0 0 1 {a:.6f} {B-v:.6f} V {b+v:.6f} '
                f'A {u:.6f} {v:.6f} 0 0 1 {a+u:.6f} {b:.6f} Z')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<defs><linearGradient id="insetBackground" gradientUnits="userSpaceOnUse" '
            f'x1="0" x2="0" y1="{y:.6f}" y2="{Y:.6f}">'
            f'<stop offset="0" stop-color="{_hex(p[12:15])}"/>'
            f'<stop offset="1" stop-color="{_hex(p[15:18])}"/></linearGradient></defs>'
            f'<rect x="{x:.6f}" y="{y:.6f}" width="{X-x:.6f}" height="{Y-y:.6f}" '
            f'rx="{rx:.6f}" ry="{ry:.6f}" fill="url(#insetBackground)" stroke="none"/>'
            f'<path d="{path}" fill="#ffffff" stroke="none"/></svg>')

    weights = np.ones((height, width, 1))
    corner = max(4, int(np.ceil(max(rx, ry)))+2)
    for cx, cy in ((x, y), (x, Y), (X, y), (X, Y), (a, b), (a, B)):
        weights[max(0, int(cy)-corner):min(height, int(cy)+corner),
                max(0, int(cx)-corner):min(width, int(cx)+corner)] = 6
    result = _register(parameters, 12, build, valid, arr, render_fn, error_fn, 'inset_panel',
        loss_fn=lambda source, raster: np.mean(weights*(source.astype(float)-raster)**2),
        satisfactory_fn=lambda p, measured: inset_details(arr, measured[3], p)['passed'])
    if result is None or (session and session.time_reason()):
        return None
    result['quality'] = pixel_quality(arr, result['rendered'])
    result['details'] = inset_details(arr, result['rendered'], result['parameters'])
    if not result['quality']['passed'] or not result['details']['passed']:
        return None
    return result
