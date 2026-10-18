from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np
import pytest
from src.iCCModules.imageCompositeConverterMotorValve import fit_motor_valve
from tools.evaluate_motor_valve_recheck import symbol_semantics
from tools.review_conversion_quality import normalized_mse
from tools.run_plan_b_variations import render, measure_quality

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'artifacts/evaluation/motor_valve_recheck_v1'
DESCRIPTION=(FOLDER/'description.txt').read_text(encoding='utf-8')


def fit(image,description=DESCRIPTION,render_fn=render):
    return fit_motor_valve(image.shape[1],image.shape[0],description=description,image=image,
        render_fn=render_fn,error_fn=lambda a,b:normalized_mse(a,b)[0])


@pytest.mark.parametrize('size',['L','M','S'])
def test_observed_catalog_sizes_pass_strict_gates_without_name_or_reference(size):
    image=cv2.imread(str(ROOT/f'artifacts/images_to_convert/AC0232_{size}.jpg'))
    result=fit(image)
    assert result is not None
    assert result['error'] < result['initial_error']
    assert measure_quality(image,result['svg'])['satisfactory']
    assert symbol_semantics(result['svg'])==1


@pytest.mark.parametrize('label',['R','P'])
@pytest.mark.parametrize('scale',[.8,1.4])
def test_independent_scene_with_other_glyph_palette_scale_and_position(label,scale):
    svg=(FOLDER/'independent.svg').read_text(encoding='utf-8').replace('>R</text>',f'>{label}</text>')
    image=render(svg,round(120*scale),round(86*scale))
    result=fit(image,DESCRIPTION.replace('"M"',f'"{label}"'))
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']
    assert symbol_semantics(result['svg'],label)==1


@pytest.mark.parametrize('kind',['wing','glyph','connector','extra','wrong_letter'])
def test_incomplete_or_contradictory_scenes_are_rejected(kind):
    root=ET.fromstring((FOLDER/'independent.svg').read_text(encoding='utf-8'))
    if kind=='wing':
        root.remove(root.findall('{*}path')[-1])
    elif kind=='glyph':
        root.remove(root.find('{*}text'))
    elif kind=='connector':
        root.remove(root.find('{*}line'))
    elif kind=='extra':
        ET.SubElement(root,'circle',cx='110',cy='74',r='6',fill='#333333')
    image=render(ET.tostring(root,encoding='unicode'),120,86)
    description=DESCRIPTION.replace('"M"','"P"' if kind=='wrong_letter' else '"R"')
    assert fit(image,description) is None


def test_failed_renderer_and_wrong_topology_description_are_rejected():
    image=render((FOLDER/'independent.svg').read_text(encoding='utf-8'),120,86)
    assert fit(image,render_fn=lambda *args:None) is None
    description=DESCRIPTION.replace('"M"','"R"')
    assert fit(image,description.replace('Griff nach rechts','Griff nach links')) is None


def test_head_direction_word_order_and_horizontal_synonym_preserve_fit():
    svg=(FOLDER/'independent.svg').read_text(encoding='utf-8')
    image=render(svg,120,86)
    description=DESCRIPTION.replace('"M"','"R"').replace('links, oben und unten','oben, unten sowie links').replace('waagerechter','horizontaler')
    result=fit(image,description)
    assert result is not None and measure_quality(image,result['svg'])['satisfactory']


def test_independent_topology_checker_rejects_missing_wing_and_wrong_letter():
    svg=(FOLDER/'independent.svg').read_text(encoding='utf-8')
    assert symbol_semantics(svg,'R')==1
    root=ET.fromstring(svg)
    root.remove(root.findall('{*}path')[0])
    assert symbol_semantics(ET.tostring(root,encoding='unicode'),'R')==0
    assert symbol_semantics(svg.replace('>R</text>','>M</text>'),'R')==0
