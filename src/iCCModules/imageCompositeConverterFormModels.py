"""Compare admissible form models using their measured search history.

Each model keeps one resumable registration, including unsuccessful trials.
Quality and recent progress allocate bounded turns; every model gets a probe.
The evidence belongs to this comparison, never to a different input image.
"""
from __future__ import annotations

import math
import time

from src.iCCModules.imageCompositeConverterAdaptiveSearch import (
    candidate_identity, current_search, pixel_quality, preferred_quality, raster_identity,
    vector_quality_score,
)
from src.iCCModules.imageCompositeConverterFilledSymbols import _register_steps
from src.iCCModules.imageCompositeConverterSearchPortfolio import progress


def compare_form_models(models, *, image, render_fn, error_fn, validate_fn,
                        source, render_budget=448, probe_renderings=24):
    """Return the best semantically valid fit within one shared render budget.

    Probes and refinements resume the same iterator. Failed coordinates and
    rendered outputs remain remembered, so a new turn cannot restart the same
    neighbourhood. Foreground/edge agreement and measured progress determine
    the next turn, with recurring exploration for the remaining alternatives.
    """
    if render_budget < 1 or probe_renderings < 1:
        raise ValueError('Positive model render budgets required')
    if not models or len({model['name'] for model in models}) != len(models):
        raise ValueError('Models require unique names')
    session = current_search()
    start = time.monotonic()
    attempts, states, jobs, rasters, qualities = [], {}, {}, {}, {}
    rendered = cache_hits = 0
    best = None
    best_quality = None
    stop = 'models_exhausted'
    turn = 0

    def expired():
        return session is not None and session.reason() is not None

    def rank(result, quality):
        return (bool(quality['passed']), -result['error'])

    def make_job(model):
        name = model['name']
        state = states[name] = dict(best=None, quality=None, trials=0,
            rejected=0, initial_error=None, turns=0, last_turn=-1, gain=0., stale=0,
            exhausted=False, stop_reason=None, shape_anchor=None, error_anchor=None,
            initial_score=None, stale_trials=0,
            patience=max(8, 2*len(model['parameters'])+1))

        def observed(parameters, measured):
            nonlocal best, best_quality
            state['trials'] += 1
            state['stale_trials'] += 1
            loss, error, svg, raster = measured
            if state['initial_error'] is None:
                state['initial_error'] = error
            if (state['best'] is not None and state['quality']['passed']
                    and error >= state['best']['error']):
                return
            # Semantics remain mandatory even for a pixel-perfect alternative.
            if not validate_fn(svg):
                state['rejected'] += 1
                return
            pixels_key = raster_identity(raster)
            if pixels_key not in qualities:
                qualities[pixels_key] = pixel_quality(image, raster)
            quality = qualities[pixels_key]
            if quality is None or not math.isfinite(error):
                return
            score = vector_quality_score(quality)
            if state['initial_score'] is None:
                state['initial_score'] = score
            anchor = state['shape_anchor']
            error_anchor = state['error_anchor']
            if (anchor is None or anchor-score >= max(1e-9, abs(anchor)*.01)
                    or error_anchor is None
                    or error_anchor-error >= max(1e-9, abs(error_anchor)*.01)):
                state['shape_anchor'] = min(anchor, score) if anchor is not None else score
                state['error_anchor'] = min(error_anchor, error) if error_anchor is not None else error
                state['stale_trials'] = 0
            result = dict(svg=svg, rendered=raster, error=error,
                initial_error=state['initial_error'], parameters=parameters.tolist(),
                source=source+'_'+name, model=name)
            if state['best'] is None or rank(result, quality) > rank(state['best'], state['quality']):
                state['best'], state['quality'] = result, quality
            if best is None or rank(result, quality) > rank(best, best_quality):
                best, best_quality = result, quality

        def counted(svg, width, height):
            nonlocal rendered, cache_hits
            key = candidate_identity(svg)
            if key in rasters:
                cache_hits += 1
                return rasters[key]
            rendered += 1
            raster = render_fn(svg, width, height)
            rasters[key] = raster
            return raster

        counted.search_renderer = getattr(render_fn, 'search_renderer',
            render_fn.__module__+'.'+render_fn.__qualname__)

        return _register_steps(model['parameters'], model['geometry_count'],
            model['build'], model['valid'], image, counted, error_fn, source+'_'+name,
            max_evaluations=render_budget, allow_portfolio=False, on_candidate=observed,
            reconsider_after=0)

    def attempt(name, phase, allowance):
        nonlocal turn
        state = states[name]
        before = rendered
        began = time.monotonic()
        previous = vector_quality_score(state['quality']) if state['quality'] else None
        # Cache hits and invalid probes must not monopolize a scheduling turn.
        steps = 0
        while rendered-before < allowance and rendered < render_budget and not expired():
            try:
                next(jobs[name])
            except StopIteration:
                state['exhausted'] = True
                state['stop_reason'] = 'schedule_exhausted'
                break
            steps += 1
            if best_quality and preferred_quality(best_quality):
                break
            if state['stale_trials'] >= state['patience']:
                # One full coordinate sweep without shape or pixel progress
                # is evidence to change models, rather than repeat tiny steps.
                state['exhausted'] = True
                state['stop_reason'] = 'shape_stagnation'
                break
            if steps >= max(8, allowance*4):
                break
        quality = state['quality']
        score = vector_quality_score(quality) if quality else None
        if previous is None:
            previous = state['initial_score']
        gain = (max(0., previous-score)/max(abs(previous), 1e-9)
                if previous is not None and score is not None else 0.)
        state['gain'] = gain
        state['stale'] = state['stale']+1 if previous is not None and gain < .01 else 0
        if quality and quality['passed'] and state['stale'] >= 2:
            state['exhausted'] = True
            state['stop_reason'] = 'quality_plateau'
        state['turns'] += 1
        state['last_turn'] = turn
        turn += 1
        record = dict(model=name, phase=phase, renderings=rendered-before,
            seconds=time.monotonic()-began, semantic_passed=state['best'] is not None,
            pixel_passed=bool(quality and quality['passed']),
            error=state['best']['error'] if state['best'] else None,
            quality_score=score, relative_gain=gain, stagnant_turns=state['stale'],
            remembered_trials=state['trials'], semantic_rejections=state['rejected'],
            stagnant_trials=state['stale_trials'],
            exhausted=state['exhausted'], stop_reason=state['stop_reason'])
        attempts.append(record)
        progress(source, event='form_model_attempt', **record)

    def choose(active):
        oldest = min(active, key=lambda name: states[name]['last_turn'])
        # Retain exploration even when one initially promising model stalls.
        if turn-states[oldest]['last_turn'] >= 2*len(active):
            return oldest
        def priority(name):
            state = states[name]
            quality = state['quality']
            score = vector_quality_score(quality) if quality else math.inf
            return (not bool(quality and quality['passed']),
                    score*(1+.25*state['stale'])/(1+4*state['gain']),
                    state['last_turn'])
        return min(active, key=priority)

    try:
        for model in models:
            name = model['name']
            jobs[name] = make_job(model)
        for model in models:
            if expired() or rendered >= render_budget:
                break
            attempt(model['name'], 'probe', min(probe_renderings, render_budget-rendered))
            if best_quality and preferred_quality(best_quality):
                stop = 'satisfactory'
                break
        else:
            while rendered < render_budget and not expired():
                active = [name for name, state in states.items() if not state['exhausted']]
                if not active:
                    break
                attempt(choose(active), 'refine', min(probe_renderings, render_budget-rendered))
                if best_quality and preferred_quality(best_quality):
                    stop = 'satisfactory'
                    break
    finally:
        for job in jobs.values():
            job.close()
    if stop != 'satisfactory':
        if expired():
            stop = session.reason()
        elif rendered >= render_budget:
            stop = 'render_limit'
    report = dict(attempts=attempts, selected_model=best['model'] if best else None,
        renderings=rendered, render_budget=render_budget, seconds=time.monotonic()-start,
        stop_reason=stop, satisfactory=bool(best_quality and best_quality['passed']),
        selection_policy='quality_progress_with_exploration',
        remembered_trials=sum(state['trials'] for state in states.values()),
        duplicate_renderings_avoided=cache_hits)
    progress(source, event='form_model_comparison_finished', **report)
    if best is not None:
        best['model_comparison'] = report
        best['evaluations'] = rendered
        if session:
            best['search_control'] = dict(stop_reason=stop, **session.report())
    return best
