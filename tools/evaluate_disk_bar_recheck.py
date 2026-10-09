"""Measure the two distinct raster topologies previously grouped in one entry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def symbol_semantics(svg: str, family: str) -> float:
    try:
        root = ET.fromstring(svg)
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'rect', 'circle', 'ellipse', 'path', 'polygon', 'line', 'polyline', 'text', 'image'}]
        shapes = [e for e in shapes if not (e.tag.endswith('rect') and e.get('fill') == '#ffffff'
                  and e.get('x', '0') == '0' and e.get('y', '0') == '0'
                  and float(e.get('width', 0)) == float(root.get('width', 0).removesuffix('px'))
                  and float(e.get('height', 0)) == float(root.get('height', 0).removesuffix('px')))]
        if any(e.get('transform') for e in root.iter()):
            return 0.
        if family == 'solid_down_arrow':
            if len(shapes) != 1 or not shapes[0].tag.endswith('polygon'):
                return 0.
            points = [tuple(map(float, p.split(','))) for p in shapes[0].get('points', '').split()]
            if len(points) != 7 or shapes[0].get('fill', 'none') == 'none':
                return 0.
            a, b, c, d, tip, f, g = points
            return float(a[1] == b[1] < c[1] == d[1] == f[1] == g[1] < tip[1]
                         and f[0] < a[0] == g[0] < tip[0] < b[0] == c[0] < d[0])
        if family != 'disk_bar' or [e.tag.rsplit('}', 1)[-1] for e in shapes] != ['circle', 'rect']:
            return 0.
        disk, bar = shapes
        cx, cy, r = (float(disk.get(k, 0)) for k in ('cx', 'cy', 'r'))
        x, y, w, h, rx = (float(bar.get(k, 0)) for k in ('x', 'y', 'width', 'height', 'rx'))
        gradient = next(e for e in root.iter() if e.tag.endswith('linearGradient')
                        and disk.get('fill') == f"url(#{e.get('id')})")
        return float(r > 0 and gradient.get('x1') == gradient.get('x2')
                     and gradient.get('y1') != gradient.get('y2') and len(list(gradient)) >= 2
                     and w > 2*h > 0 and abs(rx-h/2) < .002
                     and abs(y+h/2-cy) < r*.12 and abs(x+w/2-cx) < r*.12
                     and all((px-cx)**2+(py-cy)**2 < r*r for px in (x, x+w) for py in (y, y+h))
                     and disk.get('stroke', 'none') != 'none' and float(disk.get('stroke-width', 0)) > 0
                     and bar.get('fill', 'none') != 'none' and bar.get('stroke', 'none') != 'none')
    except (ET.ParseError, ValueError, TypeError, StopIteration):
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
        old, new = (measure(image, root/case[mode+'_svg'], case['family']) for mode in ('before', 'after'))
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256']})
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
        'provenance': {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}},
        'cases': before})
    return {'schema_version': 'disk_bar_recheck_v1', 'baseline': baseline, 'evidence': evidence,
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
