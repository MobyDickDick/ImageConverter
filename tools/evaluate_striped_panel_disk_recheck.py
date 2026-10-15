"""Check a saved vector's disk and three contiguous enclosed horizontal bands."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.run_plan_b_variations import measure_quality


def symbol_semantics(svg: str) -> float:
    try:
        root = ET.fromstring(svg)
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'rect', 'circle', 'ellipse', 'path', 'polygon', 'line', 'polyline', 'text', 'image'}]
        if [e.tag.rsplit('}', 1)[-1] for e in shapes] != ['rect', 'circle', 'rect', 'rect', 'rect']:
            return 0.
        if any(e.get('transform') for e in root.iter()):
            return 0.
        background, disk, *bands = shapes
        cx, cy, radius = (float(disk.get(k, 0)) for k in ('cx', 'cy', 'r'))
        rectangles = [tuple(float(band.get(k, 0)) for k in ('x','y','width','height')) for band in bands]
        x, y, w, _ = rectangles[0]
        h = sum(rect[3] for rect in rectangles)
        gradient = next(e for e in root.iter() if e.tag.endswith('linearGradient')
                        and disk.get('fill') == f"url(#{e.get('id')})")
        return float(radius > 0 and w > h > 0
                     and all(abs(bx-x) < .002 and abs(bw-w) < .002 and bh > 0 for bx,by,bw,bh in rectangles)
                     and all(abs(a[1]+a[3]-b[1]) < .002 for a,b in zip(rectangles, rectangles[1:]))
                     and len({band.get('fill') for band in bands}) == 3
                     and gradient.get('x1') == gradient.get('x2')
                     and gradient.get('y1') != gradient.get('y2') and len(list(gradient)) >= 2
                     and all((px-cx)**2+(py-cy)**2 < radius**2
                             for px in (x,x+w) for py in (y,y+h))
                     and all(e.get('fill', 'none') != 'none' for e in shapes)
                     and float(disk.get('stroke-width', 0)) > 0)
    except (ET.ParseError, ValueError, TypeError, StopIteration):
        return 0.


def measure(image: Path, svg: Path) -> dict:
    record = measure_raster(image, svg)
    m = record['metrics']
    m['semantic_score'] = symbol_semantics(record['svg'])
    record['combined_score'] = (1-m['error_per_pixel']+m['edge_alignment']+m['object_mask_iou']+m['semantic_score'])/4
    return record


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root/case['image']
        old, new = (measure(image, root/case[mode+'_svg']) for mode in ('before', 'after'))
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256']})
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
        'provenance': {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}},
        'cases': before})
    strict = {case['case_id']: measure_quality(cv2.imread(str(root/case['image'])),
                  (root/case['after_svg']).read_text(encoding='utf-8')) for case in manifest['cases']}
    return {'schema_version': 'striped_panel_disk_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'strict_pixel_gates': strict,
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
    return 0 if (all(c['satisfactory'] for c in report['satisfaction_gate']['cases'])
                 and all(c['satisfactory'] for c in report['strict_pixel_gates'].values())) else 2


if __name__ == '__main__':
    raise SystemExit(main())
