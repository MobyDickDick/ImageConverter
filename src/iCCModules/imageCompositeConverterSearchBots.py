"""Cooperative, bounded parameter workers for one analytic model.

Workers run in small deterministic turns, sharing admissible improvements and
compact negative evidence. Retired workers and their trials survive retries in
the active ImageSearch, but no history is read from disk or another image.
"""
from __future__ import annotations

import hashlib
import json
import math
import random

import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import SearchRun, raster_identity


STRATEGIES = ('reverse_coordinates', 'shuffled_coordinates', 'joint_restart',
              'fine_coordinates', 'geometry_pair', 'color_pair')


class Bot:
    def __init__(self, name, parameters, incumbent, rng):
        self.name = name
        self.parameters = parameters.copy()
        self.best = incumbent
        self.order = list(range(len(parameters)))
        if name == 'reverse_coordinates':
            self.order.reverse()
        elif name == 'shuffled_coordinates':
            rng.shuffle(self.order)
        self.cursor = self.proposals = self.stale = self.received = 0
        self.anchor = incumbent[0]
        self.improved = False
        self.active = True
        self.stop_reason = None

    def proposal(self, geometry_count, rng, seed):
        cursor = self.cursor
        self.cursor += 1
        probe = self.parameters.copy()
        if self.name in {'joint_restart', 'geometry_pair', 'color_pair'}:
            pool = list(range(len(probe)))
            if self.name == 'geometry_pair':
                pool = pool[:geometry_count]
            elif self.name == 'color_pair':
                pool = pool[geometry_count:]
            if not pool:
                return None
            # Joint restarts keep independent starts in addition to peer seeds.
            if self.name == 'joint_restart' and cursor % 3 == 0:
                probe = seed.copy()
            step = (.5, 1., 2., .25, 4., .125)[(cursor // 4) % 6]
            for index in rng.sample(pool, min(3 if self.name == 'joint_restart' else 2, len(pool))):
                probe[index] += rng.choice((-1, 1))*step*(4 if index >= geometry_count else 1)
        else:
            index = self.order[(cursor // 2) % len(self.order)]
            steps = (.125, .0625, .25, .5) if self.name == 'fine_coordinates' else (1., .5, .25, .125, .0625, 2.)
            step = steps[(cursor // (2*len(self.order))) % len(steps)]
            probe[index] += (-1 if cursor % 2 == 0 else 1)*step*(4 if index >= geometry_count else 1)
        return probe

    def record(self):
        return dict(strategy=self.name, proposals=self.proposals, error=self.best[1],
                    improved=self.improved, active=self.active, stop_reason=self.stop_reason,
                    received_messages=self.received)


class Blackboard:
    def __init__(self, parameters, incumbent, session, config, source, identity):
        self.seed = parameters.copy()
        self.best_p, self.best = parameters.copy(), incumbent
        self.rng = random.Random(config['seed'] ^ int(identity[:16], 16))
        self.bots = [Bot(name, parameters, incumbent, self.rng) for name in STRATEGIES]
        self.rng.shuffle(self.bots)
        self.seen = {tuple(np.round(parameters, 8)): dict(valid=True, loss=incumbent[0], error=incumbent[1])}
        self.monitor = SearchRun(session, config['budget'], source=source)
        self.monitor.anchor = incumbent[0]
        self.patience = max(8, session.policy.patience // len(self.bots))
        self.winning = self.reason = None
        self.generated = self.cache_hits = self.messages = 0


def explore_bots(parameters, geometry_count, measure, incumbent, *, source, image,
                 satisfactory_fn, session, config, emit):
    # The initial SVG and objective values distinguish parameterizations and
    # differently weighted fits even when they have the same source label.
    contract = [source, raster_identity(image), incumbent[2], parameters.tolist(),
                geometry_count, float(incumbent[0]), float(incumbent[1]), config['seed'], config['budget']]
    identity = hashlib.sha256(json.dumps(contract, allow_nan=False).encode()).hexdigest()
    board = session.bot_searches.get(identity)
    reused = board is not None
    if board is None:
        board = Blackboard(parameters, incumbent, session, config, source, identity)
        session.bot_searches[identity] = board
    monitor = board.monitor
    start_proposals, started = monitor.proposals, session.elapsed
    slice_size = max(1, min(8, config['budget']//len(board.bots)))
    # A fresh caller must run its own semantics, even for a previously checked fit.
    satisfactory = lambda: bool(satisfactory_fn and satisfactory_fn(board.best_p, board.best))
    if satisfactory():
        board.reason = 'satisfactory'
    elif board.reason == 'satisfactory':
        board.reason = None

    def retire(bot, reason):
        bot.active, bot.stop_reason = False, reason
        emit(source, event='bot_deactivated', **bot.record())

    while board.reason is None and board.generated < monitor.maximum*8:
        active = [bot for bot in board.bots if bot.active]
        if not active:
            board.reason = 'all_bots_inactive'
            break
        for bot in active:
            board.reason = monitor.reason(alternatives_tried=all(b.proposals or not b.active for b in board.bots))
            if board.reason:
                break
            if board.best[0] < bot.best[0]-1e-9:
                bot.parameters, bot.best = board.best_p.copy(), board.best
                bot.anchor = min(bot.anchor, board.best[0])
                bot.received += 1
                emit(source, event='bot_message', sender=board.winning, recipient=bot.name,
                     message='adopt_best', best_error=board.best[1])
                board.messages += 1
            emit(source, event='strategy_started', strategy=bot.name, proposals=monitor.proposals,
                 budget=monitor.limit, seed=config['seed'], best_error=board.best[1])
            used = generated = 0
            # A slice counts unique measurements; duplicate generation is bounded too.
            while used < slice_size and generated < 64 and board.generated < monitor.maximum*8:
                board.reason = monitor.reason(alternatives_tried=all(b.proposals or not b.active for b in board.bots))
                if board.reason:
                    break
                probe = bot.proposal(geometry_count, board.rng, board.seed)
                board.generated += 1
                generated += 1
                if probe is None:
                    retire(bot, 'no_parameters')
                    break
                key = tuple(np.round(probe, 8))
                if key in board.seen:
                    board.cache_hits += 1
                    continue
                measured = measure(probe)
                admissible = bool(measured is not None and math.isfinite(measured[0])
                                  and math.isfinite(measured[1]) and measured[1] <= incumbent[1]+1e-9)
                board.seen[key] = dict(valid=admissible,
                    loss=float(measured[0]) if measured is not None and math.isfinite(measured[0]) else None,
                    error=float(measured[1]) if measured is not None and math.isfinite(measured[1]) else None,
                    bot=bot.name)
                used += 1
                bot.proposals += 1
                bot.stale += 1
                if admissible and measured[0] < bot.best[0]-1e-9:
                    bot.parameters, bot.best = probe.copy(), measured
                if admissible and measured[0] < board.best[0]-1e-9 and measured[1] <= board.best[1]+1e-9:
                    board.best_p, board.best, board.winning = probe.copy(), measured, bot.name
                    session.observe(board.best[1], evaluation=False)
                    bot.improved = True
                # Peer messages alone never earn a worker more time.
                if admissible and bot.anchor-measured[0] >= max(1e-9, abs(bot.anchor)*session.policy.relative_gain):
                    bot.anchor, bot.stale = measured[0], 0
                monitor.observe(board.best[0])
                if satisfactory():
                    board.reason = 'satisfactory'
                    break
                if bot.stale >= board.patience:
                    retire(bot, 'stagnation')
                    break
            if bot.active and not used and not board.reason:
                retire(bot, 'duplicate_exhaustion')
            emit(source, event='strategy_finished', **bot.record(), best_error=board.best[1])
            if board.reason:
                break
    board.reason = board.reason or 'search_exhausted'
    records = [bot.record() for bot in board.bots]
    report = dict(seed=config['seed'], additional_evaluations=monitor.proposals-start_proposals,
        total_evaluations=monitor.proposals, winning_strategy=board.winning,
        budget=config['budget'], effective_budget=monitor.limit, max_budget=monitor.maximum,
        budget_extensions=monitor.extensions, stop_reason=board.reason, attempts=records,
        elapsed_seconds=round(session.elapsed-started, 6), reused_blackboard=reused,
        remembered_candidates=len(board.seen), duplicate_proposals=board.cache_hits,
        messages=board.messages, bot_patience=board.patience)
    if config['directory']:
        # Short paths also work in Windows checkouts without long-path support.
        target = config['directory']/'bots'
        target.mkdir(parents=True, exist_ok=True)
        evidence = dict(identity=identity, **report, trials=[dict(parameters=list(key), **value)
                        for key, value in board.seen.items()],
                        validation='search_loss_only_pending_semantic_and_pixel_gates')
        (target/(identity+'.json')).write_text(json.dumps(evidence, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    emit(source, event='search_finished', stop_reason=board.reason, proposals=monitor.proposals,
         budget=monitor.limit, best_error=board.best[1], messages=board.messages)
    return board.best_p.copy(), board.best, report
