"""Bounded composition of flat colored circle/rectangle instances.

Color regions supply boundary alternatives, never output paths. Spatially
identical boundaries are grouped before complete scene hypotheses are fitted.
Only disjoint objects and strict containment (up to three objects) are supported.
"""
from __future__ import annotations

import itertools
import re

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register
from src.iCCModules.imageCompositeConverterPrimitiveScene import _alternatives, _circle, _local_quality


SHAPES = re.compile(
    r'\b(ein(?:e|en|em)?|1|zwei|2|drei|3)\s+'
    r'((?:(?:voneinander|getrennt\w*|unbeschriftet\w*|einzeln\w*|'
    r'gefüllt\w*|einfarbig\w*|farbig\w*|klein\w*|groß\w*|dunk\w*|hell\w*)\s+)*)'
    r'(kreis(?:e|en)?|rechteck(?:e|en)?)\b')


def scene_contract(description):
    """Conservative vocabulary: reject unmodelled content and contradictory counts."""
    text = str(description or '').casefold()
    if re.search(r'nicht\s+unbeschriftet\w*', text):
        return None
    text = re.sub(r'\bunbeschriftet\w*\b', ' ', text)
    if re.search(r'nicht\s+(?:ohne|keine?)\s+(?:beschriftung|schriftzeichen|schrift|text)', text):
        return None
    text = re.sub(r'(?:keine?|ohne)\s+(?:beschriftung|schriftzeichen|schrift|text)(?:\s+oder\s+zeichen)?', '', text)
    if re.search(r'verlauf|schraff|stiel|schaft|griff|pfeil|dreieck|linie|text|schrift|buchstab|zeichen|zusätzlich|überlapp|berühr|verbunden', text):
        return None
    if re.search(r'(?:kein\w*|ohne|nicht)\s+(?:\w+\s+)?(?:kreis\w*|rechteck\w*|füll\w*|gefüllt\w*|kontur\w*|umriss\w*|rand\w*)', text):
        return None
    if re.search(r'(?:kein\w*|ohne|nicht)\s+(?:\w+\s+)?(?:verschachtel\w*|ineinander|innerhalb|getrennt\w*|nebeneinander|untereinander|übereinander)', text):
        return None
    matches = list(SHAPES.finditer(text))
    counts = {'circle': 0, 'rectangle': 0}
    for match in matches:
        counts['circle' if match[3].startswith('kreis') else 'rectangle'] += {'zwei': 2, '2': 2, 'drei': 3, '3': 3}.get(match[1], 1)
    if re.search(r'kreis|rechteck', SHAPES.sub('', text)) or not 1 <= sum(counts.values()) <= 3:
        return None
    nested = bool(re.search(r'verschachtelt|ineinander|innerhalb', text))
    separate = bool(re.search(r'getrennt|nebeneinander|untereinander|übereinander', text))
    if nested and (separate or sum(counts.values()) < 2):
        return None
    if not re.search(r'gefüllt|füllung|einfarbig', text) and not nested:
        return None  # The established outline-only path retains its output.
    return dict(counts=counts, nested=nested, separate=separate,
                filled=bool(re.search(r'gefüllt|füllung', text)),
                outlined='jede form hat eine dunkle kontur' in text,
                axis=0 if 'nebeneinander' in text else 1 if re.search(r'untereinander|übereinander', text) else None)


def _box(candidate):
    x, y, w, h, sw = candidate['geometry']
    return np.array([x-sw/2, y-sw/2, x+w+sw/2, y+h+sw/2])


def _solid(contour, color):
    x, y, w, h = cv2.boundingRect(contour)
    if min(w, h) < 7:
        return []
    result = []
    center, radius, residual = _circle(contour)
    if abs(w-h) <= 2 and residual < .65:
        r = radius + .3
        result.append(dict(kind='circle', geometry=[center[0]-r, center[1]-r, 2*r, 2*r, 0.], fill=color, stroke=color))
    polygon = cv2.approxPolyDP(contour, .025*cv2.arcLength(contour, True), True)
    if len(polygon) == 4 and cv2.contourArea(contour) >= (w-1)*(h-1)*.94:
        result.append(dict(kind='rectangle', geometry=[float(x), float(y), float(w), float(h), 0.], fill=color, stroke=color))
    return result


def detect_instances(pixels):
    """Color cores and whole foreground provide complementary analytic boundaries."""
    foreground = np.max(255-pixels.astype(float), axis=2) > 25
    values = pixels[foreground]
    if len(values) < 12:
        return []
    bins, counts = np.unique((values.astype(int)//16), axis=0, return_counts=True)
    masks = [foreground.astype('uint8')]
    # Bounded, deterministic palette; antialias colors never become output objects.
    for index in np.argsort(-counts, kind='stable')[:16]:
        if counts[index] < 12:
            continue
        members = np.all(values.astype(int)//16 == bins[index], axis=1)
        color = np.median(values[members], axis=0)
        masks.append((np.max(abs(pixels.astype(float)-color), axis=2) <= 12).astype('uint8'))
    candidates = []
    for mask in masks:
        number, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
        for index in range(1, number):
            x, y, w, h, area = stats[index]
            if area < 12 or min(w, h) < 7 or x < 2 or y < 2 or x+w > pixels.shape[1]-2 or y+h > pixels.shape[0]-2:
                continue
            component = (labels == index).astype('uint8')
            core = cv2.erode(component, np.ones((3, 3), 'uint8')).astype(bool)
            near_boundary = core & (cv2.distanceTransform(component, cv2.DIST_L2, 3) <= 3)
            color = np.median(pixels[near_boundary if near_boundary.any() else core if core.any() else component.astype(bool)], axis=0)
            contour = max(cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
            # Rings propose both native geometry and their exposed interior fill.
            rings = _alternatives(component, pixels)
            for kind, geometry, stroke in rings:
                if not .7 <= geometry[4] <= min(geometry[2:4]) / 4:
                    continue
                interior = np.zeros_like(component)
                cv2.drawContours(interior, [contour], -1, 1, -1)
                interior = cv2.erode(interior, np.ones((5, 5), 'uint8')).astype(bool) & ~component.astype(bool)
                if not interior.any():
                    continue
                # A large child can dominate the interior median. Its parent
                # fill is visible beside the parent's own boundary instead.
                band = interior & (cv2.distanceTransform(interior.astype('uint8'), cv2.DIST_L2, 3) <= 3)
                fill = np.median(pixels[band if band.any() else interior], axis=0)
                candidates.append(dict(kind=kind, geometry=geometry, fill=None if min(fill) > 245 else fill, stroke=stroke))
            candidates.extend(_solid(contour, color))
    # Group repeated threshold/color detections of one physical boundary.
    # Prefer actual outline evidence to the same boundary viewed as a solid blob.
    candidates.sort(key=lambda c: (-bool(c['geometry'][4]), -float(np.prod(_box(c)[2:]-_box(c)[:2])), c['kind']))
    groups = []
    for candidate in candidates:
        box = _box(candidate)
        group = next((g for g in groups if np.max(abs(_box(g[0])-box)) <= 3.), None)
        if group is None:
            groups.append([candidate])
        elif not any(c['kind'] == candidate['kind']
                     and bool(c['geometry'][4]) == bool(candidate['geometry'][4])
                     and (c['fill'] is None) == (candidate['fill'] is None)
                     and np.max(abs(c['stroke']-candidate['stroke'])) <= 12
                     and (c['fill'] is None or np.max(abs(c['fill']-candidate['fill'])) <= 12)
                     for c in group):
            # The same boundary can be a solid disk or a ring surrounding a
            # differently colored child. Group the instance, keep both models.
            group.append(candidate)
    return groups


def _contains(parent, child):
    """Strict native-shape containment, including rectangle corners inside circles."""
    px, py, pw, ph, ps = parent['geometry']
    cx, cy, cw, ch, cs = child['geometry']
    if parent['kind'] == 'rectangle':
        return bool(cx-cs/2 > px+ps/2+1 and cy-cs/2 > py+ps/2+1
                    and cx+cw+cs/2 < px+pw-ps/2-1 and cy+ch+cs/2 < py+ph-ps/2-1)
    pc = np.array([px+pw/2, py+ph/2])
    r = pw/2-ps/2-1
    if child['kind'] == 'circle':
        return np.linalg.norm(np.array([cx+cw/2, cy+ch/2])-pc)+cw/2+cs/2 < r
    return all(np.linalg.norm(np.array([x, y])-pc) < r
               for x in (cx-cs/2, cx+cw+cs/2) for y in (cy-cs/2, cy+ch+cs/2))


def _compatible(scene, contract):
    if any(sum(c['kind'] == kind for c in scene) != number for kind, number in contract['counts'].items()):
        return False
    if contract['filled'] and any(c['fill'] is None for c in scene):
        return False
    if contract['outlined'] and any(c['geometry'][4] == 0 for c in scene):
        return False
    nested_pairs = 0
    for a, b in itertools.combinations(scene, 2):
        ba, bb = _box(a), _box(b)
        disjoint = ba[2] < bb[0]-1 or bb[2] < ba[0]-1 or ba[3] < bb[1]-1 or bb[3] < ba[1]-1
        contains = _contains(a, b) or _contains(b, a)
        if not disjoint and not contains:
            return False  # Partial occlusions have no supported scene model.
        nested_pairs += contains
        axis = contract['axis']
        if axis is not None and not (ba[axis+2] < bb[axis] or bb[axis+2] < ba[axis]):
            return False
    if contract['nested'] and nested_pairs != len(scene)*(len(scene)-1)//2:
        return False
    if contract['separate'] and nested_pairs:
        return False
    return True


def fit_layered_scene(width, height, *, description, image, render_fn, error_fn):
    contract = scene_contract(description)
    if contract is None:
        return None
    pixels = np.asarray(image)
    if pixels.shape != (height, width, 3) or min(width, height) < 16 or not np.isfinite(pixels).all():
        return None
    border = np.concatenate([pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]])
    if np.max(abs(border.astype(float)-255)) > 3:
        return None
    groups = detect_instances(pixels)
    return fit_scene_groups(width, height, contract=contract, groups=groups, image=pixels,
                            render_fn=render_fn, error_fn=error_fn)


def fit_scene_groups(width, height, *, contract, groups, image, render_fn, error_fn,
                     compatible_fn=_compatible, all_orders=False, source='primitive_layered_scene_v1'):
    """Fit complete native scenes from fused instance alternatives at one budget."""
    pixels = np.asarray(image)
    n = sum(contract['counts'].values())
    # Unexplained analytic instances are not discarded even if a global score
    # could hide them. A count mismatch must return to the broader converter.
    if len(groups) != n:
        return None
    best, tried = None, 0
    scenes = itertools.product(*groups)
    if all_orders:
        # Bound proposal expansion before rendering/ranking; no detector can
        # create an exponential unbudgeted scene queue.
        scenes = list(itertools.islice(scenes, 64))
        scenes = [order for scene in scenes for order in itertools.permutations(scene)]
        # Cheap analytic color raster ranking reserves the image budget for
        # plausible painter orders. Final decisions use the real SVG renderer.
        yy, xx = np.indices((height, width), dtype=float)
        def order_loss(scene):
            from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search
            session = current_search()
            if session and session.time_reason():
                return float('inf')
            raster = np.full(pixels.shape, 255., dtype=float)
            for c in scene:
                x, y, w, h, _ = c['geometry']
                mask = ((xx+.5-x-w/2)**2+(yy+.5-y-h/2)**2 <= (w/2)**2 if c['kind'] == 'circle' else
                        (xx+.5 >= x) & (xx+.5 <= x+w) & (yy+.5 >= y) & (yy+.5 <= y+h))
                if c['fill'] is not None:
                    raster[mask] = c['fill']
            return float(np.abs(pixels.astype(float)-raster).mean())
        scenes.sort(key=order_loss)
    for scene in scenes:
        # The foreground can supply an enclosing blob already represented
        # by a color region. Only complete, nonduplicated scenes survive.
        if not compatible_fn(scene, contract):
            continue
        tried += 1
        if tried > 24:
            return best
        if not all_orders:
            scene = sorted(scene, key=lambda c: -float(np.prod(_box(c)[2:]-_box(c)[:2])))
        kinds = [c['kind'] for c in scene]
        filled = [c['fill'] is not None for c in scene]
        stroked = [c['geometry'][4] > 0 for c in scene]
        geometry_parameters = []
        # Independent centers/diameters and rectangle sides avoid an
        # artificial local minimum when only one visible edge must move.
        for c in scene:
            g = np.array(c['geometry'], dtype=float)
            if c['kind'] == 'circle':
                g[:2] += g[2:4]/2
            else:
                g[2:4] += g[:2]
            geometry_parameters.append(g)
        parameters = np.r_[np.concatenate(geometry_parameters),
                           np.concatenate([np.r_[c['stroke'], c['fill'] if c['fill'] is not None else [255]*3] for c in scene])]
        regions = [(max(0, int(_box(c)[0])-3), max(0, int(_box(c)[1])-3),
                    min(width, int(np.ceil(_box(c)[2]))+3), min(height, int(np.ceil(_box(c)[3]))+3)) for c in scene]

        def build(p):
            shapes = []
            for i, kind in enumerate(kinds):
                x, y, w, h, sw = p[5*i:5*i+5]
                if kind == 'circle':
                    h = w
                else:
                    w, h = w-x, h-y
                stroke, fill = p[5*n+6*i:5*n+6*i+6].reshape(2, 3)
                style = f'fill="{_hex(fill) if filled[i] else "none"}" stroke="{_hex(stroke) if stroked[i] else "none"}" stroke-width="{sw:.4f}"'
                if kind == 'circle':
                    shapes.append(f'<circle cx="{x:.4f}" cy="{y:.4f}" r="{w/2:.4f}" {style}/>')
                else:
                    shapes.append(f'<rect x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}" {style}/>')
            return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="{width}" height="{height}" fill="#ffffff"/>' + ''.join(shapes) + '</svg>'

        def valid(p):
            adjusted = []
            for i, kind in enumerate(kinds):
                geometry = p[5*i:5*i+5].copy()
                if kind == 'circle':
                    geometry[3] = geometry[2]
                    geometry[:2] -= geometry[2]/2
                else:
                    geometry[2:4] -= geometry[:2]
                x, y, w, h, sw = geometry
                if min(w, h) < 5 or (stroked[i] and not .7 <= sw <= min(w, h)/4):
                    return False
                if not stroked[i]:
                    if sw != 0:
                        return False
                if x-sw/2 < 1 or y-sw/2 < 1 or x+w+sw/2 > width-1 or y+h+sw/2 > height-1:
                    return False
                # A circle has one radius, so height follows width.
                if kind == 'circle':
                    geometry[3] = geometry[2]
                stroke, fill = p[5*n+6*i:5*n+6*i+6].reshape(2, 3)
                adjusted.append(dict(scene[i], geometry=geometry, stroke=stroke,
                                     fill=fill if filled[i] else None))
            return compatible_fn(adjusted, contract)

        def loss(a, b):
            # Use the production MAE metric in every object region. A
            # squared surrogate can improve while MAE regresses, causing
            # _register to restore an inadmissible initial contour fit.
            return float(np.mean([np.mean(np.abs(a[y:Y, x:X].astype(float)-b[y:Y, x:X].astype(float))) for x, y, X, Y in regions]))

        def local_pass(p, measured):
            return all(q is not None and q['passed'] for q in
                       (_local_quality(pixels[y:Y, x:X], measured[3][y:Y, x:X]) for x, y, X, Y in regions))

        fitted = _register(parameters, 5*n, build, valid, pixels, render_fn, error_fn,
                           source, loss_fn=loss, preserve_initial_error=True,
                           satisfactory_fn=local_pass)
        if fitted is None:
            continue
        quality = _local_quality(pixels, fitted['rendered'])
        qualities = [_local_quality(pixels[y:Y, x:X], fitted['rendered'][y:Y, x:X]) for x, y, X, Y in regions]
        if not quality or not quality['passed'] or any(not q or not q['passed'] for q in qualities):
            continue
        fitted.update(object_kinds=kinds, object_quality=qualities, neural_scene_selected=False,
                      scene_hypotheses=tried, instance_groups=len(groups),
                      scene_detectors=sorted({d for c in scene for d in c.get('detectors', [])}))
        if best is None or fitted['error'] < best['error']:
            best = fitted
        # Every object and the whole raster passed; no extra search is needed.
        return best
    return best
