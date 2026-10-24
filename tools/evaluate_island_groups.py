"""Independent same-paint instances whose visible fills are split by a bridge."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.run_plan_b_variations import make_original_case, make_variations, write_cases


def make_cases(seed=731529, *, rounded=False, outlined=False, children=3):
    if children not in (3, 4):
        raise ValueError('Island fixtures use two or three circles and one bridge')
    rng = random.Random(seed)
    cases = []
    for index in range(12):
        size = 320 if children == 3 else 360
        center = size/2
        radius = center-15
        axis = index % 2
        palette = rng.sample(['#284d79', '#a04753', '#486d31', '#7851a3'], 2)
        boxes = [[center+(i-(children-2)/2)*86-r, center-r+rng.uniform(-1, 1), 2*r, 2*r]
                 for i in range(children-1) for r in [rng.uniform(28, 31)]]
        left, right = boxes[0][0]-12, boxes[-1][0]+boxes[-1][2]+12
        boxes.append([left, center-5+rng.uniform(-1, 1), right-left, rng.uniform(9, 11)])
        if index % 4 >= 2:
            boxes = [[y, x, h, w] for x, y, w, h in boxes]
        sw = (1.5+.25*(index % 3)) if outlined else 0.
        parent_sw = (1.+.25*(index % 3)) if outlined else 0.
        stroke = '#f3f0ed' if outlined else 'none'
        corner = rng.uniform(2., 2.7) if rounded else 0.
        objects = [dict(kind='circle', bbox=[15-parent_sw/2, 15-parent_sw/2,
                        2*radius+parent_sw, 2*radius+parent_sw], parent=None,
                        gradient_axis=axis, stroke_width=parent_sw)]
        shapes = [f'<circle cx="{center}" cy="{center}" r="{radius}" fill="url(#fixture)" '
                  f'stroke="{stroke}" stroke-width="{parent_sw}"/>']
        for i, (x, y, w, h) in enumerate(boxes):
            circle = i < children-1
            style = f'fill="{palette[0 if circle else 1]}" stroke="{stroke}" stroke-width="{sw}"'
            if circle:
                shapes.append(f'<circle cx="{x+w/2}" cy="{y+h/2}" r="{w/2}" {style}/>')
            else:
                shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{corner}" {style}/>')
            obj = dict(kind='circle' if circle else 'rectangle',
                       bbox=[x-sw/2, y-sw/2, w+sw, h+sw], parent=0, stroke_width=sw)
            obj.update(behind_all=[children] if circle else [],
                       **({} if circle else {'corner_radius': corner}))
            objects.append(obj)
        end = 'x2="0%" y2="100%"' if axis else 'x2="100%" y2="0%"'
        defs = f'<defs><linearGradient id="fixture" {end}><stop stop-color="#bbd9eb"/><stop offset="1" stop-color="#6198b3"/></linearGradient></defs>'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">{defs}<rect width="{size}" height="{size}" fill="white"/>'+''.join(shapes)+'</svg>'
        description = (f'{children} gefüllte Kreise und ein gefülltes Rechteck'
                       + (' mit leicht gerundeten Ecken' if rounded else '')
                       + f'. Der äussere Kreis hat einen {"vertikalen" if axis else "horizontalen"} Farbverlauf. '
                       'Die inneren Formen liegen innerhalb des äusseren Kreises und überlappen sich teilweise. '
                       'Keine Beschriftung.' + (' Die Formen haben helle Konturen.' if outlined else ''))
        cases.append(dict(case_id=f'islands_{children}_{index:02d}', width=size, height=size,
                          svg=svg, description=description, expected_objects=objects))
    return cases


def make_variation_cases(seed=731529, **kwargs):
    source = make_cases(seed, **kwargs)[3]
    cases = [make_original_case(source['svg'], source['description']),
             *make_variations(source['svg'], source['description'], seed)]
    for case in cases:
        scale = case['variation']['scale']
        dx, dy = case['variation']['relative_x'], case['variation']['relative_y']
        w, h = source['width'], source['height']
        case['expected_objects'] = [dict(obj, bbox=[
            w/2+scale*(obj['bbox'][0]-w/2)+dx*w,
            h/2+scale*(obj['bbox'][1]-h/2)+dy*h,
            scale*obj['bbox'][2], scale*obj['bbox'][3]], stroke_width=scale*obj['stroke_width'],
            **({'corner_radius': scale*obj['corner_radius']} if 'corner_radius' in obj else {}))
            for obj in source['expected_objects']]
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--seed', type=int, default=731529)
    parser.add_argument('--children', type=int, choices=(3, 4), default=3)
    parser.add_argument('--rounded', action='store_true')
    parser.add_argument('--outlines', action='store_true')
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        cases = (make_variation_cases if args.variations else make_cases)(
            args.seed, rounded=args.rounded, outlined=args.outlines, children=args.children)
        args.prepare.mkdir(parents=True, exist_ok=False)
        write_cases(cases, args.prepare)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (args.prepare/'generation.json').write_text(json.dumps(dict(seed=args.seed, children=args.children,
            rounded=args.rounded, outlines=args.outlines, variations=args.variations), indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required')
    summary = (verify_report if args.verify_only else evaluate_cases)(
        args.inputs, args.output, require_all=args.require_all)
    print(f"Verified: {summary['accepted']}/{summary['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
