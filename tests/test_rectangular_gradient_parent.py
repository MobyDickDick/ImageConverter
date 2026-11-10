"""Rectangular parents share native instances, topology and quality gates."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_layered_scene import check_objects
from tools.evaluate_rectangular_parent import make_cases
from tools.run_plan_b_variations import render


@pytest.mark.parametrize('index', range(12))
def test_independent_fixture_keeps_native_parent_and_complete_inventory(index):
    case = make_cases()[index]
    assert check_objects(case['svg'], case['expected_objects'])['passed']
    assert case['expected_objects'][0]['kind'] == 'rectangle'
    assert len(case['expected_objects']) == [4, 6, 5, 7][index % 4]


@pytest.mark.parametrize('index', range(12))
def test_rectangular_parent_composes_under_existing_budget(index):
    case = make_cases()[index]
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert result['object_kinds'][0] == 'rectangle'
    assert sum(a['operator'] in ('edit', 'split_edit', 'group_islands')
               for a in result['scene_attempts']) <= 96


@pytest.mark.parametrize('claim', [' Mit Text.', ' Das äussere Rechteck ist gerundet.',
    ' Die Formen sind nicht gefüllt.', ' Die Gruppen überlappen sich.',
    ' Ein zusätzlicher Kreis.', ' Die inneren Kreise haben leicht gerundete Ecken.'])
def test_new_parent_contract_does_not_erase_other_assertions(claim):
    assert mixed.scene_contract(make_cases()[0]['description']+claim) is None


@pytest.mark.parametrize('damage', ['missing', 'extra', 'texture', 'wrong_axis',
    'wrong_parent', 'wrong_groups', 'wrong_singletons', 'dark_rim', 'missing_rim', 'rounded_parent'])
def test_parent_change_preserves_complete_object_relation_and_pixel_gates(damage):
    case = deepcopy(make_cases()[1])
    root = ET.fromstring(case['svg'])
    parent = root[2]
    if damage == 'missing':
        root.remove(root[-1])
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='165', y='165', width='12', height='12', fill='#123456')
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x='165', y='165', width='12', height='12', fill='white')
    elif damage == 'wrong_axis':
        case['description'] = case['description'].replace('vertikalen', 'horizontalen')
    elif damage == 'wrong_parent':
        parent.tag = '{http://www.w3.org/2000/svg}circle'
        parent.attrib.update(cx='180', cy='180', r='165')
        for key in ('x', 'y', 'width', 'height'):
            parent.attrib.pop(key)
    elif damage == 'wrong_groups':
        case['description'] = case['description'].replace('2 Überdeckungsgruppen', '1 Überdeckungsgruppe')
    elif damage == 'wrong_singletons':
        case['description'] = case['description'].replace('1 einzelne Form', '2 einzelne Formen')
    elif damage == 'rounded_parent':
        parent.set('rx', '24')
    else:
        parent.set('stroke', '#303030' if damage == 'dark_rim' else 'none')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_expired_budget_starts_no_rectangular_detection(monkeypatch):
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1))
    session.spent = 2
    monkeypatch.setattr(mixed, 'detect_instances', lambda *a, **k: pytest.fail('Expired budget'))
    assert fit(make_cases()[0], session)[1] is None


def test_parent_kind_is_bound_to_the_contract_during_registration():
    from src.iCCModules.imageCompositeConverterSearchScheduler import drain
    case = make_cases()[0]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    objects = mixed.detect_instances(pixels, contract)
    objects[0]['kind'] = 'circle'
    assert drain(mixed._fit_instances_steps(case['width'], case['height'], pixels=pixels,
        contract=contract, objects=objects, render_fn=render,
        error_fn=lambda a, b: float(abs(a.astype(float)-b).mean()))) is None


@pytest.mark.parametrize('replacement', ['9 gefüllte Rechtecke', '1 gefüllte Rechtecke'])
def test_inventory_limits_still_include_the_rectangular_parent(replacement):
    text = make_cases()[0]['description'].replace('2 gefüllte Rechtecke', replacement)
    assert mixed.scene_contract(text) is None


def test_parent_contract_is_not_inferred_from_pixels():
    case = make_cases()[0]
    contract = mixed.scene_contract(case['description'])
    assert contract['parent_kind'] == 'rectangle'
    assert contract['children'] == {'circle': 2, 'rectangle': 1}
    assert not contract['rounded']


@pytest.mark.parametrize('claim', [' Die inneren Rechtecke haben leicht gerundete Ecken.',
    ' mit leicht gerundeten Ecken'])
def test_ambiguous_or_repeated_rounding_claims_fail(claim):
    assert mixed.scene_contract(make_cases()[1]['description']+claim) is None


@pytest.mark.parametrize('kind', ['circle', 'rectangle'])
def test_parent_supports_homogeneous_child_inventories(kind):
    case = make_cases()[0]
    root = ET.fromstring(case['svg'])
    for element, obj in zip(list(root)[3:], case['expected_objects'][1:]):
        if obj['kind'] == kind:
            continue
        x, y, w, h = obj['bbox']
        for key in ('cx', 'cy', 'r', 'x', 'y', 'width', 'height', 'rx'):
            element.attrib.pop(key, None)
        element.tag = '{http://www.w3.org/2000/svg}'+('rect' if kind == 'rectangle' else kind)
        if kind == 'rectangle':
            element.attrib.update(x=str(x), y=str(y), width=str(w), height=str(h))
        else:
            element.attrib.update(cx=str(x+w/2), cy=str(y+w/2), r=str(w/2))
            obj['bbox'][3] = w
        obj.update(kind=kind)
        obj.pop('corner_radius', None)
    inventory = '4 gefüllte Rechtecke' if kind == 'rectangle' else '3 gefüllte Kreise und ein gefülltes Rechteck'
    case.update(svg=ET.tostring(root, encoding='unicode'),
                description=inventory+'. '+case['description'].split('. ', 1)[1])
    image, result = fit(case)
    assert_accepted(case, image, result)


def test_rectangular_parent_also_reuses_the_separated_instance_path():
    case = make_cases()[0]
    root = ET.fromstring(case['svg'])
    root.remove(root[4])
    case['expected_objects'].pop(2)
    for obj in case['expected_objects'][1:]:
        obj['behind_all'] = []
    description = ('2 gefüllte Kreise und ein gefülltes Rechteck. '
        'Das äussere Rechteck hat einen horizontalen Farbverlauf. '
        'Die inneren Formen liegen innerhalb des äusseren Rechtecks und getrennt voneinander. Keine Beschriftung.')
    case.update(svg=ET.tostring(root, encoding='unicode'), description=description)
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('damage', ['clipped', 'child_outside'])
def test_frame_edges_and_children_outside_parent_remain_rejections(damage):
    case = make_cases()[0]
    root = ET.fromstring(case['svg'])
    if damage == 'clipped':
        root[2].set('x', '-8')
        root[2].set('width', '344')
    else:
        root[2].set('width', '180')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_wrong_observed_painter_order_cannot_be_accepted():
    from src.iCCModules.imageCompositeConverterSearchScheduler import drain
    case = make_cases()[1]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    objects = mixed.detect_instances(pixels, contract)
    ordered = mixed.observed_painter_order(pixels, objects)
    assert ordered is not None
    assert drain(mixed._fit_instances_steps(case['width'], case['height'], pixels=pixels,
        contract=contract, objects=[ordered[0], *reversed(ordered[1:])], render_fn=render,
        error_fn=lambda a, b: float(abs(a.astype(float)-b).mean()))) is None


def test_rectangular_parent_rejects_a_relation_to_another_parent_kind():
    text = make_cases()[0]['description'].replace('des äusseren Rechtecks', 'des äusseren Kreises')
    assert mixed.scene_contract(text) is None
