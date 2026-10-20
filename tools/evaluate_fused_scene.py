"""Independent, native-shape partial-occlusion fixtures run through the real CLI."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.run_plan_b_variations import write_cases, make_original_case, make_variations


def make_cases(seed=20261020, count=12, paraphrase=False):
    rng = random.Random(seed)
    cases = []
    for i in range(count):
        width, height = rng.choice([(220, 180), (250, 200), (200, 200)])
        size = min(width, height)*rng.uniform(.32, .40)
        cx, cy = width*.40, height*.44
        # The rear object exposes all four extreme directions; the foreground
        # occludes a corner/arc, rather than asking an oracle to invent a side.
        centers = [(cx, cy), (cx+size*.57, cy+size*.40)]
        if i % 3 == 2:
            centers.append((width*.22, height*.80))
        kinds = [('circle', 'circle'), ('rectangle', 'rectangle'),
                 ('circle', 'rectangle'), ('rectangle', 'circle')][i % 4]
        palette = rng.sample(['#3169ac', '#d88032', '#3e9866', '#994888'], len(centers))
        shapes, objects = [], []
        for j, (x, y) in enumerate(centers):
            kind = kinds[j] if j < 2 else rng.choice(['circle', 'rectangle'])
            w = size if j < 2 else size*.36
            h = w if kind == 'circle' else w*rng.uniform(.85, 1.08)
            if kind == 'circle':
                shape = f'<circle cx="{x}" cy="{y}" r="{w/2}" fill="{palette[j]}"/>'
            else:
                shape = f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" fill="{palette[j]}"/>'
            shapes.append(shape)
            objects.append(dict(kind=kind, bbox=[x-w/2, y-h/2, w, h], parent=None if j != 1 else 0))
        nouns = []
        for kind, singular, plural in [('circle', 'Kreis', 'Kreise'), ('rectangle', 'Rechteck', 'Rechtecke')]:
            n = sum(o['kind'] == kind for o in objects)
            if n:
                nouns.append(f"{['', 'ein', 'zwei', 'drei'][n]} {singular if n == 1 else plural}")
        relation = ('Die Formen überdecken sich teilweise.' if paraphrase else
                    'Die Formen überlappen teilweise.')
        text = ' und '.join(nouns)+'. Alle Formen sind einfarbig gefüllt. '+relation
        text += ' Ohne Text oder Zeichen.' if paraphrase else ' Keine Beschriftung.'
        if paraphrase:
            text += ' '+['Weißer Hintergrund.', 'Auf weißem Hintergrund.', 'Vor einem weißen Hintergrund.'][i % 3]
        if len(centers) == 3:
            text += ' Eine Form liegt getrennt.'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="{width}" height="{height}" fill="white"/>'+''.join(shapes)+'</svg>'
        cases.append(dict(case_id=f'fused_{i:02d}', width=width, height=height,
                          svg=svg, description=text, expected_objects=objects))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seed', type=int, default=20261020)
    parser.add_argument('--count', type=int, default=12)
    parser.add_argument('--paraphrase', action='store_true')
    parser.add_argument('--rotate', action='store_true')
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--rename', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        args.prepare.mkdir(parents=True, exist_ok=False)
        cases = make_cases(args.seed, args.count, args.paraphrase)
        if args.rotate:
            from tools.evaluate_primitive_scene import rotate_cases
            cases = rotate_cases(cases)
        if args.variations:
            source = cases[2] if len(cases) > 2 else cases[0]
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
        (args.prepare/'generation.json').write_text(json.dumps(vars(args), default=str, indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required')
    if args.verify_only:
        result = verify_report(args.inputs, args.output, require_all=args.require_all)
    else:
        result = evaluate_cases(args.inputs, args.output, rename=args.rename, require_all=args.require_all)
    print(f"Verified: {result['accepted']}/{result['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
