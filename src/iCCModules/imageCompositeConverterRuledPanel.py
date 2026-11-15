"""Raster-derived alternatives for framed gradients with parallel straight marks.

Both paint axes are considered. Bounds, marks and paint are measured afresh;
neither the incumbent's proportions nor catalogue names supply geometry.
"""
from __future__ import annotations

import random
import re

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register
from src.iCCModules.imageCompositeConverterSearchPortfolio import settings


def ruled_panel_candidates(image, render_fn, error_fn):
    pixels = np.asarray(image, dtype=float)
    h, w = pixels.shape[:2]
    session = current_search()
    if min(h, w) < 16 or max(h, w) > 512:
        return
    background = np.median(np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1])), axis=0)
    yy, xx = np.nonzero(np.max(abs(pixels-background), axis=2) > 25)
    if len(xx) < 60:
        return
    x, y, X, Y = int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)
    if min(X-x, Y-y) < 12:
        return
    # Use the darker sample of each two-pixel edge band: subpixel translation
    # distributes a thin rim across adjacent pixels, including the inner one.
    edges = [pixels[y:y+2, x:X].min(axis=0), pixels[Y-2:Y, x:X].min(axis=0),
             pixels[y:Y, x:x+2].min(axis=1), pixels[y:Y, X-2:X].min(axis=1)]
    core = pixels[y+3:Y-3, x+3:X-3]
    # A subpixel-translated one-pixel rim can be split across two pale pixels
    # on one side. Three independently dark sides still establish a rectangle;
    # the full rendered comparison must confirm the fourth edge afterwards.
    if not core.size or sum(np.median(edge.mean(axis=1)) <= np.median(core.mean(axis=2))-15 for edge in edges) < 3:
        return
    rim = np.median(np.concatenate(edges), axis=0)
    # A seed changes which alternative gets the first part of a finite budget.
    axes = [0, 1]
    random.Random((settings() or {}).get('seed', 0)).shuffle(axes)
    for axis in axes:
        if session and session.time_reason():
            return
        # Canonical coordinates: gradient along x, marks along x. Transposition
        # also tests vertical gradients with vertical marks without new logic.
        a = pixels if axis == 0 else pixels.transpose(1, 0, 2)
        left, top, right, bottom = (x, y, X, Y) if axis == 0 else (y, x, Y, X)
        inner = a[top+3:bottom-3, left+3:right-3]
        profile = np.median(inner, axis=0)
        if np.ptp(profile.mean(axis=1)) < 12:
            continue
        residual = profile[None, :, :].mean(axis=2)-inner.mean(axis=2)
        mask = (residual > 25).astype(np.uint8)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
        bars = []
        explained = np.zeros(mask.shape, dtype=bool)
        for label in range(1, count):
            bx, by, bw, bh, area = stats[label]
            if bw < max(5, (right-left)*.2) or bw < 3*bh or area < bw*bh*.65:
                continue
            color = np.median(inner[labels == label], axis=0)
            delta = np.maximum(1., profile[bx:bx+bw].mean(axis=1)-color.mean())
            alpha = np.clip(residual[by:by+bh, bx:bx+bw]/delta[None, :], 0, 1)
            thickness = float(alpha.sum()/bw)
            weights = alpha.sum(axis=1)
            center = float(np.average(np.arange(by, by+bh)+.5, weights=weights))
            bars.append([left+3+bx, left+3+bx+bw, top+3+center, thickness, color])
            explained[max(0, by-1):by+bh+1, max(0, bx-1):bx+bw+1] = True
        if not 1 <= len(bars) <= 8 or np.count_nonzero(mask & ~explained) > max(3, mask.size*.005):
            continue
        positions = np.arange(len(profile))+left+3.5
        lo, hi = left+.5, right-.5
        models = []
        for peak in np.linspace(positions[0]+1, positions[-1]-1, 33):
            basis = np.column_stack([np.interp(positions, [lo, peak, hi], np.eye(3)[i]) for i in range(3)])
            palette = np.linalg.lstsq(basis, profile, rcond=None)[0]
            models.append((np.square(basis@palette-profile).mean(), peak, np.clip(palette, 0, 255)))
        _, peak, palette = min(models, key=lambda m: m[0])
        bars.sort(key=lambda b: b[2])
        geometry = 6+4*len(bars)
        seed = np.r_[lo, top+.5, hi, bottom-.5, 1., peak,
                     np.array([b[:4] for b in bars]).ravel(), palette.ravel(), rim,
                     np.median([b[4] for b in bars], axis=0), background]

        def build(p):
            l, t, r, b, sw, peak = p[:6]
            colors = p[geometry:].reshape(-1, 3)
            coords = (f'x1="{l:.5f}" x2="{r:.5f}" y1="0" y2="0"' if axis == 0 else
                      f'y1="{l:.5f}" y2="{r:.5f}" x1="0" x2="0"')
            stops = ''.join(f'<stop offset="{offset:.7f}" stop-color="{_hex(color)}"/>'
                            for offset, color in zip((0., (peak-l)/(r-l), 1.), colors[:3]))
            rx, ry, rw, rh = (l, t, r-l, b-t) if axis == 0 else (t, l, b-t, r-l)
            lines = ''
            for start, end, center, thickness in p[6:geometry].reshape(-1, 4):
                coords_line = (start, center, end, center) if axis == 0 else (center, start, center, end)
                lines += ('<line '+ ' '.join(f'{key}="{value:.5f}"' for key, value in
                           zip(('x1', 'y1', 'x2', 'y2'), coords_line))+
                          f' stroke="{_hex(colors[4])}" stroke-width="{thickness:.5f}"/>')
            return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
                    f'<defs><linearGradient id="ruledPaint" gradientUnits="userSpaceOnUse" {coords}>{stops}</linearGradient></defs>'
                    f'<rect width="{w}" height="{h}" fill="{_hex(colors[5])}"/>'
                    f'<rect x="{rx:.5f}" y="{ry:.5f}" width="{rw:.5f}" height="{rh:.5f}" '
                    f'fill="url(#ruledPaint)" stroke="{_hex(colors[3])}" stroke-width="{sw:.5f}"/>{lines}</svg>')

        def valid(p):
            if not (np.isfinite(p).all() and np.all(abs(p[:4]-seed[:4]) <= 2)
                    and .25 <= p[4] <= 3 and p[0]+2 < p[5] < p[2]-2
                    and np.all((0 <= p[geometry:]) & (p[geometry:] <= 255))):
                return False
            return all(p[0] < start < end < p[2] and p[1] < center < p[3] and .4 <= thickness <= 6
                       for start, end, center, thickness in p[6:geometry].reshape(-1, 4))

        result = _register(seed, geometry, build, valid, image, render_fn, error_fn,
                           'raster_ruled_panel_'+str(axis), allow_portfolio=False,
                           satisfactory_fn=lambda p, m: True)
        if result:
            result['gradient_axis'] = axis
            result['mark_count'] = len(bars)
            yield result


def fit_ruled_panel(width, height, *, description, image, render_fn, error_fn):
    # This complete model has a deliberately narrow language contract. The
    # generic fallback may still compare it as an unconfirmed raster proposal.
    text = str(description).casefold()
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or np.percentile(np.ptp(arr.astype(float), axis=2), 95) > 12:
        return None
    if not ('rechteck' in text and 'grau' in text and 'verlauf' in text
            and any(word in text for word in ('linien', 'balken', 'striche'))
            and not any(word in text for word in ('diagonal', 'kreuz', 'plus', 'minus', 'kreis', 'schrift', 'pfeil'))):
        return None
    if re.search(r'\b(?:ohne|keine?)\b', text):
        return None
    mark_axis = 1 if re.search(r'(?:vertikale|senkrechte)\s+(?:linien|balken|striche)', text) else 0
    gradient_axis = (1 if re.search(r'(?:vertikaler|senkrechter)\s+farbverlauf', text) else
                     0 if re.search(r'(?:horizontaler|waagerechter)\s+farbverlauf', text) else None)
    counts = dict(eine=1, zwei=2, drei=3, vier=4, fünf=5, sechs=6, sieben=7, acht=8)
    count = re.search(r'\b(eine|zwei|drei|vier|fünf|sechs|sieben|acht|[1-8])\s+(?:graue\s+)?(?:horizontale\s+|vertikale\s+|waagerechte\s+|senkrechte\s+)?(?:linien|balken|striche)', text)
    expected = (int(count[1]) if count[1].isdigit() else counts[count[1]]) if count else None
    best = None
    for result in ruled_panel_candidates(image, render_fn, error_fn):
        if (result['gradient_axis'] != mark_axis or (gradient_axis is not None and gradient_axis != result['gradient_axis'])
                or (expected is not None and expected != result['mark_count'])):
            continue
        if pixel_quality(image, result['rendered'])['passed'] and (best is None or result['error'] < best['error']):
            best = result
    return best
