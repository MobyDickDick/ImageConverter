"""Continue generated vectors with bounded native structure and parameter probes."""
from __future__ import annotations

import copy
import os
import xml.etree.ElementTree as ET

import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality, preferred_quality


def polish_generated_svg(svg, image, render_fn, *, assertions=None, structure_mode=None, color_order='BGR'):
    structure_mode = structure_mode or os.environ.get('ICC_FALLBACK_STRUCTURE_MODE', 'combined')
    if structure_mode not in {'off', 'primitives', 'lines', 'combined', 'legacy_combined', 'groups'}:
        raise ValueError('Unknown fallback structure mode')
    if color_order not in {'BGR', 'RGB'}:
        raise ValueError('Unknown raster color order')
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
    if initial is None:
        return None
    original_svg, original_raster = svg, initial
    original_error = float(np.square(image.astype(float)-initial.astype(float)).mean()/255**2)
    structure = None
    # Even a tiny globally cheap missing line needs exploration. Exact/near-exact
    # incumbents retain their bytes and the established inexpensive early exit.
    if preferred_quality(pixel_quality(image, initial)) and (structure_mode == 'off' or np.max(abs(image.astype(float)-initial)) < 35):
        return None
    if structure_mode != 'off':
        from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
        structure_image = image if color_order == 'BGR' else image[:, :, ::-1].copy()
        structure_initial = initial if color_order == 'BGR' else initial[:, :, ::-1].copy()
        def render_structure(candidate, width, height):
            raster = render_fn(candidate, width, height)
            return raster if raster is None or color_order == 'BGR' else raster[:, :, ::-1].copy()
        selected, structure = explore_structures(svg, structure_image, structure_initial, render_structure, session, assertions,
                                                 mode=structure_mode)
        svg, initial = selected['svg'], selected['rendered']
        if color_order == 'RGB':
            initial = initial[:, :, ::-1].copy()
        root = ET.fromstring(prepare_sample(svg.encode('utf-8'), w, h))
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
        if structure is None:
            return None
        result = dict(svg=svg, rendered=initial, error=error(initial), evaluations=0,
                      source='native_svg_continuation', search_control=dict(
                          stop_reason=session.time_reason() or 'schedule_exhausted', **session.report()))
    # Recheck explicit assertions on the selected draft too, including timeouts.
    validate_svg_assertions(result['svg'], assertions)
    # Parameter polish must not erase a small newly added feature to improve a
    # much larger background. Preserve the already measured structural draft.
    if structure and structure['selected_origin'] != 'incumbent':
        from src.iCCModules.imageCompositeConverterFallbackComposition import retained_paint
        if not retained_paint(image, initial, result['rendered']):
            result.update(svg=svg, rendered=initial, error=error(initial))
            structure['refinement_reverted_for_local_detail'] = True
        from src.iCCModules.imageCompositeConverterFallbackGroups import part_regions, check_parts
        regions = part_regions(svg, w, h)
        if regions:
            # Atomic groups protect every part, including heads and joints,
            # rather than only the long line elements.
            before_parts = check_parts(image, initial, regions)
            after_parts = check_parts(image, result['rendered'], regions)
            if any((a['passed'] and not b['passed']) or b['normalized_mse'] > a['normalized_mse']+1/255**2
                   for a, b in zip(before_parts, after_parts)):
                result.update(svg=svg, rendered=initial, error=error(initial))
                structure['refinement_reverted_for_local_detail'] = True
        for node in ET.fromstring(svg).iter():
            if node.tag.rsplit('}', 1)[-1] != 'line':
                continue
            xs = [float(node.get('x1', '0')), float(node.get('x2', '0'))]
            ys = [float(node.get('y1', '0')), float(node.get('y2', '0'))]
            x, X = max(0, int(min(xs))-3), min(w, int(max(xs))+4)
            y, Y = max(0, int(min(ys))-3), min(h, int(max(ys))+4)
            if X <= x or Y <= y:
                continue
            before = np.square(image[y:Y, x:X].astype(float)-initial[y:Y, x:X]).mean()
            after = np.square(image[y:Y, x:X].astype(float)-result['rendered'][y:Y, x:X]).mean()
            if after > before+1:
                result.update(svg=svg, rendered=initial, error=error(initial))
                structure['refinement_reverted_for_local_detail'] = True
                break
    result['initial_error'] = original_error
    if structure is not None:
        result['structure_search'] = structure
        result['evaluations'] += structure['render_evaluations']
    improved = result['error'] < original_error-1e-10
    result['improved'] = improved
    if not improved:
        result.update(svg=original_svg, rendered=original_raster, error=original_error)
    return result
