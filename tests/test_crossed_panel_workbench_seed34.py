"""The reported vocabulary and false green grades must not recur."""
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterCrossedGradientPanel import fit_crossed_gradient_panel
from tools.run_plan_b_variations import render,measure_quality,make_original_case,make_variations
from tools.check_crossed_panel_scene import check_scene

FIXTURE = Path(__file__).parent/'fixtures/crossed_panel_seed34'
SVG = (FIXTURE/'source.svg').read_text(encoding='utf-8')
DESCRIPTION = (FIXTURE/'description.txt').read_text(encoding='utf-8')
CASES = [make_original_case(SVG,DESCRIPTION),*make_variations(SVG,DESCRIPTION,34,expand_canvas=True)]


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['case_id'])
def test_reported_original_and_all_sixteen_variants_fit_and_keep_the_complete_scene(case):
    image = render(case['svg'],case['width'],case['height'])
    fitted = fit_crossed_gradient_panel(case['width'],case['height'],description=case['description'],image=image,
        render_fn=render,error_fn=lambda a,b:float(np.square(a.astype(float)-b.astype(float)).mean()/255**2))
    assert fitted is not None
    result = measure_quality(image,fitted['svg'],description=case['description'])
    assert result['satisfactory'],result
    assert result['scene']['passed']
    assert result['metrics']['normalized_mse']<.001


@pytest.mark.parametrize('index,name',[(0,'false_pass_original.svg'),(3,'false_pass_probe03.svg')])
def test_actual_false_green_exports_fail_described_scene_checks(index,name):
    case = CASES[index]
    image = render(case['svg'],case['width'],case['height'])
    broken = (FIXTURE/name).read_text(encoding='utf-8')
    assert measure_quality(image,broken)['satisfactory']  # The previous gate.
    checked = measure_quality(image,broken,description=case['description'])
    assert not checked['satisfactory']
    assert 'scene_structure_mismatch' in checked['failures']


NATIVE = ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="80" viewBox="0 0 40 80">'
 '<defs><linearGradient id="random-paint" x1="1" x2="39" y1="0" y2="0">'
 '<stop offset="0" stop-color="#cccccc"/><stop offset=".4" stop-color="#f6f6f6"/>'
 '<stop offset="1" stop-color="#cccccc"/></linearGradient></defs>'
 '<rect x="1" y="1" width="38" height="78" fill="url(#random-paint)"/>'
 '<polygon points="1,1 4,1 39,79 36,79" fill="#868686"/>'
 '<polygon points="36,1 39,1 4,79 1,79" fill="#868686"/>'
 '<rect x="16" y="8" width="8" height="2" fill="#696969"/>'
 '<rect x="19" y="5" width="2" height="8" fill="#696969"/>'
 '<rect x="16" y="15" width="8" height="2" fill="#696969"/>'
 '<rect x="1" y="1" width="38" height="78" fill="none" stroke="#9f9f9f" stroke-width="1"/></svg>')


def test_independently_authored_scene_and_arbitrary_ids_are_supported():
    assert check_scene(NATIVE,40,80)['passed']


@pytest.mark.parametrize('damage',['missing_plus','missing_minus','missing_diagonal','extra_line',
                                  'hidden_extra','swapped','short_arm','invisible_mark','tiny_mark'])
def test_incomplete_or_extra_native_geometry_is_rejected(damage):
    root = ET.fromstring(NATIVE)
    bands = root.findall('{*}polygon')
    marks = root.findall('{*}rect')[1:4]
    if damage=='missing_plus':root.remove(marks[1])
    elif damage=='missing_minus':root.remove(marks[2])
    elif damage=='missing_diagonal':root.remove(bands[0])
    elif damage in {'extra_line','hidden_extra'}:
        line = ET.SubElement(root,'{http://www.w3.org/2000/svg}line',x1='4',y1='4',x2='8',y2='8',stroke='#808080')
        if damage=='hidden_extra':line.set('opacity','0')
    elif damage=='swapped':marks[2].set('y','3')
    elif damage=='short_arm':bands[0].set('points','1,1 4,1 20,39 17,39')
    elif damage=='invisible_mark':marks[2].set('opacity','0')
    elif damage=='tiny_mark':marks[2].set('height','.001')
    assert not check_scene(ET.tostring(root,encoding='unicode'),40,80)['passed']


def test_a_band_hidden_behind_the_housing_cannot_supply_visible_diagonal_support():
    root = ET.fromstring(NATIVE)
    band = root.find('{*}polygon')
    root.remove(band)
    root.insert(1,band)  # Behind the opaque housing rather than on its surface.
    broken = ET.tostring(root,encoding='unicode')
    reference = render(NATIVE,40,80)
    checked = check_scene(broken,40,80,reference=reference,rendered=render(broken,40,80))
    assert not checked['passed']
    assert checked['reason'].startswith('arm_')
