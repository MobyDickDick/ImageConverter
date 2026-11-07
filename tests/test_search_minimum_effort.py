"""Poor fits spend their effort on distinct probes, with unchanged hard caps."""
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search, explore_parameters


def run_search(*, minimum=30., seconds=60., satisfactory=False, coupled=False):
    now, visited = [0.], []
    seed = np.array([0., 100.])
    def measure(p):
        now[0] += .05
        visited.append(tuple(p))
        loss = 1. if coupled and p[0] > 12 and p[1] > 112 else 10.
        return loss, loss, str(tuple(p)), np.zeros((2, 2, 3), dtype=np.uint8)
    initial = (10., 10., 'seed', np.zeros((2, 2, 3), dtype=np.uint8))
    with search_configuration(mode='portfolio', adaptive=True, seed=7, budget=32,
                              minimum_seconds=minimum, seconds=seconds, max_seconds=seconds):
        with configured_image_search('source') as session:
            session.clock, session.active_since = lambda: now[0], 0.
            result = explore_parameters(seed, 2, measure, initial, source='model', image=initial[3],
                                        satisfactory_fn=lambda *_: satisfactory)
            elapsed = session.elapsed
    return result, visited, elapsed


def test_flat_fit_keeps_testing_unique_candidates_for_thirty_active_seconds():
    (_, best, report), visited, elapsed = run_search()
    assert 30 <= elapsed < 30.1
    assert best[0] == 10.
    assert len(visited) == len(set(visited)) > report['max_budget']
    assert any(bot['restarts'] for bot in report['attempts'])
    assert report['stop_reason'] in {'proposal_limit', 'search_exhausted'}


def test_larger_coupled_restarts_find_a_solution_outside_the_original_grid():
    (_, old, _), _, _ = run_search(minimum=0., coupled=True)
    (_, new, report), _, elapsed = run_search(coupled=True)
    assert old[0] == 10. and new[0] == 1.
    assert elapsed >= 30 and any(bot['restarts'] for bot in report['attempts'])


def test_explicit_short_budget_caps_the_minimum_and_still_stops_on_time():
    (_, _, report), _, elapsed = run_search(seconds=2.)
    assert 2 <= elapsed < 2.1
    assert report['stop_reason'] == 'time_limit'


def test_confirmed_good_fit_can_finish_without_extra_work():
    (_, _, report), visited, elapsed = run_search(satisfactory=True)
    assert elapsed == 0 and not visited and report['stop_reason'] == 'satisfactory'


def test_model_comparison_finishes_searches_only_after_the_minimum():
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import SearchRun
    now = [0.]
    session = ImageSearch(SearchPolicy(minimum_seconds=30.), clock=lambda: now[0])
    session.finish_model_searches = True
    with image_search(session):
        run = SearchRun(session, 384, source='alternative')
        assert run.reason(alternatives_tried=True) is None
        now[0] = 30.
        assert run.reason(alternatives_tried=True) == 'candidate_comparison'


@pytest.mark.parametrize('minimum', [-1., float('nan'), float('inf'), 61.])
def test_invalid_minimum_policy(minimum):
    with pytest.raises(ValueError):
        SearchPolicy(minimum_seconds=minimum)


def test_tiny_global_error_does_not_hide_a_missing_local_detail():
    from src.iCCModules.imageCompositeConverterFilledSymbols import _register
    image = np.full((256, 256, 3), 255, dtype=np.uint8)
    output = image.copy()
    image[100, 100] = 0
    output[100, 102] = 0
    with search_configuration(mode='portfolio', adaptive=True, budget=32):
        with configured_image_search('tiny'):
            fitted = _register(np.zeros(1), 1, lambda p: str(p), lambda p: True, image,
                               lambda *_: output, lambda *_: 1., 'tiny_detail')
    assert fitted['search']['additional_evaluations'] > 0


def test_native_polish_improves_placement_without_changing_the_objects():
    from xml.etree import ElementTree as ET
    from src.imageConverterSample import render_svg
    from src.iCCModules.imageCompositeConverterVectorPolish import polish_generated_svg
    seed = '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"><circle cx="21" cy="22" r="12" fill="#335577"/></svg>'
    target = render_svg(seed.replace('cx="21" cy="22"', 'cx="24" cy="24"'), 48, 48)
    now = [0.]
    def render(svg, w, h):
        now[0] += .02
        return render_svg(svg, w, h)
    with search_configuration(mode='portfolio', adaptive=True, budget=32, minimum_seconds=3., seconds=4., max_seconds=4.):
        with configured_image_search('polish') as session:
            session.clock, session.active_since = lambda: now[0], 0.
            result = polish_generated_svg(seed, target, render)
    assert result['improved'] and result['error'] < result['initial_error']
    assert len([n for n in ET.fromstring(result['svg']).iter() if n.tag.endswith('circle')]) == 1
    assert 'path' not in result['svg'] and 'image' not in result['svg']


def test_longer_search_keeps_a_valid_incumbent_when_lower_pixel_error_breaks_semantics():
    from src.iCCModules.imageCompositeConverterFilledSymbols import _register
    image = np.full((24, 24, 3), 100, dtype=np.uint8)
    now = [0.]
    def render(svg, w, h):
        now[0] += .05
        return np.full_like(image, 107-int(float(svg)))
    with search_configuration(mode='portfolio', adaptive=True, budget=32,
                              minimum_seconds=1., seconds=2., max_seconds=2.):
        with configured_image_search('semantics') as session:
            session.clock, session.active_since = lambda: now[0], 0.
            result = _register(np.zeros(1), 1, lambda p: str(p[0]), lambda p: 0 <= p[0] <= 3,
                               image, render, lambda a, b: float(np.square(a.astype(float)-b).mean()),
                               'semantics', satisfactory_fn=lambda p, measured: p[0] < .5)
    assert result['parameters'] == [0.] and result['error'] == 49.
    assert now[0] >= 1.
