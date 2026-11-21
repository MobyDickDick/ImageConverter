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
def test_independent_geometry_scale_position_and_paint(scale,color):
    w,h=40*scale,54*scale
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
         f'<defs><linearGradient id="v" x1="0%" y1="100%" x2="100%" y2="0%">'
         '<stop offset="0" stop-color="#7498ae"/><stop offset="1" stop-color="#e2e9ee"/></linearGradient></defs>'
         f'<rect width="{w}" height="{h}" fill="#ffffff"/>'
         f'<g transform="scale({scale})"><line x1="20" y1="14" x2="20" y2="39" stroke="#787b86" stroke-width="2"/>'
         f'<path d="M 3 31 L 3 47 L 20 39 Z" fill="url(#v)" stroke="#9296a0" stroke-width="1.2"/>'
         f'<path d="M 37 31 L 37 47 L 20 39 Z" fill="url(#v)" stroke="#9296a0" stroke-width="1.2"/>'
         f'<circle cx="20" cy="14" r="10" fill="{color}" stroke="#787b86" stroke-width="1.2"/></g></svg>')
    image=render(svg,w,h)
    result=fit(image)
    assert result is not None and result['quality']['passed']
    validate_svg_assertions(result['svg'],description_assertions(DESCRIPTION))


def test_real_gui_worker_replaces_stale_circle_and_preserves_description(tmp_path, monkeypatch):
    monkeypatch.setattr(gui,'catalog_descriptions',lambda: {})
    jobs=gui.Jobs(tmp_path/'jobs')
    jobs.project_directory=tmp_path/'project'
    monkeypatch.setattr(jobs,'publish_best',lambda *args: None)
    try:
        job=jobs.upload('neutral_valve.jpg',(ROOT/'artifacts/images_to_convert/AC0201_M.jpg').read_bytes())
        jobs.attach_sample(job['id'],'stale.svg',
            b'<svg xmlns="http://www.w3.org/2000/svg" width="30" height="40"><circle cx="12.5" cy="19" r="12" fill="#e2e2e2" stroke="#7f7f7f"/></svg>')
        started=jobs.start(job['id'],DESCRIPTION,'quick',seed=42)
        jobs.threads[-1].join(timeout=55)
        result=jobs.snapshot(started['id'])
        assert result['status']=='done' and result['quality']=='passed',result
        assert result['description']==DESCRIPTION and not result.get('recovery')
        svg=(jobs.folder(started['id'])/'result.svg').read_text(encoding='utf-8')
        validate_svg_assertions(svg,description_assertions(DESCRIPTION))
    finally:
        jobs.close()
