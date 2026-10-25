"""A single unoutlined rectangle with a bounded, continuous axial paint model.

Two endpoint colors are tried before a four-stop model with two free knots.
The model size is independent of raster resolution. No bands, traced paths,
catalog identities or reference vectors are used.
"""
from __future__ import annotations

from itertools import combinations
import re

import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex


def panel_contract(description):
    text = str(description or '').casefold().strip()
    extent = r'(?:geringfügig|etwas|ein wenig|leicht)'
    text = re.sub(r'\s+(?:das (?:gesamte )?motiv|die (?:gesamte )?darstellung) ist '+extent+
                  r' (?:grösser|kleiner) dargestellt und '+extent+
                  r' nach (?:links|rechts) und (?:oben|unten) (?:versetzt|verschoben)\.$', '', text)
    shape = r'ein einzelnes (?:(waagerechtes|senkrechtes), (?:sehr )?flaches )?rechteck ohne kontur\. '
    color = r'(rosa|blaue|grüne|graue|rote|violette|orange)'
    match = re.fullmatch(shape+r'die '+color+r' füllung hat einen (vertikalen|horizontalen) farbverlauf(?:: (.*))?\.', text)
    if not match:
        return None
    orientation, paint, axis, details = match.groups()
    # Descriptive light/dark zones are optional, but unknown objects, extra
    # relations or negations cannot silently disappear in this simple model.
    if details is not None and not re.fullmatch(
        r'oben gedämpftes rosa, darunter ein hellerer rosafarbener glanz, '
        r'im unteren bereich dunkleres altrosa und am unteren rand wieder ein kräftigeres rosa', details):
        return None
    return dict(axis=1 if axis == 'vertikalen' else 0, orientation=orientation,
                paint=paint, zones=details is not None)


def _palette_matches(pixels, paint):
    b, g, r = np.median(pixels.reshape(-1, 3), axis=0)
    return {
        'rosa': r > g+20 and r > b+15 and g > 70 and b > 70,
        'rote': r > g+30 and r > b+30,
        'blaue': b > r+20 and b > g+10,
        'grüne': g > r+15 and g > b+10,
        'graue': max(b, g, r)-min(b, g, r) < 12,
        'violette': b > g+15 and r > g+15,
        'orange': r > g+20 and g > b+20,
    }[paint]


def _zones_match(profile):
    """Require the claimed upper highlight, lower shadow and pink recovery.

    At five rows the highlight may be clipped into the first row. At larger
    resolutions it must have a separately observed interior maximum.
    """
    light = profile.mean(axis=1)
    if len(light) < 4 or light[:max(2, len(light)//2)].max() < light[len(light)//2:].min()+8:
        return False
    if len(light) >= 8 and light[:len(light)//2].max() < light[0]+1:
        return False
    saturation = profile[:, 2]-(profile[:, 0]+profile[:, 1])/2
    return saturation[-1] >= saturation[-2]+.5


def fit_axial_panel(width, height, *, description, image, render_fn, error_fn):
    contract = panel_contract(description)
    arr = np.asarray(image)
    if contract is None or arr.shape != (height, width, 3) or min(width, height) < 4:
        return None
    axis = contract['axis']
    pixels = arr.astype(float)
    mask = np.max(255-pixels, axis=2) > 20
    yy, xx = np.nonzero(mask)
    if len(xx) < 16:
        return None
    x0, x1, y0, y1 = int(xx.min()), int(xx.max())+1, int(yy.min()), int(yy.max())+1
    if min(x1-x0, y1-y0) < 4 or mask[y0:y1, x0:x1].mean() < .94:
        return None
    if contract['orientation'] == 'waagerechtes' and x1-x0 < 3*(y1-y0):
        return None
    if contract['orientation'] == 'senkrechtes' and y1-y0 < 3*(x1-x0):
        return None
    core = pixels[y0:y1, x0:x1]
    if not _palette_matches(core, contract['paint']):
        return None
    # Orthogonal variation means a mark, outline, multiple objects or a second
    # paint axis. Reject it before searching a plain rectangle hypothesis.
    profile = np.median(core, axis=axis)
    expanded = profile[:, None, :] if axis else profile[None, :, :]
    interior = abs(core-expanded)
    if np.percentile(interior[1:-1, 1:-1], 95) > 5 or np.ptp(profile, axis=0).max() < 8:
        return None
    if contract['zones']:
        if axis != 1 or not _zones_match(profile):
            return None

    # Side coverage can be inferred independently of the gradient along the
    # other axis, using all color channels and profile rows together.
    orthogonal = pixels[y0:y1, :] if axis else pixels[:, x0:x1].transpose(1, 0, 2)
    reference = 255-profile
    coverage = np.einsum('ijk,ik->j', 255-orthogonal, reference) / max(1., np.sum(reference**2))
    left, right = (x0, x1) if axis else (y0, y1)
    a = left+1-min(1., max(0., coverage[left]))
    b = right-1+min(1., max(0., coverage[right-1]))
    if axis:
        x0, x1 = a, b
    else:
        y0, y1 = a, b
    low, high = (y0, y1) if axis else (x0, x1)
    t = (np.arange(len(profile))+.5)/len(profile)
    session = current_search()
    evaluations, attempts = 0, []

    def build(knots, colors):
        stops = ''.join(f'<stop offset="{offset:.8g}" stop-color="{_hex(rgb)}"/>'
                        for offset, rgb in zip(knots, colors))
        coords = f'x1="0" x2="0" y1="{low:.8g}" y2="{high:.8g}"' if axis else (
                 f'y1="0" y2="0" x1="{low:.8g}" x2="{high:.8g}"')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="axialPaint" gradientUnits="userSpaceOnUse" {coords}>{stops}</linearGradient></defs>'
                f'<rect x="{x0:.8g}" y="{y0:.8g}" width="{x1-x0:.8g}" height="{y1-y0:.8g}" '
                'fill="url(#axialPaint)" stroke="none"/></svg>')

    first_error = None
    for count in (2, 4):
        if session and session.time_reason():
            break
        models = []
        pairs = [()] if count == 2 else combinations(np.linspace(.1, .9, 9), 2)
        for pair in pairs:
            knots = np.array([0., *pair, 1.])
            basis = np.column_stack([np.interp(t, knots, np.eye(count)[i]) for i in range(count)])
            colors = np.linalg.lstsq(basis, profile, rcond=None)[0]
            if np.any(colors < 0) or np.any(colors > 255):
                continue
            score = float(np.mean((basis @ colors-profile)**2))
            models.append((score, knots, colors))
        # Only the best distinct bounded paint hypotheses need actual renders.
        for _, knots, colors in sorted(models, key=lambda item: item[0])[:4]:
            if session and session.time_reason():
                break
            svg = build(knots, colors)
            rendered = render_fn(svg, width, height)
            evaluations += 1
            if session:
                session.evaluations += 1
            if rendered is None:
                continue
            error = float(error_fn(arr, rendered))
            if first_error is None:
                first_error = error
            quality = pixel_quality(arr, rendered)
            rendered_core = rendered[int(yy.min()):int(yy.max())+1, int(xx.min()):int(xx.max())+1]
            semantic_pass = bool(_palette_matches(rendered_core, contract['paint']) and
                                 (not contract['zones'] or _zones_match(np.median(rendered_core, axis=axis))))
            attempts.append(dict(stops=count, error=error, passed=quality['passed'] and semantic_pass))
            if quality['passed'] and semantic_pass:
                return dict(svg=svg, rendered=rendered, error=error, initial_error=first_error,
                            source='axial_panel', evaluations=evaluations, hypotheses=attempts,
                            parameters=dict(bounds=list(map(float, [x0, y0, x1, y1])),
                                            knots=knots.tolist(), colors=colors.tolist()))
    return None
