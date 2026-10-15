"""Independently check a saved warning triangle/disk vector and unchanged satisfaction gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.run_plan_b_variations import measure_quality


def symbol_semantics(svg: str) -> float:
    try:
        root = ET.fromstring(svg)
        if any(e.tag.rsplit('}',1)[-1] not in {'svg','defs','linearGradient','stop','rect','circle','path','line'} for e in root.iter()):
            return 0.
        defs,bg,disk,triangle,bar,dot = list(root)
        if [e.tag.rsplit('}',1)[-1] for e in (defs,bg,disk,triangle,bar,dot)] != ['defs','rect','circle','path','line','circle']:
            return 0.
        if any(e.get('transform') or e.get('opacity','1') != '1' for e in root.iter()):
            return 0.
        width,height = float(root.get('width')),float(root.get('height'))
        cx,cy,r = (float(disk.get(k)) for k in ('cx','cy','r'))
        gradient=list(defs)[0]
        if (gradient.tag.rsplit('}',1)[-1]!='linearGradient' or disk.get('fill')!=f"url(#{gradient.get('id')})"
                or gradient.get('x1')!=gradient.get('x2') or gradient.get('y1')==gradient.get('y2')
                or len(list(gradient))!=2 or gradient[0].get('stop-color')==gradient[1].get('stop-color')):
            return 0.
        path=triangle.get('d','')
        if re.sub(r'[-+\d.e\s]','',path)!='MLLZ':
            return 0.
        ax,ay,rx,by,lx,by2 = [float(v) for v in re.findall(r'[-+]?(?:\d*\.)?\d+(?:e[-+]?\d+)?',path)]
        sw=float(triangle.get('stroke-width'))
        bx,y1,bx2,y2,bw=(float(bar.get(k)) for k in ('x1','y1','x2','y2','stroke-width'))
        dx,dy,dr=(float(dot.get(k)) for k in ('cx','cy','r'))
        if not (min(width,height,r,sw,bw,dr)>0 and 0<=cx-r and cx+r<=width and 0<=cy-r and cy+r<=height
                and lx<ax<rx and ay<by==by2 and bx==bx2 and y1<y2
                and ay+sw/2<y1-bw/2<y2+bw/2<dy-dr<dy+dr<by-sw/2
                and abs(bx-dx)<bw*.6 and triangle.get('stroke-linejoin')=='round'
                and bar.get('stroke-linecap')=='round' and bar.get('stroke')==dot.get('fill')
                and triangle.get('fill','none') not in ('none',triangle.get('stroke'))
                and float(bg.get('width'))==width and float(bg.get('height'))==height):
            return 0.
        if not all((x-cx)**2+(y-cy)**2<(r-sw/2)**2 for x,y in ((ax,ay),(rx,by),(lx,by))):
            return 0.
        for x,y,pad in ((bx,y1,bw/2),(bx,y2,bw/2),(dx,dy,dr)):
            left=ax+(lx-ax)*(y-ay)/(by-ay);right=ax+(rx-ax)*(y-ay)/(by-ay)
            if not left+sw/2+pad<x<right-sw/2-pad:
                return 0.
        return 1.
    except (ET.ParseError,ValueError,TypeError,IndexError,ZeroDivisionError):
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
        old, new = (measure(image, root/case[mode+'_svg']) for mode in ('before', 'after'))
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
    return {'schema_version': 'warning_disk_recheck_v1', 'baseline': baseline, 'evidence': evidence,
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
