"""Failures, source provenance and independent gates in real-output benchmarks."""
import json
from pathlib import Path

import pytest

from tools import anytime_observer as observer
from tools import run_anytime_benchmark as benchmark


def record(mode='after', seed=17, satisfactory=False, **changes):
    result = dict(case_id='case_00', mode=mode, budget_seconds=5., seed=seed,
                  split='holdout', family='label', satisfactory=satisfactory,
                  image_seconds=5., status='timeout_no_valid_output', structure=None,
                  quality=None, telemetry=dict(render_started=0))
    result.update(changes)
    return result


def test_timeouts_remain_in_quality_and_runtime_denominators():
    rows = [record(image_seconds=5.), record(seed=42, image_seconds=1., satisfactory=True,
            status='satisfactory', svg='actual.svg', quality=dict(metrics=dict(normalized_mse=.001)),
            structure=dict(passed=True), telemetry=dict(render_started=12))]
    curve = next(c for c in benchmark.summarize(rows)['curves'] if c['split'] == 'all')
    assert curve['success_rate'] == .5
    assert curve['missing_outputs'] == 1 and curve['quality_observations'] == 1
    assert curve['median_image_seconds'] == 3. and curve['p95_image_seconds'] == pytest.approx(4.8)
    assert curve['median_success_seconds'] == 1.
    assert curve['median_output_mse'] == .001  # explicitly output-conditioned


def test_pairing_uses_case_seed_and_budget_not_execution_order():
    rows = [record('after',42,True), record('before',17,True),
            record('after',17,False),record('before',42,False)]
    assert benchmark.summarize(rows)['paired'] == [dict(budget_seconds=5., pairs=2, gained=1, lost=1, both_pass=0)]


def test_interrupted_render_and_partial_last_write_are_not_successful_renders(tmp_path):
    path = tmp_path/'events.jsonl'
    path.write_text('\n'.join(json.dumps(e) for e in (
        dict(event='worker_observed',source_sha256={'src/file.py':'frozen'}),
        dict(event='render_started'),dict(event='render_finished',valid=False,active_seconds=.2),
        dict(event='render_started'),dict(event='render_failed',active_seconds=.3),
        dict(event='render_started')))+'\n{"event":',encoding='utf-8')
    summary = observer.summarize([path])
    assert summary['render_started'] == 3 and summary['render_finished'] == 1
    assert summary['render_failed'] == summary['render_invalid'] == summary['render_interrupted'] == 1
    assert summary['render_active_seconds'] == .5


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    import cv2
    from tools.run_plan_b_variations import render, measure_quality
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="180" height="110">'
           '<rect width="180" height="110" fill="white"/>'
           '<ellipse cx="90" cy="55" rx="55" ry="24" fill="none" stroke="#4b3a8c" stroke-width="3"/></svg>')
    image = render(svg,180,110)
    cv2.imwrite(str(tmp_path/'case_00.png'),image)
    (tmp_path/'out.svg').write_text(svg,encoding='utf-8')
    case = dict(case_id='case_00',image='case_00.png',input_sha256=benchmark.digest(tmp_path/'case_00.png'),
                kind='objects',family='ellipse',expected_objects=[dict(kind='ellipse',bbox=[33.5,29.5,113,51])])
    benchmark.write_json(tmp_path/'manifest.json',dict(cases=[case]))
    rows = [record(mode,satisfactory=True,status='satisfactory',svg='out.svg',
            svg_sha256=benchmark.digest(tmp_path/'out.svg'),quality=measure_quality(image,svg),
            structure=benchmark.structure(case,svg,image),telemetry=observer.summarize([]))
            for mode in ('before','after')]
    archive = dict(cases=377)
    monkeypatch.setattr(benchmark,'archive_snapshot',lambda:archive)
    report = dict(manifest_sha256=benchmark.digest(tmp_path/'manifest.json'),budgets_seconds=[5.],seeds=[17],
                  records=rows,summary=benchmark.summarize(rows),archive_before=archive,archive_after=archive,
                  baseline_source_sha256={},current_source_sha256={})
    benchmark.write_json(tmp_path/'report.json',report)
    return tmp_path,report


def test_verify_remeasures_saved_outputs(evidence):
    output,_ = evidence
    assert benchmark.verify(output)['independent_passes'] == 2


@pytest.mark.parametrize('mutation', ['missing','duplicate','forged_acceptance','source','output'])
def test_verify_rejects_incomplete_or_tampered_evidence(evidence, mutation):
    output,report = evidence
    if mutation == 'missing':
        report['records'].pop()
    elif mutation == 'duplicate':
        report['records'].append(report['records'][0])
    elif mutation == 'forged_acceptance':
        report['records'][0]['satisfactory'] = False
    else:
        with (output/('case_00.png' if mutation == 'source' else 'out.svg')).open('ab') as handle:
            handle.write(b'changed')
    benchmark.write_json(output/'report.json',report)
    with pytest.raises(ValueError):
        benchmark.verify(output)


def test_object_oracle_detects_missing_object_even_when_global_error_is_small():
    from tools.evaluate_primitive_scene import damage_probe
    probe = damage_probe()
    assert probe['metrics']['normalized_mse'] < .01
    assert not probe['object_check']['passed']


def test_paraphrases_keep_identical_frozen_pixels(tmp_path):
    cases = benchmark.prepare_cases(tmp_path)
    pair = [c for c in cases if c.get('paraphrase_group') == 'hz']
    assert len(pair) == 2 and pair[0]['description'] != pair[1]['description']
    assert pair[0]['input_sha256'] == pair[1]['input_sha256']
    assert {c['family'] for c in cases if c['split'] == 'unseen_family'} == {'ellipse','triangle'}


def test_shape_oracle_accepts_equivalent_path_and_rejects_same_box_rectangle():
    from tools.run_plan_b_variations import render
    prefix = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="white"/>'
    triangle = prefix+'<path d="M50 20 L80 80 L20 80 Z" stroke="black" stroke-width="2" fill="none" stroke-linejoin="round"/></svg>'
    rectangle = prefix+'<rect x="20" y="20" width="60" height="60" stroke="black" stroke-width="2" fill="none"/></svg>'
    case = dict(kind='objects',family='triangle',expected_objects=[dict(kind='triangle',bbox=[19,19,62,62])])
    image = render(triangle,100,100)
    assert benchmark.structure(case,triangle,image)['passed']
    assert not benchmark.structure(case,rectangle,image)['passed']


def test_object_oracle_checks_multiple_positions(tmp_path):
    from tools.run_plan_b_variations import render
    cases = benchmark.prepare_cases(tmp_path)
    # Perfect independent fixtures must pass, including the rotated three-object case.
    from tools.evaluate_primitive_scene import make_cases,rotate_cases
    for scene,case in zip((make_cases(918273,8)[-1],rotate_cases(make_cases(581321,9))[-1]),cases[4:6]):
        image = render(scene['svg'],scene['width'],scene['height'])
        assert benchmark.structure(case,scene['svg'],image)['passed']
