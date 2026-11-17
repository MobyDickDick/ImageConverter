"""Counterfactual edits of arbitrary native SVGs, including transformed seeds.

Proposals are hypotheses, not protected objects. Only a fresh render against
the source can justify keeping, moving, replacing or removing one.
"""
from __future__ import annotations

import copy
from xml.etree import ElementTree as ET

from src.iCCModules.imageCompositeConverterFallbackComposition import atoms, at, bounds
from src.iCCModules.imageCompositeConverterAdaptiveSearch import candidate_identity
from src.iCCModules.imageCompositeConverterSearchPortfolio import proposal_rng


def _edits(svg, width, height, *, operation, rng=None):
    root = ET.fromstring(svg)
    objects = list(atoms(root))
    if rng is not None:
        rng.shuffle(objects)
    # Recent overlays are often compensating for another wrong object. Do not
    # exclude white paint, transformed atoms or large bars from counterprobes.
    for path, _ in reversed(objects) if operation == 'remove' else ():
        candidate = copy.deepcopy(root)
        at(candidate, path[:-1]).remove(at(candidate, path))
        yield ET.tostring(candidate, encoding='unicode'), 'remove'
    if operation == 'remove':
        return
    # A wrong overlay and the wrong object it compensates for may need to go
    # together. These branches may temporarily be worse than the incumbent.
    recent = list(reversed(objects))[:8]
    for i, (a, _) in enumerate(recent) if operation == 'remove_pair' else ():
        for b, _ in recent[i+1:]:
            candidate = copy.deepcopy(root)
            for path in sorted((a, b), reverse=True):
                at(candidate, path[:-1]).remove(at(candidate, path))
            yield ET.tostring(candidate, encoding='unicode'), 'remove_pair'
    try:
        view = [float(v) for v in root.get('viewBox', f'0 0 {width} {height}').replace(',', ' ').split()]
        vw, vh = view[2:]
    except (ValueError, IndexError):
        return
    # Move objects independently of their assembly. Transforms are composed in
    # the original local coordinate system rather than guessing screen bounds.
    for path, _ in reversed(objects) if operation == 'move_object' else ():
        steps = [(-vw*.05, 0), (vw*.05, 0), (0, -vh*.05), (0, vh*.05),
                 (-1, 0), (1, 0), (0, -1), (0, 1)]
        if rng is not None:
            # Other seeds reach other subpixel and coupled placements, not
            # merely another permutation of the same finite list.
            steps += [(rng.uniform(-1, 1)*vw*f, rng.uniform(-1, 1)*vh*f)
                      for f in (.005, .015, .04, .1)]
            rng.shuffle(steps)
        for dx, dy in steps:
            candidate = copy.deepcopy(root)
            node = at(candidate, path)
            node.set('transform', f'translate({dx:g} {dy:g}) '+node.get('transform', ''))
            yield ET.tostring(candidate, encoding='unicode'), 'move_object'
    for path, node in reversed(objects) if operation == 'resize_object' else ():
        box = bounds(node, width, height)
        if box is None:
            continue
        cx, cy = (box[:2]+box[2:])/2
        scales = [(.8, 1), (1.25, 1), (1, .8), (1, 1.25), (.8, .8), (1.25, 1.25)]
        if rng is not None:
            scales += [(rng.uniform(.65, 1.5), rng.uniform(.65, 1.5)) for _ in range(4)]
            rng.shuffle(scales)
        for sx, sy in scales:
            candidate = copy.deepcopy(root)
            changed = at(candidate, path)
            changed.set('transform', f'translate({cx:g} {cy:g}) scale({sx:g} {sy:g}) '
                        f'translate({-cx:g} {-cy:g}) '+changed.get('transform', ''))
            yield ET.tostring(candidate, encoding='unicode'), 'resize_object'
    # Layer order is a construction decision too; it is not a paint parameter.
    for parent in root.iter() if operation == 'layer_order' else ():
        if parent.tag.rsplit('}', 1)[-1] not in {'svg', 'g'}:
            continue
        parent_index = list(root.iter()).index(parent)
        slots = list(range(len(parent)-1))
        if rng is not None:
            rng.shuffle(slots)
        for i in slots:
            candidate = copy.deepcopy(root)
            target = list(candidate.iter())[parent_index]
            a, b = target[i], target[i+1]
            target[i], target[i+1] = b, a
            yield ET.tostring(candidate, encoding='unicode'), 'layer_order'


def native_edits(svg, width, height, *, level, seed=None):
    # Interleave operation families: a large SVG's deletion candidates must
    # not consume the whole slice before movement or layer changes get a turn.
    operations = ['remove'] if level < 2 else ['remove', 'remove_pair', 'move_object', 'resize_object', 'layer_order']
    identity = candidate_identity(svg)
    order_rng = proposal_rng('native_edit_order', [identity, level], seed=seed)
    if order_rng is not None:
        order_rng.shuffle(operations)
    active = [_edits(svg, width, height, operation=operation,
        rng=proposal_rng('native_edit:'+operation, [identity, level], seed=seed)) for operation in operations]
    while active:
        for proposals in list(active):
            try:
                yield next(proposals)
            except StopIteration:
                active.remove(proposals)
