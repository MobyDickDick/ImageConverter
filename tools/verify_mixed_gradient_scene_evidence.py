"""Re-render retained originals and vectors, including the failed first transfer.

This verifies stored production outputs. It does not run a converter or turn
development cases into independent held-out families.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2

from tools.evaluate_diagonal_square_kelle_recheck import measure
from tools.evaluate_layered_scene import check_objects, local_checks
from tools.evaluate_satisfaction_gate import evaluate_satisfaction, seal_baseline_manifest
from tools.run_plan_b_variations import measure_quality


def verified_file(root, record):
    path = root/record['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
        raise ValueError('Stored evidence hash mismatch: '+record['path'])
    return path


def verify(manifest_path):
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    annotations = json.loads(verified_file(root, manifest['initial_annotations']).read_text(encoding='utf-8'))
    if len(manifest['cases']) != len(annotations['cases']) or not manifest['cases']:
        raise ValueError('Incomplete real comparison')
    for phase, name in (('first_transfer', 'first-freeze.json'),
                        ('after_development', 'final-freeze.json')):
        freeze = json.loads((root/name).read_text(encoding='utf-8'))
        if any(c[phase]['cli_source_sha256'] != freeze['runtime_sha256'] for c in manifest['cases']):
            raise ValueError('CLI sources differ from recorded runtime freeze')
    measured, baseline, candidates = [], {}, {}
    for case, annotation in zip(manifest['cases'], annotations['cases']):
        if case['file'] != annotation['file'] or case['description'] != annotation['description']:
            raise ValueError('Frozen source or description changed')
        image = verified_file(root, case['image'])
        if case['image']['sha256'] != annotation['source_sha256']:
            raise ValueError('Original raster identity changed')
        pixels = cv2.imread(str(image))
        phases = {}
        for phase in ('before', 'first_transfer', 'after_development'):
            vector = verified_file(root, case[phase])
            svg = vector.read_text(encoding='utf-8')
            strict = measure_quality(pixels, svg)
            objects = check_objects(svg, annotation['expected_objects'])
            regions = local_checks(pixels, svg, annotation['expected_objects'])
            passed = bool(strict['satisfactory'] and objects['passed'] and all(r['passed'] for r in regions))
            if passed != case[phase]['accepted']:
                raise ValueError('Saved real decision differs from independent evaluation')
            phases[phase] = dict(accepted=passed, strict_quality=strict,
                                 objects=objects, regions=regions)
            if phase in ('before', 'after_development'):
                result = measure(image, vector)
                result['metrics']['semantic_score'] = float(passed)
                m = result['metrics']
                result['combined_score'] = (1-m['error_per_pixel']+m['edge_alignment']+
                                           m['object_mask_iou']+m['semantic_score'])/4
                if phase == 'before':
                    baseline[case['file']] = dict(metrics=m, dimensions=result['dimensions'])
                else:
                    candidates[case['file']] = result
        measured.append(dict(file=case['file'], phases=phases))
    sealed = seal_baseline_manifest(dict(schema_version='semantic_only_baseline_manifest_v1',
        provenance=manifest['provenance'], cases=baseline))
    gate = evaluate_satisfaction(sealed, candidates)
    summary = {phase: dict(accepted=sum(c['phases'][phase]['accepted'] for c in measured),
                           total=len(measured)) for phase in ('before', 'first_transfer', 'after_development')}
    return dict(schema='mixed_gradient_scene_verified_v1', evidence_kind='stored_real_cli_development',
                executes_converter=False, measures_raster_quality=True,
                new_heldout_real_families_after_tuning=0, summary=summary,
                satisfaction_gate=gate, cases=measured)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.manifest)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(report['summary'])
    print(report['satisfaction_gate']['summary'])
    return 0 if all(c['satisfactory'] for c in report['satisfaction_gate']['cases']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
