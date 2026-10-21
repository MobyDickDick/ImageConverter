"""Independently recheck local visibility CLI runs; retain compact evidence only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from tools.evaluate_layered_scene import verify_report
from tools.run_plan_b_variations import sha256


RUNS = {
    'development_before': ('visibility-dev-inputs', 'visibility-parent'),
    'development_after': ('visibility-dev-inputs', 'visibility-dev-cli'),
    'holdout_after': ('visibility-holdout-inputs', 'visibility-holdout-cli'),
    'holdout_renamed': ('visibility-holdout-inputs', 'visibility-rename-cli'),
    'plan_b': ('visibility-plan-b-inputs', 'visibility-plan-b-cli'),
    'ci_smoke': ('visibility-ci-inputs', 'visibility-ci-cli'),
    'contradictory_depth': ('visibility-negative-final-inputs', 'visibility-negative-final-cli'),
    'prior_fusion': ('fusion-complete-holdout-inputs', 'visibility-prior-fusion-cli'),
}
RUNTIME_MODULES = ('PrimitiveScene', 'SceneFusion', 'SceneVisibility', 'LayeredScene')


def summarize(work):
    runs = {}
    for name, (inputs, output) in RUNS.items():
        inputs, output = work/inputs, work/output
        if not (inputs/'manifest.json').is_file() or not (output/'report.json').is_file():
            raise ValueError('Full local evidence is missing; generate the documented CLI runs first')
        verified = verify_report(inputs, output, require_all=name not in ('development_before', 'contradictory_depth'))
        if name == 'contradictory_depth' and verified['accepted']:
            raise ValueError('Contradictory depth must not pass acceptance')
        if name not in ('development_before', 'contradictory_depth', 'prior_fusion'):
            if any(c['source'] != 'primitive_visibility_scene_v1' for c in verified['cases']):
                raise ValueError('Positive visibility evidence did not exercise the new runtime path')
        report = json.loads((output/'report.json').read_text(encoding='utf-8'))
        runs[name] = dict(completed=verified['completed'], accepted=verified['accepted'],
            manifest_sha256=sha256((inputs/'manifest.json').read_bytes()),
            report_sha256=sha256((output/'report.json').read_bytes()),
            source_tree_sha256=sha256(json.dumps(report['source_sha256'], sort_keys=True).encode()),
            runtime_source_sha256={p.replace('\\', '/'):h for p, h in report['source_sha256'].items()
                                   if any(p.endswith('imageCompositeConverter'+m+'.py') for m in RUNTIME_MODULES)},
            commit=report['commit'],
            mean_normalized_mse=float(np.mean([c['metrics']['normalized_mse'] for c in report['cases']])),
            cases=[{k:c[k] for k in ('case_id', 'accepted', 'output_sha256', 'elapsed_seconds')}
                   for c in report['cases']])
    a, b = runs['holdout_after']['cases'], runs['holdout_renamed']['cases']
    if any(x['output_sha256'] != y['output_sha256'] for x, y in zip(a, b)):
        raise ValueError('Rename invariance failed')
    previous = json.loads((work/'fusion-complete-holdout'/'report.json').read_text(encoding='utf-8'))['cases']
    if len(previous) != runs['prior_fusion']['completed'] or any(
            a['output_sha256'] != b['output_sha256'] for a, b in zip(runs['prior_fusion']['cases'], previous)):
        raise ValueError('Prior fusion vectors changed')
    return dict(schema_version='visibility_scene_evidence_v1', evidence_kind='real_cli',
                budget_seconds=5, search_seed=17, requested_iterations=64,
                catalog_images_added=0, runs=runs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, default=Path('.tmp'))
    parser.add_argument('--output', type=Path, default=Path('artifacts/evaluation/visibility_scene_v1/summary.json'))
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    result = summarize(args.work_dir)
    if args.verify_only:
        if json.loads(args.output.read_text(encoding='utf-8')) != result:
            raise ValueError('Compact summary differs from independently checked raw evidence')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print({name: f"{r['accepted']}/{r['completed']}" for name, r in result['runs'].items()})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
