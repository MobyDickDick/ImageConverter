"""Seal and verify saved development results without rerunning a converter."""
import argparse
import json
import csv
import shutil
from pathlib import Path

from tools.evaluate_curve_proposals import EVIDENCE,ROOT,CURRENT_MODULES,verified
from tools.evaluate_curve_checker import digest,write_json


def seal_results(folder=EVIDENCE):
    verified(folder)
    results=folder/'results'
    review=results/'review'
    if review.exists():
        raise ValueError('Results already sealed')
    review.mkdir()
    for name in ['replay_baseline','replay_current','controls','legacy','cli','cli_serial']:
        for path in (results/name).rglob('*'):
            if path.is_file() and (path.suffix=='.svg' or path.name=='summary.json'):
                target=review/path.relative_to(results)
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(path,target)
    for name in ['targeted-tests.txt','core-tests.txt']:
        shutil.copyfile(results/name,review/name)
    processes={}
    for arm in ['cli','cli_serial']:
        rows=[]
        data=json.loads((results/arm/'summary.json').read_text(encoding='utf-8'))
        for row in data['results']:
            path=results/arm/row['case_id']/'conversion/reports/batch_failure_summary.csv'
            with path.open(encoding='utf-8') as stream:
                failures=list(csv.DictReader(stream,delimiter=';'))
            rows.append(dict(case_id=row['case_id'],batch_failures=failures,
                clean_process_completion=row.get('returncode')==0 and not failures))
        processes[arm]=rows
    write_json(review/'process_summary.json',processes)
    sources=review/'sources'
    sources.mkdir()
    for name in CURRENT_MODULES:
        (sources/name).write_bytes((ROOT/'src/iCCModules'/name).read_bytes())
    for name in ['evaluate_curve_proposals.py','curve_proposal_cases.py','verify_curve_proposal_evidence.py']:
        (sources/name).write_bytes((ROOT/'tools'/name).read_bytes())
    (sources/'test_curve_proposals.py').write_bytes((ROOT/'tests/test_curve_proposals.py').read_bytes())
    write_json(review/'seal.json',dict(schema='curve_proposal_compact_results_seal_v1',
        manifest_sha256=digest(folder/'manifest.json'),
        files={p.relative_to(review).as_posix():digest(p) for p in sorted(review.rglob('*')) if p.is_file()}))


def verify_results(folder=EVIDENCE):
    verified(folder)
    results=folder/'results/review'
    seal=json.loads((results/'seal.json').read_text(encoding='utf-8'))
    if seal['manifest_sha256']!=digest(folder/'manifest.json'):
        raise ValueError('Changed result manifest')
    actual={p.relative_to(results).as_posix() for p in results.rglob('*') if p.is_file()}-{'seal.json'}
    if actual!=set(seal['files']):
        raise ValueError('Added or missing result evidence')
    for name,sha in seal['files'].items():
        path=(results/name).resolve()
        if not path.is_relative_to(results.resolve()) or digest(path)!=sha:
            raise ValueError('Changed curve result: '+name)
    for name in ['replay_baseline','replay_current','cli','cli_serial','controls','legacy']:
        data=json.loads((results/name/'summary.json').read_text(encoding='utf-8'))
        if data.get('real_reserves_executed',False) or data.get('model_promotions',0):
            raise ValueError('Invalid release state')
    return seal


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal',action='store_true')
    args=parser.parse_args()
    if args.seal:
        seal_results()
    seal=verify_results()
    print(str(len(seal['files']))+' curve result files verified')
