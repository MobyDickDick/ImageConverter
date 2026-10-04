"""Re-render frozen CLI SVGs and gate the observed nested-rectangle contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np

from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.review_conversion_quality import normalized_mse


def nested_rectangle_semantics(svg: str) -> float:
    root = ET.fromstring(svg)
    shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
              {'rect', 'path', 'circle', 'text', 'image', 'line', 'polygon', 'polyline', 'ellipse'}]
    if len(shapes) != 2 or any(e.tag.rsplit('}', 1)[-1] != 'rect' for e in shapes):
        return 0.
    outer, inner = shapes
    try:
        width, height = float(root.get('width')), float(root.get('height'))
        ox, oy = float(outer.get('x', 0)), float(outer.get('y', 0))
        ow, oh = float(outer.get('width')), float(outer.get('height'))
        x, y = float(inner.get('x')), float(inner.get('y'))
        w, h = float(inner.get('width')), float(inner.get('height'))
    except (TypeError, ValueError):
        return 0.
    return float(ox == oy == 0 and ow == width and oh == height
                 and 0 < x < x+w < width and 0 < y < y+h < height
                 and inner.get('fill') != outer.get('fill')
                 and all(e.get('fill', 'none') != 'none' and not e.get('transform') for e in shapes)
                 and not any(e.get('transform') for e in root.iter()))


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
    edge = float((np.exp(-distance[ref_edges]).mean() + np.exp(-reverse[out_edges]).mean())/2) if ref_edges.any() and out_edges.any() else 0.
    # Same input-derived split for before and after. Separate the light inset
    # from its darker exterior, including low-contrast grey exteriors.
    lum = image.astype(float).mean(axis=2)
    split = float((np.percentile(lum, 10) + np.percentile(lum, 90))/2)
    ref_mask, out_mask = lum < split, rendered.astype(float).mean(axis=2) < split
    union = (ref_mask | out_mask).sum()
    iou = float((ref_mask & out_mask).sum()/union) if union else 1.
    mean_delta2, mse = normalized_mse(image, rendered)
    semantic = nested_rectangle_semantics(svg)
    dimension = float(float(root.get('width', 0)) == width and float(root.get('height', 0)) == height)
    metrics = {'error_per_pixel': mse, 'edge_alignment': edge, 'object_mask_iou': iou,
               'semantic_score': semantic, 'dimension_match': dimension}
    return {'status': 'completed', 'svg': svg, 'metrics': metrics, 'mean_delta2': mean_delta2,
            'dimensions': {'width': width, 'height': height},
            'combined_score': (1-mse+edge+iou+semantic)/4,
            'mask_luminance_split': split,
            'svg_sha256': hashlib.sha256(svg_path.read_bytes()).hexdigest()}


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root / case['image']
        old, new = measure(image, root / case['before_svg']), measure(image, root / case['after_svg'])
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256'],
                         'mask_luminance_split': new['mask_luminance_split']})
    provenance = {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}}
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
                                      'provenance': provenance, 'cases': before})
    return {'schema_version': 'nested_panel_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'semantic_contract': 'two nested rectangular color regions; light inset fully enclosed',
            'measurement': {'canny_thresholds': [50, 140], 'mask': 'input luminance percentile midpoint',
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
