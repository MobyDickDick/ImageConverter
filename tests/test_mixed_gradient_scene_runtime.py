"""Independent objects, raster damage, conservative semantics and scene dispatch."""
from copy import deepcopy
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterMixedGradientScene import scene_contract, _flat_edge
from src.iCCModules.imageCompositeConverterPrimitiveScene import fit_primitive_scene
from tools.evaluate_mixed_gradient_scene import make_cases
from tools.evaluate_layered_scene import check_objects, local_checks
from tools.run_plan_b_variations import render, measure_quality


def fit(case):
    image = render(case['svg'], case['width'], case['height'])
    before = image.copy()
    result = fit_primitive_scene(case['width'], case['height'], image=image,
        description=case['description'], render_fn=render,
        error_fn=lambda a, b: float(abs(a.astype(float)-b).mean()))
    np.testing.assert_array_equal(before, image)
    return image, result


@pytest.mark.parametrize('case', make_cases(382146, 12), ids=lambda c: c['case_id'])
def test_independent_objects_and_regions(case):
    image, result = fit(case)
    assert result is not None
    assert result['source'] == 'primitive_mixed_gradient_scene_v1'
    assert result['error'] <= result['initial_error']
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert measure_quality(image, result['svg'])['satisfactory']
    assert all(q['passed'] for q in local_checks(image, result['svg'], case['expected_objects']))


@pytest.mark.parametrize('addition', [
    ' Mit Text.', ' Nicht ohne Text.', ' Ein weiterer Kreis.', ' Eine zusätzliche Linie.',
    ' Die Rechtecke liegen außerhalb des Kreises.', ' Die Formen überlappen.',
    ' Die Formen haben dunkle Konturen.', ' Mit radialem Verlauf.',
    ' Der Kreis hat einen horizontalen Farbverlauf.', ' Das Rechteck ist nicht gefüllt.',
])
def test_unknown_and_contradictory_claims_reject(addition):
    assert scene_contract(make_cases()[1]['description']+addition) is None


@pytest.mark.parametrize('damage', ['missing', 'extra', 'axis', 'flat', 'textured'])
def test_wrong_raster_cannot_be_a_complete_scene(damage):
    case = deepcopy(make_cases()[3])
    root = ET.fromstring(case['svg'])
    if damage == 'missing':
        root.remove(root[-1])
    elif damage == 'extra':
        ET.SubElement(root, '{http://www.w3.org/2000/svg}rect', x='85', y='110', width='9', height='9', fill='black')
    elif damage == 'axis':
        root[0][0].set('x2', '100%')
        root[0][0].set('y2', '0%')
    elif damage == 'flat':
        root[0][0][1].set('stop-color', root[0][0][0].get('stop-color'))
    else:
        ET.SubElement(root, '{http://www.w3.org/2000/svg}rect', x='63', y='87', width='16', height='8', fill='white')
    case['svg'] = ET.tostring(root, encoding='unicode')
    _, result = fit(case)
    assert result is None


def test_removing_a_small_rectangle_fails_the_independent_oracle():
    case = make_cases()[3]
    image = render(case['svg'], case['width'], case['height'])
    root = ET.fromstring(case['svg'])
    root.remove(root[-1])
    svg = ET.tostring(root, encoding='unicode')
    assert not check_objects(svg, case['expected_objects'])['passed']
    assert not all(q['passed'] for q in local_checks(image, svg, case['expected_objects']))


def test_a_disconnected_dark_shadow_does_not_expand_the_flat_interior():
    profile = np.full((14, 3), 220.)
    profile[4:8] = 40.
    profile[9] = 40.  # shadow beyond an intact light rim
    assert _flat_edge(profile, np.full(3, 40.), np.full(3, 220.), 4, 10) == (4., 8.)


@pytest.mark.parametrize('index', [0, 1])
def test_originals_after_the_failed_transfer_are_development_regressions(index):
    root = Path(__file__).resolve().parents[1]
    case = json.loads((root/'config/mixed_gradient_scene_families.json').read_text(encoding='utf-8'))['cases'][index]
    image = cv2.imread(str(root/'artifacts/images_to_convert'/case['file']))
    height, width = image.shape[:2]
    result = fit_primitive_scene(width, height, image=image, description=case['description'],
        render_fn=render, error_fn=lambda a, b: float(abs(a.astype(float)-b).mean()))
    assert result is not None
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert measure_quality(image, result['svg'])['satisfactory']
    assert all(q['passed'] for q in local_checks(image, result['svg'], case['expected_objects']))
