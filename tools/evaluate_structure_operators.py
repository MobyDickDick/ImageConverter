"""Synthetic development matrix for native scene edits; no real-family claim."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.run_plan_b_variations import write_cases


def make_cases(seed=20261024):
    rng = random.Random(seed)
    cases = []
    for index in range(8):
        width, height = 190, 180
        cx, cy, radius = 95., 90., 73.
        axis = index % 2
        first, last = '#bbd9eb', '#6198b3'
        end = 'x2="0%" y2="100%"' if axis else 'x2="100%" y2="0%"'
        definitions = f'<defs><linearGradient id="fixture" {end}><stop stop-color="{first}"/><stop offset="1" stop-color="{last}"/></linearGradient></defs>'
        shapes = [f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="url(#fixture)"/>']
        objects = [dict(kind='circle', bbox=[cx-radius, cy-radius, 2*radius, 2*radius],
                        parent=None, gradient_axis=axis, stroke_width=0)]
        if index < 4:
            # Adjacent dark shapes need a higher segmentation threshold;
            # the pale third shape needs a lower one. No one decomposition
            # supplies the complete native scene.
            offset = rng.uniform(-1, 1)
            children = [('rectangle', [75.3+offset, 69.2, 18., 20.], '#2a5471'),
                        ('rectangle', [94.+offset, 69.2, 18., 20.], '#2a5471'),
                        ('rectangle', [81.4, 111.3, 23., 18.], '#6d94ac' if axis == 0 else '#5d8ba4')]
        else:
            kinds = [('circle', 'rectangle'), ('circle', 'circle'),
                     ('rectangle', 'circle', 'rectangle'), ('circle', 'rectangle', 'circle')][index-4]
            children = []
            for j, kind in enumerate(kinds):
                size = rng.uniform(19, 23)
                x = 95+(j-(len(kinds)-1)/2)*34-size/2
                children.append((kind, [x, 90-size/2, size, size if kind == 'circle' else 25.],
                                 ['#285472', '#3e5e40', '#67456d'][j]))
        for kind, (x, y, w, h), color in children:
            if kind == 'circle':
                shapes.append(f'<circle cx="{x+w/2}" cy="{y+h/2}" r="{w/2}" fill="{color}"/>')
            else:
                shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')
            objects.append(dict(kind=kind, bbox=[x, y, w, h], parent=0, stroke_width=0))
        counts = {kind: sum(child[0] == kind for child in children) for kind in ('circle', 'rectangle')}
        nouns = []
        for kind, singular, plural in [('circle', 'Kreis', 'Kreise'), ('rectangle', 'Rechteck', 'Rechtecke')]:
            n = counts[kind]
            if n:
                nouns.append(f'{"ein" if n == 1 else n} gefüllt{ "er" if kind == "circle" and n == 1 else "es" if n == 1 else "e"} {singular if n == 1 else plural}')
        if counts['circle']:
            description = ('Ein gefüllter Kreis und '+' und '.join(nouns)+'. Der äußere Kreis hat einen '
                           f'{"horizontalen" if axis == 0 else "vertikalen"} Farbverlauf. '
                           'Die inneren Formen liegen innerhalb des äußeren Kreises und getrennt voneinander. Keine Beschriftung.')
        else:
            description = (f'Ein gefüllter Kreis und {len(children)} gefüllte Rechtecke. Der Kreis hat einen '
                           f'{"horizontalen" if axis == 0 else "vertikalen"} Farbverlauf. '
                           'Die Rechtecke liegen innerhalb des Kreises und getrennt voneinander. Keine Beschriftung.')
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">{definitions}<rect width="{width}" height="{height}" fill="white"/>'+''.join(shapes)+'</svg>'
        cases.append(dict(case_id=f'edit_{index:02d}', width=width, height=height, svg=svg,
                          description=description, expected_objects=objects))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--seed', type=int, default=20261024)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-only', action='store_true')
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
    summary = (verify_report if args.verify_only else evaluate_cases)(args.inputs, args.output)
    print(f"Verified: {summary['accepted']}/{summary['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
