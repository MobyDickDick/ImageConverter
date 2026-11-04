"""Mixed topology retains every instance, depth edge and separating gap."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_layered_scene import check_objects
from tools.evaluate_mixed_topology import make_cases
from tools.run_plan_b_variations import render


@pytest.mark.parametrize('index', range(12))
def test_reference_geometry_keeps_complete_oracle(index):
    case = make_cases()[index]
    assert check_objects(case['svg'], case['expected_objects'])['passed']
    assert len(case['expected_objects']) == [4, 6, 5, 7][index % 4]


@pytest.mark.parametrize('index', range(12))
def test_overlapping_groups_and_singletons_compose_under_one_budget(index):
    case = make_cases()[index]
    image, result = fit(case)
    assert_accepted(case, image, result)
    accepted = [a for a in result['scene_attempts'] if a['outcome'] == 'accepted']
    assert len(accepted) == 1 and accepted[0]['painter_order'] == 'observed_depth'
    assert sum(a['operator'] in ('edit', 'split_edit', 'group_islands')
               for a in result['scene_attempts']) <= 96


@pytest.mark.parametrize('rounded,outlined,same_fill', [(False, False, False),
    (True, False, False), (False, True, False), (True, True, True)])
def test_composition_reuses_existing_paint_and_rounding_operators(rounded, outlined, same_fill):
    case = make_cases(rounded=rounded, outlined=outlined, same_fill=same_fill)[3]
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('kind', ['rectangle', 'circle'])
def test_singletons_can_be_rectangles_or_circles(kind):
    case = make_cases(rounded=False)[3]
    root = ET.fromstring(case['svg'])
    for element, obj in zip(list(root)[3:], case['expected_objects'][1:]):
        if obj['kind'] == kind:
            continue
        x, y, w, h = obj['bbox']
        sw = obj['stroke_width']
        for key in ('cx', 'cy', 'r', 'x', 'y', 'width', 'height', 'rx'):
            element.attrib.pop(key, None)
        element.tag = '{http://www.w3.org/2000/svg}'+('rect' if kind == 'rectangle' else kind)
        if kind == 'rectangle':
            element.attrib.update(x=str(x+sw/2), y=str(y+sw/2), width=str(w-sw), height=str(h-sw))
        else:
            element.attrib.update(cx=str(x+w/2), cy=str(y+w/2), r=str((w-sw)/2))
            obj['bbox'][3] = w
        obj.update(kind=kind)
        obj.pop('corner_radius', None)
    count = len(case['expected_objects'])-1
    inventory = (f'Ein gefüllter Kreis und {count} gefüllte Rechtecke' if kind == 'rectangle'
                 else f'{count+1} gefüllte Kreise')
    case['description'] = inventory+'. '+case['description'].split('. ', 1)[1]
    case['svg'] = ET.tostring(root, encoding='unicode')
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('groups,isolated', [('1', '1'), ('eine', 'eine'), ('ein', 'ein')])
def test_full_contract_includes_group_and_singleton_counts(groups, isolated):
    text = make_cases()[0]['description'].replace('1 Überdeckungsgruppe', groups+' Überdeckungsgruppe')
    text = text.replace('1 einzelne Form', isolated+' einzelne Form')
    contract = mixed.scene_contract(text)
    assert contract is not None
    assert contract['overlap_groups'] == 1 and contract['isolated_children'] == 1


def test_written_plural_counts_are_consumed():
    text = make_cases()[3]['description'].replace('2 Überdeckungsgruppen', 'zwei Überdeckungsgruppen')
    text = text.replace('2 einzelne Formen', 'zwei einzelne Formen')
    contract = mixed.scene_contract(text)
    assert contract['overlap_groups'] == contract['isolated_children'] == 2


@pytest.mark.parametrize('claim', [' Mit Text.', ' Die Formen sind nicht gefüllt.',
    ' Die Gruppen überlappen sich.', ' Ein zusätzlicher Kreis.',
    ' Die einzelnen Formen liegen innerhalb einer Gruppe.'])
def test_topology_clause_does_not_erase_other_assertions(claim):
    assert mixed.scene_contract(make_cases()[0]['description']+claim) is None


@pytest.mark.parametrize('old,new', [
    ('1 Überdeckungsgruppe', '0 Überdeckungsgruppen'),
    ('1 Überdeckungsgruppe', '2 Überdeckungsgruppen'),
    ('1 einzelne Form', '0 einzelne Formen'),
    ('1 einzelne Form', '2 einzelne Formen'),
    ('1 einzelne Form', '9 einzelne Formen'),
    ('Die Gruppen und einzelnen Formen liegen getrennt voneinander.', ''),
    ('Die Gruppen und einzelnen Formen liegen getrennt voneinander.',
     'Die Gruppen und einzelnen Formen liegen getrennt voneinander. '*2),
])
def test_impossible_or_incomplete_topology_claims_are_unsupported(old, new):
    assert mixed.scene_contract(make_cases()[0]['description'].replace(old, new)) is None


@pytest.mark.parametrize('damage', ['wrong_groups', 'wrong_singletons', 'connected_contract',
    'missing', 'extra', 'texture', 'wrong_order'])
def test_topology_does_not_excuse_incorrect_objects_or_relations(damage):
    case = deepcopy(make_cases()[3])
    root = ET.fromstring(case['svg'])
    if damage == 'wrong_groups':
        case['description'] = case['description'].replace('2 Überdeckungsgruppen', '1 Überdeckungsgruppe')
    elif damage == 'wrong_singletons':
        case['description'] = case['description'].replace('2 einzelne Formen', '1 einzelne Form')
    elif damage == 'connected_contract':
        case['description'] = case['description'].replace(
            'und bilden 2 Überdeckungsgruppen sowie 2 einzelne Formen. '
            'Die Gruppen und einzelnen Formen liegen getrennt voneinander', 'und überlappen sich teilweise')
    elif damage == 'missing':
        root.remove(root[-1])
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='165', y='165', width='12', height='12', fill='#123456')
    elif damage == 'texture':
        obj = case['expected_objects'][1]
        x, y, w, h = obj['bbox']
        ET.SubElement(root, 'rect', x=str(x+w/2-5), y=str(y+h/2-5),
                      width='10', height='10', fill='white')
    else:
        from src.iCCModules.imageCompositeConverterSearchScheduler import drain
        pixels = render(case['svg'], case['width'], case['height'])
        contract = mixed.scene_contract(case['description'])
        objects = mixed.detect_instances(pixels, contract)
        ordered = mixed.observed_painter_order(pixels, objects)
        assert drain(mixed._fit_instances_steps(case['width'], case['height'], pixels=pixels,
            contract=contract, objects=[ordered[0], *reversed(ordered[1:])], render_fn=render,
            error_fn=lambda a, b: float(abs(a.astype(float)-b).mean()))) is None
        return
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_rejected_singleton_count_does_not_poison_another_contract():
    case = make_cases()[3]
    wrong = deepcopy(case)
    wrong['description'] = wrong['description'].replace('2 einzelne Formen', '1 einzelne Form')
    session = ImageSearch(SearchPolicy(seconds=20, max_seconds=20))
    assert fit(wrong, session)[1] is None
    assert any(session.structure_rejections.values())
    image, result = fit(case, session)
    assert_accepted(case, image, result)


def test_expired_budget_starts_no_mixed_topology_detection(monkeypatch):
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1))
    session.spent = 2
    monkeypatch.setattr(mixed, 'detect_instances', lambda *a, **k: pytest.fail('Expired budget'))
    assert fit(make_cases()[0], session)[1] is None


@pytest.mark.parametrize('gap,accepted', [(8., True), (2., False), (0., False), (-12., False)])
def test_singletons_require_separated_native_rims(gap, accepted):
    # AABB-separated fills alone cannot certify outlined separation. Check
    # the same native topology gate used during every registration step.
    def rectangle(x, y):
        return dict(kind='rectangle', geometry=np.array([x, y, 40., 40., 2.]))
    scene = [None, rectangle(20., 20.), rectangle(40., 40.), rectangle(80.+gap, 40.)]
    neighbours = {1: {2}, 2: {1}, 3: set()}
    assert mixed._overlap_groups_match(scene, neighbours, 1, isolated=1) == accepted
    assert not mixed._overlap_groups_match(scene, neighbours, 1)
