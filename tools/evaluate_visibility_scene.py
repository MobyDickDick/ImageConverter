"""Generate independent outlined, mixed-topology and explicit-depth CLI fixtures."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.run_plan_b_variations import write_cases, make_original_case, make_variations


def make_cases(seed=20261021, count=12, paraphrase=False):
    rng = random.Random(seed)
    cases = []
    for i in range(count):
        width, height = rng.choice([(240, 200), (260, 220), (250, 210)])
        size = min(width, height)*rng.uniform(.41, .46)
        combined = i % 3 == 2
        outlined = i % 3 != 1
        kinds = [('circle', 'circle'), ('rectangle', 'rectangle'),
                 ('circle', 'rectangle'), ('rectangle', 'circle')][i % 4]
        centers = [(width*.40, height*.42), (width*.40+size*.56, height*.42+size*.36)]
        sizes = [size, size*.77]
        if combined:
            centers.append((width*.40-size*.18, height*.42-size*.12))
            sizes.append(size*.22)
        palette = rng.sample(['#3169ac', '#d88032', '#3e9866', '#994888'], len(centers))
        shapes, objects = [], []
        sw = rng.uniform(2.2, 3.8) if outlined else 0.
        for j, ((cx, cy), s) in enumerate(zip(centers, sizes)):
            kind = kinds[j] if j < 2 else rng.choice(['circle', 'rectangle'])
            w, h = s, s if kind == 'circle' else s*rng.uniform(.91, 1.04)
            style = f'fill="{palette[j]}" stroke="#303030" stroke-width="{sw}"'
            shapes.append(f'<circle cx="{cx}" cy="{cy}" r="{w/2}" {style}/>' if kind == 'circle' else
                          f'<rect x="{cx-w/2}" y="{cy-h/2}" width="{w}" height="{h}" {style}/>')
            objects.append(dict(kind=kind, stroke_width=sw, bbox=[cx-w/2-sw/2, cy-h/2-sw/2, w+sw, h+sw],
                                parent=None if j == 0 else 0))
        nouns = []
        for kind, noun, plural in [('circle', 'Kreis', 'Kreise'), ('rectangle', 'Rechteck', 'Rechtecke')]:
            n = sum(o['kind'] == kind for o in objects)
            if n:
                nouns.append(f"{['', 'ein', 'zwei', 'drei'][n]} {noun if n == 1 else plural}")
        text = ' und '.join(nouns)+'. Alle Formen sind einfarbig gefüllt. Die Formen überlappen teilweise.'
        if combined:
            text += ' Die kleinste Form liegt innerhalb der größten Form.'
            text += (' Die größte Form liegt hinter der mittelgroßen Form.' if paraphrase else
                     ' Die mittelgroße Form liegt vor der größten Form.')
        else:
            text += (' Die größere Form liegt hinter der kleineren Form.' if paraphrase else
                     ' Die kleinere Form liegt vor der größeren Form.')
        if outlined:
            text += ' Jede Form hat eine dunkle Kontur.'
        text += ' Ohne Text oder Zeichen. Auf weißem Hintergrund.' if paraphrase else ' Keine Beschriftung.'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="{width}" height="{height}" fill="white"/>'+''.join(shapes)+'</svg>'
        cases.append(dict(case_id=f'visibility_{i:02d}', width=width, height=height, svg=svg,
                          description=text, expected_objects=objects))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seed', type=int, default=20261021)
    parser.add_argument('--count', type=int, default=12)
    for flag in ('paraphrase', 'rotate', 'variations', 'rename', 'verify-only', 'require-all', 'contradict-depth'):
        parser.add_argument('--'+flag, action='store_true')
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        args.prepare.mkdir(parents=True, exist_ok=False)
        cases = make_cases(args.seed, args.count, args.paraphrase)
        if args.contradict_depth:
            for case in cases:
                if args.paraphrase:
                    case['description'] = case['description'].replace('liegt hinter der', 'liegt vor der')
                else:
                    case['description'] = case['description'].replace('liegt vor der', 'liegt hinter der')
        if args.rotate:
            from tools.evaluate_primitive_scene import rotate_cases
            cases = rotate_cases(cases)
        if args.variations:
            source = cases[2] if len(cases) > 2 else cases[0]
            cases = [make_original_case(source['svg'], source['description']),
                     *make_variations(source['svg'], source['description'], args.seed)]
            for case in cases:
                v = case['variation']
                s, dx, dy = v['scale'], v['relative_x'], v['relative_y']
                w, h = source['width'], source['height']
                case['expected_objects'] = [dict(o, stroke_width=s*o['stroke_width'], bbox=[
                    w/2+s*(o['bbox'][0]-w/2)+dx*w, h/2+s*(o['bbox'][1]-h/2)+dy*h,
                    s*o['bbox'][2], s*o['bbox'][3]]) for o in source['expected_objects']]
        write_cases(cases, args.prepare)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (args.prepare/'generation.json').write_text(json.dumps(vars(args), default=str, indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required')
    run = verify_report if args.verify_only else evaluate_cases
    options = {} if args.verify_only else dict(rename=args.rename)
    result = run(args.inputs, args.output, require_all=args.require_all, **options)
    print(f"Verified: {result['accepted']}/{result['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
