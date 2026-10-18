"""Adaptive control uses measured progress, not waiting or permissive gates."""
import math
import numpy as np
import pytest
from src.iCCModules.imageCompositeConverterAdaptiveSearch import (
    ImageSearch,SearchPolicy,SearchRun,current_search,image_search,pixel_quality,svg_identity,raster_identity,
)
from src.iCCModules.imageCompositeConverterSearchPortfolio import (
    configured_image_search,explore_parameters,search_configuration,
)
from src.iCCModules.imageCompositeConverterFilledSymbols import _register


class Clock:
    def __init__(self):
        self.now=0.
    def __call__(self):
        return self.now


def test_late_measured_progress_extends_time_once_then_requires_new_progress():
    clock=Clock()
    events=[]
    session=ImageSearch(SearchPolicy(),clock=clock,emit=lambda **v:events.append(v))
    with image_search(session):
        session.observe(100.)
        clock.now=59
        session.observe(80.)
        clock.now=60
        assert session.time_reason() is None
        assert session.limit==75 and session.extensions==1
        clock.now=75
        assert session.time_reason()=='time_limit'
        assert session.extensions==1
    assert events[0]['event']=='time_extended'


def test_continued_progress_never_exceeds_hard_time_limit():
    clock=Clock()
    session=ImageSearch(SearchPolicy(),clock=clock)
    with image_search(session):
        session.observe(100.)
        for t,error in ((59,80),(74,60),(89,40),(104,20)):
            clock.now=t
            session.observe(error)
            clock.now=t+1
            assert session.time_reason() is None
        assert session.limit==120
        clock.now=119
        session.observe(1.)
        clock.now=120
        assert session.time_reason()=='time_limit'
        assert session.limit==120


@pytest.mark.parametrize('error',[99.9999,100.,101.,math.nan,math.inf])
def test_noise_flat_error_and_failed_measurements_cannot_buy_more_time(error):
    clock=Clock()
    session=ImageSearch(SearchPolicy(),clock=clock)
    with image_search(session):
        session.observe(100.)
        clock.now=59
        session.observe(error)
        clock.now=60
        assert session.time_reason()=='time_limit'


def test_interleaved_images_share_no_time_and_retries_keep_used_time():
    clock=Clock()
    first,second=[ImageSearch(SearchPolicy(),clock=clock) for _ in range(2)]
    with image_search(first):
        clock.now=11
    clock.now=1000
    with image_search(second):
        clock.now=1007
    with image_search(first):
        assert first.elapsed==11
        clock.now=1010
    assert first.elapsed==14 and second.elapsed==7
    assert current_search() is None


def test_model_switch_and_repeated_image_use_same_context_but_next_image_is_fresh():
    with search_configuration(mode='portfolio',adaptive=True):
        with configured_image_search('first') as first:
            first.observe(10.)
            with configured_image_search('first') as nested:
                assert nested is first
        with configured_image_search('other') as second:
            assert second is not first and second.evaluations==0
        with configured_image_search('first') as repeated:
            assert repeated is first and repeated.evaluations==1


def test_late_proposal_progress_extends_budget_but_not_forever():
    session=ImageSearch(SearchPolicy())
    run=SearchRun(session,32,source='model')
    run.anchor=100.
    for i in range(32):
        run.observe(80. if i>=30 else 100.)
    assert run.reason(alternatives_tried=True) is None
    assert run.limit==48 and run.extensions==1
    for _ in range(16):
        run.observe(80.)
    assert run.reason(alternatives_tried=True)=='proposal_limit'


def test_stagnation_waits_for_alternative_strategies():
    session=ImageSearch(SearchPolicy(patience=8))
    run=SearchRun(session,96,source='model')
    for _ in range(8):
        run.observe(100.)
    assert run.reason(alternatives_tried=False) is None
    assert run.reason(alternatives_tried=True)=='stagnation'


def explore(*, satisfactory=None, flat=False, penalty=False):
    visited=[]
    clock=Clock()
    def measure(p):
        clock.now += .001
        visited.append(tuple(p))
        loss=10. if flat else float(np.sum((p-2)**2))
        return loss,100. if penalty else loss,str(tuple(p)),np.zeros((1,1,3),dtype=np.uint8)
    seed=np.zeros(5 if flat else 2)
    incumbent=measure(seed)
    if penalty:
        incumbent=(incumbent[0],incumbent[0],incumbent[2],incumbent[3])
    with search_configuration(mode='portfolio',adaptive=True,seed=3,budget=384):
        with configured_image_search('source') as session:
            # Scheduling uses measured durations. Reproducibility requires the
            # same costs as well as the same seed, not OS scheduling jitter.
            session.clock = clock
            session.active_since = clock.now
            result=explore_parameters(seed,2,measure,incumbent,source='test',image=np.zeros((1,1,3)),
                                      satisfactory_fn=satisfactory)
    return result,visited


def test_satisfactory_seed_ends_before_any_extra_proposal():
    (_,_,report),visited=explore(satisfactory=lambda *_:True)
    assert report['stop_reason']=='satisfactory'
    assert report['additional_evaluations']==0 and len(visited)==1


def test_flat_search_tries_all_methods_then_stops_before_base_budget():
    (_,_,report),visited=explore(flat=True)
    assert report['stop_reason']=='all_bots_inactive'
    assert report['additional_evaluations']<=128 < report['budget']
    assert all(a['proposals']>0 for a in report['attempts'])
    assert all(not a['active'] for a in report['attempts'])
    assert len(visited)==len(set(visited))


def test_adaptive_search_keeps_caller_error_bound_and_reproducibility():
    (_,best,report),_=explore(penalty=True)
    assert best[1]==8
    assert report['budget_extensions']==0
    assert explore()[1]==explore()[1]


def test_register_can_stop_at_semantically_checked_seed_but_not_at_pixel_pass_alone():
    image=np.full((24,24,3),255,dtype=np.uint8)
    image[5:19,5:19]=20
    rendered=[]
    def render(svg,w,h):
        rendered.append(svg)
        return image.copy()
    def run(check):
        return _register(np.zeros(1),1,lambda p:str(tuple(p)),lambda p:True,image,render,
                         lambda a,b:0.,'model',satisfactory_fn=check)
    with search_configuration(mode='portfolio',adaptive=True):
        with configured_image_search('checked'):
            result=run(lambda *_:True)
            assert result['search_control']['stop_reason']=='satisfactory'
            assert result['evaluations']==1
        with configured_image_search('unchecked'):
            result=run(lambda *_:False)
            assert result['search_control']['stop_reason']!='satisfactory'
            assert result['evaluations']>1


@pytest.mark.parametrize('seconds,maximum',[(0,120),(60,30),(math.nan,120),(60,math.inf)])
def test_invalid_time_policy_is_rejected(seconds,maximum):
    with pytest.raises(ValueError):
        SearchPolicy(seconds=seconds,max_seconds=maximum)


def test_nested_different_image_does_not_spend_outer_image_time():
    clock=Clock()
    first,second=[ImageSearch(SearchPolicy(),clock=clock) for _ in range(2)]
    with image_search(first):
        clock.now=3
        with image_search(second):
            clock.now=12
        clock.now=14
    assert first.elapsed==5 and second.elapsed==9


def test_a_later_model_cannot_restart_an_exhausted_image_budget():
    clock=Clock()
    session=ImageSearch(SearchPolicy(seconds=3,max_seconds=5),clock=clock)
    calls=[]
    image=np.full((24,24,3),255,dtype=np.uint8)
    def render(*args):
        calls.append(args)
        clock.now+=2
        return image.copy()
    def fit():
        return _register(np.zeros(1),1,lambda p:str(tuple(p)),lambda p:True,image,render,
                         lambda *args:1.,'model')
    with image_search(session):
        first=fit()
        count=len(calls)
        assert first['search_control']['stop_reason']=='time_limit'
        assert fit() is None and len(calls)==count


def test_validation_proof_is_bound_to_source_pixels_and_exact_selected_svg():
    session=ImageSearch(SearchPolicy())
    image=np.zeros((3,3,3),dtype=np.uint8)
    result={'svg':'<svg/>'}
    session.validate(result,image)
    assert (svg_identity(result['svg']),raster_identity(image)) in session.validated
    image[0,0]=255
    assert (svg_identity(result['svg']),raster_identity(image)) not in session.validated


def test_nonwhite_border_cannot_hide_a_missing_object_from_early_success():
    from tools.run_plan_b_variations import render,measure_quality
    header='<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
    base='<rect width="50" height="50" fill="#dcdcdc"/><rect x="5" y="5" width="14" height="12" fill="#b4b4b4"/>'
    reference=render(header+base+'<rect x="35" y="35" width="8" height="8" fill="#b4b4b4"/></svg>',50,50)
    svg=header+base+'</svg>'
    output=render(svg,50,50)
    actual=pixel_quality(reference,output)
    expected=measure_quality(reference,svg)
    assert not actual['passed'] and not expected['satisfactory']
    assert {k:v for k,v in actual.items() if k!='passed'}==expected['metrics']


def test_adaptive_short_label_stops_after_a_checked_model():
    from tools.run_plan_b_variations import render,measure_quality
    from src.iCCModules.imageCompositeConverterShortLabelDisk import fit_short_label_disk
    from tools.evaluate_short_label_search import symbol_semantics
    svg=('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
         '<rect width="64" height="64" fill="#ffffff"/>'
         '<circle cx="32" cy="32" r="25" fill="#d7e8db" stroke="#445a51" stroke-width="2"/>'
         '<text x="32" y="42" font-family="Arial" font-weight="700" font-size="26" text-anchor="middle" fill="#283b33">AB</text></svg>')
    image=render(svg,64,64)
    description='Eine einfarbige Kreisscheibe mit dunkler Randkontur. Serifenlose Beschriftung "AB". Keine Anschlüsse.'
    with search_configuration(mode='portfolio',adaptive=True,seed=13):
        with configured_image_search('label') as session:
            result=fit_short_label_disk(64,64,description=description,image=image,render_fn=render,
                error_fn=lambda a,b:float(np.mean((a.astype(float)-b)**2)))
            assert session.validated
    assert len(result['model_attempts'])<4
    assert measure_quality(image,result['svg'])['satisfactory']
    assert symbol_semantics(result['svg'],'AB')==1
