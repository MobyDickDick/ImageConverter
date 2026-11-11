"""Raster-derived gradient parents containing flat native shapes.

The closed description contract controls topology; raster residuals supply
instances, including rounded rectangles. No catalogue keys, saved geometry
or reference vectors are read.
"""
from __future__ import annotations

import heapq
import hashlib
import re
from copy import deepcopy

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, raster_identity
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register_steps
from src.iCCModules.imageCompositeConverterGradientScene import _gradient
from src.iCCModules.imageCompositeConverterPrimitiveScene import _circle, _local_quality
from src.iCCModules.imageCompositeConverterSearchPortfolio import progress, validated_result
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
                and 'die inneren formen liegen innerhalb des äusseren kreises' in text)
            or ('das äussere rechteck hat einen' in text
                and 'die inneren formen liegen innerhalb des äusseren rechtecks' in text))


def scene_contract(description):
    """Consume all assertions, rather than silently dropping extra content."""
    text = str(description or '').casefold()
    matches = list(SHAPES.finditer(text))
    counts = {'circle': 0, 'rectangle': 0}
    for m in matches:
        number = int(m[1]) if m[1].isdigit() else NUMBERS.get(m[1], 1)
        counts['circle' if m[2].startswith('kreis') else 'rectangle'] += number
    rectangular_parent = 'das äussere rechteck hat einen' in text
    parent_kind = 'rectangle' if rectangular_parent else 'circle'
    parent_name = 'des äusseren rechtecks' if rectangular_parent else 'des äusseren kreises'
    inner_forms = 'die inneren formen liegen innerhalb '+parent_name in text
    if (counts[parent_kind] < 1 or (rectangular_parent and not inner_forms)
            or not 2 <= sum(counts.values()) <= 9
            or (not inner_forms and counts['circle'] != 1)):
        return None
    subject = ('das äussere rechteck' if rectangular_parent else
               'der äussere kreis' if inner_forms else 'der kreis')
    direction_clause = subject+r' hat einen (horizontal|vertikal)en farbverlauf'
    direction = re.findall(direction_clause, text)
    if len(direction) != 1:
        return None
    relation = ('die inneren formen liegen innerhalb '+parent_name if inner_forms
                else 'die rechtecke liegen innerhalb des kreises')
    layout_axis = None
    overlap = relation+' und überlappen sich teilweise' in text
    group_matches = list(re.finditer(re.escape(relation)+
        r' und bilden (2|3|4|zwei|drei|vier) getrennte gruppen mit teilweisen überdeckungen', text))
    mixed_groups = list(re.finditer(re.escape(relation)+
        r' und bilden (1|2|3|4|ein|eine|zwei|drei|vier) überdeckungsgruppen?'
        r' sowie (1|2|3|4|5|6|ein|eine|zwei|drei|vier|fünf|sechs) einzelne form(?:en)?\b', text))
    overlap_groups = 1
    isolated_children = 0
    separation_clause = 'die gruppen und einzelnen formen liegen getrennt voneinander'
    if mixed_groups:
        if len(mixed_groups) != 1 or group_matches or overlap or text.count(separation_clause) != 1:
            return None
        def number(token):
            return int(token) if token.isdigit() else NUMBERS.get(token, 1)
        overlap_groups, isolated_children = (number(mixed_groups[0][i]) for i in (1, 2))
        if sum(counts.values())-1 < 2*overlap_groups+isolated_children:
            return None
        overlap = True
    elif group_matches:
        if len(group_matches) != 1 or overlap:
            return None
        number = group_matches[0][1]
        overlap_groups = int(number) if number.isdigit() else NUMBERS[number]
        if sum(counts.values())-1 < 2*overlap_groups:
            return None  # Every claimed group needs an overlapping pair.
        overlap = True
    if sum(counts.values()) > 2:
        layouts = [name for name in ('nebeneinander', 'untereinander', 'voneinander')
                   if relation+' und getrennt '+name in text]
        if overlap and not layouts:
            relation = (mixed_groups[0][0] if mixed_groups else group_matches[0][0] if group_matches else
                        relation+' und überlappen sich teilweise')
        elif len(layouts) != 1 or overlap:
            return None
        else:
            relation += ' und getrennt '+layouts[0]
            layout_axis = {'nebeneinander': 0, 'untereinander': 1}.get(layouts[0])
    if text.count(relation) != 1:
        return None
    outlined = 'die formen haben helle konturen' in text
    rounded_clause = 'mit leicht gerundeten ecken'
    child_rounding = 'die inneren rechtecke haben leicht gerundete ecken'
    parent_rounding = 'das äussere rechteck hat gerundete ecken'
    parent_rounded = rectangular_parent and parent_rounding in text
    if parent_rounded and text.count(parent_rounding) != 1:
        return None
    scoped_rounding = rectangular_parent and child_rounding in text
    rounded = rounded_clause in text or scoped_rounding
    # Larger inventories use observed pairwise depth as an ordering proposal;
    # the fallback agenda still has 96 states, never a factorial expansion.
    if overlap and not 2 <= sum(counts.values())-1 <= 8:
        return None
    # The qualifier belongs to the quantified rectangle inventory. A free
    # clause must not attach rounding to circles or silently discard a claim.
    if scoped_rounding and (text.count(child_rounding) != 1 or rounded_clause in text
                            or counts['rectangle'] < 2):
        return None
    if rounded and not scoped_rounding and (rectangular_parent or text.count(rounded_clause) != 1
            or sum(m[2].startswith('rechteck') for m in matches) != 1 or not any(
            m[2].startswith('rechteck') and text[m.end():].startswith(' '+rounded_clause)
            for m in matches)):
        return None
    rest = SHAPES.sub('', text).replace(relation, '')
    if mixed_groups:
        rest = rest.replace(separation_clause, '')
    if rounded:
        rest = rest.replace(child_rounding if scoped_rounding else rounded_clause, '')
    if parent_rounded:
        rest = rest.replace(parent_rounding, '')
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
                parent_kind=parent_kind,
                parent_rounded=parent_rounded,
                outlined=outlined, layout_axis=layout_axis, rounded=rounded, overlap=overlap,
                overlap_groups=overlap_groups, isolated_children=isolated_children,
                children={kind: number for kind, number in
                          ((kind, counts[kind]-int(kind == parent_kind))
                           for kind in ('circle', 'rectangle')) if number})


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


def _exposed_corner_radius(data, predicted, fill, coverage, box, *, reconstructed=None, foreign_mask=None,
                           rim_inset=0., minimum_corners=2, tight_window=False):
    """Measure round-corner deficits only where the parent paint is exposed.

    Occluding paint cannot supply a hidden corner's radius. At least two
    independently visible corners must support the same native rounding.
    """
    a, b, w, h = box
    X, Y = a+w, b+h
    yy, xx = np.indices(coverage.shape)
    ideal = (np.clip(np.minimum(xx+1, X)-np.maximum(xx, a), 0, 1)
             * np.clip(np.minimum(yy+1, Y)-np.maximum(yy, b), 0, 1))
    if reconstructed is None:
        reconstructed = predicted+coverage[..., None]*(fill-predicted)
    foreign = np.max(abs(data-reconstructed), axis=2) > 4
    if foreign_mask is not None:
        foreign |= foreign_mask
    span = min(w, h)/3+2
    radii = []
    for left in (True, False):
        for top in (True, False):
            x0, x1 = (max(0, int(np.floor(a))-1), min(coverage.shape[1], int(np.ceil(a+span))+1)) if left else (
                max(0, int(np.floor(X-span))), min(coverage.shape[1], int(np.ceil(X))+1))
            y0, y1 = (max(0, int(np.floor(b))-1), min(coverage.shape[0], int(np.ceil(b+span))+1)) if top else (
                max(0, int(np.floor(Y-span))), min(coverage.shape[0], int(np.ceil(Y))+1))
            cx, cy = xx[y0:y1, x0:x1], yy[y0:y1, x0:x1]
            deficit = (ideal-coverage)[y0:y1, x0:x1]
            hidden = foreign[y0:y1, x0:x1]
            measured = None
            for extent in np.arange(span, 4., -1.):
                window = ((cx >= np.floor(a)-1) & (cx <= np.ceil(X))
                          & (cy >= np.floor(b)-1) & (cy <= np.ceil(Y))
                          & (cx < a+extent if left else cx >= X-extent)
                          & (cy < b+extent if top else cy >= Y-extent))
                if np.any(hidden & window):
                    continue
                missing = float(np.sum(deficit[window]))
                radius = np.sqrt(max(0., missing)/(1-np.pi/4))
                # Shrinking an observation window is valid only when the
                # entire rounded corner still fits inside the exposed area.
                if radius+2 <= extent:
                    measured = radius
                    if tight_window:
                        # Re-measure close to the observed arc so quantized
                        # straight fill cannot accumulate a large area bias.
                        extent = radius+3
                        window &= ((cx < a+extent if left else cx >= X-extent)
                                   & (cy < b+extent if top else cy >= Y-extent))
                        missing = float(np.sum(deficit[window]))
                        measured = np.sqrt(max(0., missing)/(1-np.pi/4))
                break
            if measured is not None:
                radii.append(measured)
    # A rim reduces the observed inner radius. Apply the native rounding
    # threshold to the centerline, retaining a positive measured inner deficit.
    if (len(radii) < minimum_corners or min(radii) < .75 or min(radii)+rim_inset < 1.25
            or max(radii)-min(radii) > 1.5):
        return None
    radius = float(np.median(radii))
    return radius if radius <= min(w, h)/3 else None


def _overlap_circle(component, background, coverage, reconstruction_error, shape, *, owned_fill=None):
    """Reuse visible-arc fitting, supported only by parent-facing boundaries."""
    from src.iCCModules.imageCompositeConverterSceneFusion import _arc
    contours = cv2.findContours(component.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if not contours:
        return None
    # A later shape may split the visible fill. Keep every exposed arc, while
    # excluding cut edges next to foreign paint from the radius measurement.
    points = np.concatenate(contours)
    near_parent = cv2.dilate(background.astype('uint8'), np.ones((5, 5), 'uint8')).astype(bool)
    points = points[near_parent[points[:, 0, 1], points[:, 0, 0]]]
    if len(points) < 12:
        return None
    geometry = _arc(points, shape)
    if geometry is None:
        return None
    x, y, w, h, _ = geometry
    center = np.array([x+w/2, y+h/2])
    radius = w/2
    yy, xx = np.indices(shape)
    # Pure-fill contours lie inside the true circle. Measure its subpixel
    # boundary from exposed antialias coverage against the fitted parent,
    # rather than spending registration steps correcting this quantization.
    edge = ((abs(np.hypot(xx+.5-center[0], yy+.5-center[1])-radius) < 2)
            & (coverage > .05) & (coverage < .95) & near_parent
            & (reconstruction_error <= 4))
    samples = np.c_[xx[edge]+.5, yy[edge]+.5]
    if len(samples) >= 12:
        angles = np.sort(np.arctan2(samples[:, 1]-center[1], samples[:, 0]-center[0]))
        span = 2*np.pi-np.diff(np.r_[angles, angles[0]+2*np.pi]).max()
        if span >= np.pi:
            proposal, r = center.copy(), radius
            for _ in range(3):
                distances = np.linalg.norm(samples-proposal, axis=1)
                jacobian = np.c_[(proposal-samples)/distances[:, None], -np.ones(len(samples))]
                step = np.linalg.lstsq(jacobian, distances+coverage[edge]-.5-r, rcond=None)[0]
                proposal -= step[:2]
                r -= step[2]
            if (np.isfinite(np.r_[proposal, r]).all() and r >= 5
                    and np.linalg.norm(proposal-center) <= 1.5 and abs(r-radius) <= 1.5):
                geometry = [*(proposal-r), 2*r, 2*r, 0.]
                x, y, w, h, _ = geometry
    # Expanding a rim search can reach an adjacent instance of the same
    # paint. Its pixels are not owned by this circle. The independently
    # separated fill must fit inside the measured outer arc; registration
    # still verifies every native instance and the complete original raster.
    yy, xx = np.where(component if owned_fill is None else owned_fill)
    if np.mean(np.hypot(xx+.5-x-w/2, yy+.5-y-h/2) <= w/2+1) < .995:
        return None
    return np.array(geometry)


def _paint_components(pixels, mask, *, outlined=False):
    """Keep observed islands separate until a structure hypothesis groups them."""
    data = pixels.astype(float)
    high = cv2.dilate(data, np.ones((3, 3), 'uint8'))
    low = cv2.erode(data, np.ones((3, 3), 'uint8'))
    flat = (np.max(high-low, axis=2) <= 1) & mask.astype(bool)
    colors, counts = np.unique(pixels[flat], axis=0, return_counts=True)
    colors = colors[counts >= 12]
    if outlined:
        # Pale rims are paint around an instance, not additional flat objects.
        colors = colors[colors.mean(axis=1) < 180]
    # A visible rim can separate instances even when all fills are identical.
    # The unoutlined single-paint union supplies no such instance boundary.
    if not (1 if outlined else 2) <= len(colors) <= 8 or any(
            np.max(abs(a.astype(float)-b)) < 25
            for i, a in enumerate(colors) for b in colors[i+1:]):
        return None
    paints = []
    for color in colors:
        visible = ((np.max(abs(data-color.astype(float)), axis=2) <= 3) & mask.astype(bool)).astype('uint8')
        number, labels, stats, _ = cv2.connectedComponentsWithStats(visible)
        parts = [i for i in range(1, number) if stats[i, cv2.CC_STAT_AREA] >= 12]
        if not parts:
            return None
        paints.append((color, labels, parts))
    return paints


class _OverlapProposals:
    """Reuse exact native measurements within one image's structure search.

    Thresholds and island partitions can produce the same observed paint
    groups. Their native boundaries depend on those groups and the parent
    field, not on the threshold that found them. Registration and acceptance
    still run against the complete scene contract and original raster.
    """
    def __init__(self, pixels):
        self.pixels = pixels
        self.entries = {}
        self.hits = 0
        self.measurements = 0

    def measure(self, pixels, predicted, mask, groups, *, rounded, outlined, circles):
        if pixels is not self.pixels:
            raise ValueError('Native proposal cache belongs to one image')
        key = (predicted.dtype.str, predicted.shape,
               hashlib.sha256(predicted.tobytes()).digest(), rounded, outlined, circles,
               tuple((tuple(color), hashlib.sha256(np.packbits(component).tobytes()).digest())
                     for color, component in groups))
        if key in self.entries:
            self.hits += 1
            result = self.entries[key]
            outcome = 'cache_hit'
        else:
            self.measurements += 1
            result = _overlap_instances(pixels, predicted, mask, groups=groups,
                rounded=rounded, outlined=outlined, circles=circles)
            # Bound retained proposals independently of the structure agenda.
            # Both successful measurements and native-boundary rejections count.
            if len(self.entries) >= 96:
                self.entries.pop(next(iter(self.entries)))
            self.entries[key] = deepcopy(result)
            outcome = 'measured'
        progress('primitive_mixed_gradient_scene_v1', event='native_proposal',
                 outcome=outcome, groups=len(groups), measurements=self.measurements,
                 cache_hits=self.hits, native_boundaries=result is not None)
        # Callers sort and edit candidates. Never expose the retained proposal.
        return deepcopy(result)


def _overlap_instances(pixels, predicted, mask, *, rounded=False, outlined=False, circles=False,
                       split_components=False, groups=None, proposals=None):
    """Propose native instances, each with independently exposed arcs or sides.

    Grouping does not supply hidden bounds: four observed rectangle sides or
    at least half a circle's observed circumference are still required.
    """
    data = pixels.astype(float)
    if groups is None:
        paints = _paint_components(pixels, mask, outlined=outlined)
        if paints is None:
            return None
        if sum(len(parts) if split_components else 1 for _, _, parts in paints) > 8:
            return None  # Bound allocations before expanding full-image masks.
        groups = [(color, np.isin(labels, selection)) for color, labels, parts in paints
                  for selection in ([[part] for part in parts] if split_components else [parts])]
    if len(groups) > 8:
        return None
    if proposals is not None:
        return proposals.measure(pixels, predicted, mask, groups,
                                 rounded=rounded, outlined=outlined, circles=circles)
    color_count = len({tuple(color) for color, _ in groups})
    children = []
    for color, component in groups:
        fill = color.astype(float)
        x, y, w, h = cv2.boundingRect(component.astype('uint8'))
        area = np.count_nonzero(component)
        margin = 5 if outlined else 3
        if min(w, h) < 5 or x <= margin or y <= margin or x+w+margin >= pixels.shape[1] or y+h+margin >= pixels.shape[0]:
            return None
        delta = fill-predicted
        coverage = np.clip(np.sum((data-predicted)*delta, axis=2)
                           / np.maximum(1., np.sum(delta*delta, axis=2)), 0, 1)
        if circles and not outlined:
            background = np.max(abs(data-predicted), axis=2) <= 4
            reconstruction_error = np.max(abs(data-predicted-coverage[..., None]*delta), axis=2)
            geometry = _overlap_circle(component, background, coverage, reconstruction_error, pixels.shape[:2])
            if geometry is not None:
                children.append(dict(kind='circle', geometry=geometry,
                                     colors=np.r_[fill, fill, fill]))
                continue
        stroke, sw, rim_coverage = fill, 0., None
        reconstructed = None
        if outlined:
            band = cv2.dilate(component.astype('uint8'), np.ones((9, 9), 'uint8')).astype(bool) & ~component
            light = band & (np.mean(data-predicted, axis=2) > 8) & (data.mean(axis=2) >= 180)
            samples = data[light]
            if len(samples) < (w+h)/2:
                return None
            # Subpixel translation can leave most straight rim pixels mixed
            # with the fill or parent. The brightest exposed corner samples
            # still identify the paint; averaging the broad band biases it.
            strength = samples.mean(axis=1)
            strongest = samples[strength >= strength.max()-1.]
            # Prefer a directly observed paint cluster only with five distinct
            # pixels. A broad percentile can include parent/fill mixtures when
            # subpixel placement leaves very little fully exposed bright rim.
            stroke = np.median(strongest if len(strongest) >= 5 else
                               samples[strength >= np.percentile(strength, 95)], axis=0)
            # Solve independent fill/rim coverages against the varying parent.
            # A collinear palette cannot identify these two contributions.
            rim, observed = stroke-predicted, data-predicted
            dd, rr = np.sum(delta*delta, axis=2), np.sum(rim*rim, axis=2)
            dr = np.sum(delta*rim, axis=2)
            determinant = dd*rr-dr*dr
            if np.any(determinant[band] < .002*dd[band]*rr[band]):
                return None
            od, ort = np.sum(observed*delta, axis=2), np.sum(observed*rim, axis=2)
            coverage = np.clip((od*rr-ort*dr)/np.maximum(1., determinant), 0, 1)
            rim_coverage = np.clip((ort*dd-od*dr)/np.maximum(1., determinant), 0, 1)
            reconstructed = predicted+coverage[..., None]*delta+rim_coverage[..., None]*rim
            if circles:
                # Measure both parent-facing boundaries independently. A rim
                # must explain an observed annulus, never a fixed assumed width.
                error = np.max(abs(data-reconstructed), axis=2)
                # At the inner boundary the adjacent paint is the rim, not
                # the parent. Foreign fill does not provide arc support.
                rim_background = (rim_coverage > .1) & (coverage < .05) & (error <= 4)
                inner = _overlap_circle(component, background=rim_background,
                                        coverage=coverage, reconstruction_error=error, shape=pixels.shape[:2])
                outer_coverage = np.clip(coverage+rim_coverage, 0, 1)
                outer_component = ((outer_coverage >= .95) & (error <= 4)
                                   & cv2.dilate(component.astype('uint8'), np.ones((9, 9), 'uint8')).astype(bool))
                outer = (_overlap_circle(outer_component, np.max(abs(data-predicted), axis=2) <= 4,
                                         outer_coverage, error, pixels.shape[:2])
                         if inner is not None else None)
                if inner is not None and outer is None and any(
                        other is not component and np.array_equal(color, other_color)
                        and np.any(outer_component & other)
                        for other_color, other in groups):
                    # A separately observed instance of the same paint can
                    # contaminate this expanded search region. Preserve the
                    # original proposal first and only retry containment on
                    # this circle's independently observed fill in that case.
                    outer = _overlap_circle(outer_component,
                        np.max(abs(data-predicted), axis=2) <= 4,
                        outer_coverage, error, pixels.shape[:2], owned_fill=component)
                if inner is not None and outer is not None:
                    ic = inner[:2]+inner[2:4]/2
                    oc = outer[:2]+outer[2:4]/2
                    sw = (outer[2]-inner[2])/2
                    if np.linalg.norm(ic-oc) <= .6 and .5 <= sw <= inner[2]/4:
                        center = (ic+oc)/2
                        radius = (inner[2]+outer[2])/4
                        children.append(dict(kind='circle',
                            geometry=np.r_[center-radius, 2*radius, 2*radius, sw],
                            colors=np.r_[fill, fill, stroke]))
                        continue
        background = np.max(abs(data-predicted), axis=2) <= 4
        # Pure fill begins at an integer pixel; the adjacent pixel may carry
        # fractional coverage. Only parent-facing spans supply that fraction.
        left = component[:, x] & component[:, x+2] & background[:, x-margin]
        right = component[:, x+w-1] & component[:, x+w-3] & background[:, x+w+margin-1]
        top = component[y] & component[y+2] & background[y-margin]
        bottom = component[y+h-1] & component[y+h-3] & background[y+h+margin-1]
        if color_count > 4:
            # A blend at an occlusion can happen to match another fill and
            # extend its component by a pixel. Search just inside that bound
            # for the same required five parent-facing straight-edge samples.
            # No hidden extent is extrapolated; registration checks the
            # proposed subpixel sides against the original raster as before.
            L, R, T, B = x, x+w-1, y, y+h-1
            for edge in range(x, x+3):
                side = component[:, edge] & component[:, edge+2] & background[:, edge-margin]
                if np.count_nonzero(side) >= 5:
                    L, left = edge, side
                    break
            for edge in range(x+w-1, x+w-4, -1):
                side = component[:, edge] & component[:, edge-2] & background[:, edge+margin]
                if np.count_nonzero(side) >= 5:
                    R, right = edge, side
                    break
            for edge in range(y, y+3):
                side = component[edge] & component[edge+2] & background[edge-margin]
                if np.count_nonzero(side) >= 5:
                    T, top = edge, side
                    break
            for edge in range(y+h-1, y+h-4, -1):
                side = component[edge] & component[edge-2] & background[edge+margin]
                if np.count_nonzero(side) >= 5:
                    B, bottom = edge, side
                    break
            x, y, w, h = L, T, R-L+1, B-T+1
        if any(np.count_nonzero(side) < 5 for side in (left, right, top, bottom)):
            return None
        a = x-float(np.median(coverage[left, x-1]))
        b = y-float(np.median(coverage[y-1, top]))
        X = x+w+float(np.median(coverage[right, x+w]))
        Y = y+h+float(np.median(coverage[y+h, bottom]))
        if outlined or rounded:
            # Integrate the narrow AA ramp, including the first nearly pure
            # fill pixel; its fractional coverage is not necessarily one.
            a = x+2-float(np.median(coverage[left, x-3:x+2].sum(axis=1)))
            X = x+w-2+float(np.median(coverage[right, x+w-2:x+w+3].sum(axis=1)))
            b = y+2-float(np.median(coverage[y-3:y+2, top].sum(axis=0)))
            Y = y+h-2+float(np.median(coverage[y+h-2:y+h+3, bottom].sum(axis=0)))
        if outlined:
            widths = [np.median(rim_coverage[left, x-5:x+1].sum(axis=1)),
                      np.median(rim_coverage[right, x+w-1:x+w+5].sum(axis=1)),
                      np.median(rim_coverage[y-5:y+1, top].sum(axis=0)),
                      np.median(rim_coverage[y+h-1:y+h+5, bottom].sum(axis=0))]
            sw = float(np.median(widths))
            # The width bound refers to the native centerline box, not the
            # integer pure-fill core, which excludes the rim and AA pixels.
            if min(widths) < .5 or max(widths) > (min(X-a, Y-b)+sw)/4 or max(widths)-min(widths) > .75:
                return None
        child = dict(kind='rectangle', geometry=np.array([a-sw/2, b-sw/2, X-a+sw, Y-b+sw, sw]),
                     colors=np.r_[fill, fill, stroke])
        if rounded:
            other_paint = np.zeros(mask.shape, dtype='uint8')
            for _, other_component in groups:
                if other_component is not component:
                    ox, oy, ow, oh = cv2.boundingRect(other_component.astype('uint8'))
                    # Identical bright rims do not reveal which instance
                    # painted them. Exclude the whole observed foreign box,
                    # including its rim, from this corner measurement.
                    other_paint[max(0, oy-3):oy+oh+3, max(0, ox-3):ox+ow+3] = 1
            radius = _exposed_corner_radius(data, predicted, fill, coverage, [a, b, X-a, Y-b],
                                            reconstructed=reconstructed,
                                            rim_inset=sw/2,
                                            foreign_mask=cv2.dilate(other_paint, np.ones((5, 5), 'uint8')).astype(bool))
            if radius is None:
                return None
            child['radius'] = radius+sw/2
        children.append(child)
    return children


def _visible_parent_arc(center, radius, shape):
    """Exact angular measure inside the canvas, independent of raster sampling."""
    height, width = shape
    if np.all(center-radius >= 0) and np.all(center+radius <= [width, height]):
        return 2*np.pi
    angles = [0., 2*np.pi]
    for edge in (0., float(width)):
        ratio = (edge-center[0])/radius
        if -1 < ratio < 1:
            angle = np.arccos(ratio)
            angles.extend((angle, 2*np.pi-angle))
    for edge in (0., float(height)):
        ratio = (edge-center[1])/radius
        if -1 < ratio < 1:
            angle = np.arcsin(ratio)
            angles.extend((angle % (2*np.pi), (np.pi-angle) % (2*np.pi)))
    angles = np.sort(angles)
    middle = (angles[:-1]+angles[1:])/2
    points = center+radius*np.c_[np.cos(middle), np.sin(middle)]
    visible = ((points[:, 0] >= 0) & (points[:, 0] <= width)
               & (points[:, 1] >= 0) & (points[:, 1] <= height))
    return float(np.diff(angles)[visible].sum())


def _parent_circle(contour, shape):
    """Frame cut edges are not circle evidence; require at least a half arc."""
    height, width = shape
    points = contour[:, 0]
    clipped = (np.any(points <= 0) or np.any(points[:, 0] >= width-1)
               or np.any(points[:, 1] >= height-1))
    if not clipped:
        center, radius, residual = _circle(contour)
        _, _, w, h = cv2.boundingRect(contour)
        return (center, radius) if abs(w-h) <= 2 and residual <= .85 and radius >= 12 else None
    # Keep a pixel of clearance from each cut: its AA junction supplies no
    # curvature constraint. All remaining boundary pixels must fit the arc.
    keep = ((points[:, 0] > 1) & (points[:, 0] < width-2)
            & (points[:, 1] > 1) & (points[:, 1] < height-2))
    if keep.sum() < 24:
        return None
    center, radius, residual = _circle(contour[keep])
    if (not 12 <= radius <= min(shape) or residual > .85
            or not (0 <= center[0] <= width and 0 <= center[1] <= height)):
        return None
    angles = np.sort(np.arctan2(points[keep, 1]+.5-center[1], points[keep, 0]+.5-center[0]))
    coverage = 2*np.pi-np.diff(np.r_[angles, angles[0]+2*np.pi]).max()
    if coverage < np.pi or _visible_parent_arc(center, radius, shape) < np.pi:
        return None
    return center, radius


def _gradient_context(pixels, contract, residual_threshold):
    """Measure the shared parent once for all island grouping hypotheses."""
    foreground = (np.max(255-pixels.astype(float), axis=2) > 25).astype('uint8')
    contours = cv2.findContours(foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    contours = [c for c in contours if cv2.contourArea(c) >= 12]
    if len(contours) != 1:
        return None
    contour = contours[0]
    if contract.get('parent_kind') == 'rectangle':
        return _rectangular_gradient_context(pixels, contract, foreground, contour, residual_threshold)
    circle = _parent_circle(contour, foreground.shape)
    if circle is None:
        return None
    center, radius = circle
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
    return geometry, colors, predicted, mask, distance


def _rectangular_gradient_context(pixels, contract, foreground, contour, threshold):
    """Measure a complete parent from exposed sides and, when claimed, arcs.

    A frame edge cannot substitute for an observed parent boundary. Child proposals and
    registration reuse the common search after this boundary measurement.
    """
    x, y, w, h = cv2.boundingRect(contour)
    height, width = foreground.shape
    rounded = contract.get('parent_rounded', False)
    if x < 4 or y < 4 or x+w > width-4 or y+h > height-4:
        return _clipped_rectangular_context(pixels, contract, foreground, contour, threshold)
    if (min(w, h) < 24
            or cv2.contourArea(contour) < (.85 if rounded else .95)*(w-1)*(h-1)):
        return None
    yy, xx = np.indices(foreground.shape)
    # Keep the exposed border of the fill; central children are outliers.
    edge_distance = np.minimum.reduce([xx+.5-x, x+w-xx-.5, yy+.5-y, y+h-yy-.5])
    exposed = (edge_distance > 3) & (edge_distance < min(w, h)*.12)
    if rounded:
        # The middle third of each side is outside every supported corner.
        # White corner cutouts must not bias the axial paint estimate.
        exposed &= (((xx >= x+w/3) & (xx <= x+2*w/3))
                    | ((yy >= y+h/3) & (yy <= y+2*h/3)))
    bounds = np.array([x, y, x+w, y+h], dtype=float)
    colors = _gradient(pixels, exposed, bounds, contract['axis'])
    if colors is None:
        return None
    t = ((xx if contract['axis'] == 0 else yy)+.5-bounds[contract['axis']])/(w if contract['axis'] == 0 else h)
    predicted = colors[:3]+t[..., None]*(colors[3:]-colors[:3])
    observed, delta = pixels.astype(float)-255., predicted-255.
    plain = np.clip(np.sum(observed*delta, axis=2)/np.maximum(1., np.sum(delta*delta, axis=2)), 0, 1)
    ring = (edge_distance >= -4) & (edge_distance < 4)
    if rounded:
        kernel = np.ones((9, 9), 'uint8')
        silhouette = np.zeros_like(foreground)
        cv2.drawContours(silhouette, [contour], -1, 1, cv2.FILLED)
        ring = (cv2.dilate(silhouette, kernel) != cv2.erode(silhouette, kernel))
    stroke, sw = np.zeros(3), 0.
    coverage = plain
    if contract['outlined']:
        # A uniform bright rim is separated from parent/white antialiasing
        # by the residual perpendicular to their compositing line.
        residual = np.max(abs(observed-plain[..., None]*delta), axis=2)
        samples = pixels[ring & (residual > 4) & (pixels.mean(axis=2) >= 180)]
        if len(samples) < .3*2*(w+h):
            return None
        stroke = np.median(samples, axis=0)
        if rounded:
            strength = residual[ring & (residual > 4) & (pixels.mean(axis=2) >= 180)]
            stroke = np.median(samples[strength >= np.percentile(strength, 95)], axis=0)
        rim = stroke-255.
        dd, rr, dr = np.sum(delta*delta, axis=2), float(rim@rim), delta@rim
        determinant = dd*rr-dr*dr
        if np.any(determinant[ring] < .002*dd[ring]*rr):
            return None
        od, ort = np.sum(observed*delta, axis=2), observed@rim
        coverage = np.clip((od*rr-ort*dr)/np.maximum(1., determinant), 0, 1)
        rim_coverage = np.clip((ort*dd-od*dr)/np.maximum(1., determinant), 0, 1)
        sw = float(rim_coverage[ring].sum()/(2*(w+h)))
        if not .5 <= sw <= min(w, h)/4:
            return None
    if rounded:
        # Quantized gradient colors can project a pure fill pixel onto a
        # spurious rim, especially for two nearly parallel paint vectors.
        # Preserve mixed boundary pixels, but anchor observed pure paints.
        pure_fill = np.max(abs(pixels.astype(float)-predicted), axis=2) <= 2
        pure_white = np.min(pixels, axis=2) >= 254
        coverage[pure_fill], coverage[pure_white] = 1., 0.
        if contract['outlined']:
            rim_coverage[pure_fill | pure_white] = 0.
    horizontal = np.median(coverage[y+h//3:y+2*h//3], axis=0)
    vertical = np.median(coverage[:, x+w//3:x+2*w//3], axis=1)
    # Central children need not project onto the gradient/white paint line.
    # Only the exposed edge strips measure the parent boundary.
    horizontal[x+5:x+w-5] = 1.
    vertical[y+5:y+h-5] = 1.
    edges = _rounded_coverage_edges if rounded else _coverage_edges
    lr, tb = edges(horizontal, x, x+w), edges(vertical, y, y+h)
    if lr is None or tb is None:
        return None
    left, right = lr
    top, bottom = tb
    radius = 0.
    if rounded:
        # Only foreign paint inside the observed silhouette hides a corner.
        # Color quantization in a boundary blend is not foreign evidence.
        foreign = ((np.max(abs(pixels.astype(float)-predicted), axis=2) > 4)
                   & cv2.erode(silhouette if contract['outlined'] else foreground,
                               np.ones((9, 9), 'uint8')).astype(bool))
        inner_radius = _exposed_corner_radius(pixels.astype(float), 255., predicted,
            coverage, [left, top, right-left, bottom-top], reconstructed=pixels.astype(float),
            foreign_mask=foreign, minimum_corners=4, tight_window=True)
        if inner_radius is None:
            return None
        if contract['outlined']:
            # Integrating the rim area gives its width against the measured
            # rounded perimeter, including all four arcs. The centerline is
            # offset half a stroke from the inner fill boundary.
            perimeter = 2*(right-left+bottom-top)-(8-2*np.pi)*inner_radius
            area = float(rim_coverage[ring].sum())
            sw = 2*area/(perimeter+np.sqrt(perimeter**2+4*np.pi*area))
            if not .5 <= sw <= min(w, h)/4:
                return None
        radius = inner_radius+sw/2
    else:
        # Local evidence prevents globally small corner cutouts earning a
        # sharp-parent assertion.
        for cx in (int(np.ceil(left))+1, int(np.floor(right))-4):
            for cy in (int(np.ceil(top))+1, int(np.floor(bottom))-4):
                if np.mean(coverage[cy:cy+3, cx:cx+3]) < .85:
                    return None
    geometry = np.array([left-sw/2, top-sw/2, right-left+sw, bottom-top+sw, sw])
    # Re-express the fitted gradient at the measured native centerline bounds.
    low = geometry[contract['axis']]
    span = geometry[2+contract['axis']]
    slope = (colors[3:]-colors[:3])/(w if contract['axis'] == 0 else h)
    start = colors[:3]+(low-bounds[contract['axis']])*slope
    colors = np.r_[start, start+span*slope]
    interior = (xx+.5 > left+3) & (xx+.5 < right-3) & (yy+.5 > top+3) & (yy+.5 < bottom-3)
    if rounded:
        interior &= _native_fill_mask(dict(kind='rectangle', geometry=geometry, radius=radius),
                                      xx+.5, yy+.5, inset=3)
    mask = ((np.max(abs(pixels.astype(float)-predicted), axis=2) > threshold) & interior).astype('uint8')
    return geometry, colors, predicted, mask, dict(stroke=stroke, radius=radius)


def _coverage_boundary(coverage, ring):
    """Subpixel half-coverage crossings, never the boundary of the canvas."""
    points = []
    for axis in (0, 1):
        a, b = ((coverage[:-1], coverage[1:]) if axis == 0 else
                (coverage[:, :-1], coverage[:, 1:]))
        allowed = (ring[:-1] & ring[1:]) if axis == 0 else (ring[:, :-1] & ring[:, 1:])
        valid = allowed & ((a < .5) != (b < .5)) & (abs(b-a) > .1)
        y, x = np.nonzero(valid)
        t = (.5-a[valid])/(b[valid]-a[valid])
        points.append(np.c_[x+.5+(t if axis == 1 else 0), y+.5+(t if axis == 0 else 0)])
    points = np.concatenate(points)
    height, width = coverage.shape
    points = points[(points[:, 0] > 1) & (points[:, 0] < width-1)
                    & (points[:, 1] > 1) & (points[:, 1] < height-1)]
    return points[::max(1, len(points)//1200)]


def _observed_rectangle(points, shape, rounded):
    """Fit only observed sides/arcs; reject a rank-deficient hidden boundary.

    The signed-distance Jacobian must independently constrain every bound
    and radius. In particular a sharp rectangle with a missing side has a
    zero column and cannot be completed from a generator's aspect ratio.
    """
    if len(points) < 32:
        return None
    height, width = shape
    lo, hi = points.min(axis=0), points.max(axis=0)
    if min(hi-lo) < 24:
        return None

    def residual(p):
        left, top, right, bottom = p[:4]
        radius = p[4] if rounded else 0.
        q = abs(points-np.array([(left+right)/2, (top+bottom)/2]))
        q -= np.array([(right-left)/2-radius, (bottom-top)/2-radius])
        return np.linalg.norm(np.maximum(q, 0), axis=1)+np.minimum(np.max(q, axis=1), 0)-radius

    best = None
    for radius in ((8., 24., 48.) if rounded else (0.,)):
        search = current_search()
        if search is not None and search.time_reason():
            return None
        initial = np.r_[lo, hi, radius] if rounded else np.r_[lo, hi]
        limit = min(shape)/3
        lower = [-limit, -limit, 1., 1.]+([1.] if rounded else [])
        upper = [width-1., height-1., width+limit, height+limit]+([limit] if rounded else [])
        initial = np.clip(initial, np.array(lower)+.001, np.array(upper)-.001)
        p = initial
        for _ in range(32):
            if search is not None and search.time_reason():
                return None
            error = residual(p)
            jac = np.column_stack([(residual(p+np.eye(len(p))[i]*.025)-error)/.025
                                   for i in range(len(p))])
            step = np.linalg.solve(jac.T@jac+np.eye(len(p))*.001, -jac.T@error)
            step *= min(1., 8./max(1e-9, np.max(abs(step))))
            improved = False
            for factor in (1., .5, .25, .125):
                trial = np.clip(p+factor*step, lower, upper)
                if np.mean(residual(trial)**2) < np.mean(error**2):
                    p, improved = trial, True
                    break
            if not improved or np.max(abs(step)) < .0001:
                break
        error = residual(p)
        if best is None or np.mean(error**2) < np.mean(best[1]**2):
            jac = np.column_stack([(residual(p+np.eye(len(p))[i]*.025)-error)/.025
                                   for i in range(len(p))])
            best = p, error, jac
    p, error, jac = best
    singular = np.linalg.svd(jac, compute_uv=False)
    if (singular[-1] < singular[0]*.015 or np.max(abs(error)) > 1.
            or np.sqrt(np.mean(error**2)) > .35):
        return None
    left, top, right, bottom = p[:4]
    radius = p[4] if rounded else 0.
    if min(right-left, bottom-top) < 24 or radius > min(right-left, bottom-top)/3:
        return None
    if not rounded:
        for axis, bound, low, high in ((0, left, top, bottom), (0, right, top, bottom),
                                      (1, top, left, right), (1, bottom, left, right)):
            side = (abs(points[:, axis]-bound) < .4) & (points[:, 1-axis] > low+2) & (points[:, 1-axis] < high-2)
            if side.sum() < 8 or np.ptp(points[side, 1-axis]) < 8:
                return None
    # Radius needs independent curved evidence in at least two corners.
    if rounded:
        corners = 0
        for cx in (left+radius, right-radius):
            for cy in (top+radius, bottom-radius):
                dx, dy = points[:, 0]-cx, points[:, 1]-cy
                arc = ((dx < -1 if cx == left+radius else dx > 1)
                       & (dy < -1 if cy == top+radius else dy > 1)
                       & (abs(np.hypot(dx, dy)-radius) < 1.))
                if arc.sum() >= 5:
                    angles = np.unwrap(np.sort(np.arctan2(dy[arc], dx[arc])))
                    corners += np.ptp(angles) >= .35
        if corners < 2:
            return None
    return np.array([left, top, right, bottom, radius])


def _clipped_rectangular_context(pixels, contract, foreground, contour, threshold):
    """Explain cropped parent paint from independent visible boundary samples."""
    height, width = foreground.shape
    yy, xx = np.indices(foreground.shape)
    silhouette = np.zeros_like(foreground)
    cv2.drawContours(silhouette, [contour], -1, 1, cv2.FILLED)
    distance = cv2.distanceTransform(silhouette, cv2.DIST_L2, 3)
    # Distance-to-frame is excluded from this exposure estimate as well.
    frame = np.minimum.reduce([xx, width-1-xx, yy, height-1-yy])
    exposed = (distance > 4) & (distance < 18) & (frame > 4)
    bounds = np.array([0., 0., float(width), float(height)])
    colors = _gradient(pixels, exposed, bounds, contract['axis'])
    if colors is None:
        return None
    coordinate = xx if contract['axis'] == 0 else yy
    span = width if contract['axis'] == 0 else height
    predicted = colors[:3]+((coordinate+.5)/span)[..., None]*(colors[3:]-colors[:3])
    observed, delta = pixels.astype(float)-255., predicted-255.
    plain = np.clip(np.sum(observed*delta, axis=2)/np.maximum(1., np.sum(delta*delta, axis=2)), 0, 1)
    kernel = np.ones((13, 13), 'uint8')
    ring = (cv2.dilate(silhouette, kernel) != cv2.erode(
        silhouette, kernel, borderType=cv2.BORDER_CONSTANT, borderValue=0)) & (frame > 0)
    coverage, stroke, sw = plain, np.zeros(3), 0.
    if contract['outlined']:
        residual = np.max(abs(observed-plain[..., None]*delta), axis=2)
        evidence = ring & (residual > 4) & (pixels.mean(axis=2) >= 180)
        samples, strength = pixels[evidence], residual[evidence]
        if len(samples) < 24:
            return None
        stroke = np.median(samples[strength >= np.percentile(strength, 95)], axis=0)
        rim = stroke-255.
        dd, rr, dr = np.sum(delta*delta, axis=2), float(rim@rim), delta@rim
        determinant = dd*rr-dr*dr
        if np.any(determinant[ring] < .002*dd[ring]*rr):
            return None
        od, ort = np.sum(observed*delta, axis=2), observed@rim
        coverage = np.clip((od*rr-ort*dr)/np.maximum(1., determinant), 0, 1)
        rim_coverage = np.clip((ort*dd-od*dr)/np.maximum(1., determinant), 0, 1)
    pure_fill = np.max(abs(pixels.astype(float)-predicted), axis=2) <= 2
    pure_white = np.min(pixels, axis=2) >= 254
    coverage[pure_fill], coverage[pure_white] = 1., 0.
    points = _coverage_boundary(coverage, ring)
    measured = _observed_rectangle(points, foreground.shape, contract.get('parent_rounded', False))
    if measured is None:
        return None
    left, top, right, bottom, radius = measured
    # Integrate antialias coverage on independently exposed straight spans.
    # Interpolating the half-coverage crossing biases a subpixel edge by up
    # to a quarter pixel, enough to displace a thin rim in another renderer.
    edges = [left, top, right, bottom]
    for index, (axis, bound, low, high) in enumerate((
            (0, left, top, bottom), (1, top, left, right),
            (0, right, top, bottom), (1, bottom, left, right))):
        length = width if axis == 0 else height
        if not 1 < bound < length-1:
            continue
        indices = np.arange(max(1, int(np.ceil(low+radius+4))),
                            min((height if axis == 0 else width)-1, int(high-radius-4)))
        a, b = max(0, int(bound)-3), min(length, int(np.ceil(bound))+4)
        if len(indices) < 8:
            continue
        band = coverage[indices, a:b] if axis == 0 else coverage[a:b, indices].T
        profile = np.median(band, axis=0)
        rising = index < 2
        if (profile[0] < .1 and profile[-1] > .9) if rising else (profile[0] > .9 and profile[-1] < .1):
            edges[index] = a+float(np.sum(1-profile if rising else profile))
    left, top, right, bottom = edges
    if contract['outlined']:
        rim_coverage[pure_fill | pure_white] = 0.
        # Integrate the rim normal to each independently visible straight
        # side. A cut edge contributes no samples or fictitious perimeter.
        widths = []
        for axis, bound in ((0, left), (0, right), (1, top), (1, bottom)):
            length = width if axis == 0 else height
            if not 3 < bound < length-3:
                continue
            low, high = (top+radius+4, bottom-radius-4) if axis == 0 else (left+radius+4, right-radius-4)
            indices = np.arange(max(2, int(np.ceil(low))), min((height if axis == 0 else width)-2, int(high)))
            a, b = max(0, int(bound)-6), min(length, int(bound)+7)
            if len(indices) >= 8:
                band = rim_coverage[indices, a:b] if axis == 0 else rim_coverage[a:b, indices]
                widths.append(float(np.median(band.sum(axis=1 if axis == 0 else 0))))
        if len(widths) < 2 or max(widths)-min(widths) > .85:
            return None
        sw = float(np.median(widths))
        if not .5 <= sw <= min(right-left, bottom-top)/4:
            return None
    geometry = np.array([left-sw/2, top-sw/2, right-left+sw, bottom-top+sw, sw])
    radius = radius+sw/2 if contract.get('parent_rounded') else 0.
    slope = (colors[3:]-colors[:3])/span
    start = colors[:3]+geometry[contract['axis']]*slope
    colors = np.r_[start, start+geometry[2+contract['axis']]*slope]
    interior = _native_fill_mask(dict(kind='rectangle', geometry=geometry, radius=radius), xx+.5, yy+.5, inset=3)
    mask = ((np.max(abs(pixels.astype(float)-predicted), axis=2) > threshold) & interior).astype('uint8')
    return geometry, colors, predicted, mask, dict(stroke=stroke, radius=radius)


def detect_instances(pixels, contract, *, residual_threshold=25, split_components=False,
                     overlap_proposals=None):
    """Fit background paint first, then explain contrasting interior regions."""
    context = _gradient_context(pixels, contract, residual_threshold)
    if context is None:
        return None
    geometry, colors, predicted, mask, distance = context
    yy, xx = np.indices(mask.shape)
    number, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    components = []
    children = []
    if contract.get('overlap'):
        children = _overlap_instances(pixels, predicted, mask, rounded=contract.get('rounded', False),
                                      outlined=contract['outlined'], circles=bool(contract['children'].get('circle')),
                                      split_components=split_components, proposals=overlap_proposals)
        if children is None:
            return None
    for index in (() if contract.get('overlap') else range(1, number)):
        if stats[index, cv2.CC_STAT_AREA] < 12:
            continue
        component = (labels == index).astype('uint8')
        parts = (_split_flat_component(pixels, predicted, component)
                 if split_components and not contract['outlined'] else [component])
        components.extend((part, len(parts) > 1) for part in parts)
        if len(components) > 16:
            return None
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
            if contract.get('rounded'):
                # Parent paint next to a dark rim must not be selected as
                # the claimed highlight. Require an observed light band
                # above that same local parent, not just above the fill.
                light = np.mean(pixels.astype(float)-predicted, axis=2) > 8
                if np.count_nonzero(band & light) < (w+h)/2:
                    return None
                # Separate fill and rim coverage against the local parent
                # paint. Projecting only on fill/rim mistakes the darker
                # gradient outside a rounded corner for additional fill.
                delta, rim = fill-predicted, stroke-predicted
                observed = pixels.astype(float)-predicted
                dd = np.sum(delta*delta, axis=2)
                rr = np.sum(rim*rim, axis=2)
                dr = np.sum(delta*rim, axis=2)
                determinant = dd*rr-dr*dr
                if np.any(determinant[component.astype(bool)] < .002*dd[component.astype(bool)]*rr[component.astype(bool)]):
                    return None
                od, ort = np.sum(observed*delta, axis=2), np.sum(observed*rim, axis=2)
                coverage = np.clip((od*rr-ort*dr)/np.maximum(1., determinant), 0, 1)
                rim_coverage = np.clip((ort*dd-od*dr)/np.maximum(1., determinant), 0, 1)
                if np.count_nonzero(band & (rim_coverage > .4)) < (w+h)/2:
                    return None
                left_right = _rounded_coverage_edges(
                    np.median(coverage[y+h//3:y+2*h//3], axis=0), x, x+w)
                top_bottom = _rounded_coverage_edges(
                    np.median(coverage[:, x+w//3:x+2*w//3], axis=1), y, y+h)
                # Each central section crosses two rims. Their integrated
                # coverage gives the observed width, rather than a fixed
                # width which trades against the rounded fill geometry.
                horizontal_rim = np.median(rim_coverage[y+h//3:y+2*h//3], axis=0)
                vertical_rim = np.median(rim_coverage[:, x+w//3:x+2*w//3], axis=1)
                sw = float(np.median([
                    horizontal_rim[max(0, x-3):x+w+3].sum()/2,
                    vertical_rim[max(0, y-3):y+h+3].sum()/2]))
                if not .5 <= sw <= min(w, h)/4:
                    return None
            else:
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
            # A rim is painted over the fill. Its inner boundary has radius
            # rx-sw/2; measure the exposed fill, then recover the centerline.
            inset = sw/2
            left, top, right, bottom = x+inset, y+inset, x+w-inset, y+h-inset
            cx = np.clip(np.minimum(xx+1, right)-np.maximum(xx, left), 0, 1)
            cy = np.clip(np.minimum(yy+1, bottom)-np.maximum(yy, top), 0, 1)
            window = ((xx >= np.floor(left)-1) & (xx <= np.ceil(right))
                      & (yy >= np.floor(top)-1) & (yy <= np.ceil(bottom)))
            missing = float(np.sum((cx*cy-coverage)[window]))
            corner = np.sqrt(max(0., missing)/(4-np.pi))
            # A square silhouette cannot earn an explicit rounding claim
            # just by fitting an imperceptibly small positive radius.
            if corner < 1.25:
                return None
            child['radius'] = min(float(corner)+inset, min(w, h)/3)
        children.append(child)
    if len(children) > 16:
        return None
    children.sort(key=lambda obj: obj['geometry'][0])
    parent = _gradient_parent(pixels, contract, geometry, colors, predicted, distance)
    return [parent, *children] if parent is not None else None


def _gradient_parent(pixels, contract, geometry, colors, predicted, distance):
    if contract.get('parent_kind') == 'rectangle':
        return dict(kind='rectangle', geometry=geometry.copy(), colors=np.r_[colors, distance['stroke']],
                    radius=distance['radius'])
    geometry = geometry.copy()
    radius = geometry[2]/2
    band = (distance >= radius-1) & (distance < radius)
    stroke = np.median(pixels[band], axis=0)
    geometry[4] = 1. if contract['outlined'] else 0.
    if contract['outlined'] and (contract.get('rounded') or contract.get('overlap')):
        center = geometry[:2]+radius
        # A cropped rim contributes only its visible circumference. Its width
        # must not shrink merely because another part lies outside the canvas.
        circumference = radius*_visible_parent_arc(center, radius, pixels.shape[:2])
        # White AA around an unoutlined circle is not an observed light rim.
        # Require color evidence outside the parent/white compositing line.
        delta = predicted-255.
        observed = pixels.astype(float)-255.
        plain_coverage = np.clip(np.sum(observed*delta, axis=2)
                                 / np.maximum(1., np.sum(delta*delta, axis=2)), 0, 1)
        rim_evidence = np.max(abs(observed-plain_coverage[..., None]*delta), axis=2) > 4
        ring = (distance >= radius-2) & (distance < radius+3)
        if np.count_nonzero(rim_evidence & ring) < .3*circumference:
            return None
        # A dark outer rim is visible just inside its foreground contour.
        # Sampling white antialias pixels beyond it must not turn it into a
        # claimed light rim merely because global pixel error stays small.
        if np.percentile(np.mean(pixels[band]-predicted[band], axis=1), 20) < -15:
            return None
        # The foreground contour follows the dark fill inside a pale rim.
        # Seed the native centerline outside that contour, and sample the
        # exposed rim instead of assigning the parent's gradient to it.
        band = (distance >= radius+.4) & (distance < radius+.9)
        stroke = np.median(pixels[band], axis=0)
        delta, rim = predicted-255., stroke-255.
        observed = pixels.astype(float)-255.
        dd = np.sum(delta*delta, axis=2)
        rr = float(rim@rim)
        dr = delta@rim
        determinant = dd*rr-dr*dr
        ring = (distance >= radius-2) & (distance < radius+4)
        if np.any(determinant[ring] < .002*dd[ring]*rr):
            return None
        rim_coverage = np.clip(((observed@rim)*dd-np.sum(observed*delta, axis=2)*dr)
                               / np.maximum(1., determinant), 0, 1)
        sw = float(rim_coverage[ring].sum()/circumference)
        if not .5 <= sw <= radius/2:
            return None
        geometry[:2] -= sw/2
        geometry[2:4] += sw
        geometry[4] = sw
    return dict(kind='circle', geometry=geometry, colors=np.r_[colors, stroke])


def _island_partitions(paints, target, *, max_states, stats):
    """Bounded exact covers: every observed island belongs to exactly one child.

    Nearby components are merged first, but distance only ranks proposals.
    Native boundary evidence and full registration decide their validity.
    """
    stats.update(states=0, state_limit_reached=False, candidate_limit_reached=False)
    initial = tuple(tuple((part,) for part in parts) for _, _, parts in paints)
    total = sum(map(len, initial))
    if total > 16:
        stats['candidate_limit_reached'] = True
        return
    if not len(paints) < target < total or max_states <= 0:
        return  # Union and individual-component hypotheses have already run.
    boxes = [{part: cv2.boundingRect((labels == part).astype('uint8')) for part in parts}
             for _, labels, parts in paints]

    def bounds(color, group):
        b = np.array([boxes[color][part] for part in group])
        low = b[:, :2].min(axis=0)
        return low, (b[:, :2]+b[:, 2:]).max(axis=0)

    queue, seen, serial = [(0., 0, initial)], {initial}, 0
    while queue:
        session = current_search()
        if session and session.time_reason():
            return
        score, _, state = heapq.heappop(queue)
        stats['states'] += 1
        count = sum(map(len, state))
        if count == target:
            yield [(color, np.isin(labels, group))
                   for (color, labels, _), groups in zip(paints, state) for group in groups]
            continue
        yield None  # Resume through the existing scheduler between states.
        for color, groups in enumerate(state):
            for i, a in enumerate(groups):
                for j in range(i+1, len(groups)):
                    merged = tuple(sorted((*a, *groups[j])))
                    replacement = tuple(sorted((merged, *(g for k, g in enumerate(groups) if k not in (i, j)))))
                    proposal = (*state[:color], replacement, *state[color+1:])
                    if proposal in seen:
                        continue
                    if len(seen) >= max_states:
                        stats['state_limit_reached'] = True
                        continue
                    al, ah = bounds(color, a)
                    bl, bh = bounds(color, groups[j])
                    gap = np.maximum(0, np.maximum(al-bh, bl-ah))
                    cost = float(gap@gap)
                    serial += 1
                    seen.add(proposal)
                    heapq.heappush(queue, (score+cost, serial, proposal))


def grouped_overlap_instances(pixels, contract, *, max_states, stats, overlap_proposals=None):
    """Explore mixed instance/island covers under the remaining edit budget."""
    stats.update(states=0, state_limit_reached=False, candidate_limit_reached=False)
    session = current_search()
    if session and session.time_reason():
        return
    context = _gradient_context(pixels, contract, 25)
    if context is None:
        return
    geometry, colors, predicted, mask, distance = context
    paints = _paint_components(pixels, mask, outlined=contract['outlined'])
    if paints is None:
        return
    parent = _gradient_parent(pixels, contract, geometry, colors, predicted, distance)
    if parent is None:
        return
    for groups in _island_partitions(paints, sum(contract['children'].values()),
                                     max_states=max_states, stats=stats):
        if session and session.time_reason():
            return
        if groups is None:
            yield None
            continue
        children = _overlap_instances(pixels, predicted, mask, rounded=contract['rounded'],
                                     outlined=contract['outlined'], circles=bool(contract['children'].get('circle')),
                                     groups=groups, proposals=overlap_proposals)
        progress('primitive_mixed_gradient_scene_v1', event='island_partition',
                 grouping_state=stats['states'], groups=len(groups),
                 outcome='proposed' if children is not None else 'native_boundaries_rejected')
        yield [parent, *children] if children is not None else None


def _native_fill_mask(obj, xx, yy, inset=.5):
    """Analytic interior support, excluding rims and antialiased boundaries."""
    x, y, w, h, sw = obj['geometry']
    if obj['kind'] == 'circle':
        return (xx-x-w/2)**2+(yy-y-h/2)**2 <= max(0., w/2-sw/2-inset)**2
    left, top, right, bottom = x+sw/2, y+sw/2, x+w-sw/2, y+h-sw/2
    mask = (xx >= left+inset) & (xx <= right-inset) & (yy >= top+inset) & (yy <= bottom-inset)
    radius = max(0., obj.get('radius', 0.)-sw/2)
    if radius:
        dx = np.maximum(0, np.maximum(left+radius-xx, xx-(right-radius)))
        dy = np.maximum(0, np.maximum(top+radius-yy, yy-(bottom-radius)))
        mask &= dx*dx+dy*dy <= max(0., radius-inset)**2
    return mask


def _rim_front(pixels, objects, i, j):
    """Equal fills cannot identify depth; require a visible native rim instead.

    Sample each candidate rim inside the other's fill, away from all third
    objects. One must be observed and the other covered by flat paint.
    """
    a, b = objects[i]['geometry'], objects[j]['geometry']
    low = np.maximum(0, np.floor(np.maximum(a[:2], b[:2])-2)).astype(int)
    high = np.minimum(pixels.shape[1::-1],
                      np.ceil(np.minimum(a[:2]+a[2:4], b[:2]+b[2:4])+2)).astype(int)
    left, top = low
    right, bottom = high
    if right <= left or bottom <= top:
        return None
    yy, xx = np.mgrid[top:bottom, left:right].astype(float)+.5
    data = pixels[top:bottom, left:right].astype(float)
    foreign = np.zeros(xx.shape, dtype=bool)
    for k, obj in enumerate(objects):
        if k not in (i, j):
            foreign |= _native_fill_mask(obj, xx, yy, -obj['geometry'][4]-1.)
    support = []
    for k, other in ((i, j), (j, i)):
        obj = objects[k]
        sw = obj['geometry'][4]
        band = (_native_fill_mask(obj, xx, yy, -sw+.3)
                & ~_native_fill_mask(obj, xx, yy, -.3)
                & _native_fill_mask(objects[other], xx, yy, 1.) & ~foreign)
        fill, stroke = obj['colors'][:3], obj['colors'][6:]
        delta = stroke-fill
        if sw < .5 or delta@delta < 100:
            return None
        if np.count_nonzero(band) < 5:
            # A narrow, axis-aligned rim can straddle pixel centres along its
            # entire length. Measure its pixel footprints instead of widening
            # the rim or interpolating new observations. Each selected pixel
            # must have at least half its area in the native stroke, entirely
            # inside the other fill and clear of every third object.
            area = np.zeros(xx.shape, dtype=float)
            clean = np.ones(xx.shape, dtype=bool)
            for dy in (-.4375, -.3125, -.1875, -.0625, .0625, .1875, .3125, .4375):
                for dx in (-.4375, -.3125, -.1875, -.0625, .0625, .1875, .3125, .4375):
                    sx, sy = xx+dx, yy+dy
                    area += (_native_fill_mask(obj, sx, sy, -sw)
                             & ~_native_fill_mask(obj, sx, sy, 0.))
                    clean &= _native_fill_mask(objects[other], sx, sy, 1.)
                    for third, foreign_obj in enumerate(objects):
                        if third not in (i, j):
                            clean &= ~_native_fill_mask(foreign_obj, sx, sy,
                                                       -foreign_obj['geometry'][4]-1.)
            band = (area >= 32) & clean
        if np.count_nonzero(band) < 5:
            return None
        coverage = (data-fill)@delta/(delta@delta)
        error = np.max(abs(data-fill-coverage[..., None]*delta), axis=2)
        supported = (coverage >= .5) & (error <= 12)
        support.append(float(np.mean(supported[band])))
    if support[0] >= .7 and support[1] <= .2:
        return i
    if support[1] >= .7 and support[0] <= .2:
        return j
    return None


def observed_painter_order(pixels, objects):
    """Propose a depth DAG from flat paint inside observed intersections.

    Third-party paint supplies no evidence for either member of a pair.
    Rounded corners, rims and antialias edges are excluded. Unobserved pairs
    impose no edge; balanced conflicting paint or a cycle cannot justify an order.
    This only proposes topology: registration retains every existing gate.
    """
    children = objects[1:]
    yy, xx = np.indices(pixels.shape[:2], dtype=float)
    xx, yy = xx+.5, yy+.5
    masks = [_native_fill_mask(obj, xx, yy) for obj in children]
    paints = [np.max(abs(pixels.astype(float)-obj['colors'][:3]), axis=2) <= 12
              for obj in children]
    successors = [set() for _ in children]
    incoming = [0]*len(children)
    for i in range(len(children)):
        for j in range(i+1, len(children)):
            intersection = masks[i] & masks[j]
            if not intersection.any():
                continue
            if np.max(abs(children[i]['colors'][:3]-children[j]['colors'][:3])) <= 12:
                front = _rim_front(pixels, children, i, j)
                if front is None:
                    return None
                back = j if front == i else i
                successors[back].add(front)
                incoming[front] += 1
                continue
            a, b = (np.count_nonzero(intersection & paints[k]) for k in (i, j))
            # Subpixel boundary estimates may include a few pixels of the
            # rear fill. Use a dominant observed paint as a proposal; balanced
            # contradictory evidence remains unresolved. Final depth and
            # raster gates still decide whether this order can be accepted.
            if a and b and max(a, b) < 4*min(a, b):
                return None
            if not (a or b):
                continue
            back, front = (j, i) if a > b else (i, j)
            successors[back].add(front)
            incoming[front] += 1
    order = []
    ready = [i for i, count in enumerate(incoming) if count == 0]
    while ready:
        node = ready.pop(0)
        order.append(node)
        for front in sorted(successors[node]):
            incoming[front] -= 1
            if incoming[front] == 0:
                ready.append(front)
    if len(order) != len(children):
        return None
    return [objects[0], *(children[i] for i in order)]


def _overlap_groups_match(scene, neighbours, expected, *, isolated=0):
    """Require the stated overlap groups and singleton components.

    Native rims of different groups must remain separated as well. Expanded
    silhouettes conservatively retain a one-pixel uncertainty gap; bounding
    boxes only limit the work and never establish a group or separation.
    """
    remaining = set(neighbours)
    groups = []
    while remaining:
        reached, pending = set(), [min(remaining)]
        while pending:
            node = pending.pop()
            if node not in reached:
                reached.add(node)
                pending.extend(neighbours[node]-reached)
        groups.append(reached)
        remaining -= reached
    if (sum(len(group) > 1 for group in groups) != expected
            or sum(len(group) == 1 for group in groups) != isolated):
        return False
    for index, group in enumerate(groups):
        for other in groups[index+1:]:
            for i in group:
                for j in other:
                    a, b = scene[i]['geometry'], scene[j]['geometry']
                    left, top = np.floor(np.maximum(a[:2]-a[4]/2, b[:2]-b[4]/2)-1).astype(int)
                    right, bottom = np.ceil(np.minimum(a[:2]+a[2:4]+a[4]/2,
                                                      b[:2]+b[2:4]+b[4]/2)+1).astype(int)
                    if right <= left or bottom <= top:
                        continue
                    yy, xx = np.mgrid[top:bottom, left:right].astype(float)+.5
                    if np.any(_native_fill_mask(scene[i], xx, yy, -a[4]-1.)
                              & _native_fill_mask(scene[j], xx, yy, -b[4]-1.)):
                        return False
    return True


def fit_mixed_gradient_scene(width, height, *, description, image, render_fn, error_fn):
    contract = scene_contract(description)
    pixels = np.asarray(image)
    if (contract is None or pixels.shape != (height, width, 3) or min(width, height) < 24
            or not np.isfinite(pixels).all()):
        return None
    attempts, seen, seeds = [], set(), []
    overlap_proposals = _OverlapProposals(pixels) if contract.get('overlap') else None
    detector_options = dict(overlap_proposals=overlap_proposals) if overlap_proposals is not None else {}
    session = current_search()
    rejection_scope = (raster_identity(pixels), tuple(sorted(contract['children'].items())),
                       contract['axis'], contract['outlined'], contract['layout_axis'], contract['rounded'],
                       contract.get('overlap', False), contract['overlap_groups'],
                       contract.get('isolated_children', 0), contract.get('parent_kind', 'circle'),
                       contract.get('parent_rounded', False))
    rejected = session.structure_rejections.setdefault(rejection_scope, {}) if session else {}

    def register(objects, attempt):
        attempts.append(attempt)
        try:
            if objects is not None:
                key = scene_key(objects, ordered=contract.get('overlap', False))
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
        objects = detect_instances(pixels, contract, residual_threshold=threshold, **detector_options)
        ordering = 'bounded_agenda'
        if objects is not None:
            if contract.get('overlap') and (len(objects) > 5 or contract['children'].get('circle')
                                          or contract['overlap_groups'] > 1
                                          or contract.get('isolated_children', 0)):
                ordered = observed_painter_order(pixels, objects)
                if ordered is not None:
                    objects = ordered
                    ordering = 'observed_depth'
            seeds.append(objects)
        return (yield from register(objects, dict(residual_threshold=threshold,
            operator='segmentation', painter_order=ordering, outcome='no_complete_scene')))

    def repairs():
        # Initial jobs each yield after detection. This job starts only after
        # those slices, so all observed instances are available to the agenda.
        stats, split_stats, group_stats, outcome = {}, {}, {}, 'cancelled'
        try:
            for proposal in edit_proposals(seeds, contract['children'], stats=stats,
                                           ordered=contract.get('overlap', False)):
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
            if (contract.get('overlap') or
                    (not contract['outlined'] and contract['children'].get('rectangle', 0) >= 2)):
                seed_keys = {scene_key(seed, ordered=contract.get('overlap', False)) for seed in seeds}
                for threshold in (25, 16, 36):
                    if session and session.time_reason():
                        return None
                    objects = detect_instances(pixels, contract, residual_threshold=threshold,
                                               split_components=True, **detector_options)
                    yield None
                    ordering = 'bounded_agenda'
                    if objects is not None and contract.get('overlap'):
                        ordered = observed_painter_order(pixels, objects)
                        if ordered is not None:
                            objects = ordered
                            ordering = 'observed_depth'
                    key = scene_key(objects, ordered=contract.get('overlap', False)) if objects is not None else None
                    if key is not None and key not in seed_keys:
                        seed_keys.add(key)
                        seeds.append(objects)
                        changed = True
                    fitted = yield from register(objects, dict(operator='split',
                        residual_threshold=threshold, painter_order=ordering, outcome='no_complete_scene'))
                    if fitted is not None:
                        outcome = 'accepted'
                        return fitted
            if contract.get('overlap') and remaining:
                for objects in grouped_overlap_instances(pixels, contract, max_states=remaining,
                                                        stats=group_stats, **detector_options):
                    if session and session.time_reason():
                        return None
                    yield None
                    if objects is None:
                        continue
                    ordered = observed_painter_order(pixels, objects)
                    if ordered is not None:
                        objects = ordered
                    fitted = yield from register(objects, dict(operator='group_islands',
                        residual_threshold=25, grouping_state=group_stats['states'],
                        painter_order='observed_depth' if ordered is not None else 'bounded_agenda',
                        outcome='no_complete_scene'))
                    if fitted is not None:
                        outcome = 'accepted'
                        return fitted
                remaining -= group_stats['states']
            if changed and remaining:
                for proposal in edit_proposals(seeds, contract['children'],
                                               max_states=remaining, stats=split_stats,
                                               ordered=contract.get('overlap', False)):
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
            for extra in (group_stats, split_stats):
                if extra:
                    stats['states'] += extra['states']
                    for name in ('state_limit_reached', 'candidate_limit_reached'):
                        stats[name] |= extra[name]
            if session and session.time_reason():
                outcome = 'time_limit'
            progress('primitive_mixed_gradient_scene_v1', event='structure_search_finished',
                     outcome=outcome, grouping_states=group_stats.get('states', 0), **stats)

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
    if (not complete(objects, contract['children'])
            or objects[0]['kind'] != contract.get('parent_kind', 'circle')):
        return None
    n = len(objects)
    rounded = contract.get('rounded', False) or contract.get('parent_rounded', False)
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
        scene = [dict(kind=o['kind'], geometry=geometry(p, i),
                      colors=(p[offsets[i]:offsets[i]+9] if i == 0 else
                              np.r_[p[offsets[i]:offsets[i]+3], p[offsets[i]:offsets[i]+6]]),
                      radius=p[5*n+i] if rounded else 0.) for i, o in enumerate(objects)]
        for i, obj in enumerate(scene):
            x, y, w, h, sw = obj['geometry']
            if min(w, h) < 4:
                return False
            if not (0 <= x < x+w <= width and 0 <= y < y+h <= height):
                if i:
                    return False
                if obj['kind'] == 'rectangle':
                    # Bounds were independently constrained by visible sides
                    # and arcs. Registration may refine them locally, never
                    # replace a missing boundary with the canvas edge.
                    measured = objects[0]['geometry']
                    if np.max(abs(obj['geometry'][:4]-measured[:4])) > 2.5:
                        return False
                else:
                    center, radius = np.array([x+w/2, y+h/2]), w/2
                    if (not 12 <= radius <= min(width, height)
                            or not (0 <= center[0] <= width and 0 <= center[1] <= height)
                            or _visible_parent_arc(center, radius, (height, width)) < np.pi):
                        return False
            if ((contract['outlined'] and not .5 <= sw <= min(w, h)/4)
                    or (not contract['outlined'] and sw != 0)):
                return False
            if i and not _contains(scene[0], obj):
                return False
            if i and contract.get('parent_rounded'):
                # Strict corner support in the measured rounded parent;
                # bounding-box containment alone admits shapes in cutouts.
                cx, cy, cw, ch, cs = obj['geometry']
                if not np.all(_native_fill_mask(scene[0],
                        np.array([cx-cs/2, cx+cw+cs/2])[:, None],
                        np.array([cy-cs/2, cy+ch+cs/2])[None, :], inset=1)):
                    return False
            if rounded:
                radius = p[5*n+i]
                required = (contract.get('rounded', False) if i else contract.get('parent_rounded', False))
                required = required and obj['kind'] == 'rectangle'
                if ((required and not 1. <= radius <= min(w, h)/3)
                        or (not required and radius != 0)):
                    return False
            if contract['outlined']:
                c = np.clip(p[offsets[i]:offsets[i]+(9 if i == 0 else 6)], 0, 255)
                if c[-3:].mean() < 180 or (i and c[-3:].mean() < c[:3].mean()+15):
                    return False
        if contract.get('overlap'):
            from src.iCCModules.imageCompositeConverterSceneFusion import compatible
            # This path measures each exposed rim separately. Reuse the
            # filled-scene topology check on centerlines; full outlined
            # containment and raster quality are checked independently here.
            topology = [dict(o, fill=True, geometry=np.r_[o['geometry'][:4], 0.])
                        for o in scene[1:]]
            if not compatible(topology,
                              dict(overlap=True, counts=contract['children'])):
                return False
            # Global/local area metrics alone can tolerate a wrong painter
            # order at a small intersection. Bind the front role to its own
            # observed flat paint inside that intersection as well.
            neighbours = {i: set() for i in range(1, n)}
            for i in range(1, n):
                for j in range(i+1, n):
                    a, b = scene[i]['geometry'], scene[j]['geometry']
                    left, top = np.ceil(np.maximum(a[:2], b[:2])+1).astype(int)
                    right, bottom = np.floor(np.minimum(a[:2]+a[2:4], b[:2]+b[2:4])-1).astype(int)
                    if right-left < 2 or bottom-top < 2:
                        continue
                    native_silhouettes = (bool(contract['children'].get('circle'))
                                          or contract.get('overlap_groups', 1) > 1
                                          or bool(contract.get('isolated_children', 0)))
                    yy, xx = np.mgrid[top:bottom, left:right]
                    visible = np.ones((bottom-top, right-left), dtype=bool)
                    if native_silhouettes:
                        # Bounding boxes of circles may intersect outside
                        # their actual fills. Only native silhouette pixels
                        # can establish a depth edge or supply front paint.
                        visible &= (_native_fill_mask(scene[i], xx+.5, yy+.5, 1.)
                                    & _native_fill_mask(scene[j], xx+.5, yy+.5, 1.))
                        if not visible.any():
                            continue
                    neighbours[i].add(j)
                    neighbours[j].add(i)
                    # A later layer owns its pixels, including a rim/rounded
                    # boundary. It cannot serve as evidence for this pair.
                    for later in scene[j+1:]:
                        x, y, w, h, sw = later['geometry']
                        if native_silhouettes:
                            visible &= ~_native_fill_mask(later, xx+.5, yy+.5, -sw-1.)
                        else:
                            visible &= ~((xx+.5 >= x-sw/2-1) & (xx+.5 <= x+w+sw/2+1)
                                         & (yy+.5 >= y-sw/2-1) & (yy+.5 <= y+h+sw/2+1))
                    if not visible.any():
                        continue
                    if np.max(abs(scene[i]['colors'][:3]-scene[j]['colors'][:3])) <= 12:
                        # Matching flat fills are no proof of the claimed
                        # front role. Preserve the observed rim order as the
                        # geometry changes during registration as well.
                        if _rim_front(pixels, scene[1:], i-1, j-1) != j-1:
                            return False
                    front = np.clip(p[offsets[j]:offsets[j]+3], 0, 255)
                    error = np.max(abs(pixels[top:bottom, left:right].astype(float)-front), axis=2)
                    if np.percentile(error[visible], 80) > 12:
                        return False
            if not _overlap_groups_match(scene, neighbours, contract.get('overlap_groups', 1),
                                         isolated=contract.get('isolated_children', 0)):
                return False
        # Every other pair must be disjoint, in any arrangement. An explicitly
        # named row/column imposes its stronger interval-separation rule.
        for i, a in enumerate([] if contract.get('overlap') else scene[1:]):
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
    clipped_rectangle = False
    if contract.get('parent_kind') == 'rectangle':
        context = _gradient_context(pixels, contract, 25)
        if context is None:
            return None
        if np.max(abs(objects[0]['geometry'][:4]-context[0][:4])) > 2.5:
            return None
        if contract.get('parent_rounded'):
            x, y, w, h, sw = objects[0]['geometry']
            extent = objects[0]['radius']+sw/2+3
            for left in (x-sw/2, x+w+sw/2-extent):
                for top in (y-sw/2, y+h+sw/2-extent):
                    regions.append((max(0, int(left)-1), max(0, int(top)-1),
                                    min(width, int(np.ceil(left+extent))+1),
                                    min(height, int(np.ceil(top+extent))+1)))
        x, y, w, h, sw = objects[0]['geometry']
        clipped_rectangle = (x-sw/2 < 4 or y-sw/2 < 4 or x+w+sw/2 > width-4 or y+h+sw/2 > height-4)
        if clipped_rectangle:
            # Long visible sides need their own edge gate: the parent's large
            # area and curved corners cannot certify a displaced straight rim.
            margin = max(5., objects[0].get('radius', 0.)+sw+3)+3
            for axis, edge, direction in ((0, x-sw/2, 1), (0, x+w+sw/2, -1),
                                          (1, y-sw/2, 1), (1, y+h+sw/2, -1)):
                inner = edge+direction*sw
                if not 1 < inner < (width if axis == 0 else height)-1:
                    continue
                low, high = (y-sw/2+margin, y+h+sw/2-margin) if axis == 0 else (
                    x-sw/2+margin, x+w+sw/2-margin)
                a, b = (edge-3, edge+4+sw) if direction == 1 else (edge-4-sw, edge+3)
                region = ((a, low, b, high) if axis == 0 else (low, a, high, b))
                l, t, r, b = region
                region = (max(0, int(l)), max(0, int(t)),
                          min(width, int(np.ceil(r))), min(height, int(np.ceil(b))))
                if region[2] > region[0] and region[3] > region[1]:
                    regions.append(region)
        # Bright residual patches are not flat dark child proposals. Preserve
        # their local evidence too, so a large parent cannot dilute omissions.
        _, _, stats, _ = cv2.connectedComponentsWithStats(context[3])
        for x, y, w, h, area in stats[1:]:
            if area >= 12:
                regions.append((max(0, x-3), max(0, y-3), min(width, x+w+3), min(height, y+h+3)))
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

    def corner_seeds():
        if clipped_rectangle:
            # Edge integration is accurate to fractions of a pixel. Translate
            # or resize opposite bounds together before individual coordinates:
            # moving just one bound also changes the gradient's color field and
            # can violate the original error bound despite fixing a local side.
            for axis in range(2):
                for shift in (-.03125, .03125, -.0078125, .0078125, -.0625, .0625):
                    candidate = parameters.copy()
                    candidate[[axis, axis+2]] += shift
                    yield candidate
                    candidate = parameters.copy()
                    candidate[axis] += shift
                    candidate[axis+2] -= shift
                    yield candidate
            for index in range(5):
                for shift in (-.03125, .03125, -.0625, .0625):
                    candidate = parameters.copy()
                    candidate[index] += shift
                    yield candidate
        if contract.get('parent_rounded'):
            # Corrected native corners match the analytic area deficit. Keep
            # seeds close to that measured radius, sharing all image budgets.
            for radius in np.linspace(.95*parameters[5*n], 1.05*parameters[5*n], 5):
                candidate = parameters.copy()
                candidate[5*n] = radius
                yield candidate

    checkpoint_error = float('inf')

    def satisfactory(p, measured):
        nonlocal checkpoint_error
        quality = qualities(measured[3])
        if not all(q and q['passed'] for q in quality):
            return False
        # Preserve a fully checked incumbent while the common minimum-effort
        # search continues. The supervisor can retain it at the hard deadline;
        # topology, every visible side/corner, and strict pixels still apply.
        if clipped_rectangle and measured[1] < checkpoint_error-1e-9:
            validated_result(dict(svg=measured[2], rendered=measured[3], error=measured[1],
                source='primitive_mixed_gradient_scene_v1', object_kinds=[o['kind'] for o in objects],
                object_quality=quality[:n], evidence_quality=quality[n:]), pixels)
            checkpoint_error = measured[1]
        return True

    fitted = yield from _register_steps(parameters, geometry_count, build, valid, pixels, render_fn, error_fn,
                       'primitive_mixed_gradient_scene_v1', preserve_initial_error=True,
                       loss_fn=loss, initial_candidates=corner_seeds(),
                       refinement_steps=(.125, .0625) if clipped_rectangle else (1., .5, .25, .125),
                       eager_satisfactory=clipped_rectangle,
                       satisfactory_fn=satisfactory)
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
