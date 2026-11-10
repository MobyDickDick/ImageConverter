"""Synthetic composition of overlapping groups and separately visible shapes.

References and annotations derive only from independent fixture geometry.
No reserved real families or production proposals are read.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.evaluate_mixed_overlap import make_cases as overlap_cases
from tools.run_plan_b_variations import make_original_case, make_variations, write_cases


def make_cases(seed=641927, *, rounded=True, outlined=True, same_fill=False):
    cases = []
    for index in range(12):
        groups, isolated = [(1, 1), (2, 1), (1, 2), (2, 2)][index % 4]
        case = overlap_cases(seed, groups=groups+isolated, rounded=rounded,
                             outlined=outlined, same_fill=same_fill)[index]
        root = ET.fromstring(case['svg'])
        # Spell out SVG defaults so the independent native checker can also
        # verify the reference itself with exactly the output grammar.
        gradient = root[0][0]
        gradient.set('x1', '0%')
        gradient.set('y1', '0%')
        gradient[0].set('offset', '0')
        objects = case['expected_objects']
        # The first pairs overlap; subsequent pairs each lose one member.
        # Source painter order flips; retain the corresponding native indices.
        elements = list(root)[2:]
        keep = [0]
        for i in range(1, len(objects)):
            # The source's native object order is forward for indices 0/1,
            # reversed for 2/3. It is separate from detection or output order.
            original = i-1 if index % 4 < 2 else len(objects)-1-i
            if original < 2*groups or original % 2 == 0:
                keep.append(i)
            else:
                root.remove(elements[i])
        mapping = {old: new for new, old in enumerate(keep)}
        for old in keep[1:]:
            obj = objects[old]
            obj['behind_all'] = [mapping[j] for j in obj['behind_all'] if j in mapping]
        case['expected_objects'] = [objects[i] for i in keep]
        counts = {kind: sum(o['kind'] == kind for o in case['expected_objects'])
                  for kind in ('circle', 'rectangle')}
        nouns = []
        for kind, noun in [('circle', 'Kreise'), ('rectangle', 'Rechtecke')]:
            if counts[kind]:
                suffix = ' mit leicht gerundeten Ecken' if rounded and kind == 'rectangle' else ''
                nouns.append(f'{counts[kind]} gefüllte {noun}{suffix}')
        axis = 'vertikalen' if index % 2 else 'horizontalen'
        case.update(case_id=f'mixed_topology_{index:02d}', svg=ET.tostring(root, encoding='unicode'),
            description=(' und '.join(nouns)+f'. Der äussere Kreis hat einen {axis} Farbverlauf. '
                'Die inneren Formen liegen innerhalb des äusseren Kreises und bilden '
                f'{groups} Überdeckungsgruppe'+('n' if groups > 1 else '')+
                f' sowie {isolated} einzelne Form'+('en' if isolated > 1 else '')+'. '
                'Die Gruppen und einzelnen Formen liegen getrennt voneinander. Keine Beschriftung.'+
                (' Die Formen haben helle Konturen.' if outlined else '')))
        cases.append(case)
    return cases


def make_variation_cases(seed=641927, **options):
    source = make_cases(seed, **options)[3]
    cases = [make_original_case(source['svg'], source['description']),
             *make_variations(source['svg'], source['description'], seed)]
    for case in cases:
        v = case['variation']
        s, dx, dy = v['scale'], v['relative_x'], v['relative_y']
        w, h = source['width'], source['height']
        case['expected_objects'] = [dict(obj, bbox=[
            w/2+s*(obj['bbox'][0]-w/2)+dx*w, h/2+s*(obj['bbox'][1]-h/2)+dy*h,
            s*obj['bbox'][2], s*obj['bbox'][3]], stroke_width=s*obj['stroke_width'],
            **({'corner_radius': s*obj['corner_radius']} if 'corner_radius' in obj else {}))
            for obj in source['expected_objects']]
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--seed', type=int, default=641927)
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--same-fill', action='store_true')
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        cases = (make_variation_cases if args.variations else make_cases)(args.seed, same_fill=args.same_fill)
        args.prepare.mkdir(parents=True, exist_ok=False)
        write_cases(cases, args.prepare)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (args.prepare/'generation.json').write_text(json.dumps(dict(seed=args.seed, variations=args.variations,
            same_fill=args.same_fill), indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required')
    summary = (verify_report if args.verify_only else evaluate_cases)(args.inputs, args.output,
                                                                     require_all=args.require_all)
    print(f"Verified: {summary['accepted']}/{summary['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
