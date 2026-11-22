import json,sys
from pathlib import Path
import cv2,fitz,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from src.imageConverterGui import catalog_descriptions
from src.iCCModules.imageCompositeConverterPrimitiveEvolution import evolve_primitives
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess

def render(svg,w,h):
 return render_svg_to_numpy_inprocess(svg,w,h,fitz_module=fitz,np_module=np,cv2_module=cv2)
if __name__=='__main__':
 seed=int(sys.argv[1]) if len(sys.argv)>1 else 42
 image=cv2.cvtColor(np.asarray(Image.open(ROOT/'artifacts/images_to_convert/AC0204_L.jpg').convert('RGB')),cv2.COLOR_RGB2BGR)
 result=evolve_primitives(image,catalog_descriptions()['AC0204_L'],render,seed=seed,directory=Path(__file__).parent/'memory',seconds=300,max_evaluations=100000)
 out=Path(__file__).parent
 (out/f'result-{seed}.svg').write_text(result['svg'],encoding='utf-8')
 (out/f'report-{seed}.json').write_text(json.dumps(result['search_report'],indent=2),encoding='utf-8')
 cv2.imwrite(str(out/f'result-{seed}.png'),result['rendered'])
 print(json.dumps({k:result['search_report'][k] for k in ('evaluations','valid','quality','stop_reason','elapsed_seconds')}),flush=True)
