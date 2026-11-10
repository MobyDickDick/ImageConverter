"""Continue fast legacy fits using their own native vector, never a reference SVG.

The assembly stays intact: uniform placement, shared stroke widths/paint and
ordered gradient stops are fitted together. No contour tracing or new objects.
"""
from __future__ import annotations

import copy
import xml.etree.ElementTree as ET

import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality, preferred_quality


def polish_generated_svg(svg, image, render_fn, *, assertions=None):
    session = current_search()
    if session is None or not session.minimum_pending or session.time_reason():
        return None
    from src.imageConverterSample import prepare_sample, NUMBER, SVG_NS
    from src.iCCModules.imageCompositeConverterFilledSymbols import _register
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions
    from PIL import ImageColor

    h, w = image.shape[:2]
    # Unsupported/embedded content is left to its existing failure handling.
    try:
        root = ET.fromstring(prepare_sample(svg.encode('utf-8'), w, h))
        validate_svg_assertions(svg, assertions)
    except (ValueError, SyntaxError):
        return None
    initial = render_fn(svg, w, h)
    if initial is None or preferred_quality(pixel_quality(image, initial)):
        return None
    nodes = list(root.iter())
    widths, colors, gradients = {}, {}, []
    for index, node in enumerate(nodes):
        stroke = node.get('stroke-width', '')
        if stroke and NUMBER.fullmatch(stroke) and float(stroke) > 0:
            widths.setdefault(float(stroke), []).append(index)
        for attr in ('fill', 'stroke', 'stop-color'):
            try:
                color = ImageColor.getrgb(node.get(attr, ''))
            except ValueError:
                continue
            if len(color) == 3 and min(color) < 250:
                colors.setdefault(tuple(color), []).append((index, attr))
        if node.tag.rsplit('}', 1)[-1] in {'linearGradient', 'radialGradient'}:
            stops = []
            for child in node:
                if child.tag.rsplit('}', 1)[-1] == 'stop':
                    raw = child.get('offset', '0')
                    stops.append((nodes.index(child), float(raw.rstrip('%')) * (1 if raw.endswith('%') else 100)))
            if stops:
                gradients.append(stops)
    width_groups, color_groups = list(widths.items()), list(colors.items())
    stops = [stop for gradient in gradients for stop in gradient]
    geometry = 3 + len(width_groups) + len(stops)
    seed = np.array([0., 0., 100.] + [value for value, _ in width_groups]
                    + [value for _, value in stops] + [v for color, _ in color_groups for v in color], dtype=float)
    view = list(map(float, NUMBER.findall(root.get('viewBox'))))
    cx, cy = view[0]+view[2]/2, view[1]+view[3]/2

    def valid(p):
        if (not np.isfinite(p).all() or abs(p[0]) > view[2]*.25 or abs(p[1]) > view[3]*.25
                or not 75 <= p[2] <= 125 or np.any(p[geometry:] < 0) or np.any(p[geometry:] > 255)):
            return False
        for i, (value, _) in enumerate(width_groups):
            if not value*.5 <= p[3+i] <= value*2:
                return False
        offset = 3+len(width_groups)
        for gradient in gradients:
            values = p[offset:offset+len(gradient)]
            if np.any(values < 0) or np.any(values > 100) or np.any(np.diff(values) < 0):
                return False
            offset += len(gradient)
        return True

    def build(p):
        candidate = copy.deepcopy(root)
        elements = list(candidate.iter())
        for i, (_, indexes) in enumerate(width_groups):
            for index in indexes:
                elements[index].set('stroke-width', f'{p[3+i]:.6f}')
        for i, (index, _) in enumerate(stops):
            elements[index].set('offset', f'{p[3+len(width_groups)+i]:.6f}%')
        for i, (_, assignments) in enumerate(color_groups):
            color = '#%02x%02x%02x' % tuple(np.round(p[geometry+3*i:geometry+3*i+3]).astype(int))
            for index, attr in assignments:
                elements[index].set(attr, color)
        scale = p[2]/100
        wrapper = ET.Element(f'{{{SVG_NS}}}g', transform=(
            f'translate({p[0]+cx*(1-scale):.6f} {p[1]+cy*(1-scale):.6f}) scale({scale:.6f})'))
        for child in list(candidate):
            if child.tag.rsplit('}', 1)[-1] not in {'defs', 'style', 'title', 'desc', 'metadata'}:
                candidate.remove(child)
                wrapper.append(child)
        candidate.append(wrapper)
        return ET.tostring(candidate, encoding='unicode')

    reference = image.astype(np.float32)
    border = np.concatenate((reference[0], reference[-1], reference[:, 0], reference[:, -1]))
    weights = 1 + 4*(np.max(abs(reference-np.median(border, axis=0)), axis=2) > 25)
    error = lambda pixels: float(np.square(reference-pixels.astype(np.float32)).mean()/255**2)
    loss = lambda pixels: float((np.square(reference-pixels.astype(np.float32)).mean(axis=2)*weights).mean()/255**2)

    def satisfactory(p, measured):
        try:
            validate_svg_assertions(measured[2], assertions)
            return True
        except ValueError:
            return False

    result = _register(seed, geometry, build, valid, image, render_fn, lambda a, b: error(b),
                       'native_svg_continuation', loss_fn=lambda a, b: loss(b), satisfactory_fn=satisfactory,
                       preserve_initial_error=True)
    if result is None:
        return None
    # Recheck explicit assertions on the selected draft too, including timeouts.
    validate_svg_assertions(result['svg'], assertions)
    improved = result['error'] < error(initial)-1e-10
    result['improved'] = improved
    if not improved:
        result.update(svg=svg, rendered=initial, error=error(initial))
    return result
