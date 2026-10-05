"""Register a circular pump body and one filled triangle from raster evidence."""
from __future__ import annotations

import copy
import re

import cv2
import numpy as np


def _color(bgr):
    return '#' + ''.join(f'{int(v):02x}' for v in np.clip(np.rint(bgr[::-1]), 0, 255))


def fit_pump_geometry(geometry_ir, *, image, description, render_fn, error_fn):
    """Infer colors/geometry, then accept only improving render comparisons.

    This deliberately narrow hypothesis requires an elliptical outer contour
    and a single, contrasting, approximately triangular region. Text, extra
    objects, and explicit directional contradictions cannot be fitted away.
    """
    kinds = [e.get('kind') for e in geometry_ir]
    if kinds != ['CircleBackground', 'PumpTriangleGlyph']:
        return None
    text = str(description).casefold()
    if any(word in text for word in ('text', 'beschrift', 'buchstab', 'griff', 'anschluss', 'verlauf')):
        return None
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape[2] != 3 or min(arr.shape[:2]) < 12:
        return None
    height, width = arr.shape[:2]
    foreground = (np.min(arr, axis=2) < 210).astype(np.uint8)
    contours, _ = cv2.findContours(foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    if len(contour) < 5 or cv2.contourArea(contour) < width*height*.2:
        return None
    (cx, cy), (diameter_a, diameter_b), _ = cv2.fitEllipse(contour)
    if not .85 <= diameter_a/diameter_b <= 1.18:
        return None
    # A circle remains a circle even if the contour fit's axes have rotated.
    radius = (diameter_a+diameter_b)/4
    points = contour[:, 0, :].astype(float)
    residual = np.abs(np.linalg.norm(points-[cx, cy], axis=1)-radius)
    if np.percentile(residual, 90) > max(1.5, radius*.08):
        return None
    yy, xx = np.indices((height, width))
    radial = np.hypot(xx-cx, yy-cy)/radius
    pixels = arr.astype(float)
    core = radial < .78
    values = pixels[core]
    # Deterministic two-color clustering; no global RNG or external templates.
    luminance = values.mean(axis=1)
    centers = np.array([values[np.argmin(luminance)], values[np.argmax(luminance)]])
    for _ in range(16):
        labels = np.argmin(np.sum((values[:, None]-centers)**2, axis=2), axis=1)
        if any(np.sum(labels == label) < 5 for label in (0, 1)):
            return None
        updated = np.array([np.median(values[labels == label], axis=0) for label in (0, 1)])
        if np.max(np.abs(updated-centers)) < .1:
            break
        centers = updated
    if np.linalg.norm(centers[0]-centers[1]) < 35:
        return None
    all_labels = np.argmin(np.sum((pixels[:, :, None]-centers)**2, axis=3), axis=2)
    triangles = []
    for label in (0, 1):
        mask = ((all_labels == label) & (radial < .91)).astype(np.uint8)
        regions, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for region in regions:
            hull = cv2.convexHull(region)
            polygon = cv2.approxPolyDP(hull, cv2.arcLength(hull, True)*.06, True)
            area = cv2.contourArea(polygon)
            if len(polygon) != 3 or not .12 < area/(np.pi*radius**2) < .55:
                continue
            if cv2.contourArea(region)/area < .8:
                continue
            triangles.append((area, label, polygon[:, 0, :].astype(float)))
    if len(triangles) != 1:
        return None
    _, triangle_label, vertices = triangles[0]
    # Absolute directions are hard constraints; historical relative rotation
    # prose is not reinterpreted as an absolute direction without a base pose.
    direction = re.search(r'(?:spitze|zeigt|weisend)[^.;]*?nach\s+(rechts|links|oben|unten)', text)
    if direction:
        axis = 0 if direction[1] in ('rechts', 'links') else 1
        sign = 1 if direction[1] in ('rechts', 'unten') else -1
        tip_index = np.argmax(sign*vertices[:, axis])
        base = np.delete(vertices, tip_index, axis=0)
        if abs(base[0, axis]-base[1, axis]) > radius*.2:
            return None
    outer = (radial > .9) & (radial < 1.02)
    stroke = np.median(pixels[outer], axis=0)
    params = [cx+.5, cy+.5, radius, max(.5, radius*.06), *vertices.reshape(-1)+.5]
    colors = [centers[1-triangle_label], stroke, centers[triangle_label]]

    def build(p, palette):
        x, y, r, sw = p[:4]
        result = copy.deepcopy(geometry_ir)
        result[0].update(bbox=[(x-r)/width, (y-r)/height, 2*r/width, 2*r/height],
                         fill=_color(palette[0]), stroke=_color(palette[1]), stroke_width=sw/min(width, height))
        result[1].update(points=[[float((px-(x-r))/(2*r)), float((py-(y-r))/(2*r))]
                                 for px, py in np.asarray(p[4:]).reshape(3, 2)], fill=_color(palette[2]),
                         source='raster_circle_triangle_v1')
        return result

    def measure(p, palette):
        x, y, r, sw = p[:4]
        verts = np.asarray(p[4:]).reshape(3, 2)
        if r <= 2 or sw < 0 or sw > r*.25 or np.any(np.linalg.norm(verts-[x,y], axis=1) > r*1.03):
            return None
        candidate = build(p, palette)
        rendered = render_fn(candidate)
        return None if rendered is None else (float(error_fn(rendered)), candidate, rendered)

    best = measure(params, colors)
    if best is None:
        return None
    initial_error = best[0]
    for step in (1., .5, .25):
        for index in range(len(params)):
            for delta in (-step, step):
                candidate = params.copy()
                candidate[index] += delta
                measured = measure(candidate, colors)
                if measured is not None and measured[0] < best[0]-1e-9:
                    params, best = candidate, measured
    for step in (16., 8., 4.):
        for color_index in range(3):
            for channel in range(3):
                for delta in (-step, step):
                    palette = [color.copy() for color in colors]
                    palette[color_index][channel] = np.clip(palette[color_index][channel]+delta, 0, 255)
                    measured = measure(params, palette)
                    if measured is not None and measured[0] < best[0]-1e-9:
                        colors, best = palette, measured
    return {'geometry_ir': best[1], 'rendered': best[2], 'final_error': best[0],
            'initial_error': initial_error, 'source': 'raster_circle_triangle_v1'}
