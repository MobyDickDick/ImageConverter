"""Cooperative model/strategy scheduling within the existing image deadline.

Scheduling ranks fractional progress per active second, never semantic fitness.
Each hypothesis retains its own objective; only callers can accept its output.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import sys


@dataclass
class Share:
    turns: int = 0
    last_turn: int = -1
    seconds: float = 0.
    rate: float = 0.
    best: float = math.inf


class FairSelector:
    """Try every alternative, reward progress, reserve recurring exploration."""
    def __init__(self, names):
        self.shares = {name: Share() for name in names}
        self.turn = 0

    def choose(self, active):
        unseen = [name for name in active if not self.shares[name].turns]
        if unseen:
            return unseen[0]
        oldest = min(active, key=lambda name: self.shares[name].last_turn)
        # A productive hypothesis cannot starve slower or initially flat ones.
        if self.turn-self.shares[oldest].last_turn >= 2*len(active):
            return oldest
        return max(active, key=lambda name: (self.shares[name].rate, -self.shares[name].last_turn))

    def record(self, name, seconds, before, after):
        share = self.shares[name]
        gain = (max(0., before-after)/max(abs(before), 1e-9)
                if math.isfinite(before) and math.isfinite(after) else 0.)
        seconds = max(0., seconds)
        share.rate = .5*share.rate + .5*gain/max(seconds, .001)
        share.seconds += seconds
        share.best = min(share.best, after)
        share.turns += 1
        share.last_turn = self.turn
        self.turn += 1


def drain(iterator):
    """Preserve the synchronous API for fixed-policy and single-model callers."""
    while True:
        try:
            next(iterator)
        except StopIteration as completed:
            return completed.value


def schedule_models(jobs, session, *, source, emit, slice_seconds=.05, slice_steps=8):
    """Yield completed (model, result) pairs from resumable registration jobs.

    A step is at most one measurement plus its checks. Native calls are bounded
    by the supervising process, not preempted by this cooperative scheduler.
    Closing this iterator closes every suspended model, including on exceptions.
    """
    selector = FairSelector(jobs)
    active = dict(jobs)
    record = dict(source=source, slices=0, stop_reason=None, models={})
    session.scheduler_history.append(record)
    try:
        while active:
            reason = session.time_reason()
            if reason:
                record['stop_reason'] = reason
                break
            name = selector.choose(list(active))
            share = selector.shares[name]
            before = after = share.best
            started = session.elapsed
            steps = 0
            completed = False
            value = None
            while steps < slice_steps:
                if session.time_reason():
                    break
                try:
                    loss = next(active[name])
                except StopIteration as result:
                    completed, value = True, result.value
                    del active[name]
                    break
                steps += 1
                if loss is not None and math.isfinite(loss):
                    if not math.isfinite(before):
                        before = float(loss)
                    after = min(after, float(loss))
                if session.elapsed-started >= slice_seconds:
                    break
            selector.record(name, session.elapsed-started, before, after)
            record['slices'] += 1
            record['models'][str(name)] = vars(selector.shares[name]).copy()
            # Never serialize infinity in progress reports/evidence.
            if not math.isfinite(record['models'][str(name)]['best']):
                record['models'][str(name)]['best'] = None
            emit(source, event='model_slice', model=str(name), steps=steps,
                 completed=completed, **record['models'][str(name)])
            if completed:
                yield name, value
        record['stop_reason'] = record['stop_reason'] or 'models_exhausted'
    finally:
        for job in active.values():
            job.close()
        error = sys.exc_info()[0]
        record['stop_reason'] = record['stop_reason'] or (
            'execution_error' if error and error is not GeneratorExit else 'caller_stopped')
        emit(source, event='model_schedule_finished', **{k:v for k,v in record.items() if k!='source'})
