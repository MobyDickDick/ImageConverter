"""Bounded alternative searches, live evidence, and reusable strategy statistics.

History changes strategy ordering only. Saved SVGs/parameters are evidence, never
templates; semantic-only runs do not read history. Pixel passes are explicitly
provisional until the caller's semantic checks have completed.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import math
from pathlib import Path
import random
import time

import numpy as np
from src.iCCModules.imageCompositeConverterAdaptiveSearch import (
    ImageSearch, SearchPolicy, SearchRun, current_search, image_search,pixel_quality,
)

_SETTINGS = ContextVar('conversion_search_settings', default=None)


@contextmanager
def search_configuration(*, mode='legacy', seed=0, budget=384, directory=None, allow_memory=False,
                         adaptive=False, seconds=60., max_seconds=120.):
    if mode not in {'legacy', 'portfolio'} or not 32 <= budget <= 10000:
        raise ValueError('Search mode or render budget is invalid')
    policy = SearchPolicy(seconds=seconds,max_seconds=max_seconds)
    token = _SETTINGS.set(dict(mode=mode, seed=int(seed), budget=int(budget),
                               directory=Path(directory) if directory else None,
                               allow_memory=allow_memory,adaptive=adaptive and mode=='portfolio',
                               policy=policy,images={}))
    try:
        yield
    finally:
        _SETTINGS.reset(token)


def settings():
    return _SETTINGS.get()


def configured_image_search(identity):
    config = settings()
    if not config or not config['adaptive']:
        return image_search(None)
    session = config['images'].setdefault(str(identity),ImageSearch(config['policy'],
        emit=lambda **values: progress(str(identity),**values)))
    return image_search(session)


def validated_result(result, image):
    """Call only after the model's full semantic checks have accepted its SVG."""
    session = current_search()
    if session is None:
        return False
    quality = pixel_quality(image,result['rendered'])
    if not quality or not quality['passed']:
        return False
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import svg_identity,raster_identity
    if (svg_identity(result['svg']),raster_identity(image)) not in session.validated:
        session.validate(result,image)
        progress(result.get('source','model'),event='candidate_satisfactory',**session.report())
    return True


def progress(source, **values):
    config = settings()
    if not config or config['mode'] != 'portfolio':
        return
    record = dict(source=source, **values)
    print('[Search] '+json.dumps(record, ensure_ascii=False, allow_nan=False), flush=True)
    if config['directory']:
        config['directory'].mkdir(parents=True, exist_ok=True)
        with (config['directory']/'progress.jsonl').open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False)+'\n')


def _read_memory(directory):
    try:
        data = json.loads((directory/'strategy_memory.json').read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def ranked_models(models):
    config = settings()
    if not config or config['mode'] != 'portfolio':
        return list(models)
    ordered = list(models)
    random.Random(config['seed']).shuffle(ordered)
    memory = _read_memory(config['directory']) if config['directory'] and config['allow_memory'] else {}
    def score(model):
        value = memory.get(str(model), 0)
        return value if isinstance(value, (int, float)) and math.isfinite(value) else 0
    return sorted(ordered, key=lambda model: -score(model))


def store_validated_variant(result, *, image, description, model, quality):
    config = settings()
    if not config or config['mode'] != 'portfolio' or not config['directory']:
        return
    identity = hashlib.sha256(str(np.asarray(image).shape).encode()+np.asarray(image).tobytes()+description.encode()).hexdigest()
    target = config['directory']/'validated'/identity
    target.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(result['svg'].encode()).hexdigest()
    (target/(digest+'.svg')).write_text(result['svg'], encoding='utf-8')
    record = dict(schema_version='validated_search_variant_v1', model=str(model), seed=config['seed'],
                  svg_sha256=digest, description=description, parameters=result['parameters'],
                  dimensions=list(np.asarray(image).shape[:2]), local_semantics_passed=True,
                  strict_pixel_gate=quality, validation_scope='described_short_label_disk_only')
    (target/(digest+'.json')).write_text(json.dumps(record, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    if config['allow_memory'] and quality and quality['passed']:
        memory = _read_memory(config['directory'])
        successful = [str(model)]
        strategy = (result.get('search') or {}).get('winning_strategy')
        if strategy:
            successful.append(strategy)
        for name in successful:
            old = memory.get(name, 0)
            memory[name] = (old if isinstance(old, (int,float)) and math.isfinite(old) else 0)+1
        (config['directory']/'strategy_memory.json').write_text(json.dumps(memory, indent=2)+'\n', encoding='utf-8')


def explore_parameters(parameters, geometry_count, measure, incumbent, *, source, image, satisfactory_fn=None):
    """Explore different search trajectories under one additional render budget.

    ``measure`` also applies the model's validity rules and custom loss. A probe
    can replace the incumbent only if it improves the search loss AND does not
    worsen the caller's measured error. Repeated vectors share one cache.
    """
    config = settings()
    if not config or config['mode'] != 'portfolio':
        return parameters, incumbent, None
    if config['adaptive'] and current_search() is not None:
        return _explore_adaptive(parameters,geometry_count,measure,incumbent,
                                 source=source,image=image,satisfactory_fn=satisfactory_fn)
    identity = hashlib.sha256(source.encode()+np.asarray(image).tobytes()+incumbent[2].encode()).hexdigest()
    rng = random.Random(config['seed'] ^ int(identity[:16], 16))
    paths = ['reverse_coordinates', 'shuffled_coordinates', 'joint_restart']
    rng.shuffle(paths)
    directory = config['directory']
    memory = _read_memory(directory) if directory and config['allow_memory'] else {}
    paths.sort(key=lambda name: -float(memory.get(name, 0)) if isinstance(memory.get(name, 0), (int, float))
               and math.isfinite(memory.get(name, 0)) else 0)
    best_p, best = parameters.copy(), incumbent
    seen = {tuple(np.round(best_p, 8))}
    renders = 0
    winning_strategy = None
    records = []
    started = time.monotonic()
    # Each strategy receives a reserved share, so a long first attempt cannot
    # silently starve all other approaches. These are render attempts, not time.
    quota = config['budget']//len(paths)
    for strategy in paths:
        progress(source, event='strategy_started', strategy=strategy, proposals=renders,
                 budget=config['budget'], seed=config['seed'], best_error=best[1])
        local_p, local = parameters.copy(), incumbent
        used = 0
        order = list(range(len(parameters)))
        if strategy == 'reverse_coordinates':
            order.reverse()
        else:
            rng.shuffle(order)
        probes = []
        if strategy == 'joint_restart':
            for _ in range(min(24, quota//3)):
                probe = parameters.copy()
                indices = rng.sample(order, min(3, len(order)))
                for index in indices:
                    probe[index] += rng.choice((-1, 1))*rng.choice((.5, 1., 2.))*(4 if index >= geometry_count else 1)
                probes.append(probe)
        # Rebuild coordinate proposals around the evolving local candidate.
        schedule = [(step, index, sign) for step in (1., .5, .25, .125)
                    for index in order for sign in (-1, 1)]
        for proposal in [*probes, *schedule]:
            if used >= quota:
                break
            if isinstance(proposal, tuple):
                step, index, sign = proposal
                probe = local_p.copy()
                probe[index] += sign*step*(4 if index >= geometry_count else 1)
            else:
                probe = proposal
            key = tuple(np.round(probe, 8))
            if key in seen:
                continue
            seen.add(key)
            used += 1
            renders += 1
            measured = measure(probe)
            if measured is None:
                continue
            if measured[0] < local[0]-1e-9:
                local_p, local = probe, measured
            if measured[0] < best[0]-1e-9 and measured[1] <= best[1]+1e-9:
                best_p, best = probe.copy(), measured
                winning_strategy = strategy
            if used % 32 == 0:
                progress(source, event='searching', strategy=strategy, proposals=renders,
                         budget=config['budget'], best_error=best[1])
        improved = local[0] < incumbent[0]-1e-9 and local[1] <= incumbent[1]+1e-9
        record = dict(strategy=strategy, proposals=used, error=local[1], improved=improved)
        records.append(record)
        if directory:
            target = directory/identity
            target.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256(local[2].encode()).hexdigest()
            (target/(digest+'.svg')).write_text(local[2], encoding='utf-8')
            # Every attempt remains evidence, including failures and ties.
            record.update(svg=digest+'.svg', parameters=local_p.tolist(),
                          validation='search_loss_only_pending_semantic_and_pixel_gates')
            (target/(str(config['seed'])+'-'+strategy+'.json')).write_text(
                json.dumps(record, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        progress(source, event='strategy_finished', **{k: v for k, v in record.items()
                 if k not in {'parameters', 'svg'}}, best_error=best[1])
    return best_p, best, dict(seed=config['seed'], additional_evaluations=renders,
                              winning_strategy=winning_strategy,
                              budget=config['budget'], attempts=records,
                              elapsed_seconds=round(time.monotonic()-started, 3))


def _explore_adaptive(parameters, geometry_count, measure, incumbent, *, source, image, satisfactory_fn):
    config,session = settings(),current_search()
    identity = hashlib.sha256(source.encode()+np.asarray(image).tobytes()+incumbent[2].encode()).hexdigest()
    rng = random.Random(config['seed'] ^ int(identity[:16],16))
    paths = ['reverse_coordinates','shuffled_coordinates','joint_restart']
    rng.shuffle(paths)
    best_p,best = parameters.copy(),incumbent
    seen = {tuple(np.round(best_p,8))}
    monitor = SearchRun(session,config['budget'],source=source)
    monitor.anchor = incumbent[0]
    records = {name:dict(strategy=name,proposals=0,error=incumbent[1],improved=False) for name in paths}
    orders = {name:list(range(len(parameters))) for name in paths}
    orders['reverse_coordinates'].reverse()
    for name in paths:
        if name != 'reverse_coordinates':
            rng.shuffle(orders[name])
    cursors = dict.fromkeys(paths,0)
    batch = max(4,min(32,config['budget']//3))
    tried = set()
    winning = None
    reason = 'satisfactory' if satisfactory_fn and satisfactory_fn(best_p,best) else None
    generated = 0
    started = session.elapsed
    while reason is None and generated < monitor.maximum*8:
        before_cycle = monitor.proposals
        for strategy in paths:
            reason = monitor.reason(alternatives_tried=len(tried)==len(paths))
            if reason:
                break
            tried.add(strategy)
            progress(source,event='strategy_started',strategy=strategy,proposals=monitor.proposals,
                     budget=monitor.limit,seed=config['seed'],best_error=best[1])
            used = 0
            slice_generated = 0
            while used < batch and slice_generated < batch*8 and generated < monitor.maximum*8:
                reason = monitor.reason(alternatives_tried=len(tried)==len(paths))
                if reason:
                    break
                cursor = cursors[strategy]
                cursors[strategy] += 1
                generated += 1
                slice_generated += 1
                probe = best_p.copy()
                order = orders[strategy]
                if strategy == 'joint_restart':
                    # Continue proposing coupled changes, at several scales,
                    # when one finite coordinate schedule has been exhausted.
                    step = (.125,.25,.5,1.,2.,4.)[(cursor//8)%6]
                    for index in rng.sample(order,min(3,len(order))):
                        probe[index] += rng.choice((-1,1))*step*(4 if index>=geometry_count else 1)
                else:
                    index = order[(cursor//2)%len(order)]
                    step = (1.,.5,.25,.125,.0625,2.)[(cursor//(2*len(order)))%6]
                    probe[index] += (-1 if cursor%2==0 else 1)*step*(4 if index>=geometry_count else 1)
                key = tuple(np.round(probe,8))
                if key in seen:
                    continue
                seen.add(key)
                used += 1
                measured = measure(probe)
                if measured is not None and measured[0] < best[0]-1e-9 and measured[1] <= best[1]+1e-9:
                    best_p,best,winning = probe.copy(),measured,strategy
                    session.observe(best[1],evaluation=False)
                    records[strategy]['improved'] = True
                # Only admissible improvements can buy additional work.
                monitor.observe(best[0])
                records[strategy]['proposals'] += 1
                records[strategy]['error'] = best[1]
                if satisfactory_fn and satisfactory_fn(best_p,best):
                    reason = 'satisfactory'
                    break
            progress(source,event='strategy_finished',**records[strategy],best_error=best[1])
            if reason:
                break
        if reason is None:
            reason = monitor.reason(alternatives_tried=len(tried)==len(paths))
        if reason is None and before_cycle == monitor.proposals:
            reason = 'search_exhausted'
    reason = reason or 'search_exhausted'
    if config['directory']:
        target = config['directory']/identity
        target.mkdir(parents=True,exist_ok=True)
        digest = hashlib.sha256(best[2].encode()).hexdigest()
        (target/(digest+'.svg')).write_text(best[2],encoding='utf-8')
        for record in records.values():
            (target/(str(config['seed'])+'-'+record['strategy']+'.json')).write_text(json.dumps(
                {**record,'stop_reason':reason,'parameters':best_p.tolist(),'svg':digest+'.svg',
                 'validation':'search_loss_only_pending_semantic_and_pixel_gates'},indent=2,allow_nan=False)+'\n',encoding='utf-8')
    report = dict(seed=config['seed'],additional_evaluations=monitor.proposals,
        winning_strategy=winning,budget=config['budget'],effective_budget=monitor.limit,
        max_budget=monitor.maximum,budget_extensions=monitor.extensions,stop_reason=reason,
        attempts=list(records.values()),elapsed_seconds=round(session.elapsed-started,6))
    progress(source,event='search_finished',stop_reason=reason,proposals=monitor.proposals,
             budget=monitor.limit,best_error=best[1])
    return best_p,best,report
