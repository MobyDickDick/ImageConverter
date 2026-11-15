"""Externally authored synthetic constructions. No converter or checker imports.

Annotations come from explicit construction geometry, not emitted SVG analysis.
Three primitive constructions and their similarities are development data only.
"""
from __future__ import annotations

import copy
import math
from xml.etree import ElementTree as ET

NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', 'http://www.w3.org/2000/svg')


def arc_geometry(center, radii, rotation, start, sweep):
    phi = math.radians(rotation)

    def point(angle):
        theta = math.radians(angle)
        x, y = radii[0]*math.cos(theta), radii[1]*math.sin(theta)
        return [center[0]+x*math.cos(phi)-y*math.sin(phi), center[1]+x*math.sin(phi)+y*math.cos(phi)]

    points = [point(start), point(start+sweep)]
    d = (f'M {points[0][0]:.12g} {points[0][1]:.12g} A {radii[0]} {radii[1]} {rotation} '
         f'{int(abs(sweep)>180)} {int(sweep>0)} {points[1][0]:.12g} {points[1][1]:.12g}')
    return d, dict(points=points, center=center, radii=radii, rotation=rotation, start_angle=start, sweep=sweep)


def development_cases():
    for kind, data, line_start in [
        ('quadratic', ('M24 60 Q48 12 72 60', dict(points=[[24,60],[48,12],[72,60]])), [16,76]),
        ('cubic', ('M24 60 C36 12 60 12 72 60', dict(points=[[24,60],[36,12],[60,12],[72,60]])), [20,76]),
        ('arc', arc_geometry([48,60], [24,24], 0, 180, 90), [24,76]),
    ]:
        main_d, main_geo = data
        ellipse_d, ellipse_geo = arc_geometry([110,50], [16,8], 30, 20, 240)
        if kind == 'arc':
            hidden_d, hidden_geo = arc_geometry([110,110], [8,5], 25, 10, 270)
        else:
            hidden_d = ('M100 110 Q110 98 120 110' if kind == 'quadratic'
                        else 'M100 110 C103 98 117 98 120 110')
            hidden_geo = dict(points=([[100,110],[110,98],[120,110]] if kind == 'quadratic'
                                     else [[100,110],[103,98],[117,98],[120,110]]))
        objects = [
            dict(id='background', kind='rect', points=[[0,0],[160,0],[160,160],[0,160]], fill='white'),
            dict(id='lead', kind='line', points=[line_start, [24,60]], stroke='#224466', stroke_width=2),
            dict(id='curve', kind=kind, **main_geo, stroke='#224466', stroke_width=2),
            dict(id='ellipse', kind='arc', **ellipse_geo, stroke='#993355', stroke_width=1.5),
            dict(id='hidden_curve', kind=kind, **hidden_geo, stroke='#111111', stroke_width=2),
            dict(id='cover', kind='rect', points=[[92,92],[128,92],[128,128],[92,128]], fill='#55aa66'),
        ]
        body = (f'<line x1="{line_start[0]}" y1="{line_start[1]}" x2="24" y2="60" stroke="#224466" stroke-width="2"/>'
                f'<path d="{main_d}" fill="none" stroke="#224466" stroke-width="2"/>'
                f'<path d="{ellipse_d}" fill="none" stroke="#993355" stroke-width="1.5"/>'
                f'<path d="{hidden_d}" fill="none" stroke="#111111" stroke-width="2"/>'
                '<rect x="92" y="92" width="36" height="36" fill="#55aa66"/>')
        for name, tx, angle, scale, reflect, shift in [
            ('plain', '', 0, 1, False, [0,0]),
            ('rotated', 'rotate(90 80 80)', 90, 1, False, [160,0]),
            ('scaled', 'translate(16 16) scale(.8)', 0, .8, False, [16,16]),
            ('reflected', 'matrix(-1 0 0 1 160 0)', 0, 1, True, [160,0]),
            ('oblique', 'translate(40 4) rotate(20) scale(.7)', 20, .7, False, [40,4]),
        ]:
            ann = dict(schema='independent_curve_scene_v1', size=[160,160], complete_inventory=True,
                       limits=dict(position=.05, color=0, stroke_width=.01, angle=.01),
                       objects=copy.deepcopy(objects), relations=[
                           dict(kind='endpoints_meet', objects=['lead','curve'], tolerance=.01),
                           dict(kind='tangent_join', objects=['lead','curve'], tolerance=.01, angle_tolerance=.1),
                           dict(kind='front_of', objects=['cover','hidden_curve'])])

            def point(p):
                x, y = p
                if reflect:
                    x = -x
                c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
                return [shift[0]+scale*(c*x-s*y), shift[1]+scale*(s*x+c*y)]

            for obj in ann['objects'][1:]:
                obj['points'] = [point(p) for p in obj['points']]
                if 'stroke_width' in obj:
                    obj['stroke_width'] *= scale
                if obj['kind'] == 'arc':
                    obj['center'] = point(obj['center'])
                    obj['radii'] = [r*scale for r in obj['radii']]
                    if reflect:
                        obj['rotation'] = 180-obj['rotation']
                        obj['start_angle'] = -obj['start_angle']
                        obj['sweep'] = -obj['sweep']
                    obj['rotation'] += angle
            svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160">'
                   '<rect width="160" height="160" fill="white"/>'
                   f'<g transform="{tx}">{body}</g></svg>')
            yield dict(case_id=kind+'-'+name, primitive=kind, transform=name, annotation=ann, svg=svg)


def controls(case):
    for damage in ('missing_curve','extra_curve','hidden_missing','hidden_extra','hidden_geometry',
                   'wrong_control','wrong_connection','wrong_tangent','wrong_width','wrong_paint',
                   'wrong_transform','wrong_depth','wrong_arc_sweep','wrong_arc_large','wrong_arc_rotation',
                   'wrong_arc_radius','filled_curve','compound_path','transparent_cover'):
        root = ET.fromstring(case['svg'])
        group = root[1]
        curve, ellipse, hidden, cover = group[1:]
        if damage == 'missing_curve':
            group.remove(curve)
        elif damage == 'extra_curve':
            group.append(copy.deepcopy(curve))
        elif damage == 'hidden_missing':
            group.remove(hidden)
        elif damage == 'hidden_extra':
            group.insert(3, copy.deepcopy(hidden))
        elif damage == 'hidden_geometry':
            hidden.set('transform', 'translate(2 0)')
        elif damage == 'wrong_control':
            curve.set('d', curve.get('d').replace('48 12', '48 17').replace('36 12', '36 17')
                      if case['primitive'] != 'arc' else 'M24 60 A20 24 0 0 1 48 36')
        elif damage == 'wrong_connection':
            group[0].set('x2', '25')
        elif damage == 'wrong_tangent':
            group[0].set('x1', str(float(group[0].get('x1'))+1))
        elif damage == 'wrong_width':
            curve.set('stroke-width', '3')
        elif damage == 'wrong_paint':
            curve.set('stroke', '#224477')
        elif damage == 'wrong_transform':
            group.set('transform', group.get('transform', '')+' translate(2 0)')
        elif damage == 'wrong_depth':
            group.remove(cover)
            group.insert(3, cover)
        elif damage.startswith('wrong_arc_'):
            values = ellipse.get('d').split()
            slot = {'wrong_arc_sweep':8, 'wrong_arc_large':7, 'wrong_arc_rotation':6, 'wrong_arc_radius':4}[damage]
            if damage in {'wrong_arc_sweep','wrong_arc_large'}:
                values[slot] = str(1-int(values[slot]))
            else:
                values[slot] = str(float(values[slot])+4)
            ellipse.set('d', ' '.join(values))
        elif damage == 'filled_curve':
            curve.set('fill', 'black')
        elif damage == 'compound_path':
            curve.set('d', curve.get('d')+' M4 4 Q5 2 6 4')
        else:
            cover.set('opacity', '.5')
        yield dict(damage=damage, hidden=damage.startswith('hidden_'), svg=ET.tostring(root, encoding='unicode'))
