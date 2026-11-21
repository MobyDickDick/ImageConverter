"""Later admissible models can win; failed geometry never wins on pixels."""
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterFormModels import compare_form_models
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterDiskArrow import fit_disk_arrow
from tools.run_plan_b_variations import render, measure_quality
from tests.test_right_disk_arrow_runtime import DESCRIPTION, INDEPENDENT


def model(name, shade):
    return dict(name=name, parameters=[shade], geometry_count=1,
        build=lambda p: f'{name}:{p[0]}', valid=lambda p: 0 <= p[0] <= 255)


def compare(models, *, budget=20, validate=lambda svg: True, session=None):
    calls = []
    target = np.full((16, 16, 3), 100, np.uint8)
    def rendered(svg, *_):
        calls.append(svg)
        return np.full_like(target, float(svg.split(':')[1]))
    with image_search(session):
        result = compare_form_models(models, image=target, render_fn=rendered,
            error_fn=lambda a, b: float(np.square(a.astype(float)-b).mean()),
            validate_fn=validate, source='comparison_test', render_budget=budget, probe_renderings=2)
    return result, calls


def test_later_model_wins_over_valid_but_insufficient_first_candidate():
    result, calls = compare([model('early', 150), model('late', 100)])
    assert result['model'] == 'late'
    assert result['model_comparison']['satisfactory']
    assert any(svg.startswith('early:') for svg in calls)
    assert any(svg.startswith('late:') for svg in calls)


def test_pixel_perfect_candidate_with_wrong_geometry_cannot_win():
    result, _ = compare([model('valid', 130), model('wrong', 100)],
                         validate=lambda svg: not svg.startswith('wrong:'))
    assert result['model'] == 'valid'
    assert not result['model_comparison']['satisfactory']
    assert any(not row['semantic_passed'] for row in result['model_comparison']['attempts'])


@pytest.mark.parametrize('budget', [1, 2, 7, 20])
def test_all_model_renderings_share_the_exact_budget(budget):
    result, calls = compare([model('one', 180), model('two', 170)], budget=budget)
    assert len(calls) <= budget
    assert result['evaluations'] == len(calls)
    assert result['model_comparison']['renderings'] == len(calls)


def test_expired_image_deadline_starts_no_new_rendering():
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1), clock=lambda: 0)
    session.spent = 1
    result, calls = compare([model('one', 180)], session=session)
    assert result is None and calls == []


def test_refinement_resumes_trials_without_rendering_the_probe_again():
    result, calls = compare([model('one', 200), model('two', 180)], budget=40)
    assert len(calls) == len(set(calls))
    report = result['model_comparison']
    assert report['selection_policy'] == 'quality_progress_with_exploration'
    for name in ('one', 'two'):
        rows = [row for row in report['attempts'] if row['model'] == name]
        assert rows[0]['phase'] == 'probe'
        assert any(row['phase'] == 'refine' for row in rows)
        assert rows[-1]['remembered_trials'] > rows[0]['remembered_trials']


def test_probe_evidence_gives_the_better_later_model_the_next_turn():
    result, _ = compare([model('distant', 220), model('closer', 150)], budget=12)
    rows = result['model_comparison']['attempts']
    assert [row['model'] for row in rows[:3]] == ['distant', 'closer', 'closer']
    assert rows[1]['quality_score'] < rows[0]['quality_score']
    # Exploration still gives a poorly ranked model another turn.
    assert any(row['model'] == 'distant' and row['phase'] == 'refine' for row in rows)


def test_equivalent_models_share_render_evidence_even_without_a_session():
    first, second = model('shared', 180), model('shared', 180)
    first['name'], second['name'] = 'first', 'second'
    result, calls = compare([first, second], budget=20)
    assert len(calls) == len(set(calls))
    assert result['model_comparison']['duplicate_renderings_avoided'] > 0
    assert result['evaluations'] == len(calls)


def test_deadline_during_a_probe_starts_no_further_rendering():
    now = [0.]
    session = ImageSearch(SearchPolicy(seconds=1, max_seconds=1), clock=lambda: now[0])
    target = np.full((16, 16, 3), 100, np.uint8)
    calls = []
    def render_once(svg, *_):
        calls.append(svg)
        now[0] = 1.
        return np.full_like(target, 180)
    with image_search(session):
        result = compare_form_models([model('one', 180), model('two', 170)],
            image=target, render_fn=render_once,
            error_fn=lambda a, b: float(np.square(a.astype(float)-b).mean()),
            validate_fn=lambda svg: True, source='deadline_test', render_budget=20)
    assert len(calls) == 1
    assert result['model_comparison']['stop_reason'] == 'time_limit'


def test_visually_unchanged_failed_neighbourhood_is_abandoned():
    target = np.full((16, 16, 3), 100, np.uint8)
    calls = []
    def flat_model(name):
        return dict(name=name, parameters=[10.]*8, geometry_count=8,
            build=lambda p: name+':'+repr(p.tolist()), valid=lambda p: True)
    def unchanged(svg, *_):
        calls.append(svg)
        return np.full_like(target, 180)
    result = compare_form_models([flat_model('one'), flat_model('two')],
        image=target, render_fn=unchanged,
        error_fn=lambda a, b: float(np.square(a.astype(float)-b).mean()),
        validate_fn=lambda svg: True, source='plateau_test',
        render_budget=100, probe_renderings=4)
    rows = result['model_comparison']['attempts']
    for name in ('one', 'two'):
        final = [row for row in rows if row['model'] == name][-1]
        assert final['exhausted']
        assert final['stop_reason'] == 'shape_stagnation'
    assert len(calls) < 50
    assert not result['model_comparison']['satisfactory']


def test_real_three_stop_gradient_beats_earlier_two_stop_model():
    root = ET.fromstring(INDEPENDENT)
    gradient = next(node for node in root.iter() if node.tag.endswith('linearGradient'))
    gradient.insert(1, ET.Element('stop', offset='0.5', **{'stop-color': '#c5ddba'}))
    image = render(ET.tostring(root, encoding='unicode'), 104, 92)
    result = fit_disk_arrow(104, 92, description=DESCRIPTION, image=image,
        render_fn=render, error_fn=lambda a, b: float(np.square(a.astype(float)-b).mean()/255**2))
    assert result is not None
    report = result['model_comparison']
    assert {row['model'] for row in report['attempts']} == {'two_stop', 'three_stop'}
    assert report['selected_model'] == 'three_stop'
    assert measure_quality(image, result['svg'])['satisfactory']
    assert report['renderings'] <= report['render_budget']
