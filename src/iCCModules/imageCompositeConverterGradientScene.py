"""Native rectangular scenes with axial gradients and optional white children.

Only raster boundaries and description constraints seed the registration. No
catalogue identities, saved vectors or traced output paths participate.
"""
from __future__ import annotations

import re

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register
from src.iCCModules.imageCompositeConverterPrimitiveScene import _local_quality


def requested(description):
    text = str(description or '').casefold()
    return 'rechteck' in text and 'verlauf' in text and 'gerundet' in text


def scene_contract(description):
    """A deliberately closed vocabulary; unsupported assertions never disappear."""
    text = str(description or '').casefold().replace('weiss', 'weiß').replace('äusser', 'äußer')
    if not requested(text):
        return None
    from src.iCCModules.imageCompositeConverterLayeredScene import SHAPES
    matches = list(SHAPES.finditer(text))
    if not matches or any(m[3].startswith('kreis') for m in matches):
        return None
    count = sum({'zwei': 2, '2': 2, 'drei': 3, '3': 3}.get(m[1], 1) for m in matches)
    if not 1 <= count <= 3:
        return None
    nested = 'ineinander verschachtelt' in text
    separate = 'getrennt nebeneinander' in text or 'getrennt untereinander' in text
    if (count > 1 and nested == separate) or (nested and count != 2) or (count == 1 and separate):
        return None
    horizontal, vertical = 'horizontal' in text, 'vertikal' in text
    if horizontal == vertical:
        return None
    if nested and not ('die innere form ist weiß' in text and 'die äußere form hat einen' in text):
        return None
    if not nested and ('innere form' in text or 'äußere form' in text):
        return None
    outlined = 'jede form hat eine dunkle kontur' in text
    # Consuming known clauses rather than rejecting a keyword shortlist makes
    # unknown content, relations and negations a conservative model failure.
    remaining = SHAPES.sub('', text)
    clauses = [r'mit leicht gerundeten ecken', r'und (?:horizontal|vertikal)em farbverlauf',
               r'die formen sind ineinander verschachtelt',
               r'die formen liegen getrennt (?:nebeneinander|untereinander)',
               r'die äußere form hat einen (?:horizontal|vertikal)en farbverlauf',
               r'jede form hat einen (?:horizontal|vertikal)en farbverlauf',
               r'die innere form ist weiß', r'jede form hat eine dunkle kontur',
               r'keine beschriftung', r'ohne text oder zeichen', r'weißer hintergrund']
    extent = r'(?:geringfügig|etwas|ein wenig|leicht)'
    clauses.append(r'(?:das (?:gesamte )?motiv|die (?:gesamte )?darstellung) ist '+extent+
                   r' (?:grösser|kleiner) dargestellt und '+extent+
                   r' nach (?:links|rechts) und (?:oben|unten) (?:versetzt|verschoben)')
    for clause in clauses:
        remaining = re.sub(clause, '', remaining)
    if re.sub(r'[\s.,;]+', '', remaining):
        return None
    return dict(count=count, nested=nested, axis=0 if horizontal else 1, outlined=outlined,
                layout_axis=1 if 'untereinander' in text else 0)


def _rectangle(contour, *, hole=False):
    x, y, w, h = cv2.boundingRect(contour)
    if min(w, h) < 7 or cv2.contourArea(contour) < .7*(w-1)*(h-1):
        return None
    missing = max(0., (w-1)*(h-1)-cv2.contourArea(contour))
    radius = min(min(w, h)/3, np.sqrt(missing/(4-np.pi)))
    inset = 1. if hole else 0.
    return np.array([x+inset, y+inset, x+w-inset, y+h-inset, max(.5, radius-inset), 0.])


def _gradient(pixels, mask, geometry, axis):
    """Robust affine color fit to visible interiors, excluding child and contour."""
    core = cv2.erode(mask.astype('uint8'), np.ones((5, 5), 'uint8')).astype(bool)
    if core.sum() < 12:
        core = cv2.erode(mask.astype('uint8'), np.ones((3, 3), 'uint8')).astype(bool)
    if core.sum() < max(12, .25*mask.sum()):
        # Erosion of thin borders can retain only isolated thick corners,
        # which do not constrain the visible long sides. Keep those sides and
        # let the robust regression discard JPEG/antialias fringes instead.
        core = mask.astype(bool)
    yy, xx = np.nonzero(core)
    if len(xx) < 12:
        return None
    low, high = geometry[axis], geometry[axis+2]
    t = ((xx if axis == 0 else yy)+.5-low)/(high-low)
    values = pixels[yy, xx].astype(float)
    design = np.c_[np.ones(len(t)), t]
    keep = np.ones(len(t), dtype=bool)
    for _ in range(3):
        if keep.sum() < 12 or np.ptp(t[keep]) < .08:
            return None
        fit = np.linalg.lstsq(design[keep], values[keep], rcond=None)[0]
        residual = np.max(abs(values-design@fit), axis=1)
        keep = residual <= max(4., float(np.percentile(residual, 80)))
    # A flat fill or the wrong gradient axis must not satisfy an explicit
    # gradient assertion merely because a global pixel gate is permissive.
    if np.max(abs(fit[1])) < 8 or np.percentile(residual[keep], 80) > 12:
        return None
    return np.clip(np.r_[fit[0], fit[0]+fit[1]], 0, 255)


def detect_rectangles(pixels, contract):
    foreground = (np.max(255-pixels.astype(float), axis=2) > 25).astype('uint8')
    contours, hierarchy = cv2.findContours(foreground, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hierarchy is None:
        return None
    outers = [i for i, h in enumerate(hierarchy[0]) if h[3] == -1 and cv2.contourArea(contours[i]) >= 20]
    expected = 1 if contract['nested'] else contract['count']
    if len(outers) != expected:
        return None
    objects = []
    for index in outers:
        geometry = _rectangle(contours[index])
        if geometry is None:
            return None
        holes = [i for i, h in enumerate(hierarchy[0]) if h[3] == index and cv2.contourArea(contours[i]) >= 12]
        if len(holes) != int(contract['nested']):
            return None
        mask = np.zeros(foreground.shape, 'uint8')
        cv2.drawContours(mask, contours, index, 1, -1)
        for hole in holes:
            cv2.drawContours(mask, contours, hole, 0, -1)
        colors = _gradient(pixels, mask, geometry, contract['axis'])
        if colors is None:
            return None
        stroke = np.array([48., 48., 48.])
        if contract['outlined']:
            boundary = mask.astype(bool) & ~cv2.erode(mask, np.ones((3, 3), 'uint8'),
                                                    borderType=cv2.BORDER_CONSTANT, borderValue=0).astype(bool)
            dark = pixels[boundary]
            dark = dark[dark.mean(axis=1) <= np.percentile(dark.mean(axis=1), 35)]
            stroke = np.median(dark, axis=0)
            geometry[:2] += 1.
            geometry[2:4] -= 1.
            geometry[5] = 2.
        objects.append(dict(geometry=geometry, colors=colors, stroke=stroke, parent=None))
        for hole in holes:
            child = _rectangle(contours[hole], hole=True)
            if child is None:
                return None
            if contract['outlined']:
                child[:2] -= 1.
                child[2:4] += 1.
                child[5] = 2.
            objects.append(dict(geometry=child, colors=np.full(6, 255.), stroke=stroke, parent=0))
    return objects


def fit_gradient_scene(width, height, *, description, image, render_fn, error_fn):
    contract = scene_contract(description)
    pixels = np.asarray(image)
    if contract is None or pixels.shape != (height, width, 3) or min(width, height) < 12 or not np.isfinite(pixels).all():
        return None
    objects = detect_rectangles(pixels, contract)
    if objects is None:
        return None
    n = len(objects)
    parameters = np.r_[np.concatenate([o['geometry'] for o in objects]),
                       np.concatenate([np.r_[o['colors'], o['stroke']] for o in objects])]

    def build(p):
        definitions, shapes = [], []
        for i, obj in enumerate(objects):
            x, y, X, Y, radius, sw = p[6*i:6*i+6]
            c = p[6*n+9*i:6*n+9*i+9]
            if obj['parent'] is None:
                end = 'x2="100%" y2="0%"' if contract['axis'] == 0 else 'x2="0%" y2="100%"'
                definitions.append(f'<linearGradient id="g{i}" x1="0%" y1="0%" {end}><stop offset="0" stop-color="{_hex(c[:3])}"/><stop offset="1" stop-color="{_hex(c[3:6])}"/></linearGradient>')
                fill = f'url(#g{i})'
            else:
                fill = '#ffffff'
            stroke = _hex(c[6:9]) if contract['outlined'] else 'none'
            shapes.append(f'<rect x="{x:.4f}" y="{y:.4f}" width="{X-x:.4f}" height="{Y-y:.4f}" rx="{radius:.4f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:.4f}"/>')
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><defs>'+''.join(definitions)+f'</defs><rect width="{width}" height="{height}" fill="#ffffff"/>'+''.join(shapes)+'</svg>'

    def valid(p):
        boxes = []
        for i, obj in enumerate(objects):
            x, y, X, Y, radius, sw = p[6*i:6*i+6]
            if min(X-x, Y-y) < 5 or not .25 <= radius <= min(X-x, Y-y)/2:
                return False
            if not (-.5 <= x < X <= width+.5 and -.5 <= y < Y <= height+.5):
                return False
            if ((contract['outlined'] and not .5 <= sw <= min(X-x, Y-y)/4)
                    or (not contract['outlined'] and sw != 0)):
                return False
            colors = np.clip(np.rint(p[6*n+9*i:6*n+9*i+6]), 0, 255)
            if obj['parent'] is None and np.max(abs(colors[3:]-colors[:3])) < 8:
                return False
            if obj['parent'] is not None:
                a, b, A, B = boxes[obj['parent']]
                if not (a < x < X < A and b < y < Y < B):
                    return False
            boxes.append((x, y, X, Y))
        if not contract['nested']:
            axis = contract['layout_axis']
            ordered = sorted(boxes, key=lambda box: box[axis])
            if any(a[axis+2] >= b[axis] for a, b in zip(ordered, ordered[1:])):
                return False
        return True

    regions = [(max(0, int(o['geometry'][0])-2), max(0, int(o['geometry'][1])-2),
                min(width, int(np.ceil(o['geometry'][2]))+2), min(height, int(np.ceil(o['geometry'][3]))+2)) for o in objects]

    def qualities(raster):
        return [_local_quality(pixels[y:Y, x:X], raster[y:Y, x:X]) for x, y, X, Y in regions]

    fitted = _register(parameters, 6*n, build, valid, pixels, render_fn, error_fn,
                       'primitive_gradient_scene_v1', preserve_initial_error=True,
                       # A broad pixel pass can conceal a one-pixel shift in
                       # corner radius. Refine subpixel boundaries before an
                       # early exit; noisy originals can finish the schedule.
                       satisfactory_fn=lambda p, m: (float(abs(pixels.astype(float)-m[3]).mean()) <= .5
                                                    and all(q and q['passed'] for q in qualities(m[3]))))
    if fitted is None:
        return None
    quality = _local_quality(pixels, fitted['rendered'])
    local = qualities(fitted['rendered'])
    if not quality or not quality['passed'] or any(not q or not q['passed'] for q in local):
        return None
    fitted.update(object_kinds=['rectangle']*n, object_quality=local, neural_scene_selected=False,
                  scene_hypotheses=1, instance_groups=n, scene_detectors=['gradient_rectangle_boundaries'])
    return fitted
