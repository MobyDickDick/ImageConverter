"""Evaluate saved radial disk outputs using the unchanged gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def radial_disk_semantics(svg: str) -> float:
    try:
        root = ET.fromstring(svg)
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'ellipse', 'circle', 'polygon', 'rect', 'path', 'line', 'text', 'image', 'polyline'}]
        if [e.tag.rsplit('}', 1)[-1] for e in shapes] != ['rect', 'circle']:
            return 0.
        if any(e.get('transform') or e.get('opacity', '1') != '1' for e in root.iter()):
            return 0.
        background, disk = shapes
        gradients = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] == 'radialGradient']
        if len(gradients) != 1:
            return 0.
        gradient = gradients[0]
        width, height = float(root.get('width')), float(root.get('height'))
        cx, cy, radius = [float(disk.get(k)) for k in ('cx', 'cy', 'r')]
        stops = [(float(e.get('offset')), np.array([int(e.get('stop-color')[i:i+2], 16) for i in (1, 3, 5)]))
                 for e in gradient if e.tag.rsplit('}', 1)[-1] == 'stop']
        offsets = np.array([s[0] for s in stops])
        colors = np.array([s[1] for s in stops])
        return float(
            np.isfinite([width, height, cx, cy, radius, *offsets]).all()
            and background.get('fill') == '#ffffff'
            and float(background.get('x', 0)) == float(background.get('y', 0)) == 0
            and float(background.get('width')) == width and float(background.get('height')) == height
            and radius > 0 and 0 <= cx-radius < cx+radius <= width
            and 0 <= cy-radius < cy+radius <= height
            and disk.get('fill') == f"url(#{gradient.get('id')})"
            and disk.get('stroke', 'none') == 'none'
            and gradient.get('gradientUnits', 'objectBoundingBox') == 'objectBoundingBox'
            and all(gradient.get(k, '50%') in ('50%', '0.5') for k in ('cx', 'cy', 'r', 'fx', 'fy'))
            and len(stops) >= 3 and (np.diff(offsets) > 0).all()
            and offsets[0] == 0 and offsets[-1] == 1
            and colors[0].mean() > colors[np.argmin(abs(offsets-.6))].mean()+8
            and all(e.get('stop-opacity', '1') == '1' for e in gradient)
        )
    except (ET.ParseError, TypeError, ValueError, IndexError):
        return 0.


def measure(image_path: Path, svg_path: Path) -> dict:
    record = measure_raster(image_path, svg_path)
    metrics = record['metrics']
    metrics['semantic_score'] = radial_disk_semantics(record['svg'])
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
    return {'schema_version': 'radial_disk_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'semantic_contract': 'one filled circle on white background; centered native radial gradient, light interior and darker outer region',
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
