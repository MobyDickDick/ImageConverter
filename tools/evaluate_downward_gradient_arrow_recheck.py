"""Evaluate saved downward triangle/gradient-shaft outputs using the unchanged gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def downward_gradient_arrow_semantics(svg: str) -> float:
    """Check the reflected topology using the independently specified upward contract."""
    from tools.evaluate_gradient_arrow_recheck import gradient_arrow_semantics
    try:
        root = ET.fromstring(svg)
        height = float(root.get('height'))
        for shape in root.iter():
            kind = shape.tag.rsplit('}', 1)[-1]
            if kind == 'polygon':
                points = [[float(v) for v in point.split(',')] for point in shape.get('points', '').split()]
                shape.set('points', ' '.join(f'{x:g},{height-y:g}' for x, y in points))
            elif kind == 'rect':
                shape.set('y', f"{height-float(shape.get('y', 0))-float(shape.get('height')):g}")
        return gradient_arrow_semantics(ET.tostring(root, encoding='unicode'))
    except (ET.ParseError, TypeError, ValueError, IndexError):
        return 0.


def measure(image_path: Path, svg_path: Path) -> dict:
    record = measure_raster(image_path, svg_path)
    metrics = record['metrics']
    metrics['semantic_score'] = downward_gradient_arrow_semantics(record['svg'])
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
    return {'schema_version': 'downward_gradient_arrow_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'semantic_contract': 'one downward filled triangle below a narrower rectangular shaft; white gap and background; horizontal gradient with brighter center',
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
