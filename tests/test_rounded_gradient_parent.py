"""Rounded parents need measured corners and the complete shared scene gates."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_layered_scene import check_objects
from tools.evaluate_rounded_parent import make_cases
from tools.run_plan_b_variations import render


@pytest.mark.parametrize('index', range(12))
def test_independent_fixture_has_native_parent_radius_and_complete_inventory(index):
    case = make_cases()[index]
    assert check_objects(case['svg'], case['expected_objects'])['passed']
    assert 12 <= case['expected_objects'][0]['corner_radius'] <= 32


@pytest.mark.parametrize('index', range(12))
def test_rounded_parent_uses_common_composition_and_existing_budget(index):
    case = make_cases()[index]
    image, result = fit(case)
    assert_accepted(case, image, result)
    assert sum(a['operator'] in ('edit', 'split_edit', 'group_islands')
               for a in result['scene_attempts']) <= 96


@pytest.mark.parametrize('index', [0, 1])
def test_parent_and_child_rounding_are_separately_consumed(index):
    contract = mixed.scene_contract(make_cases()[index]['description'])
    assert contract['parent_rounded'] is True
    assert contract['rounded'] is bool(index)


@pytest.mark.parametrize('damage', ['sharp', 'ellipse', 'unequal_corners', 'missing', 'extra',
    'texture', 'wrong_axis', 'wrong_groups', 'wrong_singletons', 'dark_rim', 'missing_rim',
    'unobservable_clipping', 'unclaimed_rounding'])
def test_corner_object_relation_and_raster_damage_remains_rejected(damage):
    case = deepcopy(make_cases()[1])
    root = ET.fromstring(case['svg'])
    parent = root[2]
    if damage == 'sharp':
        parent.set('rx', '0')
    elif damage == 'ellipse':
        parent.set('ry', '5')
    elif damage == 'unequal_corners':
        x, y = parent.get('x'), parent.get('y')
        ET.SubElement(root, 'rect', x=x, y=y, width='25', height='25', fill='white')
    elif damage == 'missing':
        root.remove(root[-1])
    elif damage == 'extra':
        ET.SubElement(root, 'rect', x='165', y='165', width='12', height='12', fill='#123456')
    elif damage == 'texture':
        ET.SubElement(root, 'rect', x='165', y='165', width='12', height='12', fill='white')
    elif damage == 'wrong_axis':
        case['description'] = case['description'].replace('vertikalen', 'horizontalen')
    elif damage == 'wrong_groups':
        case['description'] = case['description'].replace('2 Überdeckungsgruppen', '1 Überdeckungsgruppe')
    elif damage == 'wrong_singletons':
        case['description'] = case['description'].replace('1 einzelne Form', '2 einzelne Formen')
    elif damage == 'unobservable_clipping':
        # An entirely hidden side and its corner arcs cannot constrain a
        # native bound, even though shallower observable crops now compose.
        parent.set('x', '-100')
        parent.set('width', '436')
    elif damage == 'unclaimed_rounding':
        case['description'] = case['description'].replace(' Das äussere Rechteck hat gerundete Ecken.', '')
    else:
        parent.set('stroke', '#303030' if damage == 'dark_rim' else 'none')
    case['svg'] = ET.tostring(root, encoding='unicode')
    assert fit(case)[1] is None


def test_observed_clipped_parent_now_uses_shared_native_gates():
    case = make_cases()[1]
    root = ET.fromstring(case['svg'])
    root[2].set('x', '-8')
    root[2].set('width', '344')
    sw = case['expected_objects'][0]['stroke_width']
    case['expected_objects'][0]['bbox'][0] = -8-sw/2
    case['expected_objects'][0]['bbox'][2] = 344+sw
    case['svg'] = ET.tostring(root, encoding='unicode')
    image, result = fit(case)
    assert_accepted(case, image, result)


@pytest.mark.parametrize('claim', [' Mit Text.', ' Das äussere Rechteck hat gerundete Ecken.',
    ' Der äussere Kreis hat gerundete Ecken.', ' Die Formen sind nicht gefüllt.',
    ' Die inneren Kreise haben leicht gerundete Ecken.', ' mit leicht gerundeten Ecken'])
def test_rounding_does_not_discard_unknown_repeated_or_ambiguous_claims(claim):
    assert mixed.scene_contract(make_cases()[0]['description']+claim) is None


def test_expired_budget_starts_no_rounded_detection(monkeypatch):
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1))
    session.spent = 2
    monkeypatch.setattr(mixed, 'detect_instances', lambda *a, **k: pytest.fail('Expired budget'))
    assert fit(make_cases()[0], session)[1] is None


@pytest.mark.parametrize('radius', [0, 90])
def test_independent_native_oracle_rejects_wrong_parent_radius(radius):
    case = make_cases()[0]
    root = ET.fromstring(case['svg'])
    root[2].set('rx', str(radius))
    assert not check_objects(ET.tostring(root, encoding='unicode'), case['expected_objects'])['passed']


def test_good_global_pixels_cannot_excuse_a_compensating_native_radius():
    from tools.run_plan_b_variations import measure_quality

    case = make_cases()[0]
    root = ET.fromstring(case['svg'])
    root[2].set('rx', str(case['expected_objects'][0]['corner_radius']+2.))
    altered = ET.tostring(root, encoding='unicode')
    image = render(case['svg'], case['width'], case['height'])
    assert measure_quality(image, altered)['satisfactory']
    assert not check_objects(altered, case['expected_objects'])['passed']


def test_detected_radius_is_measured_from_pixels():
    case = make_cases()[0]
    contract = mixed.scene_contract(case['description'])
    estimates = []
    for radius in (13., 29.):
        root = ET.fromstring(case['svg'])
        root[2].set('rx', str(radius))
        pixels = render(ET.tostring(root, encoding='unicode'), case['width'], case['height'])
        objects = mixed.detect_instances(pixels, contract)
        assert objects is not None
        estimates.append(objects[0]['radius'])
    # Correct circular corners bind the area-derived proposal directly to the
    # native radius; registration only refines pixel quantization and bounds.
    assert estimates[1]-estimates[0] > 12
    assert all(.95*estimate <= radius <= 1.05*estimate
               for estimate, radius in zip(estimates, (13., 29.)))


def test_alternate_radius_seeds_share_deadline_cache_and_initial_error_bound():
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import image_search
    from src.iCCModules.imageCompositeConverterFilledSymbols import _register_steps
    from src.iCCModules.imageCompositeConverterSearchScheduler import drain

    now, rendered = [0.], []
    session = ImageSearch(SearchPolicy(seconds=.1, max_seconds=.1), clock=lambda: now[0])

    def raster(svg, width, height):
        rendered.append(svg)
        now[0] += .06
        return np.full((height, width, 3), float(svg))

    with image_search(session):
        result = drain(_register_steps(np.array([0.]), 1,
            lambda p: str(p[0]), lambda p: True, np.zeros((8, 8, 3)), raster,
            lambda a, b: float(abs(a-b).mean()), 'corner_budget_control',
            preserve_initial_error=True, loss_fn=lambda a, b: -float(b.mean()),
            initial_candidates=(np.array([v]) for v in (0., 1., 2., 3.))))
    # A cached duplicate costs no rendering. The first new alternative spends
    # the remaining time; no later seed runs, and lower search loss cannot
    # replace the original zero-error raster with a worse visible result.
    assert rendered == ['0.0', '1.0']
    assert session.evaluations == 2
    assert result['error'] == result['initial_error'] == 0
    assert result['search_control']['stop_reason'] == 'time_limit'
