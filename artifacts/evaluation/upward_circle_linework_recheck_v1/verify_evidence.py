"""Independently remeasure retained vectors; never execute the converter."""
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
from tools.evaluate_oriented_circle_linework_recheck import evaluate, symbol_semantics
from tools.evaluate_diagonal_square_kelle_recheck import measure
from tools.run_plan_b_variations import measure_quality, render


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pair(folder, report_name):
    manifest = read(folder / 'manifest.json')
    expected = read(folder / report_name)
    actual = evaluate(manifest, folder)
    for key in ('baseline', 'evidence', 'satisfaction_gate', 'strict_pixel_gates'):
        assert actual[key] == expected[key], (folder, key)
    assert actual['satisfaction_gate']['summary']['satisfactory'] == 9
    for case in manifest['cases']:
        assert sha(folder / case['image']) == case['source_sha256']
        strict = actual['strict_pixel_gates'][case['case_id']]
        if case['source'] in ('AC0411_L.jpg', 'AC0411_M.jpg', 'AC0411_S.jpg'):
            assert strict['failures'] == ['foreground_iou_outside_limit']
        else:
            assert strict['satisfactory']
    for access in expected['reference_access'].values():
        assert access['blocked_svg_reads'] == []
    return manifest


def main():
    manifest = verify_pair(FOLDER, 'acceptance.json')
    catalog = verify_pair(FOLDER / 'catalog_context', 'report.json')
    for case, named in zip(manifest['cases'], catalog['cases']):
        assert case['source'] == named['source']
        assert sha(FOLDER / case['after_svg']) == sha(FOLDER / 'catalog_context' / named['after_svg'])
    for directory in ('independent', 'independent_second_seed'):
        folder = FOLDER / directory
        record = read(folder / 'report.json')
        assert record['summary']['completed'] == record['summary']['passed'] == 17
        for case in record['cases']:
            image = cv2.imread(str(folder / case['input_png']))
            svg = (folder / case['output_svg']).read_text(encoding='utf-8')
            assert sha(folder / case['input_png']) == case['input_sha256']
            assert sha(folder / case['output_svg']) == case['output_sha256']
            assert sha(folder / case['reference_svg']) == case['reference_svg_sha256']
            reference = (folder / case['reference_svg']).read_text(encoding='utf-8')
            np.testing.assert_array_equal(image, render(reference, case['width'], case['height']))
            quality = measure_quality(image, svg)
            assert quality['satisfactory'] and quality['metrics'] == case['metrics']
            assert symbol_semantics(svg, 'up') == 1
            assert case['blocked_svg_reads'] == []

    archive = ROOT / 'artifacts/satisfactory_conversions'
    index = read(archive / 'index.json')
    safety = read(FOLDER / 'archive_safety.json')
    assert index['case_count'] == len(index['cases']) == safety['new_count'] == 365
    records = {case['variant']: case for case in index['cases']}
    for case in records.values():
        for key in ('image', 'svg'):
            assert sha(archive / case[key]) == case[key + '_sha256']
    assert len(safety['previous_record_hashes']) == safety['previous_count'] == 355
    for variant, digest in safety['previous_record_hashes'].items():
        assert hashlib.sha256(json.dumps(records[variant], sort_keys=True).encode()).hexdigest() == digest
    assert safety['restored_prior_acceptances'] == ['SE0082']
    for case in manifest['cases']:
        assert sha(archive / records[Path(case['source']).stem]['svg']) == sha(FOLDER / case['after_svg'])

    for relative, digest in read(FOLDER / 'source_sha256.json').items():
        assert sha(ROOT / relative) == digest, relative
    report = read(FOLDER / 'archive_recheck.json')
    assert report['case_count'] == report['passed'] == 355
    assert not report['comparison_with_previous_cli']['regressed']
    previous = ROOT / 'artifacts/evaluation/left_stem_labeled_square_recheck_v1'
    prior_cases = {c['variant']: c for c in read(previous / 'archive_recheck.json')['cases']}
    for case in report['cases']:
        path = FOLDER / case['output_svg']
        assert sha(path) == case['output_sha256']
        actual = measure(archive / records[case['variant']]['image'], path)
        assert actual['mean_delta2'] == case['mean_delta2']
        old = measure(archive / records[case['variant']]['image'], previous / prior_cases[case['variant']]['output_svg'])
        width, height = actual['dimensions']['width'], actual['dimensions']['height']
        assert np.array_equal(render(actual['svg'], width, height), render(old['svg'], width, height))
    restored = read(FOLDER / 'restored_prior_recheck.json')
    assert restored['case_count'] == restored['passed'] == 1
    restored_case = restored['cases'][0]
    restored_svg = FOLDER / restored_case['output_svg']
    assert sha(restored_svg) == restored_case['output_sha256']
    assert measure(archive / records['SE0082']['image'], restored_svg)['mean_delta2'] == restored_case['mean_delta2']

    summary = read(FOLDER / 'standard_profile_summary.json')
    nodes = list(ET.parse(FOLDER / 'standard_profile.xml').iter('testcase'))
    assert len(nodes) == summary['tests']
    assert sum(case.find('skipped') is not None for case in nodes) == summary['skipped']
    assert not any(case.find('failure') is not None or case.find('error') is not None for case in nodes)
    review = read(FOLDER / 'review/conversion_quality_review_v2.json')
    assert review['metrics']['successful_renderable_pairs'] == 48
    assert review['metrics']['successful_above_threshold'] == 0
    print('Verified: 9 regular catalog acceptances, 6 strict color passes, 2 x 17 independent cases, '
          '355 preserved prior records and reconversions, restored SE0082, complete default test evidence.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
