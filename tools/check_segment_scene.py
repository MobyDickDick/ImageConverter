"""Independent logical straight-line inventory over native SVG primitives.

Opt-in segment equivalence, never raster similarity or Runtime role labels.
The strict v1 oracle remains unchanged. Missing hidden geometry is explicitly
unverified: the external annotation must authorize omission under named covers.
"""
from __future__ import annotations

import copy
import math
from xml.etree import ElementTree as ET

import numpy as np

from tools import check_native_scene as native

SCHEMA = 'independent_segment_scene_v1'
WORK_LIMIT = 4096
CHOICE_LIMIT = 256


def validate_annotation(annotation):
    if annotation.get('schema') != SCHEMA:
        raise ValueError('Independent segment annotation required')
    strict = copy.deepcopy(annotation)
    strict['schema'] = native.SCHEMA
    native.validate_annotation(strict)
    by_id = {o['id']: o for o in annotation['objects']}
    for obj in annotation['objects']:
        rep = obj.get('representation')
        if rep is None:
            continue
        if (set(rep) != {'mode', 'occluders', 'max_segments', 'join_tolerance', 'collinearity', 'hidden_geometry'}
                or rep['mode'] != 'collinear_segments' or obj['kind'] != 'line'
                or obj.get('linecap', 'butt') != 'butt'
                or rep['hidden_geometry'] != 'unverified_if_omitted'
                or type(rep['max_segments']) is not int or not 2 <= rep['max_segments'] <= 8):
            raise ValueError('Invalid segment representation')
        for key, cap in [('join_tolerance', .1), ('collinearity', .25)]:
            if not math.isfinite(rep[key]) or not 0 <= rep[key] <= cap:
                raise ValueError('Invalid segment tolerance')
        covers = rep['occluders']
        if not isinstance(covers, list) or len(covers) > 8 or len(set(covers)) != len(covers):
            raise ValueError('Invalid cover inventory')
        for name in covers:
            cover = by_id.get(name, {})
            if (cover.get('kind') not in {'circle', 'rect'} or native.color(cover.get('fill', 'none')) is None
                    or not any(r['kind'] == 'front_of' and r['objects'] == [name, obj['id']]
                               for r in annotation['relations'])):
                raise ValueError('Opaque annotated cover and depth relation required')
        if np.linalg.norm(np.diff(np.array(obj['points']), axis=0)) < 1e-8:
            raise ValueError('Degenerate logical line')


def cover_interval(a, b, cover):
    """Exact centerline intersection with an opaque fill (stroke is excluded)."""
    a, b = np.array(a), np.array(b)
    delta = b-a
    if cover['fill'] is None:
        return None
    pts = np.array(cover['points'])
    if cover['kind'] == 'circle':
        offset = a-pts[0]
        aa = float(delta@delta)
        bb = float(2*offset@delta)
        cc = float(offset@offset-cover['radius']**2)
        disc = bb*bb-4*aa*cc
        if aa <= 1e-20 or disc < 0:
            return None
        lo, hi = ((-bb-math.sqrt(disc))/(2*aa), (-bb+math.sqrt(disc))/(2*aa))
    elif cover['kind'] == 'rect':
        # Similarity-transformed rectangles remain convex. Clip all half planes.
        lo, hi = 0., 1.
        center = pts.mean(axis=0)
        for p, q in zip(pts, np.roll(pts, -1, axis=0)):
            edge = q-p
            normal = np.array([-edge[1], edge[0]])
            if float(normal@(center-p)) < 0:
                normal = -normal
            start, slope = float(normal@(a-p)), float(normal@delta)
            if abs(slope) < 1e-12:
                if start < 0:
                    return None
            elif slope > 0:
                lo = max(lo, -start/slope)
            else:
                hi = min(hi, -start/slope)
    else:
        return None
    lo, hi = max(0., lo), min(1., hi)
    return (lo, hi) if hi >= lo else None


class _Budget:
    def __init__(self):
        self.work = 0

    def tick(self):
        self.work += 1
        if self.work > WORK_LIMIT:
            raise ValueError('segment_assignment_limit')


def line_choices(objects, expected, limits, budget):
    """Enumerate bounded, nonoverlapping partitions; never reuse an SVG atom."""
    rep = expected['representation']
    start, end = np.array(expected['points'], dtype=float)
    length = float(np.linalg.norm(end-start))
    axis = (end-start)/length
    candidates = []
    for index, obj in enumerate(objects):
        budget.tick()
        if obj['kind'] != 'line':
            continue
        # Reuse strict paint/stroke semantics without using expected endpoints.
        style = dict(expected, points=obj['points'])
        if not native.matches(obj, style, limits):
            continue
        points = np.array(obj['points'])
        projection = (points-start)@axis
        if projection[0] > projection[1]:
            projection, points = projection[::-1], points[::-1]
        perpendicular = points-start-projection[:, None]*axis
        if (projection[1]-projection[0] <= 1e-8 or projection[0] < -limits['position']
                or projection[1] > length+limits['position']
                or np.linalg.norm(perpendicular, axis=1).max() > limits['position']):
            continue
        candidates.append((float(projection[0]), float(projection[1]), index, points))
    candidates.sort(key=lambda row:(row[0], row[1], row[2]))
    choices = []

    def visit(parts, next_index):
        budget.tick()
        if parts and np.linalg.norm(parts[0][3][0]-start) <= limits['position'] and np.linalg.norm(parts[-1][3][1]-end) <= limits['position']:
            points = np.array([parts[0][3][0], parts[-1][3][1]])
            delta = points[1]-points[0]
            norm = float(np.linalg.norm(delta))
            if norm > 1e-8 and all(native.segment_distance(p, *points) <= rep['collinearity']+1e-8
                                   for row in parts for p in row[3]):
                virtual = dict(objects[parts[0][2]], points=points.tolist())
                if native.matches(virtual, expected, limits):
                    choices.append(dict(indices=tuple(row[2] for row in parts), object=virtual, parts=parts))
                    if len(choices) > CHOICE_LIMIT:
                        raise ValueError('segment_choice_limit')
        if len(parts) == rep['max_segments']:
            return
        for j in range(next_index, len(candidates)):
            row = candidates[j]
            if not parts:
                if np.linalg.norm(row[3][0]-start) > limits['position']:
                    continue
            elif row[0] < parts[-1][1]-1e-8:
                # Even invisible duplicate strokes cannot be silently discarded.
                continue
            visit(parts+[row], j+1)

    visit([], 0)
    return choices


def partition_passes(choice, expected, assigned, objects):
    rep = expected.get('representation')
    if rep is None or len(choice['indices']) == 1:
        return True, False
    for name in rep['occluders']:
        other = assigned[name]
        cover = objects[other['indices'][0]]
        if cover['order'] <= max(objects[i]['order'] for i in choice['indices']):
            return False, False
    omitted = False
    for left, right in zip(choice['parts'], choice['parts'][1:]):
        a, b = left[3][1], right[3][0]
        if np.linalg.norm(b-a) <= rep['join_tolerance']+1e-8:
            continue
        # Check the actual gap, not an annotation-sized mask or a runtime joint.
        intervals = sorted(interval for name in rep['occluders']
                           if (interval := cover_interval(a, b, objects[assigned[name]['indices'][0]])) is not None)
        cursor = 0.
        gap_length = float(np.linalg.norm(b-a))
        for lo, hi in intervals:
            if (lo-cursor)*gap_length > rep['join_tolerance']+1e-8:
                return False, False
            cursor = max(cursor, hi)
        if (1-cursor)*gap_length > rep['join_tolerance']+1e-8:
            return False, False
        omitted = True
    return True, omitted


def check_scene(svg, annotation):
    """Full logical inventory decision, with explicit hidden-geometry uncertainty."""
    try:
        validate_annotation(annotation)
        objects = native.extract(svg, annotation['size'])
        expected = annotation['objects']
        budget = _Budget()
        choices = {}
        for obj in expected:
            if obj.get('representation'):
                choices[obj['id']] = line_choices(objects, obj, annotation['limits'], budget)
            else:
                choices[obj['id']] = [dict(indices=(i,), object=actual) for i, actual in enumerate(objects)
                                      if native.matches(actual, obj, annotation['limits'])]
        report = dict(complete=False, supported=True, actual_count=len(objects), expected_count=len(expected),
                      unmatched_expected=[key for key, value in choices.items() if not value], mapping={},
                      relations=[], unmatched_actual=[], hidden_geometry_verified=None,
                      omitted_hidden_geometry=[], segmented_options=[key for key, value in choices.items()
                          if any(len(c['indices']) > 1 for c in value)])
        if report['unmatched_expected']:
            report['reason'] = 'object_inventory_or_geometry'
            return report
        ordered = sorted(choices, key=lambda name:len(choices[name]))
        by_id = {obj['id']:obj for obj in expected}
        best_unused = list(range(len(objects)))

        def assign(assigned, used):
            nonlocal best_unused
            budget.tick()
            if len(assigned) == len(ordered):
                unused = sorted(set(range(len(objects)))-used)
                if len(unused) <= len(best_unused):
                    best_unused = unused
                logical = [assigned[obj['id']]['object'] for obj in expected]
                mapping = {obj['id']:i for i, obj in enumerate(expected)}
                relations = []
                for rel in annotation['relations']:
                    if rel['kind'] == 'front_of':
                        a, b = [assigned[name]['indices'] for name in rel['objects']]
                        passed = min(objects[i]['order'] for i in a) > max(objects[i]['order'] for i in b)
                    else:
                        passed = native.relation_passes(rel, mapping, logical)
                    relations.append(dict(**rel, passed=bool(passed)))
                omitted = []
                partitions = True
                for name, choice in assigned.items():
                    passed, hidden = partition_passes(choice, by_id[name], assigned, objects)
                    partitions &= passed
                    if hidden:
                        omitted.append(name)
                report['relations'] = relations
                if unused or not partitions or not all(r['passed'] for r in relations):
                    return False
                report.update(complete=True, mapping={name:list(c['indices']) for name,c in assigned.items()},
                              omitted_hidden_geometry=omitted, hidden_geometry_verified=not omitted)
                return True
            name = ordered[len(assigned)]
            for choice in choices[name]:
                indices = set(choice['indices'])
                if not indices & used:
                    assigned[name] = choice
                    if assign(assigned, used | indices):
                        return True
                    del assigned[name]
            return False

        assign({}, set())
        report.update(unmatched_actual=best_unused, work_units=budget.work,
                      reason='passed' if report['complete'] else 'inventory_partition_or_relations')
        return report
    except (ValueError, KeyError, TypeError, IndexError, OverflowError, ET.ParseError) as exc:
        return dict(complete=False, supported=False, reason=str(exc))
