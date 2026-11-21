"""Seeded registration of the inventory already declared by the description.

Only paint and transforms of those IR elements may change. Restarts explore
different basins; they never add raster-derived objects or random output shapes.
"""
from __future__ import annotations

import copy
import math
import re
import zlib

import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import (
    candidate_identity, current_search, pixel_quality, preferred_quality, vector_quality_score,
)
from src.iCCModules.imageCompositeConverterCanvas import contain_svg
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterSearchPortfolio import proposal_rng, progress, settings


def register_description_ir(geometry_ir, *, image, description, svg_fn, render_fn, error_fn,
                            max_evaluations=None, seed=None):
    from src.iCCModules.imageCompositeConverterGeometryIrOptimizer import transformGeometryIrImpl

    h, w = image.shape[:2]
    assertions = description_assertions(description)
    session, config = current_search(), settings()
    budget = max_evaluations if max_evaluations is not None else (config or {}).get('budget', 384)
    effective_seed = seed if seed is not None else (session.search_seed if session and session.search_seed is not None
                                                  else (config or {}).get('seed', 0))
    rng = proposal_rng('description_ir_registration', geometry_ir, seed=effective_seed)
    cache = {}
    evaluations, rejections, cache_hits, restarts, accepted = 0, 0, 0, 0, 0
    best, initial_error = None, None
    stop_reason = 'proposal_limit'
    trace = []

    def stopped():
        nonlocal stop_reason
        if evaluations >= budget:
            stop_reason = 'proposal_limit'
            return True
        if session and session.reason():
            stop_reason = session.reason()
            return True
        return False

    def measure(ir):
        nonlocal evaluations, rejections, cache_hits, best, initial_error, accepted
        try:
            svg = contain_svg(svg_fn(ir), w, h)
            identity = candidate_identity(svg)
            if identity in cache:
                cache_hits += 1
                cached = cache[identity]
                if cached is None:
                    return None
                metadata, shape, data = cached
                return dict(metadata, rendered=np.frombuffer(zlib.decompress(data), dtype=np.uint8).reshape(shape))
            validate_svg_assertions(svg, assertions)
        except (ValueError, SyntaxError):
            rejections += 1
            return None
        if stopped():
            return None
        # Trace the real SVG render requests, including failed trial branches.
        if session:
            raster, fresh = session.render_candidate(image, svg, render_fn, w, h)
        else:
            raster, fresh = render_fn(svg, w, h), True
        evaluations += int(fresh)
        if fresh:
            trace.append(identity)
        if raster is None:
            cache[identity] = None
            return None
        error = float(error_fn(raster))
        if not math.isfinite(error):
            cache[identity] = None
            return None
        quality = pixel_quality(image, raster)
        # A tiny patch on a white canvas cannot win by suppressing foreground.
        score = vector_quality_score(quality) + quality['foreground_mse']
        rank = (not quality['passed'], score)
        result = dict(geometry_ir=copy.deepcopy(ir), svg=svg, rendered=raster, error=error,
                      quality=quality, rank=rank)
        cache[identity] = ({k:v for k,v in result.items() if k!='rendered'},
                           raster.shape, zlib.compress(raster.tobytes(), 1))
        if initial_error is None:
            initial_error = error
        if session:
            session.evaluations += int(fresh)
            session.measured(svg, float(quality['normalized_mse']), source='description_registration',
                scope='full_scene' if session.is_reference(image) else 'intermediate', valid=True,
                passed=quality['passed'])
        if best is None or rank < best['rank']:
            best, accepted = result, accepted+1
        return result

    def paints(ir):
        return [(i, key) for i, e in enumerate(ir) for key, value in e.items()
                if (key in {'fill', 'stroke', 'color'} or key.endswith(('_fill', '_stroke')))
                and isinstance(value, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', value)]

    def calibrate(ir):
        """Fit declared paint channels from their own rendered coverage masks."""
        current = measure(ir)
        fields = paints(ir)
        rng.shuffle(fields)
        # Remove a wrong default surface paint before estimating its rim;
        # otherwise antialiased red can be "compensated" with a green rim.
        fields.sort(key=lambda pair: 'stroke' in pair[1])
        for i, key in fields:
            if current is None or stopped():
                break
            low, high = copy.deepcopy(current['geometry_ir']), copy.deepcopy(current['geometry_ir'])
            low[i][key], high[i][key] = '#000000', '#ffffff'
            black, white = measure(low), measure(high)
            if black is None or white is None:
                continue
            alpha = (white['rendered'].astype(float)-black['rendered'].astype(float))/255.
            denominator = np.square(alpha).sum(axis=(0, 1))
            if np.min(denominator) < .1:
                continue
            value = (alpha*(image.astype(float)-black['rendered'])).sum(axis=(0, 1))/denominator
            color = '#'+''.join(f'{int(v):02x}' for v in np.clip(np.rint(value[::-1]), 0, 255))
            colors = [color]
            coverage = alpha.mean(axis=2) > .5
            if coverage.any():
                observed = np.median(image[coverage], axis=0)
                colors.append('#'+''.join(f'{int(v):02x}' for v in observed[::-1]))
            if 'stroke' in key:
                background = np.median(np.concatenate((image[0],image[-1],image[:,0],image[:,-1])),axis=0)
                foreground = image[np.max(abs(image.astype(float)-background),axis=2)>25]
                if len(foreground):
                    observed = np.percentile(foreground,20,axis=0)
                    colors.append('#'+''.join(f'{int(v):02x}' for v in observed[::-1]))
            probes = [current, black, white]
            for color in dict.fromkeys(colors):
                candidate = copy.deepcopy(current['geometry_ir'])
                candidate[i][key] = color
                probes.append(measure(candidate))
            current = min((r for r in probes if r is not None),
                          key=lambda r:r['rank'])
        return current

    base = copy.deepcopy(geometry_ir)
    # Semantic seeds use normalized width/height. A named square must first
    # become square in actual pixel coordinates, with its own parts transformed
    # together. Later candidate validation protects all other named forms.
    square_claim = bool(assertions.get('objects', {}).get('square'))
    equal_axes = square_claim or bool(assertions.get('objects', {}).get('circle'))
    for i, element in enumerate(base):
        square_body = square_claim and 'body_bbox' in element
        square_rect = square_claim and not assertions.get('objects', {}).get('rect') and element.get('kind') in {'RectBorder','ColorPatch'}
        true_circle = assertions.get('objects', {}).get('circle') and element.get('kind') == 'CircleBackground'
        bbox = element.get('body_bbox' if square_body else 'bbox')
        if (square_body or square_rect or true_circle) and isinstance(bbox, list) and len(bbox) == 4 and bbox[3] > 0:
            ratio = bbox[2]*w/(bbox[3]*h)
            if ratio > 0:
                base[i] = transformGeometryIrImpl([element], scale_y=ratio)[0]

    initial = calibrate(base)
    beam = [initial] if initial is not None else []
    # Spatial restarts are proposals of the same declared objects. They are
    # explored even when the intervening step is worse than the incumbent.
    for _ in range(8):
        if stopped() or (best and preferred_quality(best['quality'])):
            break
        sx = rng.uniform(.55, 1.5)
        sy = sx if equal_axes else rng.uniform(.55, 1.5)
        candidate = transformGeometryIrImpl(base, translate_x=rng.uniform(-.3, .3),
            translate_y=rng.uniform(-.3, .3), scale_x=sx, scale_y=sy,
            stroke_scale=rng.uniform(.55, 1.6))
        restart = calibrate(candidate)
        restarts += 1
        if restart:
            beam.append(restart)
    beam = sorted(beam, key=lambda r: r['rank'])[:4]

    for step in (.12, .06, .025, .01, .004):
        if stopped() or not beam or (best and preferred_quality(best['quality'])):
            break
        for _ in range(3):
            improved = False
            following = []
            for branch in beam:
                current = branch
                # Whole-scene and per-element probes permit relative placement
                # without changing element identity, topology or ordering.
                targets = [None]+list(range(len(base))) if len(base)>1 else [None]
                operations = [(target, axis, sign) for target in targets
                              for axis in ('x', 'y', 'scale', 'stroke') for sign in (-1, 1)]
                rng.shuffle(operations)
                for target, axis, sign in operations:
                    if stopped():
                        break
                    values = dict(translate_x=sign*step if axis=='x' else 0.,
                                  translate_y=sign*step if axis=='y' else 0.,
                                  scale_x=1+sign*step if axis=='scale' else 1.,
                                  scale_y=1+sign*step if axis=='scale' else 1.,
                                  stroke_scale=1+sign*step*2 if axis=='stroke' else 1.)
                    candidate = copy.deepcopy(current['geometry_ir'])
                    if target is None:
                        candidate = transformGeometryIrImpl(candidate, **values)
                    else:
                        candidate[target] = transformGeometryIrImpl([candidate[target]], **values)[0]
                    result = measure(candidate)
                    if result and result['rank'] < current['rank']:
                        current, improved = result, True
                following.append(current)
            beam = sorted(following, key=lambda r: r['rank'])[:4]
            if not improved:
                break
        if best and not stopped():
            calibrate(best['geometry_ir'])
    if best and preferred_quality(best['quality']):
        stop_reason = 'quality_target_reached'
    elif best is None and not stopped():
        stop_reason = 'no_valid_candidate'
    elif not stopped():
        stop_reason = 'parameter_stagnation'
    report = dict(mode='description_geometry_ir_multistart', evaluations=evaluations,
                  rejected_candidates=rejections, cache_hits=cache_hits, restarts=restarts,
                  accepted=accepted, stop_reason=stop_reason, candidate_identities=trace)
    progress('description_ir_registration', event='registration_finished',
             **{k:v for k,v in report.items() if k!='candidate_identities'})
    if best is None:
        return dict(report, no_valid_candidate=True, geometry_ir=base, rendered=None,
                    initial_error=float('inf'), final_error=float('inf'))
    return dict(report, geometry_ir=best['geometry_ir'], svg=best['svg'], rendered=best['rendered'],
                quality=best['quality'], initial_error=initial_error, final_error=best['error'],
                parameters={}, steps=[])
