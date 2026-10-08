"""Fit a described gradient panel, diagonal and central dot from raster evidence."""
from __future__ import annotations

import math

import cv2
import numpy as np


def fit_dot_panel(*, width, height, image, descending, render_fn, error_fn):
    """Register independent primitives without consulting a reference SVG."""
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape[:2] != (height, width) or min(width, height) < 12:
        return None
    lum = arr.astype(float).mean(axis=2)
    h, w = lum.shape
    yy, xx = np.indices((h, w), dtype=float)
    xx += .5
    yy += .5
    visible = lum < 250
    rows = np.flatnonzero(visible.sum(axis=1) > w*.5)
    cols = np.flatnonzero(visible.sum(axis=0) > h*.5)
    if not len(rows) or not len(cols):
        return None
    x0, x1 = float(cols[0])+.5, float(cols[-1])+.5
    y0, y1 = float(rows[0])+.5, float(rows[-1])+.5
    inside = (xx > x0+2) & (xx < x1-2) & (yy > y0+2) & (yy < y1-2)
    dark = (lum < np.percentile(lum[inside], 15)) & inside
    distance = cv2.distanceTransform(dark.astype(np.uint8), cv2.DIST_L2, 5)
    # A circle has a thick interior; the narrow diagonal cannot supply its seed.
    peak = float(distance.max())
    core = distance > peak*.65
    if peak < 1 or not core.any():
        return None
    cx, cy = float(xx[core].mean()), float(yy[core].mean())
    radius = peak
    dot_color = float(np.median(lum[np.hypot(xx-cx, yy-cy) < radius*.65]))
    line_mask = dark & (np.hypot(xx-cx, yy-cy) > radius*1.7)
    line_y, line_x = yy[line_mask], xx[line_mask]
    if len(line_x) < 5:
        return None
    # Row centers avoid exporting raster contour vertices as vector geometry.
    unique_y = np.unique(line_y)
    centers = np.array([np.median(line_x[line_y == y]) for y in unique_y])
    slope, intercept = np.polyfit(unique_y, centers, 1)
    if (slope > 0) != descending:
        return None
    lx0, lx1 = slope*y0+intercept, slope*y1+intercept
    line_color = float(np.percentile(lum[line_mask], 25))
    line_width = max(.7, len(line_x)/(np.ptp(unique_y)*math.hypot(1, slope)))
    profile = np.array([np.median(lum[int(y0+2):max(int(y0+3), int(y1-2)), x]) for x in range(w)])
    valid = np.arange(max(0, int(x0+2)), min(w, int(x1-1)))
    if len(valid) < 4:
        return None
    highlight = float(np.max(profile[valid]))
    plateau = valid[profile[valid] > highlight-3]
    p0, p1 = float(plateau[0]), float(plateau[-1])
    left_fit = valid[valid < p0]
    right_fit = valid[valid > p1]
    left = float(np.polyval(np.polyfit(left_fit+.5, profile[left_fit], 1), x0)) if len(left_fit) > 1 else highlight
    right = float(np.polyval(np.polyfit(right_fit+.5, profile[right_fit], 1), x1)) if len(right_fit) > 1 else highlight
    edge = visible & ~inside
    params = dict(x0=x0, x1=x1, y0=y0, y1=y1, border=1., border_color=float(np.median(lum[edge])),
                  lx0=float(lx0), ly0=y0, lx1=float(lx1), ly1=y1,
                  line_width=line_width, line_color=line_color, cx=cx, cy=cy, radius=radius,
                  dot_color=dot_color, left=left, right=right, highlight=highlight,
                  p0=(p0+.5-x0)/(x1-x0), p1=(p1+.5-x0)/(x1-x0))

    def gray(value):
        v = int(np.clip(round(value), 0, 255))
        return f'#{v:02x}{v:02x}{v:02x}'

    def svg(p):
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            '<defs><linearGradient id="panelShade">'
            f'<stop offset="0" stop-color="{gray(p["left"])}"/>'
            f'<stop offset="{p["p0"]:.5f}" stop-color="{gray(p["highlight"])}"/>'
            f'<stop offset="{p["p1"]:.5f}" stop-color="{gray(p["highlight"])}"/>'
            f'<stop offset="1" stop-color="{gray(p["right"])}"/></linearGradient></defs>'
            f'<rect width="{w}" height="{h}" fill="white"/>'
            f'<rect x="{p["x0"]:.4f}" y="{p["y0"]:.4f}" width="{p["x1"]-p["x0"]:.4f}" '
            f'height="{p["y1"]-p["y0"]:.4f}" fill="url(#panelShade)" '
            f'stroke="{gray(p["border_color"])}" stroke-width="{p["border"]:.4f}"/>'
            f'<line x1="{p["lx0"]:.4f}" y1="{p["ly0"]:.4f}" x2="{p["lx1"]:.4f}" y2="{p["ly1"]:.4f}" '
            f'stroke="{gray(p["line_color"])}" stroke-width="{p["line_width"]:.4f}"/>'
            f'<circle cx="{p["cx"]:.4f}" cy="{p["cy"]:.4f}" r="{p["radius"]:.4f}" fill="{gray(p["dot_color"])}"/>'
            '</svg>')

    evaluations = 0
    render_cache = {}
    border_pixels = np.concatenate((arr[0], arr[-1], arr[:, 0], arr[:, -1]))
    background = np.median(border_pixels.astype(float), axis=0)
    target_contrast = np.max(np.abs(arr.astype(float)-background), axis=2)

    def measure(p):
        nonlocal evaluations
        if not (p['x1'] > p['x0'] and p['y1'] > p['y0'] and 0 <= p['p0'] <= p['p1'] <= 1
                and .2 <= p['radius'] <= min(w, h)*.35 and .2 <= p['border'] <= 5
                and .2 <= p['line_width'] <= min(w, h)*.2):
            return None
        cache_key = tuple(sorted(p.items()))
        if cache_key in render_cache:
            return render_cache[cache_key]
        content = svg(p)
        raster = render_fn(content, w, h)
        evaluations += 1
        if raster is None:
            return None
        error = float(error_fn(arr, raster))
        # Give contour and tonal deviations comparable influence. Absolute
        # error alone can trade a misplaced frame for many slightly closer
        # highlight pixels, especially when the panel reaches the canvas edge.
        error += float(np.square(arr.astype(float)-raster).mean())/32
        candidate_contrast = np.max(np.abs(raster.astype(float)-background), axis=2)
        for threshold in (15, 25, 40):
            target_mask = target_contrast > threshold
            candidate_mask = candidate_contrast > threshold
            union = np.count_nonzero(target_mask | candidate_mask)
            # Normalize to the occupied region, so sparse faint structures
            # retain influence even on a mostly empty or highlighted panel.
            overlap = np.count_nonzero(target_mask & candidate_mask)/union if union else 1.
            error += 12*(1-overlap)
        if not math.isfinite(error):
            return None
        result = (error, content, raster, p)
        if len(render_cache) >= 512:
            del render_cache[next(iter(render_cache))]
        render_cache[cache_key] = result
        return result

    initial = measure(params)
    if initial is None:
        return None
    # Geometry and colors have separate units. Revisit each primitive after
    # its neighbours improve, including a fine subpixel registration pass.
    alternatives = []
    for schedule in ((1., .5, .25, .125), (2., 1., .5, .25, .125)):
        best = initial
        for step in schedule:
            for _ in range(5):
                changed = False
                for key in params:
                    delta = step*8 if key in {'left', 'right', 'highlight', 'border_color', 'line_color', 'dot_color'} else step
                    if key in {'p0', 'p1'}:
                        delta /= max(1, best[3]['x1']-best[3]['x0'])
                    for sign in (-1, 1):
                        trial = dict(best[3])
                        trial[key] += sign*delta
                        candidate = measure(trial)
                        if candidate and candidate[0] < best[0]-1e-9:
                            best, changed = candidate, True
                if not changed:
                    break
        alternatives.append(best)
    target_edges = cv2.Canny(arr, 50, 140) > 0
    target_distance = cv2.distanceTransform((~target_edges).astype(np.uint8), cv2.DIST_L2, 3)

    def registration_score(candidate):
        raster = candidate[2]
        edges = cv2.Canny(raster, 50, 140) > 0
        if not edges.any() or not target_edges.any():
            return float('inf')
        output_distance = cv2.distanceTransform((~edges).astype(np.uint8), cv2.DIST_L2, 3)
        contour_error = (target_distance[edges].mean()+output_distance[target_edges].mean())/2
        contrast = np.max(np.abs(raster.astype(float)-background), axis=2)
        overlaps = []
        for threshold in (15, 25, 40):
            a, b = target_contrast > threshold, contrast > threshold
            union = np.count_nonzero(a | b)
            overlaps.append(np.count_nonzero(a & b)/union if union else 1.)
        return float(contour_error) + 4*(1-min(overlaps)) + candidate[0]/100

    best = min(alternatives, key=registration_score)
    p = best[3]
    return float(error_fn(arr, best[2])), best[1], best[2], {
        'center_dot_radius': p['radius'], 'center_dot_x_ratio': p['cx']/w,
        'center_dot_y_ratio': p['cy']/h,
    }, [f'dot_registration_evaluations={evaluations}']
