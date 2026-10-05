"""Evaluate saved circle/triangle CLI outputs against both unchanged gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def circle_triangle_semantics(svg: str, direction: str = 'rechts') -> float:
    if direction not in {'rechts', 'links', 'oben', 'unten'}:
        raise ValueError('unsupported triangle direction')
    root = ET.fromstring(svg)
    shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
              {'ellipse', 'circle', 'polygon', 'rect', 'path', 'line', 'text', 'image', 'polyline'}]
    if sorted(e.tag.rsplit('}', 1)[-1] for e in shapes) != ['ellipse', 'polygon']:
        return 0.
    if any(e.get('transform') for e in root.iter()):
        return 0.
    circle = next(e for e in shapes if e.tag.endswith('ellipse'))
    triangle = next(e for e in shapes if e.tag.endswith('polygon'))
    try:
        cx, cy, rx, ry = (float(circle.get(k, 0)) for k in ('cx', 'cy', 'rx', 'ry'))
        vertices = np.array([[float(v) for v in point.split(',')] for point in triangle.get('points', '').split()])
        if vertices.shape != (3, 2) or min(rx, ry) <= 0 or not .85 <= rx/ry <= 1.18:
            return 0.
        if not np.all(np.isfinite(vertices)):
            return 0.
        normalized = (vertices-[cx,cy])/[rx,ry]
        # Normalize the declared direction to right for the independent check.
        for _ in range({'rechts': 0, 'oben': 1, 'links': 2, 'unten': 3}[direction]):
            normalized = np.column_stack((-normalized[:, 1], normalized[:, 0]))
        tip = np.argmax(normalized[:, 0])
        base = np.delete(normalized, tip, axis=0)
        a, b, c = vertices
        ab, ac = b-a, c-a
        area = abs(ab[0]*ac[1]-ab[1]*ac[0])/2
        filled = all(e.get('fill', 'black') != 'none' for e in shapes)
        return float(filled and circle.get('fill') != triangle.get('fill')
                     and np.all(np.linalg.norm(normalized, axis=1) <= 1.04)
                     and .12 <= area/(np.pi*rx*ry) <= .6
                     and abs(base[0,0]-base[1,0]) < .2
                     and normalized[tip,0] > .5 and abs(normalized[tip,1]) < .2
                     and base[:,0].mean() < 0 and base[:,1].min() < -.3 and base[:,1].max() > .3)
    except (ValueError, TypeError):
        return 0.


def measure(image_path: Path, svg_path: Path, direction: str = 'rechts') -> dict:
    record = measure_raster(image_path, svg_path)
    metrics = record['metrics']
    metrics['semantic_score'] = circle_triangle_semantics(record['svg'], direction)
    record['combined_score'] = (1-metrics['error_per_pixel']+metrics['edge_alignment']+
                                metrics['object_mask_iou']+metrics['semantic_score'])/4
    return record


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    direction = manifest.get('direction', 'rechts')
    for case in manifest['cases']:
        image = root/case['image']
        old, new = measure(image, root/case['before_svg'], direction), measure(image, root/case['after_svg'], direction)
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256']})
    provenance = {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}}
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
                                      'provenance': provenance, 'cases': before})
    return {'schema_version': 'pump_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'semantic_contract': 'one filled circular body and one contrasting contained triangle pointing '
                                 + {'rechts': 'right', 'links': 'left', 'oben': 'up', 'unten': 'down'}[direction]
                                 + '; colors observed from raster',
            'measurement': {'foreground_threshold': 210, 'canny_thresholds': [50, 140],
                            'output': 'saved CLI SVG re-rendered with production renderer'}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(json.loads(args.manifest.read_text(encoding='utf-8')), args.manifest.parent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report['satisfaction_gate']['summary'], sort_keys=True))
    return 0 if all(c['satisfactory'] for c in report['satisfaction_gate']['cases']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
