"""Independent development scenes for residual hypotheses, never real holdouts."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.run_plan_b_variations import write_cases


def make_cases(seed=20261023):
    rng = random.Random(seed)
    cases = []
    # Layouts are fixture geometry, not converter presets. Include the same
    # two-child topology at low contrast to expose single-threshold failure.
    for index, (rows, columns) in enumerate([(2, 1), (3, 1), (1, 3), (2, 2), (2, 3), (3, 2), (1, 2), (1, 1), (1, 2)]):
        width, height = 190, 180
        cx, cy, radius = 95+rng.uniform(-2, 2), 90+rng.uniform(-2, 2), 73.
        axis = index % 2
        low_contrast = index in (6, 7)
        first, last, fill = (('#80a3b7', '#90b3c7', '#7295a9') if low_contrast
                             else rng.choice([('#bbd9eb', '#6198b3', '#27506b'),
                                              ('#c9dfce', '#6faa87', '#325b41')]))
        if index == 8:
            first, last, fill = '#bbd9eb', '#6198b3', '#2a5471'
        end = 'x2="0%" y2="100%"' if axis else 'x2="100%" y2="0%"'
        gradient = f'<defs><linearGradient id="fixture" {end}><stop stop-color="{first}"/><stop offset="1" stop-color="{last}"/></linearGradient></defs>'
        shapes = [f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="url(#fixture)"/>']
        objects = [dict(kind='circle', bbox=[cx-radius, cy-radius, 2*radius, 2*radius],
                        parent=None, gradient_axis=axis, stroke_width=0)]
        for row in range(rows):
            for column in range(columns):
                w, h = rng.uniform(15, 19), rng.uniform(17, 21)
                x, y = cx+(column-(columns-1)/2)*29-w/2, cy+(row-(rows-1)/2)*29-h/2
                if index == 8:
                    # A subpixel gap: low residual thresholds can connect the
                    # antialias fringes of two genuinely separate rectangles.
                    x, y, w, h = (75.3 if column == 0 else 94.), 80.2, 18., 20.
                shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
                objects.append(dict(kind='rectangle', bbox=[x, y, w, h], parent=0, stroke_width=0))
        number = rows*columns
        noun = 'ein gefülltes Rechteck' if number == 1 else f'{number} gefüllte Rechtecke'
        relation = (' und getrennt nebeneinander' if rows == 1 and number > 1 else
                    ' und getrennt untereinander' if columns == 1 and number > 1 else
                    ' und getrennt voneinander' if number > 1 else '')
        description = (f'Ein gefüllter Kreis und {noun}. Der Kreis hat einen '
                       f'{"horizontalen" if axis == 0 else "vertikalen"} Farbverlauf. '
                       f'Die Rechtecke liegen innerhalb des Kreises{relation}. Keine Beschriftung.')
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">{gradient}<rect width="{width}" height="{height}" fill="white"/>'+''.join(shapes)+'</svg>'
        cases.append(dict(case_id=f'residual_{index:02d}', width=width, height=height, svg=svg,
                          description=description, expected_objects=objects))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--seed', type=int, default=20261023)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        args.prepare.mkdir(parents=True, exist_ok=False)
        cases = make_cases(args.seed)
        write_cases(cases, args.prepare)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required')
    fn = verify_report if args.verify_only else evaluate_cases
    summary = fn(args.inputs, args.output, require_all=args.require_all)
    print(f"Verified: {summary['accepted']}/{summary['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
