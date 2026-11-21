"""Reproduce the actual GUI worker with the unchanged catalog description."""
import hashlib
import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from src import imageConverterGui as gui
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterRepresentation import logical_inventory
from src.imageConverterSample import render_svg
from PIL import Image
import numpy as np

out=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--fresh',action='store_true')
args=parser.parse_args()
xmls=[gui.ROOT/'artifacts/descriptions/Finale_Wurzelformen_V3.xml',
      gui.ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml']
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in xmls}
description=next(e.get('beschreibung') for e in ET.parse(xmls[0]).iter('bild') if e.text=='AC0201_M.jpg')
manager=gui.Jobs(out/'verified-jobs')
try:
    job=manager.upload('AC0201_M.jpg',(gui.ROOT/'artifacts/images_to_convert/AC0201_M.jpg').read_bytes())
    started=manager.start(job['id'],description,'quick',seed=42,use_current_svg=not args.fresh)
    manager.threads[-1].join(timeout=60)
    result=manager.snapshot(started['id'])
    summary={key:result.get(key) for key in ('id','status','quality','elapsed','message','sample_report','pixel_quality','project_save')}
    summary['description']=description
    (out/'gui_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    assert result['status']=='done' and result['quality']=='passed'
    assert result['project_save']['status'] in ('saved','unchanged')
    target=manager.project_svg(result)
    svg=target.read_text(encoding='utf-8')
    validate_svg_assertions(svg,description_assertions(description))
    quality=gui.saved_svg_quality(gui.ROOT/'artifacts/images_to_convert/AC0201_M.jpg',target)
    assert quality['passed']
    quality['inventory']=logical_inventory(svg,dict(circle=1,line=1,triangle=2))
    (out/'saved_quality.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding='utf-8')
    with Image.open(gui.ROOT/'artifacts/images_to_convert/AC0201_M.jpg') as image:
        width,height=image.size
        original=image.convert('RGB')
    rendered=Image.fromarray(np.asarray(render_svg(svg,width,height)))
    rendered.save(out/'final.png')
    # Nearest-neighbour enlargement makes the tiny source pixels reviewable.
    panel=Image.new('RGB',(width*2,height),'white')
    panel.paste(original,(0,0)); panel.paste(rendered,(width,0))
    panel.resize((width*16,height*8),Image.Resampling.NEAREST).save(out/'comparison.png')
    assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in xmls}
finally:
    manager.close()
