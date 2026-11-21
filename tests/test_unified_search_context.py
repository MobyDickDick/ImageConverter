"""Behavioral contracts for one image's rendering, scopes and worker handoff."""
import pickle
from pathlib import Path

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import (
    ImageSearch, SearchPolicy, candidate_scope, image_search, tracked_renderer,
)
from src.iCCModules.imageCompositeConverterFilledSymbols import _register
from src.iCCModules.imageCompositeConverterSearchPortfolio import (
    configured_image_search, conversion_search_context, proposal_rng, search_configuration, validated_result,
)


SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect width="16" height="16" fill="black"/></svg>'


def test_nested_renderers_count_once_and_cached_pixels_are_isolated():
    calls = []
    @tracked_renderer
    def private(svg, w, h):
        calls.append(svg)
        return np.full((h, w, 3), 17, np.uint8)
    @tracked_renderer
    def public(svg, w, h):
        return private(svg, w, h)
    session = ImageSearch(SearchPolicy(), render_budget=2)
    with image_search(session):
        original = public(SVG, 16, 16)
        original[:] = 255
        assert np.all(public(SVG, 16, 16) == 17)
        assert len(calls) == session.renderings == 1
        assert session.render_cache_hits == 1
        assert public(SVG, 8, 8).shape == (8, 8, 3)
        assert public(SVG, 4, 4) is None
        assert session.reason() == 'render_limit'
        # Completion/checking may reuse a candidate after the budget is spent.
        assert public(SVG, 16, 16) is not None
    assert len(calls) == session.renderings == 2


def test_raster_cache_is_independent_of_masked_objectives_but_not_backend():
    session = ImageSearch(SearchPolicy(), render_budget=4)
    target = np.zeros((16, 16, 3), np.uint8)
    calls = []
    def render(svg, w, h):
        calls.append(svg)
        return target.copy()
    with image_search(session):
        session.bind_reference(target)
        first, fresh = session.render_candidate(target, SVG, render, 16, 16)
        second, again = session.render_candidate(target+1, SVG, render, 16, 16)
        assert fresh and not again and np.array_equal(first, second)
        session.measured(SVG, 0., source='masked', scope='intermediate')
        session.measured(SVG, 9., source='whole', scope='full_scene', valid=True)
        assert session.objectives[('masked', 'intermediate')] == 0.
        assert session.objectives[('whole', 'full_scene')] == 9.
        assert session.best_error == 9. and not session.validated
        session.render_candidate(target, SVG, render, 16, 16, renderer='other_color_space')
    assert len(calls) == session.renderings == 2


@pytest.mark.parametrize('mode,adaptive', [('legacy', False), ('portfolio', False), ('portfolio', True)])
def test_every_policy_shares_budget_and_full_seed_across_models_and_reentry(mode, adaptive):
    with search_configuration(mode=mode, adaptive=adaptive, seed=2**64-1, budget=32):
        with configured_image_search('source') as session:
            stream = proposal_rng('model', 'first').random()
            session.renderings = 32
            with configured_image_search('source') as nested:
                assert nested is session and nested.reason() == 'render_limit'
            assert session.search_seed == 2**64-1
            assert stream == proposal_rng('model', 'first').random()
            assert stream != proposal_rng('model', 'second').random()
        with configured_image_search('source') as retry:
            assert retry is session and retry.renderings == 32
        with configured_image_search('other') as other:
            assert other is not session and other.renderings == 0


def test_registration_and_custom_fitter_use_the_same_remaining_budget():
    target = np.zeros((16, 16, 3), np.uint8)
    calls = []
    @tracked_renderer
    def render(svg, w, h):
        calls.append(svg)
        return np.full_like(target, 200)
    session = ImageSearch(SearchPolicy(seconds=30, max_seconds=30), seed=17, render_budget=5)
    with image_search(session):
        render(SVG, 16, 16)  # A custom fitter's direct render, without _register.
        result = _register(np.zeros(2), 2, lambda p: '<svg values="'+str(p.tolist())+'"/>',
            lambda p: True, target, render, lambda a, b: 1., 'analytic', allow_portfolio=False)
        assert result is not None and session.renderings == 5
        assert result['search_control']['stop_reason'] == 'render_limit'
        assert _register(np.zeros(1), 1, lambda p: '<svg/>', lambda p: True,
            target, render, lambda a, b: 1., 'later_model') is None
    assert len(calls) == 5


def test_result_rechecks_and_export_stay_inside_the_original_context():
    @tracked_renderer
    def render(svg, w, h):
        return np.zeros((h, w, 3), np.uint8)
    @conversion_search_context
    def convert(*, folder_path, filename):
        from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search
        original = current_search()
        with configured_image_search(str(Path(folder_path, filename).resolve())) as nested:
            assert nested is original
            render(SVG, 16, 16)
        # This used to run after the per-image context had been removed.
        render(SVG, 8, 8)
        return dict(params={}, search_control={}), False
    with search_configuration(mode='portfolio', adaptive=True, budget=32):
        row, failed = convert(folder_path='.', filename='neutral.png')
    assert not failed and row['search_control']['renderings'] == 2
    assert row['params']['adaptive_search']['renderings'] == 2


def test_masked_pixel_pass_cannot_publish_a_conversion_or_extend_its_deadline():
    target = np.zeros((16, 16, 3), np.uint8)
    session = ImageSearch(SearchPolicy())
    session.bind_reference(target)
    result = dict(svg=SVG, rendered=target+1, error=0., source='mask')
    with image_search(session), candidate_scope('intermediate', 'mask'):
        assert not session.validate(result, target)
        assert not validated_result(result, target, scope='intermediate')
        assert not validated_result(result, target+1)
        session.measured(SVG, 0., source='mask', scope='intermediate', valid=True, passed=True)
    assert not session.validated and np.isinf(session.best_error)
    assert not next(iter(session.candidates.values()))['passed']
    with image_search(session):
        assert validated_result(dict(svg=SVG, rendered=target, error=0.), target)
    assert len(session.validated) == 1
    assert any(row['scope'] == 'full_scene' and row.get('passed') for row in session.attempts)


def test_budget_and_sequence_survive_worker_serialization_without_callbacks():
    @tracked_renderer
    def render(svg, w, h):
        return np.zeros((h, w, 3), np.uint8)
    session = ImageSearch(SearchPolicy(), seed=2**64-1, render_budget=2)
    with image_search(session):
        render(SVG, 16, 16)
    resumed = pickle.loads(pickle.dumps(session))
    with image_search(resumed):
        assert np.array_equal(render(SVG, 16, 16), np.zeros((16, 16, 3)))
        assert resumed.renderings == 1 and resumed.render_cache_hits == 1
        render(SVG, 8, 8)
        assert render(SVG, 4, 4) is None
    assert resumed.search_seed == 2**64-1 and resumed.renderings == 2


def test_json_handoff_keeps_render_budget_sequence_and_cached_pixels():
    import json
    import time
    @tracked_renderer
    def render(svg, w, h):
        return np.zeros((h, w, 3), np.uint8)
    session = ImageSearch(SearchPolicy(), seed=2**64-1, render_budget=2)
    with image_search(session):
        render(SVG, 16, 16)
        state = json.loads(json.dumps(session.handoff(deadline=time.monotonic()+30)))
    child = ImageSearch.from_handoff(state)
    assert child.render_sequence_sha256 == session.render_sequence_sha256
    with image_search(child):
        assert render(SVG, 16, 16) is not None
        assert child.renderings == 1 and child.render_cache_hits == 1
        render(SVG, 8, 8)
        assert render(SVG, 4, 4) is None
    assert child.search_seed == 2**64-1 and child.renderings == 2


def test_render_failures_consume_budget_and_have_explicit_evidence():
    @tracked_renderer
    def failing(svg, w, h):
        return None
    session = ImageSearch(SearchPolicy(), render_budget=1)
    with image_search(session):
        assert failing(SVG, 16, 16) is None
        assert failing(SVG, 16, 16) is None
        assert failing(SVG, 8, 8) is None
    assert session.renderings == session.render_failures == 1
    assert session.render_cache_hits == 1
    assert [a['event'] for a in session.attempts] == [
        'candidate_rendered', 'candidate_cache_hit', 'candidate_skipped']


def test_deadline_is_checked_before_a_new_render_but_cached_rasters_remain_available():
    now = [0.]
    @tracked_renderer
    def render(svg, w, h):
        return np.zeros((h, w, 3), np.uint8)
    session = ImageSearch(SearchPolicy(seconds=1., max_seconds=1.), clock=lambda: now[0])
    with image_search(session):
        render(SVG, 16, 16)
        now[0] = 1.
        assert render(SVG, 16, 16) is not None
        assert render(SVG, 8, 8) is None
    assert session.renderings == 1 and session.stop_reason == 'time_limit'
