"""Re-measure saved vectors and verify the independent CLI acceptance evidence."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import cv2
from tools.evaluate_warning_disk_recheck import evaluate
from tools.run_plan_b_variations import render, measure_quality


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder=Path(__file__).resolve().parent
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    saved=json.loads((folder/'report.json').read_text(encoding='utf-8'))
    current=evaluate(manifest,folder)
    assert current['evidence']==saved['evidence']
    assert current['satisfaction_gate']==saved['satisfaction_gate']
    assert current['strict_pixel_gates']==saved['strict_pixel_gates']
    assert all(c['satisfactory'] and not c['regressed_metrics'] for c in current['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for c in current['strict_pixel_gates'].values())
    assert all(not side['blocked_svg_reads'] for side in saved['reference_access'].values())
    catalog_folder = folder/'catalog_context'
    catalog_manifest = json.loads((catalog_folder/'manifest.json').read_text(encoding='utf-8'))
    catalog_saved = json.loads((catalog_folder/'report.json').read_text(encoding='utf-8'))
    catalog_current = evaluate(catalog_manifest, catalog_folder)
    for key in ('evidence', 'satisfaction_gate', 'strict_pixel_gates'):
        assert catalog_current[key] == catalog_saved[key]
    assert all(not side['blocked_svg_reads'] for side in catalog_saved['reference_access'].values())
    for catalog, neutral in zip(catalog_manifest['cases'], manifest['cases']):
        assert (catalog_folder/catalog['after_svg']).read_bytes() == (folder/neutral['after_svg']).read_bytes()
    sources=json.loads((folder/'source_inventory.json').read_text(encoding='utf-8'))
    for source in sources['images']:
        assert digest(ROOT/'artifacts/images_to_convert'/source['source'])==source['sha256']
    fields=('case_id','input_sha256','output_sha256','metrics','complexity','satisfactory','failures','blocked_svg_reads')
    results=[]
    for index in (1,2):
        run=folder/'plan_b'/f'run_{index}'
        report=json.loads((run/'report.json').read_text(encoding='utf-8'))
        assert report['summary']==dict(completed=17,failed=0,passed=17,required=17,satisfactory=True)
        assert digest(run/'source.png')==report['source_image_sha256']
        for case in report['cases']:
            assert case['satisfactory'] and not case['blocked_svg_reads']
            assert digest(run/case['output_svg'])==case['output_sha256']
            assert digest(run/case['reference_svg'])==case['reference_svg_sha256']
            image=render((run/case['reference_svg']).read_text(encoding='utf-8'),case['width'],case['height'])
            ok,png=cv2.imencode('.png',image)
            assert ok and hashlib.sha256(png.tobytes()).hexdigest()==case['input_sha256']
            measured=measure_quality(image,(run/case['output_svg']).read_text(encoding='utf-8'))
            assert measured['satisfactory'] and measured['metrics']==case['metrics']
        results.append([{key:case[key] for key in fields} for case in report['cases']])
    assert results[0]==results[1]
    validation_path=folder/'validation_2026-10-15.json'
    if validation_path.exists():
        validation=json.loads(validation_path.read_text(encoding='utf-8'))
        for name,expected in validation['artifact_hashes'].items():
            assert digest(ROOT/name)==expected,name
        archive=json.loads((folder/'archive_recheck.json').read_text(encoding='utf-8'))
        assert archive['expected']==archive['measured']==archive['passed']==274
        assert not archive['failures'] and all(c['passed'] for c in archive['cases'])
        from xml.etree import ElementTree as ET
        cases=list(ET.parse(folder/'standard_profile.xml').iter('testcase'))
        assert len(cases)==validation['standard']['collected']==2926
        assert len({(c.get('classname'),c.get('name')) for c in cases})==len(cases)
        assert all(c.find('failure') is None and c.find('error') is None for c in cases)
        assert sum(c.find('skipped') is not None for c in cases)==30
    print('Frozen source, saved gates and two identical 17-case CLI runs verified')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
