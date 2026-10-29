"""Fit a gray gradient panel with two symmetric slopes and two short bars.

Geometry and paint come from the uploaded raster. The model contains one
rectangle, four straight marks and a bounded gradient, never a reference SVG.
"""
from __future__ import annotations

import re

import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterFilledSymbols import _register


def paired_line_contract(description):
    text = re.sub(r'\s+', ' ', str(description or '').casefold())
    return (all(word in text for word in ('grau', 'rechteck', 'zwei', 'symmetr', 'horizontal', 'recht'))
            and any(word in text for word in ('schräg', 'diagonal'))
            and any(word in text for word in ('verlauf', 'abstufung'))
            and any(word in text for word in ('striche', 'balken'))
            and not any(word in text for word in ('kreis', 'text', 'beschrift', 'zusätzlich', 'ohne linien')))


def fit_paired_line_panel(width, height, *, description, image, render_fn, error_fn):
    if not paired_line_contract(description):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 16 or width < height:
        return None
    pixels = arr.astype(float)
    if np.percentile(np.ptp(pixels, axis=2), 95) > 12:
        return None
    gray = pixels.mean(axis=2)
    yy, xx = np.nonzero(gray < 235)
    if len(xx) < 50:
        return None
    x0, x1, y0, y1 = float(xx.min()), float(xx.max()+1), float(yy.min()), float(yy.max()+1)
    w, h = x1-x0, y1-y0
    if min(w, h) < 16:
        return None
    margin = max(2, int(round(min(w, h)*.05)))
    left, right = int(x0)+margin, int(x1)-margin
    top, bottom = int(y0)+margin, int(y1)-margin
    profile = np.median(gray[int(y0)+1:int(y1)-1, left:right], axis=1)
    if np.ptp(profile) < 12:
        return None
    deviation = np.interp(np.arange(height)+.5, np.arange(len(profile))+y0+1.5, profile)[:, None]-gray
    # Independently observe each slope over most of the panel width. The bars
    # are near the center, outside these two slope bands.
    columns = np.arange(left, right)
    upper_rows = np.arange(top, int(y0+h*.4))
    lower_rows = np.arange(int(y0+h*.6), bottom)
    if min(len(upper_rows), len(lower_rows)) < 3:
        return None
    slopes = []
    for rows in (upper_rows, lower_rows):
        values = deviation[np.ix_(rows, columns)]
        indices = values.argmax(axis=0)
        active = values[indices, np.arange(len(columns))] > 20
        if active.mean() < .8:
            return None
        ys, xs = rows[indices[active]]+.5, columns[active]+.5
        slope, intercept = np.polyfit(xs, ys, 1)
        if not .025 < abs(slope) < .6 or np.max(abs(ys-(slope*xs+intercept))) > max(1.2, h*.04):
            return None
        slopes.append((slope, intercept, xs, ys))
    upper, lower = slopes
    if upper[0] >= 0 or lower[0] <= 0:
        return None
    center = (y0+y1)/2
    if max(abs((upper[0]+lower[0])*columns+upper[1]+lower[1]-2*center)) > max(1.5, h*.05):
        return None
    # Two short, separated horizontal marks must be measured on the right.
    band_top, band_bottom = int(y0+h*.36), int(y0+h*.64)+1
    band_left, band_right = int(x0+w*.5), right
    mark = deviation[band_top:band_bottom, band_left:band_right] > 25
    import cv2
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mark.astype(np.uint8))
    bars = []
    for label in range(1, count):
        bx, by, bw, bh, area = stats[label]
        if bw >= w*.08 and bw >= 3*bh and area >= bw*.7:
            bars.append((band_left+bx, band_top+by, bw, bh))
    if len(bars) != 2:
        return None
    bars.sort(key=lambda b: b[1])
    a, b = bars
    if abs(a[0]-b[0]) > w*.05 or abs(a[2]-b[2]) > w*.05:
        return None
    # A low global error must not hide an additional dark object in the fill.
    grid_y, grid_x = np.mgrid[:height, :width]+.5
    explained = np.zeros(gray.shape, dtype=bool)
    for slope, intercept, _, _ in slopes:
        explained |= abs(grid_y-slope*grid_x-intercept) < max(1.6, h*.04)
    for bx, by, bw, bh in bars:
        explained |= ((grid_x >= bx-.5) & (grid_x <= bx+bw+.5)
                      & (grid_y >= by-.5) & (grid_y <= by+bh+.5))
    unexplained = ((deviation > 25) & ~explained)[top:bottom, left:right]
    count, _, stats, _ = cv2.connectedComponentsWithStats(unexplained.astype(np.uint8))
    if count > 1 and stats[1:, cv2.CC_STAT_AREA].max() >= 4:
        return None
    # At most nine continuous paint stops, independent of raster dimensions.
    knots = [0, len(profile)-1]
    while len(knots) < min(9, len(profile)):
        residual = abs(profile-np.interp(np.arange(len(profile)), knots, profile[knots]))
        residual[knots] = -1
        knots.append(int(np.argmax(residual)))
        knots.sort()
    offsets = np.array(knots)+y0+1.5
    rim = float(np.median(np.concatenate((gray[int(y0), int(x0):int(x1)],
                                         gray[int(y1)-1, int(x0):int(x1)]))))
    shades = [gray[int(y-.5), int(x-.5)] for line in slopes for x, y in zip(line[2], line[3])]
    shade = float(np.median(shades))
    # Bounds, rim, slope endpoints/width, bar bounds/positions/width, colors,
    # and the bounded gradient palette.
    p = [x0+.5, y0+.5, w-1, h-1, 1., upper[0]*x0+upper[1], upper[0]*x1+upper[1],
         1., (a[0]+b[0])/2, (a[0]+a[2]+b[0]+b[2])/2,
         a[1]+a[3]/2, b[1]+b[3]/2, (a[3]+b[3])/2, rim, shade, *profile[knots]]

    def valid(v):
        return (np.isfinite(v).all() and min(v[2:4]) > 8 and .2 <= v[4] <= h*.12
                and v[1] < v[6] < v[5] < center-1 and .2 <= v[7] <= h*.12
                and x0+w*.45 < v[8] < v[9] < x1 and v[9]-v[8] < w*.4
                and center-h*.2 < v[10] < v[11] < center+h*.2 and .2 <= v[12] < h*.1
                and np.all((v[13:] >= 0) & (v[13:] <= 255)))

    def color(value):
        return '#'+f'{int(np.clip(round(value), 0, 255)):02x}'*3

    def build(v):
        ox, oy, ow, oh, sw = v[:5]
        stops = ''.join(f'<stop offset="{t:.7g}" stop-color="{color(c)}"/>'
                        for t, c in zip((offsets-offsets[0])/(offsets[-1]-offsets[0]), v[15:]))
        lines = ''
        for reflect in (False, True):
            ay, by = (2*center-v[5], 2*center-v[6]) if reflect else v[5:7]
            lines += (f'<polyline points="{x0:.7g},{ay:.7g} {x1:.7g},{by:.7g}" '
                      f'fill="none" stroke="{color(v[14])}" stroke-width="{v[7]:.7g}"/>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="panelPaint" gradientUnits="userSpaceOnUse" x1="0" x2="0" '
                f'y1="{offsets[0]:.7g}" y2="{offsets[-1]:.7g}">{stops}</linearGradient></defs>'
                f'<rect x="{ox:.7g}" y="{oy:.7g}" width="{ow:.7g}" height="{oh:.7g}" '
                f'fill="url(#panelPaint)" stroke="{color(v[13])}" stroke-width="{sw:.7g}"/>'
                +lines+''.join(f'<path d="M {v[8]:.7g} {y:.7g} H {v[9]:.7g}" stroke="{color(v[14])}" '
                              f'stroke-width="{v[12]:.7g}"/>' for y in v[10:12])+'</svg>')

    result = _register(p, 13, build, valid, arr, render_fn, error_fn,
                       'raster_paired_line_panel_v1', satisfactory_fn=lambda p, m: True)
    return result if result and pixel_quality(arr, result['rendered'])['passed'] else None
