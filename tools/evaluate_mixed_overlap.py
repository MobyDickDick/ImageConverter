"""Independent circle/rectangle overlap fixtures for the shared gradient search."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
from xml.etree import ElementTree as ET

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.run_plan_b_variations import make_original_case, make_variations, write_cases


def make_cases(seed=486213, *, rounded=False, outlined=False, children=None, repeat_fill=False,
               same_fill=False):
    if children is not None and children not in range(2, 9):
        raise ValueError('Mixed overlap scenes support two to eight children')
    rng = random.Random(seed)
    cases = []
    for index in range(12):
        width = height = 360 if children and children > 4 else 240
        count = children or 2 + index // 4
        axis = index % 2
        boxes = [[65+i*22+rng.uniform(-1, 1), 60+i*20+rng.uniform(-1, 1),
                  rng.uniform(49, 53), rng.uniform(49, 53)] for i in range(count)]
        if count > 4:
            start = (width-52-(count-1)*24)/2
            boxes = [[start+i*24+rng.uniform(-1, 1), start-5+i*24+rng.uniform(-1, 1),
                      rng.uniform(49, 53), rng.uniform(49, 53)] for i in range(count)]
        kinds = ['circle' if i % 2 == 0 else 'rectangle' for i in range(count)]
        for box, kind in zip(boxes, kinds):
            if kind == 'circle':
                box[3] = box[2]
        if index % 4 == 1:
            boxes = [[width-x-w, y, w, h] for x, y, w, h in boxes]
        elif index % 4 == 2:
            boxes = [[x, height-y-h, w, h] for x, y, w, h in boxes]
        order = list(range(count))
        if index % 4 >= 2:
            order.reverse()
        palette = rng.sample(['#284d79', '#a04753', '#486d31', '#7851a3',
                              '#997b21', '#277c83', '#9c386f', '#4a3e28'][:max(4, count)], count)
        if repeat_fill:
            if count < 5:
                raise ValueError('Repeated-fill scenes need at least five children')
            palette[4] = palette[0]
        center, radius = width/2, width/2-15
        objects = [dict(kind='circle', bbox=[15., 15., 2*radius, 2*radius], parent=None,
                        gradient_axis=axis, stroke_width=0)]
        shapes = [f'<circle cx="{center:g}" cy="{center:g}" r="{radius:g}" fill="url(#fixture)"/>']
        for i in order:
            x, y, w, h = boxes[i]
            kind, fill = kinds[i], palette[i]
            obj = dict(kind=kind, bbox=boxes[i], parent=0, stroke_width=0)
            if kind == 'circle':
                shapes.append(f'<circle cx="{x+w/2}" cy="{y+h/2}" r="{w/2}" fill="{fill}"/>')
            else:
                radius = rng.uniform(4., 7.) if rounded else 0.
                shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"/>')
                obj['corner_radius'] = radius
            objects.append(obj)
        # Every adjacent pair intersects in this independent diagonal chain;
        # nonadjacent bounding boxes may meet without their silhouettes meeting.
        for i, original in enumerate(order):
            objects[i+1]['behind_all'] = [j+1 for j in range(i+1, count)
                                         if abs(order[j]-original) == 1]
        end = 'x2="0%" y2="100%"' if axis else 'x2="100%" y2="0%"'
        defs = f'<defs><linearGradient id="fixture" {end}><stop stop-color="#bbd9eb"/><stop offset="1" stop-color="#6198b3"/></linearGradient></defs>'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">{defs}<rect width="{width}" height="{height}" fill="white"/>'+''.join(shapes)+'</svg>'
        circles = kinds.count('circle')+1
        rectangles = kinds.count('rectangle')
        rounding = ' mit leicht gerundeten Ecken' if rounded else ''
        description = (f'{circles} gefüllte Kreise und {rectangles} gefüllte Rechtecke{rounding}. '
                       f'Der äussere Kreis hat einen {"vertikalen" if axis else "horizontalen"} Farbverlauf. '
                       'Die inneren Formen liegen innerhalb des äusseren Kreises und überlappen sich teilweise. '
                       'Keine Beschriftung.')
        cases.append(dict(case_id=f'{"multi"+str(children)+"_" if children else ""}{"rounded_" if rounded else ""}mixed_overlap_{index:02d}',
                          width=width, height=height, svg=svg, description=description,
                          expected_objects=objects))
    if outlined:
        for index, case in enumerate(cases):
            root = ET.fromstring(case['svg'])
            for element, obj in zip(list(root)[2:], case['expected_objects']):
                sw = (1. if obj['parent'] is None else 1.5) + .25*(index % 3)
                element.set('stroke', '#f3f0ed')
                element.set('stroke-width', str(sw))
                x, y, w, h = obj['bbox']
                obj.update(bbox=[x-sw/2, y-sw/2, w+sw, h+sw], stroke_width=sw)
            case.update(case_id='outlined_'+case['case_id'],
                        svg=ET.tostring(root, encoding='unicode'),
                        description=case['description']+' Die Formen haben helle Konturen.')
    if same_fill:
        if repeat_fill:
            raise ValueError('Choose repeated or identical child paints')
        for case in cases:
            root = ET.fromstring(case['svg'])
            elements = list(root)[3:]
            for element in elements:
                element.set('fill', elements[0].get('fill'))
            case.update(case_id='same_paint_'+case['case_id'],
                        svg=ET.tostring(root, encoding='unicode'))
    return cases


def make_variation_cases(seed=486213, *, rounded=False, outlined=False, children=None, repeat_fill=False,
                         same_fill=False):
    source = make_cases(seed, rounded=rounded, outlined=outlined, children=children,
                        repeat_fill=repeat_fill, same_fill=same_fill)[3]
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
    parser.add_argument('--seed', type=int, default=486213)
    parser.add_argument('--rounded', action='store_true')
    parser.add_argument('--outlines', action='store_true')
    parser.add_argument('--children', type=int, choices=range(2, 9))
    parser.add_argument('--repeat-fill', action='store_true')
    parser.add_argument('--same-fill', action='store_true')
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--rename', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        cases = (make_variation_cases if args.variations else make_cases)(
            args.seed, rounded=args.rounded, outlined=args.outlines, children=args.children,
            repeat_fill=args.repeat_fill, same_fill=args.same_fill)
        args.prepare.mkdir(parents=True, exist_ok=False)
        write_cases(cases, args.prepare)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (args.prepare/'generation.json').write_text(json.dumps(dict(seed=args.seed, rounded=args.rounded, outlines=args.outlines,
                                                                  variations=args.variations, children=args.children,
                                                                  repeat_fill=args.repeat_fill, same_fill=args.same_fill), indent=2)+'\n', encoding='utf-8')
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
