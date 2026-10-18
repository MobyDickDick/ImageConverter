"""Fair model slices, measured costs, shared caches and process-safe state."""
import pickle

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterFilledSymbols import _register, _register_steps
from src.iCCModules.imageCompositeConverterSearchScheduler import FairSelector, schedule_models


def test_productive_search_gets_more_turns_without_starving_flat_alternatives():
    selector = FairSelector(['local', 'coupled', 'global'])
    chosen = []
    for _ in range(30):
        name = selector.choose(['local', 'coupled', 'global'])
        chosen.append(name)
        selector.record(name, .1, 100., 80. if name == 'coupled' else 100.)
    assert chosen[:3] == ['local', 'coupled', 'global']
    assert chosen.count('coupled') > chosen.count('local')
    for name in selector.shares:
        indices = [i for i,n in enumerate(chosen) if n == name]
        assert max(b-a for a,b in zip(indices, indices[1:])) <= 7


def test_progress_is_normalized_and_charged_per_active_second():
    selector = FairSelector(['slow', 'fast'])
    selector.record('slow', 1., 1000., 900.)
    selector.record('fast', .1, 10., 9.)
    assert selector.choose(['slow', 'fast']) == 'fast'
    assert selector.shares['fast'].rate == pytest.approx(10*selector.shares['slow'].rate)


def make_session(seconds=10):
    now = [0.]
    session = ImageSearch(SearchPolicy(seconds=seconds, max_seconds=seconds), clock=lambda: now[0])
    return now, session


def test_models_interleave_in_real_time_slices_and_close_after_early_acceptance():
    now, session = make_session()
    visits, closed, events = [], [], []
    def model(name, loss):
        try:
            for _ in range(20):
                visits.append(name)
                now[0] += .03
                yield loss
            return name+' result'
        finally:
            closed.append(name)
    with image_search(session):
        jobs = schedule_models({'bad':model('bad', 100.), 'good':model('good', 1.)}, session,
                               source='test', emit=lambda *a,**v:events.append(v))
        name, result = next(jobs)
        jobs.close()
    assert visits[:4] == ['bad','bad','good','good']
    assert result == name+' result' and set(closed) == {'bad','good'}
    assert session.scheduler_history[0]['stop_reason'] == 'caller_stopped'
    assert any(event['event'] == 'model_slice' for event in events)


def test_deadline_is_shared_by_models_and_never_reset():
    now, session = make_session(.1)
    visits = []
    def model(name):
        while True:
            visits.append(name)
            now[0] += .06
            yield 1.
    with image_search(session):
        assert list(schedule_models({'a':model('a'),'b':model('b')}, session,
                                    source='test', emit=lambda *a,**v:None)) == []
        assert session.time_reason() == 'time_limit'
    assert visits == ['a','b']
    assert session.scheduler_history[-1]['stop_reason'] == 'time_limit'


def test_exception_closes_other_started_models():
    now, session = make_session()
    closed = []
    def model(name):
        try:
            now[0] += .06
            yield 1.
            if name == 'bad':
                raise ValueError('failed model')
            yield 1.
        finally:
            closed.append(name)
    with image_search(session), pytest.raises(ValueError, match='failed model'):
        list(schedule_models({n:model(n) for n in ('good','bad')}, session,
                             source='test', emit=lambda *a,**v:None))
    assert set(closed) == {'good','bad'}
    assert session.scheduler_history[-1]['stop_reason'] == 'execution_error'


def test_model_cache_shares_rasters_but_not_objective_or_semantic_acceptance():
    now, session = make_session()
    image = np.full((16,16,3),255,dtype=np.uint8)
    calls = []
    def render(svg,w,h):
        calls.append(svg)
        return image.copy()
    def fit(error, valid_semantics):
        return _register([0.], 1, lambda p: str(tuple(p)), lambda p:True, image, render,
                         lambda *a:error, 'model', satisfactory_fn=lambda *a:valid_semantics)
    with image_search(session):
        first = fit(1., True)
        second = fit(8., True)
        rejected = fit(2., False)
        assert len(calls) == len(set(calls))
        assert first['error'] == 1. and second['error'] == 8.
        assert second['evaluations'] == 0
        assert rejected['search_control']['stop_reason'] != 'satisfactory'
    assert first['search_control']['stop_reason'] == 'satisfactory'


def test_failed_renders_are_cached_but_different_source_pixels_are_independent():
    now, session = make_session()
    calls = []
    def render(*args):
        calls.append(args)
        return None
    def fit(image):
        return _register([0.],1,lambda p:'svg',lambda p:True,image,render,lambda *a:0.,'model')
    with image_search(session):
        for _ in range(2):
            assert fit(np.zeros((16,16,3),dtype=np.uint8)) is None
        assert fit(np.ones((16,16,3),dtype=np.uint8)) is None
    assert len(calls) == 2


def test_scheduled_state_can_roundtrip_between_supervised_retries():
    now, session = make_session()
    def model():
        yield 100.
        return 'unvalidated result'
    with image_search(session):
        assert list(schedule_models({'a':model()},session,source='test',emit=lambda *a,**v:None)) == [('a','unvalidated result')]
    restored = pickle.loads(pickle.dumps(session))
    assert restored.scheduler_history == session.scheduler_history
    assert not restored.validated
    assert not ImageSearch(SearchPolicy()).scheduler_history


def test_shared_cache_is_bounded():
    now, session = make_session()
    image = np.zeros((16,16,3),dtype=np.uint8)
    with image_search(session):
        for i in range(270):
            # Each seed satisfies the unchanged pixel check, so only one raster.
            _register([float(i)],1,lambda p:str(p),lambda p:True,image,
                      lambda *a:image,lambda *a:0.,'model',satisfactory_fn=lambda *a:True)
    assert len(session.registration_rasters) == 256


def test_real_registration_steps_let_an_alternative_succeed_before_flat_first_model_times_out():
    now, session = make_session(.3)
    image = np.full((16,16,3),255,dtype=np.uint8)
    calls = []
    def model(name):
        def render(svg,w,h):
            calls.append(name)
            now[0] += .03
            return image.copy() if name == 'complete' else np.zeros_like(image)
        return _register_steps(np.zeros(12),12,lambda p:name+str(p),lambda p:True,image,render,
                               lambda a,b:float(np.mean((a.astype(float)-b)**2)),name,
                               satisfactory_fn=lambda *a:name=='complete')
    with image_search(session):
        scheduled = schedule_models({name:model(name) for name in ('flat','complete')},session,
                                    source='test',emit=lambda *a,**v:None)
        try:
            name, result = next(scheduled)
        finally:
            scheduled.close()
        assert name == 'complete'
        assert result['search_control']['stop_reason'] == 'satisfactory'
        assert session.elapsed < .3
    assert calls.count('flat') <= 2 and calls.count('complete') == 1


def test_bot_rates_do_not_charge_other_models_suspended_time():
    from src.iCCModules.imageCompositeConverterSearchBots import explore_bots_steps
    from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, settings
    now, session = make_session(100)
    initial = (10.,10.,'seed',np.zeros((2,2,3),dtype=np.uint8))
    def measure(p):
        now[0] += .01
        return None
    with search_configuration(mode='portfolio',adaptive=True,budget=32), image_search(session):
        job = explore_bots_steps(np.zeros(4),2,measure,initial,source='test',image=initial[3],
                                 satisfactory_fn=None,session=session,config=settings(),emit=lambda *a,**v:None)
        next(job)
        now[0] += 10  # another model's work between cooperative steps
        from src.iCCModules.imageCompositeConverterSearchScheduler import drain
        _,_,report = drain(job)
    assert sum(s['seconds'] for s in report['scheduler'].values()) == pytest.approx(.32)
