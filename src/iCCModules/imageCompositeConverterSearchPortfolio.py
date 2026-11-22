"""Bounded alternative searches, live evidence, and reusable strategy statistics.

History changes strategy ordering only. Saved SVGs/parameters are evidence, never
templates; semantic-only runs do not read strategy history. The explicitly
selected primitive population search may resume its own source-bound frontier.
Pixel passes are explicitly
provisional until the caller's semantic checks have completed.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import hashlib
import json
import math
from pathlib import Path
import random
import time

import numpy as np
from src.iCCModules.imageCompositeConverterAdaptiveSearch import (
    ImageSearch, SearchPolicy, current_search, image_search,pixel_quality,
)

_SETTINGS = ContextVar('conversion_search_settings', default=None)


@contextmanager
def search_configuration(*, mode='legacy', seed=0, budget=384, directory=None, allow_memory=False,
                         adaptive=False, seconds=60., max_seconds=120., isolate=False,
                         disabled_bots=(), component_observation=True, neural_model=None, minimum_seconds=0.,
                         handoff=None, primitive_exploration=False, primitive_memory=None):
    if mode not in {'legacy', 'portfolio'} or not 32 <= budget <= (1000000 if primitive_exploration else 10000):
        raise ValueError('Search mode or render budget is invalid')
    policy = SearchPolicy(seconds=seconds,max_seconds=max_seconds,minimum_seconds=min(minimum_seconds,seconds))
    from src.iCCModules.imageCompositeConverterComponents import registry
    registry(disabled_bots)
    if disabled_bots and (mode != 'portfolio' or not adaptive):
        raise ValueError('Bot switches require the adaptive portfolio')
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError('Seed must be an unsigned 64-bit integer')
    config = dict(mode=mode, seed=seed, budget=int(budget),
                               directory=Path(directory) if directory else None,
                               allow_memory=allow_memory,adaptive=adaptive and mode=='portfolio',
                               policy=policy,images={},isolate=isolate,
                               disabled_bots=tuple(sorted(set(disabled_bots))),
                               component_observation=bool(component_observation),
                               neural_model=str(Path(neural_model).resolve()) if neural_model else None,
                               neural_observations=[], handoff=handoff,
                               primitive_exploration=bool(primitive_exploration),
                               primitive_memory=Path(primitive_memory) if primitive_memory else None)
    token = _SETTINGS.set(config)
    try:
        yield
    finally:
        if config.get('journal'):
            config['journal'].close()
        _SETTINGS.reset(token)


def settings():
    return _SETTINGS.get()


def proposal_rng(context, identity, *, seed=None):
    """Stable independent random streams; never depend on global RNG or paths.

    A missing search configuration preserves fixed-policy callers. An explicit seed also
    supports generators outside a configured search (including regression QA).
    """
    config = settings()
    if seed is None:
        session = current_search()
        if session is not None and session.search_seed is not None:
            seed = session.search_seed
        elif config:
            seed = config['seed']
        else:
            return None
    digest = hashlib.sha256(json.dumps([int(seed), context, identity],
        ensure_ascii=False, separators=(',', ':')).encode('utf-8')).digest()
    return random.Random(int.from_bytes(digest, 'big'))


@contextmanager
def configured_image_search(identity):
    config = settings()
    if not config:
        with image_search(current_search()) as session:
            yield session
        return
    session = config['images'].get(str(identity))
    if session is None and config.get('handoff'):
        state = json.loads(Path(config['handoff']).read_text(encoding='utf-8'))
        if hashlib.sha256(Path(identity).read_bytes()).hexdigest() != state['source_sha256']:
            raise ValueError('Search context source changed')
        if config['seed'] != state['seed'] or config['budget'] != state['render_budget']:
            raise ValueError('Search context settings changed')
        session = ImageSearch.from_handoff(state, emit=lambda **values: progress(str(identity), **values))
        config['return_handoff'] = Path(str(config['handoff'])+'.completed.json')
        config['handoff'] = None
    session = config['images'].setdefault(str(identity),session or ImageSearch(config['policy'],
        seed=config['seed'], render_budget=config['budget'],
        emit=lambda **values: progress(str(identity),**values)))
    session.search_seed = config['seed']
    if current_search() is session:
        yield session
        return
    with image_search(session):
        failed = False
        try:
            yield session
        except BaseException:
            failed = True
            raise
        finally:
            session.record(event='image_search_context_finished', satisfactory=bool(session.validated),
                stop_reason=('satisfactory' if session.validated else session.reason()
                             or ('execution_error' if failed else 'models_exhausted')), **session.report())
            if config.get('return_handoff'):
                from src.imageConverterCatalog import atomic_json
                atomic_json(config['return_handoff'], session.handoff(
                    deadline=time.monotonic()+max(0., session.policy.max_seconds-session.elapsed)))


def conversion_search_context(function):
    """Include result rechecks and PNG export in the original image budget."""
    @wraps(function)
    def convert(*args, **kwargs):
        import os
        identity = os.path.abspath(os.path.join(kwargs['folder_path'], kwargs['filename']))
        with configured_image_search(identity) as session:
            result = function(*args, **kwargs)
            if session is not None and result and isinstance(result[0], dict):
                row = result[0]
                row['search_control'] = dict(row.get('search_control', {}), **session.report())
                row.setdefault('params', {})['adaptive_search'] = row['search_control']
            return result
    return convert


@contextmanager
def standalone_image_search(identity, *, seconds, seed=None, directory=None, render_budget=384):
    """Public template/component workers share an existing context when nested."""
    active = current_search()
    if active is not None:
        yield active
        return
    config = settings()
    if config is not None:
        with configured_image_search(identity) as session:
            yield session
        return
    with search_configuration(mode='portfolio', adaptive=True, seed=0 if seed is None else seed,
            budget=render_budget, seconds=max(.001, seconds), max_seconds=max(.001, seconds),
            directory=directory):
        with configured_image_search(identity) as session:
            yield session


def validated_result(result, image, *, scope='full_scene'):
    """Call only after the model's full semantic checks have accepted its SVG."""
    session = current_search()
    if session is None:
        return False
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import candidate_scope
    # Public entry points bind the unmodified source before any subfit. A
    # masked/copied stage cannot certify the full conversion, even at zero loss.
    if scope != 'full_scene' or not session.is_reference(image):
        session.measured(result['svg'], result.get('error', 0.), source=result.get('source', 'model'),
                         scope='intermediate')
        return False
    from src.iCCModules.imageCompositeConverterCanvas import contain_svg, within_canvas
    original = result['svg']
    height, width = image.shape[:2]
    result['svg'] = contain_svg(original, width, height)
    if not within_canvas(original, width, height):
        # Most model renderers already enforce the boundary. Recheck an
        # adjusted model before binding a validation proof to the saved bytes.
        import cv2
        import fitz
        import numpy as np
        from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
        raster = render_svg_to_numpy_inprocess(result['svg'], width, height,
            fitz_module=fitz, np_module=np, cv2_module=cv2)
        if raster is None:
            return False
        result['rendered'] = raster
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions
    validate_svg_assertions(result['svg'], getattr(session, 'description_assertions', None))
    quality = pixel_quality(image,result['rendered'])
    if quality:
        session.measured(result['svg'], float(quality['normalized_mse']),
            source=result.get('source', 'model'), scope='full_scene', valid=True, passed=quality['passed'])
    if not quality or not quality['passed']:
        return False
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import svg_identity,raster_identity
    if (svg_identity(result['svg']),raster_identity(image)) not in session.validated:
        with candidate_scope('full_scene', result.get('source', 'model')):
            session.validate(result,image)
        if session.on_validated:
            session.on_validated(result, image, quality)
        progress(result.get('source','model'),event='candidate_satisfactory',**session.report())
    return True


def progress(source, **values):
    config = settings()
    if not config:
        return
    record = dict(source=source, **values)
    if config['mode'] == 'portfolio' and not values.get('event', '').startswith('candidate_'):
        print('[Search] '+json.dumps(record, ensure_ascii=False, allow_nan=False), flush=True)
    if config['directory']:
        config['directory'].mkdir(parents=True, exist_ok=True)
        if not config.get('journal'):
            config['journal'] = (config['directory']/'progress.jsonl').open('a', encoding='utf-8', buffering=1)
        config['journal'].write(json.dumps(record, ensure_ascii=False, allow_nan=False)+'\n')


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
    from src.iCCModules.imageCompositeConverterSearchBots import explore_bots
    return explore_bots(parameters, geometry_count, measure, incumbent, source=source,
                        image=image, satisfactory_fn=satisfactory_fn,
                        session=current_search(), config=settings(), emit=progress)
