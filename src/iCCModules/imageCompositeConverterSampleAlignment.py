"""Fit a whole uploaded assembly without moving or deleting its individual parts."""
from __future__ import annotations

import copy
import math
import time
import xml.etree.ElementTree as ET

import numpy as np


def _protected_grays(palette, initial):
    height,width = initial.shape[:2]
    return {rgb for rgb in palette if max(rgb)-min(rgb) <= 2 and max(rgb) <= 140
            and 0 < np.count_nonzero(np.max(abs(initial.astype(float)-rgb),axis=2) <= 8)
            <= width*height*.03}


def lightened_sample_details(sample, candidate, width, height, render_fn):
    """Compare retained small identity marks when the same template IDs exist."""
    from PIL import ImageColor
    old,new = ET.fromstring(sample),ET.fromstring(candidate)
    paints = {}
    for node in old.iter():
        if not node.get('id'):
            continue
        for attribute in ('fill','stroke'):
            try:
                rgb = ImageColor.getrgb(node.get(attribute,''))
            except ValueError:
                continue
            if len(rgb)==3:
                paints.setdefault(rgb,[]).append((node.get('id'),attribute))
    protected = _protected_grays(paints,render_fn(sample,width,height))
    by_id = {node.get('id'):node for node in new.iter() if node.get('id')}
    changed = []
    for rgb in protected:
        for identifier,attribute in paints[rgb]:
            node = by_id.get(identifier)
            if node is None:
                continue
            try:
                color = ImageColor.getrgb(node.get(attribute,''))
            except ValueError:
                continue
            if len(color)==3 and np.mean(color)>np.mean(rgb)+.5:
                changed.append(identifier)
    return changed


def align_sample(root, target, render_fn, *, deadline, initial, assertions=None):
    from PIL import ImageColor
    from src.imageConverterSample import NUMBER, SVG_NS
    from src.iCCModules.imageCompositeConverterStrokeConstraints import constrain_stroke_width, width_bindings

    height, width = target.shape[:2]
    reference = target.astype(np.float32)
    border = np.concatenate((reference[0], reference[-1], reference[:, 0], reference[:, -1]))
    background = np.median(border, axis=0)
    weights = 1 + 4*(np.max(abs(reference-background), axis=2) > 25)
    nodes = list(root.iter())
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
    # Small dark identity marks (for example +/-) must not be washed out to
    # compensate for residual alignment error in the much larger assembly.
    protected_gray = _protected_grays(palette,initial)
    paint_indices, values = [], [0., 0., 100., 100.]
    shared_width = bool(assertions and assertions.get('equal_stroke_width'))
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
                or (shared_width and not math.isclose(p[2], p[3], abs_tol=1e-8))):
            return False
        for rgb, (offset, gray) in zip(palette, paint_indices):
            color = np.repeat(p[offset], 3) if gray else p[offset:offset+3]
            if rgb in protected_gray and np.mean(color) > np.mean(rgb)+.5:
                return False
            contrast = float(np.max(abs(np.array(rgb)-background)))
            # Paint refinement must not hide an existing dark detail in the
            # background to reduce a globally averaged error.
            if contrast > 35 and np.max(abs(color-background)) < max(35, contrast*.35):
                return False
        return True

    def measure(pixels):
        squared = np.square(reference-pixels.astype(np.float32)).mean(axis=2)/255**2
        return float((squared*weights).mean()), float(squared.mean())

    best, mse = measure(initial)
    pixels, svg = initial, ET.tostring(root, encoding='unicode')
    evaluations = accepted = 0
    cache = {}

    def consider(p):
        nonlocal parameters, best, mse, pixels, svg, evaluations, accepted
        if time.monotonic() >= deadline or not valid(p):
            return False
        key = tuple(p)
        if key in cache:
            return False
        candidate = build(p)
        try:
            raster = render_fn(candidate, width, height)
        except ValueError:
            return False
        evaluations += 1
        loss, error = measure(raster)
        cache[key] = loss
        if loss < best-1e-10 and error <= mse+1e-12:
            parameters, best, mse, pixels, svg = p.copy(), loss, error, raster, candidate
            accepted += 1
            return True
        return False

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
            if shared_width:
                sx = sy = (sx+sy)/2
            scales = np.array([sx, sy])
            p[2:4] = scales*100
            p[:2] = ((observed[:2]+observed[2:])/2
                     - (np.array([width, height])/2
                        + ((predicted[:2]+predicted[2:])/2-np.array([width, height])/2)*scales))
            consider(p)
    # Alternate common geometry with shared paint. Individual paths, polygon
    # vertices, opacities and small-symbol dimensions are never edited here.
    for step, paint_step in [(2., 32.), (1., 16.), (.5, 8.), (.25, 4.), (.125, 2.), (.0625, 1.)]:
        steps = [step, step, 100*step/width, 100*step/height] + ([step] if bindings else [])
        steps += [paint_step]*(len(values)-len(steps))
        for _ in range(4):
            changed = False
            for index, delta in enumerate(steps):
                if shared_width and index == 3:
                    continue
                for sign in (-1, 1):
                    candidate = parameters.copy()
                    candidate[index] += sign*delta
                    if shared_width and index == 2:
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
                transform=dict(translate_x=float(parameters[0]), translate_y=float(parameters[1]),
                               scale_x=float(parameters[2]/100), scale_y=float(parameters[3]/100)))
