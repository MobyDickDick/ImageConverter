"""CI-only: run the actual GUI worker for one time profile and export evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import time
from xml.etree import ElementTree as ET

import cv2
from PIL import Image,ImageDraw

from src.imageConverterGui import Jobs, ROOT, PROFILES
from src.iCCModules.imageCompositeConverterSceneProgram import scene_program, validate_program_svg
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions,validate_svg_assertions
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from tools.evaluate_svg_text_baseline import render_librsvg


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',choices=PROFILES,required=True)
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    source=ROOT/'artifacts/images_to_convert/AC0233_L.jpg'
    text=ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml').find(
        ".//bild[.='AC0233_L.jpg']").get('beschreibung')
    jobs=Jobs(args.output/'jobs')
    job=jobs.upload(source.name,source.read_bytes())
    # Avoid changing the catalog or reusing a previously accepted project SVG.
    # Calling run synchronously still uses the same supervised CLI/worker tree.
    active=jobs.jobs[job['id']]
    active.update(status='running',description=text,profile=args.profile,search_seed=args.seed,
                  use_current_svg=False,catalog_background=True,started=time.time())
    jobs.run(job['id'])
    final=jobs.jobs[job['id']]
    folder=jobs.folder(job['id'])
    result=folder/'result.svg'
    candidates=list((folder/'output').rglob('*.svg'))
    if not result.is_file():
        result=next((p for p in candidates if p.parent.name=='converted_svgs'),None)
    report=dict(profile=args.profile,seed=str(args.seed),status=final.get('status'),
                message=final.get('message'),elapsed=final.get('elapsed'),
                pixel_quality=final.get('pixel_quality'),search_summary=final.get('search_summary'))
    (args.output/'summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    assert final.get('result'),report
    assert result is not None and result.is_file(),report
    svg=result.read_text(encoding='utf-8')
    validate_program_svg(svg,scene_program(text))
    validate_svg_assertions(svg,description_assertions(text))
    shutil.copyfile(result,args.output/'result.svg')
    shutil.copyfile(source,args.output/'original.jpg')
    assert final.get('pixel_quality',{}).get('passed'),report
    reference=cv2.imread(str(source))
    independent=render_librsvg(svg,reference.shape[1],reference.shape[0])
    quality=pixel_quality(reference,independent)
    report['independent_quality']=quality
    cv2.imwrite(str(args.output/'result-librsvg.png'),independent)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    assert quality['passed'],report
    assert report['search_summary'] is not None,report
    assert report['search_summary']['search_seed']==str(args.seed),report
    # Rendered by GitHub only, retained as a reviewable original/SVG comparison.
    comparison=Image.new('RGB',(440,335),'white')
    draw=ImageDraw.Draw(comparison)
    for x,label,raster in ((10,'Original',reference),(230,'SVG (librsvg)',independent)):
        draw.text((x,5),label,fill='black')
        picture=Image.fromarray(cv2.cvtColor(raster,cv2.COLOR_BGR2RGB)).resize((200,300),Image.Resampling.NEAREST)
        comparison.paste(picture,(x,25))
    comparison.save(args.output/'comparison.png')


if __name__=='__main__':
    main()
