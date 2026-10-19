"""Per-image wall-clock supervision and transactional, checked handoffs.

Workers cannot write final output paths. The parent never renders after a
deadline: it can recover only a completed handoff from this conversion run.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import pickle
import queue
import shutil
import signal
import sys
import tempfile
import threading
import time

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, image_search


class ProcessTree:
    """Contain native renderer descendants as well as the Python worker."""
    def __init__(self, process):
        self.process = process
        self.job = None
        if os.name == 'nt':
            from ctypes import wintypes

            class IO(ctypes.Structure):
                _fields_ = [(name, ctypes.c_ulonglong) for name in
                            ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]

            class Basic(ctypes.Structure):
                _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                            ('flags', wintypes.DWORD), ('min_ws', ctypes.c_size_t),
                            ('max_ws', ctypes.c_size_t), ('active', wintypes.DWORD),
                            ('affinity', ctypes.c_size_t), ('priority', wintypes.DWORD),
                            ('scheduling', wintypes.DWORD)]

            class Extended(ctypes.Structure):
                _fields_ = [('basic', Basic), ('io', IO), ('process_mem', ctypes.c_size_t),
                            ('job_mem', ctypes.c_size_t), ('peak_process', ctypes.c_size_t),
                            ('peak_job', ctypes.c_size_t)]

            self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
            self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
            self.kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
            self.kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
            self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            self.job = self.kernel.CreateJobObjectW(None, None)
            info = Extended()
            info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if (not self.job or not self.kernel.SetInformationJobObject(self.job, 9, ctypes.byref(info), ctypes.sizeof(info))
                    or not self.kernel.AssignProcessToJobObject(self.job, int(process.sentinel))):
                error = ctypes.get_last_error()
                if self.job:
                    self.kernel.CloseHandle(self.job)
                    self.job = None
                raise OSError(error, 'Cannot contain conversion worker in a Windows job')

    def close(self):
        if self.job:
            self.kernel.CloseHandle(self.job)
            self.job = None
        elif os.name != 'nt' and self.process.pid:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if self.process.is_alive():
            self.process.kill()
        self.process.join(timeout=1.)


def _atomic_pickle(path, value):
    temporary = path.with_suffix('.writing')
    with temporary.open('wb') as handle:
        pickle.dump(value, handle, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(temporary, path)


def _entry(connection, payload, worker):
    if os.name != 'nt':
        os.setsid()
    # No conversion or renderer may start until containment is installed.
    connection.send(('ready', None))
    connection.recv()
    try:
        worker(connection, payload)
    except BaseException as exc:
        connection.send(('error', f'{type(exc).__name__}: {exc}'[:1000]))
    finally:
        connection.close()


def _read_messages(connection, mailbox):
    try:
        while True:
            mailbox.put(connection.recv())
    except (EOFError, OSError):
        mailbox.put(('closed', None))


def _checkpoint_row(app, spec, result, image):
    rendered = result['rendered']
    h, w = image.shape[:2]
    mean, std = app.Action.calculateDelta2Stats(image, rendered)
    row = app.Action.calculateSpatialDelta2Quality(image, rendered)
    base = Path(spec['filename']).stem
    error = float(result.get('error', mean))
    row.update(filename=spec['filename'], variant=base.upper(), base=app.getBaseNameFromFile(base).upper(),
               w=w, h=h, mean_delta2=float(mean), std_delta2=float(std), best_error=error,
               error_per_pixel=error/max(1, w*h), best_iter=0, actual_iterations=0,
               requested_iterations=spec['iteration_budget'], elapsed_seconds=0.,
               rgb_rmse_per_channel=math.sqrt(float(mean)/3.),
               params={'mode': result.get('source', 'validated_model')}, search_satisfactory=True,
               convergence='validated_checkpoint', diff_error_distribution_status='none')
    return row


def conversion_worker(connection, payload):
    spec, stage = payload['spec'], Path(payload['stage'])
    blocked_reads = []
    if payload.get('semantic_only', True):
        def audit(event, args):
            if event != 'open' or not isinstance(args[0], (str, bytes, os.PathLike)):
                return
            path, mode, flags = args
            path = Path(os.fsdecode(path))
            if path.suffix.lower() != '.svg':
                return
            reads = ('r' in mode or '+' in mode) if isinstance(mode, str) else (flags & os.O_WRONLY) == 0
            if reads and not path.resolve().is_relative_to(stage.resolve()):
                blocked_reads.append(str(path))
                connection.send(('reference_read_blocked', str(path)))
                raise PermissionError('Semantic-only worker forbids reference SVG reads')
        sys.addaudithook(audit)
    from src import imageCompositeConverter as app
    from src.iCCModules import imageCompositeConverterSearchPortfolio as portfolio
    from src.iCCModules.imageCompositeConverterConversionExecution import convertOneImpl

    for name, value in payload['action'].items():
        setattr(app.Action, name, value)
    app.SVG_RENDER_SUBPROCESS_ENABLED = payload['render_isolated']
    app.SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = payload['render_timeout']
    config = payload['config']
    session = pickle.loads(payload['session'])
    session.spent += max(0., time.monotonic()-payload['started'])
    session.active_since = None
    session.on_progress = lambda error: connection.send(('progress', (time.monotonic(), error)))
    source_image = app.cv2.imread(str(Path(spec['folder_path'])/spec['filename']))
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import raster_identity
    source_identity = raster_identity(source_image) if source_image is not None else None
    counter = 0

    def checkpoint(result, image, quality):
        nonlocal counter
        from src.iCCModules.imageCompositeConverterAdaptiveSearch import raster_identity, svg_identity
        # Model-local semantics and unchanged strict pixels have already passed.
        if raster_identity(image) != source_identity:
            return
        row = _checkpoint_row(app, spec, result, image)
        encoded, png = app.cv2.imencode('.png', result['rendered'])
        if not encoded:
            return
        counter += 1
        path = stage / f'candidate-{counter}.pickle'
        _atomic_pickle(path, dict(row=row, svg=result['svg'], source=raster_identity(image),
                                 source_file_hash=payload['source_file_hash'], png=png.tobytes(),
                                 evaluations=session.evaluations,
                                 svg_hash=svg_identity(result['svg']), quality=quality))
        connection.send(('checkpoint', path.name))

    session.on_validated = checkpoint
    settings = {key: config[key] for key in
                ('mode', 'seed', 'budget', 'directory', 'allow_memory', 'adaptive')}
    settings.update(seconds=config['policy'].seconds, max_seconds=config['policy'].max_seconds)
    settings.update(disabled_bots=config.get('disabled_bots', ()),
                    component_observation=config.get('component_observation', True))
    failures = []
    log_path = Path(spec['reports_out_dir'])/(Path(spec['filename']).stem+'_worker.log')
    with app._optionalLogCapture(str(log_path)), portfolio.search_configuration(**settings):
        identity = os.path.abspath(os.path.join(spec['folder_path'], spec['filename']))
        portfolio.settings()['images'][identity] = session
        session.emit = lambda **values: portfolio.progress(identity, **values)
        # Also supervise legacy/fixed searches; their optimizers need no hooks.
        if not portfolio.settings()['adaptive']:
            session.on_validated = None
        from src.iCCModules.imageCompositeConverterComponents import snapshot
        component_path = Path(spec['reports_out_dir'])/(Path(spec['filename']).stem+'_components.jsonl')
        # Flush the observed switches before any search. An interrupted worker
        # has an explicit incomplete observation, never invented zero activity.
        with component_path.open('w', encoding='utf-8', buffering=1) as component_log:
            component_log.write(json.dumps(dict(event='configured', **snapshot(session, config)))+'\n')
            try:
                result = convertOneImpl(
                    **spec, run_iteration_pipeline_fn=app.runIterationPipeline,
                    read_validation_log_details_fn=app._readValidationLogDetails,
                    render_svg_to_numpy_fn=app.Action.renderSvgToNumpy,
                    calculate_delta2_stats_fn=app.Action.calculateDelta2Stats,
                    calculate_spatial_delta2_quality_fn=app.Action.calculateSpatialDelta2Quality,
                    get_base_name_from_file_fn=app.getBaseNameFromFile, cv2_module=app.cv2,
                    render_embedded_raster_svg_fn=app._renderEmbeddedRasterSvg,
                    append_batch_failure_fn=failures.append,
                )
            finally:
                component_log.write(json.dumps(dict(event='finished', **snapshot(session, config)),
                                                allow_nan=False)+'\n')
    _atomic_pickle(stage/'completed.pickle', dict(result=result, failures=failures, session=session))
    connection.send(('done', 'completed.pickle'))


class ImageDeadline:
    def __init__(self, policy, *, emit=None, hard_seconds=None):
        self.session = ImageSearch(policy, emit=emit)
        self.hard_seconds = hard_seconds if hard_seconds and hard_seconds > 0 else math.inf
        self.state = None
        self.best_row = None
        self.closed = False
        self.source_file_hash = None
        self.blocked_reads = []

    def _reason(self):
        if self.session.elapsed >= self.hard_seconds:
            return 'time_limit'
        return self.session.time_reason()

    def run(self, spec, *, config, action, render_isolated=False, render_timeout=20., worker=conversion_worker):
        current_hash = self._source_hash(spec)
        if self.source_file_hash is not None and current_hash != self.source_file_hash:
            self.best_row = None
            self.closed = True
            return self._expired(spec, 'source_changed')
        if self.closed:
            return self._expired(spec)
        root = Path(spec['reports_out_dir'])
        root.mkdir(parents=True, exist_ok=True)
        # One stage per attempt; never read previous-run SVGs as conversion input.
        with tempfile.TemporaryDirectory(prefix='.image-worker-', dir=root) as directory:
            stage = Path(directory)
            staged = dict(spec)
            for key in ('svg_out_dir', 'diff_out_dir', 'png_out_dir', 'reports_out_dir'):
                staged[key] = str(stage/key)
                Path(staged[key]).mkdir()
            if self.best_row is not None:
                name = Path(spec['filename']).stem+'.svg'
                prior = Path(spec['svg_out_dir'])/name
                if prior.exists():
                    shutil.copyfile(prior, Path(staged['svg_out_dir'])/name)
            ctx = multiprocessing.get_context('spawn')
            parent, child = ctx.Pipe()
            mailbox = queue.Queue()
            process = None
            tree = None
            completed = None
            checked = None
            failure = 'time_limit'
            blocked_reads = self.blocked_reads
            with image_search(self.session):
                started = time.monotonic()
                child_session = pickle.loads(self.state) if self.state else ImageSearch(self.session.policy)
                for key in ('spent', 'limit', 'last_progress', 'best_error', 'progress_anchor', 'extensions'):
                    setattr(child_session, key, getattr(self.session, key))
                child_session.active_since = None
                payload = dict(spec=staged, stage=str(stage), config=config, action=action,
                               session=pickle.dumps(child_session), started=started,
                               render_isolated=render_isolated, render_timeout=render_timeout,
                               source_file_hash=current_hash)
                if self.source_file_hash is None:
                    self.source_file_hash = payload['source_file_hash']
                try:
                    if not self._reason():
                        process = ctx.Process(target=_entry, args=(child, payload, worker))
                        process.start()
                        child.close()
                        threading.Thread(target=_read_messages, args=(parent, mailbox), daemon=True).start()
                        while True:
                            try:
                                event, value = mailbox.get(timeout=.02)
                            except queue.Empty:
                                event, value = None, None
                            if event == 'ready':
                                tree = ProcessTree(process)
                                parent.send('go')
                            elif event == 'progress':
                                sent, error = value
                                # A late or backlogged event cannot purchase time retroactively.
                                if self.session.elapsed < self.session.limit:
                                    self.session.observe(error, evaluation=False)
                                    if self.session.last_progress is not None:
                                        self.session.last_progress = self.session.spent+max(0., sent-started)
                            elif event == 'reference_read_blocked':
                                blocked_reads.append(value)
                            elif event == 'checkpoint' and not self._reason():
                                with (stage/value).open('rb') as handle:
                                    candidate = pickle.load(handle)
                                self.session.evaluations = max(self.session.evaluations, candidate.get('evaluations', 0))
                                if not self._valid_checkpoint(candidate, payload['source_file_hash']):
                                    continue
                                if checked is None or self._score(candidate['row']) < self._score(checked['row']):
                                    checked = candidate
                            elif event == 'done' and not self._reason():
                                with (stage/value).open('rb') as handle:
                                    completed = pickle.load(handle)
                                break
                            elif event in {'error', 'closed'}:
                                failure = 'worker_error'
                                (stage/'supervisor_error.log').write_text(
                                    str(value or f'Worker exited without handoff (exitcode={process.exitcode})'), encoding='utf-8')
                                break
                            if self._reason():
                                break
                except (OSError, ValueError, EOFError, pickle.UnpicklingError) as exc:
                    failure = 'worker_error'
                    (stage/'supervisor_error.log').write_text(str(exc), encoding='utf-8')
                finally:
                    if tree:
                        tree.close()
                    elif process is not None and process.pid:
                        if process.is_alive():
                            process.kill()
                        process.join(timeout=1.)
                    parent.close()
                    child.close()
            (root/(Path(spec['filename']).stem+'_reference_access.json')).write_text(
                json.dumps(dict(blocked_svg_reads=blocked_reads), indent=2)+'\n', encoding='utf-8')
            if completed is not None:
                if self.source_file_hash != self._source_hash(spec):
                    self.best_row = None
                    self.closed = True
                    return self._expired(spec, 'source_changed')
                self.session.evaluations = completed['session'].evaluations
                self.state = pickle.dumps(completed['session'])
                row, failed = completed['result']
                # Completed unsupported inputs may have no result row. Preserve
                # real timing/supervision evidence for those failures as well.
                control = dict(self.session.report(), isolated=True,
                               stop_reason='completed' if row is not None else 'no_result')
                (root/(Path(spec['filename']).stem+'_deadline.json')).write_text(
                    json.dumps(control, indent=2)+'\n', encoding='utf-8')
                if row is not None:
                    old_control = row.get('search_control', {})
                    row['search_control'] = dict(self.session.report(), isolated=True,
                                                 external_max_seconds=self.hard_seconds if math.isfinite(self.hard_seconds) else None,
                                                 stop_reason=old_control.get('stop_reason', 'supported_models_exhausted'))
                    row['params']['adaptive_search'] = row['search_control']
                    row['elapsed_seconds'] = self.session.elapsed
                    row['reference_access'] = dict(blocked_svg_reads=blocked_reads)
                if not failed and row is not None:
                    self.best_row = row
                self._publish(staged, spec)
                return (row, failed), completed['failures']
            self.closed = True
            if (stage/'supervisor_error.log').exists():
                shutil.copyfile(stage/'supervisor_error.log', root/(Path(spec['filename']).stem+'_supervisor_error.log'))
            # Preserve diagnostic output even when no final handoff exists.
            for log in Path(staged['reports_out_dir']).glob('*'):
                if log.is_file() and log.suffix in {'.log', '.jsonl'}:
                    shutil.copyfile(log, root/log.name)
            if checked is not None:
                self._recover(checked, spec)
            return self._expired(spec, failure)

    @staticmethod
    def _publish(staged, spec):
        for key in ('svg_out_dir', 'diff_out_dir', 'png_out_dir', 'reports_out_dir'):
            for source in Path(staged[key]).rglob('*'):
                if source.is_file():
                    target = Path(spec[key])/source.relative_to(staged[key])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    temporary = target.with_name(target.name+'.handoff')
                    shutil.copyfile(source, temporary)
                    os.replace(temporary, target)

    def _recover(self, checked, spec):
        # The IPC carries the source and SVG binding from the checked model.
        if not self._valid_checkpoint(checked, self._source_hash(spec)):
            return
        if (self.best_row and self.best_row.get('search_satisfactory')
                and self._score(self.best_row) <= self._score(checked['row'])):
            return
        target = Path(spec['svg_out_dir'])/(Path(spec['filename']).stem+'.svg')
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.handoff')
        temporary.write_text(checked['svg'], encoding='utf-8')
        os.replace(temporary, target)
        png_target = Path(spec['png_out_dir'])/(Path(spec['filename']).stem+'.png')
        png_target.parent.mkdir(parents=True, exist_ok=True)
        png_temporary = png_target.with_suffix('.handoff')
        png_temporary.write_bytes(checked['png'])
        os.replace(png_temporary, png_target)
        log = Path(spec['reports_out_dir'])/(Path(spec['filename']).stem+'_element_validation.log')
        log.write_text('status=semantic_ok\nvalidation_scope=checked_model_and_strict_pixels\n'
                       'convergence=validated_checkpoint\n', encoding='utf-8')
        self.best_row = checked['row']
        self.best_row['checkpoint_proof'] = dict(svg_sha256=checked['svg_hash'],
            source_file_sha256=checked['source_file_hash'], source_pixels_sha256=checked.get('source'),
            strict_pixel_gate=checked['quality'], local_semantics_passed=True)

    @staticmethod
    def _score(row):
        return float(row.get('spatial_quality_score', row['mean_delta2']))

    @staticmethod
    def _valid_checkpoint(checked, source_hash):
        from src.iCCModules.imageCompositeConverterAdaptiveSearch import svg_identity
        return (checked['quality']['passed'] and svg_identity(checked['svg']) == checked['svg_hash']
                and checked['source_file_hash'] == source_hash)

    @staticmethod
    def _source_hash(spec):
        digest = hashlib.sha256()
        with (Path(spec['folder_path'])/spec['filename']).open('rb') as handle:
            for block in iter(lambda: handle.read(1024*1024), b''):
                digest.update(block)
        return digest.hexdigest()

    def _expired(self, spec, reason='time_limit'):
        control = dict(self.session.report(), stop_reason=reason, isolated=True,
                       external_max_seconds=self.hard_seconds if math.isfinite(self.hard_seconds) else None,
                       recovered_checkpoint=bool(self.best_row and self.best_row.get('checkpoint_proof')),
                       retained_output=bool(self.best_row))
        path = Path(spec['reports_out_dir'])/(Path(spec['filename']).stem+'_deadline.json')
        path.write_text(json.dumps(control, indent=2)+'\n', encoding='utf-8')
        row = dict(self.best_row) if self.best_row else None
        if row:
            row['search_control'] = control
            row['elapsed_seconds'] = control['elapsed_seconds']
        failures = [] if row and row.get('search_satisfactory') else [dict(
            filename=spec['filename'], status='batch_error', reason='TimeoutError' if reason == 'time_limit' else 'WorkerError',
            details=json.dumps(control), log_file=path.name, failed_svg='')]
        return (row, bool(failures)), failures
