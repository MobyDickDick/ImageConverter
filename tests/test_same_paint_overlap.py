"""Equal fill is not an instance identity or observable depth evidence."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterSearchScheduler import drain
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_overlap_composition import make_cases, make_variation_cases
from tools.evaluate_mixed_overlap import make_cases as mixed_cases
from tools.run_plan_b_variations import render


@pytest.mark.parametrize('rounded', [False, True])
@pytest.mark.parametrize('index', [0, 1, 2, 3, 5, 7])
def test_same_paint_outlined_rectangles_retain_instances_and_order(rounded, index):
    case = make_cases(648217, rounded=rounded, outlined=True, same_fill=True)[index]
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('damage', ['missing', 'count', 'no_rim', 'dark_rim', 'texture', 'square'])
def test_equal_paint_does_not_waive_native_or_raster_evidence(damage):
    case = deepcopy(make_cases(648217, rounded=True, outlined=True, same_fill=True)[0])
    root = ET.fromstring(case['svg'])
    if damage == 'missing':
        root.remove(root[-1])
    elif damage == 'count':
        case['description'] = case['description'].replace('zwei', 'drei')
    elif damage in ('no_rim', 'dark_rim'):
        root[-1].set('stroke', 'none' if damage == 'no_rim' else '#222222')
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x='75', y='70', width='10', height='10', fill='white')
    else:
        root[-1].set('rx', '0')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_unoutlined_same_paint_union_does_not_supply_hidden_instance_boundaries():
    assert fit(make_cases(648217, same_fill=True)[0])[1] is None


def test_shifted_rounding_without_two_clean_corner_observations_is_rejected():
    case = make_variation_cases(372851, rounded=True, outlined=True, same_fill=True)[4]
    assert fit(case)[1] is None


@pytest.mark.parametrize('rounded', [False, True])
@pytest.mark.parametrize('index', range(4))
def test_same_paint_circle_and_rectangle_share_the_observed_rim_order(rounded, index):
    # This includes the previously unsupported same_color circle-rim control.
    case = mixed_cases(731921, children=2, rounded=rounded, outlined=True)[index]
    root = ET.fromstring(case['svg'])
    root[-1].set('fill', root[-2].get('fill'))
    case['svg'] = ET.tostring(root, encoding='unicode')
    image, result = fit(case)
    if index >= 2:
        # With the circle in front, adjoining equal paint contaminates the
        # outer-rim reconstruction. Keep this known limitation in the cohort;
        # do not infer its hidden boundary or weaken circle evidence.
        assert result is None
        return
    assert_accepted(case, image, result)
    accepted = next(a for a in result['scene_attempts'] if a['outcome'] == 'accepted')
    assert accepted['painter_order'] == 'observed_depth'


def test_registration_rejects_reversed_equal_paint_layers_even_when_flat_fill_matches():
    case = make_cases(648217, rounded=True, outlined=True, same_fill=True)[1]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    objects = mixed.detect_instances(pixels, contract, split_components=True)
    ordered = mixed.observed_painter_order(pixels, objects)
    assert ordered is not None
    wrong = [ordered[0], *reversed(ordered[1:])]
    with image_search(ImageSearch(SearchPolicy(seconds=5, max_seconds=5))):
        result = drain(mixed._fit_instances_steps(case['width'], case['height'], pixels=pixels,
            contract=contract, objects=wrong, render_fn=render, error_fn=lambda *args: 0.))
    assert result is None
