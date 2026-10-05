"""Measure saved checkmark-disk CLI vectors and apply both unchanged gates."""
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


def checkmark_disk_semantics(svg: str) -> float:
    """Check observed two-leg topology, disk relation, paint and stacking."""
    root = ET.fromstring(svg)
    shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
              {'ellipse', 'circle', 'polygon', 'rect', 'path', 'line', 'text', 'image', 'polyline'}]
    if [e.tag.rsplit('}', 1)[-1] for e in shapes] != ['rect', 'ellipse', 'path', 'path']:
        return 0.
    if any(e.get('transform') for e in root.iter()):
        return 0.
    _, disk, shadow, mark = shapes
    pattern = r'M\s+([-\d.]+)\s+([-\d.]+)\s+L\s+([-\d.]+)\s+([-\d.]+)\s+L\s+([-\d.]+)\s+([-\d.]+)'
    match = re.fullmatch(pattern, mark.get('d', ''))
    shade = re.fullmatch(pattern, shadow.get('d', ''))
    if match is None or shade is None or mark.get('fill') != 'none' or shadow.get('fill') != 'none':
        return 0.
    gradient_match = re.fullmatch(r'url\(#([^)]+)\)', disk.get('fill', ''))
    gradients = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] == 'radialGradient'
                 and gradient_match and e.get('id') == gradient_match.group(1)]
    if len(gradients) != 1 or len(gradients[0]) != 3:
        return 0.
    try:
        x0,y0,x1,y1,x2,y2 = map(float, match.groups())
        cx,cy,rx,ry,sw = (float(disk.get(k, 0)) for k in ('cx','cy','rx','ry','stroke-width'))
        width, shade_width = float(mark.get('stroke-width', 0)), float(shadow.get('stroke-width', 0))
        values = [x0,y0,x1,y1,x2,y2,cx,cy,rx,ry,sw,width,shade_width]
        colors = [e.get('stop-color', '') for e in gradients[0]]
        colors += [disk.get('stroke', ''), shadow.get('stroke', '')]
        if not all(re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in colors+[mark.get('stroke', '')]):
            return 0.
        rgb = lambda c: [int(c[i:i+2],16) for i in (1,3,5)]
        r,g,b = rgb(mark.get('stroke'))
        if not (g > max(r,b)+25 and all(max(rgb(c))-min(rgb(c)) <= 25 for c in colors)):
            return 0.
        return float(all(math.isfinite(v) for v in values) and rx > 0 and ry > 0 and .7 < rx/ry < 1.3
                     and 0 < sw < min(rx,ry)*.4 and 0 < width <= shade_width < width*1.8
                     and x0 < x1 < x2 and y0 < y1 and y2 < y1
                     and math.hypot(x2-x1,y2-y1) > math.hypot(x1-x0,y1-y0)*1.3
                     and abs(cx-x1) < rx and abs(cy-y1) < ry
                     and (cx-x0)**2/rx**2+(cy-y0)**2/ry**2 > 1
                     and (cx-x2)**2/rx**2+(cy-y2)**2/ry**2 > 1
                     and all(abs(a-float(b)) < 1e-4 for a,b in zip(values[:6],shade.groups())))
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.


def measure(image_path: Path, svg_path: Path) -> dict:
    record = measure_raster(image_path, svg_path)
    metrics = record['metrics']
    metrics['semantic_score'] = checkmark_disk_semantics(record['svg'])
    record['combined_score'] = (1-metrics['error_per_pixel']+metrics['edge_alignment']+
                                metrics['object_mask_iou']+metrics['semantic_score'])/4
    return record


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root/case['image']
        old = measure(image, root/case['before_svg'])
        new = measure(image, root/case['after_svg'])
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256']})
    provenance = {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}}
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
                                      'provenance': provenance, 'cases': before})
    return {'schema_version': 'checkmark_disk_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'semantic_contract': 'one neutral radial disk behind a green two-leg checkmark with short left and long upper-right leg; current raster determines geometry and colors',
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
