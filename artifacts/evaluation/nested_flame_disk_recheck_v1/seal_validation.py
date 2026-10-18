"""Seal exact coverage of the freshly collected default test profile."""
from pathlib import Path
import argparse
import json
import shutil
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def node_id(case):
    parts = case.get('classname').split('.')
    for cut in range(len(parts), 0, -1):
        module = '/'.join(parts[:cut])+'.py'
        if (ROOT/module).exists():
            return '::'.join([module, *parts[cut:], case.get('name')])
    raise ValueError(case.attrib)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    args = parser.parse_args()
    checks = FOLDER/'checks'
    checks.mkdir(exist_ok=True)
    expected = set(read(args.profile/'plan.json')['expected_nodes'])
    cases = {}
    for i in range(4):
        stem = 'shard_0' if i == 0 else f'shard_parallel_{i}'
        assert read(args.profile/(stem+'.json'))['exit_code'] == 0
        for case in ET.parse(args.profile/(stem+'.xml')).iter('testcase'):
            node = node_id(case)
            assert node not in cases, node
            cases[node] = case
        for suffix in ('xml', 'log', 'json'):
            shutil.copyfile(args.profile/(stem+'.'+suffix), checks/f'shard_{i}.{suffix}')
    assert set(cases) == expected, (sorted(expected-set(cases)), sorted(set(cases)-expected))
    assert not any(c.find('failure') is not None or c.find('error') is not None for c in cases.values())
    skipped = sum(c.find('skipped') is not None for c in cases.values())
    suite = ET.Element('testsuite', tests=str(len(cases)), failures='0', errors='0', skipped=str(skipped))
    for node in sorted(cases):
        suite.append(cases[node])
    ET.ElementTree(suite).write(FOLDER/'standard_profile.xml', encoding='utf-8', xml_declaration=True)
    summary = dict(collected=len(expected), measured=len(cases), passed=len(cases)-skipped,
                   skipped=skipped, failed=0, exact_node_coverage=True)
    (FOLDER/'standard_profile_summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    shutil.copyfile(args.profile/'plan.json', checks/'plan.json')
    print(summary)


if __name__ == '__main__':
    main()
