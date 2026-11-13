"""Small raster-supported native alternatives for the generic SVG fallback.

Contours estimate analytic primitives; they are never serialized as paths.
Probes share the active image deadline and cannot grant model validation.
"""
from __future__ import annotations

from collections import Counter
import copy
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex
from src.iCCModules.imageCompositeConverterPrimitiveScene import _circle
from src.iCCModules.imageCompositeConverterSearchPortfolio import progress

NS = 'http://www.w3.org/2000/svg'


def inventory(svg):
    root = ET.fromstring(svg)
    counts = Counter()
    def visit(node):
        tag = node.tag.rsplit('}', 1)[-1]
        if tag in {'defs', 'clipPath', 'mask', 'pattern', 'marker'}:
            return
        if tag in {'rect', 'circle', 'ellipse', 'line', 'polygon', 'polyline', 'path', 'text'}:
            counts[tag] += 1
        for child in node:
            visit(child)
    visit(root)
    return dict(counts)


def _primitive_scenes(image, session):
    pixels = image.astype(float)
    h, w = image.shape[:2]
    border = np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]))
    background = np.median(border, axis=0)
    contrast = np.max(abs(pixels-background), axis=2)
    masks = [contrast > threshold for threshold in (25, 55)]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    saturated = (hsv[:, :, 1] > 60) & (contrast > 25)
    histogram = np.bincount(hsv[:, :, 0][saturated], minlength=180)
    # Hue regions can separate a filled parent from achromatic attachments.
    for _ in range(3):
        peak = int(histogram.argmax())
        if histogram[peak] < 8:
            break
        distance = np.minimum(abs(np.arange(180)-peak), 180-abs(np.arange(180)-peak))
        masks.append(saturated & (distance[hsv[:, :, 0]] <= 15))
        histogram[distance <= 15] = 0
    seen = set()
    for mask in masks:
        if session.time_reason():
            return
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype('uint8'))
        components = []
        for i in sorted(range(1, count), key=lambda i: -stats[i, cv2.CC_STAT_AREA])[:8]:
            x, y, bw, bh, area = stats[i]
            if min(bw, bh) < 5 or area < 16 or area < bw*bh*.48:
                continue
            region = labels == i
            contours, _ = cv2.findContours(region.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            contour = max(contours, key=cv2.contourArea)
            center, radius, residual = _circle(contour)
            circular = (abs(bw-bh) <= max(2, .1*max(bw, bh))
                        and residual <= max(.8, radius*.06) and radius >= 3)
            core = cv2.erode(region.astype('uint8'), np.ones((3, 3), 'uint8')) > 0
            if core.sum() < 6:
                continue
            color = np.median(pixels[core], axis=0)
            core &= np.max(abs(pixels-color), axis=2) < 45
            if core.sum() < 6:
                continue
            components.append(dict(box=(x, y, bw, bh), center=center, radius=radius,
                                   circular=circular, core=core, color=color))
        if not components:
            continue
        for alternate in (False, True):
            for axis in (None, 0, 1):
                root = ET.Element(f'{{{NS}}}svg', width=str(w), height=str(h), viewBox=f'0 0 {w} {h}')
                defs = ET.SubElement(root, f'{{{NS}}}defs')
                ET.SubElement(root, f'{{{NS}}}rect', width=str(w), height=str(h), fill=_hex(background))
                for i, obj in enumerate(components):
                    x, y, bw, bh = obj['box']
                    fill = _hex(obj['color'])
                    if axis is not None:
                        yy, xx = np.where(obj['core'])
                        t = ((xx+.5-x)/bw if axis == 0 else (yy+.5-y)/bh)
                        colors = np.linalg.lstsq(np.c_[1-t, t], pixels[obj['core']], rcond=None)[0]
                        grad = ET.SubElement(defs, f'{{{NS}}}linearGradient', id=f'fallback{i}',
                                             x1='0%', y1='0%', x2='100%' if axis == 0 else '0%',
                                             y2='0%' if axis == 0 else '100%')
                        for offset, color in zip(('0', '1'), colors):
                            ET.SubElement(grad, f'{{{NS}}}stop', offset=offset, **{'stop-color': _hex(color)})
                        fill = f'url(#fallback{i})'
                    if obj['circular'] != alternate:
                        cx, cy = obj['center']
                        ET.SubElement(root, f'{{{NS}}}circle', cx=str(cx), cy=str(cy), r=str(obj['radius']), fill=fill)
                    else:
                        ET.SubElement(root, f'{{{NS}}}rect', x=str(x), y=str(y), width=str(bw), height=str(bh), fill=fill)
                svg = ET.tostring(root, encoding='unicode')
                if svg not in seen:
                    seen.add(svg)
                    yield svg


def _line_proposals(image, rendered, session):
    h, w = image.shape[:2]
    residual = np.max(abs(image.astype(float)-rendered.astype(float)), axis=2) > 35
    if residual.sum() < 5:
        return
    minimum = max(5, min(12, int(min(w, h)*.16)))
    delta = image.astype(float)-rendered.astype(float)
    # Separate opposite-polarity residuals: dark perimeter errors must not
    # drown out a long pale chord on a filled parent (or vice versa).
    masks = [np.max(delta, axis=2) > 35, np.min(delta, axis=2) < -35, residual]
    detected = []
    for mask in masks:
        lines = cv2.HoughLinesP(mask.astype('uint8'), 1, np.pi/180,
                               threshold=max(5, minimum//2), minLineLength=minimum, maxLineGap=2)
        if lines is not None:
            detected.extend(lines[:, 0])
    if not detected:
        return
    yy, xx = np.indices((h, w), dtype=float)
    xx, yy = xx+.5, yy+.5
    seen = []
    for raw in sorted(detected, key=lambda p: -np.hypot(p[2]-p[0], p[3]-p[1]))[:96]:
        if session.time_reason():
            return
        a, b = np.array(raw[:2], float)+.5, np.array(raw[2:], float)+.5
        length = np.linalg.norm(b-a)
        direction = (b-a)/length
        along = (xx-a[0])*direction[0]+(yy-a[1])*direction[1]
        across = abs((xx-a[0])*direction[1]-(yy-a[1])*direction[0])
        core = (across < .8) & (along >= 0) & (along <= length) & residual
        if core.sum() < minimum:
            continue
        strength = np.max(abs(delta), axis=2)
        strongest = core & (strength >= np.percentile(strength[core], 65))
        color = np.median(image[strongest], axis=0)
        coherent = np.max(abs(image.astype(float)-color), axis=2) < 65
        supported = coherent & residual & (across < 1.5) & (along >= -2) & (along <= length+2)
        # Each longitudinal interval needs observed paint, including pale marks
        # on colored parents. A large background cannot supply a line's score.
        bins = np.floor(along[supported]).astype(int)
        if len(set(bins[(bins >= 0) & (bins <= int(length))])) < .8*length:
            continue
        # Estimate antialiased coverage instead of treating every supported
        # pixel as a fully painted unit-width stroke.
        base_color = np.median(rendered[core], axis=0)
        paint_delta = color-base_color
        alpha = np.clip(np.sum(delta*paint_delta, axis=2)/max(1., np.dot(paint_delta, paint_delta)), 0, 1)
        band = (across < 2.5) & (along >= 0) & (along <= length)
        sw = float(np.clip(alpha[band].sum()/(length+1), .5, 3.))
        key = np.r_[a, b]
        if any(min(np.linalg.norm(key-old), np.linalg.norm(key-np.r_[old[2:], old[:2]])) < 4 for old in seen):
            continue
        seen.append(key)
        node = ET.Element(f'{{{NS}}}line', x1=str(a[0]), y1=str(a[1]), x2=str(b[0]), y2=str(b[1]),
                          stroke=_hex(color), **{'stroke-width': str(sw), 'stroke-linecap': 'butt'})
        yield node
        if len(seen) >= 12:
            return


def explore_structures(svg, image, initial, render_fn, session, assertions, *, mode='combined', max_probes=32):
    """Compare native complete constructions and residual add operations.

    No acceptance gates are weakened: explicit assertions are checked before
    rendering; changed pixels must improve locally and the full error must fall.
    A caller must still treat every result as an unvalidated draft.
    """
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions
    if mode not in {'primitives', 'lines', 'combined', 'legacy_combined', 'groups'}:
        raise ValueError('Unknown fallback structure mode')
    reference = image.astype(float)
    error = lambda raster: float(np.square(reference-raster.astype(float)).mean()/255**2)
    best = dict(svg=svg, rendered=initial, error=error(initial), origin='incumbent')
    report = dict(mode=mode, max_probes=max_probes, proposals=[], selected_origin='incumbent',
                  model_confirmed=False, stop_reason='proposals_exhausted', render_evaluations=0)
    if max(image.shape[:2]) > 512:
        report['stop_reason'] = 'raster_size_limit'
        return best, report
    h, w = image.shape[:2]

    def probe(candidate, origin, parent, regions=None):
        nonlocal best
        if session.time_reason() or len(report['proposals']) >= max_probes:
            return None
        row = dict(origin=origin, inventory=inventory(candidate), accepted=False)
        report['proposals'].append(row)
        try:
            validate_svg_assertions(candidate, assertions)
        except ValueError:
            row['rejection'] = 'description_assertions'
            return None
        report['render_evaluations'] += 1
        raster = render_fn(candidate, w, h)
        session.evaluations += 1
        if raster is None:
            row['rejection'] = 'render_failed'
            return None
        measured = error(raster)
        changed = np.max(abs(raster.astype(float)-parent['rendered'].astype(float)), axis=2) > 8
        before = np.square(reference-parent['rendered'].astype(float)).mean(axis=2)
        after = np.square(reference-raster.astype(float)).mean(axis=2)
        local_gain = float((before[changed]-after[changed]).mean()/255**2) if changed.any() else 0.
        row.update(error=measured, local_gain=local_gain, changed_pixels=int(changed.sum()))
        if regions:
            from src.iCCModules.imageCompositeConverterFallbackGroups import check_parts, check_relations
            row['parts'] = check_parts(image, raster, regions)
            row['relations'] = check_relations(candidate)
        # Never accept a mostly unsupported edit just because a tiny part helps.
        support = float((after[changed] < before[changed]).mean()) if changed.any() else 0.
        row['improved_fraction'] = support
        accepted = measured < parent['error']-1e-8 and local_gain > 1e-6 and support >= .6
        if 'native_object_group:' in parent['origin']:
            from src.iCCModules.imageCompositeConverterFallbackGroups import part_regions, check_parts
            protected = part_regions(parent['svg'], w, h)
            before_parts = check_parts(image, parent['rendered'], protected)
            after_parts = check_parts(image, raster, protected)
            if any((a['passed'] and not b['passed']) or b['normalized_mse'] > a['normalized_mse']+1/255**2
                   for a,b in zip(before_parts,after_parts)):
                accepted = False
                row['rejection'] = 'protected_group_part'
        if regions and not all(p['passed'] for p in row['parts']+row['relations']):
            accepted = False
            row['rejection'] = 'group_part_evidence'
        row['accepted'] = accepted
        if not accepted:
            row.setdefault('rejection', 'local_or_global_error')
        result = dict(svg=candidate, rendered=raster, error=measured, origin=origin)
        if accepted and measured < best['error']-1e-8:
            best = result
            session.observe(measured, evaluation=False)
        progress('native_svg_structure', event='structure_probe', **row)
        return result if accepted else None

    bases = [best]
    if mode in {'groups', 'combined'}:
        from src.iCCModules.imageCompositeConverterFallbackGroups import group_proposals, part_regions
        for candidate, family in group_proposals(image, session):
            if session.time_reason() or len(report['proposals']) >= min(8, max_probes):
                break
            regions = part_regions(candidate, w, h)
            probe(candidate, 'native_object_group:'+family, bases[0], regions)
    if mode in {'primitives', 'combined', 'legacy_combined'}:
        for candidate in _primitive_scenes(image, session):
            result = probe(candidate, 'raster_primitive_reconstruction', bases[0])
            if result:
                bases.append(result)
            if session.time_reason() or len(report['proposals']) >= min(12, max_probes):
                break
    if mode in {'lines', 'combined', 'legacy_combined'}:
        # Reserve line work for the original and the best alternate, rather than
        # spending all probes on descendants of the initially chosen topology.
        parents = [bases[0]] + ([best] if best is not bases[0] else [])
        for parent in parents:
            current = parent
            for line in _line_proposals(image, parent['rendered'], session):
                root = ET.fromstring(current['svg'])
                if sum(inventory(current['svg']).values()) >= 48:
                    break
                root.append(copy.deepcopy(line))
                candidate = ET.tostring(root, encoding='unicode')
                result = probe(candidate, parent['origin']+'+residual_line_group', current)
                if result:
                    current = result
                if session.time_reason() or len(report['proposals']) >= max_probes:
                    break
    report.update(selected_origin=best['origin'], selected_inventory=inventory(best['svg']),
                  probe_count=len(report['proposals']),
                  stop_reason='time_limit' if session.time_reason() else
                  ('probe_limit' if len(report['proposals']) >= max_probes else report['stop_reason']))
    progress('native_svg_structure', event='structure_search_finished', **report)
    return best, report
