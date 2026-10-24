"""Overlap is an ordered structure, with raster evidence for every native side."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy
from src.iCCModules.imageCompositeConverterStructureSearch import edit_proposals, scene_key
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_layered_scene import check_objects
from tools.evaluate_overlap_composition import make_cases
from tools.run_plan_b_variations import render


@pytest.mark.parametrize('case', make_cases(), ids=lambda c: c['case_id'])
def test_overlap_composes_with_parent_gradient_and_both_painter_orders(case):
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('claim', [
    ' Die Formen sind getrennt.', ' Mit Text.', ' Die Rechtecke sind nicht gefüllt.',
    ' Die Rechtecke liegen außerhalb des Kreises.', ' Das kleinere Rechteck liegt vorne.',
    ' Ein weiterer Kreis.', ' Die Formen haben helle Konturen.',
])
def test_unsupported_or_conflicting_assertions_fail_closed(claim):
    assert mixed.scene_contract(make_cases()[0]['description']+claim) is None


@pytest.mark.parametrize('damage', ['missing', 'extra', 'same_color', 'texture', 'disjoint', 'nested', 'outside', 'circle', 'hidden_side'])
def test_overlap_cannot_erase_inventory_topology_or_observed_marks(damage):
    case = deepcopy(make_cases()[0])
    root = ET.fromstring(case['svg'])
    back, front = root[-2:]
    if damage == 'missing':
        root.remove(front)
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='130', y='123', width='12', height='13', fill='#233749')
    elif damage == 'same_color':
        front.set('fill', back.get('fill'))
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x=str(float(front.get('x'))+7), y=str(float(front.get('y'))+9),
                      width='15', height='8', fill='white')
    elif damage == 'disjoint':
        front.set('x', '127')
    elif damage == 'nested':
        front.set('x', str(float(back.get('x'))+8))
        front.set('y', str(float(back.get('y'))+8))
        front.set('width', '20')
        front.set('height', '20')
    elif damage == 'outside':
        front.set('x', '172')
    elif damage == 'hidden_side':
        front.set('x', str(float(back.get('x'))-8))
        front.set('y', str(float(back.get('y'))+20))
        front.set('width', '75')
        front.set('height', '40')
    else:
        root.remove(front)
        ET.SubElement(root, 'circle', cx='112', cy='102', r='24', fill=front.get('fill'))
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_painter_order_changes_structure_identity_and_the_bounded_edit_agenda():
    case = make_cases()[0]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    seed = mixed.detect_instances(pixels, contract)
    reversed_seed = [seed[0], *reversed(seed[1:])]
    assert scene_key(seed) == scene_key(reversed_seed)
    assert scene_key(seed, ordered=True) != scene_key(reversed_seed, ordered=True)
    stats = {}
    proposals = [p for p in edit_proposals([seed], contract['children'], ordered=True, stats=stats) if p]
    assert any(p['edits'] == ['reorder'] and p['complete'] for p in proposals)
    assert stats['states'] <= 96


def test_independent_oracle_rejects_swapped_native_layers():
    case = make_cases()[0]
    root = ET.fromstring(case['svg'])
    assert check_objects(ET.tostring(root, encoding='unicode'), case['expected_objects'])['passed']
    back = root[-2]
    root.remove(back)
    root.append(back)
    assert not check_objects(ET.tostring(root, encoding='unicode'), case['expected_objects'])['passed']


def test_overlap_deadline_after_detection_starts_no_registration(monkeypatch):
    now = [0.]
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1), clock=lambda: now[0])
    detect = mixed.detect_instances

    def expire(*args, **kwargs):
        result = detect(*args, **kwargs)
        now[0] = 2.
        return result

    def forbidden(*args, **kwargs):
        pytest.fail('Expired overlap started registration')
        yield

    monkeypatch.setattr(mixed, 'detect_instances', expire)
    monkeypatch.setattr(mixed, '_fit_instances_steps', forbidden)
    assert fit(make_cases()[0], session)[1] is None


def test_ordered_edits_preserve_observed_instances():
    case = make_cases()[0]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    seed = mixed.detect_instances(pixels, contract)
    original = deepcopy(seed)
    list(edit_proposals([seed], contract['children'], ordered=True))
    for a, b in zip(seed, original):
        np.testing.assert_array_equal(a['geometry'], b['geometry'])
        np.testing.assert_array_equal(a['colors'], b['colors'])


@pytest.mark.parametrize('change', ['count', 'circles'])
def test_unimplemented_overlap_combinations_remain_explicitly_unsupported(change):
    description = make_cases()[0]['description']
    if change == 'count':
        description = description.replace('zwei gefüllte', 'drei gefüllte')
    else:
        description = description.replace('Ein gefüllter Kreis', 'Zwei gefüllte Kreise').replace(
            'Der Kreis', 'Der äussere Kreis').replace(
            'Die Rechtecke liegen innerhalb des Kreises',
            'Die inneren Formen liegen innerhalb des äusseren Kreises')
    assert mixed.scene_contract(description) is None


def test_rejected_painter_order_does_not_poison_the_other_order(monkeypatch):
    case = make_cases()[0]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    seed = mixed.detect_instances(pixels, contract)
    # Force the visible front rectangle to be drawn first in every initial
    # segmentation. Only an ordered edit can repair this proposal.
    front = np.array(case['expected_objects'][2]['bbox'])
    children = sorted(seed[1:], key=lambda o: float(np.max(abs(o['geometry'][:4]-front))))
    monkeypatch.setattr(mixed, 'detect_instances', lambda *a, **k: deepcopy([seed[0], *children]))
    session = ImageSearch(SearchPolicy(seconds=5, max_seconds=5))
    image, result = fit(case, session)
    assert_accepted(case, image, result)
    assert any(a.get('edits') == ['reorder'] and a['outcome'] == 'accepted' for a in result['scene_attempts'])
    assert any(a['outcome'] == 'quality_or_geometry_rejected' for a in result['scene_attempts'])
    assert sum(len(v) for v in session.structure_rejections.values()) == 1
