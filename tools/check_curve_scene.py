"""Independent, bounded oracle for single native Q/C/A curve objects.

External construction data, never Runtime roles or raster similarity, defines
the inventory. Hidden curves must be present in full. No curve tessellation,
path splitting or equivalence to a different primitive is inferred.
"""
from __future__ import annotations

import copy
import math
import re
from xml.etree import ElementTree as ET

import numpy as np

from tools import check_native_scene as native

SCHEMA = 'independent_curve_scene_v1'
CURVES = {'quadratic', 'cubic', 'arc'}
WORK_LIMIT = 4096
NS = '{http://www.w3.org/2000/svg}'


def ellipse_point(center, radii, rotation, angle):
    phi, theta = math.radians(rotation), math.radians(angle)
    axes = np.array([[math.cos(phi), -math.sin(phi)], [math.sin(phi), math.cos(phi)]])
    return np.array(center)+axes@(np.array(radii)*[math.cos(theta), math.sin(theta)])


def ellipse_shape(radii, rotation):
    phi = math.radians(rotation)
    axes = np.array([[math.cos(phi), -math.sin(phi)], [math.sin(phi), math.cos(phi)]])
    # The positive square root of the ellipse's covariance, in length units.
    return axes@np.diag(radii)@axes.T


def parse_curve(value):
    # Separate command letters without treating numeric exponents as commands.
    tokens = re.findall(native.NUMBER+r'|[A-Za-z]', value)
    if re.sub(native.NUMBER+r'|[A-Za-z]', '', value).strip(' ,\t\r\n'):
        raise ValueError('Unsupported curve syntax')
    if len(tokens) < 5 or tokens[0] not in {'M', 'm'} or tokens[3] not in set('QqCcAa'):
        raise ValueError('One explicit M and one Q/C/A required')
    # Validate all numbers with the strict bounded numeric parser.
    start = np.array(native.numbers(' '.join(tokens[1:3])))
    command = tokens[3]
    values = native.numbers(' '.join(tokens[4:]))
    needed = {'q': 4, 'c': 6, 'a': 7}[command.lower()]
    if len(start) != 2 or len(values) != needed:
        raise ValueError('Exactly one curve segment required')
    if command.lower() in {'q', 'c'}:
        points = np.array(values).reshape(-1, 2)
        if command.islower():
            points += start
        points = np.vstack([start, points])
        chord = points[-1]-points[0]
        if np.linalg.norm(chord) < 1e-8 or max(abs(chord[0]*(p-start)[1]-chord[1]*(p-start)[0])
                                             for p in points[1:-1]) < 1e-8:
            raise ValueError('Degenerate Bezier curve')
        return dict(kind='quadratic' if command.lower() == 'q' else 'cubic', points=points.tolist())
    rx, ry, rotation, large, sweep, x, y = values
    if min(rx, ry) < 1e-6 or tokens[7] not in {'0', '1'} or tokens[8] not in {'0', '1'}:
        raise ValueError('Positive radii and literal binary arc flags required')
    end = np.array([x, y])+(start if command.islower() else 0)
    if np.linalg.norm(end-start) < 1e-8:
        raise ValueError('Coincident arc endpoints unsupported')
    phi = math.radians(rotation % 360)
    axes = np.array([[math.cos(phi), -math.sin(phi)], [math.sin(phi), math.cos(phi)]])
    local = axes.T@((start-end)/2)
    radii = np.array([rx, ry])
    reach = float(np.sum((local/radii)**2))
    # SVG endpoint arcs enlarge insufficient radii, rather than changing endpoints.
    if reach > 1:
        radii *= math.sqrt(reach)
    if max(radii) > 1e6:
        raise ValueError('Excessive corrected arc radius')
    rx, ry = radii
    denominator = (rx*local[1])**2+(ry*local[0])**2
    factor = math.sqrt(max(0., ((rx*ry)**2-denominator)/denominator))
    if large == sweep:
        factor = -factor
    local_center = factor*np.array([rx*local[1]/ry, -ry*local[0]/rx])
    center = axes@local_center+(start+end)/2
    u, v = (local-local_center)/radii, (-local-local_center)/radii
    theta = math.atan2(u[1], u[0])
    delta = math.atan2(u[0]*v[1]-u[1]*v[0], float(u@v))
    if sweep and delta < 0:
        delta += 2*math.pi
    elif not sweep and delta > 0:
        delta -= 2*math.pi
    middle = center+axes@(radii*[math.cos(theta+delta/2), math.sin(theta+delta/2)])
    tangents = []
    for angle, sign in [(theta, 1), (theta+delta, -1)]:
        tangents.append((axes@(radii*[-math.sin(angle), math.cos(angle)])
                         *math.copysign(1, delta)*sign).tolist())
    return dict(kind='arc', points=[start.tolist(), end.tolist()], center=center.tolist(),
                shape=ellipse_shape(radii, rotation).tolist(), middle=middle.tolist(),
                sweep=math.degrees(delta), tangents=tangents)


def extract(svg, size):
    if len(svg) > 200000 or '<!DOCTYPE' in svg.upper() or '<!ENTITY' in svg.upper():
        raise ValueError('Unsupported or excessive XML')
    root = ET.fromstring(svg)
    curves = {}
    order = 0

    def walk(node, matrix, fill, depth=0):
        nonlocal order
        if depth > 24:
            raise ValueError('Excessive nesting')
        matrix = matrix@native.transform(node.get('transform', ''))
        fill = node.get('fill', fill)
        if node.tag in {NS+'svg', NS+'g'}:
            for child in node:
                walk(child, matrix, fill, depth+1)
            return
        if node.tag == NS+'path':
            if any(k not in native.COMMON | {'d'} and not k.startswith('data-') for k in node.attrib):
                raise ValueError('Unsupported attribute on path')
            if native.color(fill) is not None:
                raise ValueError('Only unfilled stroked curves supported')
            curve = parse_curve(node.attrib.pop('d'))
            linear, shift = matrix[:2, :2], matrix[:2, 2]
            curve['points'] = (np.array(curve['points'])@linear.T+shift).tolist()
            if curve['kind'] == 'arc':
                for key in ('center', 'middle'):
                    curve[key] = (linear@curve[key]+shift).tolist()
                scale = float(np.linalg.norm(linear[:, 0]))
                orthogonal = linear/scale
                curve['shape'] = (scale*orthogonal@curve['shape']@orthogonal.T).tolist()
                curve['tangents'] = (np.array(curve['tangents'])@linear.T).tolist()
                curve['sweep'] *= math.copysign(1, np.linalg.det(linear))
            curves[order] = curve
            # Reuse the unchanged strict parser for paint, XML, inheritance and
            # all straight objects. Proxy endpoints are only style carriers.
            node.tag = NS+'line'
            for key, value in zip(('x1', 'y1', 'x2', 'y2'), (0, 0, 1, 1)):
                node.set(key, str(value))
        order += 1

    walk(root, np.eye(3), 'black')
    objects = native.extract(ET.tostring(root, encoding='unicode'), size)
    for index, curve in curves.items():
        objects[index].update(curve)
    return objects


def endpoints(obj):
    return np.array([obj['points'][0], obj['points'][-1]])


def tangents(obj):
    if obj['kind'] == 'arc':
        return np.array(obj['tangents'])
    pts = np.array(obj['points'])
    # Inward tangents; zero first derivatives use the first noncoincident control.
    result = []
    for points in (pts, pts[::-1]):
        result.append(next(p-points[0] for p in points[1:] if np.linalg.norm(p-points[0]) > 1e-10))
    return np.array(result)


def validate_annotation(annotation):
    if annotation.get('schema') != SCHEMA:
        raise ValueError('Independent curve annotation required')
    strict = copy.deepcopy(annotation)
    strict['schema'] = native.SCHEMA
    by_id = {o['id']: o for o in annotation['objects']}
    for original, obj in zip(annotation['objects'], strict['objects']):
        if original.get('representation') is not None:
            raise ValueError('Curve partition or omission is not authorized')
        kind = obj['kind']
        if kind not in CURVES:
            continue
        points = np.array(obj['points'], dtype=float)
        count = {'quadratic': 3, 'cubic': 4, 'arc': 2}[kind]
        if points.shape != (count, 2) or not np.isfinite(points).all() or np.max(abs(points)) > 1e6:
            raise ValueError('Invalid annotated curve geometry')
        if np.linalg.norm(points[-1]-points[0]) < 1e-8:
            raise ValueError('Degenerate annotated curve')
        if native.color(obj.get('fill', 'none')) is not None or native.color(obj.get('stroke', 'none')) is None or obj.get('stroke_width', 1) <= 0:
            raise ValueError('Visible unfilled annotated curve required')
        if kind == 'arc':
            values = [*obj['center'], *obj['radii'], obj['rotation'], obj['start_angle'], obj['sweep']]
            if (len(obj['center']) != 2 or len(obj['radii']) != 2
                    or not all(math.isfinite(v) and abs(v) <= 1e6 for v in values)
                    or min(obj['radii']) <= 0 or not 1e-6 < abs(obj['sweep']) < 360):
                raise ValueError('Invalid annotated arc')
            arc_points = [ellipse_point(obj['center'], obj['radii'], obj['rotation'], angle)
                          for angle in [obj['start_angle'], obj['start_angle']+obj['sweep']]]
            if np.max(np.linalg.norm(points-arc_points, axis=1)) > 1e-6:
                raise ValueError('Annotated arc endpoints disagree with ellipse')
        obj['kind'], obj['points'] = 'line', endpoints(original).tolist()
    strict['relations'] = []
    for relation in annotation['relations']:
        kind, names = relation['kind'], relation['objects']
        if kind in {'endpoints_meet', 'tangent_join'}:
            if (len(names) != 2 or len(set(names)) != 2 or not set(names) <= set(by_id)
                    or any(by_id[n]['kind'] not in CURVES | {'line'} for n in names)
                    or not 0 <= native.scalar(relation['tolerance']) <= 1):
                raise ValueError('Invalid annotated curve connection')
            if kind == 'tangent_join' and not 0 <= native.scalar(relation['angle_tolerance']) <= 1:
                raise ValueError('Invalid tangent tolerance')
        else:
            if kind != 'front_of' and by_id[names[1]]['kind'] in CURVES:
                raise ValueError('Curved boundary relation requires a separate oracle')
            if kind == 'endpoints_on_boundaries' and by_id[relation['other']]['kind'] in CURVES:
                raise ValueError('Curved boundary relation requires a separate oracle')
            if kind == 'crosses' and any(by_id[n]['kind'] in CURVES for n in names):
                raise ValueError('Curve intersections unsupported')
            strict['relations'].append(relation)
    native.validate_annotation(strict)
    if not 0 <= native.scalar(annotation['limits']['angle']) <= .25:
        raise ValueError('Invalid arc angle tolerance')


def matches(actual, expected, limits):
    kind = expected['kind']
    if kind not in CURVES:
        return native.matches(actual, expected, limits)
    if actual['kind'] != kind:
        return False
    # Exact native control geometry within the declared tolerance. Reversing
    # traversal of an unfilled single stroke is explicitly equivalent.
    a = dict(actual, kind='line', points=endpoints(actual).tolist())
    e = dict(expected, kind='line', points=endpoints(expected).tolist())
    if not native.matches(a, e, limits):
        return False
    if kind != 'arc':
        return min(native.point_error(actual['points'], p, kind)
                   for p in (expected['points'], expected['points'][::-1])) <= limits['position']
    middle = ellipse_point(expected['center'], expected['radii'], expected['rotation'],
                           expected['start_angle']+expected['sweep']/2)
    return (np.linalg.norm(np.array(actual['center'])-expected['center']) <= limits['position']
            and np.linalg.norm(np.array(actual['middle'])-middle) <= limits['position']
            and np.linalg.norm(np.array(actual['shape'])-ellipse_shape(expected['radii'], expected['rotation']), ord=2) <= limits['position']
            and abs(abs(actual['sweep'])-abs(expected['sweep'])) <= limits['angle'])


def relation_passes(relation, mapping, objects):
    a, b = [objects[mapping[n]] for n in relation['objects']]
    if relation['kind'] in {'endpoints_meet', 'tangent_join'}:
        for i, p in enumerate(endpoints(a)):
            for j, q in enumerate(endpoints(b)):
                if np.linalg.norm(p-q) > relation['tolerance']:
                    continue
                if relation['kind'] == 'endpoints_meet':
                    return True
                u, v = tangents(a)[i], tangents(b)[j]
                cosine = float(u@v/(np.linalg.norm(u)*np.linalg.norm(v)))
                if cosine <= -math.cos(math.radians(relation['angle_tolerance']))+1e-12:
                    return True
        return False
    proxies = [dict(o, kind='line', points=endpoints(o).tolist()) if o['kind'] in CURVES else o for o in objects]
    return native.relation_passes(relation, mapping, proxies)


def check_scene(svg, annotation):
    """A pass confirms constructed native geometry, never a real model release."""
    try:
        validate_annotation(annotation)
        objects = extract(svg, annotation['size'])
        expected = annotation['objects']
        choices = {e['id']: [i for i, a in enumerate(objects) if matches(a, e, annotation['limits'])] for e in expected}
        report = dict(complete=False, supported=True, actual_count=len(objects), expected_count=len(expected),
                      unmatched_expected=[k for k, v in choices.items() if not v], mapping={}, relations=[],
                      hidden_geometry_verified=False)
        if len(objects) != len(expected) or report['unmatched_expected']:
            report['reason'] = 'object_inventory_or_geometry'
            return report
        ordered = sorted(choices, key=lambda k: len(choices[k]))
        visited, last = 0, []

        def assign(mapping, used):
            nonlocal visited, last
            visited += 1
            if visited > WORK_LIMIT:
                raise ValueError('curve_assignment_limit')
            if len(mapping) == len(ordered):
                last = [dict(**r, passed=bool(relation_passes(r, mapping, objects))) for r in annotation['relations']]
                return dict(mapping) if all(r['passed'] for r in last) else None
            name = ordered[len(mapping)]
            for index in choices[name]:
                if index in used:
                    continue
                mapping[name] = index
                result = assign(mapping, used | {index})
                if result is not None:
                    return result
                del mapping[name]
            return None

        mapping = assign({}, set())
        report.update(complete=mapping is not None, mapping=mapping or {}, relations=last,
                      assignments_visited=visited, hidden_geometry_verified=mapping is not None,
                      reason='passed' if mapping is not None else 'assignment_or_relations')
        return report
    except (ValueError, KeyError, TypeError, IndexError, OverflowError, StopIteration, ET.ParseError) as exc:
        return dict(complete=False, supported=False, hidden_geometry_verified=False, reason=str(exc))
