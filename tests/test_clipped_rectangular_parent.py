"""Cropped parent observations must constrain geometry before registration."""
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterPrimitiveScene import fit_primitive_scene
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_clipped_rectangular_parent import make_cases, parent_regions
from tools.evaluate_layered_scene import check_objects
from tools.evaluate_svg_text_baseline import render_librsvg
from tools.run_plan_b_variations import render

pytestmark = pytest.mark.per_test_timeout(30, fail_on_timeout=True)


def fit_independent(case, session=None):
    image = render_librsvg(case['svg'], case['width'], case['height'])
    original = image.copy()
    with image_search(session or ImageSearch(SearchPolicy(seconds=5, max_seconds=5))):
        result = fit_primitive_scene(case['width'], case['height'], description=case['description'],
            image=image, render_fn=render, error_fn=lambda a, b: float(abs(a.astype(float)-b).mean()))
    np.testing.assert_array_equal(image, original)
    return image, result


@pytest.mark.parametrize('index', range(12))
def test_clipped_parent_keeps_native_bounds_radius_inventory_and_relations(index):
    case = make_cases()[index]
    image, result = fit_independent(case)
    assert_accepted(case, image, result)
    assert sum(a['operator'] in ('edit', 'split_edit', 'group_islands')
               for a in result['scene_attempts']) <= 96


@pytest.mark.parametrize('index', [0, 1, 2, 3])
def test_a_sharp_parent_with_an_entirely_missing_side_is_unobservable(index):
    case = make_cases()[index]
    root = ET.fromstring(case['svg'])
    root[2].attrib.pop('rx', None)
    case['svg'] = ET.tostring(root, encoding='unicode')
    case['description'] = case['description'].replace(' Das äussere Rechteck hat gerundete Ecken.', '')
    assert fit_independent(case)[1] is None


@pytest.mark.parametrize('damage', ['missing_child', 'extra_child', 'wrong_axis', 'dark_rim', 'missing_rim', 'texture'])
def test_clipping_preserves_negative_object_paint_and_local_pixel_evidence(damage):
    case = make_cases()[1]
    root = ET.fromstring(case['svg'])
    if damage == 'missing_child':
        root.remove(root[-1])
    elif damage == 'extra_child':
        ET.SubElement(root, 'rect', x='170', y='165', width='13', height='12', fill='#123456')
    elif damage == 'wrong_axis':
        case['description'] = case['description'].replace('vertikalen', 'horizontalen')
    elif damage in ('dark_rim', 'missing_rim'):
        root[2].set('stroke', '#202020' if damage == 'dark_rim' else 'none')
    else:
        ET.SubElement(root, 'rect', x='170', y='165', width='13', height='12', fill='white')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit_independent(case)[1] is None


def test_expired_budget_starts_no_boundary_measurement(monkeypatch):
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1))
    session.spent = 2
    monkeypatch.setattr(mixed, '_clipped_rectangular_context', lambda *a: pytest.fail('Expired budget'))
    case = make_cases()[0]
    with image_search(session):
        assert fit_primitive_scene(case['width'], case['height'], description=case['description'],
            image=render(case['svg'], case['width'], case['height']), render_fn=render,
            error_fn=lambda a, b: float(abs(a.astype(float)-b).mean())) is None


def test_rank_deficient_curves_do_not_supply_a_missing_bound():
    # Only the two horizontal and one vertical side of a sharp rectangle.
    x = np.arange(2., 180.)
    y = np.arange(30., 171.)
    points = np.r_[np.c_[x, np.full_like(x, 30.)], np.c_[x, np.full_like(x, 170.)],
                   np.c_[np.full_like(y, 180.), y]]
    assert mixed._observed_rectangle(points, (200, 200), False) is None


def test_constant_coverage_has_no_observed_canvas_boundary():
    assert len(mixed._coverage_boundary(np.ones((50, 60)), np.ones((50, 60), bool))) == 0


def test_fully_hidden_corners_are_not_counted_as_positive_observations():
    case = make_cases()[0]
    case['expected_objects'][0]['bbox'][0] = -100.
    corners, sides = parent_regions(case)
    assert sum(c['visibility'] == 'hidden' for c in corners) == 2
    assert all(s['name'] != 'left' for s in sides)


def test_global_fit_does_not_override_a_wrong_cropped_native_radius():
    from tools.run_plan_b_variations import measure_quality
    case = make_cases()[0]
    root = ET.fromstring(case['svg'])
    root[2].set('rx', str(case['expected_objects'][0]['corner_radius']+2.))
    altered = ET.tostring(root, encoding='unicode')
    image = render_librsvg(case['svg'], case['width'], case['height'])
    assert measure_quality(image, altered)['satisfactory']
    assert not check_objects(altered, case['expected_objects'])['passed']


def test_unobserved_radius_is_rejected_when_all_curves_are_cropped():
    # A constant gradient crop from a huge rounded panel contains no side
    # or arc observation, irrespective of the semantic rounding claim.
    case = make_cases()[0]
    root = ET.fromstring(case['svg'])
    root[2].attrib.update(x='-150', y='-150', width='660', height='660', rx='20')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit_independent(case)[1] is None


@pytest.mark.parametrize('missing_child', [False, True])
def test_only_semantically_complete_incumbents_are_saved_during_minimum_effort(missing_child):
    case = make_cases()[0]
    if missing_child:
        root = ET.fromstring(case['svg'])
        root.remove(root[-1])
        case['svg'] = ET.tostring(root, encoding='unicode')
    saved = []
    session = ImageSearch(SearchPolicy(seconds=5, max_seconds=5, minimum_seconds=5))
    session.on_validated = lambda result, image, quality: saved.append((result, image, quality))
    fit_independent(case, session)
    if missing_child:
        assert not saved
    else:
        assert saved
        for result, image, quality in saved:
            assert quality['passed']
            assert_accepted(case, image, dict(result, scene_attempts=[]))


def test_eager_registration_can_finish_before_spending_the_next_coordinate():
    from src.iCCModules.imageCompositeConverterFilledSymbols import _register_steps
    from src.iCCModules.imageCompositeConverterSearchScheduler import drain
    session = ImageSearch(SearchPolicy(seconds=5, max_seconds=5))
    def build(p):
        assert p[1] == 0, 'A checked early success must finish before another coordinate'
        return str(p[0])
    with image_search(session):
        result = drain(_register_steps(np.zeros(2), 2, build, lambda p: p[0] >= 0,
            np.full((32, 32, 3), 100.), lambda svg, *a: np.full((32, 32, 3), float(svg)),
            lambda a, b: float(abs(a-b).mean()), 'early_checked_candidate',
            refinement_steps=(100.,), satisfactory_fn=lambda p, m: p[0] == 100.,
            eager_satisfactory=True, preserve_initial_error=True))
    assert result['error'] == 0
    assert result['search_control']['stop_reason'] == 'satisfactory'


@pytest.mark.parametrize('candidate,expected', [(100., 100.), (104., 99.)])
def test_checked_alternate_seed_keeps_the_original_error_bound(candidate, expected):
    from src.iCCModules.imageCompositeConverterFilledSymbols import _register_steps
    from src.iCCModules.imageCompositeConverterSearchScheduler import drain
    session = ImageSearch(SearchPolicy(seconds=5, max_seconds=5))
    with image_search(session):
        result = drain(_register_steps(np.array([99.]), 1, lambda p: str(p[0]), lambda p: True,
            np.full((32, 32, 3), 100.), lambda svg, *a: np.full((32, 32, 3), float(svg)),
            lambda a, b: float(abs(a-b).mean()), 'checked_seed',
            loss_fn=lambda a, b: -float(abs(a-b).mean()),
            initial_candidates=(np.array([candidate]),), refinement_steps=(),
            satisfactory_fn=lambda p, m: p[0] == candidate,
            eager_satisfactory=True, preserve_initial_error=True))
    assert result['parameters'] == [expected]
    assert result['error'] <= result['initial_error']
