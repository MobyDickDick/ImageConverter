"""Workers cooperate without revisiting failures or borrowing image budgets."""
import json
import math

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterSearchPortfolio import (
    configured_image_search, explore_parameters, search_configuration,
)
from src.iCCModules.imageCompositeConverterSearchBots import STRATEGIES


def fit(measure, *, image=None, satisfactory=None, source='model'):
    seed = np.zeros(4)
    initial = (10., 10., 'seed', np.zeros((2, 2, 3), dtype=np.uint8))
    return explore_parameters(seed, 2, measure, initial, source=source,
                              image=np.zeros((2, 2, 3), dtype=np.uint8) if image is None else image,
                              satisfactory_fn=satisfactory)


def test_retired_bots_and_negative_evidence_survive_retry_but_not_next_image(tmp_path):
    calls = []
    def failed(p):
        calls.append(tuple(p))
        return None
    with search_configuration(mode='portfolio', adaptive=True, directory=tmp_path, seed=8):
        with configured_image_search('first') as session:
            _, _, report = fit(failed)
            count = len(calls)
            assert report['stop_reason'] == 'all_bots_inactive'
            assert len(report['attempts']) == 6
            assert all(not bot['active'] for bot in report['attempts'])
            _, _, retry = fit(failed)
            assert len(calls) == count == len(set(calls))
            assert retry['reused_blackboard'] and retry['additional_evaluations'] == 0
            assert retry['remembered_candidates'] == count+1
            board = next(iter(session.bot_searches.values()))
            assert all(not r['valid'] for key, r in board.seen.items() if key != (0.,)*4)
        with configured_image_search('second'):
            fit(failed)
            assert len(calls) == 2*count
    evidence = json.loads(next((tmp_path/'bots').glob('*.json')).read_text())
    assert len(evidence['trials']) == count+1
    assert 'pending_semantic' in evidence['validation']


def test_best_is_shared_by_messages_and_preserved_on_retry():
    def measure(p):
        loss = float(np.sum((p-1)**2))
        return loss, loss, str(tuple(p)), np.zeros((2, 2, 3))
    with search_configuration(mode='portfolio', adaptive=True, seed=7):
        with configured_image_search('first'):
            p, best, report = fit(measure)
            assert best[1] < 10. and report['messages'] > 0
            assert any(b['received_messages'] for b in report['attempts'])
            p2, best2, retry = fit(lambda _: pytest.fail('repeated measurement'))
            assert np.array_equal(p, p2) and best2[2] == best[2]
            assert retry['additional_evaluations'] == 0


def test_even_small_budget_reserves_exploration_for_all_bots():
    with search_configuration(mode='portfolio', adaptive=True, seed=4, budget=32):
        with configured_image_search('image'):
            _, _, report = fit(lambda p: None)
    assert {b['strategy'] for b in report['attempts']} == set(STRATEGIES)
    assert all(b['proposals'] > 0 for b in report['attempts'])
    assert report['additional_evaluations'] == 32
    assert report['budget_extensions'] == 0


@pytest.mark.parametrize('bad', [None, (math.inf, 1., '', None), (1., math.nan, '', None),
                               (1., 11., 'worse error', None)])
def test_invalid_or_worse_error_cannot_win_or_buy_more_budget(bad):
    with search_configuration(mode='portfolio', adaptive=True, seed=9, budget=32):
        with configured_image_search('image'):
            _, best, report = fit(lambda _: bad)
    assert best[:3] == (10., 10., 'seed')
    assert report['additional_evaluations'] <= 32
    assert report['budget_extensions'] == 0


def test_changed_pixels_or_model_have_independent_blackboards():
    with search_configuration(mode='portfolio', adaptive=True, budget=32):
        with configured_image_search('image') as session:
            fit(lambda _: None)
            _, _, report = fit(lambda _: None, image=np.ones((2, 2, 3), dtype=np.uint8))
            assert not report['reused_blackboard']
            fit(lambda _: None, source='other model')
            assert len(session.bot_searches) == 3
    with search_configuration(mode='portfolio', adaptive=True, budget=32):
        with configured_image_search('image') as new_session:
            assert not new_session.bot_searches


def test_shared_time_limit_stops_all_bots_and_cannot_restart_on_retry():
    with search_configuration(mode='portfolio', adaptive=True, seconds=1., max_seconds=2.):
        with configured_image_search('image') as session:
            now = [0.]
            session.clock = lambda: now[0]
            session.active_since = 0.
            def slow(p):
                now[0] += .6
                return None
            _, _, report = fit(slow)
            assert report['stop_reason'] == 'time_limit'
            assert report['additional_evaluations'] == 2
            _, _, retry = fit(lambda _: pytest.fail('deadline restarted'))
            assert retry['additional_evaluations'] == 0


def test_cached_success_still_requires_current_callers_semantics():
    with search_configuration(mode='portfolio', adaptive=True, budget=32):
        with configured_image_search('image'):
            _, _, accepted = fit(lambda _: None, satisfactory=lambda *_: True)
            assert accepted['stop_reason'] == 'satisfactory'
            _, _, rejected = fit(lambda _: None, satisfactory=lambda *_: False)
            assert rejected['stop_reason'] != 'satisfactory'
            assert rejected['additional_evaluations'] > 0


def test_coupled_bot_escapes_coordinate_trap():
    def measure(p):
        loss = 1. if p[0] > .4 and p[1] > .4 else 10.
        return loss, loss, str(tuple(p)), np.zeros((2, 2, 3))
    with search_configuration(mode='portfolio', adaptive=True, seed=7):
        with configured_image_search('trap'):
            _, best, report = fit(measure)
    assert best[0] == 1.
    assert report['winning_strategy'] in {'joint_restart', 'geometry_pair'}
