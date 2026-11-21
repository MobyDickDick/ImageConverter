"""Fit a whole uploaded assembly without moving or deleting its individual parts."""
from __future__ import annotations

import copy
import math
import time
import xml.etree.ElementTree as ET

import numpy as np


def lightened_sample_details(*args,**kwargs):
    """Compatibility for a running older GUI; lighter paint is not a defect.

    Current selection compares independently rendered pixels against the raster
    source instead of assigning a penalty for departing from template shades.
    """
    return []


def align_sample(root, target, render_fn, *, deadline, initial, assertions=None, seed=0):
    from PIL import ImageColor
    from src.imageConverterSample import NUMBER, SVG_NS
    from src.iCCModules.imageCompositeConverterStrokeConstraints import constrain_stroke_width, width_bindings
    from src.iCCModules.imageCompositeConverterSearchPortfolio import proposal_rng
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, pixel_quality
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions

    height, width = target.shape[:2]
    reference = target.astype(np.float32)
    border = np.concatenate((reference[0], reference[-1], reference[:, 0], reference[:, -1]))
    background = np.median(border, axis=0)
    weights = 1 + 4*(np.max(abs(reference-background), axis=2) > 25)
    nodes = list(root.iter())
    rng = proposal_rng('sample_alignment', ET.tostring(root,encoding='unicode'), seed=seed)
    remaining = max(.001,deadline-time.monotonic())
    audit = ImageSearch(SearchPolicy(seconds=remaining,max_seconds=remaining))
    audit.search_seed = seed
    paints = {}
    for index, node in enumerate(nodes):
        for attribute in ('fill', 'stroke', 'stop-color'):
            try:
                rgb = ImageColor.getrgb(node.get(attribute, ''))
            except ValueError:
                continue
            if len(rgb) == 3:
                paints.setdefault(rgb, []).append((index, attribute))
    palette = list(paints)
    paint_indices, values = [], [0., 0., 100., 100.]
    shared_width = bool(assertions and assertions.get('equal_stroke_width'))
    equal_axes = shared_width or any((assertions or {}).get('objects',{}).get(kind)
                                    for kind in ('square','circle','rhombus'))
    bindings = width_bindings(root) if shared_width else []
    if bindings:
        values.append(bindings[0][2]*bindings[0][3])
    for rgb in palette:
        gray = max(rgb)-min(rgb) <= 2
        paint_indices.append((len(values), gray))
        values.extend([float(np.mean(rgb))] if gray else rgb)
    parameters = np.array(values, dtype=float)
    vx, vy, vw, vh = map(float, NUMBER.findall(root.get('viewBox')))
    aspect = root.get('preserveAspectRatio', 'xMidYMid meet').split()
    if aspect and aspect[0] == 'defer':
        aspect = aspect[1:]
    ax, ay = width/vw, height/vh
    if not aspect or aspect[0] != 'none':
        ax = ay = max(ax, ay) if 'slice' in aspect else min(ax, ay)
        alignment = aspect[0] if aspect else 'xMidYMid'
        fx = 0. if 'xMin' in alignment else 1. if 'xMax' in alignment else .5
        fy = 0. if 'YMin' in alignment else 1. if 'YMax' in alignment else .5
    else:
        fx = fy = 0.
    ox, oy = -vx*ax+(width-vw*ax)*fx, -vy*ay+(height-vh*ay)*fy

    def build(p):
        candidate = copy.deepcopy(root)
        elements = list(candidate.iter())
        for rgb, (offset, gray) in zip(palette, paint_indices):
            color = np.repeat(p[offset], 3) if gray else p[offset:offset+3]
            color = '#%02x%02x%02x' % tuple(np.rint(color).astype(int))
            for index, attribute in paints[rgb]:
                elements[index].set(attribute, color)
        sx, sy = p[2:4]/100
        tx = ((sx-1)*(ox-width/2)+p[0])/ax
        ty = ((sy-1)*(oy-height/2)+p[1])/ay
        group = ET.Element(f'{{{SVG_NS}}}g', transform=(
            f'matrix({sx:.8f} 0 0 {sy:.8f} {tx:.8f} {ty:.8f})'))
        for child in list(candidate):
            if child.tag.rsplit('}', 1)[-1] not in {'defs', 'style', 'title', 'desc', 'metadata'}:
                candidate.remove(child)
                group.append(child)
        candidate.append(group)
        return constrain_stroke_width(ET.tostring(candidate, encoding='unicode'), assertions,
                                      width=p[4] if bindings else None)

    def valid(p):
        if (not np.isfinite(p).all() or not (10 <= p[2] <= 400 and 10 <= p[3] <= 400)
                or abs(p[0]) > width*2 or abs(p[1]) > height*2
                or np.any(p[4:] < 0) or np.any(p[4:] > 255)
                or (bindings and p[4] <= 0)
                or (equal_axes and not math.isclose(p[2], p[3], abs_tol=1e-8))):
            return False
        for rgb, (offset, gray) in zip(palette, paint_indices):
            color = np.repeat(p[offset], 3) if gray else p[offset:offset+3]
            contrast = float(np.max(abs(np.array(rgb)-background)))
            # Paint refinement must not hide an existing dark detail in the
            # background to reduce a globally averaged error.
            surface = all(attribute=='fill' and nodes[index].tag.rsplit('}',1)[-1]
                          in {'rect','circle','ellipse','polygon','path'} for index,attribute in paints[rgb])
            if not surface and contrast > 35 and np.max(abs(color-background)) < max(35, contrast*.35):
                return False
        return True

    def measure(pixels):
        squared = np.square(reference-pixels.astype(np.float32)).mean(axis=2)/255**2
        return float((squared*weights).mean()), float(squared.mean())

    best, mse = measure(initial)
    pixels, svg = initial, ET.tostring(root, encoding='unicode')
    evaluations = accepted = 0
    cache = {}
    rejected, restarts = 0, 0

    def consider(p):
        nonlocal parameters, best, mse, pixels, svg, evaluations, accepted, rejected
        if time.monotonic() >= deadline or not valid(p):
            return False
        key = tuple(p)
        if key in cache:
            return False
        candidate = build(p)
        try:
            validate_svg_assertions(candidate, assertions)
            raster, fresh = audit.render_candidate(target,candidate,render_fn,width,height)
        except ValueError:
            rejected += 1
            return False
        evaluations += int(fresh)
        if raster is None:
            return False
        loss, error = measure(raster)
        cache[key] = loss
        if loss < best-1e-10 and error <= mse+1e-12:
            parameters, best, mse, pixels, svg = p.copy(), loss, error, raster, candidate
            accepted += 1
            return True
        return False

    # Calibrate paint before geometry can shrink a wrongly colored surface.
    # Black/white renders measure coverage only; final proposals still pass
    # the original detail-contrast guard and the full description validation.
    for rgb,(offset, gray) in zip(palette,paint_indices):
        # Neutral paint already has a single local brightness coordinate.
        # Reserve the early analytic stage for chromatic filled surfaces;
        # fitting rims/gradient stops before pose would absorb geometry errors.
        surface = all(attribute=='fill' and nodes[index].tag.rsplit('}',1)[-1]
                      in {'rect','circle','ellipse','polygon','path'} for index,attribute in paints[rgb])
        if gray or not surface:
            continue
        if time.monotonic() >= deadline:
            break
        anchor = parameters.copy()
        probes = []
        for value in (0.,255.):
            probe = anchor.copy()
            probe[offset:offset+(1 if gray else 3)] = value
            candidate = build(probe)
            try:
                validate_svg_assertions(candidate,assertions)
                raster,fresh = audit.render_candidate(target,candidate,render_fn,width,height)
            except ValueError:
                rejected += 1
                probes = []
                break
            evaluations += int(fresh)
            if raster is None:
                probes = []
                break
            probes.append(raster.astype(float))
        if len(probes)!=2:
            continue
        black,white = probes
        alpha = (white-black)/255.
        denominator = np.square(alpha).sum(axis=(0,1))
        if denominator.min()<.1:
            continue
        numerator = (alpha*(reference-black)).sum(axis=(0,1))
        color = numerator.sum()/denominator.sum() if gray else numerator/denominator
        anchor[offset:offset+(1 if gray else 3)] = np.clip(color,0,255)
        consider(anchor)

    def bounds(image):
        contrast = np.max(abs(image.astype(float)-background), axis=2)
        ys, xs = np.where(contrast > 35)
        if not len(xs):
            return None
        return np.array([xs.min(), ys.min(), xs.max()+1, ys.max()+1], dtype=float)

    observed, predicted = bounds(target), bounds(initial)
    if observed is not None and predicted is not None:
        sizes = (observed[2:]-observed[:2])/(predicted[2:]-predicted[:2])
        for sx, sy in [(1., 1.), (float(np.mean(sizes)),)*2, tuple(sizes),
                       *[(s, s) for s in (.25, .5, .75, .9, 1.1, 1.5, 2.)]]:
            p = np.array(values, dtype=float)
            if equal_axes:
                sx = sy = (sx+sy)/2
            scales = np.array([sx, sy])
            p[2:4] = scales*100
            p[:2] = ((observed[:2]+observed[2:])/2
                     - (np.array([width, height])/2
                        + ((predicted[:2]+predicted[2:])/2-np.array([width, height])/2)*scales))
            consider(p)
    # Correlated jumps explore another placement/scale even when no individual
    # coordinate improves. Keep exact, already passing assemblies untouched.
    if not pixel_quality(target,pixels)['passed']:
        anchor = parameters.copy()
        for _ in range(8):
            if time.monotonic() >= deadline:
                break
            probe = anchor.copy()
            probe[:2] += np.array([rng.uniform(-.15,.15)*width,rng.uniform(-.15,.15)*height])
            probe[2:4] *= rng.uniform(.7,1.3)
            consider(probe)
            restarts += 1
    # Alternate common geometry with shared paint. Individual paths, polygon
    # vertices, opacities and small-symbol dimensions are never edited here.
    for step, paint_step in [(2., 32.), (1., 16.), (.5, 8.), (.25, 4.), (.125, 2.), (.0625, 1.)]:
        steps = [step, step, 100*step/width, 100*step/height] + ([step] if bindings else [])
        steps += [paint_step]*(len(values)-len(steps))
        for _ in range(4):
            changed = False
            order = list(enumerate(steps))
            rng.shuffle(order)
            signs = [-1,1]
            rng.shuffle(signs)
            for index, delta in order:
                if equal_axes and index == 3:
                    continue
                for sign in signs:
                    candidate = parameters.copy()
                    candidate[index] += sign*delta
                    if equal_axes and index == 2:
                        candidate[3] = candidate[2]
                    changed = consider(candidate) or changed
                if time.monotonic() >= deadline:
                    break
            if not changed or time.monotonic() >= deadline:
                break
        if time.monotonic() >= deadline:
            break
    return dict(svg=svg, rendered=pixels, error=mse, weighted_error=best,
                evaluations=evaluations, accepted=accepted,
                search_control=dict(seed=str(seed),restarts=restarts,rejected_candidates=rejected,
                    candidate_evaluations=evaluations,scope='whole_assembly',
                    render_sequence_sha256=audit.report()['render_sequence_sha256'],
                    stop_reason=('quality_target_reached' if pixel_quality(target,pixels)['passed'] else
                                 'time_limit' if time.monotonic()>=deadline else 'schedule_exhausted')),
                transform=dict(translate_x=float(parameters[0]), translate_y=float(parameters[1]),
                               scale_x=float(parameters[2]/100), scale_y=float(parameters[3]/100)))
