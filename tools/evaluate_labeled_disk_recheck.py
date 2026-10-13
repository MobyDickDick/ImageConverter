"""Independently gate a described letter inside a filled outlined disk."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.run_plan_b_variations import measure_quality


def symbol_semantics(svg: str, label='Q') -> float:
    """Independently require one filled outlined circle and exact native text."""
    try:
        root = ET.fromstring(svg)
        if any(e.tag.rsplit('}', 1)[-1] not in {'svg', 'rect', 'circle', 'text'} for e in root.iter()):
            return 0.
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'rect', 'path', 'circle', 'ellipse', 'polygon', 'polyline', 'line', 'text', 'image'}]
        if sorted(e.tag.rsplit('}', 1)[-1] for e in shapes) != ['circle', 'rect', 'text']:
            return 0.
        if any(e.get('transform') or e.get('opacity', '1') != '1' for e in root.iter()):
            return 0.
        bg, disk, text = (next(e for e in shapes if e.tag.endswith(tag)) for tag in ('rect', 'circle', 'text'))
        width, height = float(root.get('width')), float(root.get('height'))
        cx, cy, r, sw = (float(disk.get(k, 0)) for k in ('cx', 'cy', 'r', 'stroke-width'))
        tx, ty, size = (float(text.get(k, 0)) for k in ('x', 'y', 'font-size'))
        colors = [tuple(int(e.get(k).removeprefix('#')[i:i+2], 16) for i in (0, 2, 4))
                  for e, k in ((disk, 'fill'), (disk, 'stroke'), (text, 'fill'))]
        return float(all(math.isfinite(v) for v in (width,height,cx,cy,r,sw,tx,ty,size))
                     and min(width,height,r,sw,size) > 0 and sw < r*.2
                     and 0 <= cx-r-sw/2 and cx+r+sw/2 <= width
                     and 0 <= cy-r-sw/2 and cy+r+sw/2 <= height
                     and abs(tx-cx) < r*.25 and cy < ty < cy+r*.8 and size < r*1.9
                     and ''.join(text.itertext()) == label and text.get('font-family') == 'Arial'
                     and text.get('font-weight') == '700' and text.get('text-anchor') == 'middle'
                     and sum(colors[0]) > sum(colors[1])+60 and sum(colors[0]) > sum(colors[2])+60
                     and bg.get('fill') == '#ffffff' and float(bg.get('x', 0)) == float(bg.get('y', 0)) == 0
                     and float(bg.get('width')) == width and float(bg.get('height')) == height)
    except (ET.ParseError, ValueError, TypeError, AttributeError, StopIteration):
        return 0.


def measure(image: Path, svg: Path, label='Q') -> dict:
    record = measure_raster(image, svg)
    m = record['metrics']
    m['semantic_score'] = symbol_semantics(record['svg'], label)
    record['combined_score'] = (1-m['error_per_pixel']+m['edge_alignment']+m['object_mask_iou']+m['semantic_score'])/4
    return record


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root/case['image']
        old, new = (measure(image, root/case[mode+'_svg'], manifest.get('label', 'Q')) for mode in ('before', 'after'))
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
    return {'schema_version': 'labeled_disk_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after), 'strict_pixel_gates': strict,
            'measurement': {'foreground_threshold': 210, 'canny_thresholds': [50, 140],
                            'output': 'saved CLI SVG re-rendered with production renderer'}}
