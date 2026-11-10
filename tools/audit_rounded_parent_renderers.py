"""Read-only corner audit of saved synthetic CLI results with two renderers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from tools.evaluate_layered_scene import evidence_path, local_checks, verify_report
from tools.evaluate_svg_text_baseline import render_librsvg
from tools.run_plan_b_variations import measure_quality, render, sha256


def audit(inputs, output):
    verify_report(inputs, output, write_verification=False)
    report_path = output/'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    cases = []
    for case in report['cases']:
        if not case['accepted']:
            continue
        reference = cv2.imread(str(inputs/case['case_id']/'input'/(case['case_id']+'.png')))
        svg = evidence_path(output, case['output_svg']).read_text(encoding='utf-8')
        parent = case['expected_objects'][0]
        x, y, w, h = parent['bbox']
        extent = parent['corner_radius']+parent['stroke_width']+3
        corners = [dict(bbox=[left, top, extent, extent])
                   for left in (x, x+w-extent) for top in (y, y+h-extent)]
        independent = render_librsvg(svg, case['width'], case['height'])
        checks = local_checks(reference, svg, corners, render_fn=lambda *args: independent)
        cases.append(dict(case_id=case['case_id'], input_sha256=case['input_sha256'],
            output_sha256=case['output_sha256'],
            global_check=measure_quality(reference, svg, render_fn=lambda *args: independent),
            native_renderer_corners=local_checks(reference, svg, corners),
            independent_renderer_corners=checks))
    # No converter or saved reference SVG is needed to reproduce this existing
    # renderer discrepancy. The ideal quarter-circle deficit is analytic.
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="360" height="360">'
           '<rect width="360" height="360" fill="white"/>'
           '<rect x="30" y="40" width="300" height="280" rx="30" fill="#555555"/></svg>')
    analytic = dict(svg=svg, radius=30., ideal_corner_deficit=(1-np.pi/4)*30**2)
    for name, renderer in [('mupdf', render), ('librsvg', render_librsvg)]:
        pixels = renderer(svg, 360, 360)
        coverage = (255-pixels[:, :, 0].astype(float))/170
        analytic[name+'_corner_deficit'] = float(np.sum(1-coverage[40:90, 30:80]))
    return dict(schema='rounded_parent_renderer_audit_v1',
        report_sha256=sha256(report_path.read_bytes()), cases=cases, analytic_control=analytic,
        summary=dict(completed=len(cases), globals_passed=sum(c['global_check']['satisfactory'] for c in cases),
            native_corners_passed=sum(q['passed'] for c in cases for q in c['native_renderer_corners']),
            independent_corners_passed=sum(q['passed'] for c in cases for q in c['independent_renderer_corners']),
            corners=4*len(cases)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.inputs, args.output)
    with args.report.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result['summary']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
