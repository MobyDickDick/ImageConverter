"""Infer an open lower elliptical arc and a detached gradient shaft from pixels."""
from __future__ import annotations

import cv2
import numpy as np
import re
from xml.etree import ElementTree as ET

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register


def reverse_arc_shaft_svg(svg):
    """Reflect analytic coordinates vertically, including the arc sweep."""
    root = ET.fromstring(svg)
    height = float(root.get('height'))
    for shape in root:
        kind = shape.tag.rsplit('}', 1)[-1]
        if kind == 'rect':
            shape.set('y', f"{height-float(shape.get('y', 0))-float(shape.get('height')):g}")
        elif kind == 'path':
            match = re.fullmatch(r'M ([\d.e+-]+) ([\d.e+-]+) A ([\d.e+-]+) ([\d.e+-]+) 0 0 ([01]) ([\d.e+-]+) ([\d.e+-]+)', shape.get('d', ''))
            if match is None:
                raise ValueError('Expected one analytic half-ellipse')
            lx, cy, rx, ry, sweep, ex, ey = map(float, match.groups())
            shape.set('d', f'M {lx:g} {height-cy:g} A {rx:g} {ry:g} 0 0 {1-int(sweep)} {ex:g} {height-ey:g}')
    return ET.tostring(root, encoding='unicode') + '\n'


def turn_arc_shaft_svg(svg):
    """Turn the analytic upper-opening motif counterclockwise into native axes."""
    root = ET.fromstring(svg)
    width, height = float(root.get('width')), float(root.get('height'))
    root.set('width', f'{height:g}')
    root.set('height', f'{width:g}')
    root.set('viewBox', f'0 0 {height:g} {width:g}')
    for shape in root.iter():
        kind = shape.tag.rsplit('}', 1)[-1]
        if kind == 'rect':
            x, y, w, h = (float(shape.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
            shape.attrib.update(x=f'{y:g}', y=f'{width-x-w:g}', width=f'{h:g}', height=f'{w:g}')
        elif kind == 'path':
            match = re.fullmatch(r'M ([\d.e+-]+) ([\d.e+-]+) A ([\d.e+-]+) ([\d.e+-]+) 0 0 0 ([\d.e+-]+) ([\d.e+-]+)', shape.get('d', ''))
            if match is None:
                raise ValueError('Expected one analytic upper-opening half-ellipse')
            lx, cy, rx, ry, ex, ey = map(float, match.groups())
            shape.set('d', f'M {cy:g} {width-lx:g} A {ry:g} {rx:g} 0 0 0 {ey:g} {width-ex:g}')
        elif kind == 'linearGradient':
            shape.attrib.update(x1='0', y1='1', x2='0', y2='0')
    return ET.tostring(root, encoding='unicode')+'\n'


def mirror_side_arc_shaft_svg(svg):
    """Reflect native horizontal coordinates and the half-ellipse sweep."""
    root = ET.fromstring(svg)
    width = float(root.get('width'))
    for shape in root.iter():
        kind = shape.tag.rsplit('}', 1)[-1]
        if kind == 'rect':
            shape.set('x', f"{width-float(shape.get('x', 0))-float(shape.get('width')):g}")
        elif kind == 'path':
            match = re.fullmatch(r'M ([\d.e+-]+) ([\d.e+-]+) A ([\d.e+-]+) ([\d.e+-]+) 0 0 ([01]) ([\d.e+-]+) ([\d.e+-]+)', shape.get('d', ''))
            if match is None:
                raise ValueError('Expected one analytic half-ellipse')
            x, y, rx, ry, sweep, ex, ey = map(float, match.groups())
            shape.set('d', f'M {width-x:g} {y:g} A {rx:g} {ry:g} 0 0 {1-int(sweep)} {width-ex:g} {ey:g}')
    return ET.tostring(root, encoding='unicode')+'\n'


def fit_arc_shaft(width, height, *, description, image, render_fn, error_fn):
    """Normalize explicitly described directions to the upper-opening fit."""
    text = str(description or '').casefold()
    right = 'rechts offen' in text
    if right:
        if ('linker halbkreis' not in text or 'rechts neben' not in text
                or any(token in text for token in ('links offen', 'rechter halbkreis', 'links neben'))):
            return None
        text = text.replace('rechts offen', 'links offen').replace('linker halbkreis', 'rechter halbkreis').replace('rechts neben', 'links neben')
    if 'links offen' in text:
        if ('rechter halbkreis' not in text or 'links neben' not in text
                or 'waagerecht' not in text or 'vertikal' not in text
                or any(token in text for token in ('oben offen', 'unten offen', 'rechts offen', 'horizontal'))):
            return None
        arr = np.asarray(image)
        if arr.shape != (height, width, 3):
            return None

        def original_svg(svg):
            turned = turn_arc_shaft_svg(svg)
            return mirror_side_arc_shaft_svg(turned) if right else turned

        def normalized_render(svg, w, h):
            raster = render_fn(original_svg(svg), h, w)
            if raster is None:
                return None
            return np.rot90(np.fliplr(raster) if right else raster, -1)

        normalized = text.replace('links offen', 'oben offen').replace('vertikal', 'horizontal')
        result = _fit_upper_open_arc_shaft(height, width, description=normalized,
                                         image=np.rot90(np.fliplr(arr) if right else arr, -1), render_fn=normalized_render,
                                         error_fn=error_fn, preserve_initial_error=True,
                                         preserve_foreground=right)
        if result is None:
            return None
        result['svg'] = original_svg(result['svg'])
        raster = np.rot90(result['rendered'])
        result['rendered'] = (np.fliplr(raster) if right else raster).copy()
        p = result['parameters'].copy()
        p[:9] = [p[1], height-p[0], p[3], p[2], p[4], p[6], height-p[5]-p[7], p[8], p[7]]
        if right:
            p[0], p[5] = width-p[0], width-p[5]-p[7]
        result.update(parameters=p, opening='right' if right else 'left')
        return result
    lower = 'unten offen' in text
    if not lower:
        return _fit_upper_open_arc_shaft(width, height, description=text,
                                       image=image, render_fn=render_fn, error_fn=error_fn)
    if 'oben offen' in text or 'unter' not in text or 'oberen halbkreis' not in text:
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3):
        return None

    def normalized_render(svg, w, h):
        raster = render_fn(reverse_arc_shaft_svg(svg), w, h)
        return None if raster is None else np.flipud(raster)

    normalized = text.replace('unten offen', 'oben offen').replace('oberen halbkreis', 'unteren halbkreis')
    result = _fit_upper_open_arc_shaft(width, height, description=normalized,
                                     image=np.flipud(arr), render_fn=normalized_render, error_fn=error_fn,
                                     preserve_initial_error=True)
    if result is None:
        return None
    result['svg'] = reverse_arc_shaft_svg(result['svg'])
    result['rendered'] = np.flipud(result['rendered']).copy()
    parameters = result['parameters'].copy()
    parameters[1] = height - parameters[1]
    parameters[6] = height - parameters[6] - parameters[8]
    result.update(parameters=parameters, opening='down')
    return result


def _fit_upper_open_arc_shaft(width, height, *, description, image, render_fn, error_fn,
                            preserve_initial_error=False, preserve_foreground=False):
    text = str(description or '').casefold()
    if not all(token in text for token in ('u-bogen', 'oben offen', 'schaft', 'horizontal', 'verlauf')):
        return None
    if any(token in text for token in ('kreis geschlossen', 'dreieck', 'beschrift', 'zusätzlich', 'zwei bögen')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 8 or not np.isfinite(arr).all():
        return None
    pixels = arr.astype(float)
    mask = np.min(arr, axis=2) < 225
    occupied = np.flatnonzero(mask.any(axis=1))
    runs = np.split(occupied, np.flatnonzero(np.diff(occupied) > 1)+1)
    if len(runs) != 2 or any(len(run) < 3 for run in runs):
        return None
    head, shaft = runs
    top, base, start, bottom = head[0], head[-1]+1, shaft[0], shaft[-1]+1
    rows = mask[top:base]
    ys, xs = np.nonzero(rows)
    left, right = xs.min(), xs.max()+1
    cx = (left+right)/2
    # Open upper rows must have two arms separated by white pixels. The
    # lower arc must join them, rather than two bars or an extra object.
    upper = rows[:max(1, len(rows)//3)]
    if not (upper[:, :int(cx)].any() and upper[:, int(cx):].any()):
        return None
    if upper[:, max(0, int(cx)-1):int(cx)+1].any():
        return None
    count, _, stats, _ = cv2.connectedComponentsWithStats(rows.astype(np.uint8))
    if count != 2:
        return None
    lengths = [np.count_nonzero(row[:int(cx)]) for row in upper]
    stroke = float(np.median(lengths))
    rx = (right-left-stroke)/2
    cy = float(top)+.5
    ry = float(base)-cy-stroke/2
    if min(rx, ry, stroke) <= 0 or stroke >= min(rx, ry):
        return None
    columns = np.flatnonzero(mask[start:bottom].mean(axis=0) > .8)
    if len(columns) < 3:
        return None
    sx, ex = int(columns[0]), int(columns[-1])+1
    if not (left < sx < ex < right and abs((sx+ex)/2-cx) < (right-left)*.12):
        return None
    if mask[start:bottom, :sx].sum()+mask[start:bottom, ex:].sum() > max(2, (bottom-start)*.1):
        return None
    profile = np.median(pixels[start:bottom, sx:ex], axis=0)
    if np.percentile(np.max(np.abs(pixels[start:bottom, sx:ex]-profile), axis=2), 95) > 30:
        return None
    middle = len(profile)//2
    side_brightness = max(profile[:middle].mean(axis=1).min(), profile[middle+1:].mean(axis=1).min())
    if profile[middle].mean() < side_brightness+8:
        return None
    core = cv2.erode(rows.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0
    color = np.median(pixels[top:base][core if core.any() else rows], axis=0)
    indices = np.unique(np.rint(np.linspace(0, ex-sx-1, min(9, ex-sx))).astype(int))
    stops = [(float((i+.5)/(ex-sx)), profile[i]) for i in indices]

    def build(p):
        cx, cy, rx, ry, sw, x, y, w, h = p[:9]
        gradient = ''.join(f'<stop offset="{t:g}" stop-color="{_hex(c+p[12:15])}"/>' for t, c in stops)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="shaft_color" x1="0" y1="0" x2="1" y2="0">{gradient}</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<path d="M {cx-rx:g} {cy:g} A {rx:g} {ry:g} 0 0 0 {cx+rx:g} {cy:g}" '
                f'fill="none" stroke="{_hex(p[9:12])}" stroke-width="{sw:g}"/>'
                f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="url(#shaft_color)"/></svg>\n')

    def valid(p):
        cx, cy, rx, ry, sw, x, y, w, h = p[:9]
        return (np.isfinite(p).all() and min(rx, ry, sw, w, h) > 0
                and sw < min(rx, ry) and 0 <= cx-rx-sw/2 < cx+rx+sw/2 <= width
                and -.5 <= cy < cy+ry+sw/2 < y < y+h <= height
                and cx-rx < x < x+w < cx+rx and abs(x+w/2-cx) < rx*.24)

    parameters = [cx, cy, rx, ry, stroke, float(sx), float(start), float(ex-sx), float(bottom-start), *color, 0., 0., 0.]
    loss_fn = None
    if preserve_initial_error:
        reference_edges = cv2.Canny(arr, 50, 140) > 0
        reference_distance = cv2.distanceTransform((~reference_edges).astype(np.uint8), cv2.DIST_L2, 3)
        border = np.concatenate((arr[0], arr[-1], arr[:, 0], arr[:, -1]))
        background = np.median(border.astype(float), axis=0)
        reference_foreground = np.max(np.abs(arr.astype(float)-background), axis=2) > 25

        def loss_fn(original, raster):
            edges = cv2.Canny(raster, 50, 140) > 0
            if edges.any() and reference_edges.any():
                distance = cv2.distanceTransform((~edges).astype(np.uint8), cv2.DIST_L2, 3)
                edge = (np.exp(-distance[reference_edges]).mean()+np.exp(-reference_distance[edges]).mean())/2
            else:
                edge = float(not edges.any() and not reference_edges.any())
            foreground_loss = 0.
            if preserve_foreground:
                foreground = np.max(np.abs(raster.astype(float)-background), axis=2) > 25
                union = (foreground | reference_foreground).sum()
                iou = (foreground & reference_foreground).sum()/union if union else 1.
                foreground_loss = 256*(1-iou)
            return np.mean((original.astype(float)-raster.astype(float))**2)+64*(1-edge)+foreground_loss

    result = _register(parameters, 9, build, valid, arr, render_fn, error_fn, 'raster_arc_shaft_v1',
                       preserve_initial_error=preserve_initial_error, loss_fn=loss_fn)
    if preserve_initial_error and len(profile) >= 7:
        # Boundary pixels blend the shaft with white. Infer a piecewise linear
        # light-centred field from interior columns instead of copying that
        # antialiasing into the native gradient. Keep the sampled-field candidate
        # for profiles that are not explained by this simpler model.
        positions = (np.arange(1, len(profile)-1)+.5)/len(profile)
        models = []
        for center in np.linspace(.3, .7, 41):
            left_weight = np.maximum(0., 1.-positions/center)
            right_weight = np.maximum(0., (positions-center)/(1.-center))
            weights = np.c_[left_weight, 1.-left_weight-right_weight, right_weight]
            colors = np.linalg.lstsq(weights, profile[1:-1], rcond=None)[0]
            residual = float(np.mean((weights@colors-profile[1:-1])**2))
            models.append((residual, center, colors))
        residual, center, colors = min(models, key=lambda item: item[0])
        if residual < 36 and colors[1].mean() > max(colors[0].mean(), colors[2].mean())+8:
            def linear_build(p):
                svg = build(p[:12].tolist()+[0., 0., 0.])
                root = ET.fromstring(svg)
                gradient = next(e for e in root.iter() if e.tag.endswith('linearGradient'))
                gradient.clear()
                gradient.attrib.update(id='shaft_color', x1='0', y1='0', x2='1', y2='0')
                for offset, shade in zip((0., center, 1.), (p[12:15], p[15:18], p[18:21])):
                    ET.SubElement(gradient, '{http://www.w3.org/2000/svg}stop',
                                  offset=f'{offset:g}', **{'stop-color': _hex(shade)})
                return ET.tostring(root, encoding='unicode')+'\n'

            linear = _register(parameters[:12]+colors.reshape(-1).tolist(), 9, linear_build,
                               valid, arr, render_fn, error_fn, 'raster_arc_shaft_v1',
                               preserve_initial_error=True, loss_fn=loss_fn)
            evaluations = (result['evaluations'] if result else 0)+(linear['evaluations'] if linear else 0)
            if linear is not None and (result is None or
                    loss_fn(arr, linear['rendered']) < loss_fn(arr, result['rendered'])):
                result = linear
            if result is not None:
                result['evaluations'] = evaluations
    if result is None:
        return None
    # The fitted analytic arc must explain its input; refinement may not erase
    # a square U, extra marks, or another topology into an approximate circle.
    fitted_mask = np.min(result['rendered'][:start], axis=2) < 225
    union = (fitted_mask | mask[:start]).sum()
    if union == 0 or (fitted_mask & mask[:start]).sum()/union < .7:
        return None
    return result
