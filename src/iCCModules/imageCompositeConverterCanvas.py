"""Keep painted SVG content, including strokes, inside the source canvas.

Measure on an expanded transparent viewport, before the final viewport clips.
Fit the entire assembly uniformly; never add, remove or reconstruct objects.
"""
from __future__ import annotations

from functools import lru_cache
import math
import io
import os
from pathlib import Path
import re
import shutil
import subprocess
from xml.etree import ElementTree as ET

NS = 'http://www.w3.org/2000/svg'
NUMBER = r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?'
NON_DRAWING = {'defs', 'style', 'title', 'desc', 'metadata'}


def _style(root, **values):
    retained = [part for part in root.get('style', '').split(';') if part.strip()
                and part.split(':', 1)[0].strip().lower() not in values]
    retained.extend(f'{key}:{value} !important' for key, value in values.items())
    root.set('style', ';'.join(retained))


def _dimensions(root, width, height):
    def length(key):
        match = re.fullmatch(r'('+NUMBER+r')(?:px)?', root.get(key, '').strip())
        return float(match[1]) if match else None
    view = list(map(float, re.findall(NUMBER, root.get('viewBox', ''))))
    original_width, original_height = length('width'), length('height')
    width = float(width) if width is not None else original_width
    height = float(height) if height is not None else original_height
    if width is None or height is None:
        if len(view) != 4:
            raise ValueError('SVG canvas dimensions are missing')
        width, height = view[2:]
    if not all(math.isfinite(v) and v > 0 for v in (width, height)):
        raise ValueError('SVG canvas dimensions are invalid')
    if len(view) != 4:
        view = [0., 0., original_width or width, original_height or height]
    if not all(math.isfinite(v) for v in view) or min(view[2:]) <= 0:
        raise ValueError('SVG viewBox is invalid')
    return width, height, view


def _mapping(root, width, height, view):
    x, y, w, h = view
    sx, sy = width/w, height/h
    aspect = root.get('preserveAspectRatio', 'xMidYMid meet').split()
    if aspect and aspect[0] == 'defer':
        aspect = aspect[1:]
    fx = fy = 0.
    if not aspect or aspect[0] != 'none':
        sx = sy = max(sx, sy) if 'slice' in aspect else min(sx, sy)
        alignment = aspect[0] if aspect else 'xMidYMid'
        fx = 0. if 'xMin' in alignment else 1. if 'xMax' in alignment else .5
        fy = 0. if 'YMin' in alignment else 1. if 'YMax' in alignment else .5
    return sx, sy, -x*sx+(width-w*sx)*fx, -y*sy+(height-h*sy)*fy


def _measure(root, width, height):
    import fitz
    import numpy as np
    from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles

    measured = ET.fromstring(inline_simple_svg_styles(ET.tostring(root, encoding='unicode')))
    _, _, view = _dimensions(measured, width, height)
    sx, sy, ox, oy = _mapping(measured, width, height, view)
    # MuPDF treats "slice" like "meet". Express the viewport map explicitly
    # for measurement, retaining the original viewBox for percentages/paints.
    mw, mh = sx*view[2], sy*view[3]
    measured.set('width', f'{mw:.12g}')
    measured.set('height', f'{mh:.12g}')
    measured.set('x', f'{ox+sx*view[0]:.12g}')
    measured.set('y', f'{oy+sy*view[1]:.12g}')
    measured.set('preserveAspectRatio', 'none')
    measured.set('overflow', 'visible')
    _style(measured, overflow='visible', width=f'{mw:.12g}px', height=f'{mh:.12g}px')
    viewport = ET.Element(f'{{{NS}}}svg', width=str(width), height=str(height),
                          viewBox=f'0 0 {width} {height}', overflow='visible')
    _style(viewport, overflow='visible', width=f'{width:g}px', height=f'{height:g}px')
    viewport.append(measured)
    # PDF display-list bounds are used only to reserve sufficient space. Their
    # stroke bounds are deliberately conservative; actual ink is measured below.
    extent = [0., 0., width, height]
    with fitz.open('svg', ET.tostring(viewport)) as doc:
        with fitz.open('pdf', doc.convert_to_pdf()) as pdf:
            for kind, box, *_ in pdf[0].get_bboxlog():
                if kind == 'ignore-text' or not all(math.isfinite(v) for v in box):
                    continue
                extent = [min(extent[0], box[0]), min(extent[1], box[1]),
                          max(extent[2], box[2]), max(extent[3], box[3])]
    x0, y0 = math.floor(extent[0])-3, math.floor(extent[1])-3
    x1, y1 = math.ceil(extent[2])+3, math.ceil(extent[3])+3
    w, h = x1-x0, y1-y0
    wrapper = ET.Element(f'{{{NS}}}svg', width=str(w), height=str(h),
                         viewBox=f'{x0} {y0} {w} {h}')
    wrapper.append(viewport)
    # Bound memory for large inputs; tiny symbols are measured at 4x resolution.
    zoom = min(4., 4096/max(w, h), math.sqrt(2_000_000/(w*h)))
    with fitz.open('svg', ET.tostring(wrapper)) as doc:
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
    rgba = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 4)
    yy, xx = np.nonzero(rgba[:, :, 3])
    if not len(xx):
        return None
    bounds = (x0+float(xx.min())/zoom, y0+float(yy.min())/zoom,
              x0+float(xx.max()+1)/zoom, y0+float(yy.max()+1)/zoom)
    # MuPDF does not implement every SVG clip/mask. Do not shrink deliberately
    # clipped linework based on its invisible extensions. Use the independent
    # SVG renderer only for this exceptional case, rather than every candidate.
    if (bounds[0] < 0 or bounds[1] < 0 or bounds[2] > width or bounds[3] > height) and any(
            node.get('clip-path') or node.get('mask') for node in measured.iter()):
        executable = shutil.which('rsvg-convert')
        if not executable and Path('C:/msys64/ucrt64/bin/rsvg-convert.exe').is_file():
            executable = 'C:/msys64/ucrt64/bin/rsvg-convert.exe'
        if not executable:
            raise RuntimeError('Clipped SVG bounds require an SVG clip-aware renderer')
        from PIL import Image
        pw, ph = max(1, math.ceil(w*zoom)), max(1, math.ceil(h*zoom))
        wrapper.set('preserveAspectRatio', 'none')
        try:
            options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
            result = subprocess.run([executable, '--format', 'png', '--width', str(pw), '--height', str(ph), '-'],
                input=ET.tostring(wrapper), capture_output=True, timeout=10, check=True, **options)
            with Image.open(io.BytesIO(result.stdout)) as image:
                alpha = np.asarray(image.convert('RGBA'))[:, :, 3]
            yy, xx = np.nonzero(alpha)
            if not len(xx):
                return None
            return (x0+float(xx.min())*w/pw, y0+float(yy.min())*h/ph,
                    x0+float(xx.max()+1)*w/pw, y0+float(yy.max()+1)*h/ph)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            raise RuntimeError('Clipped SVG bounds could not be measured') from exc
    return bounds


@lru_cache(maxsize=256)
def painted_bounds(svg, width=None, height=None):
    """Return pre-viewport painted bounds in source pixels, including antialiasing."""
    root = ET.fromstring(svg)
    width, height, _ = _dimensions(root, width, height)
    return _measure(root, width, height)


def within_canvas(svg, width=None, height=None):
    root = ET.fromstring(svg)
    width, height, _ = _dimensions(root, width, height)
    try:
        bounds = painted_bounds(svg, width, height)
    except RuntimeError:
        return (root.get('overflow') == 'hidden'
                and not re.search(r'overflow\s*:\s*visible', root.get('style', ''), re.I))
    return bounds is None or (bounds[0] >= -1e-7 and bounds[1] >= -1e-7
                              and bounds[2] <= width+1e-7 and bounds[3] <= height+1e-7)


@lru_cache(maxsize=256)
def contain_svg(svg, width=None, height=None):
    """Preserve the canvas, fitting overflowing paint by translation/uniform scale."""
    root = ET.fromstring(svg)
    if (width is None and height is None and not list(root)
            and not root.get('width') and not root.get('height') and not root.get('viewBox')):
        return svg  # legacy empty diagnostics have no paint that could escape
    width, height, view = _dimensions(root, width, height)
    same_size = root.get('width') == f'{width:g}' and root.get('height') == f'{height:g}'
    try:
        bounds = painted_bounds(svg, width, height)
    except (ValueError, RuntimeError):
        # Unsupported renderer features must not reintroduce a startup failure.
        # The final SVG viewport still enforces the visible boundary.
        bounds = None
        same_size = False
    inside = bounds is None or (bounds[0] >= 0 and bounds[1] >= 0
                               and bounds[2] <= width and bounds[3] <= height)
    overflow_css = 'overflow' in root.get('style', '').lower() or any(
        node.tag.rsplit('}', 1)[-1] == 'style' and 'overflow' in (node.text or '').lower() for node in root.iter())
    if inside and same_size and root.get('overflow') == 'hidden' and not overflow_css:
        return svg
    root.set('width', f'{width:g}')
    root.set('height', f'{height:g}')
    if not root.get('viewBox') and (not inside or not same_size):
        root.set('viewBox', ' '.join(f'{v:g}' for v in view))
    if not inside:
        x0, y0, x1, y1 = bounds
        scale = min(1., width/(x1-x0), height/(y1-y0))
        # A tiny inset absorbs serialized transform rounding, not an added border.
        inset = min(width, height)*1e-7
        scale = min(scale, (width-2*inset)/(x1-x0), (height-2*inset)/(y1-y0))
        tx = min(max(0., inset-scale*x0), width-inset-scale*x1)
        ty = min(max(0., inset-scale*y0), height-inset-scale*y1)
        sx, sy, ox, oy = _mapping(root, width, height, view)
        local_x, local_y = (tx+(scale-1)*ox)/sx, (ty+(scale-1)*oy)/sy
        group = ET.Element(f'{{{NS}}}g', transform=f'matrix({scale:.12g} 0 0 {scale:.12g} {local_x:.12g} {local_y:.12g})')
        original_transform = root.attrib.pop('transform', None)
        content = ET.SubElement(group, f'{{{NS}}}g', transform=original_transform) if original_transform else group
        for child in list(root):
            if child.tag.rsplit('}', 1)[-1] not in NON_DRAWING:
                root.remove(child)
                content.append(child)
        root.append(group)
    root.set('overflow', 'hidden')
    if overflow_css:
        _style(root, overflow='hidden')
    if re.search(r'(?:^|;)\s*(?:width|height)\s*:', root.get('style', ''), re.I):
        _style(root, width=f'{width:g}px', height=f'{height:g}px')
    return ET.tostring(root, encoding='unicode')
