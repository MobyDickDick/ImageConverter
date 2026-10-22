"""Re-render saved catalogue pairs and apply both unchanged satisfaction gates."""
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


def evaluate(manifest, root):
    before, after, evidence = {}, {}, []
    for case in manifest['cases']:
        image = root/case['image']
        if hashlib.sha256(image.read_bytes()).hexdigest() != case['source_sha256']:
            raise ValueError('Original source hash mismatch')
        pixels = cv2.imread(str(image))
        measurements = []
        for field in ('before_svg', 'after_svg'):
            path = root/case[field]
            measured = measure(image, path)
            if measured['svg_sha256'] != case[field+'_sha256']:
                raise ValueError('Saved CLI vector hash mismatch')
            native = check_objects(measured['svg'], case['expected_objects'])
            regions = local_checks(pixels, measured['svg'], case['expected_objects'])
            strict = measure_quality(pixels, measured['svg'])
            measured['metrics']['semantic_score'] = float(native['passed'] and strict['satisfactory']
                                                          and all(q['passed'] for q in regions))
            metrics = measured['metrics']
            measured['combined_score'] = (1-metrics['error_per_pixel']+metrics['edge_alignment']
                                          +metrics['object_mask_iou']+metrics['semantic_score'])/4
            measurements.append(measured)
        old, new = measurements
        before[case['case_id']] = dict(metrics=old['metrics'], dimensions=old['dimensions'])
        after[case['case_id']] = new
        evidence.append(dict(case_id=case['case_id'], input_sha256=case['source_sha256'],
            before_svg_sha256=old['svg_sha256'], after_svg_sha256=new['svg_sha256'],
            after_svg=case['after_svg'], before_mean_delta2=old['mean_delta2'], after_mean_delta2=new['mean_delta2']))
    baseline = seal_baseline_manifest(dict(schema_version='semantic_only_baseline_manifest_v1',
        provenance=manifest['provenance'], cases=before))
    return dict(schema='gradient_scene_catalogue_acceptance_v1', evidence=evidence,
                semantic_contract='Native rounded rectangles; outer axial gradient, inner white rectangle, bounds and painter order from frozen raster annotation; strict pixel and per-object region gates.',
                baseline=baseline, satisfaction_gate=evaluate_satisfaction(baseline, after))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(json.loads(args.manifest.read_text(encoding='utf-8')), args.manifest.parent)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(report['satisfaction_gate']['summary'])
    return 0 if all(c['satisfactory'] for c in report['satisfaction_gate']['cases']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
