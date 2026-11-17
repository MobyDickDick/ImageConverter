"""Shared expansion frontier for CLI, uploaded templates and GUI recovery.

The best deliverable and the exploration branch are separate. Failed branches
may be simplified or rebuilt without publishing their temporary regressions.
All work consumes the existing image session; nothing gets a fresh deadline.
"""
from __future__ import annotations

from collections import deque
from xml.etree import ElementTree as ET

import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import (
    candidate_identity, current_search, pixel_quality, raster_identity, vector_quality_score, vector_candidate_quality,
)
from src.iCCModules.imageCompositeConverterSearchPortfolio import progress, proposal_rng


def continue_native_search(svg, image, render_fn, *, assertions=None, acceptance_fn=None,
                           stop_fn=None, color_order='BGR', on_candidate=None, description=''):
    from src.iCCModules.imageCompositeConverterVectorPolish import polish_generated_svg
    from src.iCCModules.imageCompositeConverterFallbackGroups import canvas
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions
    session = current_search()
    if session is None or session.time_reason():
        return None
    h, w = image.shape[:2]
    source_key = (raster_identity(image), repr(assertions), color_order)
    state = session.native_frontiers.setdefault(source_key, dict(visited=set(), branches=set(), turns=0, sweeps={}))
    initial, _ = session.render_candidate(image, svg, render_fn, w, h)
    if initial is None:
        return None
    error = lambda pixels: float(np.square(image.astype(float)-pixels.astype(float)).mean()/255**2)
    def rank(raster, candidate):
        quality = vector_candidate_quality(image, raster, candidate)
        incomplete = False
        if assertions and assertions.get('objects'):
            from src.iCCModules.imageCompositeConverterRepresentation import validate_object_limits
            try:
                validate_object_limits(candidate, assertions['objects'], symbol_strokes=assertions.get('symbol_strokes', 0))
            except ValueError:
                incomplete = True
        return (incomplete, not quality['passed'], vector_quality_score(quality))
    best = dict(svg=svg, rendered=initial, error=error(initial), rank=rank(initial, svg))
    initial_error = best['error']
    initial_rank = best['rank']
    pending = deque([(svg, 0)])
    reports = []
    alternatives = []
    phase = 0
    reason = 'search_space_exhausted'

    def finished():
        return session.time_reason() or (stop_fn is not None and stop_fn())

    def passed(candidate):
        try:
            validate_svg_assertions(candidate, assertions)
            if acceptance_fn:
                return bool(acceptance_fn(candidate))
            raster, _ = session.render_candidate(image, candidate, render_fn, w, h)
            return bool(raster is not None and pixel_quality(image, raster)['passed'])
        except ValueError:
            return False

    def remember(result, row):
        if row.get('rejection') in {'protected_existing_paint', 'protected_group_part', 'group_part_evidence'}:
            return
        consider(dict(result, rendered=result['rendered'][:, :, ::-1].copy()) if color_order == 'RGB' else result)
        # A bounded beam can cross a worse intermediate state, e.g. removing
        # an opaque patch before replacing the underlying wrong object.
        identity = candidate_identity(result['svg'])
        if (row.get('rejection') not in {'protected_existing_paint', 'protected_group_part', 'group_part_evidence'}
                and result['error'] <= max(best['error']*1.5, best['error']+.001)
                and identity not in state['branches']):
            state['branches'].add(identity)
            alternatives.append(result)

    def consider(result):
        nonlocal best
        if result is None:
            return
        raster = result['rendered']
        actual = error(raster)
        ordering = rank(raster, result['svg'])
        if ordering < best['rank'] or passed(result['svg']):
            best = dict(result, rendered=raster, error=actual, rank=ordering)
            if on_candidate:
                on_candidate(best)

    # Moving/removing pieces of an old SVG cannot introduce a missing object
    # relationship. Share the fresh converter's *whole-scene* proposals here,
    # for every registered model, rather than deriving every template from its
    # original construction. Each image gets at most one such reconstruction
    # sweep and all fitters consume the same existing deadline and render cache.
    if description and not state.get('reconstruction_tried') and not finished() and not passed(svg):
        from src.iCCModules.imageCompositeConverterNonCompositeRuntime import scene_reconstruction_fitters
        from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions
        full_assertions = description_assertions(description)
        state['reconstruction_tried'] = True
        bgr = image if color_order == 'BGR' else image[:, :, ::-1].copy()
        def render_bgr(candidate, width, height):
            pixels = render_fn(candidate, width, height)
            return pixels if pixels is None or color_order == 'BGR' else pixels[:, :, ::-1].copy()
        for fitter, family in scene_reconstruction_fitters():
            if finished():
                break
            fitted = fitter(w, h, description=description, image=bgr, render_fn=render_bgr,
                error_fn=lambda a, b: float(np.square(a.astype(float)-b.astype(float)).mean()/255**2))
            if fitted is None:
                continue
            try:
                validate_svg_assertions(fitted['svg'], full_assertions)
            except ValueError:
                continue
            if not pixel_quality(bgr, fitted['rendered'])['passed']:
                continue
            progress('native_svg_search', event='scene_reconstructed', family=family, **session.report())
            raster = fitted['rendered'] if color_order == 'BGR' else fitted['rendered'][:, :, ::-1].copy()
            consider(dict(fitted, rendered=raster))
            if passed(best['svg']):
                break
        if passed(best['svg']):
            reason = 'satisfactory'
            pending.clear()
        else:
            pending = deque([(best['svg'], 0)])

    while pending and not finished():
        branch, level = pending.popleft()
        identity = (candidate_identity(branch), level)
        if identity in state['visited']:
            continue
        state['sweeps'][identity] = state['sweeps'].get(identity, 0)+1
        state['turns'] += 1
        if level > phase:
            phase = level
            progress('native_svg_search', event='search_expanded', level=phase,
                     operations=('remove', 'move_object', 'remove_pair', 'layer_order', 'rebuild'),
                     **session.report())
        result = polish_generated_svg(branch, image, render_fn, assertions=assertions,
            color_order=color_order, acceptance_fn=acceptance_fn, stop_fn=stop_fn,
            exploration_level=level, on_alternative=remember)
        if result:
            reports.append(result.get('structure_search') or {})
            consider(result)
        report = (result or {}).get('structure_search') or {}
        limited = report.get('stop_reason') == 'probe_limit'
        if limited and state['sweeps'][identity] >= 4:
            state['bounded'] = True
        if not limited or state['sweeps'][identity] >= 4:
            state['visited'].add(identity)
        if finished() or passed(best['svg']):
            reason = 'satisfactory' if not session.time_reason() else 'time_limit'
            break
        if result and result['improved'] and candidate_identity(best['svg']) != candidate_identity(branch):
            # Progress does not buy endless turns inside the same construction
            # space. Carry the better draft into the next, broader edit family.
            pending.append((best['svg'], min(3, level+1)))
        elif level < 3:
            pending.append((branch, level+1))
        if limited and identity not in state['visited']:
            pending.append((branch, level))
        if level >= 2:
            if not state.get('rebuilt'):
                state['rebuilt'] = True
                bgr = image if color_order == 'BGR' else image[:, :, ::-1].copy()
                pending.append((ET.tostring(canvas(bgr), encoding='unicode'), 2))
            # Branch only after trying destructive edits; reserve earlier
            # turns for broad reconstruction rather than near-identical lines.
            available = sorted(alternatives, key=lambda c: c['error'])
            alternatives.clear()
            selected = available[:4]
            rng = proposal_rng('native_frontier', [candidate_identity(branch), level, state['sweeps'][identity]])
            if rng is not None and len(available) > 4:
                # Keep two best anchors, reserve two slots for other plausible
                # constructions instead of always visiting the same top four.
                selected = available[:2]+rng.sample(available[2:], 2)
            for alternative in selected:
                pending.append((alternative['svg'], min(3, level)))
    if session.time_reason():
        reason = 'time_limit'
    elif stop_fn is not None and stop_fn():
        reason = 'satisfactory'
    elif state.get('bounded') and reason == 'search_space_exhausted':
        reason = 'construction_frontier_exhausted'
    control = dict(stop_reason=reason, exploration_level=phase, construction_turns=state['turns'],
                   distinct_states=len(state['visited']), **session.report())
    progress('native_svg_search', event='native_search_finished', **control)
    return dict(best, initial_error=initial_error, improved=best['rank'] < initial_rank,
                evaluations=session.evaluations, source='native_expanding_search',
                search_control=control, structure_search=dict(rounds=reports, exploration_level=phase))
