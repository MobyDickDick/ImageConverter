"""Complete three-wing contracts must replace the misleading square fallback."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src import imageConverterGui as gui
from src.iCCModules.imageCompositeConverterDescriptionLanguage import (
    DescriptionRejected, description_assertions, draft_assertions, validate_svg_assertions,
)
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterRepresentation import description_object_limits
from src.iCCModules.imageCompositeConverterThreeWingValve import three_wing_valve_spec, fit_three_wing_valve

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Ein 3-Wege-Ventil mit drei spitzen Dreiecken links, oben und unten, die sich in einer gemeinsamen Spitze treffen. '
               'Die Dreiecke haben einen diagonalen Grauverlauf von dunkel links unten nach hell rechts oben und eine graue Randkontur. '
               'Von der gemeinsamen Spitze führt ein waagerechter gerader Griff nach rechts zur linken Seite einem hellen Quadrat mit dunkler Randkontur. '
               'Die Diagonalen des Quadrats sind dunkelgrau gezeichnet. Keine weiteren Objekte. Maße und Farben ergeben sich aus dem Bild.')
INVENTORY = dict(triangle=3, line=1, square=1, diagonal=2)


def render(svg,w,h):
    return render_svg_to_numpy_inprocess(svg,w,h,fitz_module=fitz,np_module=np,cv2_module=cv2)


def fit(image):
    return fit_three_wing_valve(image.shape[1],image.shape[0],description=DESCRIPTION,image=image,
                               render_fn=render,error_fn=lambda a,b:float(np.square(a.astype(float)-b).mean()/255**2))


@pytest.fixture(scope='module')
def original_result():
    result=fit(cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0222_L_sia.jpg')))
    assert result is not None and result['quality']['passed']
    return result


def test_dative_plural_triangles_are_counted_without_a_compound_contract():
    assert description_object_limits('Mit drei spitzen Dreiecken.')==dict(triangle=3)
    assert description_object_limits('Mit zwei gefüllten Rechtecken und vier kleinen Quadraten.')==dict(rect=2,square=4)


def test_complete_inventory_and_dispatch_are_independent_of_name():
    for name in ('AC0222_L_sia','anonymous_symbol'):
        _,params=Reflection({name:DESCRIPTION}).parseDescription(name,name+'.jpg')
        assert params['mode']=='non_composite' and params['label']=='' and params['geometry_ir']==[]
        assert params['language_assertions']['objects']==INVENTORY
        assert params['language_assertions']['three_wing_valve']


@pytest.mark.parametrize('extra',[' Zusätzlich ein Kreis.',' Ohne Griff.',' Die Dreiecke sind rechts angeordnet.'])
def test_closed_contract_never_ignores_extra_claims(extra):
    assert three_wing_valve_spec(DESCRIPTION+extra) is None


def test_maintained_description_and_full_geometry_pass(original_result):
    actual=next(e.get('beschreibung') for e in ET.parse(ROOT/'artifacts/descriptions/Finale_Wurzelformen_V3.xml').iter('bild')
                if e.text=='AC0222_L_sia.jpg')
    assert actual==DESCRIPTION
    validate_svg_assertions(original_result['svg'],description_assertions(actual))
    assert original_result['quality']['foreground_iou']>.95
    assert original_result['quality']['edge_alignment']>.9
    assert original_result['error']<original_result['initial_error']


@pytest.mark.parametrize('draft',[False,True])
@pytest.mark.parametrize('fault',['missing_wing','apex','handle','diagonal','square','gradient','direction','flat','red_border','light_diagonal'])
def test_drafts_and_templates_keep_all_geometry_constraints(original_result,draft,fault):
    root=ET.fromstring(original_result['svg'])
    wing=next(e for e in root if e.tag.rsplit('}',1)[-1]=='path')
    line=next(e for e in root if e.tag.rsplit('}',1)[-1]=='line')
    square=next(e for e in root if e.tag.rsplit('}',1)[-1]=='rect' and e.get('stroke'))
    gradient=next(e for e in root.iter() if e.tag.rsplit('}',1)[-1]=='linearGradient')
    if fault=='missing_wing': root.remove(wing)
    elif fault=='apex': wing.set('transform','translate(.2 0)')
    elif fault=='handle': line.set('x1',str(float(line.get('x1'))+1))
    elif fault=='diagonal': root.remove(list(root)[-1])
    elif fault=='square': square.set('height',str(float(square.get('height'))+1))
    elif fault=='gradient': wing.set('fill','#cccccc')
    elif fault=='direction': gradient.set('y2','200%')
    elif fault=='red_border': wing.set('stroke','#ff0000')
    elif fault=='light_diagonal': list(root)[-1].set('stroke','#ffffff')
    else: gradient[1].set('stop-color',gradient[0].get('stop-color'))
    assertions=description_assertions(DESCRIPTION)
    with pytest.raises(DescriptionRejected):
        validate_svg_assertions(ET.tostring(root,encoding='unicode'),draft_assertions(assertions) if draft else assertions)


@pytest.mark.parametrize('scale',[1,2])
def test_independent_three_wing_geometry_and_scale(scale):
    # Independently authored geometry, paint and dimensions, no fitted fixture.
    w,h=92*scale,64*scale
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
         '<defs><linearGradient id="g" x1="0%" y1="100%" x2="100%" y2="0%">'
         '<stop offset="0" stop-color="#ababab"/><stop offset="1" stop-color="#e8e8e8"/></linearGradient></defs>'
         f'<rect width="{w}" height="{h}" fill="white"/><g transform="scale({scale})">'
         '<line x1="30" y1="31" x2="56" y2="31" stroke="#707070" stroke-width="2.5"/>'
         '<path d="M 30 31 L 6 17 L 6 45 Z" fill="url(#g)" stroke="#969696" stroke-width="1.5"/>'
         '<path d="M 30 31 L 16 6 L 43 6 Z" fill="url(#g)" stroke="#969696" stroke-width="1.5"/>'
         '<path d="M 30 31 L 15 56 L 44 56 Z" fill="url(#g)" stroke="#969696" stroke-width="1.5"/>'
         '<rect x="56" y="20" width="22" height="22" fill="#f8f8f8" stroke="#707070" stroke-width="1.5"/>'
         '<line x1="56" y1="20" x2="78" y2="42" stroke="#707070" stroke-width="1.5"/>'
         '<line x1="56" y1="42" x2="78" y2="20" stroke="#707070" stroke-width="1.5"/></g></svg>')
    result=fit(render(svg,w,h))
    assert result is not None and result['quality']['passed']
    validate_svg_assertions(result['svg'],description_assertions(DESCRIPTION))


def test_real_gui_worker_discards_the_reported_incomplete_square(tmp_path,monkeypatch):
    monkeypatch.setattr(gui,'catalog_descriptions',lambda: {})
    jobs=gui.Jobs(tmp_path/'jobs')
    jobs.project_directory=tmp_path/'project'
    monkeypatch.setattr(jobs,'publish_best',lambda *args:None)
    try:
        uploaded=jobs.upload('anonymous_valve.jpg',(ROOT/'artifacts/images_to_convert/AC0222_L_sia.jpg').read_bytes())
        jobs.attach_sample(uploaded['id'],'stale.svg',
            b'<svg xmlns="http://www.w3.org/2000/svg" width="75" height="50">'
            b'<rect x="1" y="1" width="48" height="48" fill="#d8d8d8"/>'
            b'<path d="M 48 2 L 2 48" stroke="white" fill="none"/></svg>')
        started=jobs.start(uploaded['id'],DESCRIPTION,'quick',seed=2026)
        jobs.threads[-1].join(timeout=70)
        result=jobs.snapshot(started['id'])
        assert result['status']=='done' and result['quality']=='passed',result
        assert result['description']==DESCRIPTION
        validate_svg_assertions((jobs.folder(started['id'])/'result.svg').read_text(encoding='utf-8'),description_assertions(DESCRIPTION))
    finally:
        jobs.close()
