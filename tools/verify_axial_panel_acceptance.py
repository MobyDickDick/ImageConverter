"""Independently verify saved panel SVGs, inputs, budgets and paint-zone claims."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np


def check_case(root, case):
    svg = root/case['output_svg']
    document = ET.parse(svg).getroot()
    elements = list(document.iter())
    tag = lambda e: e.tag.rsplit('}', 1)[-1]
    rectangles = [e for e in elements if tag(e) == 'rect']
    gradients = [e for e in elements if tag(e) == 'linearGradient']
    assert len(rectangles) == len(gradients) == 1
    assert not any(tag(e) in {'image', 'path', 'text', 'circle', 'ellipse', 'polygon', 'line'} for e in elements)
    assert 2 <= len([e for e in gradients[0] if tag(e) == 'stop']) <= 4
    rectangle = rectangles[0]
    assert rectangle.get('stroke', 'none') == 'none'
    assert rectangle.get('fill') == f'url(#{gradients[0].get("id")})'
    assert all(float(rectangle.get(k)) > 0 for k in ('width', 'height'))
    assert case['returncode'] == 0 and case['satisfactory'] and not case['blocked_svg_reads']
    assert case['elapsed_seconds'] < 60
    return dict(case_id=case['case_id'], metrics=case['metrics'], elapsed_seconds=case['elapsed_seconds'],
                input_sha256=case['input_sha256'], output_sha256=case['output_sha256'],
                bounds={k: float(rectangle.get(k)) for k in ('x', 'y', 'width', 'height')},
                stop_count=len(gradients[0]))


def verify_run(root):
    report = json.loads((root/'report.json').read_text(encoding='utf-8'))
    assert report['status'] == 'completed' and report['summary']['passed'] == 17
    assert len({case['input_sha256'] for case in report['cases']}) == 17
    assert report['iterations'] == 64 and report['timeout_seconds'] == 60
    checked = []
    for case in report['cases']:
        record = check_case(root, case)
        # Read saved output independently of the runtime fitter and inspect
        # its pink upper highlight/lower shadow/saturation recovery in pixels.
        image = cv2.imread(str(root/case['case_id']/'output.png'))
        profile = np.median(image.astype(float), axis=1)
        assert image.shape[:2] == (case['height'], case['width'])
        b, g, r = np.median(profile, axis=0)
        assert r > g+20 and r > b+15
        assert profile[:2].mean(1).max() > profile[2:].mean(1).min()+8
        pink = profile[:, 2]-(profile[:, 0]+profile[:, 1])/2
        assert pink[-1] > pink[-2]
        assert record['bounds']['width'] > 3*record['bounds']['height']
        deadline = json.loads((root/case['case_id']/'conversion/reports'/f'{case["case_id"]}_deadline.json').read_text())
        assert deadline['candidate_evaluations'] <= 5 and deadline['time_extensions'] == 0
        record['render_evaluations'] = deadline['candidate_evaluations']
        result_map = json.loads((root/case['case_id']/'conversion/reports/conversion_result_map.json').read_text())
        record['registration'] = result_map[case['case_id']+'.png']['params']['axial_panel_registration']
        assert record['registration']['evaluations'] == deadline['candidate_evaluations']
        checked.append(record)
    return dict(seed=report['seed'], summary=report['summary'], cases=checked)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, action='append', required=True)
    parser.add_argument('--independent', type=Path, required=True)
    parser.add_argument('--summary', type=Path)
    args = parser.parse_args(argv)
    report = dict(runs=[verify_run(root) for root in args.run])
    independent = json.loads((args.independent/'summary.json').read_text(encoding='utf-8'))
    report['independent'] = [check_case(args.independent, case) for case in independent]
    assert len(report['independent']) == 8
    for record in report['independent']:
        assert abs(record['bounds']['x']-4) < .2 and abs(record['bounds']['y']-3) < .2
    if args.summary:
        args.summary.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('Verified', sum(len(run['cases']) for run in report['runs']), 'source cases and 8 unrelated CLI cases')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
