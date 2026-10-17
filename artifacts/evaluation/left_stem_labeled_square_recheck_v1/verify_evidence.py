"""Re-render saved vectors; no converter execution or reference access by runtime."""
from pathlib import Path
import hashlib
import json
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.evaluate_labeled_square_recheck import evaluate, labeled_square_semantics, measure
from tools.run_plan_b_variations import measure_quality, render


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = read(FOLDER/'manifest.json')
    report = evaluate(manifest, FOLDER)
    expected = read(FOLDER/'acceptance.json')
    assert report['baseline'] == expected['baseline']
    assert report['satisfaction_gate'] == expected['satisfaction_gate']
    assert report['evidence'] == expected['evidence']
    for case in manifest['cases']:
        image = FOLDER/case['image']
        assert sha(image) == case['source_sha256']
        strict = measure_quality(cv2.imread(str(image)), (FOLDER/case['after_svg']).read_text(encoding='utf-8'))
        assert strict == expected['strict_pixel_gate'] and strict['satisfactory']
    for path, digest in read(FOLDER/'source_sha256.json').items():
        assert sha(ROOT/path) == digest, path
    for directory in ('independent', 'independent_second_seed'):
        record = read(FOLDER/directory/'report.json')
        assert record['summary']['completed'] == record['summary']['passed'] == 17
        for case in record['cases']:
            folder = FOLDER/directory
            image = cv2.imread(str(folder/case['input_png']))
            vector = folder/case['output_svg']
            svg = vector.read_text(encoding='utf-8')
            assert sha(vector) == case['output_sha256']
            assert sha(folder/case['input_png']) == case['input_sha256']
            assert sha(folder/case['reference_svg']) == case['reference_svg_sha256']
            np.testing.assert_array_equal(image, render((folder/case['reference_svg']).read_text(encoding='utf-8'),
                                                       case['width'], case['height']))
            quality = measure_quality(image, svg)
            assert quality['satisfactory'] and quality['metrics'] == case['metrics']
            assert labeled_square_semantics(svg, 'P', 'left') == 1
            assert case['blocked_svg_reads'] == []
            assert case['registration']['render_evaluations'] > case['registration']['evaluations']
    catalog = read(FOLDER/'catalog_context/report.json')
    for case in catalog['cases']:
        assert sha(FOLDER/'catalog_context'/case['svg']) == case['output_sha256']
        assert case['blocked_svg_reads'] == []
    assert catalog['cases'][0]['output_sha256'] == catalog['cases'][1]['output_sha256']
    assert catalog['cases'][2]['output_sha256'] == sha(FOLDER/'after.svg')
    safety = read(FOLDER/'archive_safety.json')
    archive = ROOT/'artifacts/satisfactory_conversions'
    index = read(archive/'index.json')
    assert index['case_count'] == len(index['cases']) == safety['new_count'] == 356
    previous = {}
    for case in index['cases']:
        for field in ('image', 'svg'):
            assert sha(archive/case[field]) == case[field+'_sha256']
        previous[case['variant']] = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()
    assert len(safety['previous_record_hashes']) == safety['previous_count'] == 355
    assert all(previous[key] == value for key,value in safety['previous_record_hashes'].items())
    if (FOLDER/'archive_recheck.json').exists():
        recheck = read(FOLDER/'archive_recheck.json')
        assert recheck['passed'] == recheck['measured'] == 355 and not recheck['failures']
        images = {c['variant']:archive/c['image'] for c in index['cases']}
        previous_folder = ROOT/'artifacts/evaluation/conversion_search_2026-10-17'
        previous = {c['variant']:previous_folder/c['output_svg']
                    for c in read(previous_folder/'archive_recheck.json')['cases']}
        previous.update({Path(c['source']).stem:previous_folder/c['after_svg']
                         for c in read(previous_folder/'manifest.json')['cases']})
        for case in recheck['cases']:
            assert sha(FOLDER/case['output_svg']) == case['output_sha256']
            assert sha(previous[case['variant']]) == case['previous_cli_svg_sha256']
            measured = measure(images[case['variant']], FOLDER/case['output_svg'])
            assert measured['mean_delta2'] == case['mean_delta2']
            w, h = measured['dimensions']['width'], measured['dimensions']['height']
            old_svg = previous[case['variant']].read_text(encoding='utf-8')
            identical = bool(np.array_equal(render(measured['svg'], w, h), render(old_svg, w, h)))
            assert identical == case['pixel_identical_to_previous_cli']
    print('PASS: catalog gates, strict pixels, 34 independent CLI cases, source hashes and archive preservation')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
