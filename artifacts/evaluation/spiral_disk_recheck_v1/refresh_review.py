"""Freshly remeasure the previous review inventory and advance accepted cases."""
from pathlib import Path
import csv,json,sys,os
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT)); os.chdir(ROOT)
from tools.review_conversion_quality import review_variant,select_plan_b_candidates,write_reports,DEFAULT_THRESHOLD
previous=ROOT/'artifacts/evaluation/flame_disk_recheck_v1'
output=Path(__file__).resolve().parent
args=json.loads((previous/'review_args.json').read_text(encoding='utf-8'))
args[args.index('--output-dir')+1]=str(output.relative_to(ROOT))
manifest=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
for case in manifest['cases']: args.extend(['--exclude',Path(case['source']).stem])
excluded=[args[i+1] for i,a in enumerate(args) if a=='--exclude']
successful,diff=[],[]
with (previous/'conversion_quality_records_v2.csv').open(encoding='utf-8',newline='') as f:
 for index,row in enumerate(csv.DictReader(f),1):
  result=review_variant(row['variant'],source=row['source'])
  (successful if row['source']=='successful_conversion' else diff).append(result)
  if index%100==0: print(index,flush=True)
candidates=select_plan_b_candidates(successful,diff,excluded_variants=excluded)
report=write_reports(output,successful,diff,candidates,threshold=DEFAULT_THRESHOLD,max_image_area=6400)
(output/'review_args.json').write_text(json.dumps(args,indent=2)+'\n',encoding='utf-8')
print(report['metrics']);print([c.variant for c in candidates])
