"""Independent synthetic development scenes for overlap inside a gradient circle."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.run_plan_b_variations import make_original_case, make_variations, write_cases


def make_cases(seed=713849):
    rng = random.Random(seed)
    cases = []
    for index in range(12):
        width, height = 210, 200
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
        objects = [dict(kind='circle', bbox=[20., 15., 170., 170.], parent=None,
                        gradient_axis=axis, stroke_width=0)]
        shapes = ['<circle cx="105" cy="100" r="85" fill="url(#fixture)"/>']
        for i, (box, fill) in enumerate(zip(boxes, palette)):
            a, b, c, d = box
            shapes.append(f'<rect x="{a}" y="{b}" width="{c}" height="{d}" fill="{fill}"/>')
            objects.append(dict(kind='rectangle', bbox=box, parent=0, stroke_width=0,
                                **({'behind': 2} if i == 0 else {})))
        end = 'x2="0%" y2="100%"' if axis else 'x2="100%" y2="0%"'
        defs = f'<defs><linearGradient id="fixture" x1="0%" y1="0%" {end}><stop offset="0" stop-color="{first}"/><stop offset="1" stop-color="{last}"/></linearGradient></defs>'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">{defs}<rect width="{width}" height="{height}" fill="white"/>'+''.join(shapes)+'</svg>'
        description = ('Ein gefüllter Kreis und zwei gefüllte Rechtecke. '
                       f'Der Kreis hat einen {"vertikalen" if axis else "horizontalen"} Farbverlauf. '
                       'Die Rechtecke liegen innerhalb des Kreises und überlappen sich teilweise. '
                       'Keine Beschriftung.')
        cases.append(dict(case_id=f'overlap_{index:02d}', width=width, height=height,
                          svg=svg, description=description, expected_objects=objects))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--seed', type=int, default=713849)
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--rename', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        args.prepare.mkdir(parents=True, exist_ok=False)
        cases = make_cases(args.seed)
        if args.variations:
            source = cases[3]
            cases = [make_original_case(source['svg'], source['description']),
                     *make_variations(source['svg'], source['description'], args.seed)]
            for case in cases:
                scale = case['variation']['scale']
                dx, dy = case['variation']['relative_x'], case['variation']['relative_y']
                w, h = source['width'], source['height']
                case['expected_objects'] = [dict(obj, bbox=[
                    w/2+scale*(obj['bbox'][0]-w/2)+dx*w,
                    h/2+scale*(obj['bbox'][1]-h/2)+dy*h,
                    scale*obj['bbox'][2], scale*obj['bbox'][3]]) for obj in source['expected_objects']]
        write_cases(cases, args.prepare)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
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
