"""Exact proposal reuse cannot change native boundaries or scene acceptance."""
from copy import deepcopy

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from tests.test_residual_scene_search import fit
from tests.test_structure_search_operators import assert_accepted
from tools.evaluate_mixed_overlap import make_cases
from tools.run_plan_b_variations import render


@pytest.fixture
def observed():
    case = make_cases(731429, groups=2, rounded=True, outlined=True)[0]
    pixels = render(case['svg'], case['width'], case['height'])
    contract = mixed.scene_contract(case['description'])
    _, _, predicted, mask, _ = mixed._gradient_context(pixels, contract, 25)
    paints = mixed._paint_components(pixels, mask, outlined=True)
    groups = [(color, np.isin(labels, parts)) for color, labels, parts in paints]
    return pixels, predicted, mask, groups


def same(actual, expected):
    if expected is None:
        assert actual is None
        return
    assert len(actual) == len(expected)
    for a, b in zip(actual, expected):
        assert set(a) == set(b)
        for key in a:
            np.testing.assert_equal(a[key], b[key])


def measure(observed, cache=None, **changes):
    pixels, predicted, mask, groups = observed
    options = dict(rounded=True, outlined=True, circles=True, groups=groups)
    options.update(changes)
    return mixed._overlap_instances(pixels, predicted, mask, proposals=cache, **options)


def test_native_reuse_is_exact_and_returned_edits_cannot_poison_it(observed):
    cache = mixed._OverlapProposals(observed[0])
    expected = measure(observed)
    assert expected is not None
    first = measure(observed, cache)
    same(first, expected)
    first.reverse()
    first[0]['geometry'][:] = -100
    first[0]['colors'][:] = 0
    same(measure(observed, cache), expected)
    assert cache.measurements == 1 and cache.hits == 1


@pytest.mark.parametrize('change', ['groups', 'order', 'parent', 'rounded', 'outlined', 'circles'])
def test_other_observed_evidence_and_native_requirements_are_measured_again(observed, change):
    cache = mixed._OverlapProposals(observed[0])
    measure(observed, cache)
    pixels, predicted, mask, groups = observed
    options = {}
    if change == 'groups':
        groups = deepcopy(groups)
        left = np.where(groups[0][1])[1].min()
        groups[0][1][:, :left+3] = False
        options['groups'] = groups
    elif change == 'order':
        options['groups'] = groups[::-1]
    elif change == 'parent':
        observed = (pixels, predicted+3., mask, groups)
    else:
        options[change] = False
    same(measure(observed, cache, **options), measure(observed, **options))
    assert cache.measurements == 2 and cache.hits == 0


def test_negative_native_evidence_is_reused_without_accepting_it(observed):
    pixels, predicted, mask, groups = observed
    groups = deepcopy(groups)
    groups[0][1][:] = False
    cache = mixed._OverlapProposals(pixels)
    assert measure(observed, cache, groups=groups) is None
    assert measure(observed, cache, groups=groups) is None
    assert cache.measurements == 1 and cache.hits == 1


def test_cache_cannot_cross_images(observed):
    pixels, predicted, mask, groups = observed
    with pytest.raises(ValueError, match='one image'):
        measure((pixels.copy(), predicted, mask, groups), mixed._OverlapProposals(pixels))


def test_cache_retains_at_most_the_structure_budget(monkeypatch):
    pixels = np.zeros((12, 12, 3), dtype=np.uint8)
    cache = mixed._OverlapProposals(pixels)
    monkeypatch.setattr(mixed, '_overlap_instances', lambda *a, **k: None)
    for index in range(97):
        cache.measure(pixels, pixels+float(index), pixels[:, :, 0],
                      [(np.zeros(3), np.ones((12, 12), dtype=bool))],
                      rounded=False, outlined=False, circles=False)
    assert len(cache.entries) == 96
    assert cache.measurements == 97


def test_threshold_reuse_still_passes_full_scene_and_independent_gates(monkeypatch):
    events = []
    monkeypatch.setattr(mixed, 'progress', lambda *a, **k: events.append(k))
    case = make_cases(731429, groups=4, rounded=True, outlined=True)[0]
    pixels, result = fit(case)
    assert_accepted(case, pixels, result)
    native = [e for e in events if e.get('event') == 'native_proposal']
    assert native[-1]['measurements'] == 1
    assert native[-1]['cache_hits'] == 2
    assert sum(a['outcome'] == 'accepted' for a in result['scene_attempts']) == 1
