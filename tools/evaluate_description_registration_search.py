"""Compare the old fixed registration with seeded, inventory-bound fitting."""
import hashlib
import json
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw

from src import imageConverterGui as gui
from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules.imageCompositeConverterGeometryIrOptimizer import optimizeGeometryIrRegistrationImpl
from src.iCCModules.imageCompositeConverterDescriptionRegistration import register_description_ir
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality, candidate_identity
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/evaluation/description_registration_search_2026-11-21'
OUT.mkdir(parents=True,exist_ok=True)


def render(svg,w,h):
    return render_svg_to_numpy_inprocess(svg,w,h,fitz_module=fitz,np_module=np,cv2_module=cv2)


image=cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0701_L.jpg'))
h,w=image.shape[:2]
description=gui.catalog_descriptions()['AC0701_L']
ir=geometry.buildGeometryIrFromDescriptionImpl(description)
assertions=description_assertions(description)
report=dict(description=description, note='Generic registration only; the specialized square fitter is not called.',
            baseline=[], current=[], impossible=[])
panels=[('Original',image)]
for seed in (17,18):
    calls=[]
    def legacy_render(candidate):
        svg=geometry.renderGeometryIrToSvgImpl(w,h,candidate)
        calls.append(candidate_identity(svg))
        return render(svg,w,h)
    with search_configuration(mode='portfolio',adaptive=True,seed=seed):
        result=optimizeGeometryIrRegistrationImpl(ir,render_fn=legacy_render,
            error_fn=lambda a:float(abs(image.astype(float)-a).mean()))
    svg=geometry.renderGeometryIrToSvgImpl(w,h,result['geometry_ir'])
    try:
        validate_svg_assertions(svg,assertions)
        error=''
    except ValueError as exc:
        error=str(exc)
    (OUT/f'legacy_seed_{seed}.svg').write_text(svg,encoding='utf-8')
    report['baseline'].append(dict(seed=seed,render_calls=len(calls),unique_candidates=len(set(calls)),
        sequence_sha256=hashlib.sha256(''.join(calls).encode()).hexdigest(),
        svg_sha256=hashlib.sha256(svg.encode()).hexdigest(),quality=pixel_quality(image,result['rendered']),
        description_error=error))
    if seed==17:
        panels.append(('Alter Fit',result['rendered']))

for seed in (17,18,19):
    with search_configuration(mode='portfolio',adaptive=True,seed=seed,seconds=30,max_seconds=30):
        with configured_image_search('neutral') as session:
            session.description_assertions=assertions
            result=register_description_ir(ir,image=image,description=description,
                svg_fn=lambda ir:geometry.renderGeometryIrToSvgImpl(w,h,ir),render_fn=render,
                error_fn=lambda a:float(abs(image.astype(float)-a).mean()))
            telemetry=session.report()
    validate_svg_assertions(result['svg'],assertions)
    assert result['quality']['passed']
    (OUT/f'current_seed_{seed}.svg').write_text(result['svg'],encoding='utf-8')
    panels.append((f'Seed {seed}',result['rendered']))
    report['current'].append(dict(seed=seed,evaluations=result['evaluations'],restarts=result['restarts'],
        stop_reason=result['stop_reason'],quality=result['quality'],
        sequence_sha256=telemetry['render_sequence_sha256'],
        unique_candidates=len(set(result['candidate_identities']))))

# A target that cannot satisfy a one-rectangle inventory must still fail.
source='<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'+''.join(
    f'<circle cx="{x}" cy="{y}" r="6" fill="#666666"/>' for x,y in ((10,10),(40,10),(10,40),(40,40)))+'</svg>'
impossible=render(source,50,50)
simple=[dict(kind='RectBorder',id='body',bbox=[.2,.2,.6,.6],fill='#e11e48',stroke='#808080',stroke_width=.02)]
for seed in (17,18,17):
    with search_configuration(mode='portfolio',adaptive=True,seed=seed,seconds=30,max_seconds=30):
        with configured_image_search('independent') as session:
            result=register_description_ir(simple,image=impossible,description='Ein Rechteck.',
                svg_fn=lambda ir:geometry.renderGeometryIrToSvgImpl(50,50,ir),render_fn=render,
                error_fn=lambda a:float(abs(impossible.astype(float)-a).mean()),max_evaluations=160)
            telemetry=session.report()
    assert not result['quality']['passed']
    report['impossible'].append(dict(seed=seed,evaluations=result['evaluations'],restarts=result['restarts'],
        quality=result['quality'],sequence_sha256=telemetry['render_sequence_sha256']))

canvas=Image.new('RGB',(len(panels)*180,380),'white')
draw=ImageDraw.Draw(canvas)
for i,(label,raster) in enumerate(panels):
    draw.text((i*180+8,8),label,fill='black')
    tile=Image.fromarray(raster[:,:,::-1]).resize((w*7,h*7),Image.Resampling.NEAREST)
    canvas.paste(tile,(i*180+2,35))
canvas.save(OUT/'comparison.png')
(OUT/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
assert report['baseline'][0]['svg_sha256']==report['baseline'][1]['svg_sha256']
assert report['baseline'][0]['sequence_sha256']==report['baseline'][1]['sequence_sha256']
assert len({r['sequence_sha256'] for r in report['current']})==3
assert report['impossible'][0]['sequence_sha256']==report['impossible'][2]['sequence_sha256']
assert report['impossible'][0]['sequence_sha256']!=report['impossible'][1]['sequence_sha256']
print(json.dumps({key:[{k:r[k] for k in r if k in ('seed','evaluations','restarts','unique_candidates','description_error')}
                       for r in report[key]] for key in ('baseline','current','impossible')},indent=2))
