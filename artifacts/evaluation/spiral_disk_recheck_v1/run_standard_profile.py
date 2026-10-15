"""Run the entire default collection in four fresh, balanced pytest processes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from xml.etree import ElementTree as ET
import argparse
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0',
               RUN_HEAVY_CONVERSION_TESTS='0', PYTHONUNBUFFERED='1')
    collected = subprocess.check_output([sys.executable, '-m', 'pytest', '--collect-only', '-q'],
                                        cwd=ROOT, env=env, text=True, encoding='utf-8')
    nodes = [line.strip() for line in collected.splitlines() if '::' in line]
    files = sorted({node.split('::')[0] for node in nodes})
    weights = {file: 1. for file in files}
    previous = ROOT/'artifacts/evaluation/flame_disk_recheck_v1/standard_profile.xml'
    for case in ET.parse(previous).iter('testcase'):
        file = case.get('classname').replace('.', '/')+'.py'
        if file in weights:
            weights[file] += float(case.get('time', 0))
    weights['tests/test_spiral_disk_runtime.py'] = 60
    shards, loads = [[] for _ in range(4)], [0.]*4
    for file in sorted(files, key=lambda file: -weights[file]):
        index = min(range(4), key=lambda index: loads[index])
        shards[index].append(file)
        loads[index] += weights[file]
    plan = dict(expected_nodes=nodes, shards=[dict(files=sorted(shard), estimated_seconds=loads[i])
                                            for i, shard in enumerate(shards)])
    (output/'plan.json').write_text(json.dumps(plan, indent=2)+'\n', encoding='utf-8')

    def run(index):
        command = [sys.executable, '-u', '-m', 'pytest', '-vv', '-o', 'faulthandler_timeout=90',
                   '--basetemp', str(output/f'tmp_{index}'), '--junitxml', str(output/f'shard_{index}.xml'),
                   *sorted(shards[index])]
        with (output/f'shard_{index}.log').open('w', encoding='utf-8') as log:
            process = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        result = dict(index=index, exit_code=process.returncode, command=command)
        (output/f'shard_{index}.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
        print('shard', index, 'exit', process.returncode, flush=True)
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, range(4)))
    (output/'results.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
    return 0 if all(result['exit_code'] == 0 for result in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
