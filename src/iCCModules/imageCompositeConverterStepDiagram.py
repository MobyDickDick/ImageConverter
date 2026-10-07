"""Fit a circle, connectors and a framed field with a two-turn light trace.

Only raster measurements initialize the primitives. Bounded coordinate search
then registers their geometry and colors against the supplied rendering error.
"""
from __future__ import annotations

import cv2
import numpy as np


def fit_step_diagram(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(token in text for token in ('kreis', 'diagramm', 'stufen', 'verbindung', 'diagonal', 'horizontal', 'rahm')):
        return None
    if any(token in text for token in ('text', 'beschrift', 'kreuz', 'zusätzlich', 'weitere',
                                      'links oben nach rechts unten', 'nach links zu')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 12:
        return None
    hsv = cv2.cvtColor(arr, cv2.COLOR_BGR2HSV)
    saturated = cv2.inRange(hsv, (0, 90, 45), (179, 255, 255))
    contours, _ = cv2.findContours(saturated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(contour)
    if min(w, h) < 8 or not .65 < w / h < 1.5 or cv2.contourArea(contour) < .6*w*h:
        return None
    fill = np.median(arr[saturated > 0], axis=0).astype(float)
    # Light pixels must form two separated vertical ends joined by a sloping
    # middle run. This rejects a cross, flat field, writing and unrelated icons.
    field = arr[y:y+h, x:x+w]
    light = np.min(field, axis=2) > 170
    # Compact/JPEG white strokes mix with the saturated field. Prefer the
    # unambiguous white core; only widen its mask when an end is undersampled.
    if min(np.count_nonzero(light[:, :max(1, int(w*.35))]),
           np.count_nonzero(light[:, int(w*.65):])) < 2:
        light = (np.mean(field, axis=2) > 170) & (np.min(field, axis=2) > 100)
    ly, lx = np.nonzero(light)
    if len(lx) < 5:
        return None
    left = lx < w*.35
    right = lx > w*.65
    if min(np.count_nonzero(left), np.count_nonzero(right)) < 2:
        return None
    xl, xr = float(np.median(lx[left])+.5+x), float(np.median(lx[right])+.5+x)
    tl, bl = float(ly[left].min()+.5+y), float(ly[left].max()+.5+y)
    tr, br = float(ly[right].min()+.5+y), float(ly[right].max()+.5+y)
    if not (tr < br < bl and tr < tl < bl and br <= tl+max(2, .2*h)):
        return None
    neutral = (np.ptp(arr, axis=2) < 20) & (np.mean(arr, axis=2) < 220)
    neutral[:, max(0, x-2):] = False
    # The interior hole of a ring supplies its center without assuming a
    # distance from the diagram. Open line segments have no interior contour.
    rings, hierarchy = cv2.findContours(neutral.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    choices = []
    if hierarchy is not None:
        for ring, relation in zip(rings, hierarchy[0]):
            if relation[3] < 0 or cv2.contourArea(ring) < 4:
                continue
            (cx, cy), radius = cv2.minEnclosingCircle(ring)
            rx, ry, rw, rh = cv2.boundingRect(ring)
            if .65 < rw/rh < 1.5 and .07*h < radius < .35*h and cx < x:
                choices.append((cx+.5, cy+.5, radius))
    if len(choices) != 1:
        return None
    cx, cy, radius = choices[0]
    lines = cv2.HoughLinesP(neutral.astype(np.uint8), 1, np.pi/180,
                            max(5, int(h*.3)), minLineLength=max(6, h*.4), maxLineGap=3)
    if lines is None:
        return None
    diagonals = [line[0].astype(float)+.5 for line in lines
                 if line[0][2] != line[0][0] and 0 > (line[0][3]-line[0][1])/(line[0][2]-line[0][0]) > -3]
    diagonals = [line for line in diagonals if abs(line[2]-line[0]) > .3*h
                 and abs(line[3]-line[1]) > .3*h]
    if not diagonals:
        return None
    # Join both visible segments through the measured circle center. A longest
    # Hough segment alone can end at the ring and omit the other half entirely.
    ys, xs = np.nonzero(neutral)
    px, py = xs+.5, ys+.5
    outside_ring = (abs(px-cx) > radius+2) & (abs(py-cy) > radius+1)
    slopes = [(line[3]-line[1])/(line[2]-line[0]) for line in diagonals]
    slopes.extend(np.linspace(-3, -.3, 81))
    def supported(slope):
        return (abs(py-cy-slope*(px-cx))/np.hypot(1, slope) < 1.3) & outside_ring
    slope = max(slopes, key=lambda value: np.count_nonzero(supported(value)))
    support = supported(slope)
    if support.sum() < 6:
        return None
    if not (np.any(py[support] < cy-radius) and np.any(py[support] > cy+radius)):
        return None
    slope, intercept = np.polyfit(px[support], py[support], 1)
    dx0, dx1 = float(px[support].min()+.5), float(px[support].max()-.5)
    border = np.median(arr[neutral], axis=0).astype(float)
    circle_fill = arr[int(cy), int(cx)].astype(float)
    if not neutral[max(0, int(cy)), min(width-1, int((cx+x)/2))]:
        return None
    # Field, diagonal, circle, horizontal width, trace vertices/width, colors.
    p = [x-.5, y-.5, w+1., h+1., 1., dx0, slope*dx0+intercept,
         dx1, slope*dx1+intercept, 2., cx, cy, radius, 1.5, 2.,
         xr, tr, xr, br, xl, tl, xl, bl, 1., *fill, *border, *circle_fill]

    def color(values):
        return '#' + ''.join(f'{int(round(v)):02x}' for v in np.clip(values[::-1], 0, 255))

    def svg(values):
        fx, fy, fw, fh, bw, ax, ay, bx, by, dw, cx, cy, r, cw, hw = values[:15]
        points = ' '.join(f'{values[i]:.6f},{values[i+1]:.6f}' for i in range(15, 23, 2))
        shade, rim, disk = color(values[24:27]), color(values[27:30]), color(values[30:33])
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<path d="M {cx:.6f},{cy:.6f} H {fx:.6f}" fill="none" stroke="{rim}" stroke-width="{hw:.6f}" stroke-linecap="round"/>'
                f'<rect x="{fx:.6f}" y="{fy:.6f}" width="{fw:.6f}" height="{fh:.6f}" fill="{shade}" stroke="{rim}" stroke-width="{bw:.6f}"/>'
                f'<polyline points="{points}" fill="none" stroke="#ffffff" stroke-width="{values[23]:.6f}" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="M {ax:.6f},{ay:.6f} L {bx:.6f},{by:.6f}" fill="none" stroke="{rim}" stroke-width="{dw:.6f}" stroke-linecap="round"/>'
                f'<circle cx="{cx:.6f}" cy="{cy:.6f}" r="{r:.6f}" fill="{disk}" stroke="{rim}" stroke-width="{cw:.6f}"/></svg>\n')

    def measure(values):
        content = svg(values)
        rendered = render_fn(content, width, height)
        if rendered is None:
            return None
        error = float(error_fn(image, rendered))
        return (error, content, rendered) if np.isfinite(error) else None

    best = measure(p)
    if best is None:
        return None
    initial_error, evaluations = best[0], 1
    for step in (1., .5, .25, .125):
        for _ in range(2):
            for index in range(len(p)):
                for sign in (-1., 1.):
                    candidate = p.copy()
                    candidate[index] += sign*step*(8 if index >= 24 else 1)
                    fx, fy, fw, fh, bw, ax, ay, bx, by, dw, cx, cy, r, cw, hw = candidate[:15]
                    if not (min(fw, fh, bw, dw, r, cw, hw, candidate[23]) > .1
                            and ax < bx < fx and ay > by and cx < fx
                            and candidate[15] > candidate[19]
                            and fy < candidate[16] < candidate[18] < candidate[22] < fy+fh
                            and candidate[16] < candidate[20] < candidate[22]):
                        continue
                    measured = measure(candidate)
                    evaluations += 1
                    if measured is not None and measured[0] < best[0]-1e-9:
                        p, best = candidate, measured
    if best[0] >= initial_error-1e-9:
        return None
    # An unsupported extra object must not silently disappear into this model.
    observed = np.min(arr, axis=2) < 225
    reconstructed = np.min(best[2], axis=2) < 225
    covered = cv2.dilate(reconstructed.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    if np.count_nonzero(observed & ~covered) > max(3, .025*np.count_nonzero(observed)):
        return None
    return {'svg': best[1], 'rendered': best[2], 'error': best[0],
            'initial_error': initial_error, 'parameters': p, 'evaluations': evaluations,
            'source': 'raster_step_diagram_v1'}
