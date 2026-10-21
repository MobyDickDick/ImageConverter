"""Frozen raster annotations and real CLI evidence, including unsupported content.

No reference SVG or runtime proposal is used to prepare the real-family oracle.
Synthetic language controls use the existing independent visibility generator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2

from tools.evaluate_layered_scene import evaluate_cases
from tools.evaluate_visibility_scene import make_cases as visibility_cases
from tools.run_plan_b_variations import write_cases, make_original_case, make_variations

ROOT = Path(__file__).resolve().parents[1]
ET.register_namespace('', 'http://www.w3.org/2000/svg')


def make_cases(seed=871209, count=12):
    """Color/position names come from independent reference geometry and fills."""
    cases = visibility_cases(seed, count)
    for case in cases:
        root = ET.fromstring(case['svg'])
        # Fixed well-separated color categories, independently assigned here.
        colors = ['#3169ac', '#d88032', '#3e9866']
        for element, color in zip(list(root)[1:], colors):
            element.set('fill', color)
        case['svg'] = ET.tostring(root, encoding='unicode')
        text = case['description']
        if len(case['expected_objects']) == 3:
            text = text.replace('kleinste Form', 'grüne Form').replace('größten Form', 'blauen Form')
            text = text.replace('mittelgroße Form', 'orange Form')
        else:
            text = text.replace('kleinere Form', 'rechte Form' if int(case['case_id'][-2:]) % 2 else 'orange Form')
            text = text.replace('größeren Form', 'linken Form' if int(case['case_id'][-2:]) % 2 else 'blauen Form')
        case.update(case_id=case['case_id'].replace('visibility', 'reference'), description=text)
    return cases


def prepare_real(output, annotations):
    manifest = json.loads(annotations.read_text(encoding='utf-8'))
    cases = []
    output.mkdir(parents=True, exist_ok=False)
    files = list((ROOT/'artifacts/images_to_convert').rglob('*'))
    for index, annotation in enumerate(manifest['cases']):
        sources = [p for p in files if p.name == annotation['file'] and 'samples' not in p.parts]
        if not sources or len({p.read_bytes() for p in sources}) != 1:
            raise ValueError('Missing or conflicting original raster: '+annotation['file'])
        source = sources[0]
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != annotation['source_sha256']:
            raise ValueError('Original source changed')
        pixels = cv2.imread(str(source))
        name = f'real_{index:02d}'
        folder = output/name/'input'
        folder.mkdir(parents=True)
        path = folder/(name+'.png')
        if not cv2.imwrite(str(path), pixels):
            raise ValueError('Could not write lossless decoded raster')
        root = ET.Element('root')
        entry = ET.SubElement(root, 'entry')
        ET.SubElement(entry, 'beschreibung').text = annotation['description']
        ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = path.name
        ET.ElementTree(root).write(folder/'descriptions.xml', encoding='utf-8', xml_declaration=True)
        cases.append(dict(annotation, case_id=name, width=pixels.shape[1], height=pixels.shape[0],
                          input_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (output/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (output/'annotations.sha256').write_text(hashlib.sha256(annotations.read_bytes()).hexdigest()+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--real', action='store_true')
    parser.add_argument('--annotations', type=Path, default=ROOT/'config/real_scene_families.json')
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seed', type=int, default=871209)
    parser.add_argument('--count', type=int, default=12)
    parser.add_argument('--require-all', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--rename', action='store_true')
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--paraphrase', action='store_true')
    parser.add_argument('--contradict', action='store_true')
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        if args.real:
            prepare_real(args.prepare, args.annotations)
        else:
            args.prepare.mkdir(parents=True, exist_ok=False)
            cases = make_cases(args.seed, args.count)
            for case in cases:
                if args.paraphrase:
                    case['description'] = case['description'].replace(
                        'Die orange Form liegt vor der blauen Form.',
                        'Die blaue Form liegt hinter der orangen Form.').replace(
                        'Die rechte Form liegt vor der linken Form.',
                        'Die linke Form liegt hinter der rechten Form.')
                if args.contradict:
                    case['description'] = case['description'].replace('liegt vor der', 'liegt hinter der')
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
    from tools.evaluate_layered_scene import verify_report
    result = (verify_report(args.inputs, args.output, require_all=args.require_all) if args.verify_only else
              evaluate_cases(args.inputs, args.output, rename=args.rename, require_all=args.require_all))
    print(f"Verified: {result['accepted']}/{result['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
