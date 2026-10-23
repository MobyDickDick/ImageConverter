"""Re-render frozen real transfer trials without rerunning or tuning the converter.

Exit zero confirms consistent evidence, including a negative experiment.
Use --require-all to demand positive reconstruction acceptance as well.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from tools.evaluate_layered_scene import verify_report


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path):
    root = path.resolve().parent
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if manifest.get('schema') != 'real_scene_transfer_evidence_v1':
        raise ValueError('Unsupported transfer evidence')
    if manifest.get('retuned_after_trial') is not False:
        raise ValueError('Transfer trials must not be retuned')
    for name, digest in manifest['files'].items():
        file = (root/name).resolve()
        if not file.is_relative_to(root) or not file.is_file() or _sha(file) != digest:
            raise ValueError('Missing or changed evidence: '+name)
    # Require the complete inventory, including negative outputs and raw CLI
    # telemetry. Omitting an inconvenient trial cannot shrink the denominator.
    actual_files = {p.relative_to(root).as_posix() for p in root.rglob('*')
                    if p.is_file() and p != path.resolve() and p.name != 'README.md'}
    if actual_files != set(manifest['files']):
        raise ValueError('Incomplete evidence inventory')
    freeze = json.loads((root/'freeze.json').read_text(encoding='utf-8'))
    if _sha(root/'annotations.json') != freeze['annotations_sha256']:
        raise ValueError('Annotations differ from the pre-trial freeze')
    if (root/'inputs/annotations.sha256').read_text().strip() != freeze['annotations_sha256']:
        raise ValueError('Prepared inputs differ from the annotation freeze')
    annotations = json.loads((root/'annotations.json').read_text(encoding='utf-8'))['cases']
    inputs = json.loads((root/'inputs/manifest.json').read_text(encoding='utf-8'))
    report = json.loads((root/'trial/report.json').read_text(encoding='utf-8'))
    if not annotations or len(annotations) != len(inputs) or len(inputs) != len(report['cases']):
        raise ValueError('Incomplete transfer matrix')
    if len({a['family'] for a in annotations}) != len(annotations):
        raise ValueError('Family descendants cannot count as separate families')
    runtime = {name.replace('\\', '/'): digest for name, digest in report['source_sha256'].items()}
    if not runtime or runtime != freeze['runtime_sha256']:
        raise ValueError('CLI runtime differs from the pre-trial freeze')
    if (report['commit'] != freeze['base_commit'] or report['budget_seconds'] != 5
            or report['seed'] != freeze['protocol']['seed']
            or freeze['protocol'] != dict(seed=17, iterations=64, search_seconds=5,
                search_max_seconds=5, external_timeout_seconds=30,
                attempts_per_original=1, retune_after_trial=False)):
        raise ValueError('Trial protocol differs from the pre-trial freeze')
    for annotation, case in zip(annotations, inputs):
        if any(case.get(k) != v for k, v in annotation.items()) or case['split'] != 'holdout':
            raise ValueError('Prepared oracle differs from frozen annotations')
        original = root/'originals'/annotation['file']
        if _sha(original) != annotation['source_sha256']:
            raise ValueError('Original raster changed')
        decoded = cv2.imread(str(root/'inputs'/case['case_id']/'input'/(case['case_id']+'.png')))
        if not np.array_equal(cv2.imread(str(original)), decoded):
            raise ValueError('CLI pixels differ from the decoded original')
    # The shared verifier checks saved SVG hashes, source/description identity,
    # worker reference-access guards and actual supervised five-second budgets.
    # It re-renders global, per-object and local-region quality independently.
    summary = verify_report(root/'inputs', root/'trial', write_verification=False)
    if summary['completed'] != manifest['total'] or summary['accepted'] != manifest['accepted']:
        raise ValueError('Saved verdict differs from independent evaluation')
    # Two pixel/geometry successes alone cannot certify independent lineage
    # or a human annotation audit. This limited experiment never closes the
    # overarching generalization task automatically.
    if manifest['task_complete'] is not False:
        raise ValueError('Limited transfer evidence cannot close the overall task')
    return dict(schema='real_scene_transfer_verified_v1', executes_converter=False,
                accepted=summary['accepted'], total=summary['completed'],
                task_complete=False, retuned_after_trial=False,
                independent_human_annotation_audit=False,
                historical_catalogue_exposure=True, cases=summary['cases'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-all', action='store_true')
    args = parser.parse_args()
    # Keep re-verification outputs outside the sealed evidence inventory.
    if args.output.resolve().is_relative_to(args.manifest.resolve().parent):
        parser.error('--output must be outside the sealed evidence folder')
    report = verify(args.manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(f"Evidence verified: {report['accepted']}/{report['total']} accepted")
    return int(args.require_all and report['accepted'] != report['total'])


if __name__ == '__main__':
    raise SystemExit(main())
