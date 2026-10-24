"""Independent synthetic development scenes for overlap inside a gradient circle."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
from xml.etree import ElementTree as ET

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.run_plan_b_variations import make_original_case, make_variations, write_cases


def make_cases(seed=713849, *, rounded=False, outlined=False, children=2, same_fill=False):
    if children not in range(2, 9):
        raise ValueError('Overlap scenes support two to eight children')
    rng = random.Random(seed)
    cases = []
    for index in range(12):
        width, height = (210, 200) if children <= 4 else (300, 300)
        parent_radius = 85 if children <= 4 else 130
        parent_x, parent_y = width/2, height/2
        axis = index % 2
        first, last = rng.choice([('#bbd9eb', '#6198b3'), ('#cee2cc', '#76a68b')])
        palette = rng.sample(['#284d79', '#a04753', '#486d31', '#7851a3'], 2)
        x, y = rng.uniform(62, 69), rng.uniform(57, 64)
        w, h = rng.uniform(49, 55), rng.uniform(43, 49)
        dx, dy = rng.uniform(24, 30), rng.uniform(19, 25)
        boxes = [[x, y, w, h], [x+dx, y+dy, w-5, h+4]]
        if index % 3 == 1:
            boxes = [[210-a-c, b, c, d] for a, b, c, d in boxes]
        elif index % 3 == 2:
            boxes = [[a, 200-b-d, c, d] for a, b, c, d in boxes]
        if index % 4 >= 2:
            boxes.reverse()
        if children > 2:
            # Independent reference geometry, including chain and triple
            # intersections. Paint order is deliberately unrelated to x.
            step = (120/(children-1) if children > 4 else
                    23 if children == 4 else (18 if index % 2 else 29))
            size = 50 if children > 4 else 42 if children == 4 else 57
            start = parent_x-(size+(children-1)*step)/2
            boxes = [[start+i*step, start-5+i*step, size, size] for i in range(children)]
            if index % 3 == 1:
                boxes = [[width-a-c, b, c, d] for a, b, c, d in boxes]
            if index % 3 == 2:
                boxes = [[a, height-b-d, c, d] for a, b, c, d in boxes]
            if index % 4 >= 2:
                boxes.reverse()
            if index % 4 == 1:
                boxes = boxes[1:]+boxes[:1]
            paints = ['#284d79', '#a04753', '#486d31', '#7851a3']
            if children > 4:
                paints += ['#997b21', '#277c83', '#9c386f', '#4a3e28']
            palette = rng.sample(paints, children)
        objects = [dict(kind='circle', bbox=[parent_x-parent_radius, parent_y-parent_radius,
                                           2.*parent_radius, 2.*parent_radius], parent=None,
                        gradient_axis=axis, stroke_width=0)]
        shapes = [f'<circle cx="{parent_x:g}" cy="{parent_y:g}" r="{parent_radius}" fill="url(#fixture)"/>']
        for i, (box, fill) in enumerate(zip(boxes, palette)):
            a, b, c, d = box
            corner = rng.uniform(4., 9.) if rounded else 0.
            radius = f' rx="{corner}"' if rounded else ''
            shapes.append(f'<rect x="{a}" y="{b}" width="{c}" height="{d}"{radius} fill="{fill}"/>')
            objects.append(dict(kind='rectangle', bbox=box, parent=0, stroke_width=0,
                                **({'corner_radius': corner} if rounded else {}),
                                **({'behind': i+2} if i < children-1 else {})))
        if children > 2:
            for i, obj in enumerate(objects[1:]):
                obj.pop('behind', None)
                a, b, c, d = boxes[i]
                obj['behind_all'] = [j+1 for j in range(i+1, children)
                    if min(a+c, boxes[j][0]+boxes[j][2]) > max(a, boxes[j][0])
                    and min(b+d, boxes[j][1]+boxes[j][3]) > max(b, boxes[j][1])]
        end = 'x2="0%" y2="100%"' if axis else 'x2="100%" y2="0%"'
        defs = f'<defs><linearGradient id="fixture" x1="0%" y1="0%" {end}><stop offset="0" stop-color="{first}"/><stop offset="1" stop-color="{last}"/></linearGradient></defs>'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">{defs}<rect width="{width}" height="{height}" fill="white"/>'+''.join(shapes)+'</svg>'
        description = ('Ein gefüllter Kreis und zwei gefüllte Rechtecke. '
                       f'Der Kreis hat einen {"vertikalen" if axis else "horizontalen"} Farbverlauf. '
                       'Die Rechtecke liegen innerhalb des Kreises und überlappen sich teilweise. '
                       'Keine Beschriftung.')
        if children > 2:
            description = description.replace('zwei', {3: 'drei', 4: 'vier', 5: 'fünf',
                6: 'sechs', 7: 'sieben', 8: 'acht'}[children])
        if rounded:
            description = description.replace('Rechtecke.', 'Rechtecke mit leicht gerundeten Ecken.')
        cases.append(dict(case_id=f'{"multi"+str(children)+"_" if children > 2 else ""}{"rounded_" if rounded else ""}overlap_{index:02d}', width=width, height=height,
                          svg=svg, description=description, expected_objects=objects))
    if outlined:
        for index, case in enumerate(cases):
            root = ET.fromstring(case['svg'])
            for element, obj in zip(list(root)[2:], case['expected_objects']):
                sw = (1. if obj['kind'] == 'circle' else 1.5) + .25*(index % 3)
                element.set('stroke', '#f3f0ed')
                element.set('stroke-width', str(sw))
                x, y, w, h = obj['bbox']
                obj.update(bbox=[x-sw/2, y-sw/2, w+sw, h+sw], stroke_width=sw)
            case.update(case_id='outlined_'+case['case_id'],
                        svg=ET.tostring(root, encoding='unicode'),
                        description=case['description']+' Die Formen haben helle Konturen.')
    if same_fill:
        for case in cases:
            root = ET.fromstring(case['svg'])
            children_elements = list(root)[3:]
            fill = children_elements[0].get('fill')
            for element in children_elements:
                element.set('fill', fill)
            case.update(case_id='same_paint_'+case['case_id'],
                        svg=ET.tostring(root, encoding='unicode'))
    return cases


def make_variation_cases(seed=713849, *, rounded=False, outlined=False, children=2, same_fill=False):
    source = make_cases(seed, rounded=rounded, outlined=outlined, children=children, same_fill=same_fill)[3]
    cases = [make_original_case(source['svg'], source['description']),
             *make_variations(source['svg'], source['description'], seed)]
    for case in cases:
        scale = case['variation']['scale']
        dx, dy = case['variation']['relative_x'], case['variation']['relative_y']
        w, h = source['width'], source['height']
        case['expected_objects'] = [dict(obj, bbox=[
            w/2+scale*(obj['bbox'][0]-w/2)+dx*w,
            h/2+scale*(obj['bbox'][1]-h/2)+dy*h,
            scale*obj['bbox'][2], scale*obj['bbox'][3]],
            stroke_width=scale*obj['stroke_width'],
            **({'corner_radius': scale*obj['corner_radius']} if 'corner_radius' in obj else {}))
            for obj in source['expected_objects']]
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--seed', type=int, default=713849)
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--rounded', action='store_true')
    parser.add_argument('--outlines', action='store_true')
    parser.add_argument('--same-fill', action='store_true')
    parser.add_argument('--children', type=int, choices=range(2, 9), default=2)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--rename', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        args.prepare.mkdir(parents=True, exist_ok=False)
        cases = make_cases(args.seed, rounded=args.rounded, outlined=args.outlines, children=args.children,
                           same_fill=args.same_fill)
        if args.variations:
            cases = make_variation_cases(args.seed, rounded=args.rounded,
                                         outlined=args.outlines, children=args.children, same_fill=args.same_fill)
        write_cases(cases, args.prepare)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (args.prepare/'generation.json').write_text(json.dumps(dict(
            seed=args.seed, children=args.children, rounded=args.rounded,
            outlines=args.outlines, variations=args.variations, same_fill=args.same_fill), indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required')
    fn = verify_report if args.verify_only else evaluate_cases
    summary = fn(args.inputs, args.output, require_all=args.require_all,
                 **({} if args.verify_only else {'rename': args.rename}))
    print(f"Verified: {summary['accepted']}/{summary['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
