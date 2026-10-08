"""Rendering helpers extracted from the imageCompositeConverter monolith."""

from __future__ import annotations

import base64
import copy
import gc
import json
import math
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

_INPROCESS_RENDER_COUNT = 0
_INPROCESS_GC_PERIOD = 25
_SUBPROCESS_RENDER_CALL_ID = 0
_SUBPROCESS_RENDER_AGG = {
    "calls": 0,
    "slow_calls": 0,
    "timeouts": 0,
    "elapsed_sum": 0.0,
}


def _expand_axis_aligned_linear_gradients_for_fitz(svg_string: str) -> str:
    """Expand gradient-filled rectangles only in the PyMuPDF render input.

    The bundled PyMuPDF build paints SVG linear gradients black.  Conversion
    output must nevertheless remain a native gradient, so this renderer adapter
    expands axis-aligned gradient rectangles in its private input document.  It
    is deliberately generic and keyed by SVG paint-server references, not image
    names or converter-specific gradient IDs.
    """
    if "linearGradient" not in svg_string or "url(#" not in svg_string:
        return svg_string
    try:
        root = ET.fromstring(svg_string)
    except ET.ParseError:
        return svg_string
    ET.register_namespace("", "http://www.w3.org/2000/svg")

    def local_name(element) -> str:
        return str(element.tag).rsplit("}", 1)[-1]

    def number(value: str | None, reference: float, default: float) -> float:
        text = str(value or "").strip()
        try:
            return reference * float(text[:-1]) / 100.0 if text.endswith("%") else float(text)
        except ValueError:
            return default

    def color(value: str) -> tuple[int, int, int] | None:
        text = value.strip()
        if len(text) == 7 and text.startswith("#"):
            try:
                return tuple(int(text[index:index + 2], 16) for index in (1, 3, 5))
            except ValueError:
                return None
        return None

    gradients = {
        element.get("id"): element
        for element in root.iter()
        if local_name(element) == "linearGradient" and element.get("id")
    }
    changed = False
    for parent in root.iter():
        for index, rectangle in reversed(list(enumerate(list(parent)))):
            if local_name(rectangle) != "rect":
                continue
            fill = rectangle.get("fill", "")
            match = re.fullmatch(r"url\(#([^)]+)\)", fill.strip())
            gradient = gradients.get(match.group(1)) if match else None
            if gradient is None:
                continue
            x = number(rectangle.get("x"), 1.0, 0.0)
            y = number(rectangle.get("y"), 1.0, 0.0)
            width = number(rectangle.get("width"), 1.0, 0.0)
            height = number(rectangle.get("height"), 1.0, 0.0)
            user_space = gradient.get("gradientUnits") == "userSpaceOnUse"
            x1 = number(gradient.get("x1"), width, x if user_space else 0.0)
            y1 = number(gradient.get("y1"), height, y if user_space else 0.0)
            x2 = number(gradient.get("x2"), width, x + width if user_space else width)
            y2 = number(gradient.get("y2"), height, y if user_space else 0.0)
            if not user_space:
                x1 += x
                x2 += x
                y1 += y
                y2 += y
            vertical = abs(y2 - y1) > abs(x2 - x1)
            reversed_axis = y2 < y1 if vertical else x2 < x1
            stops = []
            for stop in gradient:
                if local_name(stop) != "stop":
                    continue
                style = dict(
                    item.split(":", 1) for item in stop.get("style", "").split(";") if ":" in item
                )
                rgb = color(stop.get("stop-color", style.get("stop-color", "")))
                if rgb is not None:
                    stops.append((number(stop.get("offset"), 1.0, 0.0), rgb))
            stops.sort(key=lambda item: item[0])
            if width <= 0 or height <= 0 or len(stops) < 2:
                continue
            band_count = max(8, min(128, int(round(height if vertical else width)) * 2))
            inherited = {
                key: value for key, value in rectangle.attrib.items()
                if key not in {"x", "y", "width", "height", "fill", "stroke", "stroke-width"}
            }
            # Antialiased adjacent bands leave partially transparent seams.
            # Back them with an opaque fill and overlap by half a source unit;
            # clamp each band to the rectangle so its outer edge stays intact.
            backing = ET.Element(rectangle.tag, inherited)
            for key in ("x", "y", "width", "height"):
                backing.set(key, f"{dict(x=x, y=y, width=width, height=height)[key]:g}")
            backing.set("fill", "#" + "".join(f"{channel:02x}" for channel in stops[0][1]))
            backing.set("stroke", "none")
            parent.insert(index, backing)
            for band_index in range(band_count):
                position = (band_index + 0.5) / band_count
                if reversed_axis:
                    position = 1.0 - position
                left, right = stops[0], stops[-1]
                for stop_index in range(1, len(stops)):
                    if position <= stops[stop_index][0]:
                        left, right = stops[stop_index - 1], stops[stop_index]
                        break
                span = max(1e-9, right[0] - left[0])
                ratio = max(0.0, min(1.0, (position - left[0]) / span))
                rgb = tuple(round(a * (1.0 - ratio) + b * ratio) for a, b in zip(left[1], right[1]))
                band = ET.Element(rectangle.tag, inherited)
                if vertical:
                    start = max(y, y + height * band_index / band_count - 0.5)
                    end = min(y + height, y + height * (band_index + 1) / band_count + 0.5)
                    band.set("x", f"{x:g}")
                    band.set("y", f"{start:g}")
                    band.set("width", f"{width:g}")
                    band.set("height", f"{end - start:g}")
                else:
                    start = max(x, x + width * band_index / band_count - 0.5)
                    end = min(x + width, x + width * (band_index + 1) / band_count + 0.5)
                    band.set("x", f"{start:g}")
                    band.set("y", f"{y:g}")
                    band.set("width", f"{end - start:g}")
                    band.set("height", f"{height:g}")
                band.set("fill", "#" + "".join(f"{channel:02x}" for channel in rgb))
                band.set("stroke", "none")
                parent.insert(index + 1 + band_index, band)
            rectangle.set("fill", "none")
            parent.remove(rectangle)
            parent.insert(index + 1 + band_count, rectangle)
            changed = True
    return ET.tostring(root, encoding="unicode") if changed else svg_string


def _expand_bezier_linear_gradients_for_fitz(svg_string: str, *, fitz_module=None, size_w=None, size_h=None) -> str:
    """Paint a closed Bezier fill through its exact native antialiasing mask.

    Only the private render document gets a temporary image paint layer. Saved
    SVGs retain curves and gradients. The mask is rendered from the native path
    at the requested output resolution, avoiding repeated edge compositing by
    overlapping gradient bands. Flattening is used only for paint bounds.
    Unsupported commands, compound paths, transforms and alpha are untouched.
    """
    if 'linearGradient' not in svg_string or '<path' not in svg_string:
        return svg_string
    try:
        root = ET.fromstring(svg_string)
    except ET.ParseError:
        return svg_string
    if any(e.get('transform') for e in root.iter()):
        return svg_string
    if root.get('preserveAspectRatio', 'xMidYMid meet') not in {'xMidYMid', 'xMidYMid meet'}:
        return svg_string
    namespace = '{http://www.w3.org/2000/svg}'
    gradients = {e.get('id'):e for e in root.iter() if e.tag.rsplit('}', 1)[-1] == 'linearGradient'}
    changed = False

    def flatten(control, output, depth=0):
        a, b = control[0], control[-1]
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dy)
        error = max((abs(dx*(v[1]-a[1])-dy*(v[0]-a[0]))/length if length else math.dist(a,v))
                    for v in control[1:-1])
        if error <= .02 or depth >= 12:
            output.append(b)
            return
        levels = [control]
        while len(levels[-1])>1:
            levels.append([((a[0]+b[0])/2, (a[1]+b[1])/2) for a,b in zip(levels[-1],levels[-1][1:])])
        flatten([v[0] for v in levels],output,depth+1)
        flatten([v[-1] for v in levels[::-1]],output,depth+1)

    for parent in list(root.iter()):
        for index, path in reversed(list(enumerate(list(parent)))):
            if path.tag.rsplit('}',1)[-1] != 'path':
                continue
            match = re.fullmatch(r'url\(#([^)]+)\)',path.get('fill',''))
            if not match or match.group(1) not in gradients:
                continue
            if set(path.attrib)-{'id','d','fill','stroke','stroke-width','stroke-linejoin','data-role'}:
                continue
            data = path.get('d','')
            tokens = re.findall(r'[A-Za-z]|[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?',data)
            if re.sub(r'[\s,]+','',data) != ''.join(tokens):
                continue
            points, cursor, command = [], 0, None
            try:
                while cursor<len(tokens):
                    command = tokens[cursor]
                    cursor += 1
                    if command == 'Z':
                        if cursor != len(tokens) or len(points)<3:
                            raise ValueError('not one closed contour')
                        break
                    count = {'M':2,'L':2,'Q':4,'C':6}.get(command)
                    if count is None or (command=='M' and points) or (command!='M' and not points):
                        raise ValueError('unsupported path')
                    values = [float(v) for v in tokens[cursor:cursor+count]]
                    cursor += count
                    if len(values)!=count or not all(math.isfinite(v) for v in values):
                        raise ValueError('invalid coordinates')
                    controls = list(zip(values[::2],values[1::2]))
                    if command in {'M','L'}:
                        points.extend(controls)
                    else:
                        flatten([points[-1],*controls],points)
                    if len(points)>512:
                        raise ValueError('too many subdivisions')
                if command != 'Z':
                    continue
            except (ValueError,IndexError):
                continue
            gradient = gradients[match.group(1)]
            if set(gradient.attrib)-{'id','x1','y1','x2','y2','gradientUnits'}:
                continue
            if any(e.get('opacity') or e.get('style') or e.get('clip-path') or e.get('mask') for e in root.iter()):
                continue
            try:
                import numpy as np
                if fitz_module is None:
                    from src.iCCModules.imageCompositeConverterDependencies import import_with_vendored_fallback
                    fitz_module = import_with_vendored_fallback('fitz')
                xs,ys = zip(*points)
                bx,by,bw,bh = min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys)
                if min(bw,bh)<=0:
                    continue
                viewport = [float(v) for v in root.get('viewBox','').replace(',',' ').split()]
                if not viewport:
                    viewport = [0.,0.,float(root.get('width','0').removesuffix('px')),float(root.get('height','0').removesuffix('px'))]
                if len(viewport)!=4 or min(viewport[2:])<=0 or not all(math.isfinite(v) for v in viewport):
                    continue
                user = gradient.get('gradientUnits')=='userSpaceOnUse'
                def coordinate(value,axis):
                    origin,extent = (bx,bw) if axis==0 else (by,bh)
                    if user:
                        return float(value[:-1])*viewport[axis+2]/100 if value.endswith('%') else float(value)
                    return origin+extent*(float(value[:-1])/100 if value.endswith('%') else float(value))
                x1,x2 = coordinate(gradient.get('x1','0%'),0),coordinate(gradient.get('x2','100%'),0)
                y1,y2 = coordinate(gradient.get('y1','0%'),1),coordinate(gradient.get('y2','0%'),1)
                if x1!=x2 and y1!=y2 or x1==x2 and y1==y2:
                    continue
                stops = []
                for stop in gradient:
                    if set(stop.attrib)-{'offset','stop-color'} or stop.tag.rsplit('}',1)[-1]!='stop':
                        raise ValueError('unsupported stop')
                    offset = stop.get('offset','0')
                    fraction = float(offset[:-1])/100 if offset.endswith('%') else float(offset)
                    color = stop.get('stop-color','')
                    if not re.fullmatch(r'#[0-9a-fA-F]{6}',color):
                        raise ValueError('unsupported color')
                    stops.append((fraction,[int(color[i:i+2],16) for i in (1,3,5)]))
                stops.sort(key=lambda v:v[0])
                if len(stops)<2 or not all(math.isfinite(v[0]) for v in stops):
                    continue
                mask_root = ET.Element(namespace+'svg',root.attrib)
                ET.SubElement(mask_root,namespace+'path',d=data,fill='#ffffff',stroke='none')
                with fitz_module.open(stream=ET.tostring(mask_root),filetype='svg') as doc:
                    page = doc[0]
                    w,h = int(size_w or math.ceil(page.rect.width)),int(size_h or math.ceil(page.rect.height))
                    if not 0<w<=2048 or not 0<h<=2048:
                        continue
                    pix = page.get_pixmap(matrix=fitz_module.Matrix(w/page.rect.width,h/page.rect.height),alpha=True)
                alpha = np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,4)[:,:,3]
                # Preserve the root's default centered aspect-ratio mapping.
                zoom = min(w/viewport[2],h/viewport[3])
                padding = [(w-viewport[2]*zoom)/2,(h-viewport[3]*zoom)/2]
                axis,low,high = (1,y1,y2) if x1==x2 else (0,x1,x2)
                coordinates = viewport[axis]+(np.arange((h,w)[1-axis])+.5-padding[axis])/zoom
                position = (coordinates-low)/(high-low)
                colors = np.stack([np.interp(position,[v[0] for v in stops],[v[1][c] for v in stops]) for c in range(3)],axis=-1)
                colors = np.broadcast_to(colors[:,None,:] if axis==1 else colors[None,:,:],(h,w,3))
                rgba = np.concatenate((np.rint(colors*alpha[:,:,None]/255).astype(np.uint8),alpha[:,:,None]),axis=2)
                paint = fitz_module.Pixmap(fitz_module.csRGB,w,h,rgba.tobytes(),True)
                encoded = base64.b64encode(paint.tobytes('png')).decode('ascii')
            except (ValueError,TypeError,IndexError,RuntimeError):
                continue
            group = ET.Element(namespace+'g')
            # Full-canvas pixel alignment also preserves antialiasing at curves.
            image = ET.SubElement(group,namespace+'image',x=str(viewport[0]-padding[0]/zoom),
                                  y=str(viewport[1]-padding[1]/zoom),width=str(w/zoom),height=str(h/zoom))
            image.set('href','data:image/png;base64,'+encoded)
            outline = copy.deepcopy(path)
            outline.set('fill','none')
            group.append(outline)
            parent.remove(path)
            parent.insert(index,group)
            changed = True
    return ET.tostring(root,encoding='unicode') if changed else svg_string


def _expand_polygon_linear_gradients_for_fitz(svg_string: str) -> str:
    """Render simple native polygon gradients through privately clipped bands.

    PyMuPDF does not implement these paint servers. Clip each band geometrically
    so concave polygons remain vectors without relying on SVG clipPath support.
    Transforms, transparency and non-axis-aligned gradients are left untouched.
    """
    if 'linearGradient' not in svg_string or '<polygon' not in svg_string:
        return svg_string
    try:
        root = ET.fromstring(svg_string)
    except ET.ParseError:
        return svg_string
    namespace = '{http://www.w3.org/2000/svg}'
    gradients = {e.get('id'): e for e in root.iter() if e.tag.rsplit('}',1)[-1] == 'linearGradient'}
    changed = False

    def clip(points, axis, bound, greater):
        output = []
        for a, b in zip(points[-1:]+points[:-1], points):
            inside_a = a[axis] >= bound if greater else a[axis] <= bound
            inside_b = b[axis] >= bound if greater else b[axis] <= bound
            if inside_a != inside_b:
                t = (bound-a[axis])/(b[axis]-a[axis])
                output.append(tuple(a[i]+t*(b[i]-a[i]) for i in (0,1)))
            if inside_b:
                output.append(b)
        return output

    for parent in list(root.iter()):
        for index, polygon in reversed(list(enumerate(list(parent)))):
            if polygon.tag.rsplit('}',1)[-1] != 'polygon':
                continue
            match = re.fullmatch(r'url\(#([^)]+)\)', polygon.get('fill',''))
            gradient = gradients.get(match.group(1)) if match else None
            if gradient is None or any(k not in {'id','x1','y1','x2','y2','gradientUnits'} for k in gradient.attrib):
                continue
            if any(k not in {'id','points','fill','stroke','stroke-width','stroke-linejoin'} for k in polygon.attrib):
                continue
            try:
                numbers = [float(v) for v in re.split(r'[\s,]+',polygon.get('points','').strip())]
                points = list(zip(numbers[::2],numbers[1::2]))
                if len(numbers)%2 or len(points) < 3 or len(points) > 32 or not all(math.isfinite(v) for v in numbers):
                    continue
                xs, ys = zip(*points)
                x,y,w,h = min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys)
                if min(w,h) <= 0:
                    continue
                # The rectangle adapter implements coordinates, reversal and stops.
                # Restrict to a genuine axis-aligned, opaque paint server.
                if not (gradient.get('x1','0%') == gradient.get('x2','100%')
                        or gradient.get('y1','0%') == gradient.get('y2','0%')):
                    continue
                if any(s.get('stop-opacity','1') != '1' or set(s.attrib)-{'offset','stop-color'}
                       for s in gradient):
                    continue
                proxy = ET.Element(namespace+'svg')
                defs = ET.SubElement(proxy,namespace+'defs')
                paint = copy.deepcopy(gradient)
                vertical = gradient.get('x1','0%') == gradient.get('x2','100%')
                axis = 'y' if vertical else 'x'
                start,extent = (y,h) if vertical else (x,w)
                user_space = gradient.get('gradientUnits') == 'userSpaceOnUse'
                def coord(value):
                    if user_space:
                        reference = float(root.get('height' if vertical else 'width',extent))
                        return reference*float(value[:-1])/100 if value.endswith('%') else float(value)
                    return start+extent*(float(value[:-1])/100 if value.endswith('%') else float(value))
                low = coord(gradient.get(axis+'1','0%'))
                high = coord(gradient.get(axis+'2','100%' if not vertical else '0%'))
                if low == high:
                    continue
                for stop in paint:
                    offset = stop.get('offset','0')
                    fraction = float(offset[:-1])/100 if offset.endswith('%') else float(offset)
                    stop.set('offset',str((low+fraction*(high-low)-start)/extent))
                paint.set('gradientUnits','objectBoundingBox')
                paint.set('x1','0%'); paint.set('y1','0%')
                paint.set('x2','0%' if vertical else '100%')
                paint.set('y2','100%' if vertical else '0%')
                defs.append(paint)
                ET.SubElement(proxy,namespace+'rect',x=str(x),y=str(y),width=str(w),height=str(h),
                              fill=polygon.get('fill'))
                expanded = ET.fromstring(_expand_axis_aligned_linear_gradients_for_fitz(ET.tostring(proxy,encoding='unicode')))
                bands = [e for e in expanded if e.tag.rsplit('}',1)[-1] == 'rect']
                if not bands or bands[0].get('fill','').startswith('url('):
                    continue
            except (ValueError,TypeError):
                continue
            group = ET.Element(namespace+'g')
            if polygon.get('id'):
                group.set('id',polygon.get('id'))
            for band in bands:
                bx,by,bw,bh = (float(band.get(k,0)) for k in ('x','y','width','height'))
                piece = points
                for axis,bound,greater in ((0,bx,True),(0,bx+bw,False),(1,by,True),(1,by+bh,False)):
                    if piece:
                        piece = clip(piece,axis,bound,greater)
                if len(piece) >= 3:
                    ET.SubElement(group,namespace+'polygon',points=' '.join(f'{a:.6f},{b:.6f}' for a,b in piece),
                                  fill=band.get('fill'),stroke='none')
            outline = ET.SubElement(group,polygon.tag,{k:v for k,v in polygon.attrib.items() if k not in {'id','fill'}})
            outline.set('fill','none')
            parent.remove(polygon)
            parent.insert(index,group)
            changed = True
    return ET.tostring(root,encoding='unicode') if changed else svg_string


def _expand_centered_radial_gradients_for_fitz(svg_string: str) -> str:
    """Approximate centered radial ellipse fills in private renderer input.

    PyMuPDF's SVG reader does not reliably render radial paint servers. Native
    gradients stay in saved SVGs; concentric vector fills are only a rendering
    compatibility adapter. Unsupported off-center/transformed gradients stay
    untouched rather than silently changing their meaning.
    """
    if 'radialGradient' not in svg_string or 'url(#' not in svg_string:
        return svg_string
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    try:
        root = ET.fromstring(svg_string)
    except ET.ParseError:
        return svg_string
    gradients = {e.get('id'): e for e in root.iter() if e.tag.rsplit('}', 1)[-1] == 'radialGradient'}
    changed = False
    namespace = '{http://www.w3.org/2000/svg}'
    for parent in list(root.iter()):
        for index, ellipse in reversed(list(enumerate(list(parent)))):
            if ellipse.tag.rsplit('}', 1)[-1] not in ('circle', 'ellipse'):
                continue
            match = re.fullmatch(r'url\(#([^)]+)\)', ellipse.get('fill', ''))
            gradient = gradients.get(match.group(1)) if match else None
            if gradient is None or any(k not in {'id', 'cx', 'cy', 'r', 'gradientUnits', 'fx', 'fy'} for k in gradient.attrib):
                continue
            if (gradient.get('gradientUnits', 'objectBoundingBox') != 'objectBoundingBox'
                    or any(gradient.get(k, '50%') not in ('50%', '0.5') for k in ('cx', 'cy', 'r', 'fx', 'fy'))):
                continue
            try:
                cx, cy = float(ellipse.get('cx', '0')), float(ellipse.get('cy', '0'))
                rx = float(ellipse.get('rx', ellipse.get('r', '0')))
                ry = float(ellipse.get('ry', ellipse.get('r', '0')))
                stops = []
                for stop in gradient:
                    offset, color = stop.get('offset', '0'), stop.get('stop-color', '')
                    if stop.get('stop-opacity', '1') != '1' or not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
                        raise ValueError('unsupported stop')
                    position = float(offset[:-1])/100 if offset.endswith('%') else float(offset)
                    stops.append((position, tuple(int(color[i:i+2], 16) for i in (1, 3, 5))))
                stops.sort()
                if rx <= 0 or ry <= 0 or len(stops) < 2 or any(not 0 <= p <= 1 for p, _ in stops):
                    continue
            except (ValueError, TypeError):
                continue
            group = ET.Element(namespace+'g', {k: v for k, v in ellipse.attrib.items()
                                               if k not in {'cx', 'cy', 'rx', 'ry', 'r', 'fill', 'stroke', 'stroke-width'}})
            rings = max(16, min(128, int(max(rx, ry)*4)))
            for ring in range(rings, 0, -1):
                position = (ring-.5)/rings
                left, right = stops[0], stops[-1]
                for i in range(1, len(stops)):
                    if position <= stops[i][0]:
                        left, right = stops[i-1], stops[i]
                        break
                ratio = max(0., min(1., (position-left[0])/max(1e-9, right[0]-left[0])))
                rgb = [round(a+(b-a)*ratio) for a, b in zip(left[1], right[1])]
                ET.SubElement(group, namespace+'ellipse', cx=f'{cx:g}', cy=f'{cy:g}',
                              rx=f'{rx*ring/rings:g}', ry=f'{ry*ring/rings:g}',
                              fill='#'+''.join(f'{v:02x}' for v in rgb), stroke='none')
            outline = ET.SubElement(group, ellipse.tag, {k: v for k, v in ellipse.attrib.items()
                                                        if k in {'cx', 'cy', 'rx', 'ry', 'r', 'stroke', 'stroke-width'}})
            outline.set('fill', 'none')
            parent.remove(ellipse)
            parent.insert(index, group)
            changed = True
    return ET.tostring(root, encoding='unicode') if changed else svg_string


def render_svg_to_numpy_inprocess(
    svg_string: str,
    size_w: int,
    size_h: int,
    *,
    fitz_module,
    np_module,
    cv2_module,
):
    if fitz_module is None or np_module is None or cv2_module is None:
        return None

    svg_string = str(svg_string or "")
    if re.search(r"(?<![A-Za-z])(nan|inf)(?![A-Za-z])", svg_string, flags=re.IGNORECASE):
        return None

    renderer_svg = _expand_axis_aligned_linear_gradients_for_fitz(svg_string)
    renderer_svg = _expand_bezier_linear_gradients_for_fitz(renderer_svg,fitz_module=fitz_module,size_w=size_w,size_h=size_h)
    renderer_svg = _expand_polygon_linear_gradients_for_fitz(renderer_svg)
    renderer_svg = _expand_centered_radial_gradients_for_fitz(renderer_svg)
    attempts = [renderer_svg]
    normalized_svg = re.sub(r">\s+<", "><", renderer_svg.strip())
    if normalized_svg and normalized_svg != renderer_svg:
        attempts.append(normalized_svg)

    for candidate_svg in attempts:
        global _INPROCESS_RENDER_COUNT
        page = None
        pix = None
        try:
            with fitz_module.open("pdf", candidate_svg.encode("utf-8")) as doc:
                page = doc.load_page(0)
                zoom_x = size_w / page.rect.width if page.rect.width > 0 else 1
                zoom_y = size_h / page.rect.height if page.rect.height > 0 else 1
                mat = fitz_module.Matrix(zoom_x, zoom_y)
                pix = page.get_pixmap(matrix=mat, alpha=True)
            rgba = np_module.frombuffer(pix.samples, dtype=np_module.uint8).reshape(pix.h, pix.w, 4).astype(np_module.float32)
            rgb = rgba[:, :, :3]
            alpha = (rgba[:, :, 3:4] / 255.0)
            composited = rgb + (255.0 * (1.0 - alpha))
            composited = np_module.clip(composited, 0.0, 255.0)
            img = composited.astype(np_module.uint8)
            return cv2_module.cvtColor(img, cv2_module.COLOR_RGB2BGR)
        except Exception:
            continue
        finally:
            if pix is not None:
                del pix
            if page is not None:
                del page
            _INPROCESS_RENDER_COUNT += 1
            if _INPROCESS_RENDER_COUNT % _INPROCESS_GC_PERIOD == 0:
                gc.collect()
    return None


def render_svg_to_numpy_via_subprocess(
    svg_string: str,
    size_w: int,
    size_h: int,
    *,
    np_module,
    timeout_sec: float,
    status_callback=None,
):
    if np_module is None:
        return None
    payload = json.dumps(
        {"svg": str(svg_string or ""), "w": int(size_w), "h": int(size_h)},
        ensure_ascii=False,
    ).encode("utf-8")
    cmd = [sys.executable, "-m", "src.imageCompositeConverter", "--_render-svg-subprocess"]
    child_env = os.environ.copy()
    pythonpath_entries: list[str] = []
    for entry in sys.path:
        if not entry:
            entry = os.getcwd()
        if entry and entry not in pythonpath_entries:
            pythonpath_entries.append(entry)
    existing_pythonpath = child_env.get("PYTHONPATH", "")
    if existing_pythonpath:
        for entry in existing_pythonpath.split(os.pathsep):
            if entry and entry not in pythonpath_entries:
                pythonpath_entries.append(entry)
    child_env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    anchor_test_active = "test_ac08_semantic_anchor_variants_convert_without_failed_svg" in str(
        os.environ.get("PYTEST_CURRENT_TEST", "")
    )
    global _SUBPROCESS_RENDER_CALL_ID
    _SUBPROCESS_RENDER_CALL_ID += 1
    call_id = int(_SUBPROCESS_RENDER_CALL_ID)
    debug_render_timeout = (
        os.environ.get("ICC_DEBUG_RENDER_TIMEOUT", "").strip().lower() in {"1", "true", "yes", "on"}
        or "pytest" in sys.modules
    )
    started = time.monotonic()
    try:
        completed = subprocess.run(
            cmd,
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_sec,
            env=child_env,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - started
        _SUBPROCESS_RENDER_AGG["calls"] += 1
        _SUBPROCESS_RENDER_AGG["timeouts"] += 1
        _SUBPROCESS_RENDER_AGG["elapsed_sum"] += float(elapsed)
        if debug_render_timeout:
            print(
                (
                    "[ICC_RENDER_TIMEOUT] render subprocess exceeded timeout "
                    f"({elapsed:.2f}s > {timeout_sec:.2f}s, size={size_w}x{size_h}, payload_bytes={len(payload)})"
                ),
                file=sys.stderr,
                flush=True,
            )
        if anchor_test_active:
            print(
                "[ANCHOR_DEBUG] render_probe "
                f"call_id={call_id} status=timeout timeout_sec={timeout_sec:.2f} "
                f"size={size_w}x{size_h} payload_bytes={len(payload)} elapsed={elapsed:.2f}s",
                flush=True,
            )
        if status_callback is not None:
            status_callback("timeout")
        return None
    except Exception:
        if status_callback is not None:
            status_callback("error")
        return None
    elapsed = time.monotonic() - started
    _SUBPROCESS_RENDER_AGG["calls"] += 1
    _SUBPROCESS_RENDER_AGG["elapsed_sum"] += float(elapsed)
    if elapsed > 1.0:
        _SUBPROCESS_RENDER_AGG["slow_calls"] += 1
    if anchor_test_active:
        print(
            "[ANCHOR_DEBUG] render_probe "
            f"call_id={call_id} status=done returncode={completed.returncode} timeout_sec={timeout_sec:.2f} "
            f"size={size_w}x{size_h} payload_bytes={len(payload)} elapsed={elapsed:.2f}s",
            flush=True,
        )
    if _SUBPROCESS_RENDER_AGG["calls"] % 25 == 0 and anchor_test_active:
        calls = int(_SUBPROCESS_RENDER_AGG["calls"])
        mean_elapsed = float(_SUBPROCESS_RENDER_AGG["elapsed_sum"]) / float(max(1, calls))
        print(
            "[ANCHOR_DEBUG] render_probe_aggregate "
            f"calls={calls} slow_calls_gt_1s={int(_SUBPROCESS_RENDER_AGG['slow_calls'])} "
            f"timeouts={int(_SUBPROCESS_RENDER_AGG['timeouts'])} mean_elapsed={mean_elapsed:.2f}s",
            flush=True,
        )
    if completed.returncode != 0 or not completed.stdout:
        if status_callback is not None:
            status_callback("error")
        return None
    try:
        response = json.loads(completed.stdout.decode("utf-8"))
    except Exception:
        if status_callback is not None:
            status_callback("error")
        return None
    if not isinstance(response, dict) or not response.get("ok", False):
        if status_callback is not None:
            status_callback("error")
        return None
    try:
        w = int(response["w"])
        h = int(response["h"])
        raw = base64.b64decode(str(response["data"]).encode("ascii"))
        return np_module.frombuffer(raw, dtype=np_module.uint8).reshape(h, w, 3).copy()
    except Exception:
        return None
