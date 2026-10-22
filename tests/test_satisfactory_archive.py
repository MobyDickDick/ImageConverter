import json
import os
from pathlib import Path
import shutil

import pytest
from xml.etree import ElementTree as ET

from tools.refresh_satisfactory_archive import ARCHIVE, ROOT, digest, refresh
from tools.recheck_satisfactory_archive import recheck


def test_archive_contains_complete_immutable_pairs():
    archive=ROOT/ARCHIVE
    index=json.loads((archive/'index.json').read_text(encoding='utf-8'))
    assert index['case_count']==len(index['cases'])>0
    assert len({c['variant'] for c in index['cases']})==len(index['cases'])
    for case in index['cases']:
        assert digest(archive/case['image'])==case['image_sha256']
        assert digest(archive/case['svg'])==case['svg_sha256']
    table=ET.parse(archive/'descriptions.xml')
    descriptions={entry.get('key'):entry.findtext('beschreibung') for entry in table.findall('.//entry')}
    assert descriptions=={case['variant']:case['description'] for case in index['cases']}


def test_extended_profile_enables_complete_archive_reconversion(monkeypatch):
    import sys
    from tools import run_pytest_profile
    calls=[]
    monkeypatch.setattr(sys,'argv',['profile','extended','tests/test_satisfactory_archive.py'])
    monkeypatch.setattr(run_pytest_profile.subprocess,'call',lambda cmd,env:calls.append((cmd,env)) or 0)
    assert run_pytest_profile.main()==0
    assert calls[0][0][-1]=='tools.refresh_satisfactory_archive'
    assert calls[-1][1]['RECHECK_SATISFACTORY_ARCHIVE']=='1'


@pytest.mark.parametrize('accepted',[False,True])
def test_archive_admits_only_explicit_acceptances_and_checks_source_integrity(tmp_path,accepted):
    import cv2
    from tools.refresh_satisfactory_archive import refresh
    from tools.run_plan_b_variations import render
    source=tmp_path/'artifacts/images_to_convert';source.mkdir(parents=True)
    package=tmp_path/'artifacts/evaluation/example';package.mkdir(parents=True)
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><circle cx="12" cy="12" r="7" fill="#345678"/></svg>'
    image=source/'sample.jpg'
    assert cv2.imwrite(str(image),render(svg,24,24))
    (package/'result.svg').write_text(svg,encoding='utf-8')
    manifest={'description':'A filled circle.','cases':[{'case_id':'sample','image':'../../images_to_convert/sample.jpg',
        'source':'sample.jpg','source_sha256':digest(image),'after_svg':'result.svg'}]}
    (package/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    (package/'report.json').write_text(json.dumps({'satisfaction_gate':{'cases':[{'case_id':'sample',
        'technically_completed':True,'satisfactory':accepted}]}}),encoding='utf-8')
    index=refresh(tmp_path)
    assert index['case_count']==int(accepted)
    if accepted:
        assert (tmp_path/ARCHIVE/'images/sample.jpg').read_bytes()==image.read_bytes()
        image.write_bytes(b'changed pixels')
        with pytest.raises(ValueError,match='Accepted source hash mismatch'):
            refresh(tmp_path)


@pytest.fixture
def accepted_archive_package(tmp_path):
    import cv2
    from tools.run_plan_b_variations import render
    source=tmp_path/'artifacts/images_to_convert';source.mkdir(parents=True)
    package=tmp_path/'artifacts/evaluation/example';package.mkdir(parents=True)
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><circle cx="12" cy="12" r="7" fill="#345678"/></svg>'
    image=source/'sample.jpg'
    assert cv2.imwrite(str(image),render(svg,24,24))
    (package/'result.svg').write_text(svg,encoding='utf-8')
    case={'case_id':'sample','image':'../../images_to_convert/sample.jpg',
          'source':'sample.jpg','source_sha256':digest(image),'after_svg':'result.svg'}
    (package/'manifest.json').write_text(json.dumps({'description':'A filled circle.','cases':[case]}),encoding='utf-8')
    (package/'report.json').write_text(json.dumps({'satisfaction_gate':{'cases':[
        {'case_id':'sample','satisfactory':True}]}}),encoding='utf-8')
    return package,case


def test_refresh_ignores_actual_mixed_scene_schema_and_keeps_valid_archive_cases(tmp_path,accepted_archive_package):
    package=tmp_path/'artifacts/evaluation/mixed_gradient_scene_v1'
    package.mkdir()
    evidence=ROOT/'artifacts/evaluation/mixed_gradient_scene_v1'
    for name in ('manifest.json','acceptance.json'):
        shutil.copyfile(evidence/name,package/name)
    report=refresh(tmp_path)
    assert [case['variant'] for case in report['cases']]==['sample']


@pytest.mark.parametrize('foreign_case',[
    {}, {'image':'missing.jpg'}, {'case_id':'sample','image':{'path':'sample.jpg'}},
    {'case_id':'sample','image':['sample.jpg']}, {'case_id':None,'image':'sample.jpg'},
    {'case_id':'','image':'sample.jpg'}, {'case_id':42,'image':'sample.jpg'}, None,
])
def test_refresh_skips_incompatible_case_rows_but_keeps_accepted_pairs(tmp_path,accepted_archive_package,foreign_case):
    package,case=accepted_archive_package
    (package/'manifest.json').write_text(json.dumps({
        'description':'A filled circle.','cases':[foreign_case,case]}),encoding='utf-8')
    report=refresh(tmp_path)
    assert report['case_count']==1
    assert report['cases'][0]['variant']=='sample'


@pytest.mark.parametrize('report',[
    {'satisfaction_gate':None},
    {'satisfaction_gate':{'cases':None}},
    {'satisfaction_gate':{'cases':[None,{}, {'satisfactory':True}]}},
    {'satisfaction_gate':{'cases':[{'case_id':'sample','satisfactory':True}]},
     'evidence':[None,{}, {'input_sha256':'unidentified'}]},
])
def test_unrelated_report_rows_do_not_abort_archive_collection(tmp_path,accepted_archive_package,report):
    package,_=accepted_archive_package
    (package/'other-report.json').write_text(json.dumps(report),encoding='utf-8')
    assert refresh(tmp_path)['case_count']==1


def test_accepted_svg_integrity_errors_still_fail_refresh(tmp_path,accepted_archive_package):
    package,_=accepted_archive_package
    svg=package/'result.svg'
    report={'satisfaction_gate':{'cases':[{'case_id':'sample','satisfactory':True}]},
            'evidence':[{'case_id':'sample','after_svg_sha256':digest(svg)}]}
    (package/'report.json').write_text(json.dumps(report),encoding='utf-8')
    svg.write_text(svg.read_text(encoding='utf-8')+'<!-- changed -->',encoding='utf-8')
    with pytest.raises(ValueError,match='Accepted SVG hash mismatch'):
        refresh(tmp_path)


@pytest.mark.skipif(os.environ.get('RECHECK_SATISFACTORY_ARCHIVE')!='1',reason='Fresh archive reconversion runs in the extended profile')
@pytest.mark.per_test_timeout(2100, fail_on_timeout=True)
def test_every_archived_satisfactory_image_is_reconverted_and_checked(tmp_path):
    report=recheck(ROOT/ARCHIVE,tmp_path/'reconversion')
    failures=[c for c in report['cases'] if not c['passed']]
    assert not failures,failures
    assert report['passed']==report['case_count']>0
