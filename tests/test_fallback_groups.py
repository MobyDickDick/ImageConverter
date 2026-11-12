"""Atomic topology, original-pixel parts, negative relations and shared limits."""
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterFallbackGroups import check_parts, check_relations, part_regions
from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
from tools.evaluate_fallback_groups import INPUTS, EVIDENCE, review, negatives, synthetic_cases
from tools.freeze_real_composition_holdouts import digest, verify
from tools.run_plan_b_variations import render


def probe(index, mode='combined', renderer=render, session=None, max_probes=32):
    case=json.loads((INPUTS/'manifest.json').read_text(encoding='utf-8'))['cases'][index]
    image=cv2.imread(str(INPUTS/case['case_id']/'original.jpg'))
    svg=(INPUTS/case['case_id']/'seed.svg').read_text(encoding='utf-8')
    session=session or ImageSearch(SearchPolicy(seconds=5,max_seconds=5))
    with image_search(session):
        fitted,report=explore_structures(svg,image,render(svg,case['width'],case['height']),
                                          renderer,session,{},mode=mode,max_probes=max_probes)
    return case,image,fitted,report,session


@pytest.mark.parametrize('index,kind',[(0,'shaft_triangle'),(2,'crossed_panel_linkage')])
def test_two_native_object_groups_improve_both_renderers_without_model_approval(index,kind):
    case,image,before,_,_=probe(index,'legacy_combined')
    _,_,after,report,session=probe(index)
    assert after['error'] < before['error']*.4
    assert all(r['complete'] for r in review(image,after['svg'],case).values())
    assert not all(r['complete'] for r in review(image,before['svg'],case).values())
    groups=check_relations(after['svg'])
    assert any(g['group']==kind for g in groups) and all(g['passed'] for g in groups)
    assert all(c['passed'] for c in check_parts(image,after['rendered'],part_regions(after['svg'],case['width'],case['height'])))
    assert report['probe_count'] <= 32 and not session.validated and not report['model_confirmed']
    assert '<path' not in after['svg'] and '<image' not in after['svg']


@pytest.mark.parametrize('index',[0,2])
def test_missing_shifted_and_misconnected_parts_are_rejected(index):
    case,image,fitted,_,_=probe(index,'groups')
    controls=negatives(image,fitted['svg'],case)
    assert controls and {c['damage'] for c in controls}=={'remove','shift','wrong_connection'}
    assert all(r['rejected'] for c in controls for r in c['renderers'].values())
    # Global error alone misses real local defects in these small symbols.
    if index == 2:
        assert any(r['quality']['satisfactory'] and r['rejected'] for c in controls for r in c['renderers'].values())


def test_native_group_label_cannot_approve_a_broken_connection():
    _,_,fitted,_,_=probe(2,'groups')
    root=ET.fromstring(fitted['svg'])
    for node in root.iter():
        if node.get('data-part')=='connector':
            node.set('x2',str(float(node.get('x2'))-6))
    assert not all(c['passed'] for c in check_relations(ET.tostring(root,encoding='unicode')))


@pytest.mark.parametrize('case,seed_svg',list(synthetic_cases()),ids=lambda v:v['case_id'] if isinstance(v,dict) else 'seed')
def test_independent_synthetic_colours_orientations_and_positions(case,seed_svg):
    image=render(case['svg'],80,80)
    session=ImageSearch(SearchPolicy(seconds=5,max_seconds=5))
    with image_search(session):
        fitted,report=explore_structures(seed_svg,image,render(seed_svg,80,80),render,session,{},mode='groups')
    assert all(r['complete'] for r in review(image,fitted['svg'],case).values())
    assert check_relations(fitted['svg']) and all(r['passed'] for r in check_relations(fitted['svg']))
    assert report['probe_count']<=8 and not session.validated


def test_parameter_refinement_cannot_erase_head_even_with_claimed_global_gain(monkeypatch):
    from src.iCCModules import imageCompositeConverterFilledSymbols as filled
    from src.iCCModules.imageCompositeConverterVectorPolish import polish_generated_svg
    from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration,configured_image_search
    case,image,base,_,_=probe(0,'groups')
    root=ET.fromstring(base['svg'])
    for group in root.iter():
        for node in list(group):
            if node.get('data-part')=='head':
                group.remove(node)
    damaged=ET.tostring(root,encoding='unicode')
    monkeypatch.setattr(filled,'_register',lambda *a,**kw:dict(svg=damaged,rendered=render(damaged,30,80),
                       error=0.,evaluations=1,search_control={}))
    seed=(INPUTS/case['case_id']/'seed.svg').read_text(encoding='utf-8')
    with search_configuration(mode='portfolio',adaptive=True,minimum_seconds=5,seconds=5,max_seconds=5):
        with configured_image_search('heads'):
            result=polish_generated_svg(seed,image,render)
    assert result['structure_search']['refinement_reverted_for_local_detail']
    assert '<polygon' in result['svg']
    assert result['error']==pytest.approx(np.square(image.astype(float)-result['rendered']).mean()/255**2)


def test_group_probes_obey_active_deadline_and_probe_limit():
    now=[0.]
    session=ImageSearch(SearchPolicy(seconds=1,max_seconds=1),clock=lambda:now[0])
    def slow(svg,w,h):
        assert now[0]<1
        now[0]+=.4
        return render(svg,w,h)
    _,_,_,report,_=probe(0,'groups',renderer=slow,session=session)
    assert report['probe_count']==session.evaluations==3
    assert report['stop_reason']=='time_limit' and session.limit==1
    _,_,_,report,session=probe(2,'groups',max_probes=1)
    assert report['probe_count']==session.evaluations==1 and report['stop_reason']=='probe_limit'


def test_explicit_triangle_count_rejects_object_group_before_rendering():
    case=json.loads((INPUTS/'manifest.json').read_text(encoding='utf-8'))['cases'][0]
    image=cv2.imread(str(INPUTS/case['case_id']/'original.jpg'))
    svg=(INPUTS/case['case_id']/'seed.svg').read_text(encoding='utf-8')
    session=ImageSearch(SearchPolicy())
    with image_search(session):
        fitted,report=explore_structures(svg,image,render(svg,30,80),render,session,
                 {'counts':[{'kind':'polygon','count':0}]},mode='groups')
    assert fitted['svg']==svg and session.evaluations==0
    assert all(p['rejection']=='description_assertions' for p in report['proposals'])


def test_real_reservations_and_previous_runtime_are_immutable_and_unrun(tmp_path):
    assert verify(EVIDENCE/'freeze/manifest.json')['converter_executed'] is False
    manifest=json.loads((EVIDENCE/'inputs/manifest.json').read_text())
    for name,expected in manifest['files'].items():
        assert digest(EVIDENCE/'inputs'/name)==expected
    from tools.evaluate_real_scene import prepare_real
    with pytest.raises(ValueError,match='Sealed'):
        prepare_real(tmp_path/'trial',ROOT/'config/real_composition_holdout_fallback_groups.json')


ROOT=Path(__file__).resolve().parents[1]
