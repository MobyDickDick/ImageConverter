import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from src.imageConverterGui import Jobs
if __name__=='__main__':
 profile=sys.argv[1] if len(sys.argv)>1 else 'thorough'
 seed=int(sys.argv[2]) if len(sys.argv)>2 else 2026
 out=Path(__file__).parent
 jobs=Jobs(out/'gui-jobs')
 publish=jobs.publish_best
 jobs.publish_best=lambda *args:None
 try:
  uploaded=jobs.upload('AC0204_L.jpg',(ROOT/'artifacts/images_to_convert/AC0204_L.jpg').read_bytes())
  started=jobs.start(uploaded['id'],uploaded['description'],profile,seed=seed,use_current_svg=profile not in {'explore5','explore10'})
  jobs.threads[-1].join(timeout=640)
  result=jobs.snapshot(started['id'])
  if result.get('quality')=='passed':
   publish(result['id']);result=jobs.snapshot(result['id'])
  (out/f'gui-{profile}-{seed}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps({k:result.get(k) for k in ('id','status','quality','message','project_save','elapsed','description_error')},ensure_ascii=True),flush=True)
 finally:jobs.close()
