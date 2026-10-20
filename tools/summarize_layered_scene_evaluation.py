"""Retain compact, independently replayable evidence from the layered CLI matrix."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import cv2
import numpy as np

from tools.evaluate_layered_scene import check_objects, local_checks, verify_report
from tools.run_plan_b_variations import measure_quality, render, sha256


DATASETS = {'development': 'general-scene-inputs',
            'holdout': 'general-scene-blind-final',
            'plan_b': 'general-scene-plan-b-final'}
RUNS = [('development_before', 'development', 'general-scene-before-5s'),
        ('development_after', 'development', 'general-scene-final-development'),
        ('holdout_before', 'holdout', 'general-scene-final-before'),
        ('holdout_after', 'holdout', 'general-scene-final-holdout'),
        ('holdout_renamed', 'holdout', 'general-scene-final-renamed'),
        ('plan_b', 'plan_b', 'general-scene-final-plan-b')]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def verify(output):
    manifest, summary = read(output/'manifest.json'), read(output/'summary.json')
    sources = {}
    for dataset, cases in manifest['datasets'].items():
        for case in cases:
            path = output/case['image']
            if sha256(path.read_bytes()) != case['input_sha256']:
                raise ValueError('Frozen raster hash mismatch')
            sources[dataset, case['case_id']] = case
    for name, run in summary['runs'].items():
        expected_ids = {c['case_id'] for c in manifest['datasets'][run['dataset']]}
        if {c['original_case_id'] for c in run['cases']} != expected_ids or len(run['cases']) != len(expected_ids):
            raise ValueError('Incomplete compact matrix')
        accepted_count = 0
        for result in run['cases']:
            case = sources[run['dataset'], result['original_case_id']]
            if result['runtime']['guard'] != {'blocked_svg_reads': []}:
                raise ValueError('Missing or violated worker guard observation')
            control = result['runtime']['adaptive_search']
            if not control.get('isolated') or control['limit_seconds'] != 5 or control['max_seconds'] != 5:
                raise ValueError('Missing five-second observation')
            path = output/result['svg']
            if sha256(path.read_bytes()) != result['output_sha256']:
                raise ValueError('Saved SVG hash mismatch')
            svg = path.read_text(encoding='utf-8')
            image = cv2.imread(str(output/case['image']))
            accepted = bool(result['returncode'] == 0 and measure_quality(image, svg)['satisfactory']
                            and check_objects(svg, case['expected_objects'])['passed']
                            and all(q['passed'] for q in local_checks(image, svg, case['expected_objects'])))
            if accepted != result['accepted']:
                raise ValueError('Compact decision differs from saved raster/vector pair')
            accepted_count += accepted
        if accepted_count != run['accepted']:
            raise ValueError('Compact total differs from individual decisions')
    base = summary['runs']['holdout_after']['cases']
    renamed = summary['runs']['holdout_renamed']['cases']
    if any(a['output_sha256'] != b['output_sha256'] for a, b in zip(base, renamed)):
        raise ValueError('Rename invariance failed')
    print('Compact evidence verified:', {name: run['accepted'] for name, run in summary['runs'].items()})


def build(work, output):
    output.mkdir(parents=True, exist_ok=False)
    manifest = dict(schema_version='layered_scene_inputs_v1', datasets={})
    for dataset, folder in DATASETS.items():
        cases = read(work/folder/'manifest.json')
        retained = []
        for case in cases:
            relative = Path('sources')/dataset/(case['case_id']+'.png')
            target = output/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(work/folder/case['case_id']/'input'/(case['case_id']+'.png'), target)
            entry = dict(case, image=relative.as_posix())
            entry.pop('reference_svg', None)  # Raw generator vectors remain in the work directory.
            retained.append(entry)
        manifest['datasets'][dataset] = retained
    write(output/'manifest.json', manifest)
    summary = dict(schema_version='layered_scene_evidence_v1', evidence_kind='real_cli',
                   budget_seconds=5, search_seed=17, iterations=64, runs={})
    for name, dataset, folder in RUNS:
        directory = work/folder
        verify_report(work/DATASETS[dataset], directory, require_all='before' not in name)
        report = read(directory/'report.json')
        retained = []
        for original, result in zip(manifest['datasets'][dataset], report['cases']):
            case_folder = directory/result['case_id']
            rows = read(case_folder/'conversion/reports/conversion_result_map.json')
            row = next(iter(rows.values()))
            path = Path('vectors')/name/(result['case_id']+'.svg')
            target = output/path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(directory/result['output_svg'], target)
            kept = {k: result[k] for k in ('case_id', 'accepted', 'returncode', 'failures', 'satisfactory',
                                         'metrics', 'object_check', 'local_checks', 'output_sha256', 'elapsed_seconds')}
            kept.update(svg=path.as_posix(), original_case_id=original['case_id'],
                        runtime=dict(adaptive_search=row['params']['adaptive_search'],
                                     guard=row['reference_access'],
                                     registration=row['params'].get('primitive_scene_registration')))
            retained.append(kept)
        summary['runs'][name] = dict(dataset=dataset, cases=retained, accepted=sum(c['accepted'] for c in retained),
                                     source_sha256=report['source_sha256'], parent_commit=report['commit'])
    write(output/'summary.json', summary)
    # Four illustrative rows; full numeric decisions remain above.
    rows = []
    for dataset, index in [('development', 3), ('development', 4), ('holdout', 7), ('holdout', 11)]:
        case = manifest['datasets'][dataset][index]
        images = [cv2.imread(str(output/case['image']))]
        for arm in ('before', 'after'):
            result = summary['runs'][dataset+'_'+arm]['cases'][index]
            images.append(render((output/result['svg']).read_text(encoding='utf-8'), case['width'], case['height']))
        tiles = []
        for label, image in zip(('Source', 'Before', 'After'), images):
            tile = np.full((210, 260, 3), 255, 'uint8')
            factor = min(240/image.shape[1], 170/image.shape[0])
            resized = cv2.resize(image, (round(image.shape[1]*factor), round(image.shape[0]*factor)))
            tile[30:30+resized.shape[0], 10:10+resized.shape[1]] = resized
            cv2.putText(tile, label, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, .5, (40, 40, 40), 1)
            tiles.append(tile)
        rows.append(cv2.hconcat(tiles))
    assert cv2.imwrite(str(output/'comparison.png'), cv2.vconcat(rows))
    verify(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, default=Path('.tmp'))
    parser.add_argument('--output', type=Path, default=Path('artifacts/evaluation/layered_scene_v1'))
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        verify(args.output)
    else:
        build(args.work_dir, args.output)


if __name__ == '__main__':
    main()
