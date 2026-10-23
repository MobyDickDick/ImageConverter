"""Synthetic subpixel-gap scenes, independent of the residual detector."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.evaluate_structure_operators import make_cases as edit_cases
from tools.run_plan_b_variations import make_original_case, make_variations, write_cases


def make_cases(seed=731902):
    rng = random.Random(seed)
    cases = []
    for index in range(12):
        width, height = 210, 200
        cx, cy, radius = 105., 100., 82.
        axis, vertical = index % 2, (index // 2) % 2
        count = 2 + index // 8
        size = rng.uniform(15, 21)
        gap = rng.uniform(.6, .95)
        start = (cy if vertical else cx) - (count*size+(count-1)*gap)/2 + rng.uniform(-.4, .4)
        first, last, fill = rng.choice([
            ('#bbd9eb', '#6198b3', '#2a5471'),
            ('#cee2cc', '#76a68b', '#315e40'),
            ('#e3d0e9', '#9a72b6', '#684074')])
        end = 'x2="0%" y2="100%"' if axis else 'x2="100%" y2="0%"'
        shapes = [f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="url(#fixture)"/>']
        objects = [dict(kind='circle', bbox=[cx-radius, cy-radius, 2*radius, 2*radius],
                        parent=None, gradient_axis=axis, stroke_width=0)]
        for j in range(count):
            x = cx-11.3 if vertical else start+j*(size+gap)
            y = start+j*(size+gap) if vertical else cy-11.3
            w, h = (22.6, size) if vertical else (size, 22.6)
            shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
            objects.append(dict(kind='rectangle', bbox=[x, y, w, h], parent=0, stroke_width=0))
        definitions = f'<defs><linearGradient id="fixture" {end}><stop stop-color="{first}"/><stop offset="1" stop-color="{last}"/></linearGradient></defs>'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">{definitions}<rect width="{width}" height="{height}" fill="white"/>'+''.join(shapes)+'</svg>'
        description = (f'Ein gefüllter Kreis und {count} gefüllte Rechtecke. Der Kreis hat einen '
                       f'{"vertikalen" if axis else "horizontalen"} Farbverlauf. '
                       'Die Rechtecke liegen innerhalb des Kreises und getrennt '
                       f'{"untereinander" if vertical else "nebeneinander"}. Keine Beschriftung.')
        cases.append(dict(case_id=f'split_{index:02d}', width=width, height=height,
                          svg=svg, description=description, expected_objects=objects))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--seed', type=int, default=731902)
    parser.add_argument('--include-edits', action='store_true')
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--rename', action='store_true')
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        args.prepare.mkdir(parents=True, exist_ok=False)
        cases = make_cases(args.seed) + (edit_cases() if args.include_edits else [])
        if args.variations:
            source = cases[0]
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
    if args.verify_only:
        summary = verify_report(args.inputs, args.output, require_all=args.require_all)
    else:
        summary = evaluate_cases(args.inputs, args.output, rename=args.rename, require_all=args.require_all)
    print(f"Verified: {summary['accepted']}/{summary['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
