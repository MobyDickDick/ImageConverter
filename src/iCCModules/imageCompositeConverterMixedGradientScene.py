"""Raster-derived gradient circles containing flat native shapes.

The closed description contract controls topology; raster residuals supply
instances, including rounded rectangles. No catalogue keys, saved geometry
or reference vectors are read.
"""
from __future__ import annotations

import heapq
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
    overlap = relation+' und überlappen sich teilweise' in text
    if sum(counts.values()) > 2:
        layouts = [name for name in ('nebeneinander', 'untereinander', 'voneinander')
                   if relation+' und getrennt '+name in text]
        if overlap and not layouts:
            relation += ' und überlappen sich teilweise'
        elif len(layouts) != 1 or overlap:
            return None
        else:
            relation += ' und getrennt '+layouts[0]
            layout_axis = {'nebeneinander': 0, 'untereinander': 1}.get(layouts[0])
    if text.count(relation) != 1:
        return None
    outlined = 'die formen haben helle konturen' in text
    rounded_clause = 'mit leicht gerundeten ecken'
    rounded = rounded_clause in text
    # Larger inventories use observed pairwise depth as an ordering proposal;
    # the fallback agenda still has 96 states, never a factorial expansion.
    if overlap and not 2 <= sum(counts.values())-1 <= 8:
        return None
    # The qualifier belongs to the quantified rectangle inventory. A free
    # clause must not attach rounding to circles or silently discard a claim.
    if rounded and (text.count(rounded_clause) != 1
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
                outlined=outlined, layout_axis=layout_axis, rounded=rounded, overlap=overlap,
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


def _exposed_corner_radius(data, predicted, fill, coverage, box, *, reconstructed=None, foreign_mask=None,
                           rim_inset=0.):
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
            for extent in np.arange(span, 4., -1.):
                window = ((xx >= np.floor(a)-1) & (xx <= np.ceil(X))
                          & (yy >= np.floor(b)-1) & (yy <= np.ceil(Y))
                          & (xx < a+extent if left else xx >= X-extent)
                          & (yy < b+extent if top else yy >= Y-extent))
                if np.any(foreign & window):
                    continue
                missing = float(np.sum((ideal-coverage)[window]))
                radius = np.sqrt(max(0., missing)/(1-np.pi/4))
                # Shrinking an observation window is valid only when the
                # entire rounded corner still fits inside the exposed area.
                if radius+2 <= extent:
                    radii.append(radius)
                break
    # A rim reduces the observed inner radius. Apply the native rounding
    # threshold to the centerline, retaining a positive measured inner deficit.
    if (len(radii) < 2 or min(radii) < .75 or min(radii)+rim_inset < 1.25
            or max(radii)-min(radii) > 1.5):
        return None
    radius = float(np.median(radii))
    return radius if radius <= min(w, h)/3 else None


def _overlap_circle(component, background, coverage, reconstruction_error, shape):
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
    yy, xx = np.where(component)
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
    if not 2 <= len(colors) <= 8 or any(
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


def _overlap_instances(pixels, predicted, mask, *, rounded=False, outlined=False, circles=False,
                       split_components=False, groups=None):
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
            stroke = np.median(samples[samples.mean(axis=1) >= np.percentile(samples.mean(axis=1), 95)], axis=0)
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


def _gradient_context(pixels, contract, residual_threshold):
    """Measure the shared parent once for all island grouping hypotheses."""
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
    return geometry, colors, predicted, mask, distance


def detect_instances(pixels, contract, *, residual_threshold=25, split_components=False):
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
                                      split_components=split_components)
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
    geometry = geometry.copy()
    radius = geometry[2]/2
    band = (distance >= radius-1) & (distance < radius)
    stroke = np.median(pixels[band], axis=0)
    geometry[4] = 1. if contract['outlined'] else 0.
    if contract['outlined'] and (contract.get('rounded') or contract.get('overlap')):
        # White AA around an unoutlined circle is not an observed light rim.
        # Require color evidence outside the parent/white compositing line.
        delta = predicted-255.
        observed = pixels.astype(float)-255.
        plain_coverage = np.clip(np.sum(observed*delta, axis=2)
                                 / np.maximum(1., np.sum(delta*delta, axis=2)), 0, 1)
        rim_evidence = np.max(abs(observed-plain_coverage[..., None]*delta), axis=2) > 4
        ring = (distance >= radius-2) & (distance < radius+3)
        if np.count_nonzero(rim_evidence & ring) < .3*2*np.pi*radius:
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
        sw = float(rim_coverage[ring].sum()/(2*np.pi*radius))
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


def grouped_overlap_instances(pixels, contract, *, max_states, stats):
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
                                     groups=groups)
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


def fit_mixed_gradient_scene(width, height, *, description, image, render_fn, error_fn):
    contract = scene_contract(description)
    pixels = np.asarray(image)
    if (contract is None or pixels.shape != (height, width, 3) or min(width, height) < 24
            or not np.isfinite(pixels).all()):
        return None
    attempts, seen, seeds = [], set(), []
    session = current_search()
    rejection_scope = (raster_identity(pixels), tuple(sorted(contract['children'].items())),
                       contract['axis'], contract['outlined'], contract['layout_axis'], contract['rounded'],
                       contract.get('overlap', False))
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
        objects = detect_instances(pixels, contract, residual_threshold=threshold)
        ordering = 'bounded_agenda'
        if objects is not None:
            if contract.get('overlap') and (len(objects) > 5 or contract['children'].get('circle')):
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
                                               split_components=True)
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
                for objects in grouped_overlap_instances(pixels, contract, max_states=remaining, stats=group_stats):
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
        scene = [dict(kind=o['kind'], geometry=geometry(p, i),
                      radius=p[5*n+i] if rounded else 0.) for i, o in enumerate(objects)]
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
                    mixed_primitives = bool(contract['children'].get('circle'))
                    yy, xx = np.mgrid[top:bottom, left:right]
                    visible = np.ones((bottom-top, right-left), dtype=bool)
                    if mixed_primitives:
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
                        if mixed_primitives:
                            visible &= ~_native_fill_mask(later, xx+.5, yy+.5, -sw-1.)
                        else:
                            visible &= ~((xx+.5 >= x-sw/2-1) & (xx+.5 <= x+w+sw/2+1)
                                         & (yy+.5 >= y-sw/2-1) & (yy+.5 <= y+h+sw/2+1))
                    if not visible.any():
                        continue
                    front = np.clip(p[offsets[j]:offsets[j]+3], 0, 255)
                    error = np.max(abs(pixels[top:bottom, left:right].astype(float)-front), axis=2)
                    if np.percentile(error[visible], 80) > 12:
                        return False
            reached, pending = set(), [1]
            while pending:
                node = pending.pop()
                if node not in reached:
                    reached.add(node)
                    pending.extend(neighbours[node]-reached)
            if len(reached) != n-1:
                return False  # Every claimed overlapping child participates.
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
