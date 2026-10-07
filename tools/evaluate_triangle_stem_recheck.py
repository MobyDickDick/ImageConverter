"""Evaluate saved triangle/gradient-stem CLI vectors with both unchanged gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def triangle_stem_semantics(svg: str) -> float:
    """Check topology, upward direction, separation, alignment and gradient."""
    root = ET.fromstring(svg)
    shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
              {'ellipse', 'circle', 'polygon', 'rect', 'path', 'line', 'text', 'image', 'polyline'}]
    if sorted(e.tag.rsplit('}', 1)[-1] for e in shapes) != ['polygon', 'rect']:
        return 0.
    if any(e.get('transform') for e in root.iter()):
        return 0.
    triangle = next(e for e in shapes if e.tag.endswith('polygon'))
    stem = next(e for e in shapes if e.tag.endswith('rect'))
    try:
        vertices = np.array([[float(v) for v in point.split(',')] for point in triangle.get('points', '').split()])
        if vertices.shape != (3, 2) or not np.all(np.isfinite(vertices)):
            return 0.
        tip = vertices[np.argmin(vertices[:, 1])]
        base = np.delete(vertices, np.argmin(vertices[:, 1]), axis=0)
        x, y, w, h = (float(stem.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
        if not np.all(np.isfinite([x, y, w, h])):
            return 0.
        tw = abs(base[1, 0]-base[0, 0])
        th = base[:, 1].mean()-tip[1]
        fill = stem.get('fill', '')
        if not fill.startswith('url(#') or not fill.endswith(')'):
            return 0.
        gradient = next((e for e in root.iter() if e.get('id') == fill[5:-1]), None)
        if gradient is None or not gradient.tag.endswith('linearGradient'):
            return 0.
        if [gradient.get(k, default) for k, default in
            [('x1', '0%'), ('y1', '0%'), ('x2', '100%'), ('y2', '0%')]] != ['0%', '0%', '100%', '0%']:
            return 0.
        stops = list(gradient)
        if len(stops) != 3 or [s.get('offset') for s in stops] != ['0%', '50%', '100%']:
            return 0.
        colors = [s.get('stop-color', '') for s in stops]
        if any(len(c) != 7 or not c.startswith('#') for c in colors):
            return 0.
        brightness = [np.mean([int(c[i:i+2], 16) for i in (1, 3, 5)]) for c in colors]
        return float(w > 0 and h > w and tw > w and th > 0
                     and abs(base[0, 1]-base[1, 1]) < max(.01, th*.03)
                     and abs(tip[0]-base[:, 0].mean()) < tw*.1
                     and abs(x+w/2-tip[0]) < tw*.125
                     and 0 <= y-base[:, 1].mean() <= max(4, th*.3)
                     and triangle.get('fill', 'none') != 'none'
                     and brightness[1] >= max(brightness[0], brightness[2])+12)
    except (ValueError, TypeError):
        return 0.


def measure(image_path: Path, svg_path: Path) -> dict:
    record = measure_raster(image_path, svg_path)
    metrics = record['metrics']
    metrics['semantic_score'] = triangle_stem_semantics(record['svg'])
    record['combined_score'] = (1-metrics['error_per_pixel']+metrics['edge_alignment']+
                                metrics['object_mask_iou']+metrics['semantic_score'])/4
    return record


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root/case['image']
        old, new = measure(image, root/case['before_svg']), measure(image, root/case['after_svg'])
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256']})
    provenance = {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}}
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
                                      'provenance': provenance, 'cases': before})
    return {'schema_version': 'triangle_stem_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'semantic_contract': 'one upward filled triangle above a centered separate rectangular stem; horizontal dark-light-dark native gradient',
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
