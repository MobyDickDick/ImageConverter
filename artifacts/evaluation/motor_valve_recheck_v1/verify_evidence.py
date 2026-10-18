"""Re-render saved outputs, check object contracts and preserve previous records."""
from pathlib import Path
import hashlib
import json
import sys
from xml.etree import ElementTree as ET
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tools.evaluate_motor_valve_recheck import evaluate,symbol_semantics
from tools.run_plan_b_variations import render,measure_quality
from tools.review_conversion_quality import normalized_mse

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    for folder in (FOLDER,FOLDER/'catalog_context'):
        manifest=read(folder/'manifest.json')
        actual,expected=evaluate(manifest,folder),read(folder/'acceptance.json')
        for key in ('baseline','evidence','satisfaction_gate','strict_pixel_gates'):
            assert actual[key]==expected[key],(folder,key)
        assert actual['satisfaction_gate']['summary']['satisfactory']==3
        assert all(c['satisfactory'] and not c['regressed_metrics'] for c in actual['satisfaction_gate']['cases'])
        assert all(c['satisfactory'] for c in actual['strict_pixel_gates'].values())
        assert all(not a['blocked_svg_reads'] for a in expected['reference_access'].values())
        for case in manifest['cases']:
            assert sha(folder/case['image'])==case['source_sha256']
            assert symbol_semantics((folder/case['after_svg']).read_text(encoding='utf-8'))==1
            for directory in ('images_to_convert','descriptions'):
                table=ET.parse(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml')
                entry=next(e for e in table.iter('entry') if case['source'] in [p.text for p in e.findall('bilder/bild')])
                assert entry.findtext('beschreibung')==case['description']
    for neutral,named in zip(read(FOLDER/'acceptance.json')['evidence'],read(FOLDER/'catalog_context/acceptance.json')['evidence']):
        assert neutral['after_svg_sha256']==named['after_svg_sha256']
    folder=FOLDER/'holdout'
    report=read(folder/'report.json')
    assert report['summary']['passed']==report['summary']['completed']==17
    for case in report['cases']:
        for key,digest in (('input_png','input_sha256'),('output_svg','output_sha256'),('reference_svg','reference_svg_sha256')):
            assert sha(folder/case[key])==case[digest]
        image=cv2.imread(str(folder/case['input_png']))
        reference=(folder/case['reference_svg']).read_text(encoding='utf-8')
        np.testing.assert_array_equal(image,render(reference,case['width'],case['height']))
        svg=(folder/case['output_svg']).read_text(encoding='utf-8')
        measured=measure_quality(image,svg)
        assert measured['satisfactory'] and measured['metrics']==case['metrics']
        assert symbol_semantics(svg,'R')==1 and not case['blocked_svg_reads']
    archive=ROOT/'artifacts/satisfactory_conversions'
    index=read(archive/'index.json')
    records={c['variant']:c for c in index['cases']}
    safety=read(FOLDER/'archive_safety.json')
    assert len(safety)==374 and index['case_count']>=377
    for variant,digest in safety.items():
        assert hashlib.sha256(json.dumps(records[variant],sort_keys=True).encode()).hexdigest()==digest
    for case in index['cases']:
        for key in ('image','svg'):
            assert sha(archive/case[key])==case[key+'_sha256']
    assert read(FOLDER/'checks/summary.json')['failed']==0
    assert read(FOLDER/'checks/summary.json')['exact_node_coverage']
    reconverted=read(FOLDER/'archive_recheck.json')
    assert reconverted['case_count']==reconverted['passed']==374
    assert reconverted['compared_to_previous_cli']==371
    for case in reconverted['cases']:
        svg=FOLDER/case['output_svg']
        assert sha(svg)==case['output_sha256']
        image=cv2.imread(str(archive/records[case['variant']]['image']))
        h,w=image.shape[:2]
        output=render(svg.read_text(encoding='utf-8'),w,h)
        assert hashlib.sha256(output.tobytes()).hexdigest()==case['rendered_sha256']
        mean,mse=normalized_mse(image,output)
        assert mean==case['mean_delta2'] and mse==case['metrics']['error_per_pixel']
        assert mse<=reconverted['threshold'] and '<image' not in svg.read_text(encoding='utf-8').lower()
        if case.get('previous_cli_svg'):
            previous=ROOT/case['previous_cli_svg']
            assert sha(previous)==case['previous_cli_svg_sha256']
            np.testing.assert_array_equal(output,render(previous.read_text(encoding='utf-8'),w,h))
    assert read(FOLDER/'renderer_archive_control.json')['case_count']==read(FOLDER/'renderer_archive_control.json')['pixel_equal']==374
    assert all(c['exit_code']==0 for c in read(FOLDER/'checks/static_checks.json').values())
    smokes=list(ET.parse(FOLDER/'checks/conversion_smokes.xml').iter('testcase'))
    assert len(smokes)==2 and not any(c.find('failure') is not None or c.find('error') is not None for c in smokes)
    print('PASS: six catalog comparisons, 17 independent CLI cases, 374 preserved records and archive reconversions')

if __name__=='__main__':
    main()
