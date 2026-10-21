"""Observed native outlines and typed depth/containment constraints (at most 3 objects)."""
from __future__ import annotations

import itertools
import re

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search
from src.iCCModules.imageCompositeConverterSceneFusion import _arc, fusion_contract


from src.iCCModules.imageCompositeConverterSceneReferences import (
    parse_references, resolve_references, position_agrees)


def requested(description):
    text = str(description or '').casefold()
    text = re.sub(r'\b(?:(?:auf|vor)\s+(?:einem\s+)?)?weiss\w*\s+hintergrund\b', '', text)
    text = text.replace('eine form liegt getrennt.', '')
    return bool(re.search(r'überdeck|überlapp', text) and
                re.search(r'kontur|umriss|rand|innerhalb|verschachtel|vordergrund|hintergrund|vorne|hinten|davor|dahinter|\bvor\b|\bhinter\b|\bform\b', text))


def visibility_contract(description):
    parsed = parse_references(description)
    if parsed is None:
        return None
    text, relations = parsed
    outlined = 'jede form hat eine dunkle kontur.' in text
    if outlined:
        text = text.replace('jede form hat eine dunkle kontur.', '')
    contract = fusion_contract(text)
    if contract is None or not contract.get('overlap'):
        return None
    n = sum(contract['counts'].values())
    allowed = {r.casefold() for r in (('kleinere', 'größere') if n == 2 else ('kleinste', 'größte', 'mittelgroße'))}
    from src.iCCModules.imageCompositeConverterSceneReferences import SIZE_ROLES
    if any(role in SIZE_ROLES and role not in allowed for a, _, b in relations for role in (a, b)):
        return None
    # Only explicitly named containment pairs can coexist with partial overlap.
    if n == 2 and any(r == 'innerhalb' for _, r, _ in relations):
        return None
    edges = {(b, a) if r in ('vor', 'innerhalb') else (a, b) for a, r, b in relations
             if r in ('vor', 'hinter', 'innerhalb')}
    closure = set(edges)
    for _ in range(n):
        closure |= {(a, d) for a, b in closure for c, d in closure if b == c}
    if any(a == b for a, b in closure):
        return None
    return dict(contract, outlined=outlined, relations=relations)


def _outline(pixels, kind, geometry, fill):
    """Measure dark bands along exposed fill normals, requiring real outer support.

    Circle arcs need half a turn of observed stroke. Each rectangle side needs
    its own exposed stroke and white exterior; a hidden side remains unknown.
    """
    x, y, w, h, _ = geometry
    samples = []
    if kind == 'circle':
        for angle in np.linspace(0, 2*np.pi, 96, endpoint=False):
            normal = np.array([np.cos(angle), np.sin(angle)])
            samples.append((np.array([x+w/2, y+h/2])+normal*w/2, normal, 0, angle))
    else:
        for t in np.linspace(.08, .92, 32):
            samples.extend([(np.array([x, y+t*h]), np.array([-1., 0]), 0, t),
                            (np.array([x+w, y+t*h]), np.array([1., 0]), 1, t),
                            (np.array([x+t*w, y]), np.array([0., -1]), 2, t),
                            (np.array([x+t*w, y+h]), np.array([0., 1]), 3, t)])
    measured, colors, supports = [], [], []
    distances = np.arange(-2., 11.01, .25)
    for point, normal, side, angle in samples:
        coords = np.floor(point+distances[:, None]*normal).astype(int)
        if (coords < 0).any() or (coords[:, 0] >= pixels.shape[1]).any() or (coords[:, 1] >= pixels.shape[0]).any():
            continue
        values = pixels[coords[:, 1], coords[:, 0]].astype(float)
        # The ray must start inside this fill, pass through a dark band and
        # then leave it. Other fills/occluder edges cannot supply a missing side.
        if np.max(abs(values[0]-fill)) > 18:
            continue
        dark = (values.max(axis=1) < 100) & (values.mean(axis=1) < fill.mean()-20)
        runs = np.where(np.diff(np.r_[False, dark, False].astype(int)))[0].reshape(-1, 2)
        if not len(runs):
            continue
        start, end = runs[0]
        if not -.8 <= distances[start] <= 1.8 or end >= len(values)-2:
            continue
        sw = (end-start)*.25
        if not .7 <= sw <= 6:
            continue
        outside = values[min(end+8, len(values)-1)]
        if kind == 'rectangle' and np.min(outside) < 245:
            continue
        if np.max(abs(outside-fill)) < 20:
            continue
        measured.append(sw)
        colors.extend(values[start:end])
        supports.append((side, angle))
    if kind == 'circle':
        angles = np.sort([a for _, a in supports])
        if len(angles) < 32 or 2*np.pi-np.diff(np.r_[angles, angles[0]+2*np.pi]).max() < np.pi:
            return None
    elif any(sum(s == side for s, _ in supports) < 6 for side in range(4)):
        return None
    if not measured:
        return None
    sw = float(np.median(measured))
    # The color boundary is the inner stroke edge; move to the centerline.
    result = [x-sw/2, y-sw/2, w+sw, h+sw, sw]
    return dict(kind=kind, geometry=result, fill=fill, stroke=np.median(colors, axis=0),
                detectors=['visible_outline_'+('arc' if kind == 'circle' else 'sides')])


def outlined_candidates(pixels):
    values = pixels[np.max(255-pixels.astype(float), axis=2) > 25]
    bins, counts = np.unique(values.astype(int)//16, axis=0, return_counts=True)
    candidates, used = [], []
    for index in np.argsort(-counts, kind='stable')[:16]:
        session = current_search()
        if session and session.time_reason():
            break
        if counts[index] < 20:
            continue
        color = np.median(values[np.all(values.astype(int)//16 == bins[index], axis=1)], axis=0)
        if color.max() < 100 or any(np.max(abs(color-old)) <= 12 for old in used):
            continue
        used.append(color)
        mask = (np.max(abs(pixels.astype(float)-color), axis=2) <= 12).astype('uint8')
        number, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
        for label in range(1, number):
            x, y, w, h, area = stats[label]
            if area < 20 or min(w, h) < 7:
                continue
            component = (labels == label).astype('uint8')
            if cv2.distanceTransform(component, cv2.DIST_L2, 3).max() < 2.5:
                continue
            contour = max(cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
            arc = _arc(contour, pixels.shape[:2])
            proposals = [('rectangle', [float(x), float(y), float(w), float(h), 0.])]
            if arc is not None:
                proposals.append(('circle', arc))
            for kind, geometry in proposals:
                candidate = _outline(pixels, kind, geometry, color)
                if candidate is not None:
                    candidates.append(candidate)
    # Complete rings also expose contained objects whose outer side sees a
    # parent fill rather than the white canvas. Their native closed boundaries
    # supply that evidence; partial rectangles still require four exposed sides.
    from src.iCCModules.imageCompositeConverterLayeredScene import detect_instances, _box
    candidates.extend(dict(c, detectors=['complete_outline']) for g in detect_instances(pixels)
                      for c in g if c['geometry'][4] and c['fill'] is not None)
    groups = []
    for c in candidates:
        group = next((g for g in groups if np.max(abs(_box(c)-_box(g[0]))) <= 3), None)
        if group is None:
            groups.append([c])
        elif not any(old['kind'] == c['kind'] for old in group):
            group.append(c)
    return groups


def compatible(scene, contract):
    from src.iCCModules.imageCompositeConverterLayeredScene import _contains, _box
    from src.iCCModules.imageCompositeConverterSceneFusion import compatible as partial
    if any(sum(c['kind'] == kind for c in scene) != n for kind, n in contract['counts'].items()):
        return False
    if any(c['fill'] is None or bool(c['geometry'][4]) != contract['outlined'] for c in scene):
        return False
    roles = resolve_references(scene, contract['relations'])
    if roles is None:
        return False
    nested = set()
    for a, relation, b in contract['relations']:
        i, j = roles[a], roles[b]
        if i == j:
            return False  # Different names can still refer to the same object.
        if relation == 'innerhalb':
            if not _contains(scene[j], scene[i]) or j >= i:
                return False
            nested.add((j, i))
        elif (relation == 'vor' and i <= j) or (relation == 'hinter' and i >= j):
            return False
        elif relation in ('links von', 'rechts von', 'oberhalb', 'unterhalb') and not position_agrees(scene[i], relation, scene[j]):
            return False
    overlaps, observed_nested = 0, set()
    for i, j in itertools.combinations(range(len(scene)), 2):
        a, b = scene[i], scene[j]
        if _contains(a, b):
            observed_nested.add((i, j))
            continue
        if _contains(b, a):
            return False  # An enclosing opaque fill cannot erase its child.
        # The existing exact native partial-intersection test owns tangency
        # and containment uncertainty. Stroke outer envelopes are used here.
        pair = [dict(c, geometry=[*_box(c)[:2], *(_box(c)[2:]-_box(c)[:2]), 0.]) for c in (a, b)]
        counts = {kind: sum(c['kind'] == kind for c in pair) for kind in ('circle', 'rectangle')}
        intersects = partial(pair, dict(counts=counts, overlap=True))
        ba, bb = _box(a), _box(b)
        if not intersects and np.all(np.minimum(ba[2:], bb[2:])-np.maximum(ba[:2], bb[:2]) > -1):
            return False
        overlaps += intersects
    return overlaps > 0 and observed_nested == nested and (not contract.get('separate_instance') or overlaps == 1)


def fit_visibility_scene(width, height, *, description, image, render_fn, error_fn):
    from src.iCCModules.imageCompositeConverterLayeredScene import fit_scene_groups
    from src.iCCModules.imageCompositeConverterSceneFusion import fuse_candidates
    contract = visibility_contract(description)
    if contract is None:
        return None
    pixels = np.asarray(image)
    if pixels.shape != (height, width, 3) or min(width, height) < 16 or not np.isfinite(pixels).all():
        return None
    border = np.concatenate([pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]])
    if np.max(abs(border.astype(float)-255)) > 3:
        return None
    groups = outlined_candidates(pixels) if contract['outlined'] else fuse_candidates(pixels)
    yy, xx = np.indices((height, width), dtype=float)

    def observed_order(scene, constraints):
        if not compatible(scene, constraints):
            return False
        cores, envelopes = [], []
        for c in scene:
            x, y, w, h, sw = c['geometry']
            distance = (np.hypot(xx+.5-x-w/2, yy+.5-y-h/2)-w/2 if c['kind'] == 'circle' else
                        np.maximum(abs(xx+.5-x-w/2)-w/2, abs(yy+.5-y-h/2)-h/2))
            cores.append(distance < -sw/2-2)
            envelopes.append(distance < sw/2+2)
        # A painter-order claim needs observed shared interior support. A good
        # whole-object score alone could tolerate an incorrectly painted lens.
        for i, j in itertools.combinations(range(len(scene)), 2):
            lens = cores[i] & cores[j]
            for later in range(j+1, len(scene)):
                lens &= ~envelopes[later]
            if not lens.any():
                continue
            if lens.sum() < 8 or np.mean(np.max(abs(pixels[lens].astype(float)-scene[j]['fill']), axis=1) <= 24) < .85:
                return False
        return True

    return fit_scene_groups(width, height, image=pixels, groups=groups, contract=contract,
        render_fn=render_fn, error_fn=error_fn, compatible_fn=observed_order, all_orders=True,
        source='primitive_visibility_scene_v1')
