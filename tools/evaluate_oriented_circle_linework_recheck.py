"""Measure oriented circle/chord/T vectors with independent topology and gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
from tools.run_plan_b_variations import measure_quality

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_circle_linework_recheck import symbol_semantics as _down_semantics
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def symbol_semantics(svg: str, direction='down') -> float:
    # Independent inverse mapping to the established downward topology contract.
    try:
        root = ET.fromstring(svg)
        if any(e.get('transform') for e in root.iter()):
            return 0.
        w,h = float(root.get('width')),float(root.get('height'))
        if direction == 'down':
            return _down_semantics(svg)
        if direction not in ('left','up','right'):
            return 0.
        def inverse(x,y):
            if direction == 'left': return y,w-x
            if direction == 'up': return w-x,h-y
            return h-y,x
        for e in root.iter():
            tag=e.tag.rsplit('}',1)[-1]
            keys=[('cx','cy')] if tag=='circle' else [('x1','y1'),('x2','y2')] if tag=='line' else []
            for xkey,ykey in keys:
                x,y=inverse(float(e.get(xkey)),float(e.get(ykey)))
                e.set(xkey,str(x));e.set(ykey,str(y))
            if tag=='rect' and direction in ('left','right'):
                e.set('width',str(h));e.set('height',str(w))
        if direction in ('left','right'):
            root.set('width',str(h));root.set('height',str(w))
        return _down_semantics(ET.tostring(root,encoding='unicode'))
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
        old, new = (measure(image, root/case[mode+'_svg'], case['direction']) for mode in ('before', 'after'))
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256']})
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
        'provenance': {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}},
        'cases': before})
    return {'schema_version': 'oriented_circle_linework_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'strict_pixel_gates': {c['case_id']:measure_quality(cv2.imread(str(root/c['image'])), (root/c['after_svg']).read_text(encoding='utf-8')) for c in manifest['cases']},
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
