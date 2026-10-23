"""Scene edits must earn acceptance through real rendering and native gates."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterStructureSearch import edit_proposals, scene_key
from tests.test_residual_scene_search import fit
from tools.evaluate_layered_scene import check_objects, local_checks
from tools.evaluate_structure_operators import make_cases
from tools.run_plan_b_variations import measure_quality, render


def assert_accepted(case, image, result):
    assert result is not None
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert measure_quality(image, result['svg'])['satisfactory']
    assert all(q['passed'] for q in local_checks(image, result['svg'], case['expected_objects']))


def test_add_combines_incomplete_segmentations_through_real_registration():
    case = make_cases()[3]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    for threshold in (25, 16, 36):
        assert len(mixed.detect_instances(pixels, contract, residual_threshold=threshold)) != contract['count']
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert any(a.get('edits') == ['add'] and a['outcome'] == 'accepted' for a in result['scene_attempts'])


@pytest.mark.parametrize('operation', ['remove', 'replace'])
def test_edits_repair_detector_errors_without_changing_the_requested_scene(monkeypatch, operation):
    case = make_cases()[4]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    seed = mixed.detect_instances(pixels, contract)
    if operation == 'remove':
        seed.append(deepcopy(seed[1]))  # duplicate detector instance, not an extra raster object
    else:
        index = next(i for i, obj in enumerate(seed[1:], 1) if obj['kind'] == 'circle')
        seed[index]['kind'] = 'rectangle'
    original = deepcopy(seed)
    monkeypatch.setattr(mixed, 'detect_instances', lambda *a, **k: deepcopy(seed))
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert any(operation in a.get('edits', []) and a['outcome'] == 'accepted' for a in result['scene_attempts'])
    for before, after in zip(original, seed):
        np.testing.assert_array_equal(before['geometry'], after['geometry'])
        assert before['kind'] == after['kind']


@pytest.mark.parametrize('case', make_cases()[4:], ids=lambda case: case['case_id'])
def test_disjoint_native_child_classes_keep_object_region_and_pixel_gates(case):
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('damage', ['missing', 'extra', 'class', 'outside', 'overlap'])
def test_structure_edits_cannot_erase_contradictory_raster_objects(damage):
    case = deepcopy(make_cases()[4])
    root = ET.fromstring(case['svg'])
    if damage == 'missing':
        root.remove(root[-1])
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='90', y='120', width='12', height='10', fill='#123456')
    elif damage == 'class':
        obj = root[-1]
        x, y, w, h = map(float, (obj.get(k) for k in ('x', 'y', 'width', 'height')))
        root.remove(obj)
        ET.SubElement(root, 'circle', cx=str(x+w/2), cy=str(y+h/2), r=str(min(w, h)/2), fill='#3e5e40')
    elif damage == 'outside':
        root[-1].set('x', '167')
    else:
        root[-1].set('x', '80')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_rejections_survive_registration_reentry_but_are_bound_to_source_and_contract(monkeypatch):
    case = make_cases()[4]
    calls = []

    def reject(*args, **kwargs):
        calls.append(1)
        yield 1.
        return None

    monkeypatch.setattr(mixed, '_fit_instances_steps', reject)
    session = ImageSearch(SearchPolicy(seconds=60, max_seconds=60))
    assert fit(case, session)[1] is None
    first = len(calls)
    assert first > 0
    assert any(session.structure_rejections.values())
    assert fit(case, session)[1] is None
    assert len(calls) == first
    changed = deepcopy(case)
    changed['svg'] = changed['svg'].replace('#285472', '#285473')
    assert fit(changed, session)[1] is None
    assert len(calls) > first
    first = len(calls)
    changed = deepcopy(case)
    changed['description'] = changed['description'].replace('getrennt voneinander', 'getrennt nebeneinander')
    assert fit(changed, session)[1] is None
    assert len(calls) > first


def test_interrupted_registration_is_not_cached_as_negative_evidence(monkeypatch):
    case = make_cases()[4]
    now = [0.]
    session = ImageSearch(SearchPolicy(seconds=.1, max_seconds=.1), clock=lambda: now[0])

    def interrupted(*args, **kwargs):
        now[0] += .2
        yield 1.
        return None

    monkeypatch.setattr(mixed, '_fit_instances_steps', interrupted)
    assert fit(case, session)[1] is None
    assert not any(session.structure_rejections.values())


def test_agenda_is_bounded_and_canonical_under_child_permutations():
    case = make_cases()[6]
    contract = mixed.scene_contract(case['description'])
    pixels = render(case['svg'], case['width'], case['height'])
    seed = mixed.detect_instances(pixels, contract)
    assert scene_key(seed) == scene_key([seed[0], *reversed(seed[1:])])
    proposals = list(edit_proposals([seed, seed], contract['children'], max_states=4))
    assert len(proposals) <= 4
    keys = [scene_key(p['objects']) for p in proposals if p]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize('claim', [' Mit Text.', ' Eine zusätzliche Linie.',
                                  ' Die inneren Formen überlappen.', ' Ohne Farbverlauf.'])
def test_new_form_vocabulary_does_not_discard_unknown_assertions(claim):
    assert mixed.scene_contract(make_cases()[4]['description']+claim) is None
