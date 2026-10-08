"""Measure frozen CLI output for a framed gradient and open roof-shaped mark."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def chevron_panel_semantics(svg: str) -> float:
    try:
        root = ET.fromstring(svg)
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'rect', 'path', 'circle', 'text', 'image', 'line', 'polygon', 'polyline', 'ellipse'}]
        if sorted(e.tag.rsplit('}', 1)[-1] for e in shapes) != ['polyline', 'rect']:
            return 0.
        if any(e.get('transform') for e in root.iter()):
            return 0.
        rectangle = next(e for e in shapes if e.tag.endswith('rect'))
        mark = next(e for e in shapes if e.tag.endswith('polyline'))
        x, y, w, h = (float(rectangle.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
        stroke = float(mark.get('stroke-width', '0'))
        points = np.array([[float(v) for v in pair.split(',')] for pair in mark.get('points', '').split()])
        if points.shape != (3, 2) or not np.all(np.isfinite(points)) or not np.all(np.isfinite([x,y,w,h,stroke])):
            return 0.
        gradient = next(e for e in root.iter() if e.tag.endswith('linearGradient')
                        and rectangle.get('fill') == f"url(#{e.get('id')})")
        if (gradient.get('x1', '0') != gradient.get('x2', '0')
                or gradient.get('y1', '0') == gradient.get('y2', '0')):
            return 0.
        stops = list(gradient)
        offsets = [float(s.get('offset', '0')) for s in stops]
        colors = [[int(s.get('stop-color')[i:i+2], 16) for i in (1,3,5)] for s in stops]
        a, peak, b = points
        return float(min(w,h,stroke) > 0 and 2 <= len(stops) <= 9
                     and offsets == sorted(offsets) and 0 <= min(offsets) <= max(offsets) <= 1
                     and np.ptp(colors, axis=0).max() > 8
                     and a[0] < peak[0] < b[0] and peak[1] < min(a[1],b[1])
                     and x+w*.2 < peak[0] < x+w*.8 and y-stroke < peak[1] < y+h*.4
                     and abs(a[0]-x) <= stroke and abs(b[0]-(x+w)) <= stroke
                     and max(a[1],b[1]) < y+h and mark.get('fill') == 'none'
                     and mark.get('stroke', 'none') != 'none'
                     and rectangle.get('stroke', 'none') != 'none')
    except (ET.ParseError, ValueError, TypeError, StopIteration):
        return 0.


def measure(image_path: Path, svg_path: Path) -> dict:
    record = measure_raster(image_path, svg_path)
    metrics = record['metrics']
    metrics['semantic_score'] = chevron_panel_semantics(record['svg'])
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
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
        'provenance': {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}},
        'cases': before})
    return {'schema_version': 'chevron_panel_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'semantic_contract': 'one framed vertical gradient rectangle and one contrasting open upward chevron',
            'measurement': {'foreground_threshold': 210, 'canny_thresholds': [50,140],
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
