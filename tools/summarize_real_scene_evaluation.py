"""Re-render real-scene experiment outputs before writing compact evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np

from tools.evaluate_layered_scene import verify_report

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(run):
    matrix = [('parent-language', 'dev-frozen-inputs', 0, 12),
              ('parent-real', 'real-inputs', 0, 4),
              ('final-language', 'dev-frozen-inputs', 12, 12),
              ('final-holdout', 'holdout-inputs', 12, 12),
              ('final-rename', 'holdout-inputs', 12, 12),
              ('final-sealed', 'sealed-final-inputs', 12, 12),
              ('final-sealed-rename', 'sealed-final-inputs', 12, 12),
              ('final-plan-b', 'plan-b-inputs', 17, 17),
              ('final-negative', 'negative-inputs', 0, 6),
              ('final-challenge', 'real-inputs', 0, 4),
              ('final-ci', 'ci-inputs', 6, 6),
              ('plan-b-cli', 'plan-b-inputs', 1, 17)]
    groups = {}
    for name, inputs, accepted, count in matrix:
        verified = verify_report(run/inputs, run/name)
        if (verified['accepted'], verified['completed']) != (accepted, count):
            raise ValueError('Unexpected independent result: '+name)
        report = json.loads((run/name/'report.json').read_text(encoding='utf-8'))
        if name.startswith('final-') and any(digest(ROOT/p) != sha for p, sha in report['source_sha256'].items()):
            raise ValueError('Runtime changed after final evidence: '+name)
        runtime = {p: h for p, h in report['source_sha256'].items()
                   if Path(p).name in ('imageCompositeConverterSceneVisibility.py',
                                       'imageCompositeConverterSceneReferences.py',
                                       'imageCompositeConverterLayeredScene.py')}
        groups[name] = dict(accepted=accepted, count=count, input_manifest_sha256=digest(run/inputs/'manifest.json'),
                            report_sha256=digest(run/name/'report.json'),
                            runtime_sha256=runtime,
                            all_source_sha256=hashlib.sha256(json.dumps(report['source_sha256'], sort_keys=True).encode()).hexdigest(),
                            output_sha256=[c.get('output_sha256') for c in report['cases']])
        if name in ('parent-real', 'final-challenge'):
            groups[name]['global_pixel_passes'] = sum(bool(c['satisfactory']) for c in report['cases'])
            if groups[name]['global_pixel_passes']:
                raise ValueError('Revisit real-scene interpretation: a pixel gate passed')
    if groups['final-holdout']['output_sha256'] != groups['final-rename']['output_sha256']:
        raise ValueError('Renaming changed outputs')
    if groups['final-sealed']['output_sha256'] != groups['final-sealed-rename']['output_sha256']:
        raise ValueError('Renaming changed sealed outputs')
    annotation_path = ROOT/'config/real_scene_families.json'
    annotations = digest(annotation_path)
    corrected = json.loads(annotation_path.read_text(encoding='utf-8'))
    frozen_digest = (run/'real-inputs/annotations.sha256').read_text().strip()
    if frozen_digest != corrected['selection_audit']['frozen_annotation_sha256'] or digest(run/'frozen-annotations.json') != frozen_digest:
        raise ValueError('Frozen real annotation evidence changed')
    frozen_cases = json.loads((run/'real-inputs/manifest.json').read_text(encoding='utf-8'))
    if len(frozen_cases) != len(corrected['cases']):
        raise ValueError('Real case population changed')
    for frozen, current in zip(frozen_cases, corrected['cases']):
        for key in ('file', 'source_sha256', 'description', 'expected_objects'):
            if frozen[key] != current[key]:
                raise ValueError('Real oracle changed after runtime development')
    tests = {}
    collected = json.loads((run/'collected-final.json').read_text(encoding='utf-8'))
    for path, sha in collected['test_source_sha256'].items():
        if digest(ROOT/path) != sha:
            raise ValueError('Tests changed after the completion collection')
    expected_ids = set()
    for node in collected['nodeids']:
        parts = node.split('::')
        classname = parts[0][:-3].replace('/', '.')+''.join('.'+part for part in parts[1:-1])
        expected_ids.add((classname, parts[-1]))
    if len(expected_ids) != len(collected['nodeids']):
        raise ValueError('Completion collection contains duplicate test IDs')
    for name in ('scene-accepted', 'standard'):
        path = run/(name+'.xml')
        suite = ET.parse(path).getroot().find('testsuite')
        tests[name] = {key: int(suite.get(key, '0')) for key in ('tests', 'failures', 'errors', 'skipped')}
        tests[name].update(xml_sha256=digest(path), seconds=float(suite.get('time')))
        if tests[name]['failures'] or tests[name]['errors']:
            raise ValueError('Test failures remain: '+name)
        actual_ids = [(case.get('classname'), case.get('name')) for case in suite.findall('testcase')]
        if name == 'standard' and (len(actual_ids) != len(expected_ids) or set(actual_ids) != expected_ids):
            raise ValueError('Standard suite XML does not contain every collected test exactly once')
    archive = json.loads((run/'archive-recheck/report.json').read_text())
    if archive['passed'] != archive['case_count'] or archive['case_count'] != 377:
        raise ValueError('Archive acceptance regressed')
    previous_path = run/'previous-archive-report.json'
    previous = {c['variant']: c for c in json.loads(previous_path.read_text())['cases']}
    differences = [dict(variant=c['variant'], before_mean_delta2=previous[c['variant']]['mean_delta2'],
                        after_mean_delta2=c['mean_delta2']) for c in archive['cases']
                   if c['mean_delta2'] != previous[c['variant']]['mean_delta2']]
    before = json.loads((run/'archive-before.json').read_text())
    after = {p.as_posix(): digest(p) for p in (ROOT/'artifacts/satisfactory_conversions').rglob('*') if p.is_file()}
    # The snapshot uses repository-relative paths, irrespective of caller cwd.
    after = {str(Path(p).relative_to(ROOT)).replace('\\', '/'): h for p, h in after.items()}
    if before != after:
        raise ValueError('Stored archive changed')
    from src.iCCModules.imageCompositeConverterSceneVisibility import requested
    archived = json.loads((ROOT/'artifacts/satisfactory_conversions/index.json').read_text())
    activated = sum(requested(c['description']) for c in archived['cases'])
    if activated:
        raise ValueError('Archive descriptions activate the new scene path')
    static = json.loads((run/'static-checks.json').read_text())
    if len(static) != 4 or any(c['returncode'] for c in static):
        raise ValueError('Static completion checks are missing or failed')
    for i, check in enumerate(static):
        captured = (run/f'static-{i}.log').read_text(encoding='utf-8')
        if hashlib.sha256(captured.encode()).hexdigest() != check['output_sha256']:
            raise ValueError('Static completion log changed')
    return dict(schema='real_scene_evaluation_v1', groups=groups, annotations_sha256=annotations,
                toolchain=dict(python=sys.version.split()[0], numpy=np.__version__,
                               opencv=cv2.__version__, pymupdf=fitz.VersionBind),
                static_checks=static,
                frozen_annotations_sha256=frozen_digest, family_selection_audit=corrected['selection_audit'],
                effective_real_partitions={c['file']:c['split'] for c in corrected['cases']},
                previous_neural_annotations_sha256=digest(ROOT/'config/neural_real_regions.json'),
                collected_test_count=len(expected_ids), collected_manifest_sha256=digest(run/'collected-final.json'),
                tests=tests, archive=dict(passed=archive['passed'], count=archive['case_count'],
                preserved_files=len(before), higher_than_stored_best=len(archive['higher_mean_delta2']),
                new_route_activations=activated,
                previous_report_sha256=digest(previous_path), differences_from_previous=differences,
                report_sha256=digest(run/'archive-recheck/report.json')),
                catalog_accepted=377, catalog_total=1785, new_real_acceptances=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=ROOT/'.tmp/real05')
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/evaluation/real_scene_v1/summary.json')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    summary = summarize(args.run)
    if args.verify_only:
        if json.loads(args.output.read_text()) != summary:
            raise ValueError('Compact evidence differs from independently verified runs')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Independent CLI evidence, tests and archive verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
