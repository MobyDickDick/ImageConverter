"""Independently check three joined triangles and an attached labeled disk."""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np
from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.run_plan_b_variations import measure_quality


def symbol_semantics(svg, label='M'):
    try:
        root = ET.fromstring(svg)
        allowed = {'svg','defs','linearGradient','stop','rect','line','path','circle','text'}
        if any(e.tag.rsplit('}',1)[-1] not in allowed or e.get('transform') for e in root.iter()):
            return 0.
        shapes = [e for e in root.iter() if e.tag.rsplit('}',1)[-1] in {'rect','line','path','circle','text'}]
        if sorted(e.tag.rsplit('}',1)[-1] for e in shapes) != ['circle','line','path','path','path','rect','text']:
            return 0.
        circle = root.find('{*}circle')
        cx,cy,r = (float(circle.get(k)) for k in ('cx','cy','r'))
        line = root.find('{*}line')
        ax,ay,ex,ey = (float(line.get(k)) for k in ('x1','y1','x2','y2'))
        if not (r > 4 and ax < cx-r and abs(ay-cy) < r*.15
                and abs(ex-(cx-r)) < 1e-4 and abs(ey-cy) < 1e-4):
            return 0.
        orientations = set()
        for path in root.findall('{*}path'):
            data = path.get('d','')
            if re.findall('[A-Za-z]',data) != ['M','L','L','Z']:
                return 0.
            points = np.asarray([float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?\d*)',data)]).reshape(3,2)
            if not np.isfinite(points).all() or np.max(abs(points[0]-[ax,ay])) > 1e-4:
                return 0.
            a,b = points[1:]
            if abs(a[0]-b[0]) < 1e-4 and a[0] < ax and min(a[1],b[1]) < ay < max(a[1],b[1]):
                orientations.add('left')
            elif abs(a[1]-b[1]) < 1e-4 and min(a[0],b[0]) < ax < max(a[0],b[0]):
                orientations.add('top' if a[1] < ay else 'bottom')
            else:
                return 0.
        text = root.find('{*}text')
        tx,ty,size = (float(text.get(k)) for k in ('x','y','font-size'))
        return float(orientations == {'left','top','bottom'} and ''.join(text.itertext()) == label
                     and abs(tx-cx) < r*.25 and cy < ty < cy+r and 3 < size < 2*r
                     and text.get('font-family') == 'Arial' and text.get('font-weight') == '700')
    except (ET.ParseError,TypeError,ValueError,AttributeError):
        return 0.


def measure(image,svg):
    result=measure_raster(image,svg)
    m=result['metrics']
    m['semantic_score']=symbol_semantics(result['svg'])
    result['combined_score']=(1-m['error_per_pixel']+m['edge_alignment']+m['object_mask_iou']+m['semantic_score'])/4
    return result


def evaluate(manifest,root: Path):
    before,after,evidence,strict={},{},[],{}
    for case in manifest['cases']:
        old,new=(measure(root/case['image'],root/case[mode+'_svg']) for mode in ('before','after'))
        before[case['case_id']]={'metrics':old['metrics'],'dimensions':old['dimensions']}
        after[case['case_id']]=new
        evidence.append({**case,'input_sha256':hashlib.sha256((root/case['image']).read_bytes()).hexdigest(),
            'before_mean_delta2':old['mean_delta2'],'after_mean_delta2':new['mean_delta2'],
            'before_svg_sha256':old['svg_sha256'],'after_svg_sha256':new['svg_sha256']})
        strict[case['case_id']]=measure_quality(cv2.imread(str(root/case['image'])),new['svg'])
    baseline=seal_baseline_manifest(dict(schema_version='semantic_only_baseline_manifest_v1',
        provenance={**manifest['provenance'],'input_hashes':{e['case_id']:e['input_sha256'] for e in evidence}},cases=before))
    return dict(schema_version='motor_valve_recheck_v1',baseline=baseline,evidence=evidence,
        satisfaction_gate=evaluate_satisfaction(baseline,after),strict_pixel_gates=strict)
