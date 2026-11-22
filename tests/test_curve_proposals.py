"""Raster-only curve inference, local damage, external inventory and budgets."""
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch,SearchPolicy,image_search
from src.iCCModules.imageCompositeConverterFallbackCurves import curve_groups,curve_points
from src.iCCModules.imageCompositeConverterFallbackGroups import part_regions,check_parts,check_relations
from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
from tools.evaluate_curve_proposals import verified,EVIDENCE,damaged
from tools.check_curve_scene import check_scene
from tools.run_plan_b_variations import render,measure_quality
from tools.evaluate_svg_text_baseline import render_librsvg

CASES=verified()['cases']
NS='{http://www.w3.org/2000/svg}'


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['case_id'])
def test_visible_curves_are_native_connected_locally_supported_and_remain_drafts(case):
    image=cv2.imread(str(EVIDENCE/'inputs'/(case['case_id']+'.png')))
    session=ImageSearch(SearchPolicy(seconds=5,max_seconds=5))
    with image_search(session):
        fitted,report=explore_structures(case['seed_svg'],image,render(case['seed_svg'],128,128),
            render,session,{},mode='combined')
    root=ET.fromstring(fitted['svg'])
    assert len([n for n in root.iter() if n.tag==NS+'path'])==1
    assert len([n for n in root.iter() if n.tag==NS+'line'])==1
    assert check_relations(fitted['svg']) and all(r['passed'] for r in check_relations(fitted['svg']))
    regions=part_regions(fitted['svg'],128,128)
    assert len([r for r in regions if r['part'].startswith('curve:')])==33
    for renderer in (render,render_librsvg):
        assert measure_quality(image,fitted['svg'],render_fn=renderer)['satisfactory']
        assert all(r['passed'] for r in check_parts(image,renderer(fitted['svg'],128,128),regions))
    assert report['probe_count']<=32
    assert report['render_evaluations']==session.evaluations
    assert session.evaluations<=1100
    assert not session.validated and not report['model_confirmed']
    # Pixel acceptance does not stand in for native geometric acceptance.
    if case['case_id']=='visible_Q_0':
        assert check_scene(fitted['svg'],case['annotation'])['complete']


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['case_id'])
def test_external_inventory_rejects_all_damages_even_hidden_pixel_identical_extras(case):
    assert check_scene(case['svg'],case['annotation'])['complete']
    for damage,svg in damaged(case):
        assert not check_scene(svg,case['annotation'])['complete'],damage
        if damage=='hidden_extra':
            for fn in (render,render_librsvg):
                assert np.array_equal(fn(svg,128,128),fn(case['svg'],128,128))
        if damage in {'missing_curve','missing_lead','gap','tangent'}:
            assert not all(r['passed'] for r in check_relations(svg)),damage


def marked():
    root=ET.fromstring(CASES[0]['svg'])
    group=ET.Element(NS+'g',{'data-fallback-group':'open_curve_lead'})
    for node,role in zip(list(root)[1:],('lead','curve')):
        root.remove(node);node.set('data-part',role);group.append(node)
    root.append(group)
    return root,group


@pytest.mark.parametrize('attribute,value',[('transform','translate(5 2)'),('style','stroke-width:8'),
    ('opacity','.5'),('stroke-dasharray','2 3'),('filter','url(#effect)'),('marker-start','url(#m)')])
@pytest.mark.parametrize('target',['root','group','lead','curve'])
def test_runtime_rejects_effects_instead_of_guessing_viewport_connectivity(attribute,value,target):
    root,group=marked()
    node={'root':root,'group':group,'lead':group[0],'curve':group[1]}[target]
    node.set(attribute,value)
    assert not all(r['passed'] for r in check_relations(ET.tostring(root,encoding='unicode')))


def test_actual_curve_middle_is_checked_when_endpoints_and_connection_stay_unchanged():
    root,group=marked();original=ET.tostring(root,encoding='unicode')
    image=render(original,128,128)
    points=curve_points(group[1]);points[1,0]+=9
    group[1].set('d','M '+' '.join(map(str,points[0]))+' Q '+' '.join(str(v) for p in points[1:] for v in p))
    changed=ET.tostring(root,encoding='unicode')
    parts=check_parts(image,render(changed,128,128),part_regions(original,128,128))
    assert any(not p['passed'] and p['part'].startswith('curve:') for p in parts)


def test_fitting_renders_stop_at_the_shared_deadline_and_zero_probes_do_no_fitting():
    case=CASES[0];image=render(case['svg'],128,128);now=[0.]
    session=ImageSearch(SearchPolicy(seconds=1,max_seconds=1),clock=lambda:now[0])
    def slow(svg,w,h):
        assert now[0]<1
        raster=render(svg,w,h)
        now[0]+=.4
        return raster
    with image_search(session):
        assert not list(curve_groups(image,session,slow))
    assert session.evaluations==3
    session=ImageSearch(SearchPolicy(seconds=5,max_seconds=5))
    with image_search(session):
        fitted,report=explore_structures(case['seed_svg'],image,render(case['seed_svg'],128,128),
            slow,session,{},mode='groups',max_probes=0)
    assert fitted['svg']==case['seed_svg'] and session.evaluations==0


@pytest.mark.parametrize('body',[
    '<circle cx="64" cy="64" r="24" fill="none" stroke="#224466" stroke-width="2"/>',
    '<path d="M20 64 L100 64 M64 20 L64 100" fill="none" stroke="#224466" stroke-width="2"/>',
    '<rect x="20" y="20" width="60" height="50" fill="#224466"/>'])
def test_loops_branches_and_filled_components_do_not_become_open_curves(body):
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128"><rect width="128" height="128" fill="white"/>'+body+'</svg>'
    session=ImageSearch(SearchPolicy(seconds=5,max_seconds=5))
    with image_search(session):
        assert not list(curve_groups(render(svg,128,128),session,render))


def test_development_freeze_is_unchanged_and_reserves_are_not_executed():
    data=verified()
    assert data['seeds']==[17,29,43] and data['seconds']==5 and data['max_probes']==32
    assert data['real_reserves_executed'] is False and data['model_promotions']==0
    from tools.verify_curve_proposal_evidence import verify_results
    assert verify_results()['files']
