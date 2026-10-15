"""Check a saved vector's disk, converging chords and open inward spiral."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2

from tools.evaluate_diagonal_square_kelle_recheck import measure as measure_raster
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.run_plan_b_variations import measure_quality


def symbol_semantics(svg: str) -> float:
    """Independently verify converging chords and an open inward turning curve."""
    import re
    import numpy as np
    try:
        root = ET.fromstring(svg)
        shapes = [e for e in root.iter() if e.tag.rsplit('}',1)[-1] in
                  {'rect','circle','ellipse','path','polygon','line','polyline','text','image'}]
        if [e.tag.rsplit('}',1)[-1] for e in shapes] != ['rect','circle','line','line','path']:
            return 0.
        if any(e.get('transform') for e in root.iter()):
            return 0.
        _, disk, left, right, spiral = shapes
        center = np.array([float(disk.get(k,0)) for k in ('cx','cy')])
        radius = float(disk.get('r',0))
        for i,line in enumerate((left,right)):
            a,b = [np.array([float(line.get(x,0)),float(line.get(y,0))]) for x,y in (('x1','y1'),('x2','y2'))]
            if not (a[1] < center[1] < b[1] and (1 if i else -1)*(b[0]-a[0]) > 0
                    and abs(np.linalg.norm(a-center)-radius) < .01
                    and abs(np.linalg.norm(b-center)-radius) < .01
                    and float(line.get('stroke-width',0)) > 0):
                return 0.
        commands = re.findall(r'[A-Za-z]',spiral.get('d',''))
        values = np.array(list(map(float,re.findall(r'[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?',spiral.get('d','')))))
        if not (commands[0] == 'M' and 5 <= len(commands)-1 <= 10 and set(commands[1:]) == {'C'}
                and len(values) == 2+6*(len(commands)-1)):
            return 0.
        point = values[:2]; samples = [point]
        spans = []
        for controls in values[2:].reshape(-1,3,2):
            a,b,c = controls
            t = np.linspace(0,1,25)[1:,None]
            segment = (1-t)**3*point+3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3*c
            spans.append(np.linalg.norm(c-point)); samples.extend(segment); point = c
        curve = np.array(samples)
        edges = np.diff(curve,axis=0)
        turning = np.diff(np.unwrap(np.arctan2(edges[:,1],edges[:,0])))
        return float(radius > 0 and np.isfinite(curve).all()
                     and np.all(np.linalg.norm(curve-center,axis=1) < radius)
                     and np.sum(turning) < -2*np.pi and np.mean(turning < .001) > .98
                     and spans[-1] < spans[0]*.65
                     and spiral.get('fill') == 'none' and float(spiral.get('stroke-width',0)) > 0
                     and disk.get('fill','none') != 'none' and not disk.get('fill','').startswith('url('))
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
    return {'schema_version': 'spiral_disk_recheck_v1', 'baseline': baseline, 'evidence': evidence,
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
    return 0 if all(c['satisfactory'] for c in report['satisfaction_gate']['cases']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
