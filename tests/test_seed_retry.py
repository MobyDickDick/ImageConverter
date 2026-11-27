"""CI contracts for sequential retries, cancellation, persistence and best retention."""
import io
import threading

from PIL import Image
import pytest

from src import imageConverterGui as gui


@pytest.fixture
def jobs(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    manager = gui.Jobs(tmp_path/'jobs')
    manager.project_directory = tmp_path/'project'
    monkeypatch.setattr(manager, 'run', lambda job_id: None)
    yield manager
    manager.close()


def upload(jobs):
    content = io.BytesIO()
    Image.new('RGB', (32, 24), 'white').save(content, format='PNG')
    return jobs.upload('neutral.png', content.getvalue())['id']


def finish(jobs, job_id, *, result=False):
    job = jobs.jobs[job_id]
    job.update(status='done' if result else 'error', result=result, quality='warning')
    jobs.seed_retry.finished(job_id)
    return jobs.seed_retry.session(job_id)


def test_retry_after_no_rendering_uses_a_new_seed_and_a_fresh_search(jobs):
    first = jobs.seed_retry.toggle(upload(jobs), 'Ein Kreis.', 'quick', seed='9007199254740993')
    session = finish(jobs, first['id'])
    second = jobs.jobs[session['current_job_id']]
    assert second['status']=='running' and session['attempts']==2
    assert second['search_seed'] != int(first['search_seed'])
    assert second['description']==first['description'] and second['profile']=='quick'
    assert second['use_current_svg'] is False
    assert jobs.snapshot(first['id'])['seed_retry']['current_job_id']==second['id']
    jobs.seed_retry.toggle(first['id'], '', 'quick')
    assert not session['active'] and second['status']=='cancelled'
    finish(jobs, second['id'])
    assert session['attempts']==2


def test_enable_during_a_run_and_stop_through_an_old_job_id(jobs):
    first = jobs.start(upload(jobs), 'Ein Kreis.', 'quick', seed=17)
    enabled = jobs.seed_retry.toggle(first['id'], 'Ignored editor text', 'normal')
    assert len(jobs.jobs)==1 and enabled['profile']=='quick'
    session = finish(jobs, first['id'])
    current = session['current_job_id']
    jobs.cancel(first['id'])
    assert not session['active'] and jobs.jobs[current]['status']=='cancelled'


def test_best_is_frozen_and_worse_or_missing_results_cannot_replace_it(jobs, monkeypatch):
    monkeypatch.setattr(gui, 'saved_svg_quality', lambda *args: dict(
        passed=False, observed_foreground_pixels=10, output_foreground_pixels=10,
        normalized_mse=.1 if 'better' in args[1].read_text() else .5))
    monkeypatch.setattr(gui, 'result_description_error', lambda *args: '')
    monkeypatch.setattr(gui, 'vector_comparison_score', lambda q:q['normalized_mse'])
    first = jobs.seed_retry.toggle(upload(jobs), 'Ein Kreis.', 'quick', seed=17)
    def result(job_id, label):
        (jobs.folder(job_id)/'result.svg').write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24">'
            f'<!--{label}--><circle cx="12" cy="12" r="8"/></svg>')
    result(first['id'], 'better')
    session = finish(jobs, first['id'], result=True)
    second = session['current_job_id']
    result(second, 'worse')
    finish(jobs, second, result=True)
    third = session['current_job_id']
    frozen = jobs.folder(first['id'])/'seed-best.svg'
    assert 'better' in frozen.read_text() and session['best_job_id']==first['id']
    assert jobs.export_file(third)==frozen
    assert jobs.export_file(second, include_retry=False)==jobs.folder(second)/'result.svg'
    stopped = jobs.seed_retry.toggle(third, '', 'quick')
    assert stopped['id']==first['id'] and not stopped['seed_retry']['active']
    assert jobs.jobs[third]['status']=='cancelled' and 'better' in frozen.read_text()
    # Reload must retain the exact winner and never resume a stopped loop.
    restored = gui.Jobs(jobs.directory)
    try:
        assert restored.snapshot(third)['seed_retry']['best_seed']=='17'
        assert restored.export_file(third).read_bytes()==frozen.read_bytes()
        assert not restored.busy()
    finally:
        restored.close()


def test_restart_interrupts_the_loop_without_losing_history(jobs):
    first = jobs.seed_retry.toggle(upload(jobs), 'Ein Kreis.', 'quick', seed=17)
    session = finish(jobs, first['id'])
    restored = gui.Jobs(jobs.directory)
    try:
        snapshot = restored.snapshot(session['current_job_id'])
        assert snapshot['status']=='interrupted'
        assert not snapshot['seed_retry']['active'] and snapshot['seed_retry']['attempts']==2
        assert not restored.threads
    finally:
        restored.close()


def test_invalid_input_never_starts_a_retry_loop(jobs):
    job_id = upload(jobs)
    with pytest.raises(gui.RequestError):
        jobs.seed_retry.toggle(job_id, '', 'quick', seed=17)
    assert not jobs.seed_retry.busy() and not jobs.threads


def test_only_one_foreground_loop_is_admitted_and_background_lane_is_independent(jobs):
    first = jobs.seed_retry.toggle(upload(jobs), 'Ein Kreis.', 'quick', seed=17)
    with pytest.raises(gui.RequestError):
        jobs.start(upload(jobs), 'Ein Kreis.', 'quick')
    background = jobs.start(upload(jobs), 'Ein Kreis.', 'quick', background=True)
    assert background['catalog_background']
    with pytest.raises(gui.RequestError):
        jobs.seed_retry.toggle(background['id'], '', 'quick')
    jobs.cancel(first['id'])
    assert jobs.jobs[background['id']]['status']=='running'


def test_stop_during_cleanup_prevents_the_next_attempt(jobs):
    first = jobs.seed_retry.toggle(upload(jobs), 'Ein Kreis.', 'quick', seed=17)
    ready, release = threading.Event(), threading.Event()
    def cleanup():
        ready.set()
        assert release.wait(5)
        finish(jobs, first['id'])
    thread = threading.Thread(target=cleanup)
    thread.start()
    assert ready.wait(5)
    jobs.seed_retry.toggle(first['id'], '', 'quick')
    release.set()
    thread.join(5)
    session = jobs.seed_retry.session(first['id'])
    assert not thread.is_alive() and not session['active'] and session['attempts']==1
