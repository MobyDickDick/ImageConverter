"""Register a vertical triangle and a detached rectangular gradient shaft."""
from __future__ import annotations

import cv2
import numpy as np
from xml.etree import ElementTree as ET


def _fit_upward_gradient_arrow(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(token in text for token in ('pfeil', 'dreieck', 'schaft', 'verlauf', 'oben')):
        return None
    if any(token in text for token in ('text', 'beschrift', 'kreis', 'unten gerichtet', 'nach unten',
                                      'zwei pfeil', 'zusätzlich', 'weitere', 'streifen')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 7:
        return None
    pixels = arr.astype(float)
    # A white separator splits the head from the shaft. No catalog coordinates
    # or contours are retained: both regions must independently support their
    # declared primitive before any pixel-error refinement.
    foreground = np.min(arr, axis=2) < 225
    occupied = np.any(foreground, axis=1)
    runs = []
    for indices in np.split(np.flatnonzero(occupied), np.flatnonzero(np.diff(np.flatnonzero(occupied)) > 1)+1):
        if len(indices) >= 3:
            runs.append((int(indices[0]), int(indices[-1])+1))
    if len(runs) != 2:
        return None
    top, base = runs[0]
    start, bottom = runs[1]
    rows = np.arange(top, base)
    left = np.array([np.flatnonzero(foreground[y])[0] for y in rows], dtype=float)
    right = np.array([np.flatnonzero(foreground[y])[-1]+1 for y in rows], dtype=float)
    if any(foreground[y, int(a):int(b)].mean() < .9 for y, a, b in zip(rows, left, right)):
        return None
    if len(rows) < 4 or right[-1]-left[-1] < .6*width:
        return None
    lfit, rfit = np.polyfit(rows+.5, left, 1), np.polyfit(rows+.5, right, 1)
    if lfit[0] >= -.1 or rfit[0] <= .1:
        return None
    if max(np.mean(np.abs(np.polyval(lfit, rows+.5)-left)),
           np.mean(np.abs(np.polyval(rfit, rows+.5)-right))) > max(.8, .04*width):
        return None
    tip_y = float((rfit[1]-lfit[1])/(lfit[0]-rfit[0]))
    tip_x = float(np.polyval(lfit, tip_y))
    lx, rx = float(np.polyval(lfit, base)), float(np.polyval(rfit, base))
    shaft_mask = foreground[start:bottom]
    columns = np.flatnonzero(np.mean(shaft_mask, axis=0) > .8)
    if len(columns) < 3:
        return None
    sx, ex = int(columns[0]), int(columns[-1])+1
    if not (lx <= sx < ex <= rx and start > base and ex-sx < rx-lx):
        return None
    # A cylinder-like shaft has the same horizontal color profile along its
    # length. Reject holes, writing, or additional objects instead of erasing
    # them into this hypothesis.
    profile = np.median(pixels[start:bottom, sx:ex], axis=0)
    center = len(profile)//2
    side_brightness = max(np.min(profile[:center].mean(axis=1)), np.min(profile[center+1:].mean(axis=1)))
    if profile[center].mean() <= side_brightness+10:
        return None
    deviation = np.max(np.abs(pixels[start:bottom, sx:ex]-profile), axis=2)
    if np.percentile(deviation, 95) > 25:
        return None
    core = cv2.erode(foreground[top:base].astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    if not core.any():
        return None
    head_color = np.median(pixels[top:base][core], axis=0)
    if np.percentile(np.max(np.abs(pixels[top:base][core]-head_color), axis=1), 95) > 25:
        return None
    # Stops sample the observed one-dimensional profile; their count scales
    # with input resolution but is capped independently of the symbol.
    stop_indices = np.unique(np.rint(np.linspace(0, ex-sx-1, min(9, ex-sx))).astype(int))
    stops = [(float((i+.5)/(ex-sx)), profile[i]) for i in stop_indices]

    def color(value):
        return '#' + ''.join(f'{int(round(v)):02x}' for v in np.clip(value[::-1], 0, 255))

    def svg(p):
        tx, ty, x1, x2, by, x, y, w, h = p[:9]
        adjustment = np.array(p[9:12])
        gradient = ''.join(f'<stop offset="{offset:g}" stop-color="{color(value+adjustment)}"/>' for offset, value in stops)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="shaft_color" x1="0" y1="0" x2="1" y2="0">{gradient}</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<polygon points="{tx:g},{ty:g} {x2:g},{by:g} {x1:g},{by:g}" fill="{color(head_color)}"/>'
                f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="url(#shaft_color)"/></svg>\n')

    parameters = [tip_x, tip_y, lx, rx, float(base), float(sx), float(start), float(ex-sx), float(bottom-start), 0., 0., 0.]

    def measure(p):
        content = svg(p)
        raster = render_fn(content, width, height)
        if raster is None:
            return None
        error = float(error_fn(image, raster))
        return (error, content, raster) if np.isfinite(error) else None

    best = measure(parameters)
    if best is None:
        return None
    initial_error = best[0]
    evaluations = 1
    for step in (1., .5, .25):
        for index in range(len(parameters)):
            for sign in (-1., 1.):
                candidate = parameters.copy()
                candidate[index] += sign*step*(8 if index >= 9 else 1)
                tx, ty, x1, x2, by, x, y, w, h = candidate[:9]
                if not (0 <= tx <= width and -.5 <= ty < by < y < height
                        and -.5 <= x1 < tx < x2 <= width+.5
                        and x1 <= x < x+w <= x2 and w > 0 and h > 0 and y+h <= height):
                    continue
                measured = measure(candidate)
                evaluations += 1
                if measured is not None and measured[0] < best[0]-1e-9:
                    parameters, best = candidate, measured
    if best[0] >= initial_error-1e-9:
        return None
    return {'svg': best[1], 'rendered': best[2], 'error': best[0],
            'initial_error': initial_error, 'parameters': parameters,
            'evaluations': evaluations, 'source': 'raster_gradient_arrow_v1'}


def fit_gradient_arrow(width, height, *, description, image, render_fn, error_fn):
    """Normalize a declared downward direction without adding catalog knowledge."""
    text = str(description or '').casefold()
    downward = 'nach unten' in text or 'unten gerichtet' in text
    if not downward:
        return _fit_upward_gradient_arrow(width, height, description=description,
                                         image=image, render_fn=render_fn, error_fn=error_fn)
    if 'nach oben' in text or 'oben gerichtet' in text:
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3):
        return None

    def reverse_svg(svg):
        root = ET.fromstring(svg)
        for shape in root:
            kind = shape.tag.rsplit('}', 1)[-1]
            if kind == 'polygon':
                points = [[float(v) for v in point.split(',')] for point in shape.get('points').split()]
                shape.set('points', ' '.join(f'{x:g},{height-y:g}' for x, y in points))
            elif kind == 'rect':
                shape.set('y', f"{height-float(shape.get('y', 0))-float(shape.get('height')):g}")
        return ET.tostring(root, encoding='unicode') + '\n'

    def normalized_render(svg, w, h):
        rendered = render_fn(reverse_svg(svg), w, h)
        return None if rendered is None else np.flipud(rendered)

    normalized_description = text.replace('nach unten', 'nach oben').replace('unten gerichtet', 'oben gerichtet')
    result = _fit_upward_gradient_arrow(width, height, description=normalized_description,
                                       image=np.flipud(arr), render_fn=normalized_render, error_fn=error_fn)
    if result is None:
        return None
    result['svg'] = reverse_svg(result['svg'])
    result['rendered'] = np.flipud(result['rendered']).copy()
    parameters = result['parameters'].copy()
    parameters[1] = height - parameters[1]
    parameters[4] = height - parameters[4]
    parameters[6] = height - parameters[6] - parameters[8]
    result.update(parameters=parameters, direction='down')
    return result
