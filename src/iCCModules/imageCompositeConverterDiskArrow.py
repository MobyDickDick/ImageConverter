"""Fit a horizontal arrow inside a gradient disk from description and raster evidence."""
from __future__ import annotations

from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description, gradient_direction

import cv2
import numpy as np
import re

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image


def disk_arrow_direction(description):
    """Recognize a disk containing one horizontal shaft-and-head arrow."""
    text = normalize_description(description, orientations=True).casefold()
    if not gradient_direction(text, 'waagerecht'):
        return None
    text = re.sub(r'\bnach (?:links|rechts|oben|unten)(?: und (?:links|rechts|oben|unten))?\s+'
                  r'(?:verschoben|versetzt)\b', 'verschoben', text)
    directions = re.findall(r'pfeil\s+nach\s+(links|rechts|oben|unten)\b', text)
    if len(directions) != 1 or directions[0] not in ('links', 'rechts'):
        return None
    if not all(word in text for word in ('kreis', 'verlauf', 'pfeil',
                                         'schaft', 'dreieck', 'ohne lücke')):
        return None
    if any(word in text for word in ('nach oben', 'nach unten', 'zwei',
                                     'zusätzlich', 'ohne pfeil', 'beschriftung')):
        return None
    # Reject conflicting directions while allowing the disk's color gradient
    # and the whole motif's placement to have their own spatial description.
    if ('nach links' if directions[0] == 'rechts' else 'nach rechts') in text:
        return None
    return directions[0]


def validate_disk_arrow(root, direction):
    from src.iCCModules.imageCompositeConverterRepresentation import path_points
    from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform

    matrices = {}
    def visit(node, parent=(1., 0., 0., 1., 0., 0.)):
        matrix = _compose(parent, _transform(node.get('transform', '')))
        matrices[node] = matrix
        for child in node:
            visit(child, matrix)
    try:
        visit(root)
    except ValueError:
        return False

    def displayed(node):
        a, b, c, d, tx, ty = matrices[node]
        linear = np.array([[a, c], [b, d]])
        axes = np.linalg.svd(linear, compute_uv=False)
        if not np.isclose(axes[0], axes[1], rtol=1e-7) or axes[1] <= 0:
            raise ValueError('nonuniform_disk_arrow_transform')
        return linear, np.array([tx, ty]), float(axes[0])

    disks = [node for node in root.iter() if node.tag.rsplit('}', 1)[-1] == 'circle']
    arrows = [node for node in root.iter() if node.tag.rsplit('}', 1)[-1] == 'polygon']
    if len(disks) != 1 or len(arrows) != 1:
        return False
    disk, arrow = disks[0], arrows[0]
    paths = path_points(arrow)
    if len(paths) != 1 or len(paths[0][0]) != 7:
        return False
    try:
        disk_matrix, disk_offset, disk_scale = displayed(disk)
        arrow_matrix, arrow_offset, arrow_scale = displayed(arrow)
        points = paths[0][0] @ arrow_matrix.T+arrow_offset
        center = np.array([float(disk.get(axis, '0')) for axis in ('cx', 'cy')])
        center = disk_matrix @ center+disk_offset
        radius = float(disk.get('r', '0'))*disk_scale
        rim_width = float(disk.get('stroke-width', '1'))*disk_scale
        outline_width = float(arrow.get('stroke-width', '1'))*arrow_scale
    except ValueError:
        return False
    if (not np.isfinite(points).all() or not 0 < rim_width < radius
            or not 0 < outline_width < radius
            or disk.get('stroke', 'none') == 'none' or arrow.get('stroke', 'none') == 'none'
            or arrow.get('fill', 'black') == 'none'
            or not np.all(np.linalg.norm(points-center, axis=1) < radius)):
        return False
    if direction == 'rechts':
        points[:, 0] *= -1
    points = np.roll(points, -int(np.argmin(points[:, 0])), axis=0)
    if points[1, 1] > points[-1, 1]:
        points = points[[0, 6, 5, 4, 3, 2, 1]]
    tip, upper, shoulder, tail, base, lower, heel = points
    fill = disk.get('fill', '')
    gradient = next((node for node in root.iter()
                     if node.tag.rsplit('}', 1)[-1] == 'linearGradient'
                     and fill == f"url(#{node.get('id')})"), None)
    if gradient is None:
        return False
    try:
        ga, gb, gc, gd, _, _ = _transform(gradient.get('gradientTransform', ''))
        gradient_axis = disk_matrix @ np.array([ga, gb])
    except ValueError:
        return False
    return bool(gradient is not None
                and abs(gradient_axis[1]) <= 1e-7 and abs(gradient_axis[0]) > 1e-7
                and gradient.get('y1', '0') == gradient.get('y2', '0')
                and gradient.get('x1', '0') != gradient.get('x2', '1')
                and tip[0] < upper[0] < tail[0]
                and np.allclose(points[[1, 2, 5, 6], 0], upper[0])
                and np.isclose(tail[0], base[0])
                and np.isclose(shoulder[1], tail[1]) and np.isclose(lower[1], base[1])
                and upper[1] < shoulder[1] < tip[1] < lower[1] < heel[1])


def fit_disk_arrow(width, height, *, description, image, render_fn, error_fn):
    direction = disk_arrow_direction(description)
    if direction is None:
        return None
    rightward = direction == 'rechts'
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    # Work in a left-facing coordinate system. Render candidates directly in
    # the input's coordinates so the production renderer and error contract
    # still measure the actual output, including its original color field.
    if rightward:
        pixels = np.ascontiguousarray(pixels[:, ::-1])
    mask = (np.min(pixels, axis=2) < 235).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if count < 2:
        return None
    index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = stats[index]
    if not (.85 < w/h < 1.18 and area > .65*w*h):
        return None
    if sum(stats[i, cv2.CC_STAT_AREA] for i in range(1, count) if i != index) > max(3, area*.005):
        return None
    disk_mask = (labels == index).astype(np.uint8)
    contour = cv2.findContours(disk_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0][0][:, 0].astype(float) + .5
    coefficients = np.linalg.lstsq(np.c_[2*contour, np.ones(len(contour))],
                                   np.sum(contour**2, axis=1), rcond=None)[0]
    cx, cy = coefficients[:2]
    radius = float(np.sqrt(max(0., coefficients[2]+cx*cx+cy*cy)))
    if radius < 5 or np.mean(np.abs(np.linalg.norm(contour-[cx, cy], axis=1)-radius)) > max(.7, radius*.04):
        return None
    yy, xx = np.indices((height, width), dtype=float)
    distance = np.hypot(xx+.5-cx, yy+.5-cy)
    t = (xx+.5-(cx-radius))/(2*radius)
    exposed = (distance < radius*.88) & (np.abs(yy+.5-cy) > radius*.64)
    if exposed.sum() < 12:
        return None
    colors = np.linalg.lstsq(np.c_[1-t[exposed], t[exposed]], pixels[exposed], rcond=None)[0]
    if abs(colors[0].mean()-colors[1].mean()) <= 5:
        return None
    field = (1-t[..., None])*colors[0]+t[..., None]*colors[1]
    # A horizontal gradient does not prescribe its colour interpolation.
    # Estimate a second admissible fill from the same exposed original pixels.
    basis = np.stack((np.maximum(1-2*t, 0), 1-np.abs(2*t-1), np.maximum(2*t-1, 0)), axis=-1)
    three_colors = np.linalg.lstsq(basis[exposed], pixels[exposed], rcond=None)[0]
    three_field = basis @ three_colors
    if np.mean((three_field[exposed]-pixels[exposed])**2) < np.mean((field[exposed]-pixels[exposed])**2):
        field = three_field
    arrow_mask = ((np.mean(field-pixels, axis=2) > 35) & (distance < radius*.9)).astype(np.uint8)
    contrast_mask = arrow_mask.copy()
    # Pale antialiased outlines can isolate a one-pixel strip of the shaft.
    # Larger disconnected marks and gaps still fail the evidence checks.
    arrow_mask = cv2.morphologyEx(arrow_mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    count, arrow_labels, arrow_stats, _ = cv2.connectedComponentsWithStats(arrow_mask)
    if count < 2:
        return None
    index = 1 + int(np.argmax(arrow_stats[1:, cv2.CC_STAT_AREA]))
    bx, by, bw, bh, arrow_area = arrow_stats[index]
    if sum(arrow_stats[i, cv2.CC_STAT_AREA] for i in range(1, count) if i != index) > max(2, arrow_area*.01):
        return None
    arrow_mask = (arrow_labels == index).astype(np.uint8)
    columns = np.arange(bx, bx+bw)
    top = np.array([np.flatnonzero(arrow_mask[:, col])[0] for col in columns], dtype=float)
    bottom = np.array([np.flatnonzero(arrow_mask[:, col])[-1]+1 for col in columns], dtype=float)
    shoulder = int(np.argmax(bottom-top))
    if shoulder < 4 or bw-shoulder < 4:
        return None
    # Two sloped head edges meet at the left tip; the shaft has parallel edges.
    fit_indices = np.arange(1, shoulder)
    upper, lower = (np.polyfit(columns[fit_indices]+.5, edge[fit_indices], 1) for edge in (top, bottom))
    if not (upper[0] < -.2 and lower[0] > .2):
        return None
    if max(np.mean(np.abs(np.polyval(upper, columns[fit_indices]+.5)-top[fit_indices])),
           np.mean(np.abs(np.polyval(lower, columns[fit_indices]+.5)-bottom[fit_indices]))) > .8:
        return None
    tail_indices = np.arange(shoulder+2, bw-1)
    if len(tail_indices) < 2:
        return None
    shaft_top, shaft_bottom = (float(np.median(edge[tail_indices])) for edge in (top, bottom))
    if max(np.max(np.abs(top[tail_indices]-shaft_top)), np.max(np.abs(bottom[tail_indices]-shaft_bottom))) > 1:
        return None
    tip = (lower[1]-upper[1])/(upper[0]-lower[0])
    sy = (shaft_top+shaft_bottom)/2
    sx = float(columns[shoulder]+.5)
    head_half = (np.polyval(lower, sx)-np.polyval(upper, sx))/2
    shaft_half = (shaft_bottom-shaft_top)/2
    if not (head_half > shaft_half > 1 and abs(sy-cy) < radius*.18):
        return None
    core = cv2.erode(contrast_mask & arrow_mask, np.ones((3, 3), np.uint8)).astype(bool)
    if not core.any():
        return None
    fill = np.median(pixels[core], axis=0)
    if np.percentile(np.max(np.abs(pixels[core]-fill), axis=1), 95) > 25:
        return None
    outside = (distance < radius*.88) & ~cv2.dilate(arrow_mask, np.ones((5, 5), np.uint8)).astype(bool)
    if not outside.any() or np.percentile(np.max(np.abs(pixels[outside]-field[outside]), axis=1), 95) > 25:
        return None
    rim = np.median(pixels[(distance > radius*.94) & (distance < radius*1.01)], axis=0)
    edge = pixels[(cv2.dilate(arrow_mask, np.ones((3, 3), np.uint8))-arrow_mask).astype(bool)]
    outline = np.median(edge[edge.mean(axis=1) >= np.percentile(edge.mean(axis=1), 70)], axis=0)
    p = np.r_[cx, cy, radius-.3, 1., tip, sx, float(bx+bw), sy, head_half, shaft_half, .8,
              colors.ravel(), rim, fill, outline]

    def points(p):
        _, _, _, _, tip, shoulder, tail, center, head, shaft, _ = p[:11]
        return [(tip, center), (shoulder, center-head), (shoulder, center-shaft),
                (tail, center-shaft), (tail, center+shaft),
                (shoulder, center+shaft), (shoulder, center+head)]

    def build(p):
        cx, cy, r, sw = p[:4]
        light, dark, rim, fill, outline = p[11:26].reshape(-1, 3)
        arrow_points = points(p)
        if rightward:
            cx = width-cx
            arrow_points = [(width-x, y) for x, y in arrow_points]
        start, end = ('1', '0') if rightward else ('0', '1')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="disk_color" x1="{start}" y1="0" x2="{end}" y2="0">'
                f'<stop offset="0" stop-color="{_hex(light)}"/>'
                +(f'<stop offset="0.5" stop-color="{_hex(p[26:29])}"/>' if len(p) == 29 else '')+
                f'<stop offset="1" stop-color="{_hex(dark)}"/>'
                '</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="url(#disk_color)" stroke="{_hex(rim)}" stroke-width="{sw:.4f}"/>'
                '<polygon points="'+' '.join(f'{x:.4f},{y:.4f}' for x, y in arrow_points)+
                f'" fill="{_hex(fill)}" stroke="{_hex(outline)}" stroke-width="{p[10]:.4f}"/></svg>\n')

    def valid(p):
        cx, cy, r, sw, tip, shoulder, tail, center, head, shaft, outline = p[:11]
        return (r > 4 and .1 <= sw <= 3 and .1 <= outline <= 2.5
                and tip < shoulder < tail and head > shaft > 1
                and 0 <= cx-r-sw/2 and cx+r+sw/2 <= width
                and 0 <= cy-r-sw/2 and cy+r+sw/2 <= height
                and abs(center-cy) < r*.18
                and all((x-cx)**2+(y-cy)**2 < (r-sw/2-outline/2)**2 for x, y in points(p)))

    from xml.etree import ElementTree as ET
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
    from src.iCCModules.imageCompositeConverterFormModels import compare_form_models
    from src.iCCModules.imageCompositeConverterSearchPortfolio import settings

    assertions = description_assertions(description)
    def validate(svg):
        try:
            validate_svg_assertions(svg, assertions)
            return validate_disk_arrow(ET.fromstring(svg), direction)
        except ValueError:
            return False

    alternative = np.r_[p, three_colors[1]]
    alternative[11:17] = three_colors[[0, 2]].ravel()
    models = [dict(name=name, parameters=parameters, geometry_count=11, build=build, valid=valid)
              for name, parameters in [('two_stop', p), ('three_stop', alternative)]]
    config = settings()
    return compare_form_models(models, image=image, render_fn=render_fn, error_fn=error_fn,
        validate_fn=validate, source='raster_disk_arrow_v1',
        render_budget=min(417, config['budget']) if config else 417)
