"""Re-render saved CLI vectors and verify gates, hashes and exact test coverage."""
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
from tools.evaluate_labeled_disk_recheck import evaluate, symbol_semantics
from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_saved
from tools.run_plan_b_variations import render, measure_quality


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifests = []
    for folder in (FOLDER, FOLDER/'catalog_context'):
        manifest = read(folder/'manifest.json')
        manifests.append(manifest)
        actual, expected = evaluate(manifest, folder), read(folder/'acceptance.json')
        for key in ('baseline', 'evidence', 'satisfaction_gate', 'strict_pixel_gates'):
            assert actual[key] == expected[key], (folder, key)
        assert actual['satisfaction_gate']['summary']['satisfactory'] == 3
        assert all(c['satisfactory'] and not c['regressed_metrics'] for c in actual['satisfaction_gate']['cases'])
        assert all(c['satisfactory'] for c in actual['strict_pixel_gates'].values())
        assert all(not a['blocked_svg_reads'] for a in expected['reference_access'].values())
        for case in manifest['cases']:
            assert sha(folder/case['image']) == case['source_sha256']
    for neutral, named in zip(*[m['cases'] for m in manifests]):
        assert sha(FOLDER/neutral['after_svg']) == sha(FOLDER/'catalog_context'/named['after_svg'])
        for directory in ('images_to_convert', 'descriptions'):
            entries = ET.parse(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml').iter('entry')
            entry = next(e for e in entries if neutral['source'] in [p.text for p in e.findall('bilder/bild')])
            assert entry.findtext('beschreibung') == neutral['description']
    folder = FOLDER/'independent'
    report = read(folder/'report.json')
    assert report['summary']['passed'] == report['summary']['completed'] == 17
    for case in report['cases']:
        for key, digest in (('input_png', 'input_sha256'), ('output_svg', 'output_sha256'), ('reference_svg', 'reference_svg_sha256')):
            assert sha(folder/case[key]) == case[digest]
        image = cv2.imread(str(folder/case['input_png']))
        reference = (folder/case['reference_svg']).read_text(encoding='utf-8')
        np.testing.assert_array_equal(image, render(reference, case['width'], case['height']))
        svg = (folder/case['output_svg']).read_text(encoding='utf-8')
        quality = measure_quality(image, svg)
        assert quality['satisfactory'] and quality['metrics'] == case['metrics']
        assert symbol_semantics(svg, 'R', bottom_stem=True) == 1 and not case['blocked_svg_reads']
    archive = ROOT/'artifacts/satisfactory_conversions'
    index = read(archive/'index.json')
    records = {c['variant']: c for c in index['cases']}
    safety = read(FOLDER/'archive_safety.json')
    assert len(safety['previous_record_hashes']) == 371
    assert index['case_count'] == len(records) >= 374
    for variant, digest in safety['previous_record_hashes'].items():
        assert hashlib.sha256(json.dumps(records[variant], sort_keys=True).encode()).hexdigest() == digest
    for path, digest in safety['previous_file_hashes'].items():
        assert sha(archive/path) == digest
    for case in index['cases']:
        for key in ('image', 'svg'):
            assert sha(archive/case[key]) == case[key+'_sha256']
    reconverted = read(FOLDER/'archive_recheck.json')
    assert reconverted['case_count'] == reconverted['passed'] == len(reconverted['cases']) == 371
    assert all(c['pixels_equal_to_previous_cli'] for c in reconverted['cases'])
    control = read(FOLDER/'archive_control/report.json')
    assert sha(FOLDER/'parent_labeled_disk.py.txt') == control['parent_module_sha256']
    assert control['parent_commit'] == '8c0d2ab66' and control['search_seed'] == 0
    assert len(control['cases']) == 3
    assert all(not a['blocked_svg_reads'] for a in control['reference_access'].values())
    for case in control['cases']:
        before = FOLDER/'archive_control'/case['before_svg']
        after = FOLDER/'archive_control'/case['after_svg']
        assert sha(before) == sha(after) == case['output_sha256']
        assert records[case['variant']]['image_sha256'] == case['input_sha256']
    for case in reconverted['cases']:
        svg_path = FOLDER/'archive_reconverted_svgs'/(case['variant']+'.svg')
        assert sha(svg_path) == case['output_sha256']
        image = cv2.imread(str(archive/records[case['variant']]['image']))
        svg = svg_path.read_text(encoding='utf-8')
        raster = render(svg, image.shape[1], image.shape[0])
        assert hashlib.sha256(raster.tobytes()).hexdigest() == case['rendered_sha256']
        baseline = ROOT/case['previous_cli_svg']
        assert sha(baseline) == case['previous_cli_svg_sha256']
        np.testing.assert_array_equal(raster, render(baseline.read_text(encoding='utf-8'), image.shape[1], image.shape[0]))
        measured = measure_saved(archive/records[case['variant']]['image'], svg_path)
        assert measured['metrics'] == case['metrics'] and measured['mean_delta2'] == case['mean_delta2']
        assert measured['metrics']['error_per_pixel'] <= reconverted['threshold'] and '<image' not in svg.lower()
    from seal_validation import node_id
    expected = set(read(FOLDER/'checks/plan.json')['expected_nodes'])
    cases = list(ET.parse(FOLDER/'standard_profile.xml').iter('testcase'))
    assert len(cases) == len(expected) and {node_id(c) for c in cases} == expected
    assert not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
    assert all(c['exit_code'] == 0 for c in read(FOLDER/'checks/static_checks.json').values())
    assert read(FOLDER/'checks/conversion_smokes.json')['exit_code'] == 0
    print('PASS: six catalog comparisons, 17 independent CLI cases, 371 preserved and reconverted archive pairs, complete default tests')


if __name__ == '__main__':
    main()
