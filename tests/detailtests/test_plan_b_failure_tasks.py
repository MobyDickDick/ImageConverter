import json
from pathlib import Path

import pytest

from tools import report_plan_b_failures as reporter


def write(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report), encoding='utf-8')


def battery(source='symbol.svg', failed=True, original=False):
    return dict(schema_version='plan_b_variations_v2', seed=42, status='completed',
        source_svg_sha256='abc', source_description_sha256='def', source_description='Quadrat mit Griff.',
        original_satisfactory=not original, selection={'source_svg': '/runner/artifacts/images_to_convert/samples/'+source},
        summary={'satisfactory': not failed}, limits={'min_foreground_iou': .85},
        cases=[dict(case_id='original' if original else 'probe_03', satisfactory=not failed,
                    failures=['foreground_iou_outside_limit'] if failed else [], metrics={'foreground_iou': .8})])


def test_pool_keeps_failed_originals_when_final_battery_passes_and_has_replay_data(tmp_path):
    write(tmp_path/'attempt_01/report.json', battery(original=True))
    write(tmp_path/'attempt_02/report.json', battery('good.svg', failed=False))
    write(tmp_path/'report.json', dict(schema_version='plan_b_search_v1', status='completed',
        summary={'satisfactory': True}, attempts=[{'report': f'attempt_0{i}/report.json'} for i in (1,2)]))
    tasks = reporter.collect_tasks(tmp_path, conclusion='success', run_url='https://github.com/o/r/actions/runs/1')
    assert len(tasks) == 1 and tasks[0]['phase'] == 'original'
    assert tasks[0]['seed'] == 42 and tasks[0]['failures'][0]['metrics']['foreground_iou'] == .8
    assert tasks[0]['limits']['min_foreground_iou'] == .85
    text = reporter.write_evidence(tmp_path, tasks)
    assert 'Beschreibung' in text and 'Original und alle 16 Varianten' in text
    assert json.loads((tmp_path/'failure_tasks.json').read_text(encoding='utf-8'))['tasks'] == tasks


def test_task_identity_ignores_seed_but_distinguishes_description_source_and_phase(tmp_path):
    base = battery()
    write(tmp_path/'report.json', base)
    first = reporter.collect_tasks(tmp_path)[0]['key']
    base['seed'] = 99
    write(tmp_path/'report.json', base)
    assert reporter.collect_tasks(tmp_path)[0]['key'] == first
    base['source_description_sha256'] = 'different'
    write(tmp_path/'report.json', base)
    assert reporter.collect_tasks(tmp_path)[0]['key'] != first


def test_non_catalog_reference_keeps_repository_relative_path():
    assert reporter.source_path('/runner/project/artifacts/evaluation/recheck/independent.svg') == 'artifacts/evaluation/recheck/independent.svg'


@pytest.mark.parametrize('status', ['interrupted', 'preparation_error', 'running_variations'])
def test_incomplete_run_generates_execution_task(tmp_path, status):
    write(tmp_path/'report.json', dict(status=status, cases=[], error='renderer unavailable'))
    assert reporter.collect_tasks(tmp_path)[0]['phase'] == 'execution'


def test_missing_and_malformed_reports_generate_actionable_fallback(tmp_path):
    assert reporter.collect_tasks(tmp_path)[0]['status'] == 'report_unavailable'
    (tmp_path/'report.json').write_text('broken')
    assert reporter.main(['--artifact-dir', str(tmp_path)]) == 0
    assert 'error' in (tmp_path/'failure_summary.md').read_text()


def test_attempt_paths_cannot_read_outside_downloaded_artifact(tmp_path):
    write(tmp_path/'report.json', dict(schema_version='plan_b_search_v1', attempts=[{'report':'../secret.json'}]))
    tasks = reporter.collect_tasks(tmp_path)
    assert 'escapes' in tasks[0]['error']


class Client:
    def __init__(self, issues=()):
        self.saved = list(issues)
        self.calls = []

    def issues(self):
        return iter(self.saved)

    def request(self, method, path, data):
        self.calls.append((method, path, data))
        result = dict(number=1, html_url='https://github.com/o/r/issues/1', **data)
        self.saved[:] = [result]
        return result


def test_publishing_deduplicates_replays_reopens_recurrence_and_preserves_user_notes(tmp_path):
    write(tmp_path/'report.json', battery())
    tasks = reporter.collect_tasks(tmp_path)
    client = Client()
    assert reporter.sync_issues(tasks, client, '1')[0]['action'] == 'created'
    assert reporter.sync_issues(tasks, client, '1')[0]['action'] == 'already_recorded'
    assert len(client.calls) == 1
    client.saved[0]['body'] += '\nUser investigation notes.'
    client.saved[0]['state'] = 'closed'
    assert reporter.sync_issues(tasks, client, '2')[0]['action'] == 'updated'
    assert client.calls[-1][0] == 'PATCH'
    assert client.calls[-1][2]['state'] == 'open'
    assert 'User investigation notes.' in client.saved[0]['body']


def test_permission_denial_keeps_drafts_and_records_failure(tmp_path, monkeypatch):
    write(tmp_path/'report.json', battery())
    monkeypatch.setenv('GITHUB_REPOSITORY', 'o/r')
    monkeypatch.setenv('GH_TOKEN', 'test-token')
    monkeypatch.setenv('GITHUB_STEP_SUMMARY', str(tmp_path/'summary.md'))
    def denied(*args):
        raise PermissionError('issues write denied')
    monkeypatch.setattr(reporter.GitHub, 'issues', denied)
    assert reporter.main(['--artifact-dir', str(tmp_path), '--publish']) == 1
    assert (tmp_path/'failure_tasks.json').exists()
    assert 'issues write denied' in (tmp_path/'issue_sync.json').read_text()
    assert 'fehlgeschlagen' in (tmp_path/'summary.md').read_text(encoding='utf-8')


def test_markdown_cannot_be_broken_by_description_fences(tmp_path):
    write(tmp_path/'report.json', dict(battery(), source_description='```\n# injected'))
    assert '````json' in reporter.task_markdown(reporter.collect_tasks(tmp_path)[0])


def test_successful_run_creates_no_tasks(tmp_path):
    write(tmp_path/'report.json', battery(failed=False))
    assert reporter.collect_tasks(tmp_path, conclusion='success') == []


def test_workflow_failure_after_quality_pass_is_still_an_execution_task(tmp_path):
    write(tmp_path/'report.json', battery(failed=False))
    assert reporter.collect_tasks(tmp_path, conclusion='failure')[0]['phase'] == 'execution'
    assert reporter.collect_tasks(tmp_path) == []


def test_missing_report_publishing_includes_the_actual_failed_job_step(tmp_path, monkeypatch):
    class InfrastructureClient(Client):
        def request(self, method, path, data=None):
            if method == 'GET':
                assert path == '/actions/runs/17/jobs?per_page=100'
                return {'jobs':[dict(name='sixteen-variations',html_url='https://github.com/o/r/actions/runs/17',
                    conclusion='failure',steps=[dict(name='Install test dependencies',conclusion='failure')])]}
            return super().request(method,path,data)
    client = InfrastructureClient()
    monkeypatch.setattr(reporter,'GitHub',lambda *args:client)
    monkeypatch.setenv('GITHUB_REPOSITORY','o/r')
    monkeypatch.setenv('GH_TOKEN','test-token')
    assert reporter.main(['--artifact-dir',str(tmp_path),'--publish','--run-id','17-1']) == 0
    assert 'Install test dependencies' in client.saved[0]['body']
    saved=json.loads((tmp_path/'failure_tasks.json').read_text(encoding='utf-8'))
    assert saved['tasks'][0]['failed_jobs'][0]['steps'] == ['Install test dependencies']
