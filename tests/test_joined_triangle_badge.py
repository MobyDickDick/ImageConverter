"""Complete scenes must never be silently reduced to a circle/text badge."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest
import json
import shutil

from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterPrimitiveEvolution import evolve_primitives
from src.iCCModules.imageCompositeConverterSceneInitialization import observed_scene_parameters
from src.iCCModules.imageCompositeConverterSceneProgram import scene_program, program_svg, validate_program_svg, STRIDE
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterSemantic import apply_semantic_badge_description_rules

ROOT=Path(__file__).resolve().parents[1]


def description():
    return ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml').find(
        ".//bild[.='AC0233_L.jpg']").get('beschreibung')


def render(svg,w,h):
    return render_svg_to_numpy_inprocess(svg,w,h,fitz_module=fitz,np_module=np,cv2_module=cv2)


def test_catalog_description_keeps_all_objects_and_original_label():
    text=description()
    program=scene_program(text)
    assert program is not None
    assert sorted(o['kind'] for o in program['objects'])==['circle','line','text','triangle','triangle','triangle']
    assert next(o['label'] for o in program['objects'] if o['kind']=='text')=='M'
    assert len([r for r in program['relations'] if r['kind']=='coincident'])==3
    assert not apply_semantic_badge_description_rules(desc=text,params={})
    assert description_assertions(text)['labels']==['M']


def test_initializer_proposes_the_complete_source_scene():
    image=cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0233_L.jpg'))
    program=scene_program(description())
    p=observed_scene_parameters(program,image)
    assert p is not None and p.shape==(len(program['objects'])*STRIDE,)
    svg=program_svg(program,p,image.shape[1],image.shape[0])
    evidence=ROOT/'ci-evidence'; evidence.mkdir(exist_ok=True)
    (evidence/'ac0233-initial.svg').write_text(svg,encoding='utf-8')
    raster=render(svg,image.shape[1],image.shape[0])
    cv2.imwrite(str(evidence/'ac0233-initial.png'),raster)
    quality=pixel_quality(image,raster)
    (evidence/'initial-quality.json').write_text(json.dumps(quality),encoding='utf-8')
    assert quality['foreground_iou']>.65


@pytest.mark.parametrize('seed',[17,18])
@pytest.mark.per_test_timeout(50,fail_on_timeout=True)
def test_real_scene_search_checks_exported_geometry_and_paint(tmp_path,seed):
    image=cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0233_L.jpg'))
    text=description(); program=scene_program(text)
    result=evolve_primitives(image,text,render,seed=seed,directory=tmp_path,
        initial_parameters=observed_scene_parameters(program,image),seconds=35,max_evaluations=8000)
    assert result is not None
    evidence=ROOT/'ci-evidence'; evidence.mkdir(exist_ok=True)
    (evidence/f'result-{seed}.svg').write_text(result['svg'],encoding='utf-8')
    cv2.imwrite(str(evidence/f'result-{seed}.png'),result['rendered'])
    (evidence/f'report-{seed}.json').write_text(json.dumps(result['search_report']),encoding='utf-8')
    shutil.copyfile(next(tmp_path.rglob('candidates.jsonl')),evidence/f'candidates-{seed}.jsonl')
    validate_program_svg(result['svg'],program)
    validate_svg_assertions(result['svg'],description_assertions(text))
    assert result['valid']
    assert result['quality']['passed'], result['quality']


def test_labels_and_three_shared_apices_are_checked_on_the_output():
    program=scene_program(description())
    p=np.full((6,STRIDE),.5)
    p[0,:6]=[.5,.75,.3,.2,0,.2]
    p[1,:6]=[.35,.3,.3,.2,0,.2]
    p[2,:6]=[.5,.2,.3,.2,.25,.2]
    p[3,:6]=[.65,.3,.3,.2,.5,.2]
    p[4,:6]=[.5,.475,.525,.1,.75,.2]
    p[5,:6]=[.5,.75,.1,.1,0,.2]
    svg=program_svg(program,p,100,150)
    validate_program_svg(svg,program)
    root=ET.fromstring(svg)
    root.find('{*}text').text='W'
    with pytest.raises(ValueError,match='label'):
        validate_program_svg(ET.tostring(root,encoding='unicode'),program)
    root=ET.fromstring(svg)
    node=root.find('{*}polygon'); node.set('transform','translate(0 1)')
    with pytest.raises(ValueError,match='disconnected'):
        validate_program_svg(ET.tostring(root,encoding='unicode'),program)


def test_failed_population_replays_real_candidates_and_uses_larger_work_budget(tmp_path):
    # This independent raster cannot be explained by a single circle. A larger
    # work budget must continue the search, even when the incumbent stays equal.
    raster=(np.indices((20,24)).sum(axis=0)%4<2).astype('uint8')*180+40
    image=np.repeat(raster[:,:,None],3,axis=2)
    def run(seed,budget):
        calls=[]
        def observed(svg,w,h):
            calls.append(svg)
            return render(svg,w,h)
        result=evolve_primitives(image,'Ein Kreis.',observed,seed=seed,seconds=10,
                                  max_evaluations=budget)
        return result,calls
    first,a=run(17,64); replay,b=run(17,64); other,c=run(18,64); longer,d=run(17,128)
    assert a==b and a!=c and d[:64]==a and len(d)==128
    assert first['search_report']['trace_hash']==replay['search_report']['trace_hash']
    assert first['search_report']['trace_hash']!=other['search_report']['trace_hash']
    assert not longer['quality']['passed']
