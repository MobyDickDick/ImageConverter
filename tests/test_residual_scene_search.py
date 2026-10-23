"""Real rendering checks for alternative segmentations and generic layouts."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterMixedGradientScene import scene_contract
from src.iCCModules.imageCompositeConverterPrimitiveScene import fit_primitive_scene
from tools.evaluate_layered_scene import check_objects, local_checks
from tools.evaluate_residual_scene import make_cases
from tools.run_plan_b_variations import measure_quality, render


def fit(case, session=None):
    image = render(case['svg'], case['width'], case['height'])
    original = image.copy()
    with image_search(session or ImageSearch(SearchPolicy(seconds=5, max_seconds=5))):
        result = fit_primitive_scene(case['width'], case['height'], description=case['description'],
            image=image, render_fn=render, error_fn=lambda a, b: float(abs(a.astype(float)-b).mean()))
    np.testing.assert_array_equal(image, original)
    return image, result


@pytest.mark.parametrize('case', make_cases(), ids=lambda c: c['case_id'])
def test_generic_layouts_and_alternative_segmentations(case):
    image, result = fit(case)
    if case['case_id'] in {'residual_06', 'residual_07'}:
        # Detection can now propose these objects, but the unchanged local
        # edge gate cannot certify them. Retain these negative observations.
        assert result is None
        return
    assert result is not None
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert measure_quality(image, result['svg'])['satisfactory']
    assert all(q['passed'] for q in local_checks(image, result['svg'], case['expected_objects']))
    assert result['scene_attempts'][-1]['outcome'] == 'accepted'
    if case['case_id'] == 'residual_08':
        assert result['scene_attempts'][0]['outcome'] != 'accepted'
        assert result['scene_hypotheses'] >= 2


@pytest.mark.parametrize('damage', ['missing', 'extra', 'texture', 'axis'])
def test_alternative_proposals_do_not_waive_the_object_or_paint_contract(damage):
    case = deepcopy(make_cases()[3])
    root = ET.fromstring(case['svg'])
    if damage == 'missing':
        root.remove(root[-1])
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='90', y='120', width='12', height='10', fill='#123456')
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x='77', y='67', width='7', height='12', fill='white')
    else:
        root[0][0].set('x2', '0%')
        root[0][0].set('y2', '100%')
        case['description'] = case['description'].replace('vertikalen', 'horizontalen')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


@pytest.mark.parametrize('claim', [' Mit Text.', ' Nicht ohne Text.', ' Die Formen überlappen.',
    ' Eine zusätzliche Linie.', ' Die Rechtecke sind nicht gefüllt.', ' Ohne Farbverlauf.',
    ' Die Rechtecke liegen außerhalb des Kreises.'])
def test_unknown_claims_are_not_erased_by_fallback(claim):
    assert scene_contract(make_cases()[3]['description']+claim) is None


def test_an_exhausted_image_budget_does_not_start_another_hypothesis(monkeypatch):
    from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1))
    session.spent = 2
    monkeypatch.setattr(mixed, 'detect_instances', lambda *a, **k: pytest.fail('Budget already exhausted'))
    assert fit(make_cases()[0], session)[1] is None


def test_horizontal_language_cannot_accept_a_vertical_group():
    case = deepcopy(make_cases()[0])
    case['description'] = case['description'].replace('untereinander', 'nebeneinander')
    assert fit(case)[1] is None


@pytest.mark.parametrize('adjective', ['kleines', 'helles', 'dunkles', 'unbeschriftetes'])
def test_existing_shape_adjectives_remain_supported(adjective):
    description = make_cases()[7]['description'].replace('ein gefülltes Rechteck', f'ein {adjective} gefülltes Rechteck')
    assert scene_contract(description) is not None
