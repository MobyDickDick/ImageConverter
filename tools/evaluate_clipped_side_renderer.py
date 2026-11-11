"""Freeze independent thin-side controls and audit their unchanged native SVGs."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np

from tools.evaluate_clipped_rectangular_parent import make_cases, parent_regions
from tools.evaluate_layered_scene import check_objects, local_checks
from tools.evaluate_svg_text_baseline import find_librsvg, render_librsvg
from tools.run_plan_b_variations import render, sha256, write_cases, measure_quality


def controls():
    original = make_cases(391827)
    cases = [original[2], original[10]]
    for axis in range(2):
        for width in (1., 1.5, 3.):
            for delta in (-.25, -.03125, .03125, .25):
                case = copy.deepcopy(original[10])
                root = ET.fromstring(case['svg'])
                parent = root[2]
                for key in ('x', 'y'):
                    parent.set(key, str(float(parent.get(key))+delta))
                parent.set('stroke-width', str(width))
                gradient = root[0][0]
                gradient.set('x2', '100%' if axis == 0 else '0%')
                gradient.set('y2', '0%' if axis == 0 else '100%')
                x, y, w, h = [float(parent.get(k)) for k in ('x', 'y', 'width', 'height')]
                case['expected_objects'][0].update(bbox=[x-width/2, y-width/2, w+width, h+width],
                                                   stroke_width=width, gradient_axis=axis)
                case['case_id'] = f'control_{len(cases):02d}'
                case['svg'] = ET.tostring(root, encoding='unicode')
                cases.append(case)
    return cases


def side_profile(image, side):
    x, y, w, h = side['bbox']
    x, y = max(0, int(x)-3), max(0, int(y)-3)
    X, Y = min(image.shape[1], int(np.ceil(side['bbox'][0]+w))+3), min(image.shape[0], int(np.ceil(side['bbox'][1]+h))+3)
    crop = image[y:Y, x:X]
    edges = cv2.Canny(crop, 50, 140)
    if side['name'] in ('left', 'right'):
        colors, line = crop[len(crop)//2], edges[len(crop)//2]
    else:
        colors, line = crop[:, crop.shape[1]//2], edges[:, crop.shape[1]//2]
    return dict(bgr=colors.tolist(), canny_positions=np.flatnonzero(line).tolist(),
                canny_pixels=int(np.count_nonzero(edges)))


def audit(folder, *, render_fn=render):
    rows = []
    for case in json.loads((folder/'manifest.json').read_text(encoding='utf-8')):
        svg_data = (folder/case['reference_svg']).read_bytes()
        data = (folder/case['case_id']/'input'/(case['case_id']+'.png')).read_bytes()
        if sha256(data) != case['input_sha256'] or sha256(svg_data) != case['reference_svg_sha256']:
            raise ValueError('Frozen renderer control changed')
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        svg = svg_data.decode('utf-8')
        corners, sides = parent_regions(case)
        row = dict(case_id=case['case_id'], input_sha256=sha256(data),
                   reference_svg_sha256=sha256(svg_data), native=check_objects(svg, case['expected_objects']),
                   renderers={})
        for name, fn in [('native', render_fn), ('librsvg', render_librsvg)]:
            raster = fn(svg, case['width'], case['height'])
            frozen = lambda *args: raster
            result = dict(global_check=measure_quality(image, svg, render_fn=frozen),
                          objects=local_checks(image, svg, case['expected_objects'], render_fn=frozen),
                          corners=local_checks(image, svg, [c for c in corners if c['visibility'] != 'hidden'], render_fn=frozen),
                          sides=local_checks(image, svg, sides, render_fn=frozen))
            # Keep actual Canny coordinates, independent from the shape oracle.
            result['edge_pixels'] = int(np.count_nonzero(cv2.Canny(raster, 50, 140)))
            result['side_profiles'] = [dict(name=s['name'], reference=side_profile(image, s),
                                            rendered=side_profile(raster, s)) for s in sides]
            row['renderers'][name] = result
        row['passed'] = row['native']['passed'] and all(
            r['global_check']['satisfactory'] and all(q['passed'] for q in r['objects']+r['corners']+r['sides'])
            for r in row['renderers'].values())
        rows.append(row)
    return dict(pymupdf=fitz.VersionBind, opencv=cv2.__version__,
                librsvg=subprocess.check_output([find_librsvg(), '--version'], text=True).strip(),
                runtime_sha256=sha256(Path('src/iCCModules/imageCompositeConverterRendering.py').read_bytes()),
                cases=rows, completed=len(rows), passed=sum(r['passed'] for r in rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--controls', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        args.prepare.mkdir(parents=True, exist_ok=False)
        cases = controls()
        write_cases(cases, args.prepare, render_fn=render_librsvg)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.controls or not args.report:
        parser.error('--controls and --report required')
    result = audit(args.controls)
    args.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(f"Renderer controls: {result['passed']}/{result['completed']}")
    return int(args.require_all and result['passed'] != result['completed'])


if __name__ == '__main__':
    raise SystemExit(main())
