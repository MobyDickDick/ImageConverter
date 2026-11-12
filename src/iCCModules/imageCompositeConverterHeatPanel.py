"""Register framed gray heat panels from observed lines and glyph components."""
from __future__ import annotations

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality
from src.iCCModules.imageCompositeConverterFilledSymbols import _register


def fit_heat_panel(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not (all(token in text for token in ('rechteck', 'verlauf', 'diagon', 'plus'))
            and any(token in text for token in ('grau', 'gray', 'grey'))):
        return None
    if any(token in text for token in ('kreis', 'punkt', 'text', 'zwei diagon', 'beide diagon', 'gedreht')):
        return None
    session = current_search()
    if session and session.time_reason():
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 16:
        return None
    pixels = arr.astype(float)
    if not np.isfinite(pixels).all() or np.percentile(np.ptp(pixels, axis=2), 95) > 12:
        return None
    gray = pixels.mean(axis=2)
    visible = gray < 235
    rows = np.flatnonzero(visible.sum(axis=1) > width*.5)
    cols = np.flatnonzero(visible.sum(axis=0) > height*.5)
    if not len(rows) or not len(cols):
        return None
    x0, x1 = cols[0]+.5, cols[-1]+.5
    y0, y1 = rows[0]+.5, rows[-1]+.5
    w, h = x1-x0, y1-y0
    if min(w, h) < 12:
        return None
    inset = max(2, int(round(min(w, h)*.06)))
    left, right = int(x0)+inset, int(x1)-inset+1
    top, bottom = int(y0)+inset, int(y1)-inset+1
    if min(right-left, bottom-top) < 8:
        return None
    profile = np.median(gray[top:bottom, left:right], axis=0)
    if np.ptp(profile) < 15:
        return None
    # The long diagonal and small glyphs occupy a minority of each column.
    background = np.interp(np.arange(width)+.5, np.arange(left, right)+.5, profile)
    deviation = background[None, :]-gray
    mask = np.zeros(gray.shape, np.uint8)
    mask[top:bottom, left:right] = deviation[top:bottom, left:right] > 28
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    diagonal = [i for i in range(1, count)
                if stats[i, cv2.CC_STAT_HEIGHT] > h*.6 and stats[i, cv2.CC_STAT_WIDTH] > w*.6]
    if len(diagonal) != 1:
        return None
    dy, dx = np.nonzero(labels == diagonal[0])
    ys = np.unique(dy)
    centers = np.array([np.median(dx[dy == y])+.5 for y in ys])
    slope, intercept = np.polyfit(ys+.5, centers, 1)
    descending = 'oben links' in text and 'unten rechts' in text and 'oben rechts' not in text
    if (slope > 0) != descending or np.max(abs(centers-(slope*(ys+.5)+intercept))) > max(1.5, w*.04):
        return None
    marks = []
    for label in range(1, count):
        if label == diagonal[0] or stats[label, cv2.CC_STAT_AREA] < 3:
            continue
        bx, by, bw, bh, area = stats[label]
        if by+bh > y0+h*.35 or bx+bw > x0+w*.65:
            return None
        marks.append((label, bx, by, bw, bh, area))
    # Observe the horizontal and vertical arms independently. Bright gradient
    # highlights are never used as a glyph location, and an absent minus cannot
    # be fabricated from the ambiguous family term "Plus-Minus-Zeichen".
    plus = []
    minus = []
    for label, bx, by, bw, bh, area in marks:
        component = labels[by:by+bh, bx:bx+bw] == label
        if min(bw, bh) >= 3 and .5 < bw/bh < 2:
            row_counts, col_counts = component.sum(axis=1), component.sum(axis=0)
            ry = float(np.flatnonzero(row_counts == row_counts.max()).mean())
            rx = float(np.flatnonzero(col_counts == col_counts.max()).mean())
            if row_counts.max() >= bw*.75 and col_counts.max() >= bh*.75:
                plus.append((bx, by, bw, bh, rx, ry, label))
                continue
        if bw >= 3*bh and bw >= w*.08:
            minus.append((bx, by, bw, bh, label))
        else:
            return None
    if len(plus) != 1 or len(minus) > 1 or (minus and 'minus' not in text):
        return None
    if not minus and ('und minus' in text or 'plus und' in text):
        return None
    bx, by, bw, bh, rx, ry, label = plus[0]
    cx, cy = bx+rx+.5, by+ry+.5
    halfx, halfy = (bw-1)/2, (bh-1)/2
    glyph_width = float(np.median([np.count_nonzero(labels[by:by+bh, bx] == label),
                                  np.count_nonzero(labels[by, bx:bx+bw] == label)]))
    line_width = len(dx)/(np.ptp(ys)*np.hypot(1, slope))
    # Pixel support describes the outside of a thick frame, not its centerline.
    # Measure all four rim cores so larger inputs do not inherit a one-pixel rim.
    horizontal = np.median(gray[:, int(x0+w*.25):int(x0+w*.75)], axis=1)
    vertical = np.median(gray[int(y0+h*.35):int(y0+h*.65), :], axis=0)
    rim_colors, rim_widths, bounds = [], [], []
    for axis, start, end in ((vertical, x0, x0+inset), (vertical, x1-inset, x1+1),
                             (horizontal, y0, y0+inset), (horizontal, y1-inset, y1+1)):
        indices = np.arange(int(start), min(len(axis), int(end)+1))
        core = indices[axis[indices] <= axis[indices].min()+20]
        bounds.append(float((core+.5).mean()))
        rim_colors.extend(axis[core])
        rim_widths.append(len(core))
    frame_x0, frame_x1, frame_y0, frame_y1 = bounds
    # A fixed five-stop analytic gradient allows a central highlight plateau;
    # the palette size stays independent of the raster resolution.
    knots = np.linspace(0, len(profile)-1, 5)
    shades = np.interp(knots, np.arange(len(profile)), profile)
    p = [frame_x0, frame_y0, frame_x1, frame_y1, float(np.median(rim_widths)),
         slope*frame_y0+intercept, slope*frame_y1+intercept, line_width,
         cx, cy, max(1., halfx), max(1., halfy), max(.7, glyph_width)]
    if minus:
        mx, my, mw, mh, _ = minus[0]
        p.extend([mx+.5, mx+mw-.5, my+mh/2, float(mh)])
    geometry_count = len(p)
    p.extend([float(np.median(rim_colors)), float(np.percentile(gray[labels == diagonal[0]], 20)),
              float(np.percentile(gray[labels == label], 20)), *shades])

    def color(value):
        return '#'+f'{int(np.clip(round(value), 0, 255)):02x}'*3

    def valid(v):
        return (np.isfinite(v).all() and v[2]-v[0] > w*.8 and v[3]-v[1] > h*.8
                and abs(v[0]-x0) < inset and abs(v[2]-x1) < inset
                and abs(v[1]-y0) < inset and abs(v[3]-y1) < inset
                and .2 <= v[4] <= inset and .3 <= v[7] <= min(w, h)*.15
                and abs(v[5]-(slope*y0+intercept)) < inset
                and abs(v[6]-(slope*y1+intercept)) < inset
                and abs(v[8]-cx) < max(1., bw*.2) and abs(v[9]-cy) < max(1., bh*.2)
                and .6 <= v[10]/max(1., halfx) <= 1.4 and .6 <= v[11]/max(1., halfy) <= 1.4
                and .4 <= v[12] <= min(bw, bh)*.5
                and (not minus or (v[13] < v[14] and .3 <= v[16] <= max(2., minus[0][3]*2)
                                   and abs(v[13]-(mx+.5)) < max(1., mw*.2)
                                   and abs(v[14]-(mx+mw-.5)) < max(1., mw*.2)
                                   and abs(v[15]-(my+mh/2)) < max(1., mh)))
                and np.all((v[geometry_count:] >= 0) & (v[geometry_count:] <= 255)))

    def build(v):
        rim_color, line_color, glyph_color = map(color, v[geometry_count:geometry_count+3])
        stops = ''.join(f'<stop offset="{t:.5f}" stop-color="{color(c)}"/>'
                        for t, c in zip(np.linspace(0, 1, 5), v[geometry_count+3:]))
        glyph = (f'<path d="M {v[8]-v[10]:.5f} {v[9]:.5f} H {v[8]+v[10]:.5f} '
                 f'M {v[8]:.5f} {v[9]-v[11]:.5f} V {v[9]+v[11]:.5f}" '
                 f'fill="none" stroke="{glyph_color}" stroke-width="{v[12]:.5f}"/>')
        if minus:
            glyph += (f'<path d="M {v[13]:.5f} {v[15]:.5f} H {v[14]:.5f}" '
                      f'stroke="{glyph_color}" stroke-width="{v[16]:.5f}"/>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="heatPaint" gradientUnits="userSpaceOnUse" '
                f'x1="{left+.5}" x2="{right-.5}" y1="0" y2="0">{stops}</linearGradient>'
                f'<clipPath id="heatClip"><rect x="{v[0]:.5f}" y="{v[1]:.5f}" '
                f'width="{v[2]-v[0]:.5f}" height="{v[3]-v[1]:.5f}"/></clipPath></defs>'
                f'<rect width="{width}" height="{height}" fill="white"/>'
                f'<rect x="{v[0]:.5f}" y="{v[1]:.5f}" width="{v[2]-v[0]:.5f}" height="{v[3]-v[1]:.5f}" '
                f'fill="url(#heatPaint)" stroke="{rim_color}" stroke-width="{v[4]:.5f}"/>'
                f'<line x1="{v[5]:.5f}" y1="{v[1]:.5f}" x2="{v[6]:.5f}" y2="{v[3]:.5f}" '
                f'stroke="{line_color}" stroke-width="{v[7]:.5f}" clip-path="url(#heatClip)"/>'
                +glyph+'</svg>')

    result = _register(p, geometry_count, build, valid, arr, render_fn, error_fn,
                       'raster_heat_panel_v1', satisfactory_fn=lambda p, m: True)
    if result is None or not pixel_quality(arr, result['rendered'])['passed']:
        return None
    result['observed_glyphs'] = ['plus', 'minus'] if minus else ['plus']
    return result
