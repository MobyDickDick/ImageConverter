"""Register a framed grey panel with a bounded, continuous axial gradient.

Four paint stops describe the highlight independently of raster resolution.
Neither catalogue identities nor saved vectors participate in registration.
"""
from __future__ import annotations

from itertools import combinations
import re

import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register
from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description


def panel_contract(description):
    original = str(description or '').casefold()
    text = re.sub(r'\s+', ' ', normalize_description(description).casefold()
                  .replace('weiß', 'weiss').replace('graustufenverlauf', 'farbverlauf')).strip()
    # Plan-B wording describes a whole-motif transform, not another object.
    text = re.sub(r' (?:das gesamte motiv|das motiv|die gesamte darstellung|die darstellung) ist '
                  r'(?:geringfügig|etwas|ein wenig|leicht) (?:kleiner|größer) dargestellt und '
                  r'(?:leicht|geringfügig|ein wenig|etwas) nach (?:links|rechts) und (?:oben|unten) '
                  r'(?:versetzt|verschoben)\.$', '', text)
    match = re.fullmatch(
        r'(liegendes|stehendes) rechteck mit farbverlauf in (vertikaler|horizontaler) '
        r'richtung und dunkelgrauer umrandung\. der farbverlauf ist von '
        r'(oben nach unten|links nach rechts) grau / fast weiss / fast weiss / grau\.'
        r'(?: die zwei fast-weissen bereiche deuten auf ein kleines helles, horizontales band hin; '
        r'der helle bereich liegt oberhalb der mitte\.)?', text.strip())
    if match:
        orientation, direction, order = match.groups()
        axis = 1 if direction == 'vertikaler' else 0
        if (order == 'oben nach unten') != bool(axis) or ('oberhalb' in text and not axis):
            return None
        return dict(axis=axis, orientation=orientation, upper='oberhalb' in text)
    # Free grey-gradient prose supplies the axis and highlight relationship;
    # bounds, paint, stops and stroke still come exclusively from raster data.
    if (not re.search(r'grau', original) or 'farbverlauf' not in text
            or not re.search(r'hell(?:igkeit|ste|e[rsn]? (?:bereich|band))', text)
            or not re.search(r'rand|rahmen', text)
            or re.search(r'kreis|dreieck|pfeil|beschrift|schrift|text|punkt|linie|diagonal|streifen|'
                         r'plus|minus|griff|anschl|muster|oval|ohne (?:farb)?verlauf|kein (?:farb)?verlauf', text)):
        return None
    axes = set()
    for words, axis in ((r'vertikal\w*|senkrecht\w*', 1), (r'horizontal\w*|waagerecht\w*', 0)):
        if re.search(rf'(?:{words}) farbverlauf|farbverlauf in (?:{words})', text):
            axes.add(axis)
    if len(axes) != 1:
        return None
    orientation = 'liegendes' if 'liegend' in text else 'stehendes' if 'stehend' in text else None
    axis = axes.pop()
    return dict(axis=axis, orientation=orientation,
                upper=bool(re.search(r'oberhalb|oberen (?:bild)?rand', text)) if axis else False,
                lower=bool(re.search(r'unterhalb|unteren (?:bild)?rand', text)) if axis else False)


def profile_quality(reference, rendered, axis, bounds, inset=1):
    """Check the light band locally; broad whole-image gates can hide its loss."""
    x, y, X, Y = bounds
    margin = max(2, int((X-x if axis else Y-y)*.2))
    a = reference[y+inset:Y-inset, x+margin:X-margin] if axis else reference[y+margin:Y-margin, x+inset:X-inset]
    b = rendered[y+inset:Y-inset, x+margin:X-margin] if axis else rendered[y+margin:Y-margin, x+inset:X-inset]
    p, q = np.median(a, axis=axis), np.median(b, axis=axis)
    error = float(np.percentile(abs(p.astype(float)-q.astype(float)), 95))
    peak_error = float(abs(p.mean(axis=1).max()-q.mean(axis=1).max()))
    return dict(profile_error_p95=error, highlight_error=peak_error,
                passed=bool(error <= 4 and peak_error <= 3))


def fit_framed_panel(width, height, *, description, image, render_fn, error_fn):
    contract = panel_contract(description)
    arr = np.asarray(image)
    if contract is None or arr.shape != (height, width, 3) or min(width, height) < 12:
        return None
    pixels = arr.astype(float)
    if not np.isfinite(pixels).all():
        return None
    session = current_search()
    if session and session.time_reason():
        return None
    axis = contract['axis']
    yy, xx = np.nonzero(pixels.min(axis=2) < 235)
    if len(xx) < 60:
        return None
    x, y, X, Y = int(xx.min()), int(yy.min()), int(xx.max())+1, int(yy.max())+1
    if min(X-x, Y-y) < 12 or (contract['orientation'] is not None and
                            ((X-x > Y-y) != (contract['orientation'] == 'liegendes'))):
        return None
    bounds = (x, y, X, Y)
    margin = max(2, int((X-x if axis else Y-y)*.2))
    cross = (np.median(pixels[y+(Y-y)//4:Y-(Y-y)//4, x:X], axis=0) if axis else
             np.median(pixels[y:Y, x+(X-x)//4:X-(X-x)//4], axis=1)).mean(axis=1)
    threshold = (np.median(cross[len(cross)//4:-len(cross)//4])+min(cross[0], cross[-1]))/2
    dark = cross < threshold
    leading = int(np.argmax(~dark)) if (~dark).any() else len(cross)
    trailing = int(np.argmax(~dark[::-1])) if (~dark).any() else len(cross)
    stroke_width = float(max(1, min(leading, trailing)))
    inset = int(np.ceil(stroke_width))
    # A partially covered contour pixel can look like a fifth gradient stop.
    # Fit paint only beyond its antialiasing transition; keep the existing
    # independent profile and pixel gates on the wider original region.
    sample_inset = max(2, inset+1)
    if sample_inset*2 >= min(X-x, Y-y)-4:
        return None
    core = (pixels[y+sample_inset:Y-sample_inset, x+margin:X-margin] if axis else
            pixels[y+margin:Y-margin, x+sample_inset:X-sample_inset])
    profile = np.median(core, axis=axis)
    expanded = profile[:, None, :] if axis else profile[None, :, :]
    # Marks, a second paint axis and coloured panels are outside this model.
    if np.percentile(abs(core-expanded), 95) > 6 or np.max(np.ptp(core, axis=2)) > 12:
        return None
    light = profile.mean(axis=1)
    peak = int(np.argmax(light))
    if min(light.max()-light[0], light.max()-light[-1]) < 12:
        return None
    if contract['upper'] and peak >= len(light)/2:
        return None
    if contract.get('lower') and peak < len(light)/2:
        return None
    border = np.concatenate((pixels[y, x:X], pixels[Y-1, x:X], pixels[y:Y, x], pixels[y:Y, X-1]))
    # Clipped sides expose the fill or white padding rather than the contour.
    # Seed the contour from the dark observed tail instead of requiring every
    # pixel on the raster bounding box to have the same paint.
    stroke = np.percentile(border, 10, axis=0)
    if light.max()-stroke.mean() < 20:
        return None

    half = stroke_width/2
    geometry = np.array([x+half, y+half, X-half, Y-half])
    low, high = (geometry[1], geometry[3]) if axis else (geometry[0], geometry[2])
    positions = np.arange(len(profile))+(y if axis else x)+sample_inset+.5
    # Fit endpoint colours and two free highlight knots to observed interiors.
    # Only a fixed-size analytic model is emitted, never one stop per row.
    models = []
    for a, b in combinations(np.linspace(low+1, high-1, 25), 2):
        knots = np.array([low, a, b, high])
        basis = np.column_stack([np.interp(positions, knots, np.eye(4)[i]) for i in range(4)])
        colors = np.linalg.lstsq(basis, profile, rcond=None)[0]
        if colors.min() < 0 or colors.max() > 255:
            continue
        models.append((float(np.mean((basis@colors-profile)**2)), a, b, colors))
    if not models:
        return None
    _, a, b, colors = min(models, key=lambda m: m[0])
    parameters = np.r_[geometry, stroke_width, a, b, colors.ravel(), stroke]

    def build(p):
        left, top, right, bottom, sw, a, b = p[:7]
        lo, hi = (top, bottom) if axis else (left, right)
        coords = f'x1="0" x2="0" y1="{lo:.5f}" y2="{hi:.5f}"' if axis else (
                 f'y1="0" y2="0" x1="{lo:.5f}" x2="{hi:.5f}"')
        stops = ''.join(f'<stop offset="{(k-lo)/(hi-lo):.7f}" stop-color="{_hex(c)}"/>'
                        for k, c in zip([lo, a, b, hi], p[7:19].reshape(4, 3)))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="panelPaint" gradientUnits="userSpaceOnUse" {coords}>{stops}</linearGradient></defs>'
                f'<rect x="{left:.5f}" y="{top:.5f}" width="{right-left:.5f}" height="{bottom-top:.5f}" '
                f'fill="url(#panelPaint)" stroke="{_hex(p[19:22])}" stroke-width="{sw:.5f}"/></svg>')

    def valid(p):
        left, top, right, bottom, sw, a, b = p[:7]
        lo, hi = (top, bottom) if axis else (left, right)
        return (np.all(abs(p[:4]-geometry) <= max(2., min(width, height)*.12))
                and right-left >= 8 and bottom-top >= 8
                and .5 <= sw <= max(2, stroke_width*1.5) and lo < a < b < hi
                and np.all((0 <= p[7:]) & (p[7:] <= 255)))

    result = _register(parameters, 7, build, valid, arr, render_fn, error_fn, 'framed_axial_panel',
        preserve_initial_error=True, satisfactory_fn=lambda p, m:
            profile_quality(arr, m[3], axis, bounds, inset)['passed'] and m[0] <= 4)
    if result is None:
        return None
    quality = profile_quality(arr, result['rendered'], axis, bounds, inset)
    if not quality['passed'] or not pixel_quality(arr, result['rendered'])['passed']:
        return None
    result['profile_quality'] = quality
    return result
