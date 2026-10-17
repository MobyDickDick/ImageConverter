"""Independently evaluate saved short-label CLI outputs against frozen baselines."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.run_plan_b_variations import measure_quality


def symbol_semantics(svg, label):
    try:
        root = ET.fromstring(svg)
        allowed = {'svg','rect','circle','text'}
        if any(e.tag.rsplit('}',1)[-1] not in allowed or e.get('transform') for e in root.iter()):
            return 0.
        disks = [e for e in root.iter() if e.tag.endswith('circle')]
        texts = [e for e in root.iter() if e.tag.endswith('text')]
        backgrounds = [e for e in root.iter() if e.tag.endswith('rect')]
        if len(disks)!=1 or len(backgrounds)!=1 or len(texts) not in {1,len(label)}:
            return 0.
        if ''.join(''.join(e.itertext()) for e in texts)!=label:
            return 0.
        disk = disks[0]
        w,h = float(root.get('width')),float(root.get('height'))
        cx,cy,r,sw = [float(disk.get(k,0)) for k in ('cx','cy','r','stroke-width')]
        values = [w,h,cx,cy,r,sw]
        if (min(w,h,r,sw)<=0 or sw>=r*.25 or disk.get('fill') in {None,'none'}
                or disk.get('stroke') in {None,'none'} or disk.get('fill')==disk.get('stroke')
                or cx-r-sw/2<0 or cy-r-sw/2<0 or cx+r+sw/2>w or cy+r+sw/2>h):
            return 0.
        positions = []
        for text in texts:
            x,y,size = [float(text.get(k,0)) for k in ('x','y','font-size')]
            values.extend([x,y,size])
            if (abs(x-cx)>=r*.8 or not cy<y<cy+r*.95 or not 3<=size<r*1.9
                    or text.get('font-family')!='Arial' or text.get('font-weight') not in {'400','700'}
                    or text.get('text-anchor')!='middle' or text.get('fill') in {None,'none'}):
                return 0.
            positions.append(x)
        bg = backgrounds[0]
        return float(all(math.isfinite(v) for v in values) and positions==sorted(positions)
                     and bg.get('fill')=='#ffffff' and float(bg.get('width'))==w and float(bg.get('height'))==h)
    except (ValueError,TypeError,ET.ParseError):
        return 0.


def evaluate(root):
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    before,after,evidence,strict = {},{},{},{}
    for case in manifest['cases']:
        name = case['case_id']
        image = root/case['image']
        if hashlib.sha256(image.read_bytes()).hexdigest()!=case['source_sha256']:
            raise ValueError('Source changed: '+name)
        measured = []
        for mode in ('before','after'):
            record = measure_raster(image,root/case[mode+'_svg'])
            record['metrics']['semantic_score'] = symbol_semantics(record['svg'],manifest['label'])
            m = record['metrics']
            record['combined_score'] = (1-m['error_per_pixel']+m['edge_alignment']+m['object_mask_iou']+m['semantic_score'])/4
            measured.append(record)
        old,new = measured
        before[name] = dict(metrics=old['metrics'],dimensions=old['dimensions'])
        after[name] = new
        evidence[name] = dict(case_id=name,input_sha256=case['source_sha256'],before_mean_delta2=old['mean_delta2'],
                              after_mean_delta2=new['mean_delta2'],after_svg_sha256=new['svg_sha256'])
        strict[name] = measure_quality(cv2.imread(str(image)),new['svg'])
    baseline = seal_baseline_manifest(dict(schema_version='semantic_only_baseline_manifest_v1',
        provenance={**manifest['provenance'],'input_hashes':{k:v['input_sha256'] for k,v in evidence.items()}},cases=before))
    return dict(schema_version='short_label_search_recheck_v1',baseline=baseline,evidence=list(evidence.values()),
                satisfaction_gate=evaluate_satisfaction(baseline,after),strict_pixel_gates=strict)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    report=evaluate(args.directory)
    (args.directory/'acceptance.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(report['satisfaction_gate']['summary'])
    return 0 if all(c['satisfactory'] for c in report['satisfaction_gate']['cases']) else 2


if __name__=='__main__':
    raise SystemExit(main())
