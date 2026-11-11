"""Frozen independent edge/corner crops, with native geometry and depth oracles."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
import subprocess
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from tools.evaluate_layered_scene import (evaluate_cases, verify_report, evidence_path,
                                         check_objects, local_checks)
from tools.evaluate_rounded_parent import make_cases as rounded_cases
from tools.evaluate_rectangular_parent import make_cases as rectangular_cases
from tools.run_plan_b_variations import (write_cases, render, measure_quality, sha256,
                                         make_original_case, make_variations)
from tools.evaluate_svg_text_baseline import find_librsvg, render_librsvg


def make_cases(seed=718293):
    rng = random.Random(seed)
    cases = []
    for index in range(12):
        # Keep every child fixed and wholly visible. Crop the parent itself,
        # independently of its gradient axis, child rounding and topology.
        case = (rounded_cases if index < 8 else rectangular_cases)(seed)[index]
        root = ET.fromstring(case['svg'])
        parent = root[2]
        x, y, w, h = [float(parent.get(k)) for k in ('x', 'y', 'width', 'height')]
        sw = case['expected_objects'][0]['stroke_width']
        sides = [('left',), ('right',), ('top',), ('bottom',),
                 ('left', 'top'), ('right', 'bottom'), ('left',), ('bottom',)][index % 8]
        # Rounded corners retain partial arcs even where their straight side
        # is gone. Sharp cases retain an observed fill edge and crop the rim.
        cut = -rng.uniform(2., 5.) if index < 8 else rng.uniform(.6, .9)
        if index >= 8:
            sw = 3.
            parent.set('stroke', '#ded8d2')
            parent.set('stroke-width', str(sw))
            if 'helle Konturen' not in case['description']:
                # The contract applies to all objects, so outline every child.
                case['description'] += ' Die Formen haben helle Konturen.'
                for element, obj in zip(list(root)[3:], case['expected_objects'][1:]):
                    element.set('stroke', '#ded8d2')
                    element.set('stroke-width', '1.5')
                    a, b, cw, ch = obj['bbox']
                    obj.update(bbox=[a-.75, b-.75, cw+1.5, ch+1.5], stroke_width=1.5)
        right, bottom = x+w, y+h
        if 'left' in sides:
            x = cut
        if 'right' in sides:
            right = case['width']-cut
        if 'top' in sides:
            y = cut
        if 'bottom' in sides:
            bottom = case['height']-cut
        parent.attrib.update(x=str(x), y=str(y), width=str(right-x), height=str(bottom-y))
        case['expected_objects'][0].update(bbox=[x-sw/2, y-sw/2, right-x+sw, bottom-y+sw], stroke_width=sw)
        case.update(case_id=f'clipped_rectangle_{index:02d}',
                    crop_sides=sides, svg=ET.tostring(root, encoding='unicode'))
        cases.append(case)
    return cases


def make_variation_cases(seed=718293):
    # Use the project's coupled scale/position variation distribution intact;
    # it includes complete, shallow and unobservable crops. Negative geometry
    # must remain a negative result, not a reason to reselect a nicer seed.
    source = make_cases(seed)[0]
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
        case['case_id'] = 'crop_variant_'+case['case_id']
    return cases


def parent_regions(case):
    """Label partial/hidden corners explicitly; frame segments are no sides."""
    parent = case['expected_objects'][0]
    x, y, w, h = parent['bbox']
    extent = max(5., parent.get('corner_radius', 0.)+parent['stroke_width']+3)
    corners, sides = [], []
    for a in (x, x+w-extent):
        for b in (y, y+h-extent):
            visible = max(0., min(a+extent, case['width'])-max(a, 0.))*max(0., min(b+extent, case['height'])-max(b, 0.))
            corners.append(dict(bbox=[a, b, extent, extent], visibility=(
                'hidden' if visible == 0 else 'complete' if abs(visible-extent**2) < 1e-6 else 'partial')))
    margin = extent+3
    for name, box, boundary, length in [
        ('left', [x-3, y+margin, 7+parent['stroke_width'], h-2*margin], x, case['width']),
        ('right', [x+w-4-parent['stroke_width'], y+margin, 7+parent['stroke_width'], h-2*margin], x+w, case['width']),
        ('top', [x+margin, y-3, w-2*margin, 7+parent['stroke_width']], y, case['height']),
        ('bottom', [x+margin, y+h-4-parent['stroke_width'], w-2*margin, 7+parent['stroke_width']], y+h, case['height'])]:
        # The outer edge can be clipped while an inner fill edge is visible.
        inner = boundary+(parent['stroke_width'] if name in ('left', 'top') else -parent['stroke_width'])
        if 1 < inner < length-1 and min(box[2:]) > 0:
            sides.append(dict(name=name, bbox=box))
    return corners, sides


def audit(inputs, output):
    verify_report(inputs, output, write_verification=False)
    manifest = json.loads((inputs/'manifest.json').read_text(encoding='utf-8'))
    report = json.loads((output/'report.json').read_text(encoding='utf-8'))
    rows = []
    for source, result in zip(manifest, report['cases']):
        name = source['case_id']
        data = (inputs/name/'input'/(name+'.png')).read_bytes()
        reference = evidence_path(inputs, source['reference_svg']).read_bytes()
        description = (inputs/name/'input'/'descriptions.xml').read_bytes()
        if (sha256(reference) != source['reference_svg_sha256'] or
                ET.fromstring(description).findtext('entry/beschreibung') != source['description']):
            raise ValueError('Changed reference or description')
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        corners, sides = parent_regions(source)
        visible = [c for c in corners if c['visibility'] != 'hidden']
        row = dict(case_id=name, input_sha256=sha256(data), reference_svg_sha256=sha256(reference),
                   description_sha256=sha256(description), expected_objects=source['expected_objects'],
                   corners=corners, sides=sides, recorded_accepted=result['accepted'],
                   seconds=result['elapsed_seconds'], accepted=False, renderers={})
        if result.get('output_svg'):
            svg_data = evidence_path(output, result['output_svg']).read_bytes()
            if sha256(svg_data) != result['output_sha256']:
                raise ValueError('Changed CLI vector')
            svg = svg_data.decode('utf-8')
            row.update(output_sha256=sha256(svg_data), native_objects=check_objects(svg, source['expected_objects']))
            # Exclude children from the remainder while retaining all exposed
            # parent paint, background, corners and edges at original pixels.
            remainder = np.ones(image.shape[:2], bool)
            for obj in source['expected_objects'][1:]:
                x, y, w, h = obj['bbox']
                remainder[max(0, int(y)-4):min(image.shape[0], int(np.ceil(y+h))+4),
                          max(0, int(x)-4):min(image.shape[1], int(np.ceil(x+w))+4)] = False
            a = image.copy()
            a[~remainder] = 255
            for name, renderer in [('native', render), ('librsvg', render_librsvg)]:
                raster = renderer(svg, source['width'], source['height'])
                frozen = lambda *args: raster
                b = raster.copy()
                b[~remainder] = 255
                row['renderers'][name] = dict(
                    global_check=measure_quality(image, svg, render_fn=frozen),
                    objects=local_checks(image, svg, source['expected_objects'], render_fn=frozen),
                    corners=local_checks(image, svg, visible, render_fn=frozen),
                    sides=local_checks(image, svg, sides, render_fn=frozen),
                    remainder=measure_quality(a, svg, render_fn=lambda *args: b))
            row['accepted'] = bool(result['accepted'] and row['native_objects']['passed'] and all(
                r['global_check']['satisfactory'] and r['remainder']['satisfactory']
                and all(q['passed'] for q in r['objects']+r['corners']+r['sides'])
                for r in row['renderers'].values()))
        rows.append(row)
    return dict(schema='clipped_rectangular_parent_v1', source_sha256=report['source_sha256'],
                report_sha256=sha256((output/'report.json').read_bytes()), cases=rows,
                summary=dict(completed=len(rows), accepted=sum(r['accepted'] for r in rows),
                    recorded_accepted=sum(r['recorded_accepted'] for r in rows),
                    hidden_corners=sum(c['visibility'] == 'hidden' for r in rows for c in r['corners'])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--seed', type=int, default=718293)
    parser.add_argument('--variations', action='store_true')
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--require-all', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--audit', type=Path)
    args = parser.parse_args()
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        cases = (make_variation_cases if args.variations else make_cases)(args.seed)
        args.prepare.mkdir(parents=True, exist_ok=False)
        write_cases(cases, args.prepare, render_fn=render_librsvg)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (args.prepare/'generation.json').write_text(json.dumps(dict(seed=args.seed, variations=args.variations,
            reference_renderer=subprocess.check_output([find_librsvg(), '--version'], text=True).strip()), indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required')
    if args.audit:
        result = audit(args.inputs, args.output)
        args.audit.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(result['summary'])
        return int(args.require_all and result['summary']['accepted'] != result['summary']['completed'])
    result = (verify_report if args.verify_only else evaluate_cases)(args.inputs, args.output, require_all=args.require_all)
    print(f"Verified: {result['accepted']}/{result['completed']} accepted")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
