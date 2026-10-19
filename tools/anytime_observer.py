"""Benchmark-only observer, installed in spawned production CLI workers.

No search decisions or acceptance checks are replaced. Append-only telemetry
survives termination, including a render begun but interrupted at the deadline.
"""
from __future__ import annotations

import json
import hashlib
import importlib
import os
from pathlib import Path
import time


def observed_worker(connection, payload):
    from src import imageCompositeConverter as app
    from src.iCCModules.imageCompositeConverterDeadline import conversion_worker

    target = Path(os.environ['ICC_ANYTIME_TELEMETRY'])
    target.mkdir(parents=True, exist_ok=True)
    name = Path(payload['spec']['filename']).stem
    render = app.Action.renderSvgToNumpy
    with (target / f'{name}-{os.getpid()}.jsonl').open('a', encoding='utf-8', buffering=1) as log:
        def emit(event, **values):
            log.write(json.dumps(dict(event=event, image_seconds=time.monotonic()-payload['started'],
                                      **values))+'\n')

        def counted(*args, **kwargs):
            emit('render_started')
            started = time.perf_counter()
            try:
                result = render(*args, **kwargs)
            except BaseException:
                emit('render_failed', active_seconds=time.perf_counter()-started)
                raise
            emit('render_finished', active_seconds=time.perf_counter()-started, valid=result is not None)
            return result

        app.Action.renderSvgToNumpy = staticmethod(counted)
        names = ('imageCompositeConverter.py', 'iCCModules/imageCompositeConverterAdaptiveSearch.py',
                 'iCCModules/imageCompositeConverterFilledSymbols.py', 'iCCModules/imageCompositeConverterSearchBots.py',
                 'iCCModules/imageCompositeConverterShortLabelDisk.py')
        if os.environ.get('ICC_COMPONENT_EVALUATION'):
            names += tuple('iCCModules/imageCompositeConverter'+suffix+'.py' for suffix in
                           ('Cli','Components','Deadline','SearchPortfolio','SearchScheduler'))
        if os.environ.get('ICC_NEURAL_EVALUATION'):
            names += tuple('iCCModules/imageCompositeConverter'+suffix+'.py' for suffix in
                           ('NeuralElements','PrimitiveScene','NonCompositeRuntime','ConversionExecution'))
        emit('worker_observed', source_sha256={
            'src/'+name: hashlib.sha256(Path(importlib.import_module('src.'+name[:-3].replace('/','.')).__file__).read_bytes()).hexdigest()
            for name in names}, applied_controls=getattr(render,'_component_controls',None))
        try:
            conversion_worker(connection, payload)
        finally:
            app.Action.renderSvgToNumpy = staticmethod(render)


def install():
    """Use the ordinary supervisor with an instrumented conversion callback."""
    from src.iCCModules.imageCompositeConverterDeadline import ImageDeadline
    ImageDeadline.run.__kwdefaults__['worker'] = observed_worker


def summarize(paths):
    result = dict(render_started=0, render_finished=0, render_failed=0,
                  render_invalid=0, render_active_seconds=0., workers_observed=0, source_sha256={})
    for path in paths:
        # A killed process may leave one partial last line; completed events count.
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            kind = event['event']
            if kind == 'worker_observed':
                result['workers_observed'] += 1
                if result['source_sha256'] and result['source_sha256'] != event['source_sha256']:
                    raise ValueError('Worker implementation changed during a cell')
                result['source_sha256'] = event['source_sha256']
            elif kind in {'render_started', 'render_finished', 'render_failed'}:
                result[kind] += 1
                result['render_active_seconds'] += event.get('active_seconds', 0.)
                if kind == 'render_finished' and not event['valid']:
                    result['render_invalid'] += 1
    result['render_interrupted'] = result['render_started']-result['render_finished']-result['render_failed']
    return result
