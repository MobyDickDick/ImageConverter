"""External development contract for a user's five-part humidifier scene.

No runtime detector, fitted parameters, SVG group names or model release is
used. All native elements must be consumed by the fixed visual annotation.
This deliberately limited checker does not certify arbitrary SVG semantics.
"""
from __future__ import annotations

from collections import Counter
import math
import re
from xml.etree import ElementTree as ET


def _number(node, name, default='0'):
    value = float(node.get(name,default))
    if not math.isfinite(value):
        raise ValueError('Nonfinite SVG length')
    return value


def _box(node):
    return [_number(node,k) for k in ('x','y','width','height')]


def _gray(paint):
    if not re.fullmatch(r'#[0-9a-fA-F]{6}',paint or ''):
        raise ValueError('Unsupported paint')
    rgb = [int(paint[i:i+2],16) for i in (1,3,5)]
    if len(set(rgb)) != 1:
        raise ValueError('Expected achromatic paint')
    return rgb[0]


def _match_all(actual, expected, matches):
    def assign(index, used):
        if index == len(expected):
            return len(used) == len(actual)
        return any(assign(index+1, used|{i}) for i,a in enumerate(actual)
                   if i not in used and matches(a,expected[index]))
    return len(actual) == len(expected) and assign(0,set())


def check_scene(svg, annotation):
    try:
        if annotation['schema'] != 'spray_panel_visual_contract_v1' or len(svg) > 100_000:
            raise ValueError('Unsupported annotation or size')
        root = ET.fromstring(svg)
        size = annotation['size']
        if [_number(root,'width'),_number(root,'height')] != size:
            raise ValueError('Wrong viewport')
        if list(map(float,root.get('viewBox','').split())) != [0,0,*size]:
            raise ValueError('Wrong coordinate system')
        native=[]
        permitted={'svg','g','desc','defs','linearGradient','stop','rect','polygon','line'}
        forbidden={'transform','style','opacity','fill-opacity','stroke-opacity','clip-path','mask','filter',
                   'display','visibility','marker-start','marker-end','marker-mid'}
        def walk(node, inherited):
            tag = node.tag.rsplit('}',1)[-1]
            if tag not in permitted or any(k in node.attrib for k in forbidden):
                raise ValueError('Unsupported element/effect')
            attrs = dict(inherited,**node.attrib)
            if tag in {'rect','polygon','line'}:
                native.append((tag,attrs))
            for child in node:
                walk(child,{k:v for k,v in attrs.items() if k.startswith(('stroke','fill'))})
        walk(root,{})
        counts = Counter(tag for tag,_ in native)
        if counts != {'rect':3,'polygon':5,'line':15}:
            return dict(complete=False,reason='native_inventory',counts=dict(counts))
        rects = [a for t,a in native if t == 'rect']
        background = next(a for a in rects if a.get('fill','').startswith('url(#'))
        frame = next(a for a in rects if a.get('fill') == 'none')
        rail = next(a for a in rects if a is not background and a is not frame)
        def near(a,b,t):
            return max(abs(x-y) for x,y in zip(a,b)) <= t
        checks = dict(background=near(_box(background),annotation['background'],.6),
            rail=near(_box(rail),annotation['rail'],.8) and _gray(rail.get('fill')) <= 160,
            frame=near(_box(frame),annotation['frame'],1.) and _gray(frame.get('stroke')) <= 170)
        dash = [float(v) for v in frame.get('stroke-dasharray','').split()]
        checks['dashed_frame'] = (len(dash) == 2 and all(math.isfinite(v) and v > 0 for v in dash)
                                  and 2.2 <= sum(dash) <= 2.6 and .15 <= dash[1]/sum(dash) <= .6
                                  and .4 <= _number(frame,'stroke-width') <= 1.2)
        gradients = [n for n in root.iter() if n.tag.rsplit('}',1)[-1] == 'linearGradient']
        if len(gradients) != 1 or background['fill'] != 'url(#'+gradients[0].get('id','')+')':
            raise ValueError('Wrong paint server')
        stops = list(gradients[0])
        checks['background_gradient'] = (len(stops) == 4 and
            [_gray(s.get('stop-color')) for s in stops][1:3] == [255,255] and
            all(180 <= _gray(stops[i].get('stop-color')) <= 220 for i in (0,3)))
        polygons = [a for t,a in native if t == 'polygon']
        def nozzle_matches(a,cy):
            values = [float(v) for v in re.split(r'[\s,]+',a.get('points','').strip())]
            if len(values) != 12 or not all(math.isfinite(v) for v in values) or _gray(a.get('fill')) > 185:
                return False
            points = list(zip(values[::2],values[1::2]))
            xs,ys = zip(*points)
            rail_right = _number(rail,'x')+_number(rail,'width')
            return (abs(min(xs)-rail_right) <= .15 and 1 <= max(xs)-min(xs) <= 3.5
                    and abs((min(ys)+max(ys))/2-cy) <= 1 and .4 <= max(ys)-min(ys) <= 3
                    and points[0][0] == points[-1][0] and points[2][0] == points[3][0])
        checks['five_connected_nozzles'] = _match_all(polygons,annotation['nozzle_centers'],nozzle_matches)
        lines = [a for t,a in native if t == 'line']
        expected=[]
        for cy in annotation['spray_centers']:
            expected.extend([[(8.5,cy-2),(15.5,cy-6.5)],[(8.5,cy),(17,cy)],[(8.5,cy+2),(15.5,cy+6.5)]])
        def ray_matches(a,ends):
            points=[(_number(a,'x'+s),_number(a,'y'+s)) for s in ('1','2')]
            distance = lambda p,q:math.dist(p,q)
            error = min(max(distance(p,q) for p,q in zip(points,ends)),
                        max(distance(p,q) for p,q in zip(points,reversed(ends))))
            return (error <= annotation['line_position_tolerance'] and 130 <= _gray(a.get('stroke')) <= 215
                    and .25 <= _number(a,'stroke-width','1') <= 1.6
                    and a.get('stroke-linecap','butt') == 'butt' and 'stroke-dasharray' not in a)
        checks['fifteen_individual_rays'] = _match_all(lines,expected,ray_matches)
        checks['depth'] = native[0][1] is background and native[1][1] is rail
        return dict(complete=all(checks.values()),reason='passed' if all(checks.values()) else 'visual_contract',
                    checks=checks,counts=dict(counts))
    except (ValueError,KeyError,TypeError,StopIteration,ET.ParseError,OverflowError) as exc:
        return dict(complete=False,reason='unsupported_or_invalid',error=str(exc))
