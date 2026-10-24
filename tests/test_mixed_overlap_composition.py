"""Mixed overlapping primitives retain native inventory, depth and raster gates."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_layered_scene import check_objects
from tools.evaluate_mixed_overlap import make_cases
from tools.run_plan_b_variations import render


@pytest.mark.parametrize('rounded', [False, True])
@pytest.mark.parametrize('index', range(12))
def test_mixed_native_overlap_earns_independent_acceptance(index, rounded):
    case = make_cases(seed=486213, rounded=rounded)[index]
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert result['scene_attempts'][0]['painter_order'] == 'observed_depth'
    assert sum(a['outcome'] == 'accepted' for a in result['scene_attempts']) == 1
    assert sum(a['operator'] == 'edit' for a in result['scene_attempts']) <= 96


@pytest.mark.parametrize('claim', [' Mit Text.', ' Die Formen sind getrennt.',
    ' Der innere Kreis ist nicht gefüllt.', ' Der innere Kreis liegt vorne.',
    ' Ein zusätzlicher Kreis.', ' Die Kreise haben gerundete Ecken.'])
def test_unmodelled_claims_remain_unsupported(claim):
    assert mixed.scene_contract(make_cases()[0]['description']+claim) is None


@pytest.mark.parametrize('damage', ['missing', 'extra', 'same_color', 'ellipse',
                                   'square', 'texture', 'disjoint', 'bbox_only', 'outside', 'hidden_arc'])
def test_partial_circle_proposals_cannot_erase_contradictory_evidence(damage):
    case = deepcopy(make_cases()[0])
    root = ET.fromstring(case['svg'])
    circle, rectangle = root[-2:]
    cx, cy, radius = (float(circle.get(k)) for k in ('cx', 'cy', 'r'))
    if damage == 'missing':
        root.remove(rectangle)
    elif damage == 'extra':
        ET.SubElement(root, 'circle', cx='160', cy='68', r='12', fill='#765232')
    elif damage == 'same_color':
        rectangle.set('fill', circle.get('fill'))
    elif damage in ('ellipse', 'square'):
        root.remove(circle)
        element = (ET.Element('ellipse', cx=str(cx), cy=str(cy), rx=str(radius), ry=str(radius*.65),
                              fill=circle.get('fill')) if damage == 'ellipse' else
                   ET.Element('rect', x=str(cx-radius), y=str(cy-radius), width=str(2*radius),
                              height=str(2*radius), fill=circle.get('fill')))
        root.insert(len(root)-1, element)
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x=str(cx-13), y=str(cy-13), width='15', height='12', fill='white')
    elif damage == 'disjoint':
        rectangle.set('x', '134')
    elif damage == 'bbox_only':
        rectangle.set('x', str(cx+radius-5))
        rectangle.set('y', str(cy+radius-5))
    elif damage == 'outside':
        rectangle.set('x', '207')
    else:
        rectangle.set('x', str(cx-4))
        rectangle.set('y', str(cy-radius-5))
        rectangle.set('width', str(radius+14))
        rectangle.set('height', str(2*radius+10))
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_two_inner_circles_share_the_same_observed_arc_and_depth_search():
    case = deepcopy(make_cases()[0])
    root = ET.fromstring(case['svg'])
    rectangle = root[-1]
    x, y, w, h = (float(rectangle.get(k)) for k in ('x', 'y', 'width', 'height'))
    root.remove(rectangle)
    ET.SubElement(root, 'circle', cx=str(x+w/2), cy=str(y+w/2), r=str(w/2), fill=rectangle.get('fill'))
    case['svg'] = ET.tostring(root, encoding='unicode')
    case['description'] = case['description'].replace('2 gefüllte Kreise und 1 gefüllte Rechtecke',
                                                     '3 gefüllte Kreise')
    case['expected_objects'][-1].update(kind='circle', bbox=[x, y, w, w])
    case['expected_objects'][-1].pop('corner_radius')
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('seed,index', [(486213, 4), (983147, 10)])
def test_exposed_antialias_edges_supply_subpixel_circle_seeds(seed, index):
    case = make_cases(seed, rounded=True)[index]
    pixels = render(case['svg'], case['width'], case['height'])
    objects = mixed.detect_instances(pixels, mixed.scene_contract(case['description']))
    assert objects is not None
    expected = [o for o in case['expected_objects'][1:] if o['kind'] == 'circle']
    for obj in objects[1:]:
        if obj['kind'] == 'circle':
            assert min(max(abs(obj['geometry'][:4]-np.array(o['bbox']))) for o in expected) < .15


def test_opposite_circle_and_rectangle_depth_is_a_distinct_rejected_hypothesis():
    case = make_cases()[0]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    objects = mixed.detect_instances(pixels, contract)
    ordered = mixed.observed_painter_order(pixels, objects)
    from src.iCCModules.imageCompositeConverterSearchScheduler import drain
    result = drain(mixed._fit_instances_steps(case['width'], case['height'], pixels=pixels,
        contract=contract, objects=[ordered[0], *reversed(ordered[1:])], render_fn=render,
        error_fn=lambda a, b: float(abs(a.astype(float)-b).mean())))
    assert result is None
    root = ET.fromstring(case['svg'])
    back = root[-2]
    root.remove(back)
    root.append(back)
    assert not check_objects(ET.tostring(root, encoding='unicode'), case['expected_objects'])['passed']


def test_exhausted_mixed_structure_budget_starts_no_detector(monkeypatch):
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1))
    session.spent = 2
    monkeypatch.setattr(mixed, 'detect_instances', lambda *a, **k: pytest.fail('Expired budget'))
    assert fit(make_cases()[0], session)[1] is None
