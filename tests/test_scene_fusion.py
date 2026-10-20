"""Real raster fits and independent topology/damage controls for fused scenes."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

ET.register_namespace('', 'http://www.w3.org/2000/svg')

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterPrimitiveScene import fit_primitive_scene
from src.iCCModules.imageCompositeConverterSceneFusion import (
    compatible, fuse_candidates, fusion_contract, visible_candidates,
)
from tools.evaluate_fused_scene import make_cases
from tools.evaluate_layered_scene import check_objects, local_checks
from tools.run_plan_b_variations import render, measure_quality


def fit(case, description=None):
    image = render(case['svg'], case['width'], case['height'])
    original = image.copy()
    with image_search(ImageSearch(SearchPolicy(seconds=5, max_seconds=5))):
        result = fit_primitive_scene(case['width'], case['height'], description=description or case['description'],
            image=image, render_fn=render, error_fn=lambda a, b: float(np.mean(cv2.absdiff(a, b))))
    np.testing.assert_array_equal(image, original)
    return image, result


@pytest.mark.parametrize('case', make_cases(50874, 12), ids=lambda c:c['case_id'])
def test_partial_scenes_have_correct_objects_order_and_local_rasters(case):
    image, result = fit(case)
    assert result is not None
    assert result['source'] == 'primitive_fused_scene_v1'
    assert result['error'] <= result['initial_error']
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert all(q['passed'] for q in local_checks(image, result['svg'], case['expected_objects']))
    assert measure_quality(image, result['svg'])['satisfactory']
    assert any(d.startswith('visible_') for d in result['scene_detectors'])


@pytest.mark.parametrize('index', range(4))
def test_painter_order_comes_from_pixels_not_instance_size_or_palette(index):
    case = deepcopy(make_cases(7293, 4)[index])
    root = ET.fromstring(case['svg'])
    root[1], root[2] = root[2], root[1]
    case['svg'] = ET.tostring(root, encoding='unicode')
    case['expected_objects'][:2] = case['expected_objects'][1::-1]
    case['expected_objects'][0]['parent'] = None
    case['expected_objects'][1]['parent'] = 0
    _, result = fit(case)
    assert result is not None
    assert check_objects(result['svg'], case['expected_objects'])['passed']


@pytest.mark.parametrize('text', [
    'Zwei gefüllte Kreise überlappen nicht teilweise. Keine Beschriftung.',
    'Zwei gefüllte Kreise ohne teilweise Überdeckung. Keine Beschriftung.',
    'Zwei gefüllte Kreise überlappen vollständig. Keine Beschriftung.',
    'Zwei gefüllte Kreise überlappen teilweise und liegen getrennt nebeneinander.',
    'Zwei gefüllte Kreise überlappen teilweise und sind ineinander verschachtelt.',
    'Zwei gefüllte Kreise überlappen teilweise. Mit Schrift.',
    'Zwei gefüllte Kreise überlappen teilweise. Nicht ohne Text.',
    'Zwei gefüllte Kreise überlappen teilweise. Ein Objekt liegt im Vordergrund.',
    'Zwei gefüllte Kreise überlappen teilweise. Jede Form hat eine dunkle Kontur.',
    'Zwei gefüllte Kreise überlappen teilweise. Eine Form liegt getrennt.',
    'Vier gefüllte Kreise überlappen teilweise.',
    'Zwei gefüllte Kreise überlappen teilweise. Kein weißer Hintergrund.',
    'Zwei gefüllte Kreise überlappen teilweise. Schwarzer Hintergrund.',
])
def test_unsupported_or_contradictory_constraints_are_rejected(text):
    assert fusion_contract(text) is None


@pytest.mark.parametrize('background', ['Weißer Hintergrund.', 'Auf weißem Hintergrund.', 'Vor einem weißen Hintergrund.'])
def test_white_canvas_declaration_is_not_a_depth_order_request(background):
    case = make_cases()[0]
    _, result = fit(case, case['description']+' '+background)
    assert result is not None


def candidate(kind, box):
    return dict(kind=kind, geometry=[*box, 0.], fill=np.array([20, 100, 180]), stroke=np.array([20, 100, 180]))


@pytest.mark.parametrize('scene', [
    [candidate('circle', [20, 20, 40, 40]), candidate('circle', [52, 52, 40, 40])],
    [candidate('circle', [20, 20, 40, 40]), candidate('rectangle', [57, 57, 30, 30])],
])
def test_overlapping_boxes_do_not_prove_native_shape_overlap(scene):
    counts = {kind: sum(c['kind'] == kind for c in scene) for kind in ('circle', 'rectangle')}
    assert not compatible(scene, dict(counts=counts, overlap=True))


def test_a_claimed_separate_third_instance_must_actually_be_separate():
    scene = [candidate('circle', box) for box in ([20, 20, 40, 40], [45, 30, 40, 40], [30, 45, 40, 40])]
    assert not compatible(scene, dict(counts={'circle': 3, 'rectangle': 0}, overlap=True, separate_instance=True))


@pytest.mark.parametrize('scene', [
    [candidate('circle', [20, 20, 60, 60]), candidate('circle', [60, 40, 20, 20])],
    [candidate('rectangle', [20, 20, 60, 60]), candidate('rectangle', [60, 40, 20, 20])],
    [candidate('rectangle', [20, 20, 60, 60]), candidate('circle', [60, 40, 20, 20])],
])
def test_internal_tangency_is_containment_not_partial_overlap(scene):
    counts = {kind: sum(c['kind'] == kind for c in scene) for kind in ('circle', 'rectangle')}
    assert not compatible(scene, dict(counts=counts, overlap=True))


def test_fully_hidden_rectangle_side_is_not_invented():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="180" height="160"><rect width="180" height="160" fill="white"/><rect x="20" y="40" width="80" height="60" fill="#3169ac"/><rect x="70" y="20" width="70" height="100" fill="#d88032"/></svg>'
    pixels = render(svg, 180, 160)
    proposals = visible_candidates(pixels)
    assert not any(c['kind'] == 'rectangle' and c['geometry'][0] < 40 for c in proposals)
    _, result = fit(dict(svg=svg, width=180, height=160,
                        description='Zwei einfarbig gefüllte Rechtecke überlappen teilweise. Keine Beschriftung.'))
    assert result is None


def test_complete_and_visible_detectors_deduplicate_the_same_instance():
    case = make_cases()[0]
    groups = fuse_candidates(render(case['svg'], case['width'], case['height']))
    assert len(groups) == 2
    assert any(set(c['detectors']) >= {'complete_boundary', 'visible_arc'} for g in groups for c in g)


def test_extra_separate_instance_cannot_be_erased_by_a_good_large_pair():
    case = make_cases()[2]
    _, result = fit(case, 'Ein Kreis und ein Rechteck. Alle Formen sind einfarbig gefüllt. Die Formen überlappen teilweise. Keine Beschriftung.')
    assert result is None


@pytest.mark.parametrize('damage', ['delete', 'move', 'reorder', 'hidden_extra'])
def test_independent_oracle_rejects_corrupted_overlapping_vectors(damage):
    case = make_cases()[2]
    root = ET.fromstring(case['svg'])
    if damage == 'delete':
        root.remove(root[-1])
    elif damage == 'move':
        element = root[1]
        key = 'cx' if element.tag.endswith('circle') else 'x'
        element.set(key, str(float(element.get(key))+9))
    elif damage == 'reorder':
        root[1], root[2] = root[2], root[1]
    else:
        root.insert(1, ET.fromstring('<circle cx="90" cy="80" r="2" fill="red"/>'))
    assert not check_objects(ET.tostring(root, encoding='unicode'), case['expected_objects'])['passed']
