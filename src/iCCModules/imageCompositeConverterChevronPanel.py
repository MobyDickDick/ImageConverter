"""Register a framed vertical gradient and an open upward chevron from pixels."""
from __future__ import annotations

import cv2
import numpy as np


def fit_chevron_panel(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(token in text for token in ('rechteck', 'rahm', 'vertikal', 'verlauf', 'dachlinie', 'oben')):
        return None
    if any(token in text for token in ('kreis', 'griff', 'text', 'beschrift', 'zusätzlich',
                                      'weitere', 'horizontaler verlauf', 'spitze unten')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 10:
        return None
    mask = np.min(arr, axis=2) < 240
    ys, xs = np.nonzero(mask)
    if len(xs) < 30:
        return None
    x, y, w, h = cv2.boundingRect(np.column_stack((xs, ys)).astype(np.int32))
    if min(w, h) < 8 or mask[y:y+h, x:x+w].mean() < .75:
        return None
    pixels = arr.astype(float)
    profile = np.median(pixels[y+2:y+h-2, x+2:x+w-2], axis=1)
    if np.ptp(profile, axis=0).max() < 8:
        return None
    # Compare each row against its dominant fill, which also works for an
    # achromatic panel with a dark mark rather than a white mark on color.
    deviation = np.linalg.norm(pixels[y+2:y+h-2, x+2:x+w-2]-profile[:, None, :], axis=2)
    mark = deviation > max(35., float(np.percentile(deviation, 95))*.45)
    my, mx = np.nonzero(mark)
    if len(mx) < max(8, w*.3):
        return None
    mx, my = mx.astype(float)+x+2.5, my.astype(float)+y+2.5
    # Each arm is estimated separately. Border pixels, compression fringes,
    # and the join cannot determine the slopes by themselves.
    lines = cv2.HoughLinesP(mark.astype(np.uint8), 1, np.pi/180,
                            max(4, int(w*.12)), minLineLength=max(4, w*.18), maxLineGap=3)
    if lines is None:
        return None
    arms = []
    for sign in (-1, 1):
        candidates = []
        for line in lines[:, 0]:
            ax, ay, bx, by = line.astype(float)+[x+2.5, y+2.5, x+2.5, y+2.5]
            if abs(bx-ax) < w*.15:
                continue
            slope = (by-ay)/(bx-ax)
            if .1 < sign*slope < 2:
                intercept = ay-slope*ax
                support = abs(my-slope*mx-intercept)/np.hypot(1, slope) < max(1.5, h*.06)
                candidates.append((int(support.sum()), slope, intercept, support))
        if not candidates:
            return None
        _, slope, intercept, support = max(candidates, key=lambda item: item[0])
        if support.sum() < max(4, w*.15) or np.ptp(mx[support]) < w*.25:
            return None
        slope, intercept = np.polyfit(mx[support], my[support], 1)
        arms.append((slope, intercept, support))
    left, right = arms
    px = float((right[1]-left[1])/(left[0]-right[0]))
    py = float(left[0]*px+left[1])
    if not (x+w*.2 < px < x+w*.8 and y-1 < py < y+h*.35):
        return None
    supported = left[2] | right[2]
    if supported.mean() < .85:
        return None
    values = pixels[(my-.5).astype(int), (mx-.5).astype(int)]
    strengths = deviation[mark]
    shade = np.median(values[supported & (strengths > np.percentile(strengths[supported], 65))], axis=0)
    rim_samples = np.concatenate((pixels[y+2:y+h-2, x], pixels[y+2:y+h-2, x+w-1]))
    rim = np.median(rim_samples, axis=0)
    # A bounded number of native gradient stops describes a continuous profile;
    # no per-pixel paths or reference vectors enter the runtime.
    indices = np.unique(np.rint(np.linspace(0, len(profile)-1, min(9, len(profile)))).astype(int))
    stops = [(float((i+2.5)/h), profile[i]) for i in indices]
    endpoints = (float(x), float(left[0]*x+left[1]),
                 float(x+w), float(right[0]*(x+w)+right[1]))
    length = np.hypot(px-endpoints[0], py-endpoints[1])+np.hypot(endpoints[2]-px, endpoints[3]-py)
    stroke = float(np.clip(supported.sum()/length, .6, h*.2))
    # Rectangle, left endpoint, join, right endpoint, mark width and colors.
    p = [x+.5, y+.5, w-1., h-1., 1., *endpoints[:2], px, py, *endpoints[2:], stroke,
         *rim, *shade, 0., 0., 0.]

    def color(value):
        return '#' + ''.join(f'{int(round(v)):02x}' for v in np.clip(value[::-1], 0, 255))

    def svg(values):
        rx, ry, rw, rh, bw, ax, ay, cx, cy, bx, by, sw = values[:12]
        gradient = ''.join(f'<stop offset="{offset:.6f}" stop-color="{color(shade+values[18:21])}"/>'
                           for offset, shade in stops)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="panel_fill" x1="0" y1="0" x2="0" y2="1">{gradient}</linearGradient></defs>'
                f'<rect x="{rx:.6f}" y="{ry:.6f}" width="{rw:.6f}" height="{rh:.6f}" fill="url(#panel_fill)" '
                f'stroke="{color(values[12:15])}" stroke-width="{bw:.6f}"/>'
                f'<polyline points="{ax:.6f},{ay:.6f} {cx:.6f},{cy:.6f} {bx:.6f},{by:.6f}" fill="none" '
                f'stroke="{color(values[15:18])}" stroke-width="{sw:.6f}" stroke-linejoin="miter"/></svg>\n')

    evaluations, cache = 0, {}

    def measure(values):
        nonlocal evaluations
        content = svg(values)
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

    def valid(values):
        rx, ry, rw, rh, bw, ax, ay, cx, cy, bx, by, sw = values[:12]
        return (min(rw, rh) > 4 and .1 <= min(bw, sw) and max(bw, sw) < rh*.3
                and rx-2 <= ax < cx < bx <= rx+rw+2 and cy < min(ay, by)
                and ry-2 < cy < ry+rh*.4 and max(ay, by) < ry+rh)

    best = measure(p)
    if best is None:
        return None
    initial_error = best[0]
    for step in (1., .5, .25, .125):
        for _ in range(2):
            for index in range(len(p)):
                for sign in (-1., 1.):
                    candidate = p.copy()
                    candidate[index] += sign*step*(8 if index >= 12 else 1)
                    if not valid(candidate):
                        continue
                    measured = measure(candidate)
                    if measured is not None and measured[0] < best[0]-1e-9:
                        p, best = candidate, measured
    if best[0] > initial_error or not valid(p):
        return None
    residual = np.max(np.abs(pixels-best[2].astype(float)), axis=2) > 65
    if residual.mean() > .04:
        return None
    return {'svg': best[1], 'rendered': best[2], 'error': best[0], 'initial_error': initial_error,
            'parameters': p, 'evaluations': evaluations, 'source': 'raster_chevron_panel_v1'}
