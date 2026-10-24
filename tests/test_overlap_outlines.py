"""Rims, visible extents and painter order compose under one raster contract."""
from copy import deepcopy
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_layered_scene import check_objects
from tools.evaluate_overlap_composition import make_cases
from tools.run_plan_b_variations import render


@pytest.mark.parametrize('rounded', [False, True])
@pytest.mark.parametrize('index', range(12))
def test_visible_outlines_compose_with_overlap_and_rounding(rounded, index):
    case = make_cases(rounded=rounded, outlined=True)[index]
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('rounded', [False, True])
@pytest.mark.parametrize('damage', ['parent_no_rim', 'back_no_rim', 'front_no_rim',
    'parent_dark_rim', 'back_dark_rim', 'front_dark_rim', 'missing', 'extra',
    'texture', 'same_color', 'hidden_side', 'outside'])
def test_rims_cannot_replace_inventory_visible_sides_or_light_paint(rounded, damage):
    case = deepcopy(make_cases(rounded=rounded, outlined=True)[0])
    root = ET.fromstring(case['svg'])
    back, front = root[-2:]
    if damage.endswith('_rim'):
        obj = {'parent': root[2], 'back': back, 'front': front}[damage.split('_')[0]]
        obj.set('stroke', 'none' if '_no_' in damage else '#303030')
    elif damage == 'missing':
        root.remove(front)
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='90', y='140', width='12', height='12', fill='black')
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x=str(float(front.get('x'))+10),
                      y=str(float(front.get('y'))+12), width='12', height='7', fill='white')
    elif damage == 'same_color':
        front.set('fill', back.get('fill'))
    elif damage == 'hidden_side':
        front.set('x', str(float(back.get('x'))-8))
        front.set('y', str(float(back.get('y'))+20))
        front.set('width', '75')
        front.set('height', '40')
    else:
        front.set('x', '175')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


@pytest.mark.parametrize('claim', [' Mit Text.', ' Die Formen haben dunkle Konturen.',
    ' Die Rechtecke sind nicht gefüllt.', ' Die Formen sind getrennt.',
    ' Ein weiterer Kreis.', ' Das kleinere Rechteck liegt vorne.'])
def test_unknown_and_conflicting_assertions_are_still_rejected(claim):
    assert mixed.scene_contract(make_cases(outlined=True)[0]['description']+claim) is None


@pytest.mark.parametrize('rounded', [False, True])
def test_a_newly_supported_outline_claim_still_needs_observed_rims(rounded):
    case = deepcopy(make_cases(rounded=rounded)[0])
    case['description'] += ' Die Formen haben helle Konturen.'
    assert mixed.scene_contract(case['description']) is not None
    assert fit(case)[1] is None


@pytest.mark.parametrize('which', [-1, -2])
def test_each_rounded_child_needs_its_own_corner_evidence(which):
    case = deepcopy(make_cases(rounded=True, outlined=True)[0])
    root = ET.fromstring(case['svg'])
    root[which].set('rx', '0')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_shifted_thin_rims_do_not_average_away_the_exposed_corner_paint():
    base = Path(__file__).resolve().parents[1]/'artifacts/evaluation/overlap_outlines_v1/plan_b'
    case = json.loads((base/'manifest.json').read_text(encoding='utf-8'))[8]
    case['svg'] = (base/'references'/f"{case['case_id']}.svg").read_text(encoding='utf-8')
    image, result = fit(case)
    assert_accepted(case, image, result)


def test_collinear_parent_fill_and_rim_paints_do_not_identify_separate_coverages():
    case = deepcopy(make_cases(rounded=True, outlined=True)[0])
    root = ET.fromstring(case['svg'])
    for stop, color in zip(root[0][0], ('#dddddd', '#888888')):
        stop.set('stop-color', color)
    for obj in list(root)[2:]:
        obj.set('stroke', '#eeeeee')
    root[-2].set('fill', '#444444')
    root[-1].set('fill', '#666666')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_reorder_preserves_observed_rims_and_radii(monkeypatch):
    case = make_cases(rounded=True, outlined=True)[0]
    pixels = render(case['svg'], case['width'], case['height'])
    seed = mixed.detect_instances(pixels, mixed.scene_contract(case['description']))
    front = np.array(case['expected_objects'][2]['bbox'])
    children = sorted(seed[1:], key=lambda o: float(np.max(abs(o['geometry'][:4]-front))))
    monkeypatch.setattr(mixed, 'detect_instances', lambda *a, **k: deepcopy([seed[0], *children]))
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert any(a.get('edits') == ['reorder'] and a['outcome'] == 'accepted'
               for a in result['scene_attempts'])


def test_expired_detection_starts_no_registration(monkeypatch):
    now = [0.]
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1), clock=lambda: now[0])
    detect = mixed.detect_instances

    def expire(*args, **kwargs):
        objects = detect(*args, **kwargs)
        now[0] = 2.
        return objects

    def forbidden(*args, **kwargs):
        pytest.fail('Expired detection started registration')
        yield

    monkeypatch.setattr(mixed, 'detect_instances', expire)
    monkeypatch.setattr(mixed, '_fit_instances_steps', forbidden)
    assert fit(make_cases(rounded=True, outlined=True)[0], session)[1] is None


@pytest.mark.parametrize('damage', ['rim', 'radius', 'order'])
def test_independent_oracle_rejects_native_damage(damage):
    case = make_cases(rounded=True, outlined=True)[0]
    root = ET.fromstring(case['svg'])
    assert check_objects(case['svg'], case['expected_objects'])['passed']
    if damage == 'rim':
        root[-1].set('stroke', 'none')
    elif damage == 'radius':
        root[-1].set('rx', '0')
    else:
        back = root[-2]
        root.remove(back)
        root.append(back)
    assert not check_objects(ET.tostring(root, encoding='unicode'), case['expected_objects'])['passed']
