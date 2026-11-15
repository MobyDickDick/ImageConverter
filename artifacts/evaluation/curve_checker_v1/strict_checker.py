"""Independent, conservative native SVG object/relation oracle.

No converter imports, detector results, SVG IDs or data-* roles are used. A pass
requires a complete external annotation, including background and hidden parts.
Unsupported SVG semantics fail closed; this is not a general SVG equivalence test.
"""
from __future__ import annotations

import math
import re
from xml.etree import ElementTree as ET

import numpy as np
from PIL import ImageColor

SCHEMA = 'independent_native_scene_v1'
NUMBER = r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?'
PAINT = {'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin'}
COMMON = PAINT | {'id', 'transform'}
GEOMETRY = {
    'line': {'x1', 'y1', 'x2', 'y2'},
    'rect': {'x', 'y', 'width', 'height'},
    'circle': {'cx', 'cy', 'r'},
    'polygon': {'points'},
}


def numbers(value):
    if re.sub(NUMBER, '', value).strip(' ,\t\r\n'):
        raise ValueError('Unsupported numeric syntax')
    result = [float(v) for v in re.findall(NUMBER, value)]
    if not result or not all(math.isfinite(v) and abs(v) <= 1e6 for v in result):
        raise ValueError('Nonfinite or excessive coordinate')
    return result


def scalar(value):
    values = numbers(str(value))
    if len(values) != 1:
        raise ValueError('Expected one number')
    return values[0]


def transform(value):
    result = np.eye(3)
    pattern = r'([a-zA-Z]+)\s*\(([^()]*)\)'
    if re.sub(pattern, '', value).strip(' ,\t\r\n'):
        raise ValueError('Malformed transform')
    for name, args in re.findall(pattern, value):
        v = numbers(args)
        matrix = np.eye(3)
        if name == 'translate' and len(v) in (1, 2):
            matrix[:2, 2] = [v[0], v[1] if len(v) == 2 else 0]
        elif name == 'scale' and len(v) in (1, 2):
            matrix[0, 0], matrix[1, 1] = v[0], v[-1]
        elif name == 'rotate' and len(v) in (1, 3):
            angle = math.radians(v[0])
            matrix[:2, :2] = [[math.cos(angle), -math.sin(angle)],
                              [math.sin(angle), math.cos(angle)]]
            if len(v) == 3:
                center = np.array(v[1:])
                matrix[:2, 2] = center-matrix[:2, :2]@center
        elif name == 'matrix' and len(v) == 6:
            matrix = np.array([[v[0], v[2], v[4]], [v[1], v[3], v[5]], [0, 0, 1.]])
        else:
            raise ValueError('Unsupported transform')
        result = result@matrix
    # Similarities give unambiguous native circles and stroke widths. Affine
    # shear/nonuniform scaling, including singular transforms, need another oracle.
    gram = result[:2, :2].T@result[:2, :2]
    if gram[0, 0] <= 1e-12 or not np.allclose(gram/gram[0, 0], np.eye(2), rtol=1e-8, atol=1e-8):
        raise ValueError('Only nonsingular similarity transforms supported')
    return result


def color(value):
    if value == 'none':
        return None
    try:
        rgb = ImageColor.getrgb(value)
        if len(rgb) != 3:
            raise ValueError('Alpha paint requires a separate oracle')
        return rgb
    except ValueError as exc:
        raise ValueError('Unsupported paint') from exc


def extract(svg, size):
    """Flatten group inheritance and similarities into pixel-space primitives."""
    if len(svg) > 200000 or '<!DOCTYPE' in svg.upper() or '<!ENTITY' in svg.upper():
        raise ValueError('Unsupported or excessive XML')
    root = ET.fromstring(svg)
    if root.tag != '{http://www.w3.org/2000/svg}svg':
        raise ValueError('SVG namespace required')
    width, height = size
    if [scalar(root.get('width', '0')), scalar(root.get('height', '0'))] != [width, height]:
        raise ValueError('Viewport differs from annotation')
    if numbers(root.get('viewBox', f'0 0 {width} {height}')) != [0, 0, width, height]:
        raise ValueError('Only pixel-space viewBox supported')
    objects = []

    def walk(node, matrix, inherited, depth=0):
        if depth > 24:
            raise ValueError('Excessive nesting')
        if not node.tag.startswith('{http://www.w3.org/2000/svg}'):
            raise ValueError('Unsupported element namespace')
        tag = node.tag.rsplit('}', 1)[-1]
        allowed = COMMON | (GEOMETRY.get(tag, set()))
        if node is root:
            allowed |= {'width', 'height', 'viewBox', 'version'}
        elif tag != 'g' and tag not in GEOMETRY:
            raise ValueError('Unsupported element: '+tag)
        if any(k not in allowed and not k.startswith('data-') for k in node.attrib):
            raise ValueError('Unsupported attribute on '+tag)
        matrix = matrix@transform(node.get('transform', ''))
        style = dict(inherited)
        style.update({k: v for k, v in node.attrib.items() if k in PAINT})
        if node is root or tag == 'g':
            if (node.text or '').strip() or any((child.tail or '').strip() for child in node):
                raise ValueError('Unexpected container text')
            for child in node:
                walk(child, matrix, style, depth+1)
            return
        if len(node) or (node.text or '').strip():
            raise ValueError('Unexpected primitive content')
        get = lambda key, default='0': scalar(node.get(key, default))
        if tag == 'line':
            points = [[get('x1'), get('y1')], [get('x2'), get('y2')]]
        elif tag == 'rect':
            x, y, w, h = [get(k) for k in ('x', 'y', 'width', 'height')]
            if w <= 0 or h <= 0:
                raise ValueError('Empty rectangle')
            points = [[x,y], [x+w,y], [x+w,y+h], [x,y+h]]
        elif tag == 'circle':
            if get('r') <= 0:
                raise ValueError('Empty circle')
            points = [[get('cx'), get('cy')]]
        else:
            values = numbers(node.get('points', ''))
            if len(values) < 6 or len(values) % 2 or len(values) > 128:
                raise ValueError('Invalid polygon')
            points = np.array(values).reshape(-1, 2)
        points = np.array(points, dtype=float)
        points = points@matrix[:2, :2].T+matrix[:2, 2]
        scale = float(np.linalg.norm(matrix[:2, 0]))
        stroke = color(style['stroke'])
        fill = None if tag == 'line' else color(style['fill'])
        stroke_width = scalar(style['stroke-width'])*scale
        if stroke_width < 0 or (fill is None and (stroke is None or stroke_width == 0)):
            raise ValueError('Invisible or invalid primitive')
        obj = dict(kind=tag, points=points.tolist(), fill=fill, stroke=stroke,
                   stroke_width=stroke_width if stroke is not None else 0.,
                   linecap=style['stroke-linecap'], linejoin=style['stroke-linejoin'], order=len(objects))
        if tag == 'circle':
            obj['radius'] = get('r')*scale
        objects.append(obj)
        if len(objects) > 48:
            raise ValueError('More than 48 native objects')

    walk(root, np.eye(3), dict(fill='black', stroke='none', **{
        'stroke-width': '1', 'stroke-linecap': 'butt', 'stroke-linejoin': 'miter'}))
    return objects


def point_error(a, b, kind):
    a, b = np.array(a), np.array(b)
    if a.shape != b.shape:
        return math.inf
    alternatives = [b]
    if kind == 'line':
        alternatives.append(b[::-1])
    elif kind in {'rect', 'polygon'}:
        alternatives = [np.roll(p, k, axis=0) for p in (b, b[::-1]) for k in range(len(b))]
    return min(float(np.linalg.norm(a-p, axis=1).max()) for p in alternatives)


def matches(actual, expected, limits):
    if actual['kind'] != expected['kind']:
        return False
    if point_error(actual['points'], expected['points'], actual['kind']) > limits['position']:
        return False
    if actual['kind'] == 'circle' and abs(actual['radius']-expected['radius']) > limits['position']:
        return False
    for key in ('fill', 'stroke'):
        a, b = actual[key], color(expected.get(key, 'none'))
        if (a is None) != (b is None) or (a is not None and max(abs(x-y) for x,y in zip(a,b)) > limits['color']):
            return False
    if actual['stroke'] is not None:
        if abs(actual['stroke_width']-expected.get('stroke_width', 1)) > limits['stroke_width']:
            return False
        if any(actual[k] != expected.get(k, default) for k,default in [('linecap','butt'), ('linejoin','miter')]):
            return False
    return True


def segment_distance(point, a, b):
    delta = b-a
    t = np.clip(np.dot(point-a, delta)/max(float(np.dot(delta, delta)), 1e-20), 0, 1)
    return float(np.linalg.norm(point-(a+t*delta)))


def boundary_distance(point, obj):
    points = np.array(obj['points'])
    if obj['kind'] == 'circle':
        return abs(float(np.linalg.norm(point-points[0]))-obj['radius'])
    pairs = zip(points, np.roll(points, -1, axis=0)) if obj['kind'] != 'line' else [(points[0], points[1])]
    return min(segment_distance(point,a,b) for a,b in pairs)


def relation_passes(relation, mapping, objects):
    a, b = [objects[mapping[name]] for name in relation['objects']]
    kind = relation['kind']
    if kind == 'front_of':
        return a['order'] > b['order']
    if kind == 'endpoint_on_boundary':
        return min(boundary_distance(p,b) for p in np.array(a['points'])) <= relation['tolerance']
    if kind == 'endpoints_on_boundaries':
        targets = [b, objects[mapping[relation['other']]]]
        points = np.array(a['points'])
        return any(all(boundary_distance(p,target) <= relation['tolerance'] for p,target in zip(points,order))
                   for order in (targets, targets[::-1]))
    if kind == 'crosses':
        p, q = np.array(a['points']); r, s = np.array(b['points'])
        cross = lambda u,v: float(u[0]*v[1]-u[1]*v[0])
        return cross(q-p,r-p)*cross(q-p,s-p) < 0 and cross(s-r,p-r)*cross(s-r,q-r) < 0
    raise ValueError('Unknown relation: '+kind)


def validate_annotation(annotation):
    if annotation.get('schema') != SCHEMA or annotation.get('complete_inventory') is not True:
        raise ValueError('Complete independent annotation required')
    size = annotation['size']
    if len(size) != 2 or any(not isinstance(v, int) or not 1 <= v <= 512 for v in size):
        raise ValueError('Invalid annotation size')
    limits = annotation['limits']
    for key, cap in [('position', 2), ('color', 16), ('stroke_width', .5)]:
        if not math.isfinite(limits[key]) or not 0 <= limits[key] <= cap:
            raise ValueError('Invalid annotation tolerance')
    expected = annotation['objects']
    ids = [obj['id'] for obj in expected]
    if not expected or len(expected) > 48 or len(set(ids)) != len(ids):
        raise ValueError('Unique nonempty object inventory required')
    by_id = dict(zip(ids, expected))
    for obj in expected:
        kind = obj['kind']
        pts = np.array(obj['points'], dtype=float)
        count = {'line': 2, 'rect': 4, 'circle': 1}.get(kind)
        if (kind not in GEOMETRY or pts.ndim != 2 or pts.shape[1] != 2
                or not np.isfinite(pts).all() or (count is not None and len(pts) != count)
                or (kind == 'polygon' and not 3 <= len(pts) <= 64)):
            raise ValueError('Invalid annotated geometry')
        if kind == 'circle' and (not math.isfinite(obj['radius']) or obj['radius'] <= 0):
            raise ValueError('Invalid annotated radius')
        for key in ('fill', 'stroke'):
            color(obj.get(key, 'none'))
        if obj.get('linecap','butt') not in {'butt','round','square'} or obj.get('linejoin','miter') not in {'miter','round','bevel'}:
            raise ValueError('Invalid annotated stroke style')
        if not math.isfinite(obj.get('stroke_width', 1)) or obj.get('stroke_width', 1) < 0:
            raise ValueError('Invalid annotated stroke')
    for rel in annotation['relations']:
        kind = rel['kind']
        names = rel['objects']
        if kind not in {'front_of','endpoint_on_boundary','endpoints_on_boundaries','crosses'} or len(names) != 2 or not set(names) <= set(ids):
            raise ValueError('Invalid annotated relation')
        if kind in {'endpoint_on_boundary','endpoints_on_boundaries','crosses'} and by_id[names[0]]['kind'] != 'line':
            raise ValueError('Relation requires a line')
        if kind == 'crosses' and by_id[names[1]]['kind'] != 'line':
            raise ValueError('Crossing requires two lines')
        if kind == 'endpoints_on_boundaries' and rel.get('other') not in ids:
            raise ValueError('Unknown second boundary')
        if kind in {'endpoint_on_boundary','endpoints_on_boundaries'} and not 0 <= scalar(rel['tolerance']) <= 1:
            raise ValueError('Invalid relation tolerance')


def check_scene(svg, annotation):
    """Return diagnostics; never promotes runtime models or unlocks holdouts."""
    try:
        validate_annotation(annotation)
        objects = extract(svg, annotation['size'])
        expected = annotation['objects']
        choices = {obj['id']: [i for i,actual in enumerate(objects) if matches(actual,obj,annotation['limits'])]
                   for obj in expected}
        report = dict(complete=False, supported=True, actual_count=len(objects), expected_count=len(expected),
                      unmatched_expected=[key for key,value in choices.items() if not value], mapping={}, relations=[])
        if len(objects) != len(expected) or report['unmatched_expected']:
            report['reason'] = 'object_inventory_or_geometry'
            return report
        # Bounded injective assignment. Never let two expected parts use one atom.
        ordered = sorted(choices, key=lambda key: len(choices[key]))
        visited = 0
        last_relations = []

        def assign(mapping, used):
            nonlocal visited, last_relations
            visited += 1
            if visited > 4096:
                return None
            if len(mapping) == len(ordered):
                last_relations = [dict(**rel, passed=bool(relation_passes(rel,mapping,objects))) for rel in annotation['relations']]
                if all(r['passed'] for r in last_relations):
                    return dict(mapping)
                return None
            name = ordered[len(mapping)]
            for index in choices[name]:
                if index not in used:
                    mapping[name] = index
                    result = assign(mapping, used | {index})
                    if result is not None:
                        return result
                    del mapping[name]
                if visited > 4096:
                    break
            return None

        mapping = assign({}, set())
        report.update(complete=mapping is not None, mapping=mapping or {}, relations=last_relations,
                      assignments_visited=visited, reason='passed' if mapping is not None else (
                          'assignment_limit' if visited > 4096 else 'assignment_or_relations'))
        return report
    except (ValueError, KeyError, TypeError, IndexError, ET.ParseError) as exc:
        return dict(complete=False, supported=False, reason=str(exc))
