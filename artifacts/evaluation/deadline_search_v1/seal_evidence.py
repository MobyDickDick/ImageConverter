"""Retain actual archive outputs and merge the final test-module rerun."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.evaluate_diagonal_square_kelle_recheck import measure
from tools.run_deadline_evidence import verify as verify_cli


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def output_svg(run, case):
    matches = [p for worker in run.glob('worker_*') for directory in ('converted_svgs', 'converted_svg_failed')
               for p in (worker/case['execution_mode']/directory).glob('*.svg')
               if p.stem.casefold() == case['variant'].casefold()]
    assert len(matches) == 1, case['variant']
    return matches[0]


def seal_archive(run, direct):
    report, control = read(run/'report.json'), read(direct/'report.json')
    assert report['case_count'] == report['passed'] == control['case_count'] == control['passed'] == 377
    controls = {case['variant']: case for case in control['cases']}
    (FOLDER/'archive_outputs').mkdir(exist_ok=True)
    (FOLDER/'archive_direct_differences').mkdir(exist_ok=True)
    for case in report['cases']:
        target = FOLDER/'archive_outputs'/(case['variant']+'.svg')
        shutil.copyfile(output_svg(run, case), target)
        case['output_svg'] = target.relative_to(FOLDER).as_posix()
        case['output_sha256'] = sha(target)
        direct_svg = output_svg(direct, case)
        case['direct_sha256'] = sha(direct_svg)
        case['direct_mean_delta2'] = controls[case['variant']]['mean_delta2']
        case['byte_identical_to_direct'] = case['output_sha256'] == case['direct_sha256']
        case['direct_svg'] = case['output_svg']
        if not case['byte_identical_to_direct']:
            other = FOLDER/'archive_direct_differences'/target.name
            shutil.copyfile(direct_svg, other)
            case['direct_svg'] = other.relative_to(FOLDER).as_posix()
    report['worse_than_direct'] = [c['variant'] for c in report['cases']
                                 if c['mean_delta2'] > c['direct_mean_delta2']+1e-6]
    report['byte_identical_to_direct'] = sum(c['byte_identical_to_direct'] for c in report['cases'])
    (FOLDER/'archive_recheck.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    with zipfile.ZipFile(FOLDER/'archive_worker_logs.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for mode, folder in (('supervised', run), ('direct', direct)):
            for worker in folder.glob('worker_*'):
                for path in worker.glob('*.log'):
                    archive.write(path, mode+'/'+worker.name+'/'+path.name)


def node_id(case):
    parts = case.get('classname').split('.')
    for cut in range(len(parts), 0, -1):
        path = '/'.join(parts[:cut])+'.py'
        if (ROOT/path).exists():
            return '::'.join([path, *parts[cut:], case.get('name')])
    raise ValueError(case.attrib)


def seal_checks():
    checks = FOLDER/'checks'
    cases = [case for number in range(4) for case in ET.parse(checks/f'group_{number}.xml').iter('testcase')
             if not node_id(case).startswith('tests/test_conversion_deadline.py::')]
    cases.extend(ET.parse(checks/'deadline_final.xml').iter('testcase'))
    collection = subprocess.run([sys.executable, '-m', 'pytest', '--collect-only', '-q'], cwd=ROOT,
                                env=dict(os.environ, PYTHONIOENCODING='utf-8', ICC_SEARCH_SEED='20261018',
                                         IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0'),
                                capture_output=True, encoding='utf-8', check=True).stdout
    expected = [line for line in collection.splitlines() if line.startswith('tests/') and '::' in line]
    actual = [node_id(case) for case in cases]
    assert len(actual) == len(set(actual)) == len(expected) and set(actual) == set(expected)
    failed = sum(case.find('failure') is not None or case.find('error') is not None for case in cases)
    skipped = sum(case.find('skipped') is not None for case in cases)
    summary = dict(collected=len(expected), measured=len(cases), passed=len(cases)-skipped-failed,
                   failed=failed, skipped=skipped, exact_node_coverage=True,
                   note='Final deadline-module rerun replaces its earlier group entries')
    (checks/'release_summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    (checks/'release_nodes.json').write_text(json.dumps(actual, indent=2)+'\n', encoding='utf-8')
    assert failed == 0
    return summary


def verify():
    print(verify_cli(FOLDER))
    report = read(FOLDER/'archive_recheck.json')
    archive = ROOT/'artifacts/satisfactory_conversions'
    cases = {case['variant']: case for case in read(archive/'index.json')['cases']}
    frozen = read(ROOT/'artifacts/evaluation/adaptive_search_v1/archive_safety.json')
    assert len(cases) == len(frozen) == report['case_count'] == report['passed'] == 377
    for variant, record in cases.items():
        assert hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest() == frozen[variant]
        assert sha(archive/record['image']) == record['image_sha256']
        assert sha(archive/record['svg']) == record['svg_sha256']
    for case in report['cases']:
        image = archive/cases[case['variant']]['image']
        path = FOLDER/case['output_svg']
        assert sha(path) == case['output_sha256']
        assert sha(FOLDER/case['direct_svg']) == case['direct_sha256']
        measured = measure(image, path)
        assert measured['mean_delta2'] == case['mean_delta2']
        assert measured['metrics']['error_per_pixel'] <= report['threshold'] and '<image' not in measured['svg'].lower()
    assert not report['worse_than_direct']
    print('Archive:', report['passed'], 'passed;', report['byte_identical_to_direct'], 'identical to direct control')
    summary = read(FOLDER/'checks/release_summary.json')
    assert summary['failed'] == 0 and summary['exact_node_coverage']
    checks = FOLDER/'checks'
    measured = [case for number in range(4) for case in ET.parse(checks/f'group_{number}.xml').iter('testcase')
                if not node_id(case).startswith('tests/test_conversion_deadline.py::')]
    measured.extend(ET.parse(checks/'deadline_final.xml').iter('testcase'))
    nodes = [node_id(case) for case in measured]
    assert len(nodes) == len(set(nodes)) == summary['measured']
    assert set(nodes) == set(read(checks/'release_nodes.json'))
    assert not any(case.find('failure') is not None or case.find('error') is not None for case in measured)
    assert all(result['exit_code'] == 0 for result in read(checks/'static_checks.json').values())
    print('Tests:', summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive-run', type=Path)
    parser.add_argument('--direct-run', type=Path)
    parser.add_argument('--checks', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.archive_run:
        seal_archive(args.archive_run, args.direct_run)
    if args.checks:
        print(seal_checks())
    if args.verify:
        verify()
