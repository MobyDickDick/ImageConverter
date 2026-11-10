"""Independent synthetic rounded gradient parents; no reserved real inputs."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
import subprocess
from xml.etree import ElementTree as ET

from tools.evaluate_layered_scene import evaluate_cases, verify_report
from tools.evaluate_rectangular_parent import make_cases as rectangular_cases
from tools.run_plan_b_variations import make_original_case, make_variations, write_cases


def make_cases(seed=624873):
    rng = random.Random(seed)
    cases = rectangular_cases(seed)
    for index, case in enumerate(cases):
        root = ET.fromstring(case['svg'])
        radius = rng.uniform(12, 32)
        root[2].set('rx', str(radius))
        case['expected_objects'][0]['corner_radius'] = radius
        case.update(case_id=f'rounded_parent_{index:02d}',
                    svg=ET.tostring(root, encoding='unicode'),
                    description=case['description']+' Das äussere Rechteck hat gerundete Ecken.')
    return cases


def make_variation_cases(seed=624873):
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
    parser.add_argument('--seed', type=int, default=624873)
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--independent-reference', action='store_true',
                        help='Prepare reference PNGs with librsvg instead of the production renderer')
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        cases = (make_variation_cases if args.variations else make_cases)(args.seed)
        reference_options = {}
        generation = dict(seed=args.seed, variations=args.variations)
        if args.independent_reference:
            from tools.evaluate_svg_text_baseline import find_librsvg, render_librsvg
            generation['reference_renderer'] = subprocess.check_output(
                [find_librsvg(), '--version'], text=True).strip()
            reference_options['render_fn'] = render_librsvg
        args.prepare.mkdir(parents=True, exist_ok=False)
        write_cases(cases, args.prepare, **reference_options)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (args.prepare/'generation.json').write_text(json.dumps(generation, indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required')
    result = (verify_report if args.verify_only else evaluate_cases)(args.inputs, args.output,
                                                                    require_all=args.require_all)
    print(f"Verified: {result['accepted']}/{result['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
