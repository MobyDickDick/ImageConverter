"""Seal complete test-node coverage and retain each real archive reconversion."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.evaluate_diagonal_square_kelle_recheck import measure
from tools.run_plan_b_variations import render
from seal_evidence import read, save, sha


def node_id(case):
    parts = case.get('classname').split('.')
    for cut in range(len(parts), 0, -1):
        module = '/'.join(parts[:cut])+'.py'
        if (ROOT/module).exists():
            return '::'.join([module, *parts[cut:], case.get('name')])
    raise ValueError(case.attrib)


def main():
    profile = ROOT/'.tmp/ls-standard-profile'
    cases = {}
    checks = FOLDER/'checks'
    checks.mkdir(exist_ok=True)
    for path in [*(profile/f'shard_{i}.xml' for i in range(4)), ROOT/'.tmp/ls-validation-tests.xml']:
        tree = ET.parse(path)
        for case in tree.iter('testcase'):
            cases[node_id(case)] = case  # Final affected-module rerun supersedes earlier imports.
        shutil.copyfile(path, checks/path.name)
    collection = subprocess.check_output([sys.executable, '-m', 'pytest', '--collect-only', '-q'],
                                         cwd=ROOT, text=True, encoding='utf-8')
    nodes = [line.strip() for line in collection.splitlines() if '::' in line]
    assert set(cases) == set(nodes) and len(nodes) == len(cases)
    assert not any(case.find('failure') is not None or case.find('error') is not None for case in cases.values())
    counts = dict(tests=len(cases), skipped=sum(c.find('skipped') is not None for c in cases.values()),
                  failures=0, errors=0)
    counts['passed'] = counts['tests']-counts['skipped']
    combined = ET.Element('testsuites')
    suite = ET.SubElement(combined, 'testsuite', name='final_standard_profile',
                          **{k:str(v) for k,v in counts.items() if k != 'passed'})
    for node in sorted(cases):
        suite.append(cases[node])
    ET.ElementTree(combined).write(FOLDER/'standard_profile.xml', encoding='utf-8', xml_declaration=True)
    save(FOLDER/'standard_profile_summary.json', dict(**counts, coverage='every current node exactly once',
         final_module_rerun='155 cases; includes 44 new cases',
         source_sha256=read(FOLDER/'source_sha256.json')))

    directory = ROOT/'.tmp/ls-archive'
    archive = read(directory/'report.json')
    assert archive['measured'] == archive['passed'] == archive['expected'] == 355
    assert not archive['failures']
    before = {p.stem:p for p in (FOLDER/'archive_previous_cli_svgs').glob('*.svg')}
    assert len(before) == 355
    index = read(ROOT/'artifacts/satisfactory_conversions/index.json')
    images = {c['variant']:ROOT/'artifacts/satisfactory_conversions'/c['image'] for c in index['cases']}
    outputs = FOLDER/'archive_reconverted_svgs'
    outputs.mkdir(exist_ok=True)
    comparison = dict(improved=[], unchanged=[], regressed=[])
    for case in archive['cases']:
        variant = case['variant']
        family = variant.split('_', 1)[0] if case['execution_mode'] == 'semantic-only' else 'compatibility'
        conversion = directory/family/case['execution_mode']
        matches = [p for folder in ('converted_svgs', 'converted_svg_failed')
                   for p in (conversion/folder).glob('*.svg') if p.stem.casefold() == variant.casefold()]
        assert len(matches) == 1, variant
        saved = outputs/(variant+'.svg')
        shutil.copyfile(matches[0], saved)
        case.update(output_svg=saved.relative_to(FOLDER).as_posix(), output_sha256=sha(saved),
                    previous_cli_svg_sha256=sha(before[variant]))
        actual = measure(images[variant], saved)
        old = measure(images[variant], before[variant])
        assert actual['mean_delta2'] == case['mean_delta2']
        w, h = actual['dimensions']['width'], actual['dimensions']['height']
        case['pixel_identical_to_previous_cli'] = bool(np.array_equal(render(actual['svg'], w, h), render(old['svg'], w, h)))
        delta = actual['mean_delta2']-old['mean_delta2']
        comparison['improved' if delta < -1e-6 else 'regressed' if delta > 1e-6 else 'unchanged'].append(variant)
    archive['comparison_with_previous_cli'] = comparison
    assert not comparison['regressed']
    save(FOLDER/'archive_recheck.json', archive)
    print('TESTS', counts, 'ARCHIVE', archive['passed'], {k:len(v) for k,v in comparison.items()})


if __name__ == '__main__':
    main()
=======
"""Seal complete test-node coverage and retain each real archive reconversion."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.evaluate_diagonal_square_kelle_recheck import measure
from tools.run_plan_b_variations import render
from seal_evidence import read, save, sha


def node_id(case):
    parts = case.get('classname').split('.')
    for cut in range(len(parts), 0, -1):
        module = '/'.join(parts[:cut])+'.py'
        if (ROOT/module).exists():
            return '::'.join([module, *parts[cut:], case.get('name')])
    raise ValueError(case.attrib)


def main():
    profile = ROOT/'.tmp/ls-standard-profile'
    cases = {}
    checks = FOLDER/'checks'
    checks.mkdir(exist_ok=True)
    for path in [*(profile/f'shard_{i}.xml' for i in range(4)), ROOT/'.tmp/ls-validation-tests.xml']:
        tree = ET.parse(path)
        for case in tree.iter('testcase'):
            cases[node_id(case)] = case  # Final affected-module rerun supersedes earlier imports.
        shutil.copyfile(path, checks/path.name)
    collection = subprocess.check_output([sys.executable, '-m', 'pytest', '--collect-only', '-q'],
                                         cwd=ROOT, text=True, encoding='utf-8')
    nodes = [line.strip() for line in collection.splitlines() if '::' in line]
    assert set(cases) == set(nodes) and len(nodes) == len(cases)
    assert not any(case.find('failure') is not None or case.find('error') is not None for case in cases.values())
    counts = dict(tests=len(cases), skipped=sum(c.find('skipped') is not None for c in cases.values()),
                  failures=0, errors=0)
    counts['passed'] = counts['tests']-counts['skipped']
    combined = ET.Element('testsuites')
    suite = ET.SubElement(combined, 'testsuite', name='final_standard_profile',
                          **{k:str(v) for k,v in counts.items() if k != 'passed'})
    for node in sorted(cases):
        suite.append(cases[node])
    ET.ElementTree(combined).write(FOLDER/'standard_profile.xml', encoding='utf-8', xml_declaration=True)
    save(FOLDER/'standard_profile_summary.json', dict(**counts, coverage='every current node exactly once',
         final_module_rerun='155 cases; includes 44 new cases',
         source_sha256=read(FOLDER/'source_sha256.json')))

    directory = ROOT/'.tmp/ls-archive'
    archive = read(directory/'report.json')
    assert archive['measured'] == archive['passed'] == archive['expected'] == 355
    assert not archive['failures']
    previous = read(ROOT/'artifacts/evaluation/conversion_search_2026-10-17/archive_recheck.json')
    before = {c['variant']:ROOT/'artifacts/evaluation/conversion_search_2026-10-17'/c['output_svg']
              for c in previous['cases']}
    old_short = read(ROOT/'artifacts/evaluation/conversion_search_2026-10-17/manifest.json')
    for case in old_short['cases']:
        before[Path(case['source']).stem] = ROOT/'artifacts/evaluation/conversion_search_2026-10-17'/case['after_svg']
    assert len(before) == 355
    index = read(ROOT/'artifacts/satisfactory_conversions/index.json')
    images = {c['variant']:ROOT/'artifacts/satisfactory_conversions'/c['image'] for c in index['cases']}
    outputs = FOLDER/'archive_reconverted_svgs'
    outputs.mkdir(exist_ok=True)
    comparison = dict(improved=[], unchanged=[], regressed=[])
    for case in archive['cases']:
        variant = case['variant']
        family = variant.split('_', 1)[0] if case['execution_mode'] == 'semantic-only' else 'compatibility'
        conversion = directory/family/case['execution_mode']
        matches = [p for folder in ('converted_svgs', 'converted_svg_failed')
                   for p in (conversion/folder).glob('*.svg') if p.stem.casefold() == variant.casefold()]
        assert len(matches) == 1, variant
        saved = outputs/(variant+'.svg')
        shutil.copyfile(matches[0], saved)
        case.update(output_svg=saved.relative_to(FOLDER).as_posix(), output_sha256=sha(saved),
                    previous_cli_svg_sha256=sha(before[variant]))
        actual = measure(images[variant], saved)
        old = measure(images[variant], before[variant])
        assert actual['mean_delta2'] == case['mean_delta2']
        w, h = actual['dimensions']['width'], actual['dimensions']['height']
        case['pixel_identical_to_previous_cli'] = bool(np.array_equal(render(actual['svg'], w, h), render(old['svg'], w, h)))
        delta = actual['mean_delta2']-old['mean_delta2']
        comparison['improved' if delta < -1e-6 else 'regressed' if delta > 1e-6 else 'unchanged'].append(variant)
    archive['comparison_with_previous_cli'] = comparison
    assert not comparison['regressed']
    save(FOLDER/'archive_recheck.json', archive)
    print('TESTS', counts, 'ARCHIVE', archive['passed'], {k:len(v) for k,v in comparison.items()})


if __name__ == '__main__':
    main()
