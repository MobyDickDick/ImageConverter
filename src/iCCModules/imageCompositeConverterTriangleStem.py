"""Fit an upward filled triangle over a separated rectangular gradient stem."""
from __future__ import annotations

import copy
import cv2
import numpy as np

SOURCE = 'raster_triangle_stem_v1'


def _hex(bgr):
    return '#' + ''.join(f'{int(v):02x}' for v in np.clip(np.rint(bgr[::-1]), 0, 255))


def fit_triangle_stem(geometry_ir, *, image, render_fn, error_fn):
    """Register analytic geometry only, with a bounded improving render search."""
    if len(geometry_ir) != 1 or geometry_ir[0].get('kind') != 'TriangleStemGlyph':
        return None
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape[2] != 3 or min(arr.shape[:2]) < 8:
        return None
    h, w = arr.shape[:2]
    pixels = arr.astype(float)
    mask = (np.min(arr, axis=2) < 225).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    triangles = []
    for label in range(1, count):
        x, y, bw, bh, area = stats[label]
        if area < max(5, w*h*.025) or y+bh > h*.6 or bw < w*.3 or bh < 3:
            continue
        region = (labels == label).astype(np.uint8)
        contours, _ = cv2.findContours(region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        hull = cv2.convexHull(max(contours, key=cv2.contourArea))
        polygon = cv2.approxPolyDP(hull, cv2.arcLength(hull, True)*.065, True)
        if len(polygon) != 3:
            continue
        verts = polygon[:, 0, :].astype(float)
        tip = verts[np.argmin(verts[:, 1])]
        base = np.delete(verts, np.argmin(verts[:, 1]), axis=0)
        polygon_area = cv2.contourArea(polygon)
        if (polygon_area <= 0 or not .75 <= cv2.contourArea(hull)/polygon_area <= 1.3
                or abs(base[0, 1]-base[1, 1]) > max(1, bh*.15)
                or abs(tip[0]-base[:, 0].mean()) > bw*.15):
            continue
        triangles.append((region, x, y, bw, bh))
    if len(triangles) != 1:
        return None
    region, x, y, bw, bh = triangles[0]
    # Straight edge regressions estimate the triangle; never export its contour.
    rows = []
    for row in range(y+1, y+bh-1):
        cols = np.flatnonzero(region[row])
        if len(cols) >= 2:
            rows.append((row+.5, cols[0]+.5, cols[-1]+.5))
    if len(rows) < 2:
        return None
    rows = np.array(rows)
    left = np.polyfit(rows[:, 0], rows[:, 1], 1)
    right = np.polyfit(rows[:, 0], rows[:, 2], 1)
    if left[0] >= -.1 or right[0] <= .1:
        return None
    tip_y = (right[1]-left[1])/(left[0]-right[0])
    center = np.polyval(left, tip_y)
    base_y = y+bh-.25
    half = (np.polyval(right, base_y)-np.polyval(left, base_y))/2 + .4
    stem_mask = mask.copy()
    stem_mask[:y+bh+1] = 0
    ys, xs = np.where(stem_mask)
    if len(xs) < 4:
        return None
    sx, sy, ex, ey = xs.min(), ys.min(), xs.max()+1, ys.max()+1
    stem_w, stem_h = ex-sx, ey-sy
    if (stem_w < 2 or stem_w >= bw*.8 or stem_h < bh*.65
            or abs((sx+ex)/2-center) > bw*.15
            or sy-base_y > max(4, bh*.3)):
        return None
    # Both edges must persist through the stem; reject dots, diagonals, text.
    occupied = stem_mask[sy:ey, sx:ex]
    if (np.mean(occupied[:, :max(1, stem_w//3)].any(axis=1)) < .85
            or np.mean(occupied[:, -max(1, stem_w//3):].any(axis=1)) < .85):
        return None
    core = cv2.erode(region, np.ones((3, 3), np.uint8)).astype(bool)
    if not core.any():
        core = region.astype(bool)
    fill = np.median(pixels[core], axis=0)
    border = np.median(pixels[region.astype(bool) & ~core], axis=0)
    # Boundary pixels mix foreground with white. Estimate colors from inner
    # columns and put the analytic boundary halfway through the outer pixels.
    if stem_w < 4:
        return None
    profile = np.median(pixels[sy+1:ey, sx+1:ex-1], axis=0)
    t = np.arange(1, stem_w-1)/(stem_w-1)
    weights = np.column_stack((np.maximum(1-2*t, 0), 1-np.abs(2*t-1), np.maximum(2*t-1, 0)))
    stops = np.clip(np.linalg.lstsq(weights, profile, rcond=None)[0], 0, 255)
    # A brighter middle is part of the declared cylindrical stem topology.
    if stops[1].mean() < max(stops[0].mean(), stops[2].mean())+12:
        return None
    params = [center, max(-.5, tip_y), half, base_y, .3, sx+.5, sy+.5, stem_w-1, stem_h-.5]
    palette = [fill, border, *stops]
    evaluations = 0

    def build(p, colors):
        cx, ty, hw, by, sw, rx, ry, rw, rh = p
        candidate = copy.deepcopy(geometry_ir)
        candidate[0].update(
            points=[[cx/w, ty/h], [(cx-hw)/w, by/h], [(cx+hw)/w, by/h]],
            fill=_hex(colors[0]), stroke=_hex(colors[1]), stroke_width=sw/min(w, h),
            stem_bbox=[rx/w, ry/h, rw/w, rh/h],
            stem_stops=[{'offset': offset, 'color': _hex(color)}
                        for offset, color in zip(('0%', '50%', '100%'), colors[2:])],
            source=SOURCE)
        return candidate

    def measure(p, colors):
        nonlocal evaluations
        cx, ty, hw, by, sw, rx, ry, rw, rh = p
        if (hw <= 1 or by-ty <= 2 or not 0 <= sw <= 1.5
                or rw < 1 or rh < 2 or rw > hw*1.5
                or abs(rx+rw/2-cx) > hw*.25
                or ry < by or ry-by > max(4, (by-ty)*.3)
                or rx < -.5 or rx+rw > w+.5 or ry+rh > h+.5
                or colors[3].mean() < max(colors[2].mean(), colors[4].mean())+12):
            return None
        evaluations += 1
        candidate = build(p, colors)
        rendered = render_fn(candidate)
        if rendered is None:
            return None
        error = float(error_fn(rendered))
        return (error, candidate, rendered) if np.isfinite(error) else None

    seed = render_fn(geometry_ir)
    if seed is None:
        return None
    initial_error = float(error_fn(seed))
    if not np.isfinite(initial_error):
        return None
    best = measure(params, palette)
    if best is None:
        return None
    # Two analytic boundary hypotheses cover both fully covered and
    # antialiased edge pixels. The render error chooses between them.
    full_profile = np.median(pixels[sy:ey, sx:ex], axis=0)
    full_t = (np.arange(stem_w)+.5)/stem_w
    full_weights = np.column_stack((np.maximum(1-2*full_t, 0),
                                   1-np.abs(2*full_t-1), np.maximum(2*full_t-1, 0)))
    full_stops = np.clip(np.linalg.lstsq(full_weights, full_profile, rcond=None)[0], 0, 255)
    seeds = [(params.copy(), [c.copy() for c in palette]),
             ([center, max(-.5, tip_y), half, base_y, .3, sx, sy, stem_w, stem_h],
              [fill, border, *full_stops])]
    global_best = None
    for params, palette in seeds:
        best = measure(params, palette)
        if best is None:
            continue
        for phase in range(2):
            for step in ((1., .5, .25) if phase == 0 else (.5, .25)):
                for index in range(len(params)):
                    for delta in (-step, step):
                        trial = params.copy()
                        trial[index] += delta
                        measured = measure(trial, palette)
                        if measured is not None and measured[0] < best[0]-1e-9:
                            params, best = trial, measured
            for step in ((12., 4.) if phase == 0 else (4., 2.)):
                for index in range(len(palette)):
                    for channel in range(3):
                        for delta in (-step, step):
                            colors = [color.copy() for color in palette]
                            colors[index][channel] = np.clip(colors[index][channel]+delta, 0, 255)
                            measured = measure(params, colors)
                            if measured is not None and measured[0] < best[0]-1e-9:
                                palette, best = colors, measured
        if global_best is None or best[0] < global_best[0]:
            global_best = best
    if global_best is None:
        return None
    best = global_best
    if best[0] >= initial_error-1e-9:
        return None
    return {'geometry_ir': best[1], 'rendered': best[2], 'initial_error': initial_error,
            'final_error': best[0], 'evaluations': evaluations, 'source': SOURCE}
