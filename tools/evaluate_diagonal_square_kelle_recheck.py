"""Gate saved CLI SVGs for a square with a connected rightward stem."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np

from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.review_conversion_quality import normalized_mse


def square_and_right_stem_semantics(svg: str) -> float:
    root = ET.fromstring(svg)
    shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
              {'rect', 'path', 'circle', 'text', 'image', 'line', 'polygon', 'polyline', 'ellipse'}]
    if sorted(e.tag.rsplit('}', 1)[-1] for e in shapes) not in (['path', 'rect'], ['path', 'path', 'rect']):
        return 0.
    if any(e.get('transform') for e in root.iter()):
        return 0.
    rect = next(e for e in shapes if e.tag.endswith('rect'))
    paths = [e for e in shapes if e.tag.endswith('path')]
    stems = [e for e in paths if re.fullmatch(r'M\s+([-\d.]+)\s+([-\d.]+)\s+L\s+([-\d.]+)\s+([-\d.]+)', e.get('d', ''))]
    if len(stems) != 1:
        return 0.
    stem = stems[0]
    match = re.fullmatch(r'M\s+([-\d.]+)\s+([-\d.]+)\s+L\s+([-\d.]+)\s+([-\d.]+)', stem.get('d', ''))
    if not match:
        return 0.
    try:
        x0, y0, x1, y1 = map(float, match.groups())
        x, y, w, h = (float(rect.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
        tolerance = float(rect.get('stroke-width', 0))/2 + 1e-4
    except (TypeError, ValueError):
        return 0.
    marks = [e for e in paths if e is not stem]
    if marks:
        mark = marks[0]
        coordinates = re.findall(r'[-\d.]+', mark.get('d', ''))
        if len(coordinates) != 16 or not mark.get('d', '').endswith(' Z') or mark.get('fill', 'none') == 'none':
            return 0.
        points = list(zip(map(float, coordinates[::2]), map(float, coordinates[1::2])))
        if not all(x < px < x+w and y < py < y+h for px, py in points):
            return 0.
        if not all(abs(a[0]-b[0]) < 1e-4 or abs(a[1]-b[1]) < 1e-4
                   for a, b in zip(points, points[1:]+points[:1])):
            return 0.
    return float(w > 0 and h > 0 and .7 <= w/h <= 1.3
                 and abs(y0-y1) < 1e-4 and abs(y0-(y+h/2)) <= h*.1
                 and abs(x0-(x+w)) <= tolerance and x1 > x+w
                 and rect.get('fill', 'none') != 'none')


def measure(image_path: Path, svg_path: Path) -> dict:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f'Unreadable input: {image_path}')
    height, width = image.shape[:2]
    svg = svg_path.read_text(encoding='utf-8')
    rendered = render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)
    if rendered is None:
        raise ValueError(f'Unrenderable SVG: {svg_path}')
    root = ET.fromstring(svg)
    ref_edges, out_edges = cv2.Canny(image, 50, 140) > 0, cv2.Canny(rendered, 50, 140) > 0
    distance = cv2.distanceTransform((~out_edges).astype(np.uint8), cv2.DIST_L2, 3)
    reverse = cv2.distanceTransform((~ref_edges).astype(np.uint8), cv2.DIST_L2, 3)
    edge = float((np.exp(-distance[ref_edges]).mean()+np.exp(-reverse[out_edges]).mean())/2) if ref_edges.any() and out_edges.any() else 0.
    ref_mask, out_mask = np.min(image, axis=2) < 210, np.min(rendered, axis=2) < 210
    union = (ref_mask | out_mask).sum()
    iou = float((ref_mask & out_mask).sum()/union) if union else 1.
    mean_delta2, mse = normalized_mse(image, rendered)
    semantic = square_and_right_stem_semantics(svg)
    dimension = float(float(root.get('width', '0').removesuffix('px')) == width
                      and float(root.get('height', '0').removesuffix('px')) == height)
    metrics = {'error_per_pixel': mse, 'edge_alignment': edge, 'object_mask_iou': iou,
               'semantic_score': semantic, 'dimension_match': dimension}
    return {'status': 'completed', 'svg': svg, 'metrics': metrics, 'mean_delta2': mean_delta2,
            'dimensions': {'width': width, 'height': height}, 'combined_score': (1-mse+edge+iou+semantic)/4,
            'svg_sha256': hashlib.sha256(svg_path.read_bytes()).hexdigest()}


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
    return {'schema_version': 'diagonal_square_kelle_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'semantic_contract': 'square at left with centered rightward stem; optional orthogonal interior mark inferred from raster contrast, without OCR claims',
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
    return 0 if all(case['satisfactory'] for case in report['satisfaction_gate']['cases']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
