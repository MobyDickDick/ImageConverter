"""Independently check a saved diagonal cross/disk vector and unchanged satisfaction gates."""
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
        if any(e.tag.rsplit('}',1)[-1] not in {'svg','rect','circle','line'} for e in root.iter()):
            return 0.
        bg,disk,a,b = list(root)
        if [e.tag.rsplit('}',1)[-1] for e in (bg,disk,a,b)] != ['rect','circle','line','line']:
            return 0.
        if any(e.get('transform') or e.get('opacity','1') != '1' for e in root.iter()):
            return 0.
        width,height = float(root.get('width')),float(root.get('height'))
        cx,cy,r = (float(disk.get(k)) for k in ('cx','cy','r'))
        lines=[]
        for e in (a,b):
            x1,y1,x2,y2,sw=(float(e.get(k)) for k in ('x1','y1','x2','y2','stroke-width'))
            if not (sw>0 and e.get('stroke-linecap')=='round' and abs(x2-x1)>sw*2 and abs(y2-y1)>sw*2):
                return 0.
            if not all((x-cx)**2+(y-cy)**2 < (r-sw/2)**2 for x,y in ((x1,y1),(x2,y2))):
                return 0.
            lines.append((x1,y1,x2,y2))
        x1,y1,x2,y2=lines[0];x3,y3,x4,y4=lines[1]
        if (x2-x1)*(y2-y1)*(x4-x3)*(y4-y3)>=0:
            return 0.
        def orient(ax,ay,bx,by,cx,cy):return (bx-ax)*(cy-ay)-(by-ay)*(cx-ax)
        return float(orient(x1,y1,x2,y2,x3,y3)*orient(x1,y1,x2,y2,x4,y4)<0
            and orient(x3,y3,x4,y4,x1,y1)*orient(x3,y3,x4,y4,x2,y2)<0
            and min(width,height,r)>0 and 0<=cx-r and cx+r<=width and 0<=cy-r and cy+r<=height
            and a.get('stroke')==b.get('stroke')!=disk.get('fill') and disk.get('fill','none')!='none'
            and float(bg.get('width'))==width and float(bg.get('height'))==height)
    except (ET.ParseError,ValueError,TypeError):
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
    return {'schema_version': 'diagonal_cross_disk_recheck_v1', 'baseline': baseline, 'evidence': evidence,
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
