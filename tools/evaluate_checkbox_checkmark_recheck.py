"""Measure saved checkbox/checkmark vectors against both unchanged gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def checkbox_checkmark_semantics(svg: str) -> float:
    try:
        root = ET.fromstring(svg)
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'rect', 'polygon', 'path', 'circle', 'ellipse', 'line', 'polyline', 'image', 'text'}]
        if [e.tag.rsplit('}', 1)[-1] for e in shapes] != ['rect', 'polygon']:
            return 0.
        if any(e.get('transform') for e in root.iter()):
            return 0.
        box, mark = shapes
        x, y, w, h, bw = (float(box.get(k, 0)) for k in ('x', 'y', 'width', 'height', 'stroke-width'))
        p = np.array([[float(v) for v in pair.split(',')] for pair in mark.get('points', '').split()])
        sw = float(mark.get('stroke-width', 0))
        if p.shape != (6, 2) or not np.isfinite(p).all() or not np.isfinite([x,y,w,h,bw,sw]).all():
            return 0.
        gradient = next(e for e in root.iter() if e.tag.endswith('linearGradient')
                        and mark.get('fill') == f"url(#{e.get('id')})")
        stops = list(gradient)
        offsets = [float(s.get('offset', '0')) for s in stops]
        colors = np.array([[int(s.get('stop-color')[i:i+2], 16) for i in (1,3,5)] for s in stops])
        a, inner, end, tip, outer, b = p
        d = np.roll(p,-1,axis=0)-p
        cross = d[:,0]*np.roll(d,-1,axis=0)[:,1]-d[:,1]*np.roll(d,-1,axis=0)[:,0]
        return float(min(w,h,bw,sw) > 0 and .7 < w/h < 1.3
                     and box.get('fill') == '#ffffff' and box.get('stroke', 'none') != 'none'
                     and mark.get('stroke', 'none') != 'none'
                     and gradient.get('x1') == gradient.get('x2') and gradient.get('y1') != gradient.get('y2')
                     and 2 <= len(stops) <= 5 and offsets == sorted(offsets)
                     and 0 <= min(offsets) <= max(offsets) <= 1
                     and np.any(colors[:,1] > np.maximum(colors[:,0],colors[:,2])+20)
                     and np.ptp(colors,axis=0).max() > 8
                     and a[0] < inner[0] < end[0] and inner[1] > max(a[1],end[1])
                     and outer[1] > inner[1] and b[0] < outer[0] < tip[0]
                     and np.linalg.norm(end-inner) > np.linalg.norm(inner-a)*1.2
                     and np.count_nonzero(cross > 0) == 5 and np.count_nonzero(cross < 0) == 1
                     and x < outer[0] < x+w and y < outer[1] < y+h
                     and min(end[1],tip[1]) < y and a[0] < x+w*.5)
    except (ET.ParseError, ValueError, TypeError, StopIteration):
        return 0.


def measure(image_path: Path, svg_path: Path) -> dict:
    record = measure_raster(image_path,svg_path)
    metrics = record['metrics']
    metrics['semantic_score'] = checkbox_checkmark_semantics(record['svg'])
    record['combined_score'] = (1-metrics['error_per_pixel']+metrics['edge_alignment']+
                                metrics['object_mask_iou']+metrics['semantic_score'])/4
    return record


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root/case['image']
        old, new = measure(image,root/case['before_svg']), measure(image,root/case['after_svg'])
        before[case['case_id']] = {'metrics':old['metrics'],'dimensions':old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case,'input_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2':old['mean_delta2'],'after_mean_delta2':new['mean_delta2'],
                         'before_svg_sha256':old['svg_sha256'],'after_svg_sha256':new['svg_sha256']})
    baseline = seal_baseline_manifest({'schema_version':'semantic_only_baseline_manifest_v1',
        'provenance':{**manifest['provenance'],'input_hashes':{e['case_id']:e['input_sha256'] for e in evidence}},
        'cases':before})
    return {'schema_version':'checkbox_checkmark_recheck_v1','baseline':baseline,'evidence':evidence,
            'satisfaction_gate':evaluate_satisfaction(baseline,after),
            'semantic_contract':'white framed checkbox behind a six-vertex two-leg checkmark with native vertical green gradient and dark outline',
            'measurement':{'foreground_threshold':210,'canny_thresholds':[50,140],
                           'output':'saved CLI SVG re-rendered with production renderer'}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = evaluate(json.loads(args.manifest.read_text(encoding='utf-8')),args.manifest.parent)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(report['satisfaction_gate']['summary'],sort_keys=True))
    return 0 if all(c['satisfactory'] for c in report['satisfaction_gate']['cases']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
