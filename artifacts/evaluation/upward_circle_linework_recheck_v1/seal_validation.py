"""Retain complete test coverage and compare every prior CLI archive output."""
from pathlib import Path
import argparse
import shutil
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
        module = '/'.join(parts[:cut]) + '.py'
        if (ROOT / module).exists():
            return '::'.join([module, *parts[cut:], case.get('name')])
    raise ValueError(case.attrib)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--restored', type=Path)
    args = parser.parse_args()
    checks = FOLDER / 'checks'
    checks.mkdir(exist_ok=True)
    cases = {}
    for number in range(4):
        path = args.profile / f'shard_{number}.xml'
        for case in ET.parse(path).iter('testcase'):
            node = node_id(case)
            assert node not in cases
            cases[node] = case
        for suffix in ('xml', 'json', 'log'):
            shutil.copyfile(args.profile / f'shard_{number}.{suffix}', checks / f'shard_{number}.{suffix}')
    expected = read(args.profile / 'plan.json')['expected_nodes']
    assert set(cases) == set(expected) and len(cases) == len(expected)
    counts = dict(tests=len(cases), skipped=sum(c.find('skipped') is not None for c in cases.values()),
                  failures=sum(c.find('failure') is not None for c in cases.values()),
                  errors=sum(c.find('error') is not None for c in cases.values()))
    counts['passed'] = counts['tests'] - counts['skipped'] - counts['failures'] - counts['errors']
    assert counts['failures'] == counts['errors'] == 0
    combined = ET.Element('testsuites')
    suite = ET.SubElement(combined, 'testsuite', name='complete_default_profile',
                          **{k: str(v) for k, v in counts.items() if k != 'passed'})
    for node in sorted(cases):
        suite.append(cases[node])
    ET.ElementTree(combined).write(FOLDER / 'standard_profile.xml', encoding='utf-8', xml_declaration=True)
    save(FOLDER / 'standard_profile_summary.json', dict(**counts, coverage='every collected node exactly once'))
    save(checks / 'plan.json', read(args.profile / 'plan.json'))
    if args.archive is None:
        print('TESTS', counts)
        return 0
    if args.restored is None:
        raise ValueError('--archive also requires --restored')

    archive = read(args.archive / 'report.json')
    assert archive['case_count'] == archive['passed'] == 355
    previous_folder = ROOT / 'artifacts/evaluation/left_stem_labeled_square_recheck_v1'
    previous = {c['variant']: previous_folder / c['output_svg']
                for c in read(previous_folder / 'archive_recheck.json')['cases']}
    index_folder = ROOT / 'artifacts/satisfactory_conversions'
    index = {c['variant']: c for c in read(index_folder / 'index.json')['cases']}
    assert set(previous) == {c['variant'] for c in archive['cases']}
    output = FOLDER / 'archive_reconverted_svgs'
    output.mkdir(exist_ok=True)
    comparison = dict(improved=[], unchanged=[], regressed=[])
    for case in archive['cases']:
        variant, mode = case['variant'], case['execution_mode']
        matches = [path for worker in args.archive.glob('worker_*')
                   for directory in ('converted_svgs', 'converted_svg_failed')
                   for path in (worker / mode / directory).glob('*.svg')
                   if path.stem.casefold() == variant.casefold()]
        assert len(matches) == 1, variant
        saved = output / (variant + '.svg')
        shutil.copyfile(matches[0], saved)
        image = index_folder / index[variant]['image']
        actual, old = measure(image, saved), measure(image, previous[variant])
        assert actual['mean_delta2'] == case['mean_delta2']
        w, h = actual['dimensions']['width'], actual['dimensions']['height']
        identical = bool(np.array_equal(render(actual['svg'], w, h), render(old['svg'], w, h)))
        case.update(output_svg=saved.relative_to(FOLDER).as_posix(), output_sha256=sha(saved),
                    previous_cli_svg_sha256=sha(previous[variant]), pixel_identical_to_previous_cli=identical)
        delta = actual['mean_delta2'] - old['mean_delta2']
        comparison['improved' if delta < -1e-6 else 'regressed' if delta > 1e-6 else 'unchanged'].append(variant)
    archive['comparison_with_previous_cli'] = comparison
    save(FOLDER / 'archive_recheck.json', archive)
    assert not comparison['regressed']

    restored = read(args.restored / 'report.json')
    assert restored['case_count'] == restored['passed'] == 1
    case = restored['cases'][0]
    saved = output / 'SE0082.svg'
    shutil.copyfile(args.restored / 'semantic-only/converted_svgs/SE0082.svg', saved)
    case.update(output_svg=saved.relative_to(FOLDER).as_posix(), output_sha256=sha(saved))
    save(FOLDER / 'restored_prior_recheck.json', restored)
    print('TESTS', counts, 'ARCHIVE', archive['passed'], {key: len(value) for key, value in comparison.items()})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
