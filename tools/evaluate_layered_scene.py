"""Frozen real-CLI comparisons for flat filled and nested primitive scenes.

The oracle reads saved native SVG objects and generator boxes, independently
of production proposals. References are forbidden to the conversion workers.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path, PureWindowsPath
import random
import shutil
import subprocess
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from tools.run_plan_b_variations import (render, run_case, sha256, write_cases,
                                        measure_quality, make_original_case, make_variations)

ROOT = Path(__file__).resolve().parents[1]


def evidence_path(root, name):
    """Resolve portable and historical Windows paths inside an evidence folder."""
    portable = str(name).replace('\\', '/')
    relative = Path(portable)
    root = root.resolve()
    target = (root/relative).resolve()
    if (relative.is_absolute() or PureWindowsPath(portable).drive
            or not target.is_relative_to(root)):
        raise ValueError('Evidence path must stay inside its folder: '+str(name))
    return target


def make_cases(seed=20261020, count=18, wide_nesting=False):
    rng = random.Random(seed)
    cases = []
    for index in range(count):
        width, height = rng.choice([(200, 160), (240, 190), (180, 180)])
        nested = index % 2 == 1
        n = 2 + (index // 2) % 2 if nested else 1 + (index // 2) % 3
        objects, shapes = [], []
        palette = rng.sample(['#3169ac', '#d88032', '#3e9866', '#994888'], n)
        for j in range(n):
            kind = rng.choice(['circle', 'rectangle'])
            if nested:
                size = min(width, height) * (.72, .36, .14)[j]
                cx, cy = width * .5 + j * 2.1, height * .5 - j * 1.8
                if wide_nesting:
                    cx, cy = width*.5, height*.5
                    if j == 1:
                        parent = objects[-1]
                        ratio = .58 if parent['kind'] == 'circle' and kind == 'rectangle' else .65
                        parent_sw = 2.5 if index % 3 == 2 else 0.
                        size = ratio*min(parent['bbox'][2]-parent_sw, parent['bbox'][3]-parent_sw)
            else:
                size = min(height * .45, width / n * .65)
                size *= rng.uniform(.82, 1.03)
                cx, cy = width * (j + .5) / n, height * rng.uniform(.4, .6)
            w, h = size, size if kind == 'circle' else size * rng.uniform(.8, 1.1)
            x, y = cx-w/2, cy-h/2
            # Every third family includes separately colored native outlines.
            sw = 2.5 if index % 3 == 2 else 0.
            style = f'fill="{palette[j]}" stroke="#303030" stroke-width="{sw}"'
            if kind == 'circle':
                shape = f'<circle cx="{cx}" cy="{cy}" r="{w/2}" {style}/>'
            else:
                shape = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {style}/>'
            shapes.append(shape)
            objects.append(dict(kind=kind, bbox=[x-sw/2, y-sw/2, w+sw, h+sw],
                                parent=j-1 if nested and j else None))
        nouns = []
        for kind, noun, plural in [('circle', 'Kreis', 'Kreise'), ('rectangle', 'Rechteck', 'Rechtecke')]:
            number = sum(obj['kind'] == kind for obj in objects)
            if number:
                nouns.append(f"{['', 'ein', 'zwei', 'drei'][number]} {noun if number == 1 else plural}")
        relation = 'Die Formen sind ineinander verschachtelt.' if nested else 'Die Formen liegen getrennt nebeneinander.'
        description = ' und '.join(nouns) + '. Alle Formen sind einfarbig gefüllt. ' + relation + ' Keine Beschriftung.'
        if index % 3 == 2:
            description += ' Jede Form hat eine dunkle Kontur.'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="{width}" height="{height}" fill="white"/>' + ''.join(shapes) + '</svg>'
        cases.append(dict(case_id=f'layer_{index:02d}', width=width, height=height,
                          description=description, svg=svg, expected_objects=objects))
    return cases


def check_objects(svg, expected):
    """Native object count, shape, bounds and painter order; no production fitter."""
    root = ET.fromstring(svg)
    actual = []
    gradients = {g.get('id'): g for defs in root if defs.tag.rsplit('}', 1)[-1] == 'defs' for g in defs}
    for element in root:
        kind = element.tag.rsplit('}', 1)[-1]
        if kind == 'defs':
            # Native paint definitions do not count as scene objects. Accept
            # only the bounded axial, two-stop gradient model used here.
            for gradient in element:
                if (gradient.tag.rsplit('}', 1)[-1] != 'linearGradient'
                        or set(gradient.attrib) - {'id', 'x1', 'y1', 'x2', 'y2'}
                        or len(gradient) != 2):
                    return dict(passed=False, reason='non_native_scene_definition')
                for stop in gradient:
                    if (stop.tag.rsplit('}', 1)[-1] != 'stop' or len(stop)
                            or set(stop.attrib) != {'offset', 'stop-color'}):
                        return dict(passed=False, reason='non_native_scene_definition')
            continue
        sw = float(element.get('stroke-width', '0')) if element.get('stroke', 'none') != 'none' else 0.
        if kind == 'circle':
            r = float(element.get('r', '0'))
            box = [float(element.get('cx', '0'))-r-sw/2,
                   float(element.get('cy', '0'))-r-sw/2, 2*r+sw, 2*r+sw]
        elif kind == 'rect':
            box = [float(element.get('x', '0'))-sw/2, float(element.get('y', '0'))-sw/2,
                   float(element.get('width', '0'))+sw, float(element.get('height', '0'))+sw]
            if box == [0., 0., float(root.get('width')), float(root.get('height'))] and element.get('fill') in ('white', '#ffffff'):
                continue
        else:
            return dict(passed=False, reason='non_native_scene_element')
        fill = element.get('fill', '')
        gradient = gradients.get(fill[5:-1]) if fill.startswith('url(#') and fill.endswith(')') else None
        gradient_axis = None
        if gradient is not None:
            if (gradient.get('x1'), gradient.get('y1')) == ('0%', '0%'):
                gradient_axis = {("100%", "0%"): 0, ("0%", "100%"): 1}.get((gradient.get('x2'), gradient.get('y2')))
        actual.append(dict(kind='rectangle' if kind == 'rect' else kind, bbox=box, stroke_width=sw,
                           corner_radius=float(element.get('rx', '0')), gradient_axis=gradient_axis,
                           fill=fill))
    if len(actual) != len(expected):
        return dict(passed=False, detected_count=len(actual), expected_count=len(expected))
    best = float('inf')
    for order in itertools.permutations(range(len(actual))):
        if any(actual[a]['kind'] != obj['kind'] for a, obj in zip(order, expected)):
            continue
        if any('stroke_width' in obj and abs(actual[a]['stroke_width']-obj['stroke_width']) > .85
               for a, obj in zip(order, expected)):
            continue
        if any('corner_radius' in obj and abs(actual[a]['corner_radius']-obj['corner_radius']) > 1.25
               for a, obj in zip(order, expected)):
            continue
        if any('gradient_axis' in obj and actual[a]['gradient_axis'] != obj['gradient_axis']
               for a, obj in zip(order, expected)):
            continue
        if any('fill' in obj and actual[a]['fill'] != obj['fill'] for a, obj in zip(order, expected)):
            continue
        if any(obj['parent'] is not None and order[obj['parent']] >= order[i] for i, obj in enumerate(expected)):
            continue
        if any('behind' in obj and order[i] >= order[obj['behind']] for i, obj in enumerate(expected)):
            continue
        if any(order[i] >= order[j] for i, obj in enumerate(expected) for j in obj.get('behind_all', [])):
            continue
        best = min(best, max(abs(v-w) for a, obj in zip(order, expected)
                             for v, w in zip(actual[a]['bbox'], obj['bbox'])))
    return dict(passed=best <= 2.5, detected_count=len(actual), expected_count=len(expected),
                max_bbox_error_px=best if np.isfinite(best) else None)


def local_checks(reference, svg, objects):
    # Use the independent global evaluator on each crop, including internal
    # color boundaries: small children cannot hide behind a large parent.
    raster = render(svg, reference.shape[1], reference.shape[0])
    checks = []
    for obj in objects:
        x, y, w, h = obj['bbox']
        x, y, X, Y = max(0, int(x)-3), max(0, int(y)-3), min(reference.shape[1], int(np.ceil(x+w))+3), min(reference.shape[0], int(np.ceil(y+h))+3)
        # Pixel metrics are computed explicitly; no embedded raster SVG oracle.
        a, b = reference[y:Y, x:X], raster[y:Y, x:X]
        error = np.square(a.astype(float)-b.astype(float)).mean(axis=2)/255**2
        bg = np.array([255., 255., 255.])
        ma, mb = np.max(abs(a-bg), axis=2)>25, np.max(abs(b-bg), axis=2)>25
        union = ma | mb
        fg = float(error[union].mean()) if union.any() else float(error.mean())
        iou = np.count_nonzero(ma & mb)/max(1, np.count_nonzero(union))
        ea, eb = cv2.Canny(a, 50, 140)>0, cv2.Canny(b, 50, 140)>0
        if ea.any() and eb.any():
            da = cv2.distanceTransform((~ea).astype('uint8'), cv2.DIST_L2, 3)
            db = cv2.distanceTransform((~eb).astype('uint8'), cv2.DIST_L2, 3)
            edge = float((np.exp(-db[ea]).mean()+np.exp(-da[eb]).mean())/2)
        else:
            edge = float(not ea.any() and not eb.any())
        checks.append(dict(normalized_mse=float(error.mean()), foreground_mse=fg,
                           foreground_iou=float(iou), edge_alignment=edge,
                           passed=bool(error.mean() <= .01 and fg <= .04 and iou >= .85 and edge >= .72)))
    return checks


def verify_report(inputs, output, *, require_all=False, write_verification=True):
    report = json.loads((output/'report.json').read_text(encoding='utf-8'))
    manifest = json.loads((inputs/'manifest.json').read_text(encoding='utf-8'))
    if not manifest or len(report['cases']) != len(manifest):
        raise ValueError('Incomplete CLI matrix')
    verified = []
    for expected, result in zip(manifest, report['cases']):
        original = inputs/expected['case_id']/'input'/(expected['case_id']+'.png')
        if sha256(original.read_bytes()) != expected['input_sha256'] or result['input_sha256'] != expected['input_sha256']:
            raise ValueError('Input hash mismatch')
        if result['description'] != expected['description'] or result['expected_objects'] != expected['expected_objects']:
            raise ValueError('Description or object oracle mismatch')
        folder = output/result['case_id']
        access = json.loads((folder/'reference_access.json').read_text(encoding='utf-8'))
        if access['blocked_svg_reads']:
            raise ValueError('Forbidden vector access')
        rows = json.loads((folder/'conversion/reports/conversion_result_map.json').read_text(encoding='utf-8'))
        if not rows and not result.get('output_svg') and result.get('accepted') is False:
            # A supervised timeout without any retained SVG is a negative
            # observation, not a missing successful row. Keep it in the
            # denominator, but require independent containment/access evidence.
            control = json.loads((folder/f'conversion/reports/{result["case_id"]}_deadline.json').read_text(encoding='utf-8'))
            worker_access = json.loads((folder/f'conversion/reports/{result["case_id"]}_reference_access.json').read_text(encoding='utf-8'))
            outputs = [p for name in ('converted_svgs', 'converted_svg_failed')
                       for p in (folder/'conversion'/name).glob('*.svg')]
            if (outputs or worker_access.get('blocked_svg_reads') != []
                    or control.get('stop_reason') != 'time_limit'
                    or control.get('isolated') is not True
                    or control.get('limit_seconds') != 5. or control.get('max_seconds') != 5.
                    or control.get('elapsed_seconds', -1) < 5.
                    or control.get('retained_output') is not False):
                raise ValueError('Unverified missing-output timeout')
            verified.append(dict(case_id=result['case_id'], accepted=False, source=None,
                                 adaptive_search=control, absence_reason='time_limit_no_output'))
            continue
        if len(rows) != 1:
            raise ValueError('Missing or ambiguous runtime row')
        row = next(iter(rows.values()))
        if row.get('reference_access', {}).get('blocked_svg_reads') != []:
            raise ValueError('Forbidden worker vector access or missing worker guard evidence')
        control = row.get('params', {}).get('adaptive_search', {})
        if not control.get('isolated') or control.get('max_seconds') != 5. or control.get('limit_seconds') != 5.:
            raise ValueError('Supervised five-second budget was not observed')
        accepted = False
        if result.get('output_svg'):
            path = evidence_path(output, result['output_svg'])
            if sha256(path.read_bytes()) != result['output_sha256']:
                raise ValueError('Output hash mismatch')
            svg = path.read_text(encoding='utf-8')
            image = cv2.imread(str(original))
            quality = measure_quality(image, svg)
            objects = check_objects(svg, expected['expected_objects'])
            local = local_checks(image, svg, expected['expected_objects'])
            accepted = bool(result.get('returncode') == 0 and quality['satisfactory'] and objects['passed'] and all(q['passed'] for q in local))
        if accepted != result['accepted']:
            raise ValueError('Saved decision differs from independently re-rendered output')
        verified.append(dict(case_id=result['case_id'], accepted=accepted,
                             source=row.get('params', {}).get('primitive_scene_registration', {}).get('source'),
                             adaptive_search=control))
    summary = dict(cases=verified, completed=len(verified), accepted=sum(c['accepted'] for c in verified))
    if write_verification:
        (output/'verification.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    if require_all and summary['accepted'] != summary['completed']:
        raise ValueError('One or more CLI scenes failed independent acceptance')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seed', type=int, default=20261020)
    parser.add_argument('--count', type=int, default=18)
    parser.add_argument('--rename', action='store_true')
    parser.add_argument('--rotate', action='store_true')
    parser.add_argument('--paraphrase', action='store_true')
    parser.add_argument('--variations', action='store_true', help='Original plus 16 Plan-B variations of a new nested scene')
    parser.add_argument('--wide-nesting', action='store_true', help='Concentric scenes with larger child objects')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    os.environ.update(IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0', ICC_SEARCH_SEED='17')
    if args.prepare:
        args.prepare.mkdir(parents=True, exist_ok=False)
        cases = make_cases(args.seed, args.count, args.wide_nesting)
        if args.variations:
            source = make_cases(args.seed, 12, args.wide_nesting)[11]
            cases = [make_original_case(source['svg'], source['description']),
                     *make_variations(source['svg'], source['description'], args.seed)]
            for case in cases:
                variation = case['variation']
                scale, dx, dy = variation['scale'], variation['relative_x'], variation['relative_y']
                w, h = source['width'], source['height']
                case['expected_objects'] = [dict(obj, bbox=[
                    w/2+scale*(obj['bbox'][0]-w/2)+dx*w,
                    h/2+scale*(obj['bbox'][1]-h/2)+dy*h,
                    scale*obj['bbox'][2], scale*obj['bbox'][3]]) for obj in source['expected_objects']]
        if args.rotate:
            from tools.evaluate_primitive_scene import rotate_cases
            cases = rotate_cases(cases)
        if args.paraphrase:
            for case in cases:
                case['description'] = case['description'].replace('Alle Formen sind einfarbig gefüllt.', 'Die Formen besitzen eine einfarbige Füllung.').replace('ineinander verschachtelt', 'ineinander angeordnet').replace('Keine Beschriftung.', 'Ohne Text oder Zeichen.')
        write_cases(cases, args.prepare)
        (args.prepare/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (args.prepare/'generation.json').write_text(json.dumps(dict(seed=args.seed, count=len(cases), rotate=args.rotate, paraphrase=args.paraphrase, variations=args.variations, wide_nesting=args.wide_nesting), indent=2)+'\n', encoding='utf-8')
        return 0
    if not args.inputs or not args.output:
        parser.error('--inputs and --output required')
    if args.verify_only:
        summary = verify_report(args.inputs, args.output, require_all=args.require_all)
        print(f"Verified: {summary['accepted']}/{summary['completed']} accepted")
        return 0
    evaluate_cases(args.inputs, args.output, rename=args.rename, require_all=args.require_all)
    return 0


def evaluate_cases(inputs, output, *, rename=False, require_all=False):
    """Shared audited CLI runner; fixtures and object oracles remain external."""
    cases = json.loads((inputs/'manifest.json').read_text(encoding='utf-8'))
    output.mkdir(parents=True, exist_ok=False)
    report = dict(evidence_kind='real_cli', budget_seconds=5, seed=17,
                  commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_sha256={str(p.relative_to(ROOT)):sha256(p.read_bytes()) for p in (ROOT/'src').rglob('*.py')}, cases=[])
    for i, case in enumerate(cases):
        old_name = case['case_id']
        name = f'anonymous_{i:02d}' if rename else old_name
        case['case_id'] = name
        folder = output/name/'input'
        folder.mkdir(parents=True)
        original = inputs/old_name/'input'
        shutil.copyfile(original/(old_name+'.png'), folder/(name+'.png'))
        assert sha256((folder/(name+'.png')).read_bytes()) == case['input_sha256']
        (folder/'descriptions.xml').write_text((original/'descriptions.xml').read_text(encoding='utf-8').replace(old_name, name), encoding='utf-8')
        result = run_case(case, output, timeout=30, iterations=64,
                          extra_cli_args=('--search-seconds', '5', '--search-max-seconds', '5'))
        if result.get('output_svg'):
            svg = evidence_path(output, result['output_svg']).read_text(encoding='utf-8')
            result['object_check'] = check_objects(svg, case['expected_objects'])
            reference = cv2.imread(str(original/(old_name+'.png')))
            result['local_checks'] = local_checks(reference, svg, case['expected_objects'])
        result['accepted'] = bool(result['satisfactory'] and result.get('object_check', {}).get('passed')
                                  and all(q['passed'] for q in result.get('local_checks', [])))
        report['cases'].append(result)
        (output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(name, result['accepted'], result.get('failures'), flush=True)
    return verify_report(inputs, output, require_all=require_all)


if __name__ == '__main__':
    raise SystemExit(main())
