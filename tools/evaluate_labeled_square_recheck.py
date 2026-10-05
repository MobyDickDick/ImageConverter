"""Measure saved labeled-square CLI vectors and apply both unchanged gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from xml.etree import ElementTree as ET

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def labeled_square_semantics(svg: str, label: str = 'P') -> float:
    root = ET.fromstring(svg)
    shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
              {'ellipse', 'circle', 'polygon', 'rect', 'path', 'line', 'text', 'image', 'polyline'}]
    if sorted(e.tag.rsplit('}', 1)[-1] for e in shapes) != ['path', 'rect', 'text']:
        return 0.
    if any(e.get('transform') for e in root.iter()):
        return 0.
    square = next(e for e in shapes if e.tag.endswith('rect'))
    stem = next(e for e in shapes if e.tag.endswith('path'))
    text = next(e for e in shapes if e.tag.endswith('text'))
    match = re.fullmatch(r'M\s+([-\d.]+)\s+([-\d.]+)\s+L\s+([-\d.]+)\s+([-\d.]+)', stem.get('d', ''))
    if match is None or ''.join(text.itertext()) != label:
        return 0.
    try:
        x, y, w, h = (float(square.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
        sx, sy, ex, ey = map(float, match.groups())
        tx, ty, size = (float(text.get(k, 0)) for k in ('x', 'y', 'font-size'))
        sw = float(square.get('stroke-width', 0))
        cw = float(stem.get('stroke-width', 0))
        if not all(math.isfinite(v) for v in (x,y,w,h,sx,sy,ex,ey,tx,ty,size,sw,cw)):
            return 0.
        return float(w > 0 and h > 0 and .7 <= w/h <= 1.3
                     and 0 < sw < min(w,h)*.2 and 0 < cw < w*.3
                     and abs(sx-ex) < 1e-4 and abs(sx-(x+w/2)) < w*.1
                     and abs(sy-(y+h)) <= sw/2+1e-4 and ey > y+h
                     and x < tx < x+w and y < ty < y+h and 0 < size < h
                     and square.get('fill', 'none') != 'none'
                     and text.get('fill', 'none') not in ('none', square.get('fill')))
    except (TypeError, ValueError):
        return 0.


def measure(image_path: Path, svg_path: Path, label: str = 'P') -> dict:
    record = measure_raster(image_path, svg_path)
    metrics = record['metrics']
    metrics['semantic_score'] = labeled_square_semantics(record['svg'], label)
    record['combined_score'] = (1-metrics['error_per_pixel']+metrics['edge_alignment']+
                                metrics['object_mask_iou']+metrics['semantic_score'])/4
    return record


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root/case['image']
        old = measure(image, root/case['before_svg'], manifest['label'])
        new = measure(image, root/case['after_svg'], manifest['label'])
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256']})
    provenance = {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}}
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
                                      'provenance': provenance, 'cases': before})
    return {'schema_version': 'labeled_square_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'semantic_contract': 'one filled square, centered connected lower stem and exact described contrast text; geometry and colors from raster',
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
