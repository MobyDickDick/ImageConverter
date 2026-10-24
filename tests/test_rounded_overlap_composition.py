"""Rounding and painter order must retain every observed native instance."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_overlap_composition import make_cases
from tools.evaluate_layered_scene import check_objects
from tools.run_plan_b_variations import render


@pytest.mark.parametrize('case', make_cases(rounded=True), ids=lambda c: c['case_id'])
def test_rounded_overlaps_compose_with_both_axes_and_painter_orders(case):
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('damage', ['square', 'one_square', 'missing', 'extra', 'texture', 'hidden_side'])
def test_rounding_cannot_replace_observed_corners_or_inventory(damage):
    case = deepcopy(make_cases(rounded=True)[0])
    root = ET.fromstring(case['svg'])
    if damage in ('square', 'one_square'):
        for obj in list(root)[-2:] if damage == 'square' else [root[-1]]:
            obj.set('rx', '0')
    elif damage == 'missing':
        root.remove(root[-1])
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='90', y='140', width='12', height='12', rx='3', fill='black')
    elif damage == 'texture':
        obj = root[-1]
        ET.SubElement(root, 'rect', x=str(float(obj.get('x'))+10), y=str(float(obj.get('y'))+12),
                      width='12', height='7', fill='white')
    else:
        back, front = root[-2:]
        front.set('x', str(float(back.get('x'))-8))
        front.set('y', str(float(back.get('y'))+20))
        front.set('width', '75')
        front.set('height', '40')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


@pytest.mark.parametrize('claim', [' Die Formen haben keine Konturen.', ' Mit Text.',
    ' Die Rechtecke sind nicht gerundet.', ' Das kleinere Rechteck liegt vorne.'])
def test_unsupported_rounded_overlap_claims_fail_closed(claim):
    assert mixed.scene_contract(make_cases(rounded=True)[0]['description']+claim) is None


@pytest.mark.parametrize('damage', ['square', 'order'])
def test_independent_oracle_rejects_radius_and_layer_damage(damage):
    case = make_cases(rounded=True)[0]
    root = ET.fromstring(case['svg'])
    assert check_objects(case['svg'], case['expected_objects'])['passed']
    if damage == 'square':
        root[-1].set('rx', '0')
    else:
        back = root[-2]
        root.remove(back)
        root.append(back)
    assert not check_objects(ET.tostring(root, encoding='unicode'), case['expected_objects'])['passed']


def test_rounded_overlap_detection_expiry_starts_no_registration(monkeypatch):
    now = [0.]
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1), clock=lambda: now[0])
    detect = mixed.detect_instances

    def expire(*args, **kwargs):
        result = detect(*args, **kwargs)
        now[0] = 2.
        return result

    def forbidden(*args, **kwargs):
        pytest.fail('Expired rounded overlap started registration')
        yield

    monkeypatch.setattr(mixed, 'detect_instances', expire)
    monkeypatch.setattr(mixed, '_fit_instances_steps', forbidden)
    assert fit(make_cases(rounded=True)[0], session)[1] is None


def test_rejected_rounded_order_preserves_the_alternative_and_its_radii(monkeypatch):
    case = make_cases(rounded=True)[0]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    seed = mixed.detect_instances(pixels, contract)
    front = np.array(case['expected_objects'][2]['bbox'])
    children = sorted(seed[1:], key=lambda o: float(np.max(abs(o['geometry'][:4]-front))))
    monkeypatch.setattr(mixed, 'detect_instances', lambda *a, **k: deepcopy([seed[0], *children]))
    session = ImageSearch(SearchPolicy(seconds=5, max_seconds=5))
    image, result = fit(case, session)
    assert_accepted(case, image, result)
    assert any(a.get('edits') == ['reorder'] and a['outcome'] == 'accepted' for a in result['scene_attempts'])
    assert sum(len(v) for v in session.structure_rejections.values()) == 1
