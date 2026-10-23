"""Rounded residual children retain observed rims and the complete contract."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_rounded_composition import make_cases


@pytest.mark.parametrize('case', make_cases(outlined=True), ids=lambda c: c['case_id'])
def test_rounding_and_light_outlines_compose_in_the_existing_search(case):
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('damage', ['square', 'no_rims', 'parent_no_rim', 'child_no_rim',
                                    'parent_dark_rim', 'child_dark_rim', 'dark_rims', 'missing',
                                    'extra', 'texture', 'outside', 'count', 'layout'])
def test_rims_cannot_hide_wrong_shapes_objects_or_relations(damage):
    case = deepcopy(make_cases(outlined=True)[3])
    root = ET.fromstring(case['svg'])
    if damage == 'square':
        for rect in list(root)[3:]:
            rect.set('rx', '0')
    elif damage in ('no_rims', 'dark_rims'):
        for obj in list(root)[2:]:
            obj.set('stroke', 'none' if damage == 'no_rims' else '#303030')
    elif damage in ('parent_no_rim', 'child_no_rim', 'parent_dark_rim', 'child_dark_rim'):
        obj = root[-1] if damage.startswith('child_') else root[2]
        obj.set('stroke', '#303030' if damage.endswith('dark_rim') else 'none')
    elif damage == 'missing':
        root.remove(root[-1])
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='94', y='133', width='9', height='9', rx='2', fill='black')
    elif damage == 'texture':
        rect = root[-1]
        ET.SubElement(root, 'rect', x=str(float(rect.get('x'))+4), y=str(float(rect.get('y'))+8),
                      width='12', height='4', fill='white')
    elif damage == 'outside':
        root[-1].set('x', '183')
    elif damage == 'count':
        case['description'] = case['description'].replace('2 gefüllte', '3 gefüllte')
    else:
        case['description'] = case['description'].replace('nebeneinander', 'untereinander')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


@pytest.mark.parametrize('claim', [' Die Formen überlappen.', ' Mit Text.',
    ' Die Formen haben dunkle Konturen.', ' Die Kreise haben leicht gerundete Ecken.',
    ' Die Ecken sind nicht gerundet.', ' Ein weiterer Kreis.'])
def test_combined_contract_still_consumes_every_assertion(claim):
    assert mixed.scene_contract(make_cases(outlined=True)[3]['description']+claim) is None


def test_combination_retains_native_remove(monkeypatch):
    detect = mixed.detect_instances

    def duplicate(*args, **kwargs):
        objects = detect(*args, **kwargs)
        if objects:
            objects.append(deepcopy(objects[1]))
        return objects

    monkeypatch.setattr(mixed, 'detect_instances', duplicate)
    case = make_cases(outlined=True)[3]
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert any('remove' in a.get('edits', []) and a['outcome'] == 'accepted'
               for a in result['scene_attempts'])


def test_combined_detection_expiry_starts_no_registration(monkeypatch):
    detect = mixed.detect_instances
    now = [0.]
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1), clock=lambda: now[0])

    def expire(*args, **kwargs):
        objects = detect(*args, **kwargs)
        now[0] = 2.
        return objects

    def register(*args, **kwargs):
        pytest.fail('Expired detection must not start registration')
        yield

    monkeypatch.setattr(mixed, 'detect_instances', expire)
    monkeypatch.setattr(mixed, '_fit_instances_steps', register)
    assert fit(make_cases(outlined=True)[3], session)[1] is None


def test_unobservable_rims_are_rejected_instead_of_invented():
    case = deepcopy(make_cases(outlined=True)[3])
    root = ET.fromstring(case['svg'])
    # Collinear grey paints do not identify three independent coverages.
    for stop, color in zip(root[0][0], ('#dddddd', '#888888')):
        stop.set('stop-color', color)
    for rect in list(root)[3:]:
        rect.set('fill', '#444444')
        rect.set('stroke', '#eeeeee')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_rounding_stays_bound_to_rectangles_alongside_an_outlined_circle():
    case = deepcopy(make_cases(outlined=True)[3])
    root = ET.fromstring(case['svg'])
    ET.SubElement(root, 'circle', cx='105', cy='137', r='10.5', fill='#2a5471',
                  stroke='#f3f0ed', **{'stroke-width': '1.5'})
    case['description'] = case['description'].replace('Ein gefüllter Kreis', 'Zwei gefüllte Kreise')
    case['description'] = case['description'].replace('Der Kreis', 'Der äussere Kreis').replace(
        'Die Rechtecke liegen innerhalb des Kreises und getrennt nebeneinander',
        'Die inneren Formen liegen innerhalb des äusseren Kreises und getrennt voneinander')
    case['svg'] = ET.tostring(root, encoding='unicode')
    case['expected_objects'].append(dict(kind='circle', bbox=[93.75, 125.75, 22.5, 22.5],
                                         parent=0, stroke_width=1.5))
    image, result = fit(case)
    assert_accepted(case, image, result)
