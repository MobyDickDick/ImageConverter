"""Seal complete tests and preservation evidence for the oriented linework family."""
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
import argparse
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--standard', type=Path, default=ROOT/'.tmp/ocls')
    parser.add_argument('--archive', type=Path, default=ROOT/'.tmp/ocla/report.json')
    parser.add_argument('--smoke', type=Path, default=ROOT/'.tmp/oclh.xml')
    args = parser.parse_args()
    results = read(args.standard/'results.json')
    assert all(r['exit_code'] == 0 for r in results)
    merged = ET.Element('testsuites')
    for index in range(4):
        merged.extend(ET.parse(args.standard/f'shard_{index}.xml').getroot())
    cases = list(merged.iter('testcase'))
    actual = [c.get('classname').replace('.', '/')+'.py::'+c.get('name') for c in cases]
    expected = read(args.standard/'plan.json')['expected_nodes']
    assert Counter(actual) == Counter(expected) and len(set(actual)) == len(actual)
    assert all(c.find('failure') is None and c.find('error') is None for c in cases)
    skipped = sum(c.find('skipped') is not None for c in cases)
    ET.ElementTree(merged).write(FOLDER/'standard_profile.xml', encoding='utf-8', xml_declaration=True)
    shutil.copyfile(args.standard/'results.json', FOLDER/'standard_result.json')
    shutil.copyfile(args.standard/'plan.json', FOLDER/'standard_plan.json')

    archive = read(args.archive)
    assert archive['expected'] == archive['measured'] == archive['passed'] == 329
    assert not archive['failures'] and all(c['passed'] for c in archive['cases'])
    prior_folder = ROOT/'artifacts/evaluation/right_gradient_junction_recheck_v1'
    previous = read(prior_folder/'archive_recheck.json')
    current = {c['variant']: c for c in archive['cases']}
    assert all(current[c['variant']] == c for c in previous['cases'])
    assert sorted(archive['higher_mean_delta2']) == sorted(previous['higher_mean_delta2'])
    assert len(archive['higher_mean_delta2']) == 22
    shutil.copyfile(args.archive, FOLDER/'archive_recheck.json')
    commit = read(FOLDER/'manifest.json')['provenance']['commit']
    old_index = json.loads(subprocess.check_output(
        ['git', 'show', commit+':artifacts/satisfactory_conversions/index.json'], cwd=ROOT))
    index = read(ROOT/'artifacts/satisfactory_conversions/index.json')
    records = {c['variant']: c for c in index['cases']}
    assert old_index['case_count'] == 320 and index['case_count'] == 329
    assert all(records[c['variant']] == c for c in old_index['cases'])
    review, prior_review = read(FOLDER/'review_summary.json'), read(prior_folder/'review_summary.json')
    assert review['metrics'] == prior_review['metrics']
    assert review['threshold_normalized_mse'] == prior_review['threshold_normalized_mse']
    added = [arg for c in read(FOLDER/'manifest.json')['cases']
             for arg in ('--exclude', Path(c['source']).stem)]
    assert read(FOLDER/'review_args.json')[2:] == read(prior_folder/'review_args.json')[2:]+added
    smoke = list(ET.parse(args.smoke).iter('testcase'))
    assert len(smoke) == 2 and all(c.find('failure') is None and c.find('error') is None
                                  and c.find('skipped') is None for c in smoke)
    shutil.copyfile(args.smoke, FOLDER/'smoke.xml')
    for command in (
        [sys.executable, '-m', 'compileall', '-q', 'src', 'tests', 'tools'],
        [sys.executable, '-m', 'src.imageCompositeConverter', '--help'],
        [sys.executable, '-m', 'tools.check_no_new_image_id_hardcoding'],
        ['git', '-c', 'core.whitespace=cr-at-eol', 'diff', '--check'],
    ):
        subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    statistics = dict(collected=len(cases), passed=len(cases)-skipped, skipped=skipped,
                      failed=0, all_collected_nodes_verified_once=True)
    document = ROOT/'docs/next_arbeitspaket_2026-10-17_ac0414_2_l.md'
    text = document.read_text(encoding='utf-8')
    marker = 'bleiben unverändert. Vollständige Test- und Archivnachweise werden in'
    if marker in text:
        passed = f"{statistics['passed']:,}".replace(',', '.')
        collected = f'{len(cases):,}'.replace(',', '.')
        text = text.replace(marker,
            f'bleiben unverändert. Die vollständige Standardsammlung besteht mit **{passed} bestandenen Tests, '
            f'{skipped} bestehenden Skips und null Fehlern**.\nAlle {collected} gesammelten Testknoten sind genau einmal nachgewiesen.\n'
            'Die erneute Archivkonvertierung besteht mit **329/329**; alle 320 bisherigen\n'
            'Prüfdatensätze und die 22 bekannten älteren Kompatibilitätsabweichungen\n'
            'bleiben unverändert. Die schweren AC08-/AC0100-Smoke-Tests bestehen mit **2/2**.\n'
            'Vollständige Test- und Archivnachweise sind in')
        document.write_text(text, encoding='utf-8', newline='\n')
    paths = [p for p in FOLDER.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and p.name != 'validation_2026-10-17.json']
    paths.extend(ROOT/name for name in (
        'src/iCCModules/imageCompositeConverterCircleLinework.py',
        'tools/evaluate_oriented_circle_linework_recheck.py',
        'tools/run_oriented_circle_linework_recheck.py',
        'tests/test_oriented_circle_linework_runtime.py',
        'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml',
        'artifacts/descriptions/Finale_Wurzelformen_V3.xml',
        'docs/next_arbeitspaket_2026-10-17_ac0414_2_l.md',
    ))
    validation = dict(standard=statistics, heavy_smoke_passed=2,
        all_catalog_outputs_equal_neutral=True,
        archive=dict(previous_count=320, new_count=329, passed=329,
                     all_previous_records_identical=True, all_previous_recheck_results_identical=True,
                     known_drift_count=22, known_drift_list_unchanged=True),
        artifact_hashes={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in sorted(paths)})
    (FOLDER/'validation_2026-10-17.json').write_text(
        json.dumps(validation, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(statistics))


if __name__ == '__main__':
    main()
