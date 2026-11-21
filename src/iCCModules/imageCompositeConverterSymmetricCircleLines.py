"""Fit only the circle and mirrored pair of lines declared by the description."""
from __future__ import annotations

import re
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality, vector_quality_score
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def symmetric_circle_lines_spec(description):
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description
    text = ' '.join(normalize_description(description).casefold().split())
    match = re.fullmatch(
        r'(?:es ist ein |ein )grauer kreis mit grauem rand[.;] '
        r'im kreis sind zwei dunkelgraue linien enthalten, '
        r'(?:welche|welches|die) symmetrisch in bezug auf die '
        r'(?P<axis>horizontale|waagerechte|vertikale|senkrechte) symmetrieachse des kreises sind[.;]?', text)
    if match:
        return dict(axis='horizontal' if match['axis'] in {'horizontale', 'waagerechte'} else 'vertical')
    return None


def validate_symmetric_circle_lines(svg, spec):
    """Check the same relations after template transforms and later refinement."""
    from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform
    from src.iCCModules.imageCompositeConverterRepresentation import EXCLUDED
    from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles
    circles, lines = [], []

    def visit(node, parent=(1., 0., 0., 1., 0., 0.)):
        kind = node.tag.rsplit('}', 1)[-1]
        if kind in EXCLUDED:
            return
        matrix = _compose(parent, _transform(node.get('transform', '')))
        a, b, c, d, tx, ty = matrix
        def mapped(points):
            return np.asarray(points) @ np.array([[a, b], [c, d]]) + [tx, ty]
        if kind == 'circle':
            sx, sy = np.hypot(a, b), np.hypot(c, d)
            if not np.isclose(sx, sy) or not np.isclose(a*c+b*d, 0.):
                raise ValueError('symmetric_circle_lines:deformed_circle')
            circles.append((mapped([[float(node.get('cx', '0')), float(node.get('cy', '0'))]])[0],
                            float(node.get('r', '0'))*sx))
        elif kind == 'line':
            lines.append(mapped([[float(node.get('x1', '0')), float(node.get('y1', '0'))],
                                 [float(node.get('x2', '0')), float(node.get('y2', '0'))]]))
        for child in node:
            visit(child, matrix)
    visit(ET.fromstring(inline_simple_svg_styles(svg)))
    if len(circles) != 1 or len(lines) != 2:
        raise ValueError('symmetric_circle_lines:incomplete')
    center, radius = circles[0]
    tolerance = max(1e-4, radius*1e-5)
    if radius <= 0 or any(np.linalg.norm(line[1]-line[0]) < tolerance
                          or np.max(np.linalg.norm(line-center, axis=1)) > radius+tolerance for line in lines):
        raise ValueError('symmetric_circle_lines:outside_circle')
    reflection = lines[0].copy()
    axis = 1 if spec['axis'] == 'horizontal' else 0
    reflection[:, axis] = 2*center[axis]-reflection[:, axis]
    if not any(np.allclose(reflection, other, atol=tolerance, rtol=0.) for other in (lines[1], lines[1][::-1])):
        raise ValueError('symmetric_circle_lines:wrong_symmetry')
    if any(np.allclose(lines[0], other, atol=tolerance, rtol=0.) for other in (lines[1], lines[1][::-1])):
        raise ValueError('symmetric_circle_lines:duplicate_line')


def fit_symmetric_circle_lines(width, height, *, description, image, render_fn, error_fn):
    spec = symmetric_circle_lines_spec(description)
    pixels = _image(width, height, image)
    if spec is None or pixels is None:
        return None
    gray = pixels.mean(axis=2)
    background = np.median(np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1])), axis=0)
    mask = (np.max(abs(pixels-background), axis=2) > 18).astype('uint8')
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)[:, 0].astype(float)+.5
    if len(contour) < 16:
        return None
    coef = np.linalg.lstsq(np.c_[2*contour, np.ones(len(contour))], (contour**2).sum(axis=1), rcond=None)[0]
    center = coef[:2]
    outer = np.sqrt(max(0., coef[2]+center@center))
    if outer < 4 or np.mean(abs(np.linalg.norm(contour-center, axis=1)-outer)) > max(.8, outer*.06):
        return None
    yy, xx = np.indices(gray.shape, dtype=float)+.5
    radial = np.hypot(xx-center[0], yy-center[1])
    interior = radial < outer*.88
    fill = np.percentile(pixels[interior], 85, axis=0)
    marks = interior & (gray < fill.mean()-25)
    axis = 1 if spec['axis'] == 'horizontal' else 0
    marks &= (yy if axis else xx) < center[axis]-outer*.12
    y, x = np.nonzero(marks)
    if len(x) < 5:
        return None
    points = np.c_[x+.5, y+.5]
    vx, vy, px, py = cv2.fitLine(points.astype('float32'), cv2.DIST_HUBER, 0, .01, .01).ravel()
    direction = np.array([vx, vy], dtype=float)
    closest = np.array([px, py])-center
    closest -= (closest@direction)*direction
    radius = min(outer, center[0], width-center[0], center[1], height-center[1])-.5
    distance = np.sqrt(max(0., (radius-.5)**2-closest@closest))
    endpoints = np.array([closest-distance*direction, closest+distance*direction])+center
    rim = np.percentile(pixels[(radial > outer-1.5) & (radial < outer+.5)], 15, axis=0)
    ink = np.percentile(pixels[y, x], 15, axis=0)
    # Circle, line widths and one free segment. Reflection defines the other;
    # neither pixels nor optimization can introduce additional objects.
    initial = np.r_[center, radius, 1., 1., (endpoints-center).ravel(), fill.mean(), rim.mean(), ink.mean()]

    def build(p):
        cx, cy, radius, sw, lw = p[:5]
        first = p[5:9].reshape(2, 2)+[cx, cy]
        second = first.copy()
        second[:, axis] = 2*p[axis]-second[:, axis]
        fill, rim, ink = [np.repeat(shade, 3) for shade in p[9:]]
        lines = ''.join(f'<line x1="{a[0]:.5f}" y1="{a[1]:.5f}" x2="{b[0]:.5f}" y2="{b[1]:.5f}" '
                        f'stroke="{_hex(ink)}" stroke-width="{lw:.5f}" stroke-linecap="round"/>'
                        for a, b in (first, second))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<rect width="{width}" height="{height}" fill="{_hex(background)}"/>'
                f'<circle cx="{cx:.5f}" cy="{cy:.5f}" r="{radius:.5f}" '
                f'fill="{_hex(fill)}" stroke="{_hex(rim)}" stroke-width="{sw:.5f}"/>'+lines+'</svg>')

    def valid(p):
        cx, cy, radius, sw, lw = p[:5]
        first = p[5:9].reshape(2, 2)
        return (np.isfinite(p).all() and radius > 3 and .25 <= min(sw, lw) <= max(sw, lw) < radius*.4
                and radius+sw/2 <= min(cx, width-cx, cy, height-cy)+1e-7
                and np.max(np.linalg.norm(first, axis=1)) <= radius
                and np.linalg.norm(first[1]-first[0]) > radius*.25
                and np.all((p[9:] >= 0) & (p[9:] <= 255)))

    result = _register(initial, 9, build, valid, image, render_fn, error_fn,
                       'description_symmetric_circle_lines_v1', allow_portfolio=False,
                       max_evaluations=1800, reconsider_after=0,
                       refinement_steps=(1., .5, .25, .125, .0625, .03125))
    if result is not None and not pixel_quality(image, result['rendered'])['passed']:
        def quality_loss(a, b):
            quality = pixel_quality(a, b)
            return (float(not quality['passed'])+1-quality['foreground_iou']
                    +.1*quality['normalized_mse']+.05*(1-quality['edge_alignment']))
        refined = _register(result['parameters'], 9, build, valid, image, render_fn, error_fn,
                            'description_symmetric_circle_lines_quality', allow_portfolio=False,
                            max_evaluations=900, reconsider_after=0, loss_fn=quality_loss,
                            initial_error_bound=result['initial_error'],
                            refinement_steps=(.5, .25, .125, .0625, .03125))
        if refined is not None:
            total_evaluations = result['evaluations']+refined['evaluations']
            before, after = pixel_quality(image, result['rendered']), pixel_quality(image, refined['rendered'])
            if (not after['passed'], vector_quality_score(after)) < (not before['passed'], vector_quality_score(before)):
                result = refined
            result['evaluations'] = total_evaluations
    if result is not None:
        validate_symmetric_circle_lines(result['svg'], spec)
        result['quality'] = pixel_quality(image, result['rendered'])
    return result
