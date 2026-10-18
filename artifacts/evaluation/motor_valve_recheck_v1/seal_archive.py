"""Save actual archive outputs and compare them with the previous CLI evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tools.run_plan_b_variations import render

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('run',type=Path)
    args=parser.parse_args()
    report=json.loads((args.run/'report.json').read_text(encoding='utf-8'))
    assert report['case_count']==report['passed']==374
    archive=ROOT/'artifacts/satisfactory_conversions'
    entries={c['variant']:c for c in json.loads((archive/'index.json').read_text(encoding='utf-8'))['cases']}
    previous=ROOT/'artifacts/evaluation/bottom_stem_letter_disk_recheck_v1/archive_reconverted_svgs'
    target=FOLDER/'archive_reconverted_svgs'
    target.mkdir(exist_ok=True)
    checked=0
    for case in report['cases']:
        variant=case['variant']
        matches=[p for worker in args.run.glob('worker_*')
            for d in ('converted_svgs','converted_svg_failed')
            for p in (worker/case['execution_mode']/d).glob('*.svg') if p.stem.casefold()==variant.casefold()]
        assert len(matches)==1,(variant,matches)
        output=target/(variant+'.svg')
        shutil.copyfile(matches[0],output)
        case['output_svg']=output.relative_to(FOLDER).as_posix()
        case['output_sha256']=sha(output)
        image=cv2.imread(str(archive/entries[variant]['image']))
        h,w=image.shape[:2]
        actual=render(output.read_text(encoding='utf-8'),w,h)
        case['rendered_sha256']=hashlib.sha256(actual.tobytes()).hexdigest()
        old=previous/(variant+'.svg')
        if old.exists():
            case['previous_cli_svg']=old.relative_to(ROOT).as_posix()
            case['previous_cli_svg_sha256']=sha(old)
            old_raster=render(old.read_text(encoding='utf-8'),w,h)
            case['pixels_equal_to_previous_cli']=np.array_equal(actual,old_raster)
            assert case['pixels_equal_to_previous_cli'],variant
            checked+=1
    assert checked==371,checked
    report['compared_to_previous_cli']=checked
    (FOLDER/'archive_recheck.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    for worker in args.run.glob('worker_*'):
        for path in worker.glob('*.log'):
            shutil.copyfile(path,FOLDER/'checks'/(worker.name+'_'+path.name))
    print('PASS:',report['passed'],'archive cases;',checked,'previous CLI outputs pixel-identical')

if __name__=='__main__':
    main()
