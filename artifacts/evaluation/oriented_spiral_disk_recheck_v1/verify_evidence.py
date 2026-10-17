"""Re-render saved vectors; verify sources, topology, gates and CLI evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
from collections import Counter
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import cv2
from tools.evaluate_oriented_spiral_disk_recheck import evaluate, symbol_semantics
from tools.run_plan_b_variations import render, measure_quality


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-validation-seal', action='store_true')
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    saved = json.loads((folder/'report.json').read_text(encoding='utf-8'))
    measured = evaluate(manifest, folder)
    for key in ('evidence', 'satisfaction_gate', 'strict_pixel_gates'):
        assert measured[key] == saved[key], key
    assert all(case['satisfactory'] and not case['regressed_metrics']
               for case in measured['satisfaction_gate']['cases'])
    gray = {case['case_id'] for case in manifest['cases']
            if case['source'] in ('AC0424_L.jpg', 'AC0424_M.jpg', 'AC0424_S.jpg')}
    assert {key for key, gate in measured['strict_pixel_gates'].items() if not gate['satisfactory']} == gray
    assert all(measured['strict_pixel_gates'][key]['failures'] == ['foreground_iou_outside_limit'] for key in gray)
    assert all(not side['blocked_svg_reads'] for side in saved['reference_access'].values())
    for case in manifest['cases']:
        assert digest(folder/case['image']) == case['source_sha256']
    inventory = json.loads((folder/'source_inventory.json').read_text(encoding='utf-8'))
    for case in inventory:
        assert digest(ROOT/'artifacts/images_to_convert'/case['source']) == case['source_sha256']

    context = folder/'catalog_context'
    cm = json.loads((context/'manifest.json').read_text(encoding='utf-8'))
    cs = json.loads((context/'report.json').read_text(encoding='utf-8'))
    cr = evaluate(cm, context)
    for key in ('evidence', 'satisfaction_gate', 'strict_pixel_gates'):
        assert cr[key] == cs[key]
    assert all(not side['blocked_svg_reads'] for side in cs['reference_access'].values())
    for actual, neutral in zip(cm['cases'], manifest['cases']):
        assert (context/actual['after_svg']).read_bytes() == (folder/neutral['after_svg']).read_bytes()

    for index in (1, 2):
        run = folder/'plan_b'/f'run_{index}'
        report = json.loads((run/'report.json').read_text(encoding='utf-8'))
        assert report['summary'] == dict(completed=17, failed=0, passed=17, required=17, satisfactory=True)
        assert digest(run/'source.png') == report['source_image_sha256']
        # The driver hashes the decoded input SVG; write_text uses native EOLs.
        assert hashlib.sha256((run/'source.svg').read_text(encoding='utf-8').encode('utf-8')).hexdigest() == report['source_svg_sha256']
        for case in report['cases']:
            assert case['satisfactory'] and not case['blocked_svg_reads']
            assert digest(run/case['output_svg']) == case['output_sha256']
            assert digest(run/case['reference_svg']) == case['reference_svg_sha256']
            image = render((run/case['reference_svg']).read_text(encoding='utf-8'), case['width'], case['height'])
            ok, png = cv2.imencode('.png', image)
            assert ok and hashlib.sha256(png.tobytes()).hexdigest() == case['input_sha256']
            output = (run/case['output_svg']).read_text(encoding='utf-8')
            quality = measure_quality(image, output)
            assert quality['satisfactory'] and quality['metrics'] == case['metrics']
            assert symbol_semantics(output, 'left') == 1

    if not args.skip_validation_seal:
        validation = json.loads((folder/'validation_2026-10-17.json').read_text(encoding='utf-8'))
        for name, expected in validation['artifact_hashes'].items():
            assert digest(ROOT/name) == expected, name
        archive = json.loads((folder/'archive_recheck.json').read_text(encoding='utf-8'))
        assert archive['expected'] == archive['measured'] == archive['passed'] == 352
        assert not archive['failures']
        assert archive['prior_archive_comparison']['unchanged_results'] == 343
        assert len(archive['higher_mean_delta2']) == 22
        from tools.evaluate_diagonal_square_kelle_recheck import measure
        from tools.review_conversion_quality import DEFAULT_THRESHOLD
        index = json.loads((ROOT/'artifacts/satisfactory_conversions/index.json').read_text(encoding='utf-8'))
        sources = {case['variant']: case for case in index['cases']}
        prior_report = ROOT/archive['prior_archive_comparison']['baseline']
        assert digest(prior_report) == archive['prior_archive_comparison']['baseline_sha256']
        prior = {case['variant']: case for case in json.loads(prior_report.read_text(encoding='utf-8'))['cases']}
        assert Counter(case['variant'] for case in archive['cases']) == Counter(sources.keys())
        unchanged = 0
        for case in archive['cases']:
            source = sources[case['variant']]
            vector = folder/case['output_svg']
            assert digest(vector) == case['output_sha256']
            image_path = ROOT/'artifacts/satisfactory_conversions'/source['image']
            assert digest(image_path) == source['image_sha256']
            value = measure(image_path, vector)
            assert value['mean_delta2'] == case['mean_delta2'] and value['metrics'] == case['metrics']
            assert value['metrics']['error_per_pixel'] <= DEFAULT_THRESHOLD
            assert '<image' not in value['svg'].lower()
            if case['variant'] in prior:
                old = prior[case['variant']]
                assert all(old[key] == case[key] for key in ('mean_delta2', 'metrics', 'output_sha256', 'passed'))
                unchanged += 1
        assert unchanged == 343
        cases = list(ET.parse(folder/'standard_profile.xml').iter('testcase'))
        plan = json.loads((folder/'standard_plan.json').read_text(encoding='utf-8'))
        actual = [case.get('classname').replace('.', '/')+'.py::'+case.get('name') for case in cases]
        assert Counter(actual) == Counter(plan['expected_nodes'])
        assert all(case.find('failure') is None and case.find('error') is None for case in cases)
        assert sum(case.find('skipped') is not None for case in cases) == validation['standard']['skipped']
    print('Nine regular acceptances, three separate strict gray failures, catalog equality and two 17-case CLI batteries verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
