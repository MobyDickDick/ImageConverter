"""Gate saved open lower arc and detached gradient-shaft SVGs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def symbol_semantics(svg: str, family=None) -> float:
    try:
        root = ET.fromstring(svg)
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'rect', 'path', 'circle', 'ellipse', 'polygon', 'polyline', 'line', 'text', 'image'}]
        if [e.tag.rsplit('}', 1)[-1] for e in shapes] != ['rect', 'path', 'rect']:
            return 0.
        if any(e.get('transform') or e.get('opacity', '1') != '1' for e in root.iter()):
            return 0.
        bg, arc, shaft = shapes
        match = re.fullmatch(r'M ([\d.e+-]+) ([\d.e+-]+) A ([\d.e+-]+) ([\d.e+-]+) 0 0 0 ([\d.e+-]+) ([\d.e+-]+)', arc.get('d', ''))
        if not match:
            return 0.
        lx, cy, rx, ry, ex, ey = map(float, match.groups())
        sw = float(arc.get('stroke-width', 0))
        x, y, w, h = (float(shaft.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
        width, height = float(root.get('width')), float(root.get('height'))
        gradients = [e for e in root.iter() if e.tag.endswith('linearGradient')]
        if len(gradients) != 1:
            return 0.
        gradient = gradients[0]
        stops = [(float(e.get('offset')), sum(int(e.get('stop-color')[i:i+2], 16) for i in (1,3,5))/3)
                 for e in gradient]
        if len(stops) < 3 or any(a[0] >= b[0] for a,b in zip(stops, stops[1:])):
            return 0.
        center = min(stops, key=lambda s: abs(s[0]-.5))[1]
        left = [value for t,value in stops if t < .4]
        right = [value for t,value in stops if t > .6]
        return float(bg.get('fill') == '#ffffff' and float(bg.get('x',0)) == float(bg.get('y',0)) == 0
                     and float(bg.get('width')) == width and float(bg.get('height')) == height
                     and min(rx,ry,sw,w,h) > 0 and sw < min(rx,ry)
                     and abs(cy-ey) < .002 and abs(ex-lx-2*rx) < .002
                     and 0 <= lx-sw/2 < ex+sw/2 <= width and cy >= -.5
                     and cy+ry+sw/2 < y < y+h <= height
                     and lx < x < x+w < ex and abs(x+w/2-(lx+ex)/2) < rx*.24
                     and arc.get('fill') == 'none' and arc.get('stroke', 'none') != 'none'
                     and shaft.get('fill') == f"url(#{gradient.get('id')})"
                     and gradient.get('x1') == '0' and gradient.get('x2') == '1'
                     and gradient.get('y1') == gradient.get('y2') == '0'
                     and gradient.get('gradientUnits', 'objectBoundingBox') == 'objectBoundingBox'
                     and 0 <= stops[0][0] < .25 and .75 < stops[-1][0] <= 1
                     and left and right and center > max(min(left),min(right))+8)
    except (ET.ParseError, ValueError, TypeError, IndexError):
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
        old, new = (measure(image, root/case[mode+'_svg'], 'arc_shaft') for mode in ('before', 'after'))
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256']})
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
        'provenance': {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}},
        'cases': before})
    return {'schema_version': 'arc_shaft_recheck_v1', 'baseline': baseline, 'evidence': evidence,
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
