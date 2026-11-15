"""Independent visible development constructions, without converter imports."""
import copy
import math


def cases():
    for degree in (2, 3):
        for variant, angle, scale, color in [(0, 0, 1, '#224466'), (1, 90, .85, '#993355'),
                                             (2, 180, 1.1, '#397a46')]:
            def point(p):
                x, y = (p[0]-64)*scale, (p[1]-64)*scale
                c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
                return [64+c*x-s*y, 64+s*x+c*y]
            # Axis-linear Bezier graphs with a tangent straight lead.
            pts = ([[32,40], [32,64], [80,88]] if degree == 2 else
                   [[32,40], [32,56], [44,72], [80,88]])
            pts = [point(p) for p in pts]
            lead = [point([32,20]), pts[0]]
            width = 2.4*scale
            command = 'Q' if degree == 2 else 'C'
            path = 'M '+' '.join(map(str,pts[0]))+' '+command+' '+' '.join(str(v) for p in pts[1:] for v in p)
            body = (f'<line x1="{lead[0][0]}" y1="{lead[0][1]}" x2="{lead[1][0]}" y2="{lead[1][1]}" '
                    f'stroke="{color}" stroke-width="{width}"/>'
                    f'<path d="{path}" stroke="{color}" stroke-width="{width}" fill="none"/>')
            header = '<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><rect width="128" height="128" fill="white"/>'
            annotation = dict(schema='independent_curve_scene_v1', size=[128,128], complete_inventory=True,
                limits=dict(position=.05, color=0, stroke_width=.01, angle=.01), objects=[
                    dict(id='background',kind='rect',points=[[0,0],[128,0],[128,128],[0,128]],fill='white'),
                    dict(id='lead',kind='line',points=copy.deepcopy(lead),stroke=color,stroke_width=width),
                    dict(id='curve',kind='quadratic' if degree == 2 else 'cubic',points=pts,stroke=color,stroke_width=width)],
                relations=[dict(kind='endpoints_meet',objects=['lead','curve'],tolerance=.01),
                           dict(kind='tangent_join',objects=['lead','curve'],tolerance=.01,angle_tolerance=.1)])
            yield dict(case_id=f'visible_{command}_{variant}', width=128, height=128, svg=header+body+'</svg>',
                seed_svg=header+'</svg>', annotation=annotation,
                description='Eine offene farbige Kurve mit einer tangential angeschlossenen geraden Linie auf weissem Hintergrund.',
                regions=[dict(name='lead',box=[max(0,int(min(p[0] for p in lead))-3), max(0,int(min(p[1] for p in lead))-3),
                    int(abs(lead[1][0]-lead[0][0]))+7,int(abs(lead[1][1]-lead[0][1]))+7])])
