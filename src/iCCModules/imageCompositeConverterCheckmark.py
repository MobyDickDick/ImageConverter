"""Register a described green checkmark over a neutral disk from the current raster."""
from __future__ import annotations

import copy
import math

import cv2
import numpy as np


def _hex(bgr):
    return '#' + ''.join(f'{int(np.clip(round(v), 0, 255)):02x}' for v in bgr[::-1])


def fit_checkmark_disk(geometry_ir, *, image, render_fn, error_fn):
    """Fit two line segments and a disk, preserving their topology and stacking.

    Color evidence locates the green stroke; a two-line regression estimates its
    joint. The largest neutral component supplies the occluded disk bounds.
    No contour is exported, and no filename or reference artifact is consulted.
    """
    if ([e.get('role') for e in geometry_ir] != [None, 'checkmark_disk', 'checkmark_shadow', 'checkmark']
            or [e.get('kind') for e in geometry_ir] != ['ColorPatch', 'CircleBackground', 'PolygonPath', 'PolygonPath']):
        return None
    if not isinstance(geometry_ir[1].get('radial_gradient'), dict) or len(geometry_ir[1]['radial_gradient'].get('stops', [])) != 3:
        return None
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape[2] != 3 or min(arr.shape[:2]) < 12:
        return None
    h, w = arr.shape[:2]
    scale = min(w, h)
    values = arr.astype(float)
    chroma = values[:, :, 1] - np.maximum(values[:, :, 0], values[:, :, 2])
    green = chroma > 35
    count, labels, stats, _ = cv2.connectedComponentsWithStats(green.astype(np.uint8))
    if count < 2:
        return None
    index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    green = labels == index
    ys, xs = np.where(green)
    if len(xs) < 8 or np.ptp(xs) < w*.3 or np.ptp(ys) < h*.3:
        return None
    columns = np.unique(xs)
    centers = np.array([np.average(np.flatnonzero(green[:, x])+.5,
                                  weights=chroma[green[:, x], x]) for x in columns])
    xcenters = columns+.5
    best_lines = None
    # Regression is performed on column centers, not raster boundary vertices.
    for split in range(3, len(columns)-3):
        left = np.polyfit(xcenters[:split], centers[:split], 1)
        right = np.polyfit(xcenters[split:], centers[split:], 1)
        if not (left[0] > .25 and right[0] < -.4):
            continue
        joint_x = (right[1]-left[1])/(left[0]-right[0])
        if not xcenters[1] < joint_x < xcenters[-2]:
            continue
        residual = float(np.sum((np.polyval(left, xcenters[:split])-centers[:split])**2)
                         + np.sum((np.polyval(right, xcenters[split:])-centers[split:])**2))
        if best_lines is None or residual < best_lines[0]:
            best_lines = (residual, left, right, joint_x)
    if best_lines is None:
        return None
    _, left, right, joint_x = best_lines
    points = [[xcenters[0], np.polyval(left, xcenters[0])],
              [joint_x, np.polyval(left, joint_x)],
              [xcenters[-1], np.polyval(right, xcenters[-1])]]
    neutral = (np.ptp(values, axis=2) < 22) & (np.mean(values, axis=2) < 215)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(neutral.astype(np.uint8))
    if count < 2:
        return None
    index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, bw, bh, area = stats[index].astype(float)
    if min(bw, bh) < scale*.25 or not .6 < bw/bh < 1.7 or area < bw*bh*.25:
        return None
    # The foreground can split the disk into two components. Its lower exposed
    # arc still spans the diameter; infer the missing upper half geometrically.
    y, bh = y+bh-bw, bw
    cx, cy, radius = x+bw/2, y+bh/2, bw/2
    yy, xx = np.indices((h, w))
    distance = np.hypot(xx+.5-cx, yy+.5-cy)/radius
    candidate = copy.deepcopy(geometry_ir)
    disk = next(e for e in candidate if e.get('role') == 'checkmark_disk')
    stroke = next(e for e in candidate if e.get('role') == 'checkmark')
    shadow = next(e for e in candidate if e.get('role') == 'checkmark_shadow')
    disk.update(bbox=[(x+.5)/w, (y+.5)/h, (bw-1)/w, (bh-1)/h], stroke_width=1/scale)
    observed = neutral & (distance < .95)
    for stop, bounds in zip(disk['radial_gradient']['stops'], [(0, .35), (.5, .8), (.8, .95)]):
        pixels = values[observed & (distance >= bounds[0]) & (distance < bounds[1])]
        if len(pixels):
            stop['color'] = _hex(np.median(pixels, axis=0))
    edge_pixels = values[neutral & (distance > .85) & (distance < 1.05)]
    if len(edge_pixels):
        disk['stroke'] = _hex(np.median(edge_pixels, axis=0))
    stroke.pop('stroke_gradient', None)
    stroke.update(points=[[float(px/w), float(py/h)] for px, py in points],
                  stroke=_hex(np.median(values[green & (chroma >= np.percentile(chroma[green], 65))], axis=0)),
                  stroke_width=max(1.5, len(xs)/(np.linalg.norm(np.subtract(points[1], points[0]))
                                                       + np.linalg.norm(np.subtract(points[2], points[1]))))/scale)
    shadow.update(points=copy.deepcopy(stroke['points']), stroke_width=stroke['stroke_width']+1/scale,
                  stroke='#aaaaaa')
    original = render_fn(geometry_ir)
    if original is None:
        return None
    initial_error = float(error_fn(original))
    if not math.isfinite(initial_error):
        return None
    evaluations = 0

    def measure(ir):
        nonlocal evaluations
        disk, shadow, stroke = ir[1:]
        p = stroke['points']
        box = disk['bbox']
        if not (p[0][0] < p[1][0] < p[2][0] and p[0][1] < p[1][1] and p[2][1] < p[1][1]
                and .7 < box[2]*w/(box[3]*h) < 1.3 and min(box[2]*w, box[3]*h) > scale*.25
                and 0 < disk['stroke_width'] < .1 and 0 < stroke['stroke_width'] < .25
                and stroke['stroke_width'] <= shadow['stroke_width'] <= stroke['stroke_width']+1.5/scale):
            return None
        shadow['points'] = copy.deepcopy(p)
        raster = render_fn(ir)
        evaluations += 1
        if raster is None:
            return None
        error = float(error_fn(raster))
        return (error, copy.deepcopy(ir), raster) if math.isfinite(error) else None

    best = measure(candidate)
    if best is None:
        return None
    # Bounded coordinate descent in pixel units. Colors remain raster estimates.
    for step in (1., .5, .25):
        for _ in range(2):
            changed = False
            for element, field, count in [(1, 'bbox', 4), (1, 'stroke_width', 1),
                                           (2, 'stroke_width', 1), (3, 'stroke_width', 1), (3, 'points', 6)]:
                for i in range(count):
                    for sign in (-1, 1):
                        trial = copy.deepcopy(best[1])
                        divisor = (w if i % 2 == 0 else h) if field in ('bbox', 'points') else scale
                        delta = sign*step/divisor
                        if field == 'points':
                            trial[element][field][i//2][i % 2] += delta
                        elif field == 'bbox':
                            trial[element][field][i] += delta
                        else:
                            trial[element][field] += delta
                        measured = measure(trial)
                        if measured and measured[0] < best[0]-1e-9:
                            best, changed = measured, True
            if not changed:
                break
    if best[0] >= initial_error-1e-9:
        return None
    return {'geometry_ir': best[1], 'rendered': best[2], 'initial_error': initial_error,
            'final_error': best[0], 'evaluations': evaluations, 'source': 'raster_checkmark_disk_registration_v1'}
