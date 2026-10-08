"""Measure saved zigzag panel vectors against both unchanged gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def zigzag_panel_semantics(svg: str) -> float:
    try:
        root = ET.fromstring(svg)
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'rect', 'polygon', 'path', 'circle', 'ellipse', 'line', 'polyline', 'image', 'text'}]
        if [e.tag.rsplit('}', 1)[-1] for e in shapes] != ['rect', 'rect', 'polyline']:
            return 0.
        outer, inner, mark = shapes
        x,y,w,h = (float(outer.get(k,0)) for k in ('x','y','width','height'))
        ix,iy,iw,ih = (float(inner.get(k,0)) for k in ('x','y','width','height'))
        points = np.array([[float(v) for v in pair.split(',')] for pair in mark.get('points','').split()])
        gradient = next(e for e in root.iter() if e.tag.endswith('linearGradient')
                        and outer.get('fill') == f"url(#{e.get('id')})")
        dx,dy = np.diff(points,axis=0).T
        return float(min(w,h,iw,ih)>0 and h>w and x<ix<ix+iw<x+w and y<iy<iy+ih<y+h
                     and inner.get('fill')=='none' and mark.get('fill')=='none'
                     and all(float(e.get('stroke-width',0))>0 for e in shapes)
                     and len(points)>=7 and (dy>0).all() and (dx[:-1]*dx[1:]<0).all()
                     and (points[:,0]>x).all() and (points[:,0]<ix).all()
                     and (points[:,1]>=y).all() and (points[:,1]<=y+h).all()
                     and gradient.get('y1')==gradient.get('y2') and gradient.get('x1')!=gradient.get('x2')
                     and 3<=len(list(gradient))<=11 and not any(e.get('transform') for e in root.iter()))
    except (ET.ParseError,ValueError,TypeError,StopIteration):
        return 0.


def measure(image_path: Path, svg_path: Path) -> dict:
    record = measure_raster(image_path,svg_path)
    metrics = record['metrics']
    metrics['semantic_score'] = zigzag_panel_semantics(record['svg'])
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
    return {'schema_version':'zigzag_panel_recheck_v1','baseline':baseline,'evidence':evidence,
            'satisfaction_gate':evaluate_satisfaction(baseline,after),
            'semantic_contract':'framed horizontal gradient panel with left vertical zigzag and right unfilled tall rectangle',
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
