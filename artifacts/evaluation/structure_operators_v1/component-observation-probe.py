"""Timing-sensitive pre-existing observation test probe; run from repository root.

Example: python -c "import sys,runpy; sys.argv=['probe','base']; runpy.run_path('artifacts/evaluation/structure_operators_v1/component-observation-probe.py',run_name='__main__')"
The baseline replaces only AdaptiveSearch with its exact base-commit code,
including the original ImageSearch; all other exercised files are unchanged.
Counts vary because scheduling uses the real clock. This is not a quality study.
"""
import sys,types,subprocess,json,contextlib,io
from pathlib import Path
import numpy as np
mode=sys.argv[1]
if mode=='base':
 name='src.iCCModules.imageCompositeConverterAdaptiveSearch'
 import src.iCCModules
 module=types.ModuleType(name);module.__file__=str(Path('src/iCCModules/imageCompositeConverterAdaptiveSearch.py').resolve());sys.modules[name]=module
 source=subprocess.check_output(['git','show','dd832bd228f2c24f4a757f1a8b05e008476b2e12:src/iCCModules/imageCompositeConverterAdaptiveSearch.py'])
 exec(compile(source,module.__file__,'exec'),module.__dict__);setattr(src.iCCModules,'imageCompositeConverterAdaptiveSearch',module)
from tests.test_component_value import run_search
failures=[]
for i in range(200):
 with contextlib.redirect_stdout(io.StringIO()):
  on,off=run_search(),run_search(observed=False)
 if not(np.array_equal(on[0],off[0]) and on[1][:3]==off[1][:3] and on[2]['additional_evaluations']==off[2]['additional_evaluations']):
  failures.append(dict(repeat=i,on_parameters=on[0].tolist(),off_parameters=off[0].tolist(),on_evaluations=on[2]['additional_evaluations'],off_evaluations=off[2]['additional_evaluations']))
result=dict(mode=mode,repetitions=200,failed=len(failures),failures=failures)
Path('artifacts/evaluation/structure_operators_v1/component-observation-'+mode+'.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(mode,len(failures),'/',200)
