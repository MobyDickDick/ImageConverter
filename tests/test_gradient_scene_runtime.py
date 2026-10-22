"""Native scene semantics and independent geometry/pixel damage controls."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterGradientScene import scene_contract
from src.iCCModules.imageCompositeConverterPrimitiveScene import fit_primitive_scene
from tools.evaluate_gradient_scene import make_cases
from tools.evaluate_layered_scene import check_objects, local_checks
from tools.run_plan_b_variations import render, measure_quality


def fit(case, description=None):
    image = render(case['svg'], case['width'], case['height'])
    before = image.copy()
    result = fit_primitive_scene(case['width'], case['height'], image=image,
        description=description or case['description'], render_fn=render,
        error_fn=lambda a, b: float(abs(a.astype(float)-b).mean()))
    np.testing.assert_array_equal(image, before)
    return image, result


@pytest.mark.parametrize('case', make_cases(290921, 12), ids=lambda c: c['case_id'])
def test_independent_native_geometry_and_regions(case):
    image, result = fit(case)
    assert result is not None
    assert result['source'] == 'primitive_gradient_scene_v1'
    assert result['error'] <= result['initial_error']
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert measure_quality(image, result['svg'])['satisfactory']
    assert all(q['passed'] for q in local_checks(image, result['svg'], case['expected_objects']))


@pytest.mark.parametrize('addition', [
    ' Nicht ohne Text.', ' Mit zusätzlicher Linie.', ' Die innere Form ist rot.',
    ' Nicht ineinander verschachtelt.', ' Die linke Form liegt vor der rechten Form.',
    ' Ein Kreis.', ' Ohne Füllung.', ' Die äußere Form ist nicht gerundet.',
    ' Mit radialem Farbverlauf.', ' Mit einer unbekannten Kurve.',
])
def test_unknown_or_contradictory_assertions_reject_the_model(addition):
    assert scene_contract(make_cases()[0]['description']+addition) is None


@pytest.mark.parametrize('size', ['größer', 'kleiner'])
def test_whole_motif_words_preserve_the_object_contract(size):
    text = make_cases()[0]['description']
    assert scene_contract(text+f' Das gesamte Motiv ist etwas {size} dargestellt und leicht nach links und unten verschoben.') == scene_contract(text)


def test_outlined_rectangle_can_touch_all_image_edges():
    case = make_cases()[1]
    case['svg'] = (case['svg'].replace('x="13.0"', 'x="0.0"').replace('y="17.0"', 'y="0.0"')
                   .replace('width="181.0"', 'width="210.0"').replace('height="95.0"', 'height="130.0"'))
    image, result = fit(case)
    assert result is not None
    assert measure_quality(image, result['svg'])['satisfactory']


def test_three_separate_gradient_rectangles_share_the_same_scene_path():
    case = make_cases()[2]
    root = ET.fromstring(case['svg'])
    root.set('width', '320')
    root[1].set('width', '320')
    third = deepcopy(root[-1])
    third.set('x', str(float(third.get('x'))+102))
    root.append(third)
    case['width'] = 320
    case['description'] = case['description'].replace('Zwei', 'Drei')
    case['svg'] = ET.tostring(root, encoding='unicode')
    obj = deepcopy(case['expected_objects'][-1])
    obj['bbox'][0] += 102
    case['expected_objects'].append(obj)
    image, result = fit(case)
    assert result is not None
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('damage', ['flat', 'axis', 'missing_child', 'extra_child'])
def test_incompatible_raster_is_not_a_native_scene_success(damage):
    case = deepcopy(make_cases()[0])
    root = ET.fromstring(case['svg'])
    gradient = list(root[0])[0]
    if damage == 'flat':
        gradient[1].set('stop-color', gradient[0].get('stop-color'))
    elif damage == 'axis':
        gradient.set('x2', '0%')
        gradient.set('y2', '100%')
    elif damage == 'missing_child':
        root.remove(root[-1])
    else:
        ET.SubElement(root, '{http://www.w3.org/2000/svg}rect',
                      x='155', y='60', width='18', height='20', fill='white')
    case['svg'] = ET.tostring(root, encoding='unicode')
    _, result = fit(case)
    assert result is None


@pytest.mark.parametrize('damage', ['corners', 'contour', 'child', 'paint', 'axis', 'definition'])
def test_independent_oracle_detects_damaged_outputs(damage):
    case = make_cases()[9]  # nested and outlined
    image = render(case['svg'], case['width'], case['height'])
    root = ET.fromstring(case['svg'])
    if damage == 'corners':
        root[-2].set('rx', '0')
    elif damage == 'contour':
        root[-2].set('stroke-width', '0')
    elif damage == 'child':
        root.remove(root[-1])
    elif damage == 'paint':
        root[-2].set('fill', '#111111')
    elif damage == 'axis':
        root[0][0].set('x2', '100%')
        root[0][0].set('y2', '0%')
    else:
        ET.SubElement(root[0], '{http://www.w3.org/2000/svg}image', href='forbidden.png')
    svg = ET.tostring(root, encoding='unicode')
    structural = check_objects(svg, case['expected_objects'])['passed']
    assert not structural or not all(q['passed'] for q in local_checks(image, svg, case['expected_objects']))
