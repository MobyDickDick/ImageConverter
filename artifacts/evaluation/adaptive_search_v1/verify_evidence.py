"""Independently remeasure saved outputs and check test/archive integrity."""
from pathlib import Path
import hashlib
import json
import re
import sys
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import cv2
import numpy as np
from tools.run_plan_b_variations import render,measure_quality
from tools.evaluate_diagonal_square_kelle_recheck import measure
from tools.evaluate_primitive_scene import check_objects
from tools.evaluate_motor_valve_recheck import symbol_semantics as motor_semantics
from tools.evaluate_labeled_disk_recheck import symbol_semantics as letter_semantics
from tools.evaluate_short_label_search import symbol_semantics as label_semantics
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def semantic(case,svg,image):
    if case['kind']=='motor':
        return motor_semantics(svg)
    if case['kind']=='letter':
        return letter_semantics(svg,'Q',bottom_stem=True)
    if case['kind']=='label':
        return label_semantics(svg,case['label'])
    return float(check_objects(render(svg,image.shape[1],image.shape[0]),case['expected_objects'])['passed'])

def node_id(case):
    parts=case.get('classname').split('.')
    for cut in range(len(parts),0,-1):
        module='/'.join(parts[:cut])+'.py'
        if (ROOT/module).exists():
            return '::'.join([module,*parts[cut:],case.get('name')])
    raise ValueError(case.attrib)

def main():
    benchmark=read(FOLDER/'benchmark.json')
    cases={c['case_id']:c for c in benchmark['cases']}
    assert len(cases)==8
    for policy,data in benchmark['policies'].items():
        assert not data['reference_access']['blocked_svg_reads']
        log=(FOLDER/(policy+'.log')).read_text(encoding='utf-8')
        for record in data['cases']:
            case=cases[record['case_id']]
            assert sha(FOLDER/case['image'])==case['source_sha256']
            assert sha(FOLDER/record['output_svg'])==record['output_sha256']
            image=cv2.imread(str(FOLDER/case['image']))
            svg=(FOLDER/record['output_svg']).read_text(encoding='utf-8')
            quality=measure_quality(image,svg)
            assert quality==record['quality']
            assert semantic(case,svg,image)==record['semantic_score']==1.
            if policy=='adaptive':
                assert quality['satisfactory'] and record['satisfactory']
                assert record['conversion_attempts']==1
                assert record['search_control']['stop_reason']=='satisfactory'
            times=re.findall(r'^\[INFO\] Konvertiert '+re.escape(case['case_id'])+r'\.(?:jpg|png).*Dauer=([\d.]+)s',log,re.M)
            assert len(times)==record['conversion_attempts']
    previous=ROOT/'artifacts/evaluation/motor_valve_recheck_v1'
    old={Path(c['source']).stem:c for c in read(previous/'manifest.json')['cases']}
    for row in benchmark['policies']['fixed']['cases']:
        if row['source'] in old:
            assert (FOLDER/row['output_svg']).read_bytes()==(previous/old[row['source']]['after_svg']).read_bytes()
    bad=read(FOLDER/'counterexample.json')
    assert sha(FOLDER/bad['svg'])==bad['svg_sha256']
    image=cv2.imread(str(FOLDER/bad['source']))
    svg=(FOLDER/bad['svg']).read_text(encoding='utf-8')
    assert not measure_quality(image,svg)['satisfactory']
    assert not pixel_quality(image,render(svg,image.shape[1],image.shape[0]))['passed']
    folder=FOLDER/'holdout'
    battery=read(folder/'report.json')
    assert battery['summary']['completed']==battery['summary']['passed']==17
    for case in battery['cases']:
        for key,digest in (('input_png','input_sha256'),('output_svg','output_sha256'),('reference_svg','reference_svg_sha256')):
            assert sha(folder/case[key])==case[digest]
        image=cv2.imread(str(folder/case['input_png']))
        np.testing.assert_array_equal(image,render((folder/case['reference_svg']).read_text(encoding='utf-8'),case['width'],case['height']))
        svg=(folder/case['output_svg']).read_text(encoding='utf-8')
        assert measure_quality(image,svg)['satisfactory'] and motor_semantics(svg,'R')==1.
        assert not case['blocked_svg_reads']
    archive=ROOT/'artifacts/satisfactory_conversions'
    index=read(archive/'index.json')
    records={c['variant']:c for c in index['cases']}
    safety=read(FOLDER/'archive_safety.json')
    assert len(records)==len(safety)==377
    for variant,digest in safety.items():
        assert hashlib.sha256(json.dumps(records[variant],sort_keys=True).encode()).hexdigest()==digest
    for case in index['cases']:
        for key in ('image','svg'):
            assert sha(archive/case[key])==case[key+'_sha256']
    report=read(FOLDER/'archive_recheck.json')
    assert report['case_count']==report['passed']==377
    for case in report['cases']:
        path=FOLDER/case['output_svg']
        assert sha(path)==case['output_sha256']
        actual=measure(archive/records[case['variant']]['image'],path)
        assert actual['mean_delta2']==case['mean_delta2']
        assert actual['metrics']['error_per_pixel']<=report['threshold']
        assert '<image' not in actual['svg'].lower()
    checks=FOLDER/'checks_final'
    plan,summary=read(checks/'plan.json'),read(checks/'summary.json')
    measured=[c for number in range(4) for c in ET.parse(checks/f'group_{number}.xml').iter('testcase')]
    actual=[node_id(c) for c in measured]
    assert len(actual)==len(set(actual))==len(plan['expected_nodes'])==summary['measured']
    assert set(actual)==set(plan['expected_nodes']) and summary['failed']==0
    assert not any(c.find('error') is not None or c.find('failure') is not None for c in measured)
    assert all(v['exit_code']==0 for v in read(checks/'static_checks.json').values())
    print('PASS: eight strict CLI cases, 17 independent variations, 377 unchanged archive records and reconversions, complete default tests')

if __name__=='__main__':
    main()
