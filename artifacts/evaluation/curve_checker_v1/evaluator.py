"""Seal/replay independent curve controls; no production or reserve execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.check_curve_scene import check_scene
from tools.curve_checker_cases import development_cases, controls

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/curve_checker_v1'
SOURCES = {
    'checker.py': ROOT/'tools/check_curve_scene.py',
    'constructions.py': ROOT/'tools/curve_checker_cases.py',
    'evaluator.py': Path(__file__),
    'strict_checker.py': ROOT/'tools/check_native_scene.py',
    'segment_checker.py': ROOT/'tools/check_segment_scene.py',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def freeze(folder):
    folder.mkdir(parents=True, exist_ok=False)
    cases = list(development_cases())
    for case in cases:
        case['controls'] = list(controls(case))
    write_json(folder/'manifest.json', dict(schema='curve_checker_freeze_v1',
        role='synthetic_development_only', cases=cases, real_reserves_executed=False,
        real_release_ready=False, hidden_omission_supported=False,
        missing_requirements=['human_annotation_audit', 'independent_real_completeness',
                              'productive_curve_group_proposals']))
    for name, source in SOURCES.items():
        (folder/name).write_bytes(source.read_bytes())
    write_json(folder/'seal.json', dict(files={name:digest(folder/name) for name in [*SOURCES, 'manifest.json']}))


def verify(folder=EVIDENCE):
    seal = json.loads((folder/'seal.json').read_text(encoding='utf-8'))
    if set(seal['files']) != set(SOURCES) | {'manifest.json'}:
        raise ValueError('Incomplete curve seal')
    for name, value in seal['files'].items():
        if digest(folder/name) != value or (name in SOURCES and digest(SOURCES[name]) != value):
            raise ValueError('Changed frozen curve evidence: '+name)
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if manifest['real_reserves_executed'] or manifest['real_release_ready']:
        raise ValueError('Invalid reserve status')
    return manifest


def evaluate(output, evidence=EVIDENCE):
    import numpy as np
    from PIL import Image
    from tools.evaluate_svg_text_baseline import render_librsvg
    from tools.run_plan_b_variations import render

    manifest = verify(evidence)
    output.mkdir(parents=True, exist_ok=False)
    positives, negatives = [], []
    for case in manifest['cases']:
        size = case['annotation']['size']
        positive = dict(case_id=case['case_id'], check=check_scene(case['svg'], case['annotation']))
        rasters = {name:fn(case['svg'], *size) for name, fn in [('MuPDF',render), ('librsvg',render_librsvg)]}
        if case['transform'] == 'plain':
            for name, raster in rasters.items():
                Image.fromarray(raster[:, :, ::-1]).save(output/(case['case_id']+'-'+name+'.png'))
        positives.append(positive)
        for control in case['controls']:
            identical = {name:bool(np.array_equal(rasters[name], fn(control['svg'], *size)))
                         for name, fn in [('MuPDF',render), ('librsvg',render_librsvg)]}
            negatives.append(dict(case_id=case['case_id'], damage=control['damage'],
                expected_hidden=control['hidden'], check=check_scene(control['svg'], case['annotation']),
                raster_identical=identical))
    summary = dict(positives=positives, negatives=negatives,
        positive_count=len(positives), negative_count=len(negatives),
        raster_identical_rejected=sum(all(r['raster_identical'].values()) and not r['check']['complete'] for r in negatives),
        sealed_files=json.loads((evidence/'seal.json').read_text(encoding='utf-8'))['files'],
        converter_executions=0, model_promotions=0, real_reserves_executed=False)
    write_json(output/'summary.json', summary)
    if (not all(r['check']['complete'] for r in positives) or any(r['check']['complete'] for r in negatives)
            or not all(all(r['raster_identical'].values()) for r in negatives if r['expected_hidden'])):
        raise AssertionError('Independent curve controls failed; inspect summary')
    print(f"{len(positives)} positive scenes; {len(negatives)} rejected controls; "
          f"{summary['raster_identical_rejected']} raster-identical under both renderers")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.freeze:
        freeze(args.freeze)
    if args.output:
        evaluate(args.output, args.evidence)


if __name__ == '__main__':
    main()
