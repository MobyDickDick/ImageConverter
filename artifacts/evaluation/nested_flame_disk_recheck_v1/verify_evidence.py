"""Independently re-render accepted CLI vectors and check preserved archive hashes."""
from pathlib import Path
import hashlib
import json
import sys
from xml.etree import ElementTree as ET

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.evaluate_flame_disk_recheck import evaluate, symbol_semantics
from tools.run_plan_b_variations import render, measure_quality


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for folder in (FOLDER, FOLDER/'catalog_context'):
        manifest = read(folder/'manifest.json')
        actual, expected = evaluate(manifest, folder), read(folder/'acceptance.json')
        for key in ('baseline', 'evidence', 'satisfaction_gate', 'strict_pixel_gates'):
            assert actual[key] == expected[key], (folder, key)
        assert actual['satisfaction_gate']['summary']['satisfactory'] == 3
        assert all(c['satisfactory'] and not c['regressed_metrics']
                   for c in actual['satisfaction_gate']['cases'])
        assert all(c['satisfactory'] for c in actual['strict_pixel_gates'].values())
        assert all(not access['blocked_svg_reads'] for access in expected['reference_access'].values())
        for case in manifest['cases']:
            assert sha(folder/case['image']) == case['source_sha256']
            assert symbol_semantics((folder/case['after_svg']).read_text(encoding='utf-8')) == 1
    neutral, named = read(FOLDER/'manifest.json'), read(FOLDER/'catalog_context/manifest.json')
    for case, catalog in zip(neutral['cases'], named['cases']):
        assert sha(FOLDER/case['after_svg']) == sha(FOLDER/'catalog_context'/catalog['after_svg'])
        for directory in ('images_to_convert', 'descriptions'):
            root = ET.parse(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml')
            entries = [e for e in root.iter('entry') if case['source'] in [p.text for p in e.findall('bilder/bild')]]
            assert len(entries) == 1 and entries[0].findtext('beschreibung') == case['description']
    folder = FOLDER/'independent'
    report = read(folder/'report.json')
    assert report['summary']['passed'] == report['summary']['completed'] == 17
    for case in report['cases']:
        for key, digest in (('input_png', 'input_sha256'), ('output_svg', 'output_sha256'),
                            ('reference_svg', 'reference_svg_sha256')):
            assert sha(folder/case[key]) == case[digest]
        image = cv2.imread(str(folder/case['input_png']))
        reference = (folder/case['reference_svg']).read_text(encoding='utf-8')
        np.testing.assert_array_equal(image, render(reference, case['width'], case['height']))
        svg = (folder/case['output_svg']).read_text(encoding='utf-8')
        quality = measure_quality(image, svg)
        assert quality['satisfactory'] and quality['metrics'] == case['metrics']
        assert symbol_semantics(svg) == 1 and not case['blocked_svg_reads']
    archive = ROOT/'artifacts/satisfactory_conversions'
    index = read(archive/'index.json')
    records = {case['variant']: case for case in index['cases']}
    assert index['case_count'] == len(records) >= 371
    assert {'GE0204_M', 'GE0204_L', 'GE0204_S'} <= records.keys()
    safety = read(FOLDER/'archive_safety.json')
    assert len(safety['previous_record_hashes']) == 368
    for variant, digest in safety['previous_record_hashes'].items():
        assert hashlib.sha256(json.dumps(records[variant], sort_keys=True).encode()).hexdigest() == digest
    for case in index['cases']:
        for key in ('image', 'svg'):
            assert sha(archive/case[key]) == case[key+'_sha256']
    from seal_validation import node_id
    summary = read(FOLDER/'standard_profile_summary.json')
    expected = set(read(FOLDER/'checks/plan.json')['expected_nodes'])
    cases = list(ET.parse(FOLDER/'standard_profile.xml').iter('testcase'))
    assert len(cases) == len(expected) == summary['collected'] == summary['measured']
    assert {node_id(case) for case in cases} == expected
    assert not any(case.find('failure') is not None or case.find('error') is not None for case in cases)
    assert all(c['exit_code'] == 0 for c in read(FOLDER/'checks/static_checks.json').values())
    print('PASS: six catalog comparisons, 17 independent CLI cases, 368 preserved archive records')


if __name__ == '__main__':
    main()
