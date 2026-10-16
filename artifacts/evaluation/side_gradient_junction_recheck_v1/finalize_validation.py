"""Seal completed test and archive evidence; reject missing or changed cases."""
from pathlib import Path
from xml.etree import ElementTree as ET
from collections import Counter
import hashlib
import json
import shutil
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    standard = ROOT/'.tmp/sdstd'
    results = read(standard/'results.json')
    assert all(result['exit_code'] == 0 for result in results)
    merged = ET.Element('testsuites')
    for number in range(4):
        for suite in ET.parse(standard/f'shard_{number}.xml').getroot():
            merged.append(suite)
    cases = list(merged.iter('testcase'))
    actual = [c.get('classname').replace('.', '/')+'.py::'+c.get('name') for c in cases]
    expected = read(standard/'plan.json')['expected_nodes']
    assert Counter(actual) == Counter(expected) and len(set(actual)) == len(actual)
    assert all(c.find('failure') is None and c.find('error') is None for c in cases)
    skipped = sum(c.find('skipped') is not None for c in cases)
    ET.ElementTree(merged).write(FOLDER/'standard_profile.xml', encoding='utf-8', xml_declaration=True)
    shutil.copyfile(standard/'results.json', FOLDER/'standard_result.json')

    archive = read(ROOT/'.tmp/sda/report.json')
    assert archive['expected'] == archive['measured'] == archive['passed'] == 302
    assert not archive['failures'] and all(c['passed'] for c in archive['cases'])
    previous_folder = ROOT/'artifacts/evaluation/gradient_junction_recheck_v1'
    previous = read(previous_folder/'archive_recheck.json')
    current_by_name = {c['variant']: c for c in archive['cases']}
    assert all(current_by_name[c['variant']] == c for c in previous['cases'])
    assert sorted(archive['higher_mean_delta2']) == sorted(previous['higher_mean_delta2'])
    assert len(archive['higher_mean_delta2']) == 22
    shutil.copyfile(ROOT/'.tmp/sda/report.json', FOLDER/'archive_recheck.json')
    old_index = json.loads(subprocess.check_output(
        ['git','show','3297925e2:artifacts/satisfactory_conversions/index.json'], cwd=ROOT, text=True, encoding='utf-8'))
    index = read(ROOT/'artifacts/satisfactory_conversions/index.json')
    records = {c['variant']: c for c in index['cases']}
    assert old_index['case_count'] == 288 and index['case_count'] == 302
    assert all(records[c['variant']] == c for c in old_index['cases'])

    smoke_cases = list(ET.parse(ROOT/'.tmp/side-smoke.xml').iter('testcase'))
    assert len(smoke_cases) == 2 and all(
        c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in smoke_cases)
    shutil.copyfile(ROOT/'.tmp/side-smoke.xml', FOLDER/'smoke.xml')
    checks = [
        [sys.executable,'-m','compileall','-q','src','tests','tools'],
        [sys.executable,'-m','src.imageCompositeConverter','--help'],
        [sys.executable,'-m','tools.check_no_new_image_id_hardcoding'],
        ['git','-c','core.whitespace=cr-at-eol','diff','--check'],
    ]
    for command in checks:
        subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    statistics = dict(collected=len(cases), passed=len(cases)-skipped, skipped=skipped,
                      failed=0, all_collected_nodes_verified_once=True)
    document = ROOT/'docs/next_arbeitspaket_2026-10-16_ge9034_6m.md'
    text = document.read_text(encoding='utf-8')
    old = ('bleiben unverändert. Abschlusszahlen und Artefakthashes werden in\n'
           '`artifacts/evaluation/side_gradient_junction_recheck_v1/validation_2026-10-16.json`\n'
           'festgehalten.')
    passed_text = f'{statistics["passed"]:,}'.replace(',', '.')
    count_text = f'{len(cases):,}'.replace(',', '.')
    new = (f'bleiben unverändert. Die vollständige Standardsammlung besteht mit **{passed_text} '
           f'bestandenen Tests, {skipped} bestehenden Skips und null Fehlern**. '
           f'Alle {count_text} gesammelten Testknoten sind genau einmal nachgewiesen. '
           'Die erneute Archivkonvertierung besteht mit **302/302**; alle 288 bisherigen '
           'Prüfdatensätze und die 22 bekannten älteren Kompatibilitätsabweichungen bleiben '
           'unverändert. Abschlusszahlen und Artefakthashes stehen in\n'
           '`artifacts/evaluation/side_gradient_junction_recheck_v1/validation_2026-10-16.json`.')
    if old in text:
        document.write_text(text.replace(old,textwrap.fill(new,width=80,
            break_long_words=False,break_on_hyphens=False)), encoding='utf-8', newline='\n')
    paths = [p for p in FOLDER.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and p.name != 'validation_2026-10-16.json']
    paths.extend(ROOT/name for name in (
        'src/iCCModules/imageCompositeConverterGradientJunction.py',
        'tools/evaluate_gradient_junction_recheck.py', 'tests/test_side_gradient_junction_runtime.py',
        'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml',
        'artifacts/descriptions/Finale_Wurzelformen_V3.xml',
        'artifacts/satisfactory_conversions/index.json',
        'artifacts/satisfactory_conversions/descriptions.xml',
        'docs/next_arbeitspaket_2026-10-16_ge9034_6m.md'))
    validation = dict(schema_version='side_gradient_junction_completion_v1', standard=statistics,
        smoke_passed=2, local_checks=checks, all_catalog_outputs_equal_neutral=True,
        archive=dict(previous_count=288,new_count=302,passed=302,known_drift_count=22,
            all_previous_records_identical=True,all_previous_recheck_results_identical=True,
            known_drift_list_unchanged=True),
        rotation=dict(next_candidates=[c['variant'] for c in read(FOLDER/'review_summary.json')['selected_candidates']]),
        artifact_hashes={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in sorted(paths)})
    (FOLDER/'validation_2026-10-16.json').write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(statistics, sort_keys=True))


if __name__ == '__main__':
    main()
