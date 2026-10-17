"""Retain compact, independently verifiable CLI evidence without scratch reports."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.evaluate_labeled_square_recheck import evaluate
from tools.run_plan_b_variations import measure_quality
import cv2


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_case_outputs(source, destination, *, diagnostic=False):
    report = read(source/'report.json')
    destination.mkdir(exist_ok=True)
    results = []
    for case in report['cases']:
        name = case['case_id']
        entry = {key: value for key, value in case.items() if key not in
                 ('command', 'output_svg', 'reference_svg', 'converter_log_tail')}
        # Every final case retains pixels, actual vector, reference and CLI log.
        # Failed experiments retain the same evidence for failed cases only.
        if not diagnostic or not case['satisfactory']:
            folder = destination/name
            folder.mkdir(exist_ok=True)
            for original, target, key in (
                (source/case['output_svg'], folder/'output.svg', 'output_svg'),
                (source/case['reference_svg'], folder/'reference.svg', 'reference_svg'),
                (source/name/'input'/(name+'.png'), folder/'input.png', 'input_png'),
                (source/name/'converter.log', folder/'converter.log', 'converter_log'),
            ):
                shutil.copyfile(original, target)
                entry[key] = target.relative_to(destination).as_posix()
            mapping = read(source/name/'conversion/reports/conversion_result_map.json')
            params = next(iter(mapping.values())).get('params', {})
            entry['registration'] = params.get('labeled_square_registration')
        results.append(entry)
    report['cases'] = results
    report.pop('selection', None)
    report['artifact_retention'] = 'failed_cases' if diagnostic else 'all_input_reference_output_log_pairs'
    save(destination/'report.json', report)
    return report


def main():
    manifest = read(FOLDER/'manifest.json')
    fresh = ROOT/'.tmp/ls-sealed'
    replay = ROOT/'.tmp/ls-sealed-replay'
    frozen = read(FOLDER/'frozen/manifest.json')
    current = read(fresh/'manifest.json')
    repeated = read(replay/'manifest.json')
    for old, new, again, case in zip(frozen['cases'], current['cases'], repeated['cases'], manifest['cases']):
        assert sha(FOLDER/'frozen'/old['before_svg']) == sha(fresh/new['before_svg'])
        assert sha(fresh/new['after_svg']) == sha(replay/again['after_svg'])
        for mode in ('before', 'after'):
            target = FOLDER/(mode+'.svg')
            shutil.copyfile(fresh/new[mode+'_svg'], target)
            case[mode+'_svg'] = target.name
    save(FOLDER/'manifest.json', manifest)
    for mode in ('before', 'after'):
        shutil.copyfile(fresh/(mode+'.log'), FOLDER/(mode+'.log'))
    report = evaluate(manifest, FOLDER)
    image = cv2.imread(str(FOLDER/manifest['cases'][0]['image']))
    strict = measure_quality(image, (FOLDER/'after.svg').read_text(encoding='utf-8'))
    assert strict['satisfactory']
    assert all(c['satisfactory'] for c in report['satisfaction_gate']['cases'])
    report['strict_pixel_gate'] = strict
    report['frozen_baseline_and_replay_match'] = True
    report['reference_access'] = read(fresh/'report.json')['reference_access']
    mapping = read(fresh/'after/reports/conversion_result_map.json')
    report['registration'] = next(iter(mapping.values()))['params']['labeled_square_registration']
    save(FOLDER/'acceptance.json', report)
    copy_case_outputs(ROOT/'.tmp/ls-independent-initial', FOLDER/'diagnostics_initial', diagnostic=True)
    copy_case_outputs(ROOT/'.tmp/ls-independent-final', FOLDER/'diagnostics_absolute_error', diagnostic=True)
    final = copy_case_outputs(ROOT/'.tmp/ls-independent-sealed', FOLDER/'independent')
    other = copy_case_outputs(ROOT/'.tmp/ls-independent-sealed-replay', FOLDER/'independent_second_seed')
    assert final['summary']['satisfactory'] and other['summary']['satisfactory']
    catalog = ROOT/'.tmp/ls-catalog-sealed'
    target = FOLDER/'catalog_context'
    target.mkdir(exist_ok=True)
    for filename in ('report.json', 'baseline.svg', 'old_catalog_current_runtime.svg', 'final.svg',
                     'baseline.log', 'old_catalog_current_runtime.log', 'final.log'):
        shutil.copyfile(catalog/filename, target/filename)
    assert sha(target/'final.svg') == sha(FOLDER/'after.svg')
    save(FOLDER/'source_sha256.json', {p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'src').rglob('*.py')})
    print('Sealed catalog gates, baseline/replay, two independent 17-case CLI batteries and diagnostics')


if __name__ == '__main__':
    main()
