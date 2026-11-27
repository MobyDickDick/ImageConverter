"""Run one deterministic file shard of the complete ordinary pytest suite in CI.

The existing heavy conversion jobs execute the three explicitly heavy modules.
No failing node or ordinary test module is filtered by this runner.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--shard',type=int,required=True)
    parser.add_argument('--shards',type=int,default=8)
    args=parser.parse_args()
    if not 0<=args.shard<args.shards:
        parser.error('Invalid shard')
    heavy={'test_image_composite_converter.py','test_satisfactory_regression_battery.py',
           'test_conversion_regression_smoke.py'}
    files=sorted(str(p) for p in Path('tests').rglob('test_*.py') if p.name not in heavy)
    selected=files[args.shard::args.shards]
    folder=Path('ci-suite')/f'shard-{args.shard}'
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'files.txt').write_text('\n'.join(selected)+'\n',encoding='utf-8')
    print(f'{len(selected)} modules in shard {args.shard}/{args.shards}',flush=True)
    return subprocess.call([sys.executable,'-m','pytest','-q','-ra',*selected,
        '--basetemp',str(folder/'temporary'),f'--junitxml={folder}/results.xml'])


if __name__=='__main__':
    raise SystemExit(main())
