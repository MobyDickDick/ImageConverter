"""Check saved native V shapes, raster gates, input hashes and actual budgets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from tools.run_plan_b_variations import measure_quality


def check_native(svg):
    root=ET.fromstring(svg)
    tag=lambda e:e.tag.rsplit('}',1)[-1]
    assert sorted(tag(e) for e in root.iter()) == sorted(
        ['svg','defs','linearGradient','rect','polyline']+['stop']*len(root.findall('.//{*}stop')))
    assert not any(e.get('transform') for e in root.iter())
    rect=root.find('{*}rect')
    mark=root.find('{*}polyline')
    gradient=root.find('.//{*}linearGradient')
    assert rect.get('fill') == f'url(#{gradient.get("id")})'
    assert gradient.get('x1') == gradient.get('x2') and gradient.get('y1') != gradient.get('y2')
    stops=list(gradient)
    assert 2 <= len(stops) <= 9
    offsets=[float(e.get('offset')) for e in stops]
    assert offsets == sorted(offsets) and 0 <= offsets[0] < offsets[-1] <= 1
    assert len({e.get('stop-color') for e in stops}) > 1
    x,y,w,h=(float(rect.get(k)) for k in ('x','y','width','height'))
    width=float(mark.get('stroke-width'))
    points=np.array([list(map(float,p.split(','))) for p in mark.get('points').split()])
    assert points.shape == (3,2) and np.all(np.isfinite(points))
    assert np.all(np.isfinite([x,y,w,h,width])) and min(w,h,width) > 0
    assert points[0,0] < points[1,0] < points[2,0]
    assert points[1,1] > max(points[0,1],points[2,1])
    assert x+w*.2 < points[1,0] < x+w*.8 and y+h*.6 < points[1,1] < y+h+width
    assert abs(points[0,0]-x) <= max(1,width)+.00001
    assert abs(points[2,0]-x-w) <= max(1,width)+.00001
    assert mark.get('fill') == 'none'
    color=lambda value:np.array([int(value[i:i+2],16) for i in (1,3,5)])
    assert min(color(mark.get('stroke'))) >= 210 and np.ptp(color(mark.get('stroke'))) <= 20
    assert np.ptp(color(rect.get('stroke'))) <= 30 and float(rect.get('stroke-width')) > 0
    return dict(bounds=[x,y,w,h],points=points.tolist(),stop_count=len(stops))


def check_case(root,case):
    path=root/case['output_svg']
    content=path.read_text(encoding='utf-8')
    record=check_native(content)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == case['output_sha256']
    assert case['satisfactory'] and case['returncode'] == 0 and not case['blocked_svg_reads']
    assert case['elapsed_seconds'] < 60
    input_path=root/case['case_id']/'input'/f'{case["case_id"]}.png'
    assert hashlib.sha256(input_path.read_bytes()).hexdigest() == case['input_sha256']
    comparison=cv2.imread(str(root/case['case_id']/'comparison.png'))
    reference=comparison[:,:case['width']]
    np.testing.assert_array_equal(reference,cv2.imread(str(input_path)))
    quality=measure_quality(reference,content)
    assert quality['satisfactory']
    np.testing.assert_allclose(list(quality['metrics'].values()),list(case['metrics'].values()),atol=1e-8)
    reports=root/case['case_id']/'conversion/reports'
    deadline=json.loads((reports/f'{case["case_id"]}_deadline.json').read_text())
    result_map=json.loads((reports/'conversion_result_map.json').read_text(encoding='utf-8'))
    registration=result_map[case['case_id']+'.png']['params']['raster_chevron_panel_v1']
    assert registration['direction'] == 'down'
    assert registration['evaluations'] == deadline['candidate_evaluations'] <= 1800
    assert sum(a['evaluations'] for a in registration['hypotheses']) == registration['evaluations']
    assert deadline['time_extensions'] == 0
    record.update(case_id=case['case_id'],metrics=quality['metrics'],
                  input_sha256=case['input_sha256'],output_sha256=case['output_sha256'],
                  elapsed_seconds=case['elapsed_seconds'],registration=registration)
    return record


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,action='append',required=True)
    parser.add_argument('--independent',type=Path,required=True)
    parser.add_argument('--summary',type=Path)
    args=parser.parse_args(argv)
    results=[]
    for root in args.run:
        report=json.loads((root/'report.json').read_text(encoding='utf-8'))
        assert report['status'] == 'completed' and report['summary']['passed'] == 17
        assert report['iterations'] == 64 and report['timeout_seconds'] == 60
        assert len({c['input_sha256'] for c in report['cases']}) == 17
        results.append(dict(seed=report['seed'],summary=report['summary'],cases=[check_case(root,c) for c in report['cases']]))
    independent=json.loads((args.independent/'summary.json').read_text(encoding='utf-8'))
    assert len(independent) == 9
    verified=[check_case(args.independent,c) for c in independent]
    output=dict(runs=results,independent=verified)
    if args.summary:
        args.summary.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Verified',17*len(results),'seeded cases and 9 independent CLI cases')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
