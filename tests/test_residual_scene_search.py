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
    assert sum(attempt['outcome'] == 'accepted' for attempt in result['scene_attempts']) == 1
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


def test_poor_first_structure_cannot_starve_a_complete_alternative(monkeypatch):
    from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
    case = make_cases()[0]
    image = render(case['svg'], case['width'], case['height'])
    objects = mixed.detect_instances(image, scene_contract(case['description']))
    poor = deepcopy(objects)
    poor[1]['colors'][:6] = 0
    detected, rendered = [], []
    now = [0.]
    session = ImageSearch(SearchPolicy(seconds=.4, max_seconds=.4), clock=lambda: now[0])

    def detect(*args, residual_threshold):
        detected.append(residual_threshold)
        return deepcopy(objects if residual_threshold == 16 else poor)

    def timed_render(svg, width, height):
        now[0] += .03
        rendered.append(svg)
        return render(svg, width, height)

    monkeypatch.setattr(mixed, 'detect_instances', detect)
    from src.iCCModules.imageCompositeConverterSearchScheduler import drain
    sequential = ImageSearch(SearchPolicy(seconds=.4, max_seconds=.4), clock=lambda: now[0])
    with image_search(sequential):
        for proposal in (poor, objects):
            assert drain(mixed._fit_instances_steps(
                case['width'], case['height'], pixels=image, contract=scene_contract(case['description']),
                objects=deepcopy(proposal), render_fn=timed_render,
                error_fn=lambda source, target: float(abs(source.astype(float)-target).mean()))) is None
    assert sequential.time_reason() == 'time_limit'
    now[0] = 0.
    rendered.clear()
    with image_search(session):
        result = mixed.fit_mixed_gradient_scene(
            case['width'], case['height'], description=case['description'], image=image,
            render_fn=timed_render, error_fn=lambda source, target: float(abs(source.astype(float)-target).mean()))
    assert result is not None
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert measure_quality(image, result['svg'])['satisfactory']
    assert all(quality['passed'] for quality in local_checks(image, result['svg'], case['expected_objects']))
    assert detected == [25, 16, 36]
    assert len(rendered) < 13
    assert session.elapsed < .4
    outcomes = {attempt['residual_threshold']: attempt['outcome'] for attempt in result['scene_attempts']}
    assert outcomes == {25: 'cancelled', 16: 'accepted', 36: 'duplicate'}
    history = session.scheduler_history[-1]
    assert history['stop_reason'] == 'caller_stopped'
    assert all(share['turns'] for share in history['models'].values())


def test_structure_jobs_share_the_deadline_and_close_suspended_fits(monkeypatch):
    from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
    case = make_cases()[0]
    image = render(case['svg'], case['width'], case['height'])
    objects = mixed.detect_instances(image, scene_contract(case['description']))
    now, visited, closed, events = [0.], [], [], []
    session = ImageSearch(SearchPolicy(seconds=.15, max_seconds=.15), clock=lambda: now[0])

    def detect(*args, residual_threshold):
        proposal = deepcopy(objects)
        proposal[1]['geometry'][0] += residual_threshold/100
        return proposal

    def optimize(*args, objects, **kwargs):
        identity = float(objects[1]['geometry'][0])
        try:
            while True:
                visited.append(identity)
                now[0] += .06
                yield 10.
        finally:
            closed.append(identity)

    monkeypatch.setattr(mixed, 'detect_instances', detect)
    monkeypatch.setattr(mixed, '_fit_instances_steps', optimize)
    monkeypatch.setattr(mixed, 'progress', lambda *args, **values: events.append(values))
    with image_search(session):
        assert mixed.fit_mixed_gradient_scene(
            case['width'], case['height'], description=case['description'], image=image,
            render_fn=render, error_fn=lambda *args: 0.) is None
    assert len(visited) == len(set(visited)) == 3
    assert sorted(closed) == sorted(visited)
    assert session.scheduler_history[-1]['stop_reason'] == 'time_limit'
    assert all(event['outcome'] == 'time_limit' for event in events if event['event'] == 'scene_hypothesis')
