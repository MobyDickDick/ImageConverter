"""Explicit, immutable SVG components with raster-based placement.

Component directives are a complete inventory, separate from free-form prose.
Only placement and uniform scale may change; donor geometry and paint survive.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import math
from pathlib import Path
import re
import time
from xml.etree import ElementTree as ET
from src.iCCModules.imageCompositeConverterAdaptiveSearch import tracked_renderer

ROOT = Path(__file__).resolve().parents[2]
NS = 'http://www.w3.org/2000/svg'
NUM = r'(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?'
COORD = r'[+-]?'+NUM
DIRECTIVE = re.compile(
    r'SVG-Bauteil:\s*([\w-]+\.svg)'
    r'(?:\s+bei\s+('+COORD+r')\s+('+COORD+r')\s+skaliert\s+('+NUM+r'))?'
    r'(?:\s+(hinter|vor)\s+([\w-]+\.svg))?\s*', re.I)


def parse_components(description):
    if not re.search(r'\bSVG-Bauteil\b', description, re.I):
        return []
    result = []
    for line in re.split(r'[\n;]', description.strip()):
        if not line.strip():
            continue
        match = DIRECTIVE.fullmatch(line.strip())
        if not match:
            raise ValueError('Bauteilbeschreibung: pro Zeile „SVG-Bauteil: NAME.svg“ '
                             'oder „SVG-Bauteil: NAME.svg bei X Y skaliert FAKTOR“. '
                             'Optional folgt „hinter NAME.svg“ oder „vor NAME.svg“. '
                             'Die Bauteilliste ersetzt den Freitext vollständig.')
        name, *placement, relation, relative_to = match.groups()
        position = tuple(map(float, placement)) if placement[0] is not None else None
        if position and (not all(math.isfinite(v) for v in position) or position[2] <= 0):
            raise ValueError('Bauteilposition und Skalierung müssen endlich und die Skalierung positiv sein.')
        spec = dict(name=name, placement=position)
        if relation:
            spec.update(relation=relation.lower(), relative_to=relative_to)
        result.append(spec)
    if not 1 <= len(result) <= 12:
        raise ValueError('Bitte ein bis zwölf SVG-Bauteile angeben.')
    _ordered_indices(result)  # Reject missing/ambiguous references and cycles before starting.
    return result


def _layer_edges(specs):
    edges = []
    for index, spec in enumerate(specs):
        if not spec.get('relation'):
            continue
        matches = [i for i, other in enumerate(specs)
                   if other['name'].casefold() == spec['relative_to'].casefold()]
        if len(matches) != 1:
            raise ValueError(f'Die Ebenenreferenz „{spec["relative_to"]}“ muss genau einmal in der Bauteilliste stehen.')
        other = matches[0]
        edges.append((index, other) if spec['relation'] == 'hinter' else (other, index))
    return edges


def _ordered_indices(specs):
    edges = _layer_edges(specs)
    remaining, ordered = list(range(len(specs))), []
    while remaining:
        ready = next((i for i in remaining if not any(b == i and a in remaining for a, b in edges)), None)
        if ready is None:
            raise ValueError('Widersprüchliche Ebenenangaben: Bauteile können nicht gegenseitig vor oder hintereinander liegen.')
        ordered.append(ready)
        remaining.remove(ready)
    return ordered


def _allows_order(order, specs):
    positions = {index: layer for layer, index in enumerate(order)}
    return all(positions[a] < positions[b] for a, b in _layer_edges(specs))


def load_component(name, index, root=None):
    from src.imageConverterSample import prepare_sample, NUMBER
    root = ROOT if root is None else root
    # Exact names only: no family substitution, arbitrary files or remote URLs.
    folders = ('artifacts/converted_images/converted_svgs', 'artifacts/samples',
               'artifacts/satisfactory_conversions/svgs')
    path = None
    for folder in folders:
        directory = root / folder
        if directory.is_dir():
            path = next((p for p in directory.iterdir()
                         if p.name.casefold() == name.casefold() and p.is_file()
                         and p.resolve().is_relative_to(directory.resolve())), None)
        if path:
            break
    if path is None:
        raise ValueError(f'Kein gespeichertes SVG-Bauteil „{name}“ gefunden.')
    data = path.read_bytes()
    # Validate before inspecting dimensions (including the byte/nesting limits).
    prepared = ET.fromstring(prepare_sample(data, 1, 1))
    original = ET.fromstring(data.decode('utf-8-sig'))
    view = list(map(float, NUMBER.findall(prepared.get('viewBox'))))
    def dimension(key, fallback):
        match = re.fullmatch('('+NUMBER.pattern+r')(?:px)?', original.get(key, '').strip())
        return float(match[1]) if match else fallback
    width, height = dimension('width', view[2]), dimension('height', view[3])
    if not all(math.isfinite(v) and 0 < v <= 8192 for v in (width, height)):
        raise ValueError(f'Ungültige Bauteilabmessungen: {name}.')
    prepared.set('width', f'{width:g}')
    prepared.set('height', f'{height:g}')
    # Isolate all paint and clipping identifiers before merging documents.
    ids = [n.get('id') for n in prepared.iter() if n.get('id')]
    if len(ids) != len(set(ids)):
        raise ValueError(f'Doppelte SVG-IDs im Bauteil „{name}“.')
    mapping = {value: f'component{index}_{value}' for value in ids}
    for node in prepared.iter():
        # Relative geometry depends on a nested viewport, which the renderer
        # cannot reliably preserve when composing. Paint percentages are safe.
        if node.tag.rsplit('}', 1)[-1] in {'rect', 'circle', 'ellipse', 'line', 'text', 'tspan'}:
            if any('%' in node.get(key, '') for key in
                   ('x', 'y', 'cx', 'cy', 'x1', 'x2', 'y1', 'y2', 'r', 'rx', 'ry', 'width', 'height')):
                raise ValueError(f'Bitte relative Bauteilgeometrie in „{name}“ zuerst in SVG-Einheiten umwandeln.')
        if node.get('id'):
            node.set('id', mapping[node.get('id')])
        for key, value in list(node.attrib.items()):
            if key.rsplit('}', 1)[-1] == 'href' and value.startswith('#'):
                value = '#'+mapping.get(value[1:], value[1:])
            value = re.sub(r'url\(\s*[\"\']?#([^\s)\"\']+)[\"\']?\s*\)',
                           lambda m: 'url(#'+mapping.get(m[1], m[1])+')', value)
            node.set(key, value)
    prepared.set('data-svg-component', name)
    prepared.set('data-svg-component-index', str(index))
    prepared.set('overflow', 'hidden')
    return prepared, width, height, path


def placed_component(component, x, y, scale):
    from src.iCCModules.imageCompositeConverterCanvas import _mapping
    from src.imageConverterSample import NUMBER
    node, width, height, _ = component
    # Express placement independently of the donor's original viewport.
    placed = ET.Element(f'{{{NS}}}g', transform=f'translate({x:.9g} {y:.9g}) scale({scale:.9g})')
    # Flatten the donor viewport explicitly: nested SVGs have inconsistent
    # coordinate/paint handling in MuPDF. Preserve root presentation attributes.
    donor = copy.deepcopy(node)
    view = list(map(float, NUMBER.findall(donor.get('viewBox'))))
    sx, sy, ox, oy = _mapping(donor, width, height, view)
    donor.tag = f'{{{NS}}}g'
    for key in ('width', 'height', 'viewBox', 'preserveAspectRatio', 'overflow', 'version', 'x', 'y'):
        donor.attrib.pop(key, None)
    # Preserve the donor's original clipping boundary as well as its shapes.
    used_ids = {n.get('id') for n in donor.iter()}
    clip_id = 'component'+donor.get('data-svg-component-index')+'_viewport'
    while clip_id in used_ids:
        clip_id += '_'
    definitions = ET.SubElement(placed, f'{{{NS}}}defs')
    clip = ET.SubElement(definitions, f'{{{NS}}}clipPath', id=clip_id, clipPathUnits='userSpaceOnUse')
    ET.SubElement(clip, f'{{{NS}}}rect', width=f'{width:g}', height=f'{height:g}')
    clipped = ET.SubElement(placed, f'{{{NS}}}g', {'clip-path': 'url(#'+clip_id+')'})
    viewport = ET.SubElement(clipped, f'{{{NS}}}g',
        transform=f'translate({ox:.9g} {oy:.9g}) scale({sx:.9g} {sy:.9g})')
    viewport.append(donor)
    return placed


def _canonical(node):
    tag = node.tag.rsplit('}', 1)[-1]
    text = (node.text or '') if tag in {'text', 'tspan', 'style'} else (node.text or '').strip()
    tail = (node.tail or '') if tag == 'tspan' else ''
    return (node.tag, tuple(sorted(node.attrib.items())), text, tail,
            tuple(_canonical(child) for child in node))


def _render_rgba(svg, width, height):
    from PIL import Image
    pixels = _render_rgba_pixels(svg, width, height)
    if pixels is None:
        from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search
        raise ValueError('SVG-Bauteilsuche beendet: '+str(current_search().reason()))
    return Image.fromarray(pixels)


@tracked_renderer
def _render_rgba_pixels(svg, width, height):
    """Retain alpha for measuring the donor's clipped, painted footprint."""
    import io
    import os
    import shutil
    import subprocess
    from PIL import Image
    import numpy as np
    executable = shutil.which('rsvg-convert')
    if not executable and Path('C:/msys64/ucrt64/bin/rsvg-convert.exe').is_file():
        executable = 'C:/msys64/ucrt64/bin/rsvg-convert.exe'
    if not executable:
        raise ValueError('SVG-Bauteile benötigen den vorhandenen SVG-Renderer rsvg-convert.')
    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search
    session = current_search()
    timeout = min(10., max(.001, session.limit-session.elapsed)) if session else 10.
    try:
        result = subprocess.run([executable, '--format', 'png', '--width', str(width),
                                 '--height', str(height), '-'], input=svg.encode('utf-8'),
                                capture_output=True, timeout=timeout, check=True, **options)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError('Das zusammengesetzte SVG konnte nicht gerendert werden.') from exc
    with Image.open(io.BytesIO(result.stdout)) as image:
        return np.asarray(image.convert('RGBA'))


@tracked_renderer
def render_components(svg, width, height):
    """Use the clip/gradient-aware renderer for composed donor viewports."""
    import numpy as np
    from PIL import Image
    rgba = _render_rgba(svg, width, height)
    background = Image.new('RGBA', rgba.size, 'white')
    background.alpha_composite(rgba)
    return np.asarray(background.convert('RGB'))


@lru_cache(maxsize=256)
def _painted_bounds(svg, width, height):
    # Measure alpha, including white paint, with the donor viewport clipped.
    # Empty viewport margins may leave the target; painted content may not.
    zoom = min(4., 4096/max(width, height), math.sqrt(2_000_000/(width*height)))
    w, h = max(1, math.ceil(width*zoom)), max(1, math.ceil(height*zoom))
    box = _render_rgba(svg, w, h).getchannel('A').getbbox()
    if box is None:
        raise ValueError('Ein leeres SVG kann nicht als Bauteil platziert werden.')
    return box[0]*width/w, box[1]*height/h, box[2]*width/w, box[3]*height/h


def component_bounds(component):
    node, width, height, _ = component
    return _painted_bounds(ET.tostring(node, encoding='unicode'), width, height)


@lru_cache(maxsize=32)
def _cached_alpha(svg, width, height):
    import numpy as np
    return np.asarray(_render_rgba(svg, width, height))[:, :, 3] > 64


def component_overlap_quality(reference, output, svg):
    """Check each painted overlap locally, so a small intrusion cannot hide in a large canvas."""
    import numpy as np
    drawing = ET.fromstring(svg)
    height, width = reference.shape[:2]
    masks = []
    for child in drawing:
        wrapper = ET.Element(f'{{{NS}}}svg', width=str(width), height=str(height),
                             viewBox=f'0 0 {width} {height}')
        wrapper.append(child)
        serialized = ET.tostring(wrapper, encoding='unicode')
        if width*height <= 1_000_000:
            masks.append(_cached_alpha(serialized, width, height))
        else:
            masks.append(np.asarray(_render_rgba(serialized, width, height))[:, :, 3] > 64)
    error = np.square(reference.astype(np.float32)-output.astype(np.float32)).mean(axis=2)/255**2
    regions = []
    for front in range(len(masks)):
        for back in range(front):
            overlap = masks[front] & masks[back]
            count = int(np.count_nonzero(overlap))
            if count:
                regions.append(dict(back=back, front=front, pixels=count,
                                    normalized_mse=float(error[overlap].mean())))
    worst = max((region['normalized_mse'] for region in regions), default=0.)
    return dict(overlap_regions=regions, overlap_mse=worst, overlap_passed=worst <= .01)


def validate_components(svg, description, root=None):
    from src.imageConverterSample import prepare_sample
    # Apply the same total byte/element/depth limits as ordinary SVG inputs.
    prepare_sample(svg.encode('utf-8'), 1, 1)
    specs = parse_components(description)
    drawing = ET.fromstring(svg)
    if drawing.tag != f'{{{NS}}}svg' or len(drawing) != len(specs):
        raise ValueError('Die SVG-Bauteilliste ist unvollständig oder enthält zusätzliche Elemente.')
    allowed = {'width', 'height', 'viewBox', 'overflow'}
    if set(drawing.attrib)-allowed or drawing.get('overflow') != 'hidden':
        raise ValueError('Unerwartete Änderung der Bauteil-Zeichenfläche.')
    width, height = float(drawing.get('width', '0')), float(drawing.get('height', '0'))
    if not all(math.isfinite(v) and v > 0 for v in (width, height)):
        raise ValueError('Ungültige Bauteil-Zeichenfläche.')
    if drawing.get('viewBox') != f'0 0 {width:g} {height:g}':
        raise ValueError('Unerwartete Änderung des Bauteil-Koordinatensystems.')
    order = []
    for actual in drawing:
        markers = [node.get('data-svg-component-index') for node in actual.iter()
                   if node.get('data-svg-component')]
        if len(markers) != 1 or not re.fullmatch(r'\d+', markers[0] or ''):
            raise ValueError('Ungültige Bauteilinstanz.')
        index = int(markers[0])
        if index >= len(specs) or index in order:
            raise ValueError('Die SVG-Bauteilliste enthält fehlende oder doppelte Instanzen.')
        order.append(index)
        spec = specs[index]
        component = load_component(spec['name'], index, root)
        _, cw, ch, _ = component
        matrix = re.fullmatch(r'translate\(('+COORD+r') ('+COORD+r')\) scale\(('+NUM+r')\)',
                              actual.get('transform', ''))
        if not matrix:
            raise ValueError('Ungültige Bauteiltransformation.')
        x, y, scale = map(float, matrix.groups())
        w, h = cw*scale, ch*scale
        bx0, by0, bx1, by1 = component_bounds(component)
        if (not all(math.isfinite(v) for v in (x, y, w, h)) or scale <= 0
                or x+bx0*scale < -1e-6 or y+by0*scale < -1e-6
                or x+bx1*scale > width+1e-6 or y+by1*scale > height+1e-6):
            raise ValueError('Bauteile müssen unverzerrt innerhalb der Zeichenfläche liegen.')
        if spec['placement'] and any(not math.isclose(a, b, abs_tol=1e-6)
                                     for a, b in zip((x, y, scale), spec['placement'])):
            raise ValueError('Die vorgegebene Bauteilposition wurde verändert.')
        expected = placed_component(component, x, y, scale)
        if _canonical(actual) != _canonical(expected):
            raise ValueError(f'Das SVG-Bauteil „{spec["name"]}“ wurde verändert oder ersetzt.')
    if not _allows_order(order, specs):
        raise ValueError('Die vorgegebene Reihenfolge „vor/hinter“ der SVG-Bauteile wurde verletzt.')


def locate_component(component, target, deadline):
    """Bounded multiscale template matching; no raster geometry is generated."""
    import cv2
    import numpy as np
    th, tw = target.shape[:2]
    bx0, by0, bx1, by1 = component_bounds(component)
    bw, bh = bx1-bx0, by1-by0
    max_scale = min(tw/bw, th/bh)
    if max_scale <= 0:
        raise ValueError('Das SVG-Bauteil passt nicht auf die Zeichenfläche.')
    target = target.astype(np.float32)
    target_edges = (cv2.Canny(cv2.cvtColor(target.astype(np.uint8), cv2.COLOR_RGB2GRAY),
                             20, 60) > 0).astype(np.float32)
    target_near_edges = cv2.dilate(target_edges, np.ones((3, 3), np.uint8))
    best = None
    evaluations = 0
    seen = set()

    def measure(scale):
        nonlocal best, evaluations
        w, h = max(2, math.ceil(bw*scale-1e-9)), max(2, math.ceil(bh*scale-1e-9))
        key = round(scale, 9)
        if (key in seen or min(w, h) < 12 or w > tw or h > th
                or time.monotonic() >= deadline):
            return
        seen.add(key)
        template = ET.Element(f'{{{NS}}}svg', width=str(w), height=str(h),
                              viewBox=f'0 0 {w} {h}')
        template.append(placed_component(component, -bx0*scale, -by0*scale, scale))
        pixels = render_components(ET.tostring(template, encoding='unicode'), w, h).astype(np.float32)
        # Include the neighbourhood of painted pixels, avoiding empty canvas
        # dominating placement while preserving interior/edge mismatches.
        foreground = (np.max(abs(pixels-255), axis=2) > 18).astype(np.uint8)
        if not foreground.any():
            raise ValueError('Ein leeres SVG kann nicht als Bauteil platziert werden.')
        mask = cv2.dilate(foreground, np.ones((3, 3), np.uint8)).astype(np.float32)
        error = cv2.matchTemplate(target, pixels, cv2.TM_SQDIFF, mask=mask)
        error = np.maximum(error, 0)/(max(1., float(mask.sum()))*3*255**2)
        # Colour alone can match a miniature M to an unrelated grey cap.
        # Compare both edge recall and precision across the whole viewport.
        edges = (cv2.Canny(cv2.cvtColor(pixels.astype(np.uint8), cv2.COLOR_RGB2GRAY),
                          20, 60) > 0).astype(np.float32)
        if edges.any():
            near_edges = cv2.dilate(edges, np.ones((3, 3), np.uint8))
            recall = cv2.matchTemplate(target_near_edges, edges, cv2.TM_CCORR)/edges.sum()
            hits = cv2.matchTemplate(target_edges, near_edges, cv2.TM_CCORR)
            count = cv2.matchTemplate(target_edges, np.ones((h, w), np.float32), cv2.TM_CCORR)
            precision = hits/np.maximum(count, 1)
            edge_error = 1-.5*np.clip(recall, 0, 1)-.5*np.clip(precision, 0, 1)
            error += .15*np.minimum(1, error/.01)*edge_error
        error = np.nan_to_num(error, nan=np.inf, posinf=np.inf, neginf=np.inf)
        minimum, _, (x, y), _ = cv2.minMaxLoc(error)
        score = minimum
        evaluations += 1
        candidate = (score, x-bx0*scale, y-by0*scale, scale)
        if best is None or candidate[0] < best[0]:
            best = candidate

    scales = sorted(set([min(1., max_scale), max_scale, *np.geomspace(
        max(.1, max_scale/24), max_scale, 48)]), key=lambda s: abs(math.log(max(s, 1e-9))))
    for scale in scales:
        measure(scale)
        if best is not None and best[0] < 1e-8:
            break
    if best is not None and best[0] >= 1e-8:
        for scale in np.linspace(best[3]*.94, min(max_scale, best[3]*1.06), 25):
            measure(scale)
    if best is None:
        raise ValueError('Zeitlimit vor der Bauteilplatzierung erreicht.')
    return best[1:], evaluations


def compose_components(description, target, *, seconds=30., root=None):
    from src.iCCModules.imageCompositeConverterSearchPortfolio import standalone_image_search
    with standalone_image_search('svg_components', seconds=seconds) as session:
        session.bind_reference(target)
        return _compose_components(description, target, seconds=seconds, root=root)


def _compose_components(description, target, *, seconds=30., root=None):
    import hashlib
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import vector_candidate_quality, vector_quality_score
    root = ROOT if root is None else root
    specs = parse_components(description)
    if not specs:
        raise ValueError('Keine SVG-Bauteilverweise angegeben.')
    height, width = target.shape[:2]
    assembly = ET.Element(f'{{{NS}}}svg', width=str(width), height=str(height),
                          viewBox=f'0 0 {width} {height}', overflow='hidden')
    deadline = time.monotonic()+seconds
    placement_deadline = time.monotonic()+seconds*.65
    references, evaluations = [], 0
    components = []
    for index, spec in enumerate(specs):
        component = load_component(spec['name'], index, root)
        components.append(component)
        placement = spec['placement']
        if placement is None:
            share = time.monotonic()+max(0., placement_deadline-time.monotonic())/(len(specs)-index)
            placement, count = locate_component(component, target, share)
            evaluations += count
        assembly.append(placed_component(component, *placement))
        references.append(dict(name=spec['name'], source=str(component[3].relative_to(root)),
                               sha256=hashlib.sha256(component[3].read_bytes()).hexdigest(),
                               placement=list(placement), automatic=spec['placement'] is None))
    ET.register_namespace('', NS)
    layer_order = _ordered_indices(specs)

    def rebuild():
        assembly[:] = [placed_component(components[i], *references[i]['placement']) for i in layer_order]

    rebuild()
    # Template matching locates each donor independently. Refine subpixel
    # placement against the actual layered assembly and the final pixel gates.
    def rank():
        nonlocal evaluations
        svg = ET.tostring(assembly, encoding='unicode')
        quality = vector_candidate_quality(target, render_components(svg, width, height), svg)
        evaluations += 1
        return not quality['passed'], vector_quality_score(quality)+quality['overlap_mse']

    if time.monotonic() < deadline:
        best = rank()
        # Compare permitted layer orders before accepting even a globally passing fit.
        # Donor geometry and explicit placement remain unchanged.
        for sweep in range(len(specs)):
            changed = False
            for first in range(len(specs)):
                for second in range(first+1, len(specs)):
                    if time.monotonic() >= deadline:
                        break
                    trial = list(layer_order)
                    trial[first], trial[second] = trial[second], trial[first]
                    if not _allows_order(trial, specs):
                        continue
                    previous = layer_order
                    layer_order = trial
                    rebuild()
                    score = rank()
                    if score < best:
                        best, changed = score, True
                    else:
                        layer_order = previous
                        rebuild()
            if not changed or time.monotonic() >= deadline:
                break
        for fraction in (1., .5, .25):
            if not best[0]:
                break
            for sweep in range(6):
                changed = False
                for index, (component, ref) in enumerate(zip(components, references)):
                    if not ref['automatic']:
                        continue
                    bx0, by0, bx1, by1 = component_bounds(component)
                    steps = (.5*fraction, .5*fraction, .5*fraction/max(bx1-bx0, by1-by0))
                    for axis, step in enumerate(steps):
                        for sign in (-1, 1):
                            if time.monotonic() >= deadline or not best[0]:
                                break
                            trial = list(ref['placement'])
                            trial[axis] += sign*step
                            x, y, scale = trial
                            if (scale <= 0 or x+bx0*scale < 0 or y+by0*scale < 0
                                    or x+bx1*scale > width or y+by1*scale > height):
                                continue
                            layer = layer_order.index(index)
                            assembly[layer] = placed_component(component, *trial)
                            score = rank()
                            if score < best:
                                ref['placement'], best, changed = trial, score, True
                            else:
                                assembly[layer] = placed_component(component, *ref['placement'])
                if not changed or not best[0] or time.monotonic() >= deadline:
                    break
    svg = ET.tostring(assembly, encoding='unicode')
    for index, ref in enumerate(references):
        ref['layer'] = layer_order.index(index)
    validate_components(svg, description, root)
    return svg, references, evaluations
