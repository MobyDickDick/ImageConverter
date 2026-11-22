"""Progress-sensitive search limits; quality acceptance stays with each model.

All clocks are monotonic and injectable. Time is charged only while an image
is active, so interleaved batch images cannot spend one another's budgets.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from collections import OrderedDict
from dataclasses import asdict, dataclass
from functools import wraps
import hashlib
import math
import time

_SESSION = ContextVar('adaptive_conversion_search', default=None)
_RENDERING = ContextVar('conversion_render_in_progress', default=False)
_SCOPE = ContextVar('conversion_candidate_scope', default=('intermediate', 'model'))


@dataclass(frozen=True)
class SearchPolicy:
    seconds: float = 60.
    max_seconds: float = 120.
    patience: int = 128
    relative_gain: float = .01
    extension_seconds: float = 15.
    minimum_seconds: float = 0.

    def __post_init__(self):
        numbers = (self.seconds,self.max_seconds,self.relative_gain,self.extension_seconds,self.minimum_seconds)
        if (not all(math.isfinite(v) for v in numbers) or not 0 < self.seconds <= self.max_seconds
                or not 0 < self.relative_gain < 1 or self.extension_seconds <= 0 or self.patience < 1
                or not 0 <= self.minimum_seconds <= self.seconds):
            raise ValueError('Invalid adaptive search policy')


class ImageSearch:
    def __init__(self, policy, *, clock=None, emit=None, seed=None, render_budget=10000):
        if type(render_budget) is not int or render_budget < 1:
            raise ValueError('Positive image render budget required')
        if seed is not None and (type(seed) is not int or not 0 <= seed < 2**64):
            raise ValueError('Seed must be an unsigned 64-bit integer')
        self.policy = policy
        self.clock = clock or time.monotonic
        self.emit = emit or (lambda **values: None)
        self.spent = 0.
        self.active_since = None
        self.limit = policy.seconds
        self.best_error = math.inf
        self.progress_anchor = math.inf
        self.last_progress = None
        self.extensions = 0
        self.evaluations = 0
        self.validated = set()
        self.previous_output_error = None
        # Conversion-local blackboards. Never loaded as templates for other images.
        self.bot_searches = {}
        self.scheduler_history = []
        self.registration_rasters = {}
        self.structure_rejections = {}
        self.native_frontiers = {}
        self.structural_trials = set()
        self.render_memo = OrderedDict()
        self.render_memo_bytes = 0
        self.render_cache_hits = 0
        self.search_seed = seed
        self.render_budget = render_budget
        self.renderings = 0
        self.render_failures = 0
        self.stop_reason = None
        self.reference_identity = None
        self.attempts = []
        self.candidates = OrderedDict()
        self.objectives = {}
        self.render_sequence_sha256 = '00'*32
        self.finish_model_searches = False
        self.on_progress = None
        self.on_validated = None

    def __getstate__(self):
        # Callbacks belong to the supervising process, never to saved history.
        return {key: value for key, value in self.__dict__.items()
                if key not in {'clock', 'emit', 'on_progress', 'on_validated'}}

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.clock = time.monotonic
        self.emit = lambda **values: None
        self.on_progress = self.on_validated = None

    def handoff(self, *, deadline):
        """JSON-only transport for the optional-template -> CLI process boundary."""
        import base64
        return dict(schema='image_search_context_v1', policy=asdict(self.policy),
            spent=self.elapsed, transferred_at=time.monotonic(), deadline=deadline, limit=self.limit,
            seed=self.search_seed, render_budget=self.render_budget, renderings=self.renderings,
            render_failures=self.render_failures, render_cache_hits=self.render_cache_hits,
            render_sequence_sha256=self.render_sequence_sha256,
            candidates=[(key, value) for key, value in self.candidates.items()],
            rasters=[(key, None if value is None else
                (value[0], base64.b64encode(value[1]).decode('ascii'))) for key, value in self.render_memo.items()])

    @classmethod
    def from_handoff(cls, state, *, emit=None):
        import base64
        if state.get('schema') != 'image_search_context_v1':
            raise ValueError('Invalid search context handoff')
        policy = state['policy'].copy()
        spent = float(state['spent'])+max(0., time.monotonic()-state['transferred_at'])
        cap = max(.001, spent+max(0., state['deadline']-time.monotonic()))
        policy['max_seconds'] = min(policy['max_seconds'], cap)
        policy['seconds'] = min(policy['seconds'], policy['max_seconds'])
        policy['minimum_seconds'] = min(policy['minimum_seconds'], policy['seconds'])
        session = cls(SearchPolicy(**policy), seed=state['seed'], render_budget=state['render_budget'], emit=emit)
        if (type(state['renderings']) is not int or not 0 <= state['renderings'] <= session.render_budget
                or not math.isfinite(spent) or spent < 0
                or not isinstance(state['render_sequence_sha256'], str)
                or len(bytes.fromhex(state['render_sequence_sha256'])) != 32):
            raise ValueError('Invalid search context counters')
        session.spent, session.limit = spent, min(state['limit'], session.policy.max_seconds)
        for key in ('renderings', 'render_failures', 'render_cache_hits', 'render_sequence_sha256'):
            setattr(session, key, state[key])
        session.candidates = OrderedDict((tuple(key), value) for key, value in state['candidates'])
        for key, value in state['rasters']:
            entry = None if value is None else (tuple(value[0]), base64.b64decode(value[1]))
            session.render_memo[tuple(key)] = entry
            if entry:
                session.render_memo_bytes += len(entry[1])
        return session

    @property
    def elapsed(self):
        return self.spent + (max(0.,self.clock()-self.active_since) if self.active_since is not None else 0.)

    def observe(self, error, *, evaluation=True):
        if not math.isfinite(error) or error < 0:
            return
        if evaluation:
            self.evaluations += 1
        self.best_error = min(self.best_error,error)
        if not math.isfinite(self.progress_anchor):
            self.progress_anchor = error
            if self.on_progress:
                self.on_progress(error)

        elif self.progress_anchor-error >= max(1e-9,abs(self.progress_anchor)*self.policy.relative_gain):
            self.progress_anchor = error
            self.last_progress = self.elapsed
            if self.on_progress:
                self.on_progress(error)

    @property
    def minimum_pending(self):
        """Poor fits earn real exploration before proposal/stagnation cutoffs."""
        return self.elapsed < self.policy.minimum_seconds

    def time_reason(self):
        elapsed = self.elapsed
        # A rendering that overruns the hard cap cannot earn more time.
        if elapsed >= self.policy.max_seconds:
            return 'time_limit'
        if elapsed < self.limit:
            return None
        window = min(10.,self.policy.seconds*.2)
        if self.last_progress is not None and self.last_progress >= self.limit-window:
            old = self.limit
            self.limit = min(self.policy.max_seconds,max(self.limit,elapsed)+self.policy.extension_seconds)
            self.extensions += 1
            # Each improvement can earn at most one extension.
            self.last_progress = None
            self.emit(event='time_extended',previous_seconds=old,limit_seconds=self.limit,
                      elapsed_seconds=elapsed,best_error=self.best_error)
            return None
        return 'time_limit'

    def validate(self, result, image):
        scope, _ = _SCOPE.get()
        if scope != 'full_scene' or not self.is_reference(image):
            return False
        self.validated.add((svg_identity(result['svg']),raster_identity(image)))
        return True

    def bind_reference(self, image):
        identity = raster_identity(image)
        if self.reference_identity is not None and self.reference_identity != identity:
            raise ValueError('A search context belongs to one source image')
        self.reference_identity = identity

    def is_reference(self, image):
        return self.reference_identity == raster_identity(image)

    def reason(self):
        reason = self.time_reason()
        if reason is None and self.renderings >= self.render_budget:
            reason = 'render_limit'
        if reason:
            self.stop_reason = reason
        return reason

    def record(self, **values):
        record = dict(scope=_SCOPE.get()[0], candidate_source=_SCOPE.get()[1])
        record.update(values)
        # Bound in-memory evidence; the live journal retains every event.
        if len(self.attempts) < max(1024, self.render_budget*4):
            self.attempts.append(record)
        self.emit(**record)

    def measured(self, svg, error, *, source, scope='intermediate', valid=False, passed=False):
        """Keep objectives separate: a masked loss cannot advance scene quality."""
        if not math.isfinite(error):
            return
        key = (source, scope)
        previous = self.objectives.get(key, math.inf)
        self.objectives[key] = min(previous, error)
        identity = candidate_identity(svg)
        self.candidates[(identity, source, scope)] = dict(svg=svg, error=error,
            valid=valid, passed=bool(passed and valid and scope == 'full_scene'))
        while len(self.candidates) > 256:
            self.candidates.popitem(last=False)
        if scope == 'full_scene' and valid:
            self.observe(error, evaluation=False)
        self.record(event='candidate_measured', candidate=identity, objective=source,
            scope=scope, candidate_source=source,
            validation_scope=scope, error=error, improved=error < previous,
            valid=valid, passed=bool(passed and valid and scope == 'full_scene'))

    def output_reason(self, error, *, satisfactory):
        if satisfactory:
            return 'satisfactory'
        reason = self.reason()
        if reason:
            return reason
        old = self.previous_output_error
        self.previous_output_error = error
        if old is not None and math.isfinite(old) and math.isfinite(error):
            if old-error < max(1e-9,abs(old)*self.policy.relative_gain):
                return 'stagnation'
        return 'supported_models_exhausted'

    def report(self):
        return dict(elapsed_seconds=round(self.elapsed,6),limit_seconds=self.limit,
            minimum_seconds=self.policy.minimum_seconds,
            max_seconds=self.policy.max_seconds,time_extensions=self.extensions,candidate_evaluations=self.renderings,
            model_evaluations=self.evaluations,
            render_cache_hits=self.render_cache_hits,
            renderings=self.renderings, render_budget=self.render_budget,
            render_failures=self.render_failures, global_stop_reason=self.stop_reason,
            full_scene_validations=len(self.validated),
            search_seed=str(self.search_seed) if self.search_seed is not None else None,
            render_sequence_sha256=self.render_sequence_sha256)

    def render_candidate(self, image, svg, render_fn, width, height, *, renderer=None):
        """Image-local render evidence survives model and structure re-entry.

        Compress pixels instead of retaining hundreds of full-size rasters.
        Canonical XML avoids new work for attribute order, namespace prefixes,
        insignificant whitespace and identity wrappers. Objectives and semantic
        checks still belong to the caller and are always recomputed.
        """
        import numpy as np
        import zlib
        renderer = renderer or getattr(render_fn, 'search_renderer',
            render_fn.__module__+'.'+getattr(render_fn, '__qualname__', type(render_fn).__name__))
        key = (raster_identity(image), str(renderer), int(width), int(height), candidate_identity(svg))
        if key in self.render_memo:
            self.render_cache_hits += 1
            self.render_memo.move_to_end(key)
            self.record(event='candidate_cache_hit', candidate=key[-1], renderer=renderer,
                        width=int(width), height=int(height))
            entry = self.render_memo[key]
            if entry is None:
                return None, False
            shape, payload = entry
            return np.frombuffer(zlib.decompress(payload), dtype=np.uint8).reshape(shape).copy(), False
        reason = self.reason()
        if reason:
            self.record(event='candidate_skipped', candidate=key[-1], reason=reason)
            return None, False
        # Hash actual render requests, never the seed itself. This distinguishes
        # real exploration from changing metadata on identical proposals.
        self.render_sequence_sha256 = hashlib.sha256(bytes.fromhex(self.render_sequence_sha256)
            +repr(key).encode()).hexdigest()
        self.renderings += 1
        began = self.clock()
        token = _RENDERING.set(True)
        try:
            raster = render_fn(svg, width, height)
        except Exception:
            self.render_failures += 1
            self.record(event='candidate_rendered', candidate=key[-1], renderer=renderer,
                rendering=self.renderings, seconds=max(0., self.clock()-began), status='error')
            raise
        finally:
            _RENDERING.reset(token)
        if raster is None:
            self.render_failures += 1
        self.record(event='candidate_rendered', candidate=key[-1], renderer=renderer,
            width=int(width), height=int(height), rendering=self.renderings,
            seconds=max(0., self.clock()-began), status='rendered' if raster is not None else 'failed')
        if raster is None:
            entry, size = None, 0
        else:
            pixels = np.asarray(raster, dtype=np.uint8)
            payload = zlib.compress(pixels.tobytes(), 1)
            entry, size = (pixels.shape, payload), len(payload)
        # Trial identities survive pixel-cache eviction in the frontier.
        while self.render_memo and (len(self.render_memo) >= 8192 or self.render_memo_bytes+size > 32*1024*1024):
            _, old = self.render_memo.popitem(last=False)
            if old is not None:
                self.render_memo_bytes -= len(old[1])
        if size <= 32*1024*1024:
            self.render_memo[key] = entry
            self.render_memo_bytes += size
        return raster, True


class SearchRun:
    """One model's additional proposal budget, sharing its image's time limit."""
    def __init__(self, session, budget, *, source):
        self.session = session
        self.base_budget = budget
        self.limit = budget
        self.maximum = budget*4
        self.source = source
        self.proposals = 0
        self.anchor = math.inf
        self.last_progress = None
        self.extensions = 0
        self.last_gain_used = None

    def observe(self, loss):
        self.proposals += 1
        if not math.isfinite(loss):
            return
        if not math.isfinite(self.anchor):
            self.anchor = loss
        elif self.anchor-loss >= max(1e-9,abs(self.anchor)*self.session.policy.relative_gain):
            self.anchor = loss
            self.last_progress = self.proposals

    def reason(self, *, alternatives_tried):
        reason = self.session.reason()
        if reason:
            return reason
        if self.session.minimum_pending:
            return None
        if self.session.finish_model_searches:
            return 'candidate_comparison'
        if self.proposals >= self.maximum:
            return 'proposal_limit'
        if self.proposals >= self.limit:
            window = max(8,int(self.limit*.2))
            if (self.last_progress is not None and self.last_progress >= self.limit-window
                    and self.last_progress != self.last_gain_used and self.limit < self.maximum):
                old = self.limit
                self.limit = min(self.maximum,self.limit+max(16,self.base_budget//2))
                self.last_gain_used = self.last_progress
                self.extensions += 1
                self.session.emit(event='proposal_budget_extended',model=self.source,
                    previous_budget=old,budget=self.limit,proposals=self.proposals)
            else:
                return 'proposal_limit'
        if (alternatives_tried and self.proposals >= self.session.policy.patience
                and self.proposals-(self.last_progress or 0) >= self.session.policy.patience):
            return 'stagnation'
        return None


def svg_identity(svg):
    return hashlib.sha256(svg.strip().encode('utf-8')).hexdigest()


def candidate_identity(svg):
    """Search identity only; validation proofs continue to use exact SVG bytes."""
    from xml.etree import ElementTree as ET
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg_identity(svg)
    identities = {'translate(0 0)', 'translate(0.000000 0.000000) scale(1.000000)',
                  'matrix(1 0 0 1 0 0)', 'scale(1)', 'scale(1.000000)'}
    def normalize(node, in_text=False):
        # Namespace URIs remain part of tags, independent of textual prefixes.
        if node.get('transform', '').strip() in identities:
            node.attrib.pop('transform')
        children = []
        in_text = in_text or node.tag.rsplit('}', 1)[-1] in {'text', 'tspan'}
        for child in node:
            normalized = normalize(child, in_text)
            if child.tag.rsplit('}', 1)[-1] == 'g' and not child.attrib:
                children.extend(normalized[3])
            else:
                children.append(normalized)
        text = node.text or ''
        tail = node.tail or ''
        return (node.tag, tuple(sorted(node.attrib.items())), text if in_text else text.strip(), tuple(children),
                tail if in_text or tail.strip() else '')
    return hashlib.sha256(repr(normalize(root)).encode()).hexdigest()


def raster_identity(image):
    import numpy as np
    pixels = np.asarray(image,dtype=np.uint8)
    return hashlib.sha256(str(pixels.shape).encode()+pixels.tobytes()).hexdigest()


def pixel_quality(reference, output):
    """Pixel limits with graded foreground overlap and observed background.

    Match the independent Plan-B measurement, including tightly cropped JPEG
    inputs whose border median is not pure white. Never infer success from a
    low global mean alone.
    """
    import cv2
    import numpy as np
    from src.iCCModules.imageCompositeConverterRasterQuality import foreground_overlap
    reference,output = np.asarray(reference,dtype=np.uint8),np.asarray(output,dtype=np.uint8)
    if reference.shape!=output.shape or reference.ndim!=3 or reference.shape[2]!=3:
        return None
    a,b = reference.astype(np.float32),output.astype(np.float32)
    border = np.concatenate((a[0],a[-1],a[:,0],a[:,-1]))
    background = np.median(border,axis=0)
    observed_contrast = np.max(abs(a-background),axis=2)
    predicted_contrast = np.max(abs(b-background),axis=2)
    observed = observed_contrast>25
    predicted = predicted_contrast>25
    union = observed|predicted
    error = np.square(a-b).mean(axis=2)/255**2
    foreground = float(error[union].mean()) if union.any() else float(error.mean())
    ae,be = cv2.Canny(reference,50,140)>0,cv2.Canny(output,50,140)>0
    if ae.any() and be.any():
        da = cv2.distanceTransform((~ae).astype(np.uint8),cv2.DIST_L2,3)
        db = cv2.distanceTransform((~be).astype(np.uint8),cv2.DIST_L2,3)
        edge = float((np.exp(-db[ae]).mean()+np.exp(-da[be]).mean())/2)
    else:
        edge = float(not ae.any() and not be.any())
    mse = float(error.mean())
    iou, binary_iou = foreground_overlap(observed_contrast, predicted_contrast,
        normalized_mse=mse, foreground_mse=foreground, edge_alignment=edge)
    return dict(normalized_mse=mse,foreground_mse=foreground,foreground_iou=iou,
                foreground_iou_binary=binary_iou,edge_alignment=edge,
                passed=bool(mse<=.01 and foreground<=.04 and iou>=.85 and edge>=.72))


def preferred_quality(quality):
    """A stricter early-exit target, never a replacement for acceptance gates."""
    return bool(quality and quality['passed'] and quality['normalized_mse'] <= .0005
                and quality['foreground_mse'] <= .005 and quality['foreground_iou'] >= .97
                and quality['edge_alignment'] >= .90)


def vector_quality_score(quality):
    """Shared selection score; acceptance limits and model proofs are separate."""
    return (quality['normalized_mse']+.2*(1-quality['edge_alignment'])
            +.1*(1-quality['foreground_iou'])+quality.get('representation_penalty', 0.))


def vector_candidate_quality(reference, output, svg):
    from src.iCCModules.imageCompositeConverterRepresentation import representation_cost
    quality = pixel_quality(reference, output)
    if 'data-svg-component=' in svg:
        from src.iCCModules.imageCompositeConverterSvgComponents import component_overlap_quality
        quality.update(component_overlap_quality(reference, output, svg))
        quality['passed'] = bool(quality['passed'] and quality['overlap_passed'])
    cost = representation_cost(svg)
    return dict(quality, representation_penalty=cost['penalty'], representation_complexity=cost)


def current_search():
    return _SESSION.get()


@contextmanager
def candidate_scope(scope, source='model'):
    if scope not in {'intermediate', 'full_scene'}:
        raise ValueError('Unknown candidate scope')
    token = _SCOPE.set((scope, source))
    try:
        yield
    finally:
        _SCOPE.reset(token)


def tracked_renderer(function):
    """Track the outermost renderer, including custom fitters and masked stages.

    Nested private adapters are one request; color-space/backend names and
    dimensions separate caches. Cached pixels never carry a validation proof.
    """
    namespace = function.__module__+'.'+function.__qualname__
    @wraps(function)
    def render(svg, width, height, *args, **kwargs):
        session = current_search()
        if session is None or _RENDERING.get():
            return function(svg, width, height, *args, **kwargs)
        pixels, _ = session.render_candidate(None, svg,
            lambda s, w, h: function(s, w, h, *args, **kwargs), width, height,
            renderer=namespace)
        return pixels
    render.search_renderer = namespace
    return render


@contextmanager
def image_search(session):
    previous = current_search()
    if previous is session:
        yield session
        return
    if previous is not None:
        previous.spent = previous.elapsed
        previous.active_since = None
    token = _SESSION.set(session)
    if session is not None:
        session.active_since = session.clock()
    try:
        yield session
    finally:
        if session is not None:
            session.spent = session.elapsed
            session.active_since = None
        _SESSION.reset(token)
        if previous is not None:
            previous.active_since = previous.clock()
