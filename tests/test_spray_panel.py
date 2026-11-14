"""Five-part humidifier integration and meaningful missing-detail controls."""
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch,SearchPolicy,image_search
from src.iCCModules.imageCompositeConverterSprayPanel import fit_spray_panel,spray_contract
from tools.evaluate_spray_panel import EVIDENCE,annotation,inspect,controls
from tools.check_spray_scene import check_scene
from tools.run_plan_b_variations import render

DESCRIPTION=(EVIDENCE/'description.txt').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def fitted():
    image=cv2.imread(str(EVIDENCE/'inputs/AC0130_L.jpg'))
    result=fit_spray_panel(40,80,description=DESCRIPTION,image=image,render_fn=render,
                          error_fn=lambda a,b:float(np.square(a.astype(float)-b).mean()))
    assert result is not None
    return image,result


def test_every_component_receives_its_own_search_and_passes_external_checks(fitted):
    image,result=fitted
    assert inspect(result['svg'],image,annotation())['complete']
    assert len(result['stages']) == 13
    assert all(s['completed'] and s['evaluations'] > 0 for s in result['stages'])
    assert len(result['details']) == 13 and all(d['passed'] for d in result['details'])
    assert result['evaluations'] < 6000 and result['error'] < result['initial_error']
    assert result['quality']['passed']
    assert '<image' not in result['svg'] and '<polyline' not in result['svg']


def test_each_missing_nozzle_or_ray_and_extra_hidden_geometry_is_rejected(fitted):
    _,result=fitted
    ann=annotation()
    damaged=list(controls(result['svg']))
    assert len(damaged) == 29
    for name,svg in damaged:
        assert not check_scene(svg,ann)['complete'],name


def test_roles_and_ids_do_not_supply_the_external_inventory_decision(fitted):
    _,result=fitted
    root=ET.fromstring(result['svg'])
    for n in root.iter():
        if n.tag.rsplit('}',1)[-1] != 'linearGradient':
            n.attrib.pop('id',None)
        n.set('data-fallback-group','forged')
    assert check_scene(ET.tostring(root,encoding='unicode'),annotation())['complete']


def test_old_pixel_pass_does_not_meet_the_user_decomposition():
    baseline=(EVIDENCE/'baseline.svg').read_text(encoding='utf-8')
    assert not check_scene(baseline,annotation())['complete']


def test_preserved_inputs_and_saved_vectors_match_their_seal():
    from tools.evaluate_spray_panel import digest
    seal=json.loads((EVIDENCE/'source_seal.json').read_text(encoding='utf-8'))
    for name,sha in seal['files'].items():
        assert digest(EVIDENCE/name)==sha
    assert check_scene((EVIDENCE/'AC0130_L.svg').read_text(encoding='utf-8'),annotation())['complete']


def test_hard_deadline_stops_between_component_renders_without_partial_success():
    image=cv2.imread(str(EVIDENCE/'inputs/AC0130_L.jpg'))
    now=[0.]
    calls=[]
    session=ImageSearch(SearchPolicy(seconds=.8,max_seconds=.8),clock=lambda:now[0])
    def slow(svg,w,h):
        assert now[0] < .8
        now[0] += .4
        calls.append(svg)
        return render(svg,w,h)
    with image_search(session):
        result=fit_spray_panel(40,80,description=DESCRIPTION,image=image,render_fn=slow,
                              error_fn=lambda a,b:float(np.square(a.astype(float)-b).mean()))
    assert result is None and len(calls)==session.evaluations==2
    assert not session.validated


@pytest.mark.parametrize('description',[DESCRIPTION+' Zickzacklinie',DESCRIPTION+' Andreaskreuz',
                                      'Ein Rechteck mit einer Linie.',DESCRIPTION+' Der rechte Rahmen ist durchgezogen.'])
def test_incompatible_or_incomplete_contracts_do_not_route_to_the_new_model(description):
    assert not spray_contract(description)


def test_missing_frame_and_nozzle_are_not_invented_from_the_description(fitted):
    _,result=fitted
    for damage in ['missing_frame','missing_4']:
        svg=dict(controls(result['svg']))[damage]
        image=render(svg,40,80)
        selected=fit_spray_panel(40,80,description=DESCRIPTION,image=image,render_fn=render,
                                error_fn=lambda a,b:float(np.square(a.astype(float)-b).mean()))
        assert selected is None


def test_independently_authored_larger_panel_and_different_dash_period():
    # Authored before fitting; different dimensions, positions, spacing and
    # dash period ensure the runtime does not use catalogue coordinates.
    svg=('<svg xmlns="http://www.w3.org/2000/svg" width="50" height="100">'
         '<defs><linearGradient id="paint"><stop stop-color="#cccccc"/>'
         '<stop offset=".4" stop-color="white"/><stop offset="1" stop-color="#cccccc"/></linearGradient></defs>'
         '<rect x=".5" y=".5" width="49" height="99" fill="url(#paint)" stroke="#888888"/>'
         '<rect x="1.5" y="6" width="4" height="93" fill="#808080"/>'
         '<rect x="27" y="4" width="17" height="92" fill="none" stroke="#808080" stroke-width=".8" stroke-dasharray="2.4 .6"/>')
    for cy in [9,29,49,69,89]:
        svg+=f'<polygon points="5.5,{cy-1} 6.5,{cy-.5} 8,{cy-.5} 8,{cy+.5} 6.5,{cy+.5} 5.5,{cy+1}" fill="#888888"/>'
        for x,y,X,Y in [(10.5,cy,20,cy-6),(10.5,cy+2,22,cy+2),(10.5,cy+4,20,cy+10)]:
            svg+=f'<line x1="{x}" y1="{y}" x2="{X}" y2="{Y}" stroke="#bbbbbb" stroke-width=".8"/>'
    svg+='</svg>'
    image=render(svg,50,100)
    result=fit_spray_panel(50,100,description=DESCRIPTION,image=image,render_fn=render,
                          error_fn=lambda a,b:float(np.square(a.astype(float)-b).mean()))
    assert result is not None and result['quality']['passed']
    root=ET.fromstring(result['svg'])
    counts={tag:sum(n.tag.rsplit('}',1)[-1] == tag for n in root.iter()) for tag in ['rect','polygon','line']}
    assert counts == dict(rect=3,polygon=5,line=15)
    frame=next(n for n in root.iter() if n.get('stroke-dasharray'))
    assert abs(sum(map(float,frame.get('stroke-dasharray').split()))-3) < .1
