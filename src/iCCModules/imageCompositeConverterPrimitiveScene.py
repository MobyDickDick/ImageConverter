"""Bounded scene fitting for one to three separate, unlabelled outline shapes.

Components supply instances, contours supply alternative analytic hypotheses.
No contour paths or reference vectors are emitted. Each instance must agree
with the description and pass local pixel/foreground/edge checks after fitting.
"""
from __future__ import annotations

import itertools
import re

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register
from src.iCCModules.imageCompositeConverterSearchPortfolio import validated_result

QUANTIFIED_SHAPE = re.compile(
    r'\b(ein(?:e|en|em)?|1|zwei|2|drei|3)\s+'
    r'(?:(?:voneinander|getrennt\w*|unbeschriftet\w*|einzeln\w*)\s+)*'
    r'(kreis(?:e|en)?|rechteck(?:e|en)?)\b')


def description_counts(description):
    text = str(description or '').casefold()
    # Only the initial, deliberately limited vocabulary is supported. Negative
    # text constraints are consumed before rejecting positive text requirements.
    text = re.sub(r'(?:keine?|ohne)\s+(?:beschriftung|schriftzeichen|schrift|text)(?:\s+oder\s+zeichen)?', '', text)
    if re.search(r'verlauf|gefüllt|fuell|füll|schraff|stiel|schaft|griff|pfeil|dreieck|linie|text|beschrift|buchstab|zeichen|zusätzlich|überlapp|berühr|verbunden', text):
        return None
    if re.search(r'(?:kein\w*|ohne)\s+(?:kreis\w*|rechteck\w*)', text):
        return None
    if re.search(r'(?:kein\w*|ohne|nicht)\s+(?:\w+\s+)?(?:kontur\w*|umriss\w*|rand\w*)', text):
        return None
    counts = {'circle': 0, 'rectangle': 0}
    matches = list(QUANTIFIED_SHAPE.finditer(text))
    for match in matches:
        number = {'zwei': 2, '2': 2, 'drei': 3, '3': 3}.get(match[1], 1)
        counts['circle' if match[2].startswith('kreis') else 'rectangle'] += number
    # Unquantified additional shape mentions are ambiguous; do not erase them.
    remainder = QUANTIFIED_SHAPE.sub('', text)
    if re.search(r'kreis|rechteck', remainder) or not 1 <= sum(counts.values()) <= 3:
        return None
    return counts


def _circle(contour):
    points = contour[:, 0].astype(float) + .5
    matrix = np.c_[2*points, np.ones(len(points))]
    coefficients = np.linalg.lstsq(matrix, (points**2).sum(axis=1), rcond=None)[0]
    center = coefficients[:2]
    radius = np.sqrt(max(0., coefficients[2]+(center**2).sum()))
    residual = np.abs(np.linalg.norm(points-center, axis=1)-radius).mean()
    return center, radius, residual


def _alternatives(mask, pixels):
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hierarchy is None:
        return []
    outer = [i for i, row in enumerate(hierarchy[0]) if row[3] == -1]
    if len(outer) != 1:
        return []
    idx = outer[0]
    holes = [i for i, row in enumerate(hierarchy[0]) if row[3] == idx]
    # Solid fills, labels, nested objects and damaged contours are out of scope.
    if len(holes) != 1:
        return []
    outside, inside = contours[idx], contours[holes[0]]
    x,y,w,h = cv2.boundingRect(outside)
    ix,iy,iw,ih = cv2.boundingRect(inside)
    if min(w,h,iw,ih) < 5:
        return []
    colors = pixels[mask.astype(bool)]
    dark = colors[colors.mean(axis=1) <= np.percentile(colors.mean(axis=1), 40)]
    color = np.median(dark, axis=0)
    result = []
    center, radius, residual = _circle(outside)
    inner_center, inner_radius, inner_residual = _circle(inside)
    if (abs(w-h) <= 2 and residual < .65 and inner_residual < .65
            and np.linalg.norm(center-inner_center) < .8):
        r = (radius+inner_radius)/2
        sw = radius-inner_radius+.8
        result.append(('circle', [center[0]-r, center[1]-r, 2*r, 2*r, sw], color))
    epsilon = .025*cv2.arcLength(outside, True)
    polygon = cv2.approxPolyDP(outside, epsilon, True)
    if len(polygon) == 4 and cv2.contourArea(outside) >= (w-1)*(h-1)*.94:
        sw = ((ix-x)+(iy-y)+(x+w-ix-iw)+(y+h-iy-ih))/4 + 1
        result.append(('rectangle', [x+sw/2, y+sw/2, w-sw, h-sw, sw], color))
    return result


def _local_quality(reference, output):
    a = np.max(255-reference.astype(float),axis=2) > 25
    b = np.max(255-output.astype(float),axis=2) > 25
    union = a | b
    error = np.mean((reference.astype(float)-output.astype(float))**2,axis=2)/255**2
    iou = np.count_nonzero(a & b)/max(1,np.count_nonzero(union))
    fg = float(error[union].mean()) if union.any() else 0.
    ae, be = cv2.Canny(reference,50,140)>0, cv2.Canny(output,50,140)>0
    if not ae.any() or not be.any():
        return None
    da = cv2.distanceTransform((~ae).astype(np.uint8),cv2.DIST_L2,3)
    db = cv2.distanceTransform((~be).astype(np.uint8),cv2.DIST_L2,3)
    edge = float((np.exp(-db[ae]).mean()+np.exp(-da[be]).mean())/2)
    return dict(normalized_mse=float(error.mean()), foreground_mse=fg,
                foreground_iou=float(iou), edge_alignment=edge,
                passed=bool(error.mean() <= .01 and fg <= .04 and iou >= .85 and edge >= .72))


def fit_primitive_scene(width, height, *, description, image, render_fn, error_fn):
    from src.iCCModules.imageCompositeConverterGradientScene import requested as gradient_requested, fit_gradient_scene
    if gradient_requested(description):
        return fit_gradient_scene(width, height, description=description, image=image,
                                  render_fn=render_fn, error_fn=error_fn)
    from src.iCCModules.imageCompositeConverterSceneVisibility import requested, fit_visibility_scene
    if requested(description):
        return fit_visibility_scene(width, height, description=description, image=image,
                                    render_fn=render_fn, error_fn=error_fn)
    # Keep established outline scenes byte-identical; flat colored/nested
    # scenes share the same CLI registration and supervised image budget.
    fitted = _fit_outline_scene(width, height, description=description, image=image,
                                render_fn=render_fn, error_fn=error_fn)
    if fitted is not None:
        return fitted
    from src.iCCModules.imageCompositeConverterLayeredScene import fit_layered_scene
    fitted = fit_layered_scene(width, height, description=description, image=image,
                               render_fn=render_fn, error_fn=error_fn)
    if fitted is not None:
        return fitted
    from src.iCCModules.imageCompositeConverterSceneFusion import fit_fused_scene
    return fit_fused_scene(width, height, description=description, image=image,
                           render_fn=render_fn, error_fn=error_fn)


def _fit_outline_scene(width, height, *, description, image, render_fn, error_fn):
    counts = description_counts(description)
    if counts is None:
        return None
    pixels = np.asarray(image)
    if pixels.shape != (height,width,3) or min(width,height) < 16 or not np.isfinite(pixels).all():
        return None
    border = np.concatenate([pixels[0],pixels[-1],pixels[:,0],pixels[:,-1]])
    if np.max(np.abs(border.astype(float)-255)) > 3:
        return None
    mask = (np.max(255-pixels.astype(float),axis=2)>25).astype(np.uint8)
    number, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if number-1 != sum(counts.values()):
        return None
    text = str(description).casefold()
    boxes = stats[1:, :4]
    for axis, requested in ((0, 'nebeneinander' in text),
                            (1, 'übereinander' in text or 'untereinander' in text)):
        if requested:
            intervals = sorted((box[axis], box[axis]+box[axis+2]) for box in boxes)
            if any(left[1] >= right[0] for left,right in zip(intervals,intervals[1:])):
                return None
    choices, regions = [], []
    # Optional proposal source; the original analytic alternatives and all
    # description, object-local and full-image quality gates remain mandatory.
    from src.iCCModules.imageCompositeConverterNeuralElements import runtime_proposals, scene_alternatives
    neural = runtime_proposals(pixels)
    neural_ids = set()
    for index in range(1,number):
        x,y,w,h,area = stats[index]
        if area < 12 or x < 2 or y < 2 or x+w > width-2 or y+h > height-2:
            return None
        # White interiors are required, as are clear gaps between instances.
        component = (labels == index).astype(np.uint8)
        alternatives = _alternatives(component,pixels)
        for candidate in scene_alternatives(component, pixels, neural):
            if not any(candidate[0] == old[0] and np.allclose(candidate[1], old[1]) for old in alternatives):
                alternatives.append(candidate)
                neural_ids.add(id(candidate))
        if not alternatives:
            return None
        choices.append(alternatives)
        regions.append((max(0,x-3),max(0,y-3),min(width,x+w+3),min(height,y+h+3)))
    best = None
    for scene in itertools.product(*choices):
        if any(sum(obj[0] == kind for obj in scene) != n for kind,n in counts.items()):
            continue
        kinds = [obj[0] for obj in scene]
        n = len(scene)
        p = np.r_[np.concatenate([obj[1] for obj in scene]), np.concatenate([obj[2] for obj in scene])]

        def build(p):
            shapes = []
            for i,kind in enumerate(kinds):
                x,y,w,h,sw = p[i*5:i*5+5]
                color = _hex(p[5*n+3*i:5*n+3*i+3])
                style = f'fill="none" stroke="{color}" stroke-width="{sw:.4f}"'
                if kind == 'circle':
                    shapes.append(f'<circle cx="{x+w/2:.4f}" cy="{y+h/2:.4f}" r="{w/2:.4f}" {style}/>')
                else:
                    shapes.append(f'<rect x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}" {style}/>')
            return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="{width}" height="{height}" fill="#ffffff"/>'+''.join(shapes)+'</svg>'

        def valid(p):
            for i in range(n):
                x,y,w,h,sw = p[i*5:i*5+5]
                if min(w,h) < 5 or not .7 <= sw <= min(w,h)/3:
                    return False
                if x-sw/2 < 1 or y-sw/2 < 1 or x+w+sw/2 > width-1 or y+h+sw/2 > height-1:
                    return False
            return True

        # Equal per-object weight prevents large instances drowning out small ones.
        def loss(a,b):
            return float(np.mean([np.mean((a[y:Y,x:X].astype(float)-b[y:Y,x:X].astype(float))**2)
                                  for x,y,X,Y in regions]))

        fitted = _register(p,5*n,build,valid,pixels,render_fn,error_fn,
                           'primitive_scene_v1',loss_fn=loss,preserve_initial_error=True,
                           satisfactory_fn=lambda p,measured: all(
                               (q is not None and q['passed']) for q in
                               (_local_quality(pixels[y:Y,x:X],measured[3][y:Y,x:X]) for x,y,X,Y in regions)))
        if fitted is None:
            continue
        qualities = [_local_quality(pixels[y:Y,x:X], fitted['rendered'][y:Y,x:X]) for x,y,X,Y in regions]
        global_quality = _local_quality(pixels,fitted['rendered'])
        if not global_quality or not global_quality['passed'] or any(not q or not q['passed'] for q in qualities):
            continue
        fitted['object_kinds'] = kinds
        fitted['neural_scene_selected'] = any(id(obj) in neural_ids for obj in scene)
        fitted['object_quality'] = qualities
        if best is None or fitted['error'] < best['error']:
            best = fitted
        if validated_result(fitted,pixels):
            break
    from src.iCCModules.imageCompositeConverterSearchPortfolio import settings
    config = settings()
    if config and neural:
        observations = config.get('neural_observations', [])
        if observations:
            observations[-1]['scene_candidates'] += len(neural_ids)
            observations[-1]['scene_selected'] |= bool(best and best['neural_scene_selected'])
    return best
