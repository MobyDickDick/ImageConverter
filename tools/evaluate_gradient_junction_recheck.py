"""Independently check analytic T junctions with unchanged satisfaction gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.run_plan_b_variations import measure_quality


def symbol_semantics(svg: str, direction: str = 'up') -> float:
    try:
        root = ET.fromstring(svg)
        if direction != 'up':
            # Independently project explicit source-space coordinates into the
            # upright frame. Reject transformed or extra shapes as before.
            width, height = float(root.get('width')), float(root.get('height'))
            frames = {'left': ([[0,-1],[1,0]], [height,0]),
                      'right': ([[0,1],[-1,0]], [0,width]),
                      'down': ([[-1,0],[0,-1]], [width,height])}
            matrix, offset = frames[direction]
            def project(x, y):
                return np.asarray(matrix) @ [x,y] + offset
            for element in root.iter():
                tag = element.tag.rsplit('}',1)[-1]
                if tag == 'rect':
                    x,y,w,h = (float(element.get(k,0)) for k in ('x','y','width','height'))
                    corners = np.array([project(a,b) for a,b in ((x,y),(x+w,y),(x,y+h),(x+w,y+h))])
                    lo,hi = corners.min(axis=0),corners.max(axis=0)
                    for key,value in zip(('x','y','width','height'),(*lo,*(hi-lo))):
                        element.set(key, f'{value:g}')
                elif tag == 'polygon':
                    points = [project(*(float(v) for v in p.split(','))) for p in element.get('points','').split()]
                    element.set('points',' '.join(f'{x:g},{y:g}' for x,y in points))
                elif tag == 'linearGradient':
                    for suffix in ('1','2'):
                        x,y = project(float(element.get('x'+suffix,0)),float(element.get('y'+suffix,0)))
                        element.set('x'+suffix,f'{x:g}')
                        element.set('y'+suffix,f'{y:g}')
            if direction in ('left','right'):
                root.set('width',str(height))
                root.set('height',str(width))
        shapes = [e for e in root.iter() if e.tag.rsplit('}',1)[-1] in
                  {'rect','polygon','path','line','circle','ellipse','text','image','polyline'}]
        if [e.tag.rsplit('}',1)[-1] for e in shapes] != ['rect','rect','polygon']:
            return 0.
        if any(e.get('transform') or e.get('opacity','1')!='1' for e in root.iter()):
            return 0.
        bg,bar,stem=shapes
        width,height=float(root.get('width')),float(root.get('height'))
        x,y,w,h=(float(bar.get(k,0)) for k in ('x','y','width','height'))
        points=np.array([[float(v) for v in pt.split(',')] for pt in stem.get('points','').split()])
        if points.shape!=(5,2) or not np.isfinite(points).all():return 0.
        a,b,c,d,e=points
        gradients=[e for e in root.iter() if e.tag.endswith('linearGradient')]
        if len(gradients)!=2:return 0.
        for gradient,axis in zip(gradients,('y','x')):
            if gradient.get('gradientUnits')!='userSpaceOnUse':return 0.
            if float(gradient.get(axis+'2'))<=float(gradient.get(axis+'1')):return 0.
            other='x' if axis=='y' else 'y'
            if gradient.get(other+'1')!=gradient.get(other+'2'):return 0.
            stops=[(float(s.get('offset')),np.mean([int(s.get('stop-color')[i:i+2],16) for i in (1,3,5)])) for s in gradient]
            if len(stops)<3 or any(a[0]>=b[0] for a,b in zip(stops,stops[1:])):return 0.
            mid=min(stops,key=lambda s:abs(s[0]-.5))[1]
            low=[v for t,v in stops if t<.4];high=[v for t,v in stops if t>.6]
            if not low or not high or mid<=max(min(low),min(high))+8:return 0.
        return float(bg.get('fill')=='#ffffff' and float(bg.get('width'))==width
          and float(bg.get('height'))==height and 0<=x<a[0]<b[0]<x+w<=width+.01
          and 0<=a[1]==b[1]<y and abs(c[1]-y)<.002 and abs(e[1]-y)<.002
          and abs(a[0]-e[0])<.002 and abs(b[0]-c[0])<.002
          and abs(d[0]-(a[0]+b[0])/2)<.002 and abs(d[1]-(y+h/2))<.002
          and y+h<=height and h>0 and bar.get('fill')=='url(#bar_color)'
          and stem.get('fill')=='url(#stem_color)')
    except (ET.ParseError,ValueError,TypeError,IndexError,KeyError):
        return 0.


def measure(image: Path, svg: Path, direction: str = 'up') -> dict:
    record = measure_raster(image, svg)
    m = record['metrics']
    m['semantic_score'] = symbol_semantics(record['svg'], direction)
    record['combined_score'] = (1-m['error_per_pixel']+m['edge_alignment']+m['object_mask_iou']+m['semantic_score'])/4
    return record


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root/case['image']
        old, new = (measure(image, root/case[mode+'_svg'], manifest.get('direction','up')) for mode in ('before', 'after'))
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
    return {'schema_version': 'gradient_junction_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'strict_pixel_gates': strict,
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
    return 0 if (all(c['satisfactory'] for c in report['satisfaction_gate']['cases'])
                 and all(c['satisfactory'] for c in report['strict_pixel_gates'].values())) else 2


if __name__ == '__main__':
    raise SystemExit(main())
