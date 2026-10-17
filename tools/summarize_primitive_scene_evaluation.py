"""Verify saved primitive-scene evidence and summarize measured quality deltas."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from tools.evaluate_primitive_scene import check_objects
from tools.run_plan_b_variations import measure_quality, render, sha256


def verify_run(folder, *, require_access_file=True):
    report = json.loads((folder/'report.json').read_text(encoding='utf-8'))
    for case in report['cases']:
        assert case['returncode'] == 0 and not case['blocked_svg_reads'], case['case_id']
        log = (folder/case['case_id']/'converter.log').read_text(encoding='utf-8',errors='replace')
        assert '[INFO] Konvertiere ' in log, 'Conversion runtime was not executed: '+case['case_id']
        reference_path = folder/case['reference_svg']
        assert sha256(reference_path.read_bytes()) == case['reference_svg_sha256']
        reference = render(reference_path.read_text(encoding='utf-8'),case['width'],case['height'])
        sources = list((folder/case['case_id']/'input').rglob(case['case_id']+'.png'))
        assert len(sources) == 1 and sha256(sources[0].read_bytes()) == case['input_sha256']
        np.testing.assert_array_equal(cv2.imread(str(sources[0])),reference)
        access_path = folder/case['case_id']/'reference_access.json'
        if require_access_file or access_path.exists():
            access = json.loads(access_path.read_text(encoding='utf-8'))
            assert not access['blocked_svg_reads']
        svg_path = folder/case['output_svg']
        assert sha256(svg_path.read_bytes()) == case['output_sha256']
        svg = svg_path.read_text(encoding='utf-8')
        measured = measure_quality(reference,svg)
        assert measured['metrics'] == case['metrics'],case['case_id']
        assert measured['satisfactory'] == case['satisfactory'],case['case_id']
        if 'expected_objects' in case:
            assert check_objects(render(svg,case['width'],case['height']),case['expected_objects']) == case['object_check']
    return report


def compare(before, after):
    assert len(before['cases']) == len(after['cases'])
    assert before.get('generation') == after.get('generation')
    rows = []
    for a,b in zip(before['cases'],after['cases']):
        assert a['case_id'] == b['case_id'] and a['input_sha256'] == b['input_sha256']
        assert a['description'] == b['description'] and a['reference_svg_sha256'] == b['reference_svg_sha256']
        mse_a, mse_b = a['metrics']['normalized_mse'],b['metrics']['normalized_mse']
        rows.append(dict(case_id=a['case_id'],before_mse=mse_a,after_mse=mse_b,
                         mse_reduction_percent=100*(1-mse_b/mse_a) if mse_a else 0.,
                         before_passed=a['satisfactory'],after_passed=b['satisfactory'],
                         after_objects_passed=b.get('object_check',{}).get('passed'),
                         metric_deltas={key:b['metrics'][key]-value for key,value in a['metrics'].items()}))
    mean_a = sum(r['before_mse'] for r in rows)/len(rows)
    mean_b = sum(r['after_mse'] for r in rows)/len(rows)
    return dict(case_count=len(rows),before_passed=sum(r['before_passed'] for r in rows),
                after_passed=sum(r['after_passed'] for r in rows),
                before_mean_mse=mean_a,after_mean_mse=mean_b,
                mean_mse_reduction_percent=100*(1-mean_b/mean_a),
                mse_regressions=[r['case_id'] for r in rows if r['after_mse']>r['before_mse']+1e-10],
                cases=rows)


def verify_archive(folder):
    """Keep absolute quality acceptance distinct from preservation of bests."""
    from tools.evaluate_diagonal_square_kelle_recheck import measure
    root = Path(__file__).resolve().parents[1]
    archive = root/'artifacts/satisfactory_conversions'
    report = json.loads((folder/'report.json').read_text(encoding='utf-8'))
    index = json.loads((archive/'index.json').read_text(encoding='utf-8'))
    originals = {c['variant']:c for c in index['cases']}
    assert {c['variant'] for c in report['cases']} == set(originals)
    for case in report['cases']:
        image,svg = archive/case['source_image'],folder/case['output_svg']
        assert sha256(image.read_bytes()) == case['source_sha256']
        assert sha256(svg.read_bytes()) == case['output_sha256']
        measured = measure(image,svg)
        assert measured['mean_delta2'] == case['mean_delta2']
        assert case['baseline_mean_delta2'] == originals[case['variant']]['mean_delta2']
        preserved = case['mean_delta2'] <= case['baseline_mean_delta2']+max(1e-6,case['baseline_mean_delta2']*1e-6)
        assert preserved == case['preserves_saved_best']
    comparison = json.loads((folder/'compatibility_comparison.json').read_text(encoding='utf-8'))
    for case in comparison['cases']:
        old_svg,new_svg = folder/case['old_svg'],folder/case['new_svg']
        assert sha256(old_svg.read_bytes()) == case['old_svg_sha256']
        source = archive/originals[case['variant']]['image']
        height,width = cv2.imread(str(source)).shape[:2]
        np.testing.assert_array_equal(render(old_svg.read_text(encoding='utf-8'),width,height),
                                      render(new_svg.read_text(encoding='utf-8'),width,height))
    worsened = [c for c in report['cases'] if not c['preserves_saved_best']]
    return dict(case_count=report['case_count'],pixel_gate_passed=report['pixel_gate_passed'],
                preserves_saved_best=report['preserves_saved_best'],saved_best_regressions=len(worsened),
                max_saved_best_mean_delta2_increase_percent=max(c['historical_mean_delta2_increase_percent'] for c in worsened),
                compatibility_cases=comparison['case_count'],compatibility_old_new_pixel_identical=comparison['pixel_identical'],
                compatibility_new_code_regressions=comparison['new_code_regressions'])


def summarize(folder):
    roles = json.loads((folder/'runs.json').read_text(encoding='utf-8'))
    baseline = verify_run(folder/roles['development_before'])
    after = verify_run(folder/roles['development_after'])
    holdout_baseline = verify_run(folder/roles['holdout_before'])
    holdout = verify_run(folder/roles['holdout_after'])
    renamed = verify_run(folder/roles['rename_after'])
    assert after['source_sha256'] == holdout['source_sha256'] == renamed['source_sha256']
    rename_matches = []
    for a,b in zip(holdout['cases'],renamed['cases']):
        assert a['case_id'] == b['original_case_id']
        assert a['input_sha256'] == b['input_sha256']
        assert a['output_sha256'] == b['output_sha256']
        rename_matches.append(a['case_id'])
    original = Path('artifacts/evaluation/reconstruction_bottlenecks_2026-10-17/evidence')
    # The previous task retained audit results in report.json, not raw audit files.
    old_six = verify_run(original,require_access_file=False)
    new_six = verify_run(folder/roles['previous_diagnostics_after'])
    result = dict(evidence_kind='independently_rerendered_real_cli',
                  development=compare(baseline,after), holdout=compare(holdout_baseline,holdout),
                  previous_diagnostics=compare(old_six,new_six),
                  rename_identical=len(rename_matches),damage_probe=after['damage_probe'],
                  limitations=['24 synthetic separated outline scenes and six previous diagnostics; not a representative catalog benchmark.',
                               'The deliberately removed small object demonstrates a possible false positive, not its prevalence.',
                               'All CLI runs request 64 iterations. Analytic fitters use their own bounded render searches.',
                               'Concurrent local timings do not support a speedup claim.',
                               'Existing candidate-merge/fusion helpers and broader topology search are unchanged.'])
    damage_path = folder/'quality_damage'/'report.json'
    if damage_path.exists():
        damage = json.loads(damage_path.read_text(encoding='utf-8'))
        assert damage['executes_converter'] is False
        for case in damage['cases']:
            source = (damage_path.parent/(case['case_id']+'_reference.svg')).read_bytes()
            output = (damage_path.parent/(case['case_id']+'_damaged.svg')).read_bytes()
            assert sha256(source) == case['reference_sha256'] and sha256(output) == case['damaged_sha256']
            measured = measure_quality(render(source.decode(),240,160),output.decode())
            assert measured['metrics'] == case['metrics'] and measured['satisfactory'] == case['pixel_gate_passed']
        result['controlled_damage'] = {k:v for k,v in damage.items() if k != 'cases'}
    if (folder/'archive_recheck'/'compatibility_comparison.json').exists():
        result['archive_check'] = verify_archive(folder/'archive_recheck')
    (folder/'summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    args = parser.parse_args()
    result = summarize(args.folder)
    print(json.dumps({key:{k:v for k,v in result[key].items() if k != 'cases'}
                      for key in ('development','holdout','previous_diagnostics','archive_check')
                      if key in result},indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
