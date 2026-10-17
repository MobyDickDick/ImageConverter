"""Real CLI before/after evidence for separated primitive scenes.

Prepare once before implementation; replay the frozen inputs after changes.
Reference SVGs are available to the evaluator only, with audited CLI workers.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from tools.run_plan_b_variations import render, measure_quality, run_case, sha256, write_cases

ROOT = Path(__file__).resolve().parents[1]


def make_cases(seed=20261017, count=12):
    rng = random.Random(seed)
    cases = []
    for index in range(count):
        number = 1 + index % 3
        width, height = rng.choice([(180, 120), (240, 170), (156, 148)])
        shapes, objects, kinds = [], [], []
        for item in range(number):
            kind = rng.choice(['circle', 'rectangle'])
            # Independent analytic generator; no converter fitting helpers.
            size = rng.uniform(22, min(height * .38, width / number * .62))
            x = width * (item + .5) / number + rng.uniform(-3, 3)
            y = height * rng.uniform(.32, .68)
            sw = rng.choice([2., 3., 4.5])
            color = rng.choice(['#333333', '#20654a', '#4b3a8c', '#8c4531'])
            if kind == 'circle':
                shapes.append(f'<circle cx="{x}" cy="{y}" r="{size/2}" fill="none" stroke="{color}" stroke-width="{sw}"/>')
                bbox = [x-size/2-sw/2, y-size/2-sw/2, size+sw, size+sw]
            else:
                rw, rh = size, size*rng.uniform(.7, 1.25)
                shapes.append(f'<rect x="{x-rw/2}" y="{y-rh/2}" width="{rw}" height="{rh}" fill="none" stroke="{color}" stroke-width="{sw}"/>')
                bbox = [x-rw/2-sw/2, y-rh/2-sw/2, rw+sw, rh+sw]
            objects.append(dict(kind=kind, bbox=bbox))
            kinds.append(kind)
        labels = {'circle': 'Kreis', 'rectangle': 'Rechteck'}
        counts = {kind: kinds.count(kind) for kind in set(kinds)}
        nouns = [f"{['', 'ein', 'zwei', 'drei'][n]} {labels[kind] if n == 1 else {'circle':'Kreise','rectangle':'Rechtecke'}[kind]}" for kind, n in sorted(counts.items())]
        text = ' und '.join(nouns) + '. '
        text += rng.choice(['Dunkle Konturen, weißes Inneres. Keine Beschriftung.',
                            'Umrisse auf weißem Grund, innen weiß. Ohne Text oder Zeichen.'])
        if number > 1:
            text += ' Die Objekte liegen voneinander getrennt nebeneinander.'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="{width}" height="{height}" fill="#ffffff"/>' + ''.join(shapes) + '</svg>'
        cases.append(dict(case_id=f'scene_{index:02d}', width=width, height=height,
                          description=text, svg=svg, expected_objects=objects))
    return cases


def check_objects(image, expected):
    """Independent connected-component count and analytic outer-box oracle."""
    border = np.concatenate([image[0], image[-1], image[:, 0], image[:, -1]])
    bg = np.median(border.astype(float), axis=0)
    mask = (np.max(np.abs(image.astype(float)-bg), axis=2) > 25).astype(np.uint8)
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    boxes = [row[:4].astype(float).tolist() for row in stats[1:] if row[4] >= 4]
    if len(boxes) != len(expected):
        return dict(passed=False, detected_count=len(boxes), expected_count=len(expected), boxes=boxes)
    error = min(max(max(abs(a-b) for a, b in zip(box, obj['bbox']))
                    for box, obj in zip(boxes, order))
                for order in itertools.permutations(expected))
    return dict(passed=error <= 2.5, detected_count=len(boxes), expected_count=len(expected),
                max_bbox_error_px=error, boxes=boxes)


def damage_probe():
    """Quantify an intentionally missing small object; no converter claims."""
    prefix = '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="160"><rect width="240" height="160" fill="white"/>'
    main = '<rect x="20" y="25" width="120" height="105" fill="none" stroke="#333333" stroke-width="4"/>'
    small = '<circle cx="190" cy="78" r="5" fill="none" stroke="#333333" stroke-width="2"/>'
    original, damaged = prefix+main+small+'</svg>', prefix+main+'</svg>'
    reference = render(original, 240, 160)
    result = measure_quality(reference, damaged)
    result['object_check'] = check_objects(render(damaged, 240, 160),
        [dict(bbox=[18,23,124,109]), dict(bbox=[184,72,12,12])])
    result['evidence_kind'] = 'deliberately_removed_object'
    return result


def rotate_cases(cases):
    """A new layout axis, generated only for the post-freeze holdout set."""
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    for case in cases:
        w,h = case['width'],case['height']
        root = ET.fromstring(case['svg'])
        group = ET.Element('{http://www.w3.org/2000/svg}g', transform=f'translate({h} 0) rotate(90)')
        for child in list(root):
            root.remove(child)
            group.append(child)
        root.append(group)
        root.set('width',str(h))
        root.set('height',str(w))
        case['svg'] = ET.tostring(root,encoding='unicode')
        case['width'],case['height'] = h,w
        case['description'] = case['description'].replace('nebeneinander','untereinander')
        for obj in case['expected_objects']:
            x,y,bw,bh = obj['bbox']
            obj['bbox'] = [h-y-bh,x,bh,bw]
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seed', type=int, default=20261017)
    parser.add_argument('--count', type=int, default=12)
    parser.add_argument('--rotate', action='store_true')
    parser.add_argument('--rename', action='store_true')
    args = parser.parse_args()
    os.environ['IMAGE_CONVERTER_ISOLATE_SVG_RENDER'] = '0'
    if args.prepare:
        args.prepare.mkdir(parents=True, exist_ok=False)
        cases = make_cases(args.seed, args.count)
        if args.rotate:
            cases = rotate_cases(cases)
        write_cases(cases, args.prepare)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
        (args.prepare/'generation.json').write_text(json.dumps(
            dict(seed=args.seed,count=args.count,rotate=args.rotate),indent=2)+'\n',encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required for evaluation')
    cases = json.loads((args.inputs/'manifest.json').read_text(encoding='utf-8'))
    if args.rename:
        for index,case in enumerate(cases):
            case['original_case_id'] = case['case_id']
            case['case_id'] = f'anonymous_{index:02d}'
    args.output.mkdir(parents=True, exist_ok=False)
    # Recreate the exact same bytes of the raster/reference input in a fresh run.
    import shutil
    for case in cases:
        name = case['case_id']
        target = args.output/name/'input'
        target.mkdir(parents=True)
        original_name = case.get('original_case_id',name)
        reference = args.inputs/case['reference_svg']
        assert sha256(reference.read_bytes()) == case['reference_svg_sha256']
        destination = args.output/case['reference_svg']
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(reference,destination)
        for path in (args.inputs/original_name/'input').iterdir():
            if path.suffix == '.png':
                shutil.copyfile(path,target/(name+'.png'))
            else:
                text = path.read_text(encoding='utf-8').replace(original_name,name)
                (target/path.name).write_text(text,encoding='utf-8')
        assert sha256((target/(name+'.png')).read_bytes()) == case['input_sha256']
    generation_path = args.inputs/'generation.json'
    generation = json.loads(generation_path.read_text(encoding='utf-8')) if generation_path.exists() else None
    report = dict(evidence_kind='real_cli', iterations=64, generation=generation,
                  commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(p.relative_to(ROOT)):sha256(p.read_bytes()) for p in (ROOT/'src').rglob('*.py')},
                  cases=[], damage_probe=damage_probe())
    for case in cases:
        result = run_case(case, args.output, timeout=90, iterations=64)
        if result.get('output_svg'):
            svg = (args.output/result['output_svg']).read_text(encoding='utf-8')
            result['object_check'] = check_objects(render(svg,case['width'],case['height']),case['expected_objects'])
        report['cases'].append(result)
        (args.output/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n', encoding='utf-8')
        print(case['case_id'], result['satisfactory'], result.get('object_check',{}).get('passed'), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
