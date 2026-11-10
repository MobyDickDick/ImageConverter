"""Freeze independent rounded-rectangle controls before changing the renderer.

Preparation never overwrites inputs. Checking uses the saved PNGs, not a fresh
reference render. Historical MuPDF scenes remain a separate, unchanged cohort.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from tools.evaluate_layered_scene import check_objects, evidence_path, local_checks, verify_report
from tools.evaluate_rounded_parent import make_cases, make_variation_cases
from tools.evaluate_svg_text_baseline import find_librsvg, render_librsvg
from tools.run_plan_b_variations import measure_quality, render, sha256, write_cases


def controls():
    cases = []
    # Solid, horizontal, vertical, reversed and diagonal paint; thin/wide rims;
    # small/large radii, subpixel edges, short/tall/wide boxes and clamped radii.
    for index in range(24):
        w, h = [(300, 280), (131.5, 67.25), (66.75, 225.5)][index % 3]
        x, y = (30., 40.) if index % 2 == 0 else (30.375, 40.625)
        rx = [30., 2.5, 12., 45.25][index % 4]
        ry = rx if index < 18 else rx*.55
        sw = [0., .75, 3.5, 7.][(index//3) % 4]
        paint = index % 6
        x2, y2 = [('100%', '0%'), ('0%', '100%'), ('100%', '100%')][paint % 3]
        start, end = ('#214c87', '#b78842') if paint < 4 else ('#b78842', '#214c87')
        defs = (f'<defs><linearGradient id="g" x1="0%" y1="0%" x2="{x2}" y2="{y2}">'
                f'<stop offset="0" stop-color="{start}"/><stop offset="1" stop-color="{end}"/>'
                '</linearGradient></defs>') if paint else ''
        fill = 'url(#g)' if paint else '#555555'
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="380" height="360">{defs}'
               '<rect width="380" height="360" fill="white"/>'
               f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{ry}" '
               f'fill="{fill}" stroke="#cbd4df" stroke-width="{sw}"/></svg>')
        extent = min(max(rx, ry)+sw+3, min(w, h)/2)
        corners = [dict(bbox=[a, b, extent, extent]) for a in (x-sw/2, x+w+sw/2-extent)
                   for b in (y-sw/2, y+h+sw/2-extent)]
        cases.append(dict(case_id=f'rounded_{index:02d}', svg=svg, width=380, height=360,
                          corners=corners, radius=[min(rx, w/2), min(ry, h/2)]))
    for kind, shape in [
        ('sharp', '<rect x="30.375" y="40.625" width="300" height="280" fill="#555555"/>'),
        ('circle', '<circle cx="180" cy="180" r="90" fill="#214c87"/>'),
        ('ellipse', '<ellipse cx="180" cy="180" rx="120" ry="70" fill="#214c87"/>'),
        ('bezier', '<path d="M 30 200 C 30 30 300 30 300 200 L 160 300 Z" fill="#214c87"/>')]:
        cases.append(dict(case_id=kind, width=380, height=360, corners=[],
            svg='<svg xmlns="http://www.w3.org/2000/svg" width="380" height="360">'
                '<rect width="380" height="360" fill="white"/>'+shape+'</svg>'))
    return cases


def analytic_control():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="360" height="360">'
           '<rect width="360" height="360" fill="white"/>'
           '<rect x="30" y="40" width="300" height="280" rx="30" fill="#555555"/></svg>')
    result = dict(ideal_corner_deficit=float((1-np.pi/4)*30**2))
    for name, renderer in [('native', render), ('librsvg', render_librsvg)]:
        coverage = (255-renderer(svg, 360, 360)[:, :, 0].astype(float))/170
        result[name+'_corner_deficit'] = float(np.sum(1-coverage[40:90, 30:80]))
    return result


def check(folder):
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    results = []
    for case in manifest['cases']:
        name = case['case_id']
        svg_data, png_data = (folder/(name+'.svg')).read_bytes(), (folder/(name+'.png')).read_bytes()
        if (sha256(svg_data), sha256(png_data)) != (case['svg_sha256'], case['png_sha256']):
            raise ValueError('Frozen control changed: '+name)
        image = cv2.imdecode(np.frombuffer(png_data, np.uint8), cv2.IMREAD_COLOR)
        svg = svg_data.decode('utf-8')
        results.append(dict(case_id=name, global_check=measure_quality(image, svg),
                            corners=local_checks(image, svg, case['corners'])))
    return dict(cases=results, analytic_control=analytic_control(), summary=dict(
        completed=len(results), globals_passed=sum(c['global_check']['satisfactory'] for c in results),
        corners=sum(len(c['corners']) for c in results),
        corners_passed=sum(q['passed'] for c in results for q in c['corners'])))


def prepare(folder):
    folder.mkdir(parents=True, exist_ok=False)
    manifest = dict(schema='rounded_renderer_controls_v1', renderer=subprocess.check_output(
        [find_librsvg(), '--version'], text=True).strip(), cases=[])
    for case in controls():
        svg = case.pop('svg')
        name = case['case_id']
        (folder/(name+'.svg')).write_text(svg, encoding='utf-8')
        image = render_librsvg(svg, case['width'], case['height'])
        cv2.imwrite(str(folder/(name+'.png')), image)
        cv2.imwrite(str(folder/(name+'-before.png')), render(svg, case['width'], case['height']))
        manifest['cases'].append(dict(case, svg_sha256=sha256((folder/(name+'.svg')).read_bytes()),
            png_sha256=sha256((folder/(name+'.png')).read_bytes()),
            before_png_sha256=sha256((folder/(name+'-before.png')).read_bytes())))
    (folder/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    (folder/'before.json').write_text(json.dumps(check(folder), indent=2)+'\n', encoding='utf-8')
    for name, seed, variations in [('primary', 624873, False), ('additional', 981347, False),
                                    ('variations', 853291, True)]:
        cases = (make_variation_cases if variations else make_cases)(seed)
        inputs = folder.parent/(name+'-inputs')
        inputs.mkdir(exist_ok=False)
        write_cases(cases, inputs, render_fn=render_librsvg)
        (inputs/'manifest.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (inputs/'generation.json').write_text(json.dumps(dict(seed=seed, variations=variations,
            reference_renderer=manifest['renderer']), indent=2)+'\n', encoding='utf-8')


def audit_scenes(inputs, output, *, historical=False):
    if not historical:
        verify_report(inputs, output, write_verification=False)
    report = json.loads((output/'report.json').read_text(encoding='utf-8'))
    manifest = json.loads((inputs/'manifest.json').read_text(encoding='utf-8'))
    by_id = {case['case_id']: case for case in manifest}
    if (len(report['cases']) != len(manifest) or len(by_id) != len(manifest) or
            {case['case_id'] for case in report['cases']} != set(by_id)):
        raise ValueError('Incomplete CLI cohort')
    results = []
    for case in report['cases']:
        source = by_id[case['case_id']]
        image_data = (inputs/case['case_id']/'input'/(case['case_id']+'.png')).read_bytes()
        reference_data = evidence_path(inputs, source['reference_svg']).read_bytes()
        description_data = (inputs/case['case_id']/'input'/'descriptions.xml').read_bytes()
        if (sha256(image_data) != source['input_sha256'] or
                sha256(reference_data) != source['reference_svg_sha256'] or
                case['input_sha256'] != source['input_sha256'] or
                case['description'] != source['description'] or
                ET.fromstring(description_data).findtext('entry/beschreibung') != source['description'] or
                case['expected_objects'] != source['expected_objects']):
            raise ValueError('Changed scene input or annotations')
        row = dict(case_id=case['case_id'], input_sha256=source['input_sha256'],
                   reference_svg_sha256=source['reference_svg_sha256'],
                   expected_objects=source['expected_objects'],
                   description_sha256=sha256(source['description'].encode('utf-8')),
                   description_xml_sha256=sha256(description_data),
                   recorded_accepted=case['accepted'], seconds=case.get('elapsed_seconds'),
                   accepted=False, renderers={})
        if case.get('output_svg'):
            svg_data = evidence_path(output, case['output_svg']).read_bytes()
            if sha256(svg_data) != case['output_sha256']:
                raise ValueError('Changed saved CLI vector')
            svg = svg_data.decode('utf-8')
            image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
            parent = source['expected_objects'][0]
            x, y, w, h = parent['bbox']
            extent = parent['corner_radius']+parent['stroke_width']+3
            corners = [dict(bbox=[a, b, extent, extent]) for a in (x, x+w-extent)
                       for b in (y, y+h-extent)]
            for name, renderer in [('native', render), ('librsvg', render_librsvg)]:
                pixels = renderer(svg, case['width'], case['height'])
                frozen_render = lambda *args: pixels
                row['renderers'][name] = dict(
                    global_check=measure_quality(image, svg, render_fn=frozen_render),
                    objects=local_checks(image, svg, source['expected_objects'], render_fn=frozen_render),
                    corners=local_checks(image, svg, corners, render_fn=frozen_render))
            row.update(output_sha256=sha256(svg_data), native_objects=check_objects(svg, source['expected_objects']))
            # Keep the native radius itself reviewable, independently of pixel fit.
            native_parent = next((e for e in ET.fromstring(svg)
                if e.tag.rsplit('}', 1)[-1] == 'rect' and e.get('fill', '').startswith('url(')), None)
            row['parent_radius'] = float(native_parent.get('rx', '0')) if native_parent is not None else None
            row['parent_radius_error'] = (row['parent_radius']-parent['corner_radius']
                                          if row['parent_radius'] is not None else None)
            row['accepted'] = bool(case['accepted'] and row['native_objects']['passed'] and all(
                q['global_check']['satisfactory'] and all(v['passed'] for v in q['objects']+q['corners'])
                for q in row['renderers'].values()))
        results.append(row)
    return dict(schema='rounded_renderer_scene_audit_v1', historical=historical,
        source_sha256=report['source_sha256'],
        report_sha256=sha256((output/'report.json').read_bytes()), cases=results,
        summary=dict(completed=len(results), accepted=sum(c['accepted'] for c in results),
            recorded_accepted=sum(c['recorded_accepted'] for c in results),
            **{name+'_corners_passed': sum(q['passed'] for c in results
                for q in c['renderers'].get(name, {}).get('corners', [])) for name in ('native', 'librsvg')}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--controls', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--historical', action='store_true')
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare(args.prepare)
        return 0
    if not args.report or not (args.controls or args.inputs and args.output):
        parser.error('--report and either --controls or --inputs/--output required')
    result = check(args.controls) if args.controls else audit_scenes(args.inputs, args.output, historical=args.historical)
    with args.report.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary']))
    summary = result['summary']
    passed = (summary['globals_passed'] == summary['completed'] and
              summary['corners_passed'] == summary['corners']) if args.controls else summary['accepted'] == summary['completed']
    return 0 if passed or not args.require_all else 1


if __name__ == '__main__':
    raise SystemExit(main())
