"""Rounded geometry must compose with the full residual-scene contract."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterStructureSearch import scene_key
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_rounded_composition import make_cases
from tools.run_plan_b_variations import make_variations


@pytest.mark.parametrize('case', make_cases(), ids=lambda c: c['case_id'])
def test_rounding_composes_with_inventory_layout_and_both_gradient_axes(case):
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('damage', ['missing', 'extra', 'square', 'count', 'layout', 'texture', 'outside'])
def test_rounding_cannot_erase_objects_relations_or_observed_marks(damage):
    case = deepcopy(make_cases()[3])
    root = ET.fromstring(case['svg'])
    if damage == 'missing':
        root.remove(root[-1])
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='94', y='133', width='9', height='9', rx='2', fill='black')
    elif damage == 'square':
        for rect in list(root)[-2:]:
            rect.set('rx', '0')
    elif damage == 'count':
        case['description'] = case['description'].replace('2 gefüllte', '3 gefüllte')
    elif damage == 'layout':
        case['description'] = case['description'].replace('nebeneinander', 'untereinander')
    elif damage == 'outside':
        root[-1].set('x', '183')
    else:
        rect = root[-1]
        ET.SubElement(root, 'rect', x=str(float(rect.get('x'))+4), y=str(float(rect.get('y'))+8),
                      width='12', height='4', fill='white')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


@pytest.mark.parametrize('claim', [
    ' Mit Text.', ' Die Formen überlappen.', ' Die Ecken sind nicht gerundet.',
    ' Die Kreise haben leicht gerundete Ecken.', ' Mit radialem Verlauf.',
    ' Die Rechtecke haben spitze Ecken.', ' Ein weiterer Kreis.',
])
def test_rounded_vocabulary_consumes_all_assertions(claim):
    assert mixed.scene_contract(make_cases()[3]['description']+claim) is None


def test_rounding_changes_the_structure_identity():
    import numpy as np
    obj = dict(kind='rectangle', geometry=np.array([20., 20., 30., 25., 0.]), colors=np.full(9, 50.))
    parent = dict(kind='circle', geometry=np.array([0., 0., 100., 100., 0.]), colors=np.full(9, 150.))
    assert scene_key([parent, dict(obj, radius=2.)]) != scene_key([parent, dict(obj, radius=5.)])


def test_rounded_shapes_compose_with_native_remove(monkeypatch):
    detect = mixed.detect_instances

    def duplicate(*args, **kwargs):
        objects = detect(*args, **kwargs)
        if objects:
            objects.append(deepcopy(objects[1]))
        return objects

    monkeypatch.setattr(mixed, 'detect_instances', duplicate)
    case = make_cases()[3]
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert any(a['operator'] == 'edit' and 'remove' in a['edits']
               and a['outcome'] == 'accepted' for a in result['scene_attempts'])


def test_rounded_detection_expiry_starts_no_registration(monkeypatch):
    detect = mixed.detect_instances
    now = [0.]
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1), clock=lambda: now[0])
    calls = []

    def expire(*args, **kwargs):
        objects = detect(*args, **kwargs)
        now[0] = 2.
        return objects

    def register(*args, **kwargs):
        calls.append(1)
        yield None

    monkeypatch.setattr(mixed, 'detect_instances', expire)
    monkeypatch.setattr(mixed, '_fit_instances_steps', register)
    assert fit(make_cases()[3], session)[1] is None
    assert not calls


def test_rounding_remains_bound_to_rectangles_in_a_mixed_inventory():
    case = deepcopy(make_cases()[3])
    root = ET.fromstring(case['svg'])
    ET.SubElement(root, 'circle', cx='105', cy='137', r='10.5', fill='#2a5471')
    case['description'] = case['description'].replace('Ein gefüllter Kreis', 'Zwei gefüllte Kreise')
    case['description'] = case['description'].replace('Der Kreis', 'Der äussere Kreis').replace(
        'Die Rechtecke liegen innerhalb des Kreises und getrennt nebeneinander',
        'Die inneren Formen liegen innerhalb des äusseren Kreises und getrennt voneinander')
    case['svg'] = ET.tostring(root, encoding='unicode')
    case['expected_objects'].append(dict(kind='circle', bbox=[94.5, 126.5, 21., 21.], parent=0,
                                         stroke_width=0))
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('index', [0, 4, 11])
def test_rounded_motif_scaling_and_translation_preserve_the_contract(index):
    source = make_cases()[3]
    case = make_variations(source['svg'], source['description'], 624731)[index]
    scale = case['variation']['scale']
    dx, dy = case['variation']['relative_x'], case['variation']['relative_y']
    w, h = source['width'], source['height']
    case['expected_objects'] = [dict(obj, bbox=[
        w/2+scale*(obj['bbox'][0]-w/2)+dx*w,
        h/2+scale*(obj['bbox'][1]-h/2)+dy*h,
        scale*obj['bbox'][2], scale*obj['bbox'][3]],
        **({'corner_radius': scale*obj['corner_radius']} if 'corner_radius' in obj else {}))
        for obj in source['expected_objects']]
    image, result = fit(case)
    assert_accepted(case, image, result)
