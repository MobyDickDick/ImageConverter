"""Shape-scoped paint claims shared by search, templates and final validation."""
from __future__ import annotations

import math
import re
from xml.etree import ElementTree as ET

import numpy as np

NOUNS = dict(circle='kreise', ellipse='ellipsen', rect='rechtecke',
             square='quadrate', triangle='dreiecke')


def scoped_paint_claims(text):
    """Consume complete supported clauses; retain unknown claims for rejection."""
    claims = []
    rest = text
    for kind, noun in NOUNS.items():
        subject = r'\b(?:beide|die beiden|alle|sämtliche)\s+' + noun + r'\s+haben\s+'
        patterns = (
            ('equal_stroke', subject + r'(?:(?:jeweils|je)\s+)?gleich\s+(?:breite|dicke|starke)\s+ränder'),
            ('gradient', subject + r'(?:(?:jeweils|je)\s+)?einen\s+(?:farbverlauf|farbübergang)'
             r'(?:\s*\(\s*(hellgrau)\s+nach\s+(dunkelgrau)\s*\))?'),
        )
        for claim, pattern in patterns:
            # Match only whole sentences, not the prefix of a qualified claim.
            expression = pattern + r'\s*(?=[.!;\n]|$)'
            def consume(match):
                entry = dict(kind=kind, claim=claim)
                if claim == 'gradient' and match[1]:
                    entry['gray_light_to_dark'] = True
                claims.append(entry)
                return ' '
            rest = re.sub(expression, consume, rest)
    return claims, rest


def constrain_parameters(program, parameters):
    """Project only explicitly declared paint relationships, without raster data."""
    from src.iCCModules.imageCompositeConverterSceneProgram import STRIDE
    values = np.asarray(parameters).reshape(len(program['objects']), STRIDE).copy()
    for claim in program.get('paint_claims', []):
        indices = [i for i, obj in enumerate(program['objects']) if obj['kind'] == claim['kind']]
        if not indices:
            continue
        if claim['claim'] == 'equal_stroke':
            values[indices, 5] = values[indices[0], 5]
        else:
            values[indices, 15] = 1.
            if claim.get('gray_light_to_dark'):
                for i in indices:
                    light = np.clip(values[i, 6:9].mean(), .56, .94)
                    dark = np.clip(values[i, 12:15].mean(), .16, min(.74, light-.06))
                    values[i, 6:9] = light
                    values[i, 12:15] = dark
    return values.ravel()


def validate_scoped_paint(svg, claims):
    if not claims:
        return
    from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles
    from src.iCCModules.imageCompositeConverterRepresentation import path_points, EXCLUDED
    from src.iCCModules.imageCompositeConverterStrokeConstraints import width_bindings
    root = ET.fromstring(inline_simple_svg_styles(svg))
    widths = {id(node): factor*width for node, attr, factor, width, _ in width_bindings(root)
              if attr == 'stroke-width'}
    gradients = {node.get('id'): node for node in root.iter()
                 if node.tag.rsplit('}', 1)[-1] == 'linearGradient'}
    shapes = []

    def visit(node, inherited=None):
        tag = node.tag.rsplit('}', 1)[-1]
        if tag in EXCLUDED or node.get('display') == 'none':
            return
        style = dict(inherited or {'fill': 'black', 'fill-opacity': '1', 'opacity': '1'})
        for key in style:
            if node.get(key) is not None:
                style[key] = node.get(key)
        kind = tag
        if tag in {'polygon', 'path'}:
            paths = path_points(node)
            if len(paths) == 1 and paths[0][1]:
                points = paths[0][0]
                if len(points) > 3 and np.allclose(points[0], points[-1]):
                    points = points[:-1]
                if len(points) == 3:
                    kind = 'triangle'
        if tag == 'rect' and node.get('width') == node.get('height'):
            kind = 'square'
        background = (tag == 'rect' and node.get('stroke', 'none') == 'none'
                      and node.get('width') == root.get('width') and node.get('height') == root.get('height')
                      and float(node.get('x','0')) == 0 and float(node.get('y','0')) == 0)
        if not background and kind in NOUNS:
            shapes.append((kind, node, style))
        for child in node:
            visit(child, style)
    visit(root)
    for claim in claims:
        selected = [(node, style) for kind, node, style in shapes
                    if kind == claim['kind'] or (claim['kind'] == 'rect' and kind == 'square')]
        if not selected:
            raise ValueError('scoped_paint:missing_objects')
        if claim['claim'] == 'equal_stroke':
            actual = [widths.get(id(node), 0.) for node, _ in selected]
            if min(actual) <= 0 or not math.isclose(min(actual), max(actual), rel_tol=1e-5, abs_tol=1e-5):
                raise ValueError('scoped_paint:unequal_borders')
            continue
        for node, style in selected:
            match = re.fullmatch(r'url\(#([^)]*)\)', style['fill'])
            gradient = gradients.get(match[1]) if match else None
            if (gradient is None or float(style['fill-opacity']) <= 0 or float(style['opacity']) <= 0
                    or gradient.get('href') or gradient.get('{http://www.w3.org/1999/xlink}href')):
                raise ValueError('scoped_paint:missing_gradient')
            stops = [stop for stop in gradient if stop.tag.rsplit('}', 1)[-1] == 'stop']
            colors = []
            offsets = []
            for stop in stops:
                color = stop.get('stop-color', '')
                if not re.fullmatch(r'#[0-9a-fA-F]{6}', color) or float(stop.get('stop-opacity', '1')) <= 0:
                    raise ValueError('scoped_paint:unsupported_gradient_stop')
                colors.append(np.array([int(color[i:i+2], 16)/255 for i in (1, 3, 5)]))
                offset=stop.get('offset','0')
                offsets.append(float(offset.removesuffix('%'))/(100 if offset.endswith('%') else 1))
            if len(colors) < 2 or np.max(np.ptp(colors, axis=0)) < .05:
                raise ValueError('scoped_paint:constant_gradient')
            if not 0 <= offsets[0] < offsets[-1] <= 1 or any(a>b for a,b in zip(offsets,offsets[1:])):
                raise ValueError('scoped_paint:degenerate_gradient')
            def coordinate(key,default):
                value=gradient.get(key,default)
                return float(value.removesuffix('%'))/(100 if value.endswith('%') else 1)
            start=[coordinate('x1','0'),coordinate('y1','0')]
            end=[coordinate('x2','1'),coordinate('y2','0')]
            if np.allclose(start,end,rtol=0,atol=1e-12):
                raise ValueError('scoped_paint:degenerate_gradient')
            if claim.get('gray_light_to_dark'):
                light, dark = colors[0], colors[-1]
                if (max(np.ptp(light), np.ptp(dark)) > .02 or light.mean() < .55
                        or light.mean() > .95 or dark.mean() < .15 or dark.mean() > .75
                        or light.mean()-dark.mean() < .05):
                    raise ValueError('scoped_paint:wrong_gradient_colors')
