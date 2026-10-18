"""Compare the old and new renderer on every previously accepted vector."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import types
import cv2
import fitz
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess

def main():
    commit=json.loads((FOLDER/'manifest.json').read_text(encoding='utf-8'))['provenance']['commit']
    code=subprocess.check_output(['git','show',commit+':src/iCCModules/imageCompositeConverterRendering.py'],cwd=ROOT).decode('utf-8')
    (FOLDER/'parent_renderer.py.txt').write_text(code,encoding='utf-8')
    parent=types.ModuleType('parent_renderer')
    parent.__file__=str(ROOT/'src/iCCModules/imageCompositeConverterRendering.py')
    exec(compile(code,parent.__file__,'exec'),parent.__dict__)
    archive=ROOT/'artifacts/satisfactory_conversions'
    index=json.loads((archive/'index.json').read_text(encoding='utf-8'))
    safety=json.loads((FOLDER/'archive_safety.json').read_text(encoding='utf-8'))
    records=[]
    for case in index['cases']:
        if case['variant'] not in safety:
            continue
        image=cv2.imread(str(archive/case['image']))
        svg=(archive/case['svg']).read_text(encoding='utf-8')
        args=dict(fitz_module=fitz,np_module=np,cv2_module=cv2)
        h,w=image.shape[:2]
        before=parent.render_svg_to_numpy_inprocess(svg,w,h,**args)
        after=render_svg_to_numpy_inprocess(svg,w,h,**args)
        assert before is not None and after is not None
        records.append(dict(variant=case['variant'],pixel_equal=np.array_equal(before,after),
            before_mean_delta2=float(np.mean(np.sum((image.astype(float)-before)**2,axis=2))),
            after_mean_delta2=float(np.mean(np.sum((image.astype(float)-after)**2,axis=2)))))
    report=dict(case_count=len(records),pixel_equal=sum(c['pixel_equal'] for c in records),cases=records,
        parent_commit=commit,parent_renderer_sha256=hashlib.sha256(code.encode()).hexdigest())
    (FOLDER/'renderer_archive_control.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['case_count'],report['pixel_equal'],flush=True)
    assert all(c['after_mean_delta2'] <= c['before_mean_delta2']+1e-6 for c in records)

if __name__=='__main__':
    main()
