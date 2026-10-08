"""Observe three joined triangular wings and a crossed square actuator.

The input raster supplies every coordinate and color. Description constraints
select the topology; bounded render comparisons register its native primitives.
"""
from __future__ import annotations

import cv2
import numpy as np


def fit_three_way_valve(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold().replace('-', ' ')
    if not (('3 wege ventil' in text or 'drei' in text and 'ventil' in text)
            and all(token in text for token in ('oben', 'griff', 'unten', 'quadrat', 'diagonalen'))):
        return None
    if any(token in text for token in ('90°', '180°', 'zusätzlich', 'vier flügel', 'beschriftung m')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 16:
        return None
    pixels = arr.astype(float)
    background = np.median(np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1])), axis=0)
    mask = np.max(abs(pixels-background), axis=2) > 35
    spans = np.zeros(height)
    for row in range(height):
        cols = np.flatnonzero(mask[row])
        if len(cols):
            spans[row] = cols[-1]-cols[0]+1
    wide = np.flatnonzero(spans > spans.max()*.75)
    if not len(wide):
        return None
    head_end = int(wide[-1])+1
    lower = np.flatnonzero((np.arange(height) > head_end+1) & (spans > spans.max()*.3))
    if len(lower) < 6 or lower[0] <= head_end+1 or lower[-1]-lower[0] < 5:
        return None
    sy, bottom = int(lower[0]), int(lower[-1])+1
    sq_y, sq_x = np.nonzero(mask[sy:bottom])
    sx, ex = int(sq_x.min()), int(sq_x.max())+1
    if not .7 < (ex-sx)/(bottom-sy) < 1.35:
        return None
    # A square actuator has long outer sides and crossing diagonal supports,
    # with light interiors. A filled block or text cannot supply these holes.
    inner = pixels[sy+2:bottom-2, sx+2:ex-2]
    if not inner.size or np.percentile(inner.mean(axis=2), 75) < background.mean()-40:
        return None
    diagonals = cv2.HoughLinesP(mask[sy+1:bottom-1, sx+1:ex-1].astype(np.uint8), 1, np.pi/180,
                               4, minLineLength=max(4, (ex-sx)*.4), maxLineGap=2)
    slopes = [] if diagonals is None else [(b[3]-b[1])/(b[2]-b[0])
                                          for b in diagonals[:, 0] if b[2] != b[0]]
    if not any(.5 < s < 1.8 for s in slopes) or not any(-1.8 < s < -.5 for s in slopes):
        return None
    hy, hx = np.nonzero(mask[:head_end])
    x0, x1, top = float(hx.min()), float(hx.max()+1), float(hy.min())
    center_x = (sx+ex)/2
    if not x0+(x1-x0)*.3 < center_x < x0+(x1-x0)*.7:
        return None
    boundaries = []
    for side in ('left', 'right'):
        columns = np.arange(int(x0)+2, int(center_x)-3) if side == 'left' else np.arange(int(center_x)+3, int(x1)-2)
        if len(columns) < 4:
            return None
        lower_edge, upper_edge, coordinates = [], [], []
        for col in columns:
            rows = np.flatnonzero(mask[:head_end, col])
            if not len(rows):
                continue
            coordinates.append(col+.5)
            lower_edge.append(rows[-1]+.5)
            upper_edge.append(rows[0]+.5)
        coords = np.array(coordinates)
        lower_fit = np.polyfit(coords, lower_edge, 1)
        # Only the outside quarter is free of the upper wing's silhouette.
        outside = coords < x0+(x1-x0)*.22 if side == 'left' else coords > x1-(x1-x0)*.22
        if outside.sum() < 3:
            return None
        upper_fit = np.polyfit(coords[outside], np.array(upper_edge)[outside], 1)
        if not (lower_fit[0] < -.15 < upper_fit[0] if side == 'left' else upper_fit[0] < -.15 < lower_fit[0]):
            return None
        intersect_x = float((upper_fit[1]-lower_fit[1])/(lower_fit[0]-upper_fit[0]))
        intersect_y = float(np.polyval(lower_fit, intersect_x))
        bx = x0+.5 if side == 'left' else x1-.5
        boundaries.append((bx, float(np.polyval(upper_fit, bx)), float(np.polyval(lower_fit, bx)), intersect_x, intersect_y))
    cx, cy = np.mean(np.array(boundaries)[:, 3:5], axis=0)
    top_rows = np.arange(int(top), max(int(top)+3, int(min(boundaries[0][1], boundaries[1][1]))-2))
    tl, tr, ty = [], [], []
    for row in top_rows:
        cols = np.flatnonzero(mask[row])
        if len(cols) >= 3 and cols[0] > x0+2 and cols[-1] < x1-2:
            tl.append(cols[0]+.5)
            tr.append(cols[-1]+.5)
            ty.append(row+.5)
    if len(ty) < 3:
        return None
    lfit, rfit = np.polyfit(ty, tl, 1), np.polyfit(ty, tr, 1)
    if not lfit[0] > .1 or not rfit[0] < -.1:
        return None
    top_y = top+.5
    top_left, top_right = float(np.polyval(lfit, top_y)), float(np.polyval(rfit, top_y))
    if not top_y < cy < sy or not top_left < cx < top_right:
        return None
    if np.mean(np.any(mask[head_end:sy, max(0, int(cx)-1):int(cx)+2], axis=1)) < .75:
        return None
    core = cv2.erode(mask[:head_end].astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    if core.sum() < 10:
        return None
    body_color = np.median(pixels[:head_end][core], axis=0)
    rim_color = np.median(pixels[:head_end][mask[:head_end] & ~core], axis=0)
    square_fill = np.percentile(inner.reshape(-1, 3), 75, axis=0)
    stem_color = np.min(pixels[head_end:sy, max(0, int(cx)-1):int(cx)+2].reshape(-1, 3), axis=0)
    # Common apex; two vertical bases; upper horizontal base; square and
    # independent stroke widths. Flat wing colors reflect the observed raster,
    # including references whose SVG paint server is unsupported by PyMuPDF.
    p = [float(cx), float(cy), *boundaries[0][:3], *boundaries[1][:3],
         top_left, top_right, top_y, sx+.5, sy+.5, ex-sx-1., bottom-sy-1.,
         1., 1., 1.5, *body_color, *rim_color, *square_fill, *stem_color]

    def color(values):
        return '#' + ''.join(f'{int(round(v)):02x}' for v in np.clip(values[::-1], 0, 255))

    def svg(v):
        cx, cy, lx, ly, lb, rx, ry, rb, tl, tr, ty, sx, sy, sw, sh, bw, qw, cw = v[:18]
        fill, rim, square, stem = (color(v[i:i+3]) for i in (18, 21, 24, 27))
        triangles = [(cx,cy,lx,ly,lx,lb), (cx,cy,rx,ry,rx,rb), (cx,cy,tl,ty,tr,ty)]
        polygons = ''.join(f'<polygon points="{a:.6f},{b:.6f} {c:.6f},{d:.6f} {e:.6f},{f:.6f}" '
                           f'fill="{fill}" stroke="{rim}" stroke-width="{bw:.6f}" stroke-linejoin="round"/>'
                           for a,b,c,d,e,f in triangles)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<rect width="{width}" height="{height}" fill="{color(background)}"/>'
                f'<line x1="{cx:.6f}" y1="{cy:.6f}" x2="{cx:.6f}" y2="{sy:.6f}" stroke="{stem}" stroke-width="{cw:.6f}"/>'
                f'{polygons}<rect x="{sx:.6f}" y="{sy:.6f}" width="{sw:.6f}" height="{sh:.6f}" fill="{square}" stroke="{rim}" stroke-width="{qw:.6f}"/>'
                f'<path d="M {sx:.6f},{sy:.6f} l {sw:.6f},{sh:.6f} M {sx+sw:.6f},{sy:.6f} l {-sw:.6f},{sh:.6f}" '
                f'fill="none" stroke="{rim}" stroke-width="{qw:.6f}"/></svg>\n')

    def valid(v):
        cx, cy, lx, ly, lb, rx, ry, rb, tl, tr, ty, sx, sy, sw, sh, bw, qw, cw = v[:18]
        return (lx < cx < rx and tl < cx < tr and ty < cy < sy
                and ly < cy < lb and ry < cy < rb and abs(cx-(sx+sw/2)) < sw*.2
                and min(sw, sh) > 5 and .65 < sw/sh < 1.45 and .2 < min(bw, qw, cw) < 4
                and max(bw, qw, cw) < min(sw, sh)*.25)

    cache, evaluations = {}, 0
    def measure(v):
        nonlocal evaluations
        content = svg(v)
        if content in cache:
            return cache[content]
        evaluations += 1
        rendered = render_fn(content, width, height)
        if rendered is None:
            return None
        error = float(error_fn(image, rendered))
        result = (error, content, rendered) if np.isfinite(error) else None
        if len(cache) >= 256:
            cache.clear()
        cache[content] = result
        return result
    best = measure(p)
    if best is None or not valid(p):
        return None
    initial_error = best[0]
    for step in (1., .5, .25, .125):
        for _ in range(2):
            for index in range(len(p)):
                for sign in (-1, 1):
                    candidate = p.copy()
                    candidate[index] += sign*step*(8 if index >= 18 else 1)
                    if not valid(candidate):
                        continue
                    measured = measure(candidate)
                    if measured is not None and measured[0] < best[0]-1e-9:
                        p, best = candidate, measured
    # Reject unexplained foreground instead of deleting extra objects.
    ref_mask = np.max(abs(pixels-background), axis=2) > 35
    out_mask = np.max(abs(best[2].astype(float)-background), axis=2) > 35
    cover = cv2.dilate(out_mask.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    if np.count_nonzero(ref_mask & ~cover) > max(3, ref_mask.sum()*.03):
        return None
    return {'svg': best[1], 'rendered': best[2], 'error': best[0], 'initial_error': initial_error,
            'parameters': p, 'evaluations': evaluations, 'source': 'raster_three_way_valve_v1'}
