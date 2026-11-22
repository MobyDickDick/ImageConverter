"""Run the real GUI worker with a five-minute free-search profile."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from src.imageConverterGui import Jobs


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--profile',default='explore5')
    parser.add_argument('--publish',action='store_true')
    args=parser.parse_args()
    output=Path(__file__).resolve().parent
    jobs=Jobs(output/'gui-jobs')
    if not args.publish:
        jobs.publish_best=lambda *args:None
    try:
        uploaded=jobs.upload('AC0204_L.jpg',(ROOT/'artifacts/images_to_convert/AC0204_L.jpg').read_bytes())
        started=jobs.start(uploaded['id'],uploaded['description'],args.profile,seed=args.seed,use_current_svg=False)
        jobs.threads[-1].join(timeout=640)
        result=jobs.snapshot(started['id'])
        (output/f'gui-summary-{args.seed}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:result.get(k) for k in ('id','status','quality','message','pixel_quality','project_save','elapsed')},ensure_ascii=False))
        print('folder:',jobs.folder(result['id']))
        return 0 if result.get('result') and result.get('quality')=='passed' else 1
    finally:
        jobs.close()


if __name__=='__main__':
    raise SystemExit(main())
