"""Split proposals must satisfy the same native, regional and raster gates."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_component_splits import make_cases
from tools.evaluate_structure_operators import make_cases as edit_cases
from tools.run_plan_b_variations import make_variations
from tools.run_plan_b_variations import render


@pytest.mark.parametrize('case', make_cases()+edit_cases()[:3], ids=lambda c: c['case_id'])
def test_subpixel_seams_recover_native_objects_through_real_registration(case):
    image, result = fit(case)
    assert_accepted(case, image, result)
    if case['case_id'].startswith('edit_') or case['case_id'] in {'split_00', 'split_02'}:
        assert any(a['operator'] == 'split' and a['outcome'] == 'accepted'
                   for a in result['scene_attempts'])


@pytest.mark.parametrize('damage', ['solid_bar', 'extra', 'texture', 'count', 'layout'])
def test_split_does_not_invent_gaps_or_erase_contradictory_content(damage):
    case = deepcopy(make_cases()[0])
    root = ET.fromstring(case['svg'])
    first, second = root[-2:]
    if damage == 'solid_bar':
        right = float(second.get('x'))+float(second.get('width'))
        first.set('width', str(right-float(first.get('x'))))
        root.remove(second)
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='98', y='133', width='10', height='10', fill='#123456')
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x=first.get('x'), y='94', width=first.get('width'),
                      height='3', fill='white')
    elif damage == 'count':
        case['description'] = case['description'].replace('2 gefüllte', '3 gefüllte')
    else:
        case['description'] = case['description'].replace('nebeneinander', 'untereinander')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_split_detection_consumes_shared_deadline_without_starting_a_fit(monkeypatch):
    # Permit initial segmentations, then expire on the split detector entry.
    original = mixed.detect_instances
    now = [0.]
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1), clock=lambda: now[0])
    split_calls = []

    def detect(*args, **kwargs):
        if kwargs.get('split_components'):
            split_calls.append(1)
            now[0] = 2.
        return original(*args, **kwargs)

    monkeypatch.setattr(mixed, 'detect_instances', detect)
    assert fit(make_cases()[0], session)[1] is None
    assert split_calls == [1]
    assert not any(session.structure_rejections.values())


def test_split_and_remove_compose_without_waiving_native_or_raster_gates(monkeypatch):
    original = mixed.detect_instances
    events = []

    def detect(*args, **kwargs):
        objects = original(*args, **kwargs)
        if kwargs.get('split_components') and objects:
            objects.append(deepcopy(objects[1]))
        return objects

    monkeypatch.setattr(mixed, 'detect_instances', detect)
    monkeypatch.setattr(mixed, 'progress', lambda *args, **kwargs: events.append(kwargs))
    case = make_cases()[0]
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert any(a['operator'] == 'split_edit' and 'remove' in a['edits']
               and a['outcome'] == 'accepted' for a in result['scene_attempts'])
    final = next(e for e in events if e.get('event') == 'structure_search_finished')
    assert final['outcome'] == 'accepted'
    assert 1 < final['states'] <= 96


def test_split_reentry_reuses_image_bound_negative_evidence(monkeypatch):
    calls = []

    def reject(*args, **kwargs):
        calls.append(1)
        yield 1.
        return None

    monkeypatch.setattr(mixed, '_fit_instances_steps', reject)
    session = ImageSearch(SearchPolicy(seconds=60, max_seconds=60))
    assert fit(make_cases()[0], session)[1] is None
    first = len(calls)
    assert first > 0
    assert fit(make_cases()[0], session)[1] is None
    assert len(calls) == first


@pytest.mark.parametrize('index', range(4))
def test_scaled_and_translated_plan_b_inputs_keep_the_full_scene_contract(index):
    source = make_cases()[0]
    case = make_variations(source['svg'], source['description'], 731902)[index]
    scale = case['variation']['scale']
    dx, dy = case['variation']['relative_x'], case['variation']['relative_y']
    w, h = source['width'], source['height']
    case['expected_objects'] = [dict(obj, bbox=[
        w/2+scale*(obj['bbox'][0]-w/2)+dx*w,
        h/2+scale*(obj['bbox'][1]-h/2)+dy*h,
        scale*obj['bbox'][2], scale*obj['bbox'][3]]) for obj in source['expected_objects']]
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('claim', [' Die linke Form ist kleiner.', ' Mit Text.',
                                  ' Die Formen überlappen.', ' Nicht ohne Kontur.'])
def test_motif_qualifier_cannot_hide_object_or_relation_assertions(claim):
    source = make_cases()[0]
    description = make_variations(source['svg'], source['description'], 731902)[0]['description']
    assert mixed.scene_contract(description+claim) is None


def test_noisy_segmentation_stops_retaining_full_image_masks_at_the_instance_limit(monkeypatch):
    case = make_cases()[0]
    root = ET.fromstring(case['svg'])
    for obj in list(root)[-2:]:
        root.remove(obj)
    for row in range(5):
        for column in range(5):
            ET.SubElement(root, 'rect', x=str(70+column*14), y=str(65+row*14),
                          width='7', height='7', fill='#123456')
    pixels = render(ET.tostring(root, encoding='unicode'), case['width'], case['height'])
    observed = []

    def keep_component(pixels, predicted, component):
        observed.append(np.count_nonzero(component))
        return [component]

    monkeypatch.setattr(mixed, '_split_flat_component', keep_component)
    assert mixed.detect_instances(pixels, mixed.scene_contract(case['description']),
                                  split_components=True) is None
    assert len(observed) == 17
