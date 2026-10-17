"""Seal exact test-node coverage and all actual archive reconversion vectors."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys
from xml.etree import ElementTree as ET

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tools.evaluate_diagonal_square_kelle_recheck import measure
from tools.run_plan_b_variations import render


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def node_id(case):
    parts = case.get('classname').split('.')
    for cut in range(len(parts),0,-1):
        module = '/'.join(parts[:cut])+'.py'
        if (ROOT/module).exists():
            return '::'.join([module,*parts[cut:],case.get('name')])
    raise ValueError(case.attrib)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--archive',type=Path,required=True)
    args = parser.parse_args()
    checks = FOLDER/'checks'
    checks.mkdir(exist_ok=True)
    plan = read(args.profile/'plan.json')
    expected = set(plan['expected_nodes'])
    cases = {}
    for i in range(4):
        assert read(args.profile/f'shard_{i}.json')['exit_code'] == 0
        path = args.profile/f'shard_{i}.xml'
        for case in ET.parse(path).iter('testcase'):
            node = node_id(case)
            assert node not in cases, node
            cases[node] = case
        for suffix in ('xml','log','json'):
            shutil.copyfile(args.profile/f'shard_{i}.{suffix}',checks/f'shard_{i}.{suffix}')
    assert set(cases) == expected, (sorted(expected-set(cases)), sorted(set(cases)-expected))
    failed = [node for node,case in cases.items() if case.find('failure') is not None or case.find('error') is not None]
    skipped = [node for node,case in cases.items() if case.find('skipped') is not None]
    assert not failed
    suite = ET.Element('testsuite',tests=str(len(cases)),failures='0',errors='0',skipped=str(len(skipped)))
    for node in sorted(cases):
        suite.append(cases[node])
    ET.ElementTree(suite).write(FOLDER/'standard_profile.xml',encoding='utf-8',xml_declaration=True)
    save(FOLDER/'standard_profile_summary.json',dict(collected=len(expected),measured=len(cases),
        passed=len(cases)-len(skipped),skipped=len(skipped),failed=0,exact_node_coverage=True))
    shutil.copyfile(args.profile/'plan.json',checks/'plan.json')
    report = read(args.archive/'report.json')
    assert report['passed'] == report['case_count'] == 365
    for log in args.archive.glob('worker_*/*.log'):
        shutil.copyfile(log,checks/('archive_'+log.parent.name+'_'+log.name))
    index = read(ROOT/'artifacts/satisfactory_conversions/index.json')
    images = {c['variant']:ROOT/'artifacts/satisfactory_conversions'/c['image'] for c in index['cases']}
    previous_folder = ROOT/'artifacts/evaluation/upward_circle_linework_recheck_v1'
    previous = {p.stem:p for p in (previous_folder/'archive_reconverted_svgs').glob('*.svg')}
    for case in read(previous_folder/'manifest.json')['cases']:
        previous[Path(case['source']).stem] = previous_folder/case['after_svg']
    previous['SE0082'] = ROOT/'artifacts/evaluation/left_stem_labeled_square_recheck_v1/after.svg'
    assert len(previous) == 365
    destination = FOLDER/'archive_reconverted_svgs'
    destination.mkdir(exist_ok=True)
    for case in report['cases']:
        variant = case['variant']
        matches = [p for p in args.archive.glob('worker_*/*/converted_svg*/*.svg') if p.stem.casefold() == variant.casefold()]
        assert len(matches) == 1, (variant,len(matches))
        target = destination/(variant+'.svg')
        shutil.copyfile(matches[0],target)
        measured = measure(images[variant],target)
        assert measured['mean_delta2'] == case['mean_delta2']
        w,h = measured['dimensions']['width'],measured['dimensions']['height']
        old = previous[variant].read_text(encoding='utf-8')
        equal = bool(np.array_equal(render(measured['svg'],w,h),render(old,w,h)))
        case.update(output_svg=target.relative_to(FOLDER).as_posix(),output_sha256=sha(target),
                    previous_cli_svg=previous[variant].relative_to(ROOT).as_posix(),
                    previous_cli_svg_sha256=sha(previous[variant]),pixel_identical_to_previous_cli=equal)
    report['pixel_identical_count'] = sum(c['pixel_identical_to_previous_cli'] for c in report['cases'])
    save(FOLDER/'archive_recheck.json',report)
    print(read(FOLDER/'standard_profile_summary.json'))
    print('Archive:',report['passed'],'pixel-identical:',report['pixel_identical_count'])


if __name__ == '__main__':
    main()
