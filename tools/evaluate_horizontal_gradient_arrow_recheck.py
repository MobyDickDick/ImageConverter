"""Evaluate saved horizontal arrows with independent topology and unchanged gates."""
from __future__ import annotations

import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def horizontal_arrow_semantics(svg: str, direction: str = 'left') -> float:
    """Require a solid triangle, detached narrower shaft and transverse shading."""
    if direction not in {'left', 'right'}:
        return 0.
    try:
        root = ET.fromstring(svg)
        if any(e.get('transform') or e.get('opacity', '1') != '1' for e in root.iter()):
            return 0.
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'rect', 'polygon', 'circle', 'ellipse', 'path', 'line', 'polyline', 'text', 'image'}]
        if [e.tag.rsplit('}', 1)[-1] for e in shapes] != ['rect', 'polygon', 'rect']:
            return 0.
        background, head, shaft = shapes
        width, height = float(root.get('width')), float(root.get('height'))
        points = np.array([[float(v) for v in p.split(',')] for p in head.get('points', '').split()])
        if points.shape != (3, 2) or not np.isfinite(points).all():
            return 0.
        index = int(np.argmin(points[:, 0]) if direction == 'left' else np.argmax(points[:, 0]))
        tip, base = points[index], np.delete(points, index, axis=0)
        x, y, w, h = (float(shaft.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
        gradients = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] == 'linearGradient']
        if len(gradients) != 1:
            return 0.
        gradient = gradients[0]
        stops = [(float(e.get('offset')), np.array([int(e.get('stop-color')[i:i+2], 16) for i in (1, 3, 5)]))
                 for e in gradient if e.tag.rsplit('}', 1)[-1] == 'stop']
        offsets = np.array([s[0] for s in stops])
        if len(stops) < 3 or not (np.diff(offsets) > 0).all():
            return 0.
        middle = min(stops, key=lambda s: abs(s[0]-.5))[1].mean()
        sides = [[v.mean() for o, v in stops if o < .35], [v.mean() for o, v in stops if o > .65]]
        separated = (tip[0] < base[0, 0] < x if direction == 'left'
                     else x+w < base[0, 0] < tip[0])
        valid = (
            background.get('fill') == '#ffffff'
            and float(background.get('x', 0)) == float(background.get('y', 0)) == 0
            and float(background.get('width')) == width and float(background.get('height')) == height
            and min(w, h) > 0 and 0 <= x < x+w <= width and 0 <= y < y+h <= height
            and abs(base[0, 0]-base[1, 0]) < 1e-6 and separated
            and min(base[:, 1]) <= y < y+h <= max(base[:, 1])
            and np.ptp(base[:, 1]) > h and abs(tip[1]-y-h/2) <= max(1., height*.1)
            and head.get('fill', 'none') != 'none'
            and shaft.get('fill') == f"url(#{gradient.get('id')})"
            and gradient.get('gradientUnits', 'objectBoundingBox') == 'objectBoundingBox'
            and gradient.get('x1') == gradient.get('x2') == '0'
            and {gradient.get('y1'), gradient.get('y2')} == {'0', '1'}
            and 0 <= offsets[0] < .25 and .75 < offsets[-1] <= 1
            and all(sides) and middle > max(min(side) for side in sides)+10
        )
        return float(valid)
    except (ET.ParseError, TypeError, ValueError, IndexError):
        return 0.


def measure(image: Path, svg: Path, direction: str = 'left') -> dict:
    record = measure_raster(image, svg)
    m = record['metrics']
    m['semantic_score'] = horizontal_arrow_semantics(record['svg'], direction)
    record['combined_score'] = (1-m['error_per_pixel']+m['edge_alignment']+m['object_mask_iou']+m['semantic_score'])/4
    return record


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root/case['image']
        old, new = (measure(image, root/case[mode+'_svg'], manifest.get('direction', 'left'))
                    for mode in ('before', 'after'))
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256']})
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
        'provenance': {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}},
        'cases': before})
    return {'schema_version': 'horizontal_gradient_arrow_recheck_v1', 'baseline': baseline,
            'evidence': evidence, 'satisfaction_gate': evaluate_satisfaction(baseline, after)}
