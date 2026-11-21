"""Closed compound descriptions must survive the real conversion entry point."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src import imageConverterGui as gui
from src.iCCModules.imageCompositeConverterDescriptionLanguage import (
    DescriptionRejected, description_assertions, validate_svg_assertions,
)
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterRepresentation import logical_inventory
from src.iCCModules.imageCompositeConverterTwoWayValve import two_way_valve_contract, fit_two_way_valve
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Es ist ein motorgetriebenes Zweiwegventil. Die beiden Ventile sind horizontal angeordnet. '
               'Der Motor ist als Kelle mit Griff nach unten realisiert '
               'Bei den Ventilen werden die beiden Formen zusammengehängt und ein Farbübergang gezeichnet.')
SQUARE_DESCRIPTION = ('Es ist ein motorgetriebenes Zweiwegventil. Die beiden Ventile sind horizontal angeordnet. '
                      'Der Motor ist als Quadrat mit einem Griff nach unten realisiert. '
                      'Die Diagonalen des Quadrats sind dunkelgrau, genau gleich wie der Rand des Quadrats. '
                      'Bei den Ventilen werden die beiden Formen zusammengehängt und ein Farbübergang gezeichnet.')


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg,w,h,fitz_module=fitz,np_module=np,cv2_module=cv2)


def fit(image, description=DESCRIPTION):
    return fit_two_way_valve(image.shape[1],image.shape[0],description=description,image=image,
                            render_fn=render,error_fn=lambda a,b:normalized_mse(a,b)[0])


@pytest.fixture(scope='module')
def original_result():
    result=fit(cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0201_M.jpg')))
    assert result is not None
    return result


@pytest.fixture(scope='module')
def square_result():
    return fit(cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0201_S_sia.jpg')),SQUARE_DESCRIPTION)


@pytest.mark.parametrize('motor',['als Quadrat','ein Quadrat','Quadrat'])
def test_square_motor_declares_complete_inventory_before_search(motor):
    description=SQUARE_DESCRIPTION.replace('als Quadrat',motor)
    desc,params=Reflection({'anonymous':description}).parseDescription('anonymous','anonymous.jpg')
    assert params['mode']=='non_composite'
    assert params['language_assertions']['objects']==dict(square=1,diagonal=2,line=1,triangle=2)


def test_reported_square_original_passes_without_changing_description(square_result):
    assert square_result is not None and square_result['quality']['passed']
    actual=next(e.get('beschreibung') for e in ET.parse(ROOT/'artifacts/descriptions/Finale_Wurzelformen_V3.xml').iter('bild')
                if e.text=='AC0201_S_sia.jpg')
    assert actual==SQUARE_DESCRIPTION
    validate_svg_assertions(square_result['svg'],description_assertions(actual))
    assert logical_inventory(square_result['svg'],dict(square=1,diagonal=2,line=1,triangle=2))==dict(square=1,diagonal=2,line=1,triangle=2)
    assert square_result['evaluations']>0


@pytest.mark.parametrize('fault',['missing_diagonal','wrong_diagonal','diagonal_color','deformed_square','handle','gradient'])
def test_square_motor_contract_survives_template_reuse(square_result,fault):
    root=ET.fromstring(square_result['svg'])
    lines=[e for e in root if e.tag.rsplit('}',1)[-1]=='line']
    square=next(e for e in root if e.tag.rsplit('}',1)[-1]=='rect' and e.get('stroke'))
    if fault=='missing_diagonal':
        root.remove(lines[-1])
    elif fault=='wrong_diagonal':
        lines[-1].set('x1',str(float(lines[-1].get('x1'))+.5))
    elif fault=='diagonal_color':
        lines[-1].set('stroke','#111111')
    elif fault=='deformed_square':
        square.set('width',str(float(square.get('width'))+.5))
    elif fault=='handle':
        lines[0].set('x1','0')
    else:
        next(e for e in root.iter() if e.tag.rsplit('}',1)[-1]=='linearGradient').attrib.pop('gradientUnits')
    with pytest.raises(DescriptionRejected):
        validate_svg_assertions(ET.tostring(root,encoding='unicode'),description_assertions(SQUARE_DESCRIPTION))


@pytest.mark.parametrize('description',[DESCRIPTION,SQUARE_DESCRIPTION])
@pytest.mark.parametrize('extra',[' Zusätzlich ein Kreis.',' Ohne Griff.',' Die Ventile sind vertikal angeordnet.'])
def test_both_motor_contracts_reject_unconsumed_claims(description,extra):
    assert not two_way_valve_contract(description+extra)


def test_compound_inventory_and_dispatch_are_independent_of_filename():
    for name in ('AC0201_M','neutral_valve'):
        desc,params = Reflection({name:DESCRIPTION}).parseDescription(name,name+'.jpg')
        assert params['mode'] == 'non_composite' and params['label'] == ''
        assert params['language_assertions']['objects'] == dict(circle=1,line=1,triangle=2)
        with pytest.raises(DescriptionRejected):
            validate_svg_assertions('<svg><circle cx="15" cy="11" r="9"/></svg>',
                                    params['language_assertions'])


@pytest.mark.parametrize('extra', [' Zusätzlich ein Quadrat.', ' Eine Beschriftung "M".',
                                  ' Ohne Griff.', ' Die Ventile sind vertikal angeordnet.'])
def test_contract_does_not_ignore_extra_or_contradictory_claims(extra):
    assert not two_way_valve_contract(DESCRIPTION+extra)
    assert fit(np.full((40,30,3),255,dtype='uint8'), DESCRIPTION+extra) is None


def test_reported_original_passes_with_complete_native_inventory(original_result):
    result = original_result
    assert result is not None and result['quality']['passed']
    assert result['error'] < result['initial_error']
    validate_svg_assertions(result['svg'],description_assertions(DESCRIPTION))
    assert logical_inventory(result['svg'],dict(circle=1,line=1,triangle=2)) == dict(circle=1,line=1,triangle=2)
    nodes = list(ET.fromstring(result['svg']).iter())
    wings = [e for e in nodes if e.tag.rsplit('}',1)[-1]=='path']
    assert len(wings)==2 and wings[0].get('fill') == wings[1].get('fill')
    assert not any(e.tag.rsplit('}',1)[-1] in {'image','text'} for e in nodes)


@pytest.mark.parametrize('fault', ['apex','handle','gradient'])
def test_template_edits_cannot_break_described_connections_or_gradient(original_result,fault):
    root=ET.fromstring(original_result['svg'])
    nodes=list(root.iter())
    if fault=='apex':
        wing=next(e for e in nodes if e.tag.rsplit('}',1)[-1]=='path')
        wing.set('transform','translate(0.1 0)')
    elif fault=='handle':
        line=next(e for e in nodes if e.tag.rsplit('}',1)[-1]=='line')
        line.set('x1',str(float(line.get('x1'))+1))
    else:
        gradient=next(e for e in nodes if e.tag.rsplit('}',1)[-1]=='linearGradient')
        gradient.attrib.pop('gradientUnits')
    with pytest.raises(DescriptionRejected):
        validate_svg_assertions(ET.tostring(root,encoding='unicode'),description_assertions(DESCRIPTION))


def test_common_translation_and_scale_preserve_compound_contract(original_result):
    root=ET.fromstring(original_result['svg'])
    group=ET.Element('{http://www.w3.org/2000/svg}g',transform='translate(3 4) scale(2)')
    for child in list(root):
        if child.tag.rsplit('}',1)[-1] not in {'defs','rect'}:
            root.remove(child)
            group.append(child)
    root.append(group)
    validate_svg_assertions(ET.tostring(root,encoding='unicode'),description_assertions(DESCRIPTION))


@pytest.mark.parametrize('scale,color',[(1,'#ededf4'),(2,'#dce9ec')])
@pytest.mark.parametrize('motor',['circle','square'])
def test_independent_geometry_scale_position_and_paint(scale,color,motor):
    w,h=40*scale,54*scale
    head=(f'<circle cx="20" cy="14" r="10" fill="{color}" stroke="#787b86" stroke-width="1.2"/>' if motor=='circle' else
          f'<rect x="10" y="4" width="20" height="20" fill="{color}" stroke="#787b86" stroke-width="1.2"/>'
          '<line x1="10" y1="4" x2="30" y2="24" stroke="#787b86" stroke-width="1.2"/>'
          '<line x1="30" y1="4" x2="10" y2="24" stroke="#787b86" stroke-width="1.2"/>')
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
         f'<defs><linearGradient id="v" x1="0%" y1="100%" x2="100%" y2="0%">'
         '<stop offset="0" stop-color="#7498ae"/><stop offset="1" stop-color="#e2e9ee"/></linearGradient></defs>'
         f'<rect width="{w}" height="{h}" fill="#ffffff"/>'
         f'<g transform="scale({scale})"><line x1="20" y1="14" x2="20" y2="39" stroke="#787b86" stroke-width="2"/>'
         f'<path d="M 3 31 L 3 47 L 20 39 Z" fill="url(#v)" stroke="#9296a0" stroke-width="1.2"/>'
         f'<path d="M 37 31 L 37 47 L 20 39 Z" fill="url(#v)" stroke="#9296a0" stroke-width="1.2"/>'
         +head+'</g></svg>')
    image=render(svg,w,h)
    description=DESCRIPTION if motor=='circle' else SQUARE_DESCRIPTION
    result=fit(image,description)
    assert result is not None and result['quality']['passed']
    validate_svg_assertions(result['svg'],description_assertions(description))


@pytest.mark.parametrize('filename,description',[('AC0201_M.jpg',DESCRIPTION),('AC0201_S_sia.jpg',SQUARE_DESCRIPTION)])
def test_real_gui_worker_replaces_stale_circle_and_preserves_description(tmp_path, monkeypatch,filename,description):
    monkeypatch.setattr(gui,'catalog_descriptions',lambda: {})
    jobs=gui.Jobs(tmp_path/'jobs')
    jobs.project_directory=tmp_path/'project'
    monkeypatch.setattr(jobs,'publish_best',lambda *args: None)
    try:
        job=jobs.upload('neutral_valve.jpg',(ROOT/'artifacts/images_to_convert'/filename).read_bytes())
        jobs.attach_sample(job['id'],'stale.svg',
            b'<svg xmlns="http://www.w3.org/2000/svg" width="30" height="40"><circle cx="12.5" cy="19" r="12" fill="#e2e2e2" stroke="#7f7f7f"/></svg>')
        started=jobs.start(job['id'],description,'quick',seed=42)
        jobs.threads[-1].join(timeout=55)
        result=jobs.snapshot(started['id'])
        assert result['status']=='done' and result['quality']=='passed',result
        assert result['description']==description and not result.get('recovery')
        svg=(jobs.folder(started['id'])/'result.svg').read_text(encoding='utf-8')
        validate_svg_assertions(svg,description_assertions(description))
    finally:
        jobs.close()
