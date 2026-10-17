"""Independently re-render saved results, gates, semantic text and archive hashes."""
from pathlib import Path
import hashlib
import json
import sys
from xml.etree import ElementTree as ET

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tools.evaluate_short_label_search import evaluate, symbol_semantics
from tools.evaluate_diagonal_square_kelle_recheck import measure
from tools.review_conversion_quality import DEFAULT_THRESHOLD
from tools.run_plan_b_variations import render, measure_quality


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for folder in (FOLDER,FOLDER/'catalog_context'):
        actual,expected = evaluate(folder),read(folder/'acceptance.json')
        for key in ('baseline','evidence','satisfaction_gate','strict_pixel_gates'):
            assert actual[key] == expected[key], (folder,key)
        assert actual['satisfaction_gate']['summary']['satisfactory'] == 3
        assert all(c['satisfactory'] for c in actual['strict_pixel_gates'].values())
        assert all(not access['blocked_svg_reads'] for access in expected['reference_access'].values())
    named = read(FOLDER/'catalog_context/manifest.json')
    neutral = read(FOLDER/'manifest.json')
    for case,catalog in zip(neutral['cases'],named['cases']):
        assert sha(FOLDER/case['image']) == case['source_sha256']
        assert sha(FOLDER/case['after_svg']) == sha(FOLDER/'catalog_context'/catalog['after_svg'])
        assert symbol_semantics((FOLDER/case['after_svg']).read_text(encoding='utf-8'),'Lux') == 1
        for directory in ('images_to_convert','descriptions'):
            root = ET.parse(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml')
            entries = [e for e in root.findall('.//entry') if case['source'] in [p.text for p in e.findall('.//bild')]]
            assert len(entries) == 1 and entries[0].findtext('beschreibung') == case['description']
    for name in ('independent','independent_second_seed'):
        folder = FOLDER/name
        report = read(folder/'report.json')
        assert report['summary']['passed'] == report['summary']['completed'] == 17
        for case in report['cases']:
            for key in ('input_png','output_svg','reference_svg'):
                assert sha(folder/case[key]) == case[{'input_png':'input_sha256','output_svg':'output_sha256','reference_svg':'reference_svg_sha256'}[key]]
            image = cv2.imread(str(folder/case['input_png']))
            reference = (folder/case['reference_svg']).read_text(encoding='utf-8')
            np.testing.assert_array_equal(image,render(reference,case['width'],case['height']))
            svg = (folder/case['output_svg']).read_text(encoding='utf-8')
            quality = measure_quality(image,svg)
            assert quality['satisfactory'] and quality['metrics'] == case['metrics']
            assert symbol_semantics(svg,'mPa') == 1 and not case['blocked_svg_reads']
    archive = ROOT/'artifacts/satisfactory_conversions'
    index = read(archive/'index.json')
    assert index['case_count'] == len(index['cases']) >= 368
    records = {case['variant']:case for case in index['cases']}
    safety = read(FOLDER/'archive_safety.json')
    assert len(safety['previous_record_hashes']) == 365
    for variant,digest in safety['previous_record_hashes'].items():
        assert hashlib.sha256(json.dumps(records[variant],sort_keys=True).encode()).hexdigest() == digest
    for case in index['cases']:
        for key in ('image','svg'):
            assert sha(archive/case[key]) == case[key+'_sha256']
    if (FOLDER/'archive_recheck.json').exists():
        report = read(FOLDER/'archive_recheck.json')
        assert report['passed'] == report['case_count'] == len(report['cases']) == 365
        assert report['pixel_identical_count'] == sum(c['pixel_identical_to_previous_cli'] for c in report['cases']) == 365
        for case in report['cases']:
            svg = FOLDER/case['output_svg']
            assert sha(svg) == case['output_sha256']
            old = ROOT/case['previous_cli_svg']
            assert sha(old) == case['previous_cli_svg_sha256']
            record = measure(archive/records[case['variant']]['image'],svg)
            assert record['mean_delta2'] == case['mean_delta2']
            assert record['metrics']['error_per_pixel'] <= DEFAULT_THRESHOLD and '<image' not in record['svg'].lower()
            w,h = record['dimensions']['width'],record['dimensions']['height']
            equal = bool(np.array_equal(render(record['svg'],w,h),render(old.read_text(encoding='utf-8'),w,h)))
            assert equal == case['pixel_identical_to_previous_cli']
    if (FOLDER/'standard_profile_summary.json').exists():
        summary = read(FOLDER/'standard_profile_summary.json')
        expected = set(read(FOLDER/'checks/plan.json')['expected_nodes'])
        from seal_validation import node_id
        cases = list(ET.parse(FOLDER/'standard_profile.xml').iter('testcase'))
        assert len(cases) == len(expected) == summary['collected'] == summary['measured']
        assert {node_id(case) for case in cases} == expected
        assert not any(case.find('failure') is not None or case.find('error') is not None for case in cases)
    print('PASS: six catalog comparisons, strict pixels, 34 independent cases and 365 preserved archive records')


if __name__ == '__main__':
    main()
