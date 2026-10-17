"""Search must escape a coordinate trap without weakening error or budget rules."""
import json

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterSearchPortfolio import (
    explore_parameters, ranked_models, search_configuration, store_validated_variant,
)


def run_search(seed, directory=None, error_penalty=False):
    visited = []
    def measure(p):
        visited.append(tuple(p))
        loss = 1. if min(p) > .4 else 5.
        error = 9. if error_penalty and loss == 1 else loss
        return loss, error, str(tuple(p)), np.zeros((1,1,3), dtype=np.uint8)
    initial = measure(np.zeros(2))
    with search_configuration(mode='portfolio', seed=seed, budget=96, directory=directory):
        result = explore_parameters(np.zeros(2), 2, measure, initial,
                                    source='independent_trap', image=np.zeros((1,1,3)))
    return result, visited


def test_joint_restart_escapes_coordinate_trap_and_has_a_shared_budget():
    (parameters, best, report), visited = run_search(7)
    assert best[0] == 1
    assert min(parameters) > .4
    assert report['additional_evaluations'] <= 96
    assert len(visited) == len(set(visited))
    assert {a['strategy'] for a in report['attempts']} == {
        'reverse_coordinates', 'shuffled_coordinates', 'joint_restart'}


def test_seeds_reproduce_search_and_change_paths():
    assert run_search(7)[1] == run_search(7)[1]
    assert run_search(7)[1] != run_search(19)[1]


def test_custom_loss_cannot_accept_worse_caller_error():
    (_, best, _), _visited = run_search(7, error_penalty=True)
    assert best[1] == 5


def test_pending_proposals_are_saved_without_becoming_validated_memory(tmp_path):
    run_search(7, tmp_path)
    assert len(list(tmp_path.rglob('*.json'))) == 3
    assert not (tmp_path/'strategy_memory.json').exists()
    assert not (tmp_path/'validated').exists()


def test_semantic_only_does_not_read_strategy_history(tmp_path, monkeypatch):
    import src.iCCModules.imageCompositeConverterSearchPortfolio as module
    monkeypatch.setattr(module, '_read_memory', lambda _: pytest.fail('history read'))
    with search_configuration(mode='portfolio', directory=tmp_path, allow_memory=False):
        assert set(ranked_models(['native', 'separate'])) == {'native','separate'}


def test_only_validated_pixel_pass_updates_strategy_history(tmp_path):
    image = np.zeros((2,2,3), dtype=np.uint8)
    result = dict(svg='<svg/>', parameters=[1.])
    with search_configuration(mode='portfolio', directory=tmp_path, allow_memory=True):
        store_validated_variant(result, image=image, description='test', model='separate', quality={'passed':False})
        assert not (tmp_path/'strategy_memory.json').exists()
        store_validated_variant(result, image=image, description='test', model='separate', quality={'passed':True})
        assert ranked_models(['native','separate'])[0] == 'separate'
    assert json.loads((tmp_path/'strategy_memory.json').read_text()) == {'separate':1}


@pytest.mark.parametrize('budget',[0,31,10001])
def test_invalid_budget_rejected(budget):
    with pytest.raises(ValueError), search_configuration(mode='portfolio',budget=budget):
        pass
