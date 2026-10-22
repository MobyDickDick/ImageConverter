"""Independent rounded-rectangle sources for the supervised production CLI.

Reference geometry is generated outside production and never read by the
conversion worker. Real families are explicitly known development examples.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.evaluate_real_scene import prepare_real
from tools.run_plan_b_variations import write_cases, make_original_case, make_variations


def make_cases(seed=262210, count=12):
    rng = random.Random(seed)
    cases = []
    for index in range(count):
        width, height = 210, 130
        nested, separate = index % 3 == 0, index % 3 == 2
        axis = index % 2
        outlined = index % 4 == 1
        objects, definitions, shapes = [], [], []
        n = 2 if nested or separate else 1
        for j in range(n):
            sw = 2. if outlined else 0.
            if nested and j:
                x, y, w, h = 31., 39., rng.uniform(75, 115), 50.
            elif separate:
                x, y, w, h = 14.+j*102, rng.uniform(18, 26), 80., rng.uniform(72, 82)
            else:
                x, y, w, h = 13., 17., 181., 95.
            radius = rng.uniform(3., 9.)
            end = 'x2="0%" y2="100%"' if axis else 'x2="100%" y2="0%"'
            colors = rng.choice([('#3b718b', '#b6d5e3'), ('#56886c', '#c5ded0'), ('#6e507b', '#c7b1d4')])
            definitions.append(f'<linearGradient id="paint{j}" x1="0%" y1="0%" {end}><stop offset="0" stop-color="{colors[0]}"/><stop offset="1" stop-color="{colors[1]}"/></linearGradient>')
            fill = '#ffffff' if nested and j else f'url(#paint{j})'
            shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="#303030" stroke-width="{sw}"/>')
            objects.append(dict(kind='rectangle', bbox=[x-sw/2, y-sw/2, w+sw, h+sw], parent=0 if nested and j else None,
                                corner_radius=radius, stroke_width=sw))
            if nested and j:
                objects[-1]['fill'] = '#ffffff'
            else:
                objects[-1]['gradient_axis'] = axis
        direction = 'vertikalen' if axis else 'horizontalen'
        if nested:
            description = ('Zwei gefüllte Rechtecke mit leicht gerundeten Ecken. Die Formen sind ineinander verschachtelt. '
                           f'Die äußere Form hat einen {direction} Farbverlauf. Die innere Form ist weiß.')
        elif separate:
            description = ('Zwei gefüllte Rechtecke mit leicht gerundeten Ecken. Die Formen liegen getrennt nebeneinander. '
                           f'Jede Form hat einen {direction} Farbverlauf.')
        else:
            description = f'Ein gefülltes Rechteck mit leicht gerundeten Ecken und {direction[:-2]}em Farbverlauf.'
        if outlined:
            description += ' Jede Form hat eine dunkle Kontur.'
        description += ' Keine Beschriftung.'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><defs>'+''.join(definitions)+f'</defs><rect width="{width}" height="{height}" fill="white"/>'+''.join(shapes)+'</svg>'
        cases.append(dict(case_id=f'gradient_{index:02d}', width=width, height=height, svg=svg,
                          description=description, expected_objects=objects))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--real', action='store_true')
    parser.add_argument('--seed', type=int, default=262210)
    parser.add_argument('--count', type=int, default=12)
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--paraphrase', action='store_true')
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--require-all', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--rename', action='store_true')
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    if args.prepare:
        if args.real:
            prepare_real(args.prepare, Path('config/gradient_scene_families.json'))
        else:
            cases = make_cases(args.seed, args.count)
            if args.paraphrase:
                for case in cases:
                    case['description'] = case['description'].replace('Keine Beschriftung.', 'Ohne Text oder Zeichen.')
            if args.variations:
                source = cases[0]
                cases = [make_original_case(source['svg'], source['description']),
                         *make_variations(source['svg'], source['description'], args.seed)]
                for case in cases:
                    v = case['variation']
                    s, dx, dy = v['scale'], v['relative_x'], v['relative_y']
                    w, h = source['width'], source['height']
                    case['expected_objects'] = [dict(o, corner_radius=s*o['corner_radius'], stroke_width=s*o['stroke_width'], bbox=[
                        w/2+s*(o['bbox'][0]-w/2)+dx*w, h/2+s*(o['bbox'][1]-h/2)+dy*h,
                        s*o['bbox'][2], s*o['bbox'][3]]) for o in source['expected_objects']]
            args.prepare.mkdir(parents=True, exist_ok=False)
            write_cases(cases, args.prepare)
            (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required')
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    fn = verify_report if args.verify_only else evaluate_cases
    kwargs = {} if args.verify_only else dict(rename=args.rename)
    summary = fn(args.inputs, args.output, require_all=args.require_all, **kwargs)
    print(f"Verified: {summary['accepted']}/{summary['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
