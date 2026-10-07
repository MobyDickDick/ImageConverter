"""Fit a described, isolated shaded disk using raster geometry and radial colors."""
from __future__ import annotations

import re

import cv2
import numpy as np


def fit_radial_disk(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not ('kreis' in text and 'radial' in text and 'verlauf' in text
            and 'hell' in text and 'dunk' in text):
        return None
    if (re.search(r'innen\s+dunk|au(?:ß|ss)en\s+hell', text)
            or any(word in text for word in ('ellipse', 'ring', 'linearer'))):
        return None
    if any(word in text for word in ('text', 'beschrift', 'haken', 'griff', 'dreieck',
                                     'quadrat', 'loch', 'zwei', 'zusätzlich', 'streifen')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 10:
        return None
    values = arr.astype(float)
    if not np.isfinite(values).all():
        return None
    foreground = (np.min(values, axis=2) < 220).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(foreground)
    if count < 2:
        return None
    index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = stats[index]
    if sum(stats[i, cv2.CC_STAT_AREA] for i in range(1, count) if i != index) > max(2, area*.01):
        return None
    foreground = (labels == index).astype(np.uint8)
    if not (.8 < w/h < 1.25 and area > .6*w*h and min(w, h) >= 8):
        return None
    contours, _ = cv2.findContours(foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    points = contours[0][:, 0].astype(float) + .5
    # Algebraic circle regression; contour samples never become SVG vertices.
    coefficients = np.linalg.lstsq(np.c_[2*points, np.ones(len(points))],
                                   np.sum(points**2, axis=1), rcond=None)[0]
    cx, cy = coefficients[:2]
    radius = float(np.sqrt(max(0., coefficients[2]+cx*cx+cy*cy)))
    if radius <= 0 or np.mean(np.abs(np.linalg.norm(points-[cx, cy], axis=1)-radius)) > max(.7, radius*.06):
        return None
    yy, xx = np.indices((height, width))
    distance = np.hypot(xx+.5-cx, yy+.5-cy)/radius
    center = values[distance < .3]
    edge = values[(distance > .55) & (distance < .75)]
    if not len(center) or not len(edge) or center.mean() < edge.mean()+8:
        return None
    offsets = np.array([0., .2, .4, .6, .8, .9, 1.])
    colors = []
    for offset in offsets:
        selection = values[(distance >= max(0., offset-.1)) & (distance < min(.95, offset+.1))]
        fallback = colors[-1] if colors else np.median(center, axis=0)
        colors.append(np.median(selection, axis=0) if len(selection) else fallback)
    colors = np.array(colors)
    predicted = np.stack([np.interp(distance, offsets, colors[:, c]) for c in range(3)], axis=-1)
    core = distance < .85
    # Reject extra marks, holes, and asymmetric scenes before fitting a disk.
    if np.percentile(np.max(np.abs(values[core]-predicted[core]), axis=1), 90) > 38:
        return None
    parameters = np.r_[cx, cy, radius, colors.ravel()]

    def svg(p):
        palette = np.clip(np.rint(p[3:].reshape(-1, 3)), 0, 255).astype(int)
        stops = ''.join(f'<stop offset="{offset:g}" stop-color="#' +
                        ''.join(f'{v:02x}' for v in color[::-1]) + '"/>'
                        for offset, color in zip(offsets, palette))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><radialGradient id="disk_shade">{stops}</radialGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<circle cx="{p[0]:g}" cy="{p[1]:g}" r="{p[2]:g}" fill="url(#disk_shade)"/></svg>\n')

    evaluations = 0

    def measure(p):
        nonlocal evaluations
        if not (p[2] >= 3 and p[2] <= min(width, height)/2+.5
                and 0 <= p[0]-p[2] and p[0]+p[2] <= width
                and 0 <= p[1]-p[2] and p[1]+p[2] <= height):
            return None
        palette = p[3:].reshape(-1, 3)
        if palette[0].mean() < palette[3].mean()+8:
            return None
        content = svg(p)
        evaluations += 1
        raster = render_fn(content, width, height)
        if raster is None:
            return None
        error = float(error_fn(image, raster))
        return (error, content, raster) if np.isfinite(error) else None

    flat = parameters.copy()
    flat[3:] = np.tile(np.median(values[distance < .9], axis=0), len(offsets))
    flat_raster = render_fn(svg(flat), width, height)
    if flat_raster is None:
        return None
    initial_error = float(error_fn(image, flat_raster))
    if not np.isfinite(initial_error):
        return None
    best = measure(parameters)
    if best is None:
        return None
    # At most 145 render probes, with geometry in pixels and stop colors in BGR.
    for step in (1., .5, .25):
        for index in range(len(parameters)):
            for sign in (-1., 1.):
                trial = parameters.copy()
                trial[index] += sign*step*(8 if index >= 3 else 1)
                candidate = measure(trial)
                if candidate is not None and candidate[0] < best[0]-1e-9:
                    parameters, best = trial, candidate
    if best[0] >= initial_error-1e-9:
        return None
    return {'svg': best[1], 'rendered': best[2], 'error': best[0],
            'initial_error': initial_error, 'evaluations': evaluations,
            'parameters': parameters.tolist(), 'source': 'raster_radial_disk_v1'}
