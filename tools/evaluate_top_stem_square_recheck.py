"""Measure saved square/top-handle/slash/dot vectors with unchanged gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def symbol_semantics(svg: str) -> float:
    """Require the connected upper handle and both interior geometric marks."""
    try:
        root = ET.fromstring(svg)
        if any(e.get('transform') for e in root.iter()):
            return 0.
        shapes = [e for e in root.iter() if e.tag.rsplit('}', 1)[-1] in
                  {'rect', 'path', 'circle', 'ellipse', 'line', 'polygon', 'polyline', 'text', 'image'}]
        if sorted(e.tag.rsplit('}', 1)[-1] for e in shapes) != ['path', 'path', 'path', 'rect']:
            return 0.
        body = next(e for e in shapes if e.tag.endswith('rect'))
        x, y, w, h = (float(body.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
        if min(w, h) <= 0 or not .7 <= w/h <= 1.3 or body.get('fill', 'none') == 'none':
            return 0.
        paths = [e for e in shapes if e.tag.endswith('path')]
        stems = [e for e in paths if re.fullmatch(r'M\s+([-\d.]+)\s+([-\d.]+)\s+L\s+([-\d.]+)\s+([-\d.]+)', e.get('d', ''))]
        if len(stems) != 1:
            return 0.
        stem = stems[0]
        sx, sy, ex, ey = map(float, re.findall(r'[-\d.]+', stem.get('d')))
        if not (abs(sx-ex) < .002 and abs(sx-x-w/2) < w*.1 and
                min(sy,ey) < y and abs(max(sy,ey)-y) <= float(body.get('stroke-width',0))/2+.002):
            return 0.
        marks = []
        for e in paths:
            if e is stem:
                continue
            if not re.fullmatch(r'M\s+[-\d.]+\s+[-\d.]+(?:\s+L\s+[-\d.]+\s+[-\d.]+){3}\s+Z', e.get('d','')) or e.get('fill','none') == 'none':
                return 0.
            p = np.array(list(map(float,re.findall(r'[-\d.]+',e.get('d'))))).reshape(4,2)
            if not np.isfinite(p).all() or not ((p[:,0]>x).all() and (p[:,0]<x+w).all() and (p[:,1]>y).all() and (p[:,1]<y+h).all()):
                return 0.
            marks.append(p)
        slash, dot = sorted(marks, key=lambda p:np.ptp(p[:,1]), reverse=True)
        dw, dh = np.ptp(dot,axis=0)
        top, bottom = slash[np.argsort(slash[:,1])[:2]].mean(axis=0), slash[np.argsort(slash[:,1])[2:]].mean(axis=0)
        return float(.5 <= dw/dh <= 2 and np.ptp(slash[:,1]) > 2*dh and top[0] > bottom[0]
                     and dot[:,0].max() <= bottom[0] and dot[:,1].mean() >= top[1]+.55*(bottom[1]-top[1])
                     and all(abs(a[0]-b[0]) < .002 or abs(a[1]-b[1]) < .002 for a,b in zip(dot,np.roll(dot,-1,axis=0))))
    except (ET.ParseError, ValueError, TypeError, ZeroDivisionError):
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
        old, new = (measure(image, root/case[mode+'_svg']) for mode in ('before','after'))
        before[case['case_id']] = {'metrics':old['metrics'], 'dimensions':old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case,'input_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
            'before_mean_delta2':old['mean_delta2'],'after_mean_delta2':new['mean_delta2'],
            'before_svg_sha256':old['svg_sha256'],'after_svg_sha256':new['svg_sha256']})
    baseline = seal_baseline_manifest({'schema_version':'semantic_only_baseline_manifest_v1',
        'provenance':{**manifest['provenance'],'input_hashes':{e['case_id']:e['input_sha256'] for e in evidence}},'cases':before})
    return {'schema_version':'top_stem_marked_square_recheck_v1','baseline':baseline,'evidence':evidence,
            'satisfaction_gate':evaluate_satisfaction(baseline,after)}


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
