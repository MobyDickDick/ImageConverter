"""Explicit, immutable SVG components with raster-based placement.

Component directives are a complete inventory, separate from free-form prose.
Only placement and uniform scale may change; donor geometry and paint survive.
"""
from __future__ import annotations

import copy
import math
from pathlib import Path
import re
import time
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
NS = 'http://www.w3.org/2000/svg'
NUM = r'(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?'
DIRECTIVE = re.compile(
    r'SVG-Bauteil:\s*([\w-]+\.svg)'
    r'(?:\s+bei\s+('+NUM+r')\s+('+NUM+r')\s+skaliert\s+('+NUM+r'))?\s*', re.I)


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
                             'Die Bauteilliste ersetzt den Freitext vollständig.')
        name, *placement = match.groups()
        position = tuple(map(float, placement)) if placement[0] is not None else None
        if position and (not all(math.isfinite(v) for v in position) or position[2] <= 0):
            raise ValueError('Bauteilposition und Skalierung müssen endlich und die Skalierung positiv sein.')
        result.append(dict(name=name, placement=position))
    if not 1 <= len(result) <= 12:
        raise ValueError('Bitte ein bis zwölf SVG-Bauteile angeben.')
    return result


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


def render_components(svg, width, height):
    """Use the clip/gradient-aware renderer for composed donor viewports."""
    import io
    import os
    import shutil
    import subprocess
    import numpy as np
    from PIL import Image
    executable = shutil.which('rsvg-convert')
    if not executable and Path('C:/msys64/ucrt64/bin/rsvg-convert.exe').is_file():
        executable = 'C:/msys64/ucrt64/bin/rsvg-convert.exe'
    if not executable:
        raise ValueError('SVG-Bauteile benötigen den vorhandenen SVG-Renderer rsvg-convert.')
    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    try:
        result = subprocess.run([executable, '--format', 'png', '--width', str(width),
                                 '--height', str(height), '-'], input=svg.encode('utf-8'),
                                capture_output=True, timeout=10, check=True, **options)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError('Das zusammengesetzte SVG konnte nicht gerendert werden.') from exc
    with Image.open(io.BytesIO(result.stdout)) as image:
        rgba = image.convert('RGBA')
        background = Image.new('RGBA', rgba.size, 'white')
        background.alpha_composite(rgba)
        return np.asarray(background.convert('RGB'))


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
    for index, (spec, actual) in enumerate(zip(specs, drawing)):
        component = load_component(spec['name'], index, root)
        _, cw, ch, _ = component
        matrix = re.fullmatch(r'translate\(('+NUM+r') ('+NUM+r')\) scale\(('+NUM+r')\)',
                              actual.get('transform', ''))
        if not matrix:
            raise ValueError('Ungültige Bauteiltransformation.')
        x, y, scale = map(float, matrix.groups())
        w, h = cw*scale, ch*scale
        if (not all(math.isfinite(v) for v in (x, y, w, h)) or scale <= 0
                or min(x, y) < 0 or x+w > width+1e-6 or y+h > height+1e-6):
            raise ValueError('Bauteile müssen unverzerrt innerhalb der Zeichenfläche liegen.')
        if spec['placement'] and any(not math.isclose(a, b, abs_tol=1e-6)
                                     for a, b in zip((x, y, scale), spec['placement'])):
            raise ValueError('Die vorgegebene Bauteilposition wurde verändert.')
        expected = placed_component(component, x, y, scale)
        if _canonical(actual) != _canonical(expected):
            raise ValueError(f'Das SVG-Bauteil „{spec["name"]}“ wurde verändert oder ersetzt.')


def locate_component(component, target, deadline):
    """Bounded multiscale template matching; no raster geometry is generated."""
    import cv2
    import numpy as np
    from src.imageConverterSample import render_svg
    node, width, height, _ = component
    th, tw = target.shape[:2]
    max_scale = min(tw/width, th/height)
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
        w, h = max(2, round(width*scale)), max(2, round(height*scale))
        if ((w, h) in seen or min(w, h) < 12 or w > tw or h > th
                or time.monotonic() >= deadline):
            return
        seen.add((w, h))
        template = copy.deepcopy(node)
        template.set('width', str(w))
        template.set('height', str(h))
        pixels = render_svg(ET.tostring(template, encoding='unicode'), w, h).astype(np.float32)
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
        candidate = (score, x, y, min(w/width, h/height))
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
    import hashlib
    root = ROOT if root is None else root
    specs = parse_components(description)
    if not specs:
        raise ValueError('Keine SVG-Bauteilverweise angegeben.')
    height, width = target.shape[:2]
    assembly = ET.Element(f'{{{NS}}}svg', width=str(width), height=str(height),
                          viewBox=f'0 0 {width} {height}', overflow='hidden')
    deadline = time.monotonic()+seconds
    references, evaluations = [], 0
    for index, spec in enumerate(specs):
        component = load_component(spec['name'], index, root)
        placement = spec['placement']
        if placement is None:
            share = time.monotonic()+max(0., deadline-time.monotonic())/(len(specs)-index)
            placement, count = locate_component(component, target, share)
            evaluations += count
        assembly.append(placed_component(component, *placement))
        references.append(dict(name=spec['name'], source=str(component[3].relative_to(root)),
                               sha256=hashlib.sha256(component[3].read_bytes()).hexdigest(),
                               placement=list(placement), automatic=spec['placement'] is None))
    ET.register_namespace('', NS)
    svg = ET.tostring(assembly, encoding='unicode')
    validate_components(svg, description, root)
    return svg, references, evaluations
