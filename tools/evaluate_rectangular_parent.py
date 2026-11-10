"""Independent rectangular gradient parents using the common structure search.

Only synthetic fixture geometry is used; reserved real families are not read.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
from xml.etree import ElementTree as ET

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.evaluate_mixed_topology import make_cases as topology_cases
from tools.run_plan_b_variations import make_original_case, make_variations, write_cases


def make_cases(seed=716293):
    rng = random.Random(seed)
    cases = []
    for index in range(12):
        outlined = index % 3 != 0
        rounded = index % 2 == 1
        case = topology_cases(seed, outlined=outlined, rounded=rounded)[index]
        root = ET.fromstring(case['svg'])
        parent = root[2]
        sw = case['expected_objects'][0]['stroke_width']
        x, y = rng.uniform(20, 30), rng.uniform(32, 42)
        w, h = 360-2*x, 360-2*y
        if index % 2:
            x, y, w, h = y, x, h, w
        parent.tag = '{http://www.w3.org/2000/svg}rect'
        for key in ('cx', 'cy', 'r'):
            parent.attrib.pop(key)
        parent.attrib.update(x=str(x), y=str(y), width=str(w), height=str(h))
        case['expected_objects'][0].update(kind='rectangle',
            bbox=[x-sw/2, y-sw/2, w+sw, h+sw], corner_radius=0.)
        counts = {kind: sum(o['kind'] == kind for o in case['expected_objects'])
                  for kind in ('circle', 'rectangle')}
        inventory = f"{counts['circle']} gefüllte Kreise und {counts['rectangle']} gefüllte Rechtecke. "
        description = inventory+case['description'].split('. ', 1)[1]
        description = description.replace('Der äussere Kreis', 'Das äussere Rechteck')
        description = description.replace('des äusseren Kreises', 'des äusseren Rechtecks')
        if rounded:
            description += ' Die inneren Rechtecke haben leicht gerundete Ecken.'
        case.update(case_id=f'rectangular_parent_{index:02d}', description=description,
                    svg=ET.tostring(root, encoding='unicode'))
        cases.append(case)
    return cases


def make_variation_cases(seed=716293):
    source = make_cases(seed)[3]
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
    parser.add_argument('--seed', type=int, default=716293)
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        cases = (make_variation_cases if args.variations else make_cases)(args.seed)
        args.prepare.mkdir(parents=True, exist_ok=False)
        write_cases(cases, args.prepare)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (args.prepare/'generation.json').write_text(json.dumps(dict(seed=args.seed,
            variations=args.variations), indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required')
    result = (verify_report if args.verify_only else evaluate_cases)(args.inputs, args.output,
                                                                    require_all=args.require_all)
    print(f"Verified: {result['accepted']}/{result['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
