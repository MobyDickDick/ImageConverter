"""Bounded native instance edits over raster-derived proposals.

The agenda contains incomplete scenes too. Only a complete scene with the
requested inventory may enter registration; acceptance belongs to its caller.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy

import numpy as np


def object_key(obj):
    return (obj['kind'], *np.round(np.r_[obj['geometry'], obj['colors']], 3))


def scene_key(objects):
    # The parent has a fixed painter role. Disjoint children are unordered.
    return (object_key(objects[0]), *sorted(object_key(obj) for obj in objects[1:]))


def complete(objects, counts):
    return Counter(obj['kind'] for obj in objects[1:]) == Counter(counts)


def _overlap(a, b):
    ax, ay, aw, ah = a['geometry'][:4]
    bx, by, bw, bh = b['geometry'][:4]
    return min(ax+aw, bx+bw) > max(ax, bx) and min(ay+ah, by+bh) > max(ay, by)


def edit_proposals(seeds, counts, *, max_states=96, stats=None):
    """Yield one bounded agenda step at a time, including rejected structures.

    Every new instance is observed in a segmentation. Missing classes can be
    replaced by another native class at an observed location; full raster
    registration must establish whether that alternative is actually useful.
    No image IDs, catalogue geometry, or saved vectors are used.
    """
    stats = stats if stats is not None else {}
    stats.update(states=0, state_limit_reached=False, candidate_limit_reached=False)
    pool = {}
    queue, seen = deque(), set()
    for objects in seeds:
        if not objects:
            continue
        key = scene_key(objects)
        if key not in seen:
            seen.add(key)
            queue.append((objects, ()))
        for obj in objects[1:]:
            pool.setdefault(object_key(obj), obj)
    # Candidate count and visited-state count both have hard limits. A long
    # noisy segmentation cannot create an unbounded combination search.
    candidates = list(pool.values())[:32]
    stats['candidate_limit_reached'] = len(pool) > len(candidates)
    visited = 0
    while queue and visited < max_states:
        objects, edits = queue.popleft()
        visited += 1
        stats['states'] = visited
        if edits:
            yield dict(objects=deepcopy(objects), edits=list(edits), complete=complete(objects, counts))
        else:
            yield None
        inventory = Counter(obj['kind'] for obj in objects[1:])
        target = Counter(counts)
        successors = []
        for i, obj in enumerate(objects[1:], 1):
            if inventory[obj['kind']] > target[obj['kind']]:
                successors.append((objects[:i]+objects[i+1:], 'remove'))
        for candidate in candidates:
            if inventory[candidate['kind']] < target[candidate['kind']]:
                if not any(_overlap(candidate, obj) for obj in objects[1:]):
                    successors.append(([*objects, candidate], 'add'))
        for i, obj in enumerate(objects[1:], 1):
            alternatives = list(candidates)
            for kind in counts:
                if kind != obj['kind'] and inventory[kind] < target[kind]:
                    alternate = deepcopy(obj)
                    alternate['kind'] = kind
                    if kind == 'circle':
                        # A native circle needs a square bounding box.
                        x, y, w, h = alternate['geometry'][:4]
                        size = min(w, h)
                        alternate['geometry'][:4] = [x+(w-size)/2, y+(h-size)/2, size, size]
                    alternatives.append(alternate)
            for candidate in alternatives:
                if object_key(candidate) == object_key(obj):
                    continue
                if candidate['kind'] != obj['kind'] and not (
                        inventory[obj['kind']] > target[obj['kind']]
                        and inventory[candidate['kind']] < target[candidate['kind']]):
                    continue
                # Replacement changes one observed location, not a jump to
                # an unrelated missing instance. Those are Remove + Add.
                if not _overlap(candidate, obj):
                    continue
                others = objects[1:i]+objects[i+1:]
                if any(_overlap(candidate, other) for other in others):
                    continue
                successors.append((objects[:i]+[candidate]+objects[i+1:], 'replace'))
        for proposal, operation in successors:
            key = scene_key(proposal)
            if key in seen:
                continue
            if len(seen) >= max_states:
                stats['state_limit_reached'] = True
                break
            seen.add(key)
            queue.append((proposal, (*edits, operation)))
