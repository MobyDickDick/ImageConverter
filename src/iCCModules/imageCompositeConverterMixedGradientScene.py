"""Raster-derived gradient circles containing one or two flat rectangles.

The closed description contract controls topology; raster residuals supply
instances. No catalogue keys, saved geometry or reference vectors are read.
"""
from __future__ import annotations

import re

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register
from src.iCCModules.imageCompositeConverterGradientScene import _gradient
from src.iCCModules.imageCompositeConverterPrimitiveScene import _circle, _local_quality


def requested(description):
    text = str(description or '').casefold()
    return ('der kreis hat einen' in text
            and 'die rechtecke liegen innerhalb des kreises' in text)


def scene_contract(description):
    """Consume all assertions, rather than silently dropping extra content."""
    text = str(description or '').casefold()
    from src.iCCModules.imageCompositeConverterLayeredScene import SHAPES
    matches = list(SHAPES.finditer(text))
    counts = {'circle': 0, 'rectangle': 0}
    for m in matches:
        counts['circle' if m[3].startswith('kreis') else 'rectangle'] += {
            'zwei': 2, '2': 2, 'drei': 3, '3': 3}.get(m[1], 1)
    if counts['circle'] != 1 or counts['rectangle'] not in (1, 2):
        return None
    direction = re.findall(r'der kreis hat einen (horizontal|vertikal)en farbverlauf', text)
    if len(direction) != 1:
        return None
    relation = 'die rechtecke liegen innerhalb des kreises'
    if counts['rectangle'] == 2:
        relation += ' und getrennt nebeneinander'
    if text.count(relation) != 1:
        return None
    outlined = 'die formen haben helle konturen' in text
    rest = SHAPES.sub('', text).replace(relation, '')
    rest = re.sub(r'der kreis hat einen (?:horizontal|vertikal)en farbverlauf', '', rest)
    for clause in ('die formen haben helle konturen', 'keine beschriftung', 'ohne text oder zeichen'):
        rest = rest.replace(clause, '')
    if re.sub(r'[\s.,;]+|\bund\b', '', rest):
        return None
    return dict(count=1+counts['rectangle'], axis=0 if direction[0] == 'horizontal' else 1,
                outlined=outlined)


def _flat_edge(profile, fill, stroke, low, high):
    """Interpolate the inner straight edge from antialias coverage."""
    delta = fill-stroke
    denominator = float(delta@delta)
    if denominator < 100:
        return None
    coverage = np.clip((profile-stroke)@delta/denominator, 0, 1)
    inside = np.flatnonzero((coverage >= .5) & (np.arange(len(profile)) >= low-2)
                           & (np.arange(len(profile)) <= high+2))
    if not len(inside):
        return None
    # JPEG shadows can form a second dark stripe beyond a light rim. Only
    # the connected flat interval around the object's center is its interior.
    middle = min(inside, key=lambda i: abs(i-(low+high)/2))
    first = last = int(middle)
    while first > 0 and coverage[first-1] >= .5:
        first -= 1
    while last+1 < len(profile) and coverage[last+1] >= .5:
        last += 1
    if first < 1 or last+1 >= len(profile):
        return None
    def crossing(a, b):
        difference = coverage[b]-coverage[a]
        return a+.5+(.5-coverage[a])/difference if abs(difference) > 1e-6 else a+1.
    return crossing(first-1, first), crossing(last, last+1)


def detect_instances(pixels, contract):
    """Fit background paint first, then explain contrasting interior regions."""
    foreground = (np.max(255-pixels.astype(float), axis=2) > 25).astype('uint8')
    contours = cv2.findContours(foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    contours = [c for c in contours if cv2.contourArea(c) >= 12]
    if len(contours) != 1:
        return None
    contour = contours[0]
    center, radius, residual = _circle(contour)
    x, y, w, h = cv2.boundingRect(contour)
    if abs(w-h) > 2 or residual > .85 or radius < 12:
        return None
    yy, xx = np.indices(foreground.shape)
    distance = np.hypot(xx+.5-center[0], yy+.5-center[1])
    interior = (distance < radius-3).astype('uint8')
    geometry = np.array([center[0]-radius, center[1]-radius, 2*radius, 2*radius, 0.])
    # _gradient uses [left, top, right, bottom] bounds.
    bounds = np.r_[geometry[:2], geometry[:2]+geometry[2:4]]
    # A central child may cover more than the robust fit's outlier fraction.
    # Start with the exposed outer band; children still have to pass complete
    # native containment and all local/global raster checks after fitting.
    exposed = (interior.astype(bool) & (distance > radius*.75)).astype('uint8')
    colors = _gradient(pixels, exposed, bounds, contract['axis'])
    if colors is None:
        return None
    coordinate = xx if contract['axis'] == 0 else yy
    t = (coordinate+.5-bounds[contract['axis']])/(2*radius)
    predicted = colors[:3] + t[..., None]*(colors[3:]-colors[:3])
    mask = ((np.max(abs(pixels.astype(float)-predicted), axis=2) > 25)
            & interior.astype(bool)).astype('uint8')
    number, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    children = []
    for index in range(1, number):
        x, y, w, h, area = stats[index]
        if area < 12:
            continue
        component = (labels == index).astype('uint8')
        contour = max(cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], key=cv2.contourArea)
        hull = cv2.convexHull(contour)
        polygon = cv2.approxPolyDP(hull, .025*cv2.arcLength(hull, True), True)
        if (len(polygon) != 4 or min(w, h) < 5 or area < .75*w*h):
            return None
        core = cv2.erode(component, np.ones((5, 5), 'uint8')).astype(bool)
        if not core.any():
            core = cv2.erode(component, np.ones((3, 3), 'uint8')).astype(bool)
        if not core.any():
            return None
        fill = np.median(pixels[core if core.any() else component.astype(bool)], axis=0)
        if np.percentile(np.max(abs(pixels[core].astype(float)-fill), axis=1), 80) > 12:
            return None  # These children assert flat paint, not arbitrary texture.
        sw = 1.5 if contract['outlined'] else 0.
        band = (cv2.dilate(component, np.ones((3, 3), 'uint8')).astype(bool)
                & ~cv2.erode(component, np.ones((5, 5), 'uint8')).astype(bool))
        samples = pixels[band]
        bright = samples.mean(axis=1) >= np.percentile(samples.mean(axis=1), 90)
        stroke = np.median(samples[bright], axis=0)
        if contract['outlined']:
            # A light rim can have the same color as the parent at one side
            # and strong contrast at the other. Seed its centerline from the
            # flat interior instead of this asymmetric residual silhouette.
            flat = ((np.max(abs(pixels.astype(float)-fill), axis=2) <= 25)
                    & cv2.dilate(component, np.ones((3, 3), 'uint8')).astype(bool)).astype('uint8')
            x, y, w, h = cv2.boundingRect(flat)
            horizontal = np.median(pixels[y+h//3:y+2*h//3].astype(float), axis=0)
            vertical = np.median(pixels[:, x+w//3:x+2*w//3].astype(float), axis=1)
            left_right = _flat_edge(horizontal, fill, stroke, x, x+w)
            top_bottom = _flat_edge(vertical, fill, stroke, y, y+h)
            if left_right is None or top_bottom is None:
                return None
            left, right = left_right
            top, bottom = top_bottom
            x, y, w, h = left-sw/2, top-sw/2, right-left+sw, bottom-top+sw
        else:
            x, y, w, h = x+.25, y+.25, w-.5, h-.5
        children.append(dict(kind='rectangle', geometry=np.array([x, y, w, h, sw]),
                             colors=np.r_[fill, fill, stroke]))
    if len(children) != contract['count']-1:
        return None
    children.sort(key=lambda obj: obj['geometry'][0])
    band = (distance >= radius-1) & (distance < radius)
    stroke = np.median(pixels[band], axis=0)
    geometry[4] = 1. if contract['outlined'] else 0.
    return [dict(kind='circle', geometry=geometry, colors=np.r_[colors, stroke]), *children]


def fit_mixed_gradient_scene(width, height, *, description, image, render_fn, error_fn):
    contract = scene_contract(description)
    pixels = np.asarray(image)
    if (contract is None or pixels.shape != (height, width, 3) or min(width, height) < 24
            or not np.isfinite(pixels).all()):
        return None
    objects = detect_instances(pixels, contract)
    if objects is None:
        return None
    n = len(objects)
    boxes = [np.r_[o['geometry'][:2], o['geometry'][:2]+o['geometry'][2:4], o['geometry'][4]]
             for o in objects]
    paint = [objects[0]['colors'], *[np.r_[o['colors'][:3], o['colors'][6:]] for o in objects[1:]]]
    offsets = [5*n, *[5*n+9+6*i for i in range(n-1)]]
    parameters = np.r_[np.concatenate(boxes),
                       np.concatenate(paint)]

    def geometry(p, index):
        x, y, X, Y, sw = p[5*index:5*index+5]
        w, h = X-x, Y-y
        if index == 0:
            y, h = (y+Y-w)/2, w
        return np.array([x, y, w, h, sw])

    def build(p):
        shapes = []
        colors = p[5*n:5*n+9]
        end = 'x2="100%" y2="0%"' if contract['axis'] == 0 else 'x2="0%" y2="100%"'
        definition = f'<defs><linearGradient id="scene_paint" x1="0%" y1="0%" {end}><stop offset="0" stop-color="{_hex(colors[:3])}"/><stop offset="1" stop-color="{_hex(colors[3:6])}"/></linearGradient></defs>'
        for i, obj in enumerate(objects):
            x, y, w, h, sw = geometry(p, i)
            c = p[offsets[i]:offsets[i]+(9 if i == 0 else 6)]
            fill = 'url(#scene_paint)' if i == 0 else _hex(c[:3])
            stroke = _hex(c[-3:]) if contract['outlined'] else 'none'
            style = f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.4f}"'
            if obj['kind'] == 'circle':
                shapes.append(f'<circle cx="{x+w/2:.4f}" cy="{y+h/2:.4f}" r="{w/2:.4f}" {style}/>')
            else:
                shapes.append(f'<rect x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}" {style}/>')
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'+definition+f'<rect width="{width}" height="{height}" fill="#ffffff"/>'+''.join(shapes)+'</svg>'

    def valid(p):
        from src.iCCModules.imageCompositeConverterLayeredScene import _contains
        scene = [dict(kind=o['kind'], geometry=geometry(p, i)) for i, o in enumerate(objects)]
        for i, obj in enumerate(scene):
            x, y, w, h, sw = obj['geometry']
            if min(w, h) < 4 or not (0 <= x < x+w <= width and 0 <= y < y+h <= height):
                return False
            if ((contract['outlined'] and not .5 <= sw <= min(w, h)/4)
                    or (not contract['outlined'] and sw != 0)):
                return False
            if i and not _contains(scene[0], obj):
                return False
            if contract['outlined']:
                c = np.clip(p[offsets[i]:offsets[i]+(9 if i == 0 else 6)], 0, 255)
                if c[-3:].mean() < 180 or (i and c[-3:].mean() < c[:3].mean()+15):
                    return False
        if len(scene) == 3:
            a, b = [s['geometry'] for s in scene[1:]]
            if a[0]+a[2]+a[4]/2 >= b[0]-b[4]/2:
                return False
        c = np.clip(np.rint(p[5*n:5*n+6]), 0, 255)
        if np.max(abs(c[3:]-c[:3])) < 8:
            return False
        return True

    regions = [(max(0, int(o['geometry'][0])-3), max(0, int(o['geometry'][1])-3),
                min(width, int(np.ceil(o['geometry'][0]+o['geometry'][2]))+3),
                min(height, int(np.ceil(o['geometry'][1]+o['geometry'][3]))+3)) for o in objects]

    def qualities(raster):
        return [_local_quality(pixels[y:Y, x:X], raster[y:Y, x:X]) for x, y, X, Y in regions]

    reference_gradients = [cv2.Sobel(pixels.astype('float32'), cv2.CV_32F, dx, dy)/8
                           for dx, dy in ((1, 0), (0, 1))]

    def loss(a, b):
        errors = np.mean((a.astype(float)-b.astype(float))**2, axis=2)
        # Thin light rims can trade width for paint with almost identical
        # area error. Image derivatives retain their observed edge profile.
        for reference, (dx, dy) in zip(reference_gradients, ((1, 0), (0, 1))):
            gradient = cv2.Sobel(b.astype('float32'), cv2.CV_32F, dx, dy)/8
            errors += 4*np.mean((reference-gradient)**2, axis=2)
        return float(np.mean([errors[y:Y, x:X].mean() for x, y, X, Y in regions]))

    fitted = _register(parameters, 5*n, build, valid, pixels, render_fn, error_fn,
                       'primitive_mixed_gradient_scene_v1', preserve_initial_error=True,
                       loss_fn=loss,
                       satisfactory_fn=lambda p, m: all(q and q['passed'] for q in qualities(m[3])))
    if fitted is None:
        return None
    quality = qualities(fitted['rendered'])
    if any(not q or not q['passed'] for q in quality):
        return None
    fitted.update(object_kinds=[o['kind'] for o in objects], object_quality=quality,
                  scene_hypotheses=1, instance_groups=n,
                  scene_detectors=['gradient_boundary', 'flat_residual_rectangles'],
                  neural_scene_selected=False)
    return fitted
