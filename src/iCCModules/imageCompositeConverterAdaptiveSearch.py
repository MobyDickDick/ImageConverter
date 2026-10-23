"""Progress-sensitive search limits; quality acceptance stays with each model.

All clocks are monotonic and injectable. Time is charged only while an image
is active, so interleaved batch images cannot spend one another's budgets.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import hashlib
import math
import time

_SESSION = ContextVar('adaptive_conversion_search', default=None)


@dataclass(frozen=True)
class SearchPolicy:
    seconds: float = 60.
    max_seconds: float = 120.
    patience: int = 128
    relative_gain: float = .01
    extension_seconds: float = 15.

    def __post_init__(self):
        numbers = (self.seconds,self.max_seconds,self.relative_gain,self.extension_seconds)
        if (not all(math.isfinite(v) for v in numbers) or not 0 < self.seconds <= self.max_seconds
                or not 0 < self.relative_gain < 1 or self.extension_seconds <= 0 or self.patience < 1):
            raise ValueError('Invalid adaptive search policy')


class ImageSearch:
    def __init__(self, policy, *, clock=None, emit=None):
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
        self.validated.add((svg_identity(result['svg']),raster_identity(image)))

    def output_reason(self, error, *, satisfactory):
        if satisfactory:
            return 'satisfactory'
        reason = self.time_reason()
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
            max_seconds=self.policy.max_seconds,time_extensions=self.extensions,candidate_evaluations=self.evaluations)


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
        reason = self.session.time_reason()
        if reason:
            return reason
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


def raster_identity(image):
    import numpy as np
    pixels = np.asarray(image,dtype=np.uint8)
    return hashlib.sha256(str(pixels.shape).encode()+pixels.tobytes()).hexdigest()


def pixel_quality(reference, output):
    """Unchanged strict pixel limits, with the source's observed background.

    Match the independent Plan-B measurement, including tightly cropped JPEG
    inputs whose border median is not pure white. Never infer success from a
    low global mean alone.
    """
    import cv2
    import numpy as np
    reference,output = np.asarray(reference,dtype=np.uint8),np.asarray(output,dtype=np.uint8)
    if reference.shape!=output.shape or reference.ndim!=3 or reference.shape[2]!=3:
        return None
    a,b = reference.astype(np.float32),output.astype(np.float32)
    border = np.concatenate((a[0],a[-1],a[:,0],a[:,-1]))
    background = np.median(border,axis=0)
    observed = np.max(abs(a-background),axis=2)>25
    predicted = np.max(abs(b-background),axis=2)>25
    union = observed|predicted
    error = np.square(a-b).mean(axis=2)/255**2
    iou = float((observed&predicted).sum()/union.sum()) if union.any() else 1.
    foreground = float(error[union].mean()) if union.any() else float(error.mean())
    ae,be = cv2.Canny(reference,50,140)>0,cv2.Canny(output,50,140)>0
    if ae.any() and be.any():
        da = cv2.distanceTransform((~ae).astype(np.uint8),cv2.DIST_L2,3)
        db = cv2.distanceTransform((~be).astype(np.uint8),cv2.DIST_L2,3)
        edge = float((np.exp(-db[ae]).mean()+np.exp(-da[be]).mean())/2)
    else:
        edge = float(not ae.any() and not be.any())
    mse = float(error.mean())
    return dict(normalized_mse=mse,foreground_mse=foreground,foreground_iou=iou,edge_alignment=edge,
                passed=bool(mse<=.01 and foreground<=.04 and iou>=.85 and edge>=.72))


def current_search():
    return _SESSION.get()


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
