"""Independent synthetic development cases for rounded residual composition."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.run_plan_b_variations import make_original_case, make_variations, write_cases


def make_cases(seed=624731):
    rng = random.Random(seed)
    cases = []
    for index in range(12):
        width, height = 210, 200
        cx, cy, radius = 105., 100., 85.
        axis = index % 2
        rows, columns = [(1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (3, 2)][index // 2]
        first, last, fill = rng.choice([
            ('#bbd9eb', '#6198b3', '#2a5471'),
            ('#cee2cc', '#76a68b', '#315e40'),
            ('#e3d0e9', '#9a72b6', '#684074')])
        end = 'x2="0%" y2="100%"' if axis else 'x2="100%" y2="0%"'
        shapes = [f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="url(#fixture)"/>']
        objects = [dict(kind='circle', bbox=[cx-radius, cy-radius, 2*radius, 2*radius],
                        parent=None, gradient_axis=axis, stroke_width=0)]
        for row in range(rows):
            for column in range(columns):
                w, h = rng.uniform(21, 25), rng.uniform(23, 27)
                x = cx+(column-(columns-1)/2)*34-w/2+rng.uniform(-.5, .5)
                y = cy+(row-(rows-1)/2)*35-h/2+rng.uniform(-.5, .5)
                corner = rng.uniform(3.2, 5.8)
                shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{corner}" fill="{fill}"/>')
                objects.append(dict(kind='rectangle', bbox=[x, y, w, h], parent=0,
                                    stroke_width=0, corner_radius=corner))
        n = rows*columns
        relation = (' und getrennt nebeneinander' if rows == 1 and n > 1 else
                    ' und getrennt untereinander' if columns == 1 and n > 1 else
                    ' und getrennt voneinander' if n > 1 else '')
        description = (f'Ein gefüllter Kreis und {n} gefüllte Rechtecke mit leicht gerundeten Ecken. '
                       f'Der Kreis hat einen {"vertikalen" if axis else "horizontalen"} Farbverlauf. '
                       f'Die Rechtecke liegen innerhalb des Kreises{relation}. Keine Beschriftung.')
        definitions = f'<defs><linearGradient id="fixture" {end}><stop stop-color="{first}"/><stop offset="1" stop-color="{last}"/></linearGradient></defs>'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">{definitions}<rect width="{width}" height="{height}" fill="white"/>'+''.join(shapes)+'</svg>'
        cases.append(dict(case_id=f'rounded_{index:02d}', width=width, height=height,
                          svg=svg, description=description, expected_objects=objects))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--seed', type=int, default=624731)
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
                    scale*obj['bbox'][2], scale*obj['bbox'][3]],
                    **({'corner_radius': scale*obj['corner_radius']} if 'corner_radius' in obj else {}))
                    for obj in source['expected_objects']]
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
