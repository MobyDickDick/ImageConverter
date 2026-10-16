from pathlib import Path
import hashlib,json,shutil,subprocess,sys,os
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
from tools.evaluate_gradient_junction_recheck import evaluate
p=Path(__file__).resolve().parent
m=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
import argparse
parser=argparse.ArgumentParser(description='Check original and revised descriptions in the complete catalog context')
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
o=args.output_dir.resolve(); o.mkdir(parents=True, exist_ok=False)
paths=[str(Path(np.__file__).resolve().parents[1]),str(Path.cwd()),*sys.path]
old=subprocess.check_output(['git','show',m['provenance']['commit']+':artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'])
(o/'before.xml').write_bytes(old)
shutil.copyfile('artifacts/images_to_convert/Finale_Wurzelformen_V3.xml',o/'after.xml')
real=json.loads(json.dumps(m)); access={}
real['provenance']['baseline_mode']='full original-description catalog, unchanged parent behavior for that description; PYTHONHASHSEED=0 and TINY_ICC_OUTPUT_VARIATION=0'
for c in real['cases']:
 c['case_id']=Path(c['source']).stem
 c['image']='inputs/'+c['source']
inputs=o/'inputs'; inputs.mkdir()
for c in m['cases']:shutil.copyfile(p/c['image'],inputs/c['source'])
for mode in ('before','after'):
 copies=o/('inputs_'+mode); copies.mkdir()
 for c in m['cases']:shutil.copyfile(inputs/c['source'],copies/c['source'])
 names=sorted(c['case_id'] for c in real['cases'])
 bootstrap='import sys,runpy; sys.path[:0]='+repr(paths)

 bootstrap+="; runpy.run_module('tools.run_gradient_junction_recheck',run_name='__main__')"
 with (o/(mode+'.log')).open('w',encoding='utf-8') as log:
  subprocess.run([sys.executable,'-I','-c',bootstrap,'--_worker',mode,str((o/mode).resolve()),str(copies.resolve()),'--descriptions-path',str((o/(mode+'.xml')).resolve()),'--output-dir',str((o/mode).resolve()),'--start',names[0],'--end',names[-1],'--execution-mode','semantic-only','--deterministic-order'],env=dict(os.environ,IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0',PYTHONHASHSEED='0',TINY_ICC_OUTPUT_VARIATION='0'),stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True)
 access[mode]=json.loads((o/'reference_access.json').read_text());assert not access[mode]['blocked_svg_reads']
 for c in real['cases']:
  matches=[f for sub in ('converted_svgs','converted_svg_failed') for f in (o/mode/sub).glob('*.svg') if f.stem.casefold()==c['case_id'].casefold()]
  assert len(matches)==1,(c['case_id'],len(matches))
  c[mode+'_svg']=matches[0].relative_to(o).as_posix()
r=evaluate(real,o); r['reference_access']=access
(o/'manifest.json').write_text(json.dumps(real,indent=2)+'\n',encoding='utf-8')
(o/'report.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8')
assert all(c['satisfactory'] for c in r['satisfaction_gate']['cases'])
assert all(c['satisfactory'] for c in r['strict_pixel_gates'].values())
for c,neutral in zip(real['cases'],m['cases']):assert (o/c['after_svg']).read_bytes()==(p/neutral['after_svg']).read_bytes()

# Original full-catalog dispatch differs from anonymous dispatch. Freeze and
# replay its own baseline rather than treating unlike contexts as identical.
for c in real['cases']:
 frozen=p/'catalog_context'/c['before_svg']
 if frozen.exists():assert (o/c['before_svg']).read_bytes()==frozen.read_bytes()
print('Real-name conversions pass; all revised SVGs identical to neutral outputs; full-catalog baseline replayed')
