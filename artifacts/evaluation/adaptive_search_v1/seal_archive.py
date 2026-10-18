"""Retain actual reconverted outputs without modifying the satisfactory archive."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('run',type=Path)
    args=parser.parse_args()
    report=json.loads((args.run/'report.json').read_text(encoding='utf-8'))
    assert report['case_count']==report['passed']==377
    folder=FOLDER/'archive_reconverted'
    folder.mkdir(exist_ok=True)
    for case in report['cases']:
        matches=[p for worker in args.run.glob('worker_*') for d in ('converted_svgs','converted_svg_failed')
            for p in (worker/case['execution_mode']/d).glob('*.svg') if p.stem.casefold()==case['variant'].casefold()]
        assert len(matches)==1,case['variant']
        target=folder/(case['variant']+'.svg')
        shutil.copyfile(matches[0],target)
        case['output_svg']=target.relative_to(FOLDER).as_posix()
        case['output_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    for worker in args.run.glob('worker_*'):
        for path in worker.glob('*.log'):
            shutil.copyfile(path,FOLDER/'checks_final'/(worker.name+'_'+path.name))
    (FOLDER/'archive_recheck.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('PASS:',report['passed'],'reconversions; original archive was not rewritten')

if __name__=='__main__':
    main()
