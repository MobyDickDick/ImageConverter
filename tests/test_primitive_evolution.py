"""Actual population variation, strict outputs and durable source-bound search."""
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterPrimitiveEvolution import evolve_primitives
from src.iCCModules.imageCompositeConverterSceneProgram import scene_program,validate_program_svg,program_svg,STRIDE
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions,validate_svg_assertions
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration,configured_image_search

DESCRIPTION=('Links: Kelle mit Griff rechts. Rechts: Zweiwegventil '
             '(zwei gleichschenklige Dreiecke mit den zwei Spitzen an am gleichen Punkt). '
             'Die Spitze des Griffs und der Mittelpunkt der zwei gleichschnkligen Dreiek befinden sind am gleichen Punkt')


def render(svg,w,h):
    return render_svg_to_numpy_inprocess(svg,w,h,fitz_module=fitz,np_module=np,cv2_module=cv2)


def impossible_target():
    # One circle cannot reproduce an independent diagonal checkerboard.
    pattern=(np.indices((24,32)).sum(axis=0)%4<2).astype('uint8')*180+40
    return np.repeat(pattern[:,:,None],3,axis=2)


def run(folder,seed=42,budget=80,image=None):
    calls=[]
    def observed(svg,w,h):
        calls.append(svg)
        return render(svg,w,h)
    result=evolve_primitives(impossible_target() if image is None else image,'Ein Kreis.',observed,
                            seed=seed,directory=folder,seconds=20,max_evaluations=budget)
    return result,calls


def test_composite_expansion_and_pronoun_references_count_each_instance_once():
    assert description_assertions(DESCRIPTION)['objects']==dict(circle=1,line=1,triangle=2)
    program=scene_program(DESCRIPTION)
    assert [x['kind'] for x in program['objects']]==['circle','triangle','triangle','line']
    assert len(program['relations'])==3
    assert len(scene_program('Ein Kreis, ein Rechteck und drei Dreiecke.')['objects'])==5


@pytest.mark.parametrize('description',['Ein Kreis und ein Stern.','Ein Kreis mit Text "M".',
                                     'Ein Kreis mit drei symmetrischen Linien.',
                                     'Zwei vertikale Linien.','Ein roter Kreis.'])
def test_unimplemented_claims_are_explicitly_unsupported(description):
    assert scene_program(description) is None


def test_seed_controls_real_geometry_and_has_deterministic_fixed_work(tmp_path):
    first,a=run(tmp_path/'a')
    repeated,b=run(tmp_path/'b')
    other,c=run(tmp_path/'c',seed=43)
    assert a==b and a!=c
    assert first['search_report']['trace_hash']==repeated['search_report']['trace_hash']
    assert len(a)==80==first['search_report']['evaluations']
    assert len(set(a))==len(a)
    assert first['search_report']['distinct_geometries']>45
    assert len(first['search_report']['operators'])>=4
    # A fresh population spans the canvas, rather than jittering one pose.
    centers=[float(ET.fromstring(svg).find('{*}circle').get('cx')) for svg in a[:32]]
    assert np.ptp(centers)>12
    assert not first['quality']['passed']


def test_checkpoint_resumes_population_and_keeps_other_seeds_separate(tmp_path):
    first,_=run(tmp_path,budget=60)
    folder=Path(first['search_report']['checkpoint'])
    old=[json.loads(line) for line in (folder/'candidates.jsonl').read_text().splitlines()]
    resumed,calls=run(tmp_path,budget=40)
    report=resumed['search_report']
    assert report['resumed'] and len(calls)==40
    assert report['total_evaluations']==100
    assert report['operators']['checkpoint_validation']==1
    new=[json.loads(line) for line in (folder/'candidates.jsonl').read_text().splitlines()]
    assert new[:len(old)]==old
    assert not {x['candidate'] for x in old}&{x['candidate'] for x in new[len(old):]}
    assert (folder/'solution.json').is_file() and (folder/'best.svg').is_file()
    different,_=run(tmp_path,seed=77,budget=32)
    assert not different['search_report']['resumed']
    assert different['search_report']['checkpoint']!=str(folder)
    changed,_=run(tmp_path,budget=32,image=np.roll(impossible_target(),1,axis=0))
    assert not changed['search_report']['resumed']


def test_loaded_success_is_rechecked_instead_of_trusting_saved_flags(tmp_path):
    first,_=run(tmp_path,budget=40)
    checkpoint=Path(first['search_report']['checkpoint'])/'checkpoint.json'
    state=json.loads(checkpoint.read_text())
    for item in state['population']:
        item.update(valid=True,quality=dict(passed=True))
    checkpoint.write_text(json.dumps(state))
    result,calls=run(tmp_path,budget=32)
    assert len(calls)==32
    assert not result['quality']['passed']


def test_corrupt_checkpoint_starts_a_new_population(tmp_path):
    first,_=run(tmp_path,budget=32)
    (Path(first['search_report']['checkpoint'])/'checkpoint.json').write_text('{broken')
    result,calls=run(tmp_path,budget=32)
    assert not result['search_report']['resumed'] and len(calls)==32


def test_actual_render_count_obeys_the_shared_context(tmp_path):
    with search_configuration(mode='portfolio',primitive_exploration=True,seed=11,
                              budget=40,seconds=20,max_seconds=20):
        with configured_image_search('neutral') as session:
            result,calls=run(tmp_path,seed=11,budget=100)
            assert len(calls)==40==session.renderings==result['search_report']['evaluations']
            assert result['search_report']['stop_reason']=='render_limit'


def test_poor_fits_do_real_work_until_the_time_limit(tmp_path):
    result=evolve_primitives(impossible_target(),'Ein Kreis.',render,seed=24,directory=tmp_path,
                            seconds=.3,max_evaluations=100000)
    report=result['search_report']
    assert report['stop_reason']=='time_limit'
    assert .3<=report['elapsed_seconds']<2
    assert report['evaluations']>5


def test_composite_population_and_relationship_scores_are_serializable(tmp_path):
    result=evolve_primitives(impossible_target(),DESCRIPTION,render,seed=42,directory=tmp_path,
                            seconds=10,max_evaluations=64)
    assert result['search_report']['evaluations']==64
    json.dumps(result['search_report'],allow_nan=False)


def test_exported_relationships_survive_independent_validation():
    program=scene_program(DESCRIPTION)
    p=np.full((4,STRIDE),.5)
    p[0,:6]=[.2,.5,.2,.2,0,.2]  # circle centre (20,50), radius 10
    p[3,:6]=[.4,.5,.2,.2,0,.2]  # line (30,50) -> (50,50)
    p[1,:6]=[.5,.4,.2,.2,.25,.2] # triangle apex (50,50)
    p[2,:6]=[.5,.6,.2,.2,.75,.2] # triangle apex (50,50)
    svg=program_svg(program,p,100,100)
    validate_program_svg(svg,program)
    validate_svg_assertions(svg,description_assertions(DESCRIPTION))
    root=ET.fromstring(svg)
    line=root.find('{*}line'); line.set('y2','53')
    broken=ET.tostring(root,encoding='unicode')
    with pytest.raises(ValueError,match='primitive_relation'):
        validate_svg_assertions(broken,description_assertions(DESCRIPTION))
