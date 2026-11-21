"""Seed propagation and honest route coverage across distinct search families."""
import time
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import candidate_identity, pixel_quality
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterFilledSymbols import _register
from src.iCCModules.imageCompositeConverterRandom import conversionRandomImpl, conversionSeedImpl
from src.iCCModules.imageCompositeConverterSampleAlignment import align_sample
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search, proposal_rng
from src.imageConverterSample import render_svg, refine


@pytest.mark.parametrize('mode',['portfolio','legacy'])
def test_selected_full_seed_drives_legacy_and_shared_kernels(monkeypatch,mode):
    monkeypatch.setenv('TINY_ICC_RANDOM_SEED','123')
    def run(seed):
        with search_configuration(mode=mode,seed=seed):
            rng=conversionRandomImpl()
            return conversionSeedImpl(rng,deterministic_order=True),rng.random(),proposal_rng('model','neutral').random()
    a=run(2**64-1)
    assert run(2**64-1)==a and run(17)!=a
    assert a[0]==2**64-1


def test_disabling_late_portfolio_does_not_disable_seeded_model_proposals():
    image=np.zeros((16,16,3),dtype='uint8')
    def run(seed):
        calls=[]
        def renderer(svg,w,h):
            calls.append(svg)
            return np.full_like(image,200)
        with search_configuration(mode='portfolio',adaptive=True,seed=seed,seconds=10,max_seconds=10):
            with configured_image_search('neutral'):
                result=_register(np.zeros(3),3,
                    lambda p:'<svg values="'+' '.join(map(str,p))+'"/>',lambda p:True,
                    image,renderer,lambda a,b:1.,'bounded_stage',allow_portfolio=False,
                    max_evaluations=32,reconsider_after=0)
        return calls,result['svg']
    a=run(17)
    assert run(17)==a and run(18)[0]!=a[0]
    # A tie is not a reason to replace the best output.
    assert run(18)[1]==a[1]


SVG=('<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 50 50">'
     '<rect x="10" y="10" width="30" height="30" fill="#e11e48" stroke="#777777" stroke-width="1"/></svg>')


def impossible():
    return render_svg('<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'+''.join(
        f'<circle cx="{x}" cy="{y}" r="6" fill="#666666"/>'
        for x,y in ((10,10),(40,10),(10,40),(40,40)))+'</svg>',50,50)


def test_template_failures_try_different_geometry_and_replay_same_seed():
    target=impossible()
    assertions=description_assertions('Ein Rechteck.')
    def run(seed):
        geometries=[]
        def renderer(svg,w,h):
            root=ET.fromstring(svg)
            for node in root.iter():
                for key in ('fill','stroke'):
                    node.attrib.pop(key,None)
            geometries.append(candidate_identity(ET.tostring(root,encoding='unicode')))
            return render_svg(svg,w,h)
        result=align_sample(ET.fromstring(SVG),target,renderer,deadline=time.monotonic()+30,
                            initial=render_svg(SVG,50,50),assertions=assertions,seed=seed)
        validate_svg_assertions(result['svg'],assertions)
        assert not pixel_quality(target,result['rendered'])['passed']
        assert result['search_control']['restarts']==8
        return result['search_control']['render_sequence_sha256'],geometries
    a=run(17)
    assert run(17)==a
    b=run(18)
    assert a[0]!=b[0] and set(a[1])!=set(b[1])


def test_public_template_entry_forwards_the_selected_seed(tmp_path):
    source,sample,output=(tmp_path/n for n in ('source.png','sample.svg','result.svg'))
    Image.fromarray(impossible()).save(source)
    sample.write_text(SVG,encoding='utf-8')
    result=refine(source,sample,output,'Ein Rechteck.',10,seed=2**64-1)
    assert result['alignment_search']['seed']==str(2**64-1)
    assert result['alignment_search']['render_sequence_sha256']!='00'*32
    assert not result['passed']


def test_light_surface_can_replace_wrong_red_template_paint():
    target=render_svg(SVG.replace('#e11e48','#eeeeee'),50,50)
    result=align_sample(ET.fromstring(SVG),target,render_svg,deadline=time.monotonic()+10,
        initial=render_svg(SVG,50,50),assertions=description_assertions('Ein Rechteck.'),seed=17)
    assert pixel_quality(target,result['rendered'])['passed']


def test_route_inventory_covers_every_registered_scene_fitter():
    from tools.audit_search_routes import inventory
    from src.iCCModules.imageCompositeConverterNonCompositeRuntime import scene_reconstruction_fitters
    report=inventory()
    rows={r['symbol']:r for r in report['routes']}
    for fitter,_ in scene_reconstruction_fitters():
        assert fitter.__module__+'.'+fitter.__name__ in rows
    assert all(row['behavior_verified'] is False for row in rows.values())
    assert rows['src.iCCModules.imageCompositeConverterSquareStem.fit_square_stem']['mechanism']==['custom_fitter']
    assert rows['src.iCCModules.imageCompositeConverterTwoWayValve.fit_two_way_valve']['mechanism']==['analytic_registration']
