"""Raster-derived gradient circles containing disjoint flat native shapes.

The closed description contract controls topology; raster residuals supply
instances, including rounded rectangles. No catalogue keys, saved geometry
or reference vectors are read.
"""
from __future__ import annotations

import re

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, raster_identity
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register_steps
from src.iCCModules.imageCompositeConverterGradientScene import _gradient
from src.iCCModules.imageCompositeConverterPrimitiveScene import _circle, _local_quality
from src.iCCModules.imageCompositeConverterSearchPortfolio import progress
from src.iCCModules.imageCompositeConverterSearchScheduler import drain, schedule_models
from src.iCCModules.imageCompositeConverterStructureSearch import complete, edit_proposals, scene_key


# Bound complexity without encoding a family layout. Other scene contracts
# retain their existing vocabulary and supported instance counts.
NUMBERS = {'zwei': 2, 'drei': 3, 'vier': 4, 'fünf': 5, 'sechs': 6, 'sieben': 7, 'acht': 8}
SHAPES = re.compile(r'\b(ein(?:e|en|em)?|[1-8]|'+ '|'.join(NUMBERS) +r')\s+'
                    r'(?:(?:voneinander|getrennt\w*|unbeschriftet\w*|einzeln\w*|'
                    r'gefüllt\w*|einfarbig\w*|farbig\w*|klein\w*|groß\w*|dunk\w*|hell\w*)\s+)*'
                    r'(kreis(?:e|en)?|rechteck(?:e|en)?)\b')


def requested(description):
    text = str(description or '').casefold()
    return (('der kreis hat einen' in text
             and 'die rechtecke liegen innerhalb des kreises' in text)
            or ('der äussere kreis hat einen' in text
                and 'die inneren formen liegen innerhalb des äusseren kreises' in text))


def scene_contract(description):
    """Consume all assertions, rather than silently dropping extra content."""
    text = str(description or '').casefold()
    matches = list(SHAPES.finditer(text))
    counts = {'circle': 0, 'rectangle': 0}
    for m in matches:
        number = int(m[1]) if m[1].isdigit() else NUMBERS.get(m[1], 1)
        counts['circle' if m[2].startswith('kreis') else 'rectangle'] += number
    inner_forms = 'die inneren formen liegen innerhalb des äusseren kreises' in text
    if (counts['circle'] < 1 or not 2 <= sum(counts.values()) <= 9
            or (not inner_forms and counts['circle'] != 1)):
        return None
    subject = 'der äussere kreis' if inner_forms else 'der kreis'
    direction_clause = subject+r' hat einen (horizontal|vertikal)en farbverlauf'
    direction = re.findall(direction_clause, text)
    if len(direction) != 1:
        return None
    relation = ('die inneren formen liegen innerhalb des äusseren kreises' if inner_forms
                else 'die rechtecke liegen innerhalb des kreises')
    layout_axis = None
    if sum(counts.values()) > 2:
        layouts = [name for name in ('nebeneinander', 'untereinander', 'voneinander')
                   if relation+' und getrennt '+name in text]
        if len(layouts) != 1:
            return None
        relation += ' und getrennt '+layouts[0]
        layout_axis = {'nebeneinander': 0, 'untereinander': 1}.get(layouts[0])
    if text.count(relation) != 1:
        return None
    outlined = 'die formen haben helle konturen' in text
    rounded_clause = 'mit leicht gerundeten ecken'
    rounded = rounded_clause in text
    # The qualifier belongs to the quantified rectangle inventory. A free
    # clause must not attach rounding to circles or silently discard a claim.
    if rounded and (outlined or text.count(rounded_clause) != 1
            or sum(m[2].startswith('rechteck') for m in matches) != 1 or not any(
            m[2].startswith('rechteck') and text[m.end():].startswith(' '+rounded_clause)
            for m in matches)):
        return None
    rest = SHAPES.sub('', text).replace(relation, '')
    if rounded:
        rest = rest.replace(rounded_clause, '')
    rest = re.sub(direction_clause, '', rest)
    for clause in ('die formen haben helle konturen', 'keine beschriftung', 'ohne text oder zeichen'):
        rest = rest.replace(clause, '')
    # The existing scene vocabulary permits a whole-motif scale/translation
    # qualifier. It changes no instance or relation; geometry comes from pixels.
    extent = r'(?:geringfügig|etwas|ein wenig|leicht)'
    rest = re.sub(r'\b(?:das (?:gesamte )?motiv|die (?:gesamte )?darstellung) ist '+extent+
                  r' (?:grösser|kleiner) dargestellt und '+extent+
                  r' nach (?:links|rechts) und (?:oben|unten) (?:versetzt|verschoben)', '', rest)
    if re.sub(r'[\s.,;]+|\bund\b', '', rest):
        return None
    return dict(count=sum(counts.values()), axis=0 if direction[0] == 'horizontal' else 1,
                outlined=outlined, layout_axis=layout_axis, rounded=rounded,
                children={kind: number for kind, number in
                          (('circle', counts['circle']-1), ('rectangle', counts['rectangle'])) if number})


def _flat_edge(profile, fill, stroke, low, high):
    """Interpolate the inner straight edge from antialias coverage."""
    delta = fill-stroke
    denominator = float(delta@delta)
    if denominator < 100:
        return None
    coverage = np.clip((profile-stroke)@delta/denominator, 0, 1)
    return _coverage_edges(coverage, low, high)


def _coverage_edges(coverage, low, high):
    """Recover a contiguous subpixel interval from compositing coverage."""
    inside = np.flatnonzero((coverage >= .5) & (np.arange(len(coverage)) >= low-2)
                           & (np.arange(len(coverage)) <= high+2))
    if not len(inside):
        return None
    # JPEG shadows can form a second dark stripe beyond a light rim. Only
    # the connected flat interval around the object's center is its interior.
    middle = min(inside, key=lambda i: abs(i-(low+high)/2))
    first = last = int(middle)
    while first > 0 and coverage[first-1] >= .5:
        first -= 1
    while last+1 < len(coverage) and coverage[last+1] >= .5:
        last += 1
    if first < 1 or last+1 >= len(coverage):
        return None
    def crossing(a, b):
        difference = coverage[b]-coverage[a]
        return a+.5+(.5-coverage[a])/difference if abs(difference) > 1e-6 else a+1.
    return crossing(first-1, first), crossing(last, last+1)


def _split_flat_component(pixels, predicted, component):
    """Propose separate flat cores where antialias fringes join rectangles.

    The confidence mask proposes topology only. Registration still checks the
    original raster, including the seam, under the unchanged acceptance gates.
    """
    core = cv2.erode(component, np.ones((5, 5), 'uint8')).astype(bool)
    if not core.any():
        return [component]
    fill = np.median(pixels[core], axis=0)
    delta = fill-predicted
    coverage = np.clip(np.sum((pixels.astype(float)-predicted)*delta, axis=2)
                       / np.maximum(1., np.sum(delta*delta, axis=2)), 0, 1)
    confident = ((coverage >= .9) & component.astype(bool)).astype('uint8')
    number, labels, stats, _ = cv2.connectedComponentsWithStats(confident)
    parts = []
    for index in range(1, number):
        x, y, w, h, area = stats[index]
        if area < 12:
            continue
        # A split proposal is limited to observed rectangular flat cores.
        # Curves, texture and rims keep the original conservative detector.
        if min(w, h) < 5 or area < .94*w*h:
            return [component]
        parts.append((labels == index).astype('uint8'))
        if len(parts) > 8:
            return [component]
    return parts if 2 <= len(parts) <= 8 else [component]


def _split_coverage_edges(coverage, low, high):
    """Use boundary pixel coverage around one separately observed flat core.

    Two objects can contribute to the same pixel. Its individual edge positions
    are then ambiguous: divide the observed coverage equally as a proposal,
    and let joint registration and the raster gates assess it.
    """
    if low < 2 or high+1 >= len(coverage):
        return None
    left = float(coverage[low-1])
    right = float(coverage[high])
    if coverage[low-2] >= .9:
        left /= 2
    if coverage[high+1] >= .9:
        right /= 2
    return low-left, high+right


def _rounded_coverage_edges(coverage, low, high):
    """Integrate the straight central span without interpolating its AA ramp."""
    bounds = _coverage_edges(coverage, low, high)
    if bounds is None:
        return None
    left, right = bounds
    middle = int((left+right)/2)
    if not left < middle < right or coverage[middle] < .9:
        return None
    return (middle-float(np.sum(coverage[max(0, int(left)-2):middle])),
            middle+float(np.sum(coverage[middle:min(len(coverage), int(right)+3)])))


def detect_instances(pixels, contract, *, residual_threshold=25, split_components=False):
    """Fit background paint first, then explain contrasting interior regions."""
    foreground = (np.max(255-pixels.astype(float), axis=2) > 25).astype('uint8')
    contours = cv2.findContours(foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    contours = [c for c in contours if cv2.contourArea(c) >= 12]
    if len(contours) != 1:
        return None
    contour = contours[0]
    center, radius, residual = _circle(contour)
    x, y, w, h = cv2.boundingRect(contour)
    if abs(w-h) > 2 or residual > .85 or radius < 12:
        return None
    yy, xx = np.indices(foreground.shape)
    distance = np.hypot(xx+.5-center[0], yy+.5-center[1])
    interior = (distance < radius-3).astype('uint8')
    geometry = np.array([center[0]-radius, center[1]-radius, 2*radius, 2*radius, 0.])
    # _gradient uses [left, top, right, bottom] bounds.
    bounds = np.r_[geometry[:2], geometry[:2]+geometry[2:4]]
    # A central child may cover more than the robust fit's outlier fraction.
    # Start with the exposed outer band; children still have to pass complete
    # native containment and all local/global raster checks after fitting.
    exposed = (interior.astype(bool) & (distance > radius*.75)).astype('uint8')
    colors = _gradient(pixels, exposed, bounds, contract['axis'])
    if colors is None:
        return None
    coordinate = xx if contract['axis'] == 0 else yy
    t = (coordinate+.5-bounds[contract['axis']])/(2*radius)
    predicted = colors[:3] + t[..., None]*(colors[3:]-colors[:3])
    mask = ((np.max(abs(pixels.astype(float)-predicted), axis=2) > residual_threshold)
            & interior.astype(bool)).astype('uint8')
    number, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    components = []
    for index in range(1, number):
        if stats[index, cv2.CC_STAT_AREA] < 12:
            continue
        component = (labels == index).astype('uint8')
        parts = (_split_flat_component(pixels, predicted, component)
                 if split_components and not contract['outlined'] else [component])
        components.extend((part, len(parts) > 1) for part in parts)
        if len(components) > 16:
            return None
    children = []
    for component, was_split in components:
        x, y, w, h = cv2.boundingRect(component)
        area = cv2.countNonZero(component)
        contour = max(cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
        hull = cv2.convexHull(contour)
        polygon = cv2.approxPolyDP(hull, .025*cv2.arcLength(hull, True), True)
        if min(w, h) < 5:
            return None
        kind = 'rectangle'
        child_center, child_radius, circle_residual = _circle(contour)
        if len(polygon) != 4 or area < .75*w*h:
            if (contract.get('rounded') and contract['children'].get('circle')
                    and abs(w-h) <= 2 and circle_residual < .7):
                kind = 'circle'
            elif contract.get('rounded') and area >= .7*w*h:
                pass  # The observed corner deficit supplies a radius below.
            elif abs(w-h) <= 2 and circle_residual < .7:
                kind = 'circle'
            else:
                return None
        core = cv2.erode(component, np.ones((5, 5), 'uint8')).astype(bool)
        if not core.any():
            core = cv2.erode(component, np.ones((3, 3), 'uint8')).astype(bool)
        if not core.any():
            return None
        fill = np.median(pixels[core if core.any() else component.astype(bool)], axis=0)
        if np.percentile(np.max(abs(pixels[core].astype(float)-fill), axis=1), 80) > 12:
            return None  # These children assert flat paint, not arbitrary texture.
        sw = 1.5 if contract['outlined'] else 0.
        band = (cv2.dilate(component, np.ones((3, 3), 'uint8')).astype(bool)
                & ~cv2.erode(component, np.ones((5, 5), 'uint8')).astype(bool))
        samples = pixels[band]
        bright = samples.mean(axis=1) >= np.percentile(samples.mean(axis=1), 90)
        stroke = np.median(samples[bright], axis=0)
        if kind == 'circle':
            # Pixel centers lie just inside the antialiased silhouette.
            # Registration refines this raster-derived radius independently.
            r = child_radius+.4
            x, y, w, h = child_center[0]-r, child_center[1]-r, 2*r, 2*r
        elif contract['outlined']:
            # A light rim can have the same color as the parent at one side
            # and strong contrast at the other. Seed its centerline from the
            # flat interior instead of this asymmetric residual silhouette.
            flat = ((np.max(abs(pixels.astype(float)-fill), axis=2) <= 25)
                    & cv2.dilate(component, np.ones((3, 3), 'uint8')).astype(bool)).astype('uint8')
            x, y, w, h = cv2.boundingRect(flat)
            horizontal = np.median(pixels[y+h//3:y+2*h//3].astype(float), axis=0)
            vertical = np.median(pixels[:, x+w//3:x+2*w//3].astype(float), axis=1)
            left_right = _flat_edge(horizontal, fill, stroke, x, x+w)
            top_bottom = _flat_edge(vertical, fill, stroke, y, y+h)
            if left_right is None or top_bottom is None:
                return None
            left, right = left_right
            top, bottom = top_bottom
            x, y, w, h = left-sw/2, top-sw/2, right-left+sw, bottom-top+sw
        else:
            # Estimate subpixel edges against the varying parent paint, rather
            # than keeping a threshold-dependent integer bounding rectangle.
            delta = fill-predicted
            coverage = np.clip(np.sum((pixels.astype(float)-predicted)*delta, axis=2)
                               / np.maximum(1., np.sum(delta*delta, axis=2)), 0, 1)
            edges = (_split_coverage_edges if was_split else
                     _rounded_coverage_edges if contract.get('rounded') else _coverage_edges)
            left_right = edges(np.median(coverage[y+h//3:y+2*h//3], axis=0), x, x+w)
            top_bottom = edges(np.median(coverage[:, x+w//3:x+2*w//3], axis=1), y, y+h)
            if left_right is None or top_bottom is None:
                return None
            left, right = left_right
            top, bottom = top_bottom
            x, y, w, h = left, top, right-left, bottom-top
        child = dict(kind=kind, geometry=np.array([x, y, w, h, sw]),
                     colors=np.r_[fill, fill, stroke])
        if contract.get('rounded') and kind == 'rectangle':
            # Integrate the antialias coverage missing from a native
            # rectangle. Four round corners remove (4-pi)*r^2 area.
            # This is a proposal from pixels, not a reference radius.
            cx = np.clip(np.minimum(xx+1, x+w)-np.maximum(xx, x), 0, 1)
            cy = np.clip(np.minimum(yy+1, y+h)-np.maximum(yy, y), 0, 1)
            window = ((xx >= np.floor(x)-1) & (xx <= np.ceil(x+w))
                      & (yy >= np.floor(y)-1) & (yy <= np.ceil(y+h)))
            missing = float(np.sum((cx*cy-coverage)[window]))
            corner = np.sqrt(max(0., missing)/(4-np.pi))
            # A square silhouette cannot earn an explicit rounding claim
            # just by fitting an imperceptibly small positive radius.
            if corner < 1.25:
                return None
            child['radius'] = min(float(corner), min(w, h)/3)
        children.append(child)
    if len(children) > 16:
        return None
    children.sort(key=lambda obj: obj['geometry'][0])
    band = (distance >= radius-1) & (distance < radius)
    stroke = np.median(pixels[band], axis=0)
    geometry[4] = 1. if contract['outlined'] else 0.
    return [dict(kind='circle', geometry=geometry, colors=np.r_[colors, stroke]), *children]


def fit_mixed_gradient_scene(width, height, *, description, image, render_fn, error_fn):
    contract = scene_contract(description)
    pixels = np.asarray(image)
    if (contract is None or pixels.shape != (height, width, 3) or min(width, height) < 24
            or not np.isfinite(pixels).all()):
        return None
    attempts, seen, seeds = [], set(), []
    session = current_search()
    rejection_scope = (raster_identity(pixels), tuple(sorted(contract['children'].items())),
                       contract['axis'], contract['outlined'], contract['layout_axis'], contract['rounded'])
    rejected = session.structure_rejections.setdefault(rejection_scope, {}) if session else {}

    def register(objects, attempt):
        attempts.append(attempt)
        try:
            if objects is not None:
                key = scene_key(objects)
                if not complete(objects, contract['children']):
                    attempt['outcome'] = 'inventory_rejected'
                elif key in rejected:
                    attempt.update(outcome='previously_rejected', previous_outcome=rejected[key])
                elif key in seen:
                    attempt['outcome'] = 'duplicate'
                else:
                    seen.add(key)
                    attempt['outcome'] = 'optimizing'
                    yield None
                    fitted = yield from _fit_instances_steps(
                        width, height, pixels=pixels, contract=contract,
                        objects=objects, render_fn=render_fn, error_fn=error_fn,
                        evidence_objects=[obj for seed in seeds for obj in seed[1:]])
                    if session and session.time_reason():
                        attempt['outcome'] = 'time_limit'
                        return None
                    attempt['outcome'] = 'accepted' if fitted is not None else 'quality_or_geometry_rejected'
                    if fitted is None and len(rejected) < 96:
                        rejected[key] = attempt['outcome']
                    return fitted
            return None
        finally:
            if attempt['outcome'] == 'optimizing':
                attempt['outcome'] = 'time_limit' if session and session.time_reason() else 'cancelled'
            progress('primitive_mixed_gradient_scene_v1', event='scene_hypothesis', **attempt)

    def hypothesis(threshold):
        if session and session.time_reason():
            return None
        objects = detect_instances(pixels, contract, residual_threshold=threshold)
        if objects is not None:
            seeds.append(objects)
        return (yield from register(objects, dict(residual_threshold=threshold,
                                                 operator='segmentation', outcome='no_complete_scene')))

    def repairs():
        # Initial jobs each yield after detection. This job starts only after
        # those slices, so all observed instances are available to the agenda.
        stats, split_stats, outcome = {}, {}, 'cancelled'
        try:
            for proposal in edit_proposals(seeds, contract['children'], stats=stats):
                if session and session.time_reason():
                    return None
                yield None
                if proposal is None:
                    continue
                fitted = yield from register(proposal['objects'], dict(operator='edit',
                    edits=proposal['edits'], outcome='no_complete_scene'))
                if fitted is not None:
                    outcome = 'accepted'
                    return fitted
            # Keep established segmentations and Add/Remove/Replace first.
            # An exhausted agenda may still lack an observed instance because
            # antialiasing joined its core to a neighbour at every threshold.
            # Splitting is another raster-derived proposal, never permission
            # to remove object, relation, region or full-image checks.
            remaining = max(0, 96-stats.get('states', 0))
            changed = False
            if not contract['outlined'] and contract['children'].get('rectangle', 0) >= 2:
                seed_keys = {scene_key(seed) for seed in seeds}
                for threshold in (25, 16, 36):
                    if session and session.time_reason():
                        return None
                    objects = detect_instances(pixels, contract, residual_threshold=threshold,
                                               split_components=True)
                    yield None
                    if objects is not None and scene_key(objects) not in seed_keys:
                        seed_keys.add(scene_key(objects))
                        seeds.append(objects)
                        changed = True
                    fitted = yield from register(objects, dict(operator='split',
                        residual_threshold=threshold, outcome='no_complete_scene'))
                    if fitted is not None:
                        outcome = 'accepted'
                        return fitted
            if changed and remaining:
                for proposal in edit_proposals(seeds, contract['children'],
                                               max_states=remaining, stats=split_stats):
                    if session and session.time_reason():
                        return None
                    yield None
                    if proposal is None:
                        continue
                    fitted = yield from register(proposal['objects'], dict(operator='split_edit',
                        edits=proposal['edits'], outcome='no_complete_scene'))
                    if fitted is not None:
                        outcome = 'accepted'
                        return fitted
            outcome = ('state_limit' if any(s.get(name) for s in (stats, split_stats)
                       for name in ('state_limit_reached', 'candidate_limit_reached')) else 'agenda_exhausted')
            return None
        finally:
            # Include work performed before acceptance, cancellation or expiry.
            if split_stats:
                stats['states'] += split_stats['states']
                for name in ('state_limit_reached', 'candidate_limit_reached'):
                    stats[name] |= split_stats[name]
            if session and session.time_reason():
                outcome = 'time_limit'
            progress('primitive_mixed_gradient_scene_v1', event='structure_search_finished',
                     outcome=outcome, **stats)

    jobs = {threshold: hypothesis(threshold) for threshold in (25, 16, 36)}
    jobs['edits'] = repairs()
    if session:
        scheduled = schedule_models(jobs, session, source='primitive_mixed_gradient_scene_v1',
                                    emit=progress, slice_steps=1)
        try:
            for threshold, fitted in scheduled:
                if fitted is not None:
                    scheduled.close()
                    fitted.update(scene_hypotheses=len(attempts), scene_attempts=attempts)
                    return fitted
        finally:
            scheduled.close()
    else:
        try:
            for job in jobs.values():
                fitted = drain(job)
                if fitted is not None:
                    fitted.update(scene_hypotheses=len(attempts), scene_attempts=attempts)
                    return fitted
        finally:
            for job in jobs.values():
                job.close()
    return None


def _fit_instances_steps(width, height, *, pixels, contract, objects, render_fn, error_fn,
                         evidence_objects=()):
    if not complete(objects, contract['children']):
        return None
    n = len(objects)
    rounded = contract.get('rounded', False)
    geometry_count = 5*n+(n if rounded else 0)
    boxes = [np.r_[o['geometry'][:2], o['geometry'][:2]+o['geometry'][2:4], o['geometry'][4]]
             for o in objects]
    paint = [objects[0]['colors'], *[np.r_[o['colors'][:3], o['colors'][6:]] for o in objects[1:]]]
    offsets = [geometry_count, *[geometry_count+9+6*i for i in range(n-1)]]
    parameters = np.r_[np.concatenate(boxes),
                       [o.get('radius', 0.) for o in objects] if rounded else [],
                       np.concatenate(paint)]

    def geometry(p, index):
        x, y, X, Y, sw = p[5*index:5*index+5]
        w, h = X-x, Y-y
        if objects[index]['kind'] == 'circle':
            y, h = (y+Y-w)/2, w
        return np.array([x, y, w, h, sw])

    def build(p):
        shapes = []
        colors = p[geometry_count:geometry_count+9]
        end = 'x2="100%" y2="0%"' if contract['axis'] == 0 else 'x2="0%" y2="100%"'
        definition = f'<defs><linearGradient id="scene_paint" x1="0%" y1="0%" {end}><stop offset="0" stop-color="{_hex(colors[:3])}"/><stop offset="1" stop-color="{_hex(colors[3:6])}"/></linearGradient></defs>'
        for i, obj in enumerate(objects):
            x, y, w, h, sw = geometry(p, i)
            c = p[offsets[i]:offsets[i]+(9 if i == 0 else 6)]
            fill = 'url(#scene_paint)' if i == 0 else _hex(c[:3])
            stroke = _hex(c[-3:]) if contract['outlined'] else 'none'
            style = f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.4f}"'
            if obj['kind'] == 'circle':
                shapes.append(f'<circle cx="{x+w/2:.4f}" cy="{y+h/2:.4f}" r="{w/2:.4f}" {style}/>')
            else:
                radius = f' rx="{p[5*n+i]:.4f}"' if rounded else ''
                shapes.append(f'<rect x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}"{radius} {style}/>')
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'+definition+f'<rect width="{width}" height="{height}" fill="#ffffff"/>'+''.join(shapes)+'</svg>'

    def valid(p):
        from src.iCCModules.imageCompositeConverterLayeredScene import _contains
        scene = [dict(kind=o['kind'], geometry=geometry(p, i)) for i, o in enumerate(objects)]
        for i, obj in enumerate(scene):
            x, y, w, h, sw = obj['geometry']
            if min(w, h) < 4 or not (0 <= x < x+w <= width and 0 <= y < y+h <= height):
                return False
            if ((contract['outlined'] and not .5 <= sw <= min(w, h)/4)
                    or (not contract['outlined'] and sw != 0)):
                return False
            if i and not _contains(scene[0], obj):
                return False
            if rounded:
                radius = p[5*n+i]
                if ((obj['kind'] == 'rectangle' and not 1. <= radius <= min(w, h)/3)
                        or (obj['kind'] == 'circle' and radius != 0)):
                    return False
            if contract['outlined']:
                c = np.clip(p[offsets[i]:offsets[i]+(9 if i == 0 else 6)], 0, 255)
                if c[-3:].mean() < 180 or (i and c[-3:].mean() < c[:3].mean()+15):
                    return False
        # Every pair must be disjoint, in any arrangement. An explicitly
        # named row/column imposes its stronger interval-separation rule.
        for i, a in enumerate(scene[1:]):
            ax, ay, aw, ah, ast = a['geometry']
            for b in scene[i+2:]:
                bx, by, bw, bh, bst = b['geometry']
                gap = (ast+bst)/2
                separate = (ax+aw+gap < bx or bx+bw+gap < ax,
                            ay+ah+gap < by or by+bh+gap < ay)
                axis = contract['layout_axis']
                if not (any(separate) if axis is None else separate[axis]):
                    return False
        c = np.clip(np.rint(p[geometry_count:geometry_count+6]), 0, 255)
        if np.max(abs(c[3:]-c[:3])) < 8:
            return False
        return True

    regions = [(max(0, int(o['geometry'][0])-3), max(0, int(o['geometry'][1])-3),
                min(width, int(np.ceil(o['geometry'][0]+o['geometry'][2]))+3),
                min(height, int(np.ceil(o['geometry'][1]+o['geometry'][3]))+3))
               for o in [*objects, *evidence_objects]]
    regions = list(dict.fromkeys(regions))

    def qualities(raster):
        return [_local_quality(pixels[y:Y, x:X], raster[y:Y, x:X]) for x, y, X, Y in regions]

    reference_gradients = [cv2.Sobel(pixels.astype('float32'), cv2.CV_32F, dx, dy)/8
                           for dx, dy in ((1, 0), (0, 1))]

    def loss(a, b):
        errors = np.mean((a.astype(float)-b.astype(float))**2, axis=2)
        # Thin light rims can trade width for paint with almost identical
        # area error. Image derivatives retain their observed edge profile.
        for reference, (dx, dy) in zip(reference_gradients, ((1, 0), (0, 1))):
            gradient = cv2.Sobel(b.astype('float32'), cv2.CV_32F, dx, dy)/8
            errors += 4*np.mean((reference-gradient)**2, axis=2)
        return float(np.mean([errors[y:Y, x:X].mean() for x, y, X, Y in regions]))

    fitted = yield from _register_steps(parameters, geometry_count, build, valid, pixels, render_fn, error_fn,
                       'primitive_mixed_gradient_scene_v1', preserve_initial_error=True,
                       loss_fn=loss,
                       satisfactory_fn=lambda p, m: all(q and q['passed'] for q in qualities(m[3])))
    if fitted is None:
        return None
    quality = qualities(fitted['rendered'])
    global_quality = _local_quality(pixels, fitted['rendered'])
    if not global_quality or not global_quality['passed'] or any(not q or not q['passed'] for q in quality):
        return None
    fitted.update(object_kinds=[o['kind'] for o in objects], object_quality=quality[:n],
                  evidence_quality=quality[n:],
                  scene_hypotheses=1, instance_groups=n,
                  scene_detectors=['gradient_boundary', 'flat_residual_shapes'],
                  neural_scene_selected=False)
    return fitted
