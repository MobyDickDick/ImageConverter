"""Negative scene evidence explains failures without certifying a conversion."""
import hashlib
import json
from pathlib import Path

import pytest

from tools.evaluate_layered_scene import verify_report
from tools.run_seeded_scene_check import preserve_failure


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


@pytest.fixture
def negative_scene(tmp_path):
    inputs, output = tmp_path/'inputs', tmp_path/'output'
    original = inputs/'sample/input/sample.png'
    original.parent.mkdir(parents=True)
    original.write_bytes(b'no rendering is necessary to verify absence')
    case = dict(case_id='sample', input_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                description='A circle.', expected_objects=[])
    write_json(inputs/'manifest.json', [case])
    write_json(output/'report.json', dict(cases=[dict(case, accepted=False, returncode=0)]))
    folder = output/'sample'
    reports = folder/'conversion/reports'
    write_json(folder/'reference_access.json', dict(blocked_svg_reads=[]))
    write_json(reports/'conversion_result_map.json', {})
    write_json(reports/'sample_reference_access.json', dict(blocked_svg_reads=[]))
    write_json(reports/'sample_deadline.json', dict(isolated=True, limit_seconds=5., max_seconds=5.,
               elapsed_seconds=2., stop_reason='no_result'))
    return inputs, output, reports


@pytest.mark.parametrize('reason,elapsed', [('no_result', 2.), ('time_limit', 5.02)])
def test_explained_absence_stays_negative_and_require_all_still_fails(negative_scene, reason, elapsed):
    inputs, output, reports = negative_scene
    path = reports/'sample_deadline.json'
    control = json.loads(path.read_text())
    control.update(stop_reason=reason, elapsed_seconds=elapsed, retained_output=False)
    write_json(path, control)
    summary = verify_report(inputs, output)
    assert summary['completed'] == 1 and summary['accepted'] == 0
    assert summary['cases'][0]['absence_reason'] == reason+'_no_output'
    with pytest.raises(ValueError, match='failed independent acceptance'):
        verify_report(inputs, output, require_all=True)
    assert json.loads((output/'verification.json').read_text())['accepted'] == 0


@pytest.mark.parametrize('damage', [
    'missing_worker_audit', 'missing_deadline', 'blocked_worker_read', 'missing_guard',
    'blocked_parent_read', 'early_timeout', 'late_no_result', 'unknown_stop', 'budget',
    'retained_output', 'unexpected_svg', 'ambiguous_svgs', 'ambiguous_rows',
    'nan_elapsed', 'negative_elapsed', 'missing_elapsed', 'unisolated', 'claimed_pass',
])
def test_missing_or_tampered_evidence_cannot_explain_absence(negative_scene, damage):
    inputs, output, reports = negative_scene
    path = reports/'sample_deadline.json'
    control = json.loads(path.read_text())
    changes = {
        'early_timeout': dict(stop_reason='time_limit', elapsed_seconds=2., retained_output=False),
        'late_no_result': dict(elapsed_seconds=5.1),
        'unknown_stop': dict(stop_reason='worker_error'),
        'budget': dict(max_seconds=10.), 'retained_output': dict(retained_output=True),
        'nan_elapsed': dict(elapsed_seconds=float('nan')), 'negative_elapsed': dict(elapsed_seconds=-1),
        'unisolated': dict(isolated=False),
    }
    control.update(changes.get(damage, {}))
    if damage == 'missing_elapsed':
        control.pop('elapsed_seconds')
    write_json(path, control)
    if damage == 'missing_deadline':
        path.unlink()
    if damage == 'missing_worker_audit':
        (reports/'sample_reference_access.json').unlink()
    if damage in {'blocked_worker_read', 'missing_guard'}:
        write_json(reports/'sample_reference_access.json',
                   dict(blocked_svg_reads=['forbidden.svg']) if damage == 'blocked_worker_read' else {})
    if damage == 'blocked_parent_read':
        write_json(output/'sample/reference_access.json', dict(blocked_svg_reads=['forbidden.svg']))
    if damage in {'unexpected_svg', 'ambiguous_svgs'}:
        folder = output/'sample/conversion/converted_svgs'
        folder.mkdir()
        (folder/'sample.svg').write_text('<svg/>')
        if damage == 'ambiguous_svgs':
            (folder/'other.svg').write_text('<svg/>')
    if damage == 'ambiguous_rows':
        write_json(reports/'conversion_result_map.json', {'a': {}, 'b': {}})
    if damage == 'claimed_pass':
        report = json.loads((output/'report.json').read_text())
        report['cases'][0]['accepted'] = True
        write_json(output/'report.json', report)
    with pytest.raises((ValueError, FileNotFoundError)):
        verify_report(inputs, output)


@pytest.mark.parametrize('broken_report', [False, True])
def test_failure_bundle_is_bounded_and_excludes_generated_assets(tmp_path, broken_report):
    work, destination = tmp_path/'work', tmp_path/'evidence'
    reports = work/'cli/sample/conversion/reports'
    write_json(reports/'sample_deadline.json', dict(stop_reason='no_result'))
    log = work/'cli/sample/converter.log'
    log.write_bytes(b'x'*300_000+b'final cause')
    (work/'cli/sample/input').mkdir()
    (work/'cli/sample/input/source.png').write_bytes(b'raw raster')
    (work/'cli/sample/output.svg').write_text('<svg/>')
    (work/'cli/report.json').write_text('{"cases": [' if broken_report else
        json.dumps(dict(cases=[dict(svg='<svg>reference</svg>', accepted=False)])))
    recipe = dict(seed=915463, search_seed=17, budget_seconds=5)
    preserve_failure(work, destination, recipe, ValueError('quality failed'))
    summary = json.loads((destination/'failure.json').read_text())
    assert summary['recipe'] == recipe and summary['error'] == 'quality failed'
    item = next(f for f in summary['files'] if f['path'].endswith('converter.log'))
    assert item['truncated'] and item['saved_bytes'] == 256_000
    assert (destination/item['path']).read_bytes().endswith(b'final cause')
    assert not list(destination.rglob('*.svg')) and not list(destination.rglob('*.png'))
    if not broken_report:
        assert 'svg' not in json.loads((destination/'cli/report.json').read_text())['cases'][0]
    for item in summary['files']:
        assert hashlib.sha256((destination/item['path']).read_bytes()).hexdigest() == item['saved_sha256']


def test_scene_selection_preserves_generator_recipe(tmp_path, monkeypatch):
    from tools import run_seeded_scene_check as checks
    from tools import evaluate_layered_scene
    (tmp_path/'tools').mkdir()
    (tmp_path/'tools/evaluate_example.py').touch()
    monkeypatch.setattr(checks, 'ROOT', tmp_path)
    def prepare(command, **kwargs):
        inputs = Path(command[command.index('--prepare')+1])
        write_json(inputs/'manifest.json', [dict(case_id='case_00'), dict(case_id='case_07')])
    def evaluate(inputs, output, **kwargs):
        assert json.loads((inputs/'manifest.json').read_text()) == [dict(case_id='case_07')]
        assert kwargs['require_all'] is True
        return dict(accepted=1, completed=1)
    monkeypatch.setattr(checks.subprocess, 'run', prepare)
    monkeypatch.setattr(evaluate_layered_scene, 'evaluate_cases', evaluate)
    checks.run('evaluate_example', 915463, case_ids=['case_07'])
    recipe = json.loads((tmp_path/'config/test_run_seeds.jsonl').read_text())
    assert recipe['case_ids'] == ['case_07'] and recipe['seed'] == 915463
