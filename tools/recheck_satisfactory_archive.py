"""Reconvert every archived satisfactory input from a disposable source copy."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys

import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure
from tools.refresh_satisfactory_archive import ARCHIVE, ROOT, digest
from tools.review_conversion_quality import DEFAULT_THRESHOLD


def recheck(archive: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError('Use a fresh recheck output directory')
    index=json.loads((archive/'index.json').read_text(encoding='utf-8'))
    if not index['cases']:
        raise ValueError('The satisfactory archive is empty')
    output.mkdir(parents=True)
    paths=[str(Path(np.__file__).resolve().parents[1]),str(ROOT),*sys.path]
    env=dict(os.environ,TINY_ICC_OUTPUT_VARIATION='0',PYTHONHASHSEED='0',IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0',ICC_FORCE_RECONVERT='1')
    results=[]
    for mode in ('semantic-only','standard'):
        cases=[c for c in index['cases'] if c['execution_mode']==mode]
        if not cases:
            continue
        inputs=output/(mode+'-inputs')
        inputs.mkdir()
        for case in cases:
            source=archive/case['image']
            if digest(source)!=case['image_sha256'] or digest(archive/case['svg'])!=case['svg_sha256']:
                raise ValueError(f"Archive hash mismatch: {case['variant']}")
            shutil.copyfile(source,inputs/source.name)
        conversion=output/mode
        with (output/(mode+'.log')).open('w',encoding='utf-8') as log:
            completed=subprocess.run([sys.executable,'-I','-c','import sys,runpy; sys.path[:0]='+repr(paths)+
                "; runpy.run_module('tools.recheck_satisfactory_archive',run_name='__main__')",'--_worker',mode,
                str(conversion),str(inputs),'--descriptions-path',str(archive/'descriptions.xml'),
                '--output-dir',str(conversion),'--execution-mode',mode,'--start','AC0000','--end','ZZ9999','--deterministic-order'],
                cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900,check=False)
        if completed.returncode:
            raise RuntimeError(f'Archive conversion failed: {mode}; see {output/(mode+".log")}')
        if mode == 'semantic-only':
            access=json.loads((output/'reference_access.json').read_text(encoding='utf-8'))
            if access['blocked_svg_reads']:
                raise ValueError('Archive reconversion attempted to read reference SVGs')
        for case in cases:
            variant=case['variant']
            matches=[p for directory in ('converted_svgs','converted_svg_failed') for p in (conversion/directory).glob('*.svg') if p.stem.casefold()==variant.casefold()]
            record=dict(variant=variant,execution_mode=mode,passed=False,reason='missing_svg')
            if len(matches)==1:
                measured=measure(archive/case['image'],matches[0])
                mse=measured['metrics']['error_per_pixel']
                passed=math.isfinite(mse) and mse<=DEFAULT_THRESHOLD and '<image' not in measured['svg'].lower()
                record.update(passed=passed,reason='quality_pass' if passed else 'quality_regression',
                              mean_delta2=measured['mean_delta2'],baseline_mean_delta2=case['mean_delta2'],metrics=measured['metrics'])
            results.append(record)
    report=dict(schema_version='satisfactory_archive_recheck_v1',case_count=len(results),
                passed=sum(c['passed'] for c in results),cases=results,threshold=DEFAULT_THRESHOLD)
    report['higher_mean_delta2']=[c['variant'] for c in results if 'mean_delta2' in c
        and c['mean_delta2']>c['baseline_mean_delta2']+max(1e-6,c['baseline_mean_delta2']*1e-6)]
    if (output/'reference_access.json').exists():
        report['reference_access']=json.loads((output/'reference_access.json').read_text(encoding='utf-8'))
    (output/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return report


def main() -> int:
    if len(sys.argv)>1 and sys.argv[1]=='--_worker':
        random.seed(0)
        np.random.seed(0)
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        if sys.argv[2]=='semantic-only':
            from tools.run_plan_b_variations import converter_worker
            return converter_worker(sys.argv[3:])
        from src.imageCompositeConverter import main as convert
        return convert(sys.argv[4:])
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,default=ROOT/ARCHIVE)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    report=recheck(args.archive.resolve(),args.output_dir.resolve())
    print(f"Satisfactory archive recheck: {report['passed']}/{report['case_count']}")
    return 0 if report['passed']==report['case_count'] else 2


if __name__=='__main__':
    raise SystemExit(main())
