"""Shared displayed widths for native strokes and thin rectangular linework.

Filled arbitrary paths do not expose a line width. General curved strokes under
nonuniform transforms cannot certify a constant width and are rejected here.
"""
from __future__ import annotations

import math
import re
from statistics import median
from xml.etree import ElementTree as ET

from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform
from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles


def _number(value):
    if not re.fullmatch(r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?(?:px)?', value.strip()):
        raise ValueError('unsupported_line_width_unit')
    result = float(value.strip().removesuffix('px'))
    if not math.isfinite(result):
        raise ValueError('invalid_line_width')
    return result


def width_bindings(root):
    """Return (node, dimension, displayed/local scale, width, center attribute).

    Stroked shape outlines count as linework. Unstroked rectangles with an
    aspect ratio greater than 3 count as straight shafts/bars, like the native
    arrow model. Changing a bar's width retains its center and length.
    """
    bindings = []
    shapes = {'line', 'path', 'polyline', 'polygon', 'rect', 'circle', 'ellipse'}
    excluded = {'defs', 'clipPath', 'mask', 'symbol', 'pattern', 'marker', 'metadata'}

    def visit(node, parent=(1., 0., 0., 1., 0., 0.), inherited=None, opacity=1.):
        kind = node.tag.rsplit('}', 1)[-1]
        if kind in excluded or node.get('display') == 'none':
            return
        if kind in {'use', 'image'} or kind == 'style':
            raise ValueError('unsupported_line_width_geometry')
        style = dict(inherited or dict(stroke='none', fill='black', **{
            'stroke-width': '1', 'stroke-opacity': '1', 'fill-opacity': '1', 'visibility': 'visible'}))
        for key in style:
            if node.get(key) is not None and node.get(key) != 'inherit':
                style[key] = node.get(key)
        opacity *= float(node.get('opacity', '1'))
        matrix = _compose(parent, _transform(node.get('transform', '')))
        a, b, c, d, _, _ = matrix
        determinant = abs(a*d-b*c)

        def scale(dx=None, dy=None):
            if dx is not None:
                length = math.hypot(dx, dy)
                transformed = math.hypot(a*dx+c*dy, b*dx+d*dy)
                if length == 0 or transformed == 0:
                    return 0.
                return determinant*length/transformed
            sx, sy = math.hypot(a, b), math.hypot(c, d)
            if not math.isclose(sx, sy, rel_tol=1e-7, abs_tol=1e-9) or abs(a*c+b*d) > 1e-7*max(sx*sy, 1e-9):
                raise ValueError('nonuniform_line_width_transform')
            return sx

        if kind in shapes and opacity > 0 and style['visibility'] not in {'hidden', 'collapse'}:
            stroked = (style['stroke'].lower() != 'none' and float(style['stroke-opacity']) > 0
                       and _number(style['stroke-width']) > 0)
            if stroked:
                width = _number(style['stroke-width'])
                if width > 0:
                    if node.get('vector-effect', 'none') != 'none':
                        raise ValueError('unsupported_line_width_vector_effect')
                    factor = (scale(_number(node.get('x2', '0'))-_number(node.get('x1', '0')),
                                    _number(node.get('y2', '0'))-_number(node.get('y1', '0')))
                              if kind == 'line' else scale())
                    if factor > 0:
                        bindings.append((node, 'stroke-width', factor, width, None))
            elif kind == 'rect' and style['fill'].lower() != 'none' and float(style['fill-opacity']) > 0:
                width, height = _number(node.get('width', '0')), _number(node.get('height', '0'))
                if min(width, height) > 0 and max(width, height) > 3*min(width, height):
                    vertical = height > width
                    factor = scale(0., 1.) if vertical else scale(1., 0.)
                    if factor > 0:
                        bindings.append((node, 'width' if vertical else 'height', factor,
                                         min(width, height), 'x' if vertical else 'y'))
        for child in node:
            visit(child, matrix, style, opacity)

    # With preserveAspectRatio=none, viewport scaling can change horizontal
    # and vertical widths differently even if all XML stroke-widths agree.
    parent = (1., 0., 0., 1., 0., 0.)
    if root.get('preserveAspectRatio', '').strip() == 'none' and root.get('viewBox'):
        view = [float(v) for v in re.split(r'[\s,]+', root.get('viewBox').strip())]
        if len(view) != 4 or min(view[2:]) <= 0:
            raise ValueError('invalid_line_width_viewport')
        parent = (_number(root.get('width', str(view[2])))/view[2], 0., 0.,
                  _number(root.get('height', str(view[3])))/view[3], 0., 0.)
    visit(root, parent)
    return bindings


def validate_equal_stroke_width(svg):
    root = ET.fromstring(inline_simple_svg_styles(svg))
    widths = [factor*width for _, _, factor, width, _ in width_bindings(root)]
    if widths and not math.isclose(min(widths), max(widths), rel_tol=1e-5, abs_tol=1e-5):
        raise ValueError('unequal_line_widths')


def constrain_stroke_width(svg, assertions, *, width=None):
    """Project native linework onto one shared width, only when requested."""
    if not assertions or not assertions.get('equal_stroke_width'):
        return svg
    root = ET.fromstring(inline_simple_svg_styles(svg))
    bindings = width_bindings(root)
    if not bindings:
        return svg
    shared = median(factor*value for _, _, factor, value, _ in bindings) if width is None else float(width)
    if not math.isfinite(shared) or shared <= 0:
        raise ValueError('invalid_line_width')
    # Keep rectangular shafts recognizable as linework throughout the search.
    # Otherwise widening a short bar could silently remove it from the check.
    for node, attribute, factor, _, center in bindings:
        if center:
            length = _number(node.get('height' if attribute == 'width' else 'width'))
            shared = min(shared, length/3*(1-1e-6)*factor)
    for node, attribute, factor, old, center in bindings:
        local = shared/factor
        node.set(attribute, f'{local:.9f}')
        if center:
            node.set(center, f'{_number(node.get(center, "0"))+(old-local)/2:.9f}')
    return ET.tostring(root, encoding='unicode')
