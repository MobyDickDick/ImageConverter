"""Independently check analytic sine diagrams with unchanged satisfaction gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.run_plan_b_variations import measure_quality


def symbol_semantics(svg: str) -> float:
    """Check axes and a smooth, single-valued wave independently of the fitter."""
    import re
    try:
        root = ET.fromstring(svg)
        shapes = [e for e in root.iter() if e.tag.rsplit('}',1)[-1] in
                  {'rect','path','line','polyline','polygon','circle','ellipse','image','text'}]
        if [e.tag.rsplit('}',1)[-1] for e in shapes] != ['rect','path','path']:
            return 0.
        if any(e.get('transform') or e.get('opacity','1') != '1' for e in root.iter()):
            return 0.
        bg, axes, wave = shapes
        if not re.fullmatch(r'M [-.0-9]+ [-.0-9]+ V [-.0-9]+ H [-.0-9]+', axes.get('d','')):
            return 0.
        coords = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', axes.get('d',''))]
        if len(coords) != 4:
            return 0.
        x, top, bottom, right = coords
        tokens = re.findall(r'[A-Za-z]|-?\d+(?:\.\d+)?', wave.get('d',''))
        if tokens[0] != 'M' or (len(tokens)-3)%7 or not 4 <= (len(tokens)-3)//7 <= 24:
            return 0.
        point = np.array([float(tokens[1]),float(tokens[2])]); samples = [point]
        for start in range(3,len(tokens),7):
            if tokens[start] != 'C': return 0.
            control = np.array(list(map(float,tokens[start+1:start+7]))).reshape(3,2)
            if not point[0] < control[0,0] < control[1,0] < control[2,0]: return 0.
            for t in np.linspace(0,1,13)[1:]:
                samples.append((1-t)**3*point+3*(1-t)**2*t*control[0]+3*(1-t)*t*t*control[1]+t**3*control[2])
            point = control[2]
        points = np.array(samples)
        dy = np.diff(points[:,1]); turns = np.count_nonzero(dy[:-1]*dy[1:]<0)
        return float(bg.get('fill')=='#ffffff' and top<bottom and x<right
            and points[:,1].max()<bottom and points[:,1].min()>top
            and turns == 2 and np.ptp(points[:,1]) > 1
            and all(e.get('fill')=='none' and float(e.get('stroke-width','0'))>0 for e in (axes,wave)))
    except (ET.ParseError,ValueError,TypeError,IndexError):
        return 0.


def measure(image: Path, svg: Path) -> dict:
    record = measure_raster(image, svg)
    m = record['metrics']
    m['semantic_score'] = symbol_semantics(record['svg'])
    record['combined_score'] = (1-m['error_per_pixel']+m['edge_alignment']+m['object_mask_iou']+m['semantic_score'])/4
    return record


def evaluate(manifest: dict, root: Path) -> dict:
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root/case['image']
        old, new = (measure(image, root/case[mode+'_svg']) for mode in ('before', 'after'))
        before[case['case_id']] = {'metrics': old['metrics'], 'dimensions': old['dimensions']}
        after[case['case_id']] = new
        evidence.append({**case, 'input_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                         'before_mean_delta2': old['mean_delta2'], 'after_mean_delta2': new['mean_delta2'],
                         'before_svg_sha256': old['svg_sha256'], 'after_svg_sha256': new['svg_sha256']})
    baseline = seal_baseline_manifest({'schema_version': 'semantic_only_baseline_manifest_v1',
        'provenance': {**manifest['provenance'], 'input_hashes': {e['case_id']: e['input_sha256'] for e in evidence}},
        'cases': before})
    strict = {case['case_id']: measure_quality(cv2.imread(str(root/case['image'])),
                  (root/case['after_svg']).read_text(encoding='utf-8')) for case in manifest['cases']}
    return {'schema_version': 'sine_diagram_recheck_v1', 'baseline': baseline, 'evidence': evidence,
            'satisfaction_gate': evaluate_satisfaction(baseline, after),
            'strict_pixel_gates': strict,
            'measurement': {'foreground_threshold': 210, 'canny_thresholds': [50, 140],
                            'output': 'saved CLI SVG re-rendered with production renderer'}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(json.loads(args.manifest.read_text(encoding='utf-8')), args.manifest.parent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report['satisfaction_gate']['summary'], sort_keys=True))
    return 0 if (all(c['satisfactory'] for c in report['satisfaction_gate']['cases'])
                 and all(c['satisfactory'] for c in report['strict_pixel_gates'].values())) else 2


if __name__ == '__main__':
    raise SystemExit(main())
