"""Measure saved alarm bell vectors against both unchanged gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest


def alarm_bell_semantics(svg: str) -> float:
    """Check native bell topology and actual geometry, independently of role tags."""
    try:
        root = ET.fromstring(svg)
        shapes = [e for e in root.iter() if e.tag.rsplit('}',1)[-1] in
                  {'rect','polygon','path','circle','ellipse','line','polyline','image','text'}]
        if [e.tag.rsplit('}',1)[-1] for e in shapes] != ['path','ellipse','ellipse','path','path','path','path']:
            return 0.
        if any(e.get('transform') for e in root.iter()):
            return 0.
        body,rim,clapper,*waves = shapes
        def numbers(data):
            return [float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?',data)]
        points = numbers(body.get('d',''))
        if re.findall(r'[MLCQZ]',body.get('d','')) != ['M','C','C','L','C','C','Z'] or len(points)!=28:
            return 0.
        cx,top = points[:2]
        rx,ry,cy = (float(rim.get(k,0)) for k in ('rx','ry','cy'))
        kx,ky,krx,kry = (float(clapper.get(k,0)) for k in ('cx','cy','rx','ry'))
        if not (min(rx,ry,krx,kry)>0 and top<cy-ry and ry<rx*.5
                and abs(float(rim.get('cx',0))-cx)<1e-4
                and cx-rx<kx-krx<kx+krx<cx and cy-ry*1.6<ky<cy+ry
                and all(float(e.get('stroke-width',0))>0 for e in shapes[:2])
                and clapper.get('fill','none')!='none'):
            return 0.
        if body.get('fill')!='#ffffff':
            gradient = next(e for e in root.iter() if e.tag.endswith('linearGradient')
                            and body.get('fill')==f"url(#{e.get('id')})")
            if not (gradient.get('x1')==gradient.get('x2') and gradient.get('y1')!=gradient.get('y2')
                    and len(list(gradient))==3):
                return 0.
        arcs = []
        for i,wave in enumerate(waves):
            coords = numbers(wave.get('d',''))
            if re.findall(r'[MLCQZ]',wave.get('d',''))!=['M','Q'] or len(coords)!=6:
                return 0.
            a,b,c,d,e,f = coords
            if not (b<f<cy-ry and wave.get('fill')=='none' and float(wave.get('stroke-width',0))>0
                    and (e<a<cx and c<cx if i<2 else cx<a<e and cx<c)):
                return 0.
            arcs.append(coords)
        def horizontal_at(arc, y):
            t = np.linspace(0,1,101)[:,None]
            curve = (1-t)**2*np.array(arc[:2])+2*t*(1-t)*np.array(arc[2:4])+t**2*np.array(arc[4:])
            return float(np.interp(y,curve[:,1],curve[:,0]))
        # Compare at a shared height. Inner and outer arcs need not start at
        # the same height, so their endpoint x coordinates are not comparable.
        for side in (0,2):
            outer,inner = arcs[side:side+2]
            lo,hi = max(outer[1],inner[1]),min(outer[5],inner[5])
            if lo>=hi:
                return 0.
            for y in np.linspace(lo,hi,5):
                a,b = horizontal_at(outer,y),horizontal_at(inner,y)
                if (a>=b if side==0 else a<=b):
                    return 0.
        return 1.
    except (ET.ParseError,ValueError,TypeError,StopIteration):
        return 0.


def measure(image_path: Path, svg_path: Path) -> dict:
    record = measure_raster(image_path,svg_path)
    metrics = record['metrics']
    metrics['semantic_score'] = alarm_bell_semantics(record['svg'])
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
    return {'schema_version':'alarm_bell_recheck_v1','baseline':baseline,'evidence':evidence,
            'satisfaction_gate':evaluate_satisfaction(baseline,after),
            'semantic_contract':'upright curved bell, oval rim, bright lower-left clapper and two separated quadratic sound arcs per side; vertical gradient or unfilled body',
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
