"""Measure saved circle/chord/T vectors with independent topology and gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def symbol_semantics(svg: str, family=None) -> float:
    """Independently require a filled circle, converging chords and interior T."""
    try:
        root = ET.fromstring(svg)
        if any(e.get('transform') for e in root.iter()):
            return 0.
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'rect', 'circle', 'ellipse', 'line', 'polygon', 'polyline', 'path', 'text', 'image'}]
        shapes = [e for e in shapes if not (e.tag.endswith('rect') and e.get('fill') == '#ffffff'
                  and float(e.get('width', 0)) == float(root.get('width', 0))
                  and float(e.get('height', 0)) == float(root.get('height', 0))
                  and e.get('x', '0') == '0' and e.get('y', '0') == '0')]
        if sorted(e.tag.rsplit('}', 1)[-1] for e in shapes) != ['circle', 'line', 'line', 'line', 'line']:
            return 0.
        circle = next(e for e in shapes if e.tag.endswith('circle'))
        cx, cy, r = (float(circle.get(k, 0)) for k in ('cx', 'cy', 'r'))
        if r <= 0 or circle.get('fill', 'none') == 'none' or circle.get('stroke', 'none') == 'none':
            return 0.
        lines = [e for e in shapes if e.tag.endswith('line')]
        if any(float(e.get('stroke-width', 0)) <= 0 or e.get('stroke', 'none') == 'none' for e in lines):
            return 0.
        endpoints = [np.array([[float(e.get('x1')), float(e.get('y1'))],
                               [float(e.get('x2')), float(e.get('y2'))]]) for e in lines]
        if not np.isfinite(endpoints).all():
            return 0.
        horizontal = [p for p in endpoints if abs(p[0, 1]-p[1, 1]) < .002]
        vertical = [p for p in endpoints if abs(p[0, 0]-p[1, 0]) < .002]
        diagonal = [p for p in endpoints if abs(p[0, 1]-p[1, 1]) >= .002 and abs(p[0, 0]-p[1, 0]) >= .002]
        if len(horizontal) != 1 or len(vertical) != 1 or len(diagonal) != 2:
            return 0.
        h, v = horizontal[0], vertical[0]
        left, right = sorted((p[np.argsort(p[:, 1])] for p in diagonal), key=lambda p:p[0, 0])
        return float(all(np.max(np.abs(np.linalg.norm(p-[cx, cy], axis=1)-r)) < .015*r+.005 for p in diagonal)
                     and left[0, 0] < left[1, 0] < cx < right[1, 0] < right[0, 0]
                     and h[0, 1] < cy and abs(v[0, 1]-h[0, 1]) < .002
                     and min(h[:, 0]) < v[0, 0] < max(h[:, 0])
                     and abs(v[0, 0]-cx) < r*.2 and cy < v[1, 1] < cy+r
                     and all(np.max(np.linalg.norm(p-[cx, cy], axis=1)) < r for p in (h, v)))
    except (ET.ParseError, ValueError, TypeError):
        return 0.


def measure(image: Path, svg: Path, family: str) -> dict:
    record = measure_raster(image, svg)
    m = record['metrics']
    m['semantic_score'] = symbol_semantics(record['svg'], family)
    record['combined_score'] = (1-m['error_per_pixel']+m['edge_alignment']+m['object_mask_iou']+m['semantic_score'])/4
    return record


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root/case['image']
        old, new = (measure(image, root/case[mode+'_svg'], None) for mode in ('before', 'after'))
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256']})
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
        'provenance': {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}},
        'cases': before})
    return {'schema_version': 'circle_linework_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
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
