"""Materialize numeric dashed rectangle strokes in MuPDF's private SVG input.

Saved vectors retain their native rect and SVG dash attributes. A bounded path
expansion preserves perimeter phase, corners and the closed-path seam instead
of letting MuPDF silently paint the entire rectangle's stroke as solid.
"""
from __future__ import annotations

import math
import re
from xml.etree import ElementTree as ET


def normalize_dashed_rectangles(svg):
    if 'stroke-dasharray' not in svg or 'rect' not in svg:
        return svg
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg
    changed = False
    inherited_keys = {'stroke','stroke-width','stroke-dasharray','stroke-dashoffset',
                      'stroke-linecap','stroke-linejoin','stroke-miterlimit','stroke-opacity'}

    def visit(parent, inherited):
        nonlocal changed
        inherited = dict(inherited, **{k:v for k,v in parent.attrib.items() if k in inherited_keys})
        for index,node in list(enumerate(list(parent))):
            if node.tag.rsplit('}',1)[-1] != 'rect':
                visit(node,inherited)
                continue
            attrs = dict(inherited, **{k:v for k,v in node.attrib.items() if k in inherited_keys})
            if attrs.get('stroke-dasharray','none') == 'none' or attrs.get('stroke','none') == 'none':
                continue
            if len(node) or any(k in node.attrib for k in ('pathLength','rx','ry','style')):
                continue
            if attrs.get('stroke-linecap','butt') != 'butt':
                continue
            if attrs.get('stroke-linejoin','miter') != 'miter':
                continue
            try:
                x,y,w,h = [float(node.get(k,'0')) for k in ('x','y','width','height')]
                pattern = [float(v) for v in re.split(r'[\s,]+',attrs['stroke-dasharray'].strip())]
                offset = float(attrs.get('stroke-dashoffset','0'))
                stroke_width = float(attrs.get('stroke-width','1'))
                if not math.isfinite(stroke_width) or stroke_width <= 0 or float(attrs.get('stroke-miterlimit','4')) < 2**.5:
                    continue
                if not all(math.isfinite(v) for v in [x,y,w,h,offset,*pattern]) or min(w,h,*pattern) <= 0:
                    continue
                if len(pattern)%2:
                    pattern *= 2
                perimeter = 2*(w+h)
                period = sum(pattern)
                if len(pattern) > 32 or perimeter/min(pattern) > 4096:
                    continue
                phase = offset%period
                slot = 0
                while phase >= pattern[slot]:
                    phase -= pattern[slot]
                    slot = (slot+1)%len(pattern)
                position = 0.
                remaining = pattern[slot]-phase
                intervals = []
                while position < perimeter-1e-9:
                    end = min(perimeter,position+remaining)
                    if slot%2 == 0 and end > position:
                        intervals.append((position,end))
                    position = end
                    slot = (slot+1)%len(pattern)
                    remaining = pattern[slot]
                # Merge paint crossing the closepath seam into one joined path.
                if len(intervals) > 1 and intervals[0][0] == 0 and intervals[-1][1] == perimeter:
                    start = intervals.pop()[0]
                    end = intervals.pop(0)[1]
                    intervals.append((start,perimeter+end))
                def point(t):
                    t %= perimeter
                    if t <= w: return x+t,y
                    if t <= w+h: return x+w,y+t-w
                    if t <= 2*w+h: return x+2*w+h-t,y+h
                    return x,y+perimeter-t
                commands=[]
                join_corners=set()
                corners = [0,w,w+h,2*w+h,perimeter,perimeter+w,perimeter+w+h,perimeter+2*w+h]
                for start,end in intervals:
                    # Cairo/SVG includes the rectangle's join when a dash
                    # touches a vertex exactly. A separate outer quadrant
                    # retains that join without extending paint into a gap.
                    starts_at_corner = any(abs(start-t) < 1e-9 for t in corners)
                    ends_at_corner = any(abs(end-t) < 1e-9 for t in corners)
                    a,b = point(start)
                    commands.append(f'M {a:.9g} {b:.9g}')
                    if starts_at_corner:
                        join_corners.add(start%perimeter)
                    for t in [v for v in corners if start < v < end]+[end]:
                        a,b = point(t)
                        commands.append(f'L {a:.9g} {b:.9g}')
                    if ends_at_corner:
                        join_corners.add(end%perimeter)
                    if start == 0 and end == perimeter:
                        commands.append('Z')
                namespace = node.tag[:-4]
                group = ET.Element(namespace+'g', {k:v for k,v in node.attrib.items()
                    if k not in {'x','y','width','height','fill',*inherited_keys}})
                fill_attrs = {'fill':node.get('fill')} if 'fill' in node.attrib else {}
                ET.SubElement(group,namespace+'rect',x=str(x),y=str(y),width=str(w),height=str(h),
                              stroke='none',**fill_attrs)
                stroke = {k:v for k,v in attrs.items() if k not in {'stroke-dasharray','stroke-dashoffset'}}
                ET.SubElement(group,namespace+'path',d=' '.join(commands),fill='none',
                              **dict(stroke, **{'stroke-dasharray':'none','stroke-dashoffset':'0'}))
                for t in join_corners:
                    a,b=point(t)
                    sx,sy = (-1,-1) if t == 0 else (1,-1) if t == w else (1,1) if t == w+h else (-1,1)
                    r=stroke_width/2
                    ET.SubElement(group,namespace+'rect',x=str(a-r if sx<0 else a),
                        y=str(b-r if sy<0 else b),width=str(r),height=str(r),
                        fill=attrs['stroke'],stroke='none',**{'fill-opacity':attrs.get('stroke-opacity','1')})
                parent.remove(node)
                parent.insert(index,group)
                changed = True
            except (ValueError,TypeError,OverflowError):
                continue
    visit(root,{})
    return ET.tostring(root,encoding='unicode') if changed else svg
