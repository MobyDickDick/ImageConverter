"""Observed outlines, mixed topology, depth constraints and independent damage controls."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterPrimitiveScene import fit_primitive_scene
from src.iCCModules.imageCompositeConverterSceneVisibility import visibility_contract
from tools.evaluate_visibility_scene import make_cases
from tools.evaluate_layered_scene import check_objects, local_checks
from tools.run_plan_b_variations import render, measure_quality

ET.register_namespace('', 'http://www.w3.org/2000/svg')


def fit(case, description=None):
    image = render(case['svg'], case['width'], case['height'])
    original = image.copy()
    with image_search(ImageSearch(SearchPolicy(seconds=5, max_seconds=5))):
        result = fit_primitive_scene(case['width'], case['height'], image=image,
            description=case['description'] if description is None else description, render_fn=render,
            error_fn=lambda a, b: float(np.mean(cv2.absdiff(a, b))))
    np.testing.assert_array_equal(image, original)
    return image, result


@pytest.mark.parametrize('case', make_cases(53729, 12), ids=lambda c: c['case_id'])
def test_outlined_mixed_topology_and_depth_have_independent_native_evidence(case):
    image, result = fit(case)
    assert result is not None
    assert result['source'] == 'primitive_visibility_scene_v1'
    assert result['error'] <= result['initial_error']
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert all(q['passed'] for q in local_checks(image, result['svg'], case['expected_objects']))
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('i', range(4))
def test_explicit_depth_contradicting_the_raster_is_not_silently_ignored(i):
    case = make_cases(32976, 6)[i if i < 2 else i+1]
    wrong = case['description'].replace('kleinere Form liegt vor der größeren', 'größere Form liegt vor der kleineren')
    _, result = fit(case, wrong)
    assert result is None


@pytest.mark.parametrize('text', [
    'Zwei gefüllte Kreise überlappen teilweise. Die Form liegt vorne.',
    'Zwei gefüllte Kreise überlappen teilweise. Jede Form hat keine dunkle Kontur.',
    'Zwei gefüllte Kreise überlappen teilweise. Die kleinere Form liegt nicht vor der größeren Form.',
    'Zwei gefüllte Kreise überlappen teilweise. Die kleinere Form liegt vor der größeren Form. Die größere Form liegt vor der kleineren Form.',
    'Zwei gefüllte Kreise überlappen teilweise. Die kleinste Form liegt innerhalb der größten Form.',
    'Zwei gefüllte Kreise überlappen teilweise. Mit Text.',
    'Zwei gefüllte Kreise überlappen teilweise. Schwarzer Hintergrund.',
    'Zwei gefüllte Kreise überlappen teilweise. Die mittlere Form liegt hinter der rechten Form.',
])
def test_unmodelled_ambiguous_or_contradictory_language_is_rejected(text):
    assert visibility_contract(text) is None


@pytest.mark.parametrize('damage', ['stroke', 'order', 'child', 'hidden_extra'])
def test_independent_oracle_rejects_incomplete_visibility_reconstruction(damage):
    case = deepcopy(make_cases(53729, 3)[2])
    root = ET.fromstring(case['svg'])
    if damage == 'stroke':
        root[1].set('stroke', 'none')
    elif damage == 'order':
        root[1], root[2] = root[2], root[1]
    elif damage == 'child':
        root.remove(root[-1])
    else:
        root.insert(1, ET.fromstring('<circle cx="90" cy="80" r="2" fill="red"/>'))
    assert not check_objects(ET.tostring(root, encoding='unicode'), case['expected_objects'])['passed']


def test_fully_occluded_outlined_rectangle_side_stays_unknown():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="180" height="160"><rect width="180" height="160" fill="white"/><rect x="20" y="40" width="80" height="60" fill="#3169ac" stroke="#303030" stroke-width="3"/><rect x="70" y="20" width="70" height="100" fill="#d88032" stroke="#303030" stroke-width="3"/></svg>'
    _, result = fit(dict(svg=svg, width=180, height=160,
        description='Zwei einfarbig gefüllte Rechtecke überlappen teilweise. Jede Form hat eine dunkle Kontur. Keine Beschriftung.'))
    assert result is None


def test_equal_size_instances_cannot_resolve_a_relative_size_depth_reference():
    case = make_cases(53729, 1)[0]
    root = ET.fromstring(case['svg'])
    root[2].set('r', root[1].get('r'))
    case['svg'] = ET.tostring(root, encoding='unicode')
    _, result = fit(case)
    assert result is None
