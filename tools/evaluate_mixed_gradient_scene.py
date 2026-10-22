"""Independent mixed primitive scenes; real originals use frozen annotations."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.evaluate_real_scene import prepare_real
from tools.run_plan_b_variations import write_cases


def make_cases(seed=6221026, count=12):
    rng = random.Random(seed)
    cases = []
    for index in range(count):
        width, height = rng.choice([(180, 170), (210, 180), (190, 190)])
        radius = min(width, height)*rng.uniform(.36, .40)
        cx, cy = width/2+rng.uniform(-3, 3), height/2+rng.uniform(-3, 3)
        axis, number, outlined = index % 2, 1+(index//2) % 2, index % 3 != 0
        sw = 1.5 if outlined else 0.
        colors = rng.choice([('#bfdde9', '#6399b3', '#1b5876'),
                             ('#c7ded0', '#6eaa89', '#285c40'),
                             ('#d8c5e4', '#a87abd', '#67427f')])
        end = 'x2="0%" y2="100%"' if axis else 'x2="100%" y2="0%"'
        gradient = f'<defs><linearGradient id="paint" x1="0%" y1="0%" {end}><stop offset="0" stop-color="{colors[0]}"/><stop offset="1" stop-color="{colors[1]}"/></linearGradient></defs>'
        shapes = [f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="url(#paint)" stroke="#dce8ec" stroke-width="{sw}"/>']
        objects = [dict(kind='circle', bbox=[cx-radius-sw/2, cy-radius-sw/2, 2*radius+sw, 2*radius+sw],
                        parent=None, gradient_axis=axis, stroke_width=sw)]
        for j in range(number):
            w, h = (radius*.72, radius*.68) if number == 1 else (radius*.24, radius*.8)
            x, y = cx-w/2+(j-.5)*radius*.70 if number == 2 else cx-w/2, cy-h/2
            shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{colors[2]}" stroke="#dce8ec" stroke-width="{sw}"/>')
            objects.append(dict(kind='rectangle', bbox=[x-sw/2, y-sw/2, w+sw, h+sw], parent=0,
                                stroke_width=sw))
        noun = 'ein gefülltes Rechteck' if number == 1 else 'zwei gefüllte Rechtecke'
        direction = 'vertikalen' if axis else 'horizontalen'
        relation = ' und getrennt nebeneinander' if number == 2 else ''
        description = (f'Ein gefüllter Kreis und {noun}. Der Kreis hat einen {direction} Farbverlauf. '
                       f'Die Rechtecke liegen innerhalb des Kreises{relation}. Keine Beschriftung.')
        if outlined:
            description += ' Die Formen haben helle Konturen.'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'+gradient+f'<rect width="{width}" height="{height}" fill="white"/>'+''.join(shapes)+'</svg>'
        cases.append(dict(case_id=f'mixed_{index:02d}', width=width, height=height, svg=svg,
                          description=description, expected_objects=objects))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--real', action='store_true')
    parser.add_argument('--seed', type=int, default=6221026)
    parser.add_argument('--count', type=int, default=12)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--rename', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    if args.prepare:
        if args.real:
            prepare_real(args.prepare, Path(__file__).resolve().parents[1]/'config/mixed_gradient_scene_families.json')
        else:
            cases = make_cases(args.seed, args.count)
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
