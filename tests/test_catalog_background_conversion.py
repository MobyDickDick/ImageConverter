"""Best failing image selection, sequential retries, cancellation and admission."""
import copy
import hashlib
from pathlib import Path
import threading
import time
from types import SimpleNamespace

from PIL import Image
import pytest

from src import imageConverterGui as gui
from src.imageConverterCatalog import CatalogError, atomic_json
from src.imageConverterCatalogConversion import CatalogConversion, failure_order, checked_attempt
from test_catalog_inventory import SVG, prepare, quality
from test_catalog_quality_server import catalog, wait_for
from tools.build_catalog_inventory import build, write_report


def row(name, mse=.01, status='pixel_fail', role='catalog'):
    return dict(filename=name, status=status, role=role, description='Graues Rechteck.',
                selected=dict(measurement=quality(False, mse)))


def wait_until(predicate, timeout=5):
    end = time.monotonic()+timeout
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(.02)
    assert predicate()


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda:{})
    jobs = gui.Jobs(tmp_path/'gui')
    root = tmp_path/'repo'
    folder = root/'artifacts/images_to_convert'
    folder.mkdir(parents=True)
    rows = [row('AA0010.jpg', .03), row('AA0011.jpg', .01), row('AA0012.jpg', .02),
            row('AA0013.jpg', .00001, 'pixel_pass'), row('AA0014.jpg', .00001, 'reserved')]
    for item in rows:
        path = folder/item['filename']
        Image.new('RGB', (40,40), 'white').save(path)
        item.update(image=path.relative_to(root).as_posix(), image_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    catalog = SimpleNamespace(root=root, directory=tmp_path/'catalog', lock=threading.RLock(),
                              thread=None, conversion_owner=None, payload=lambda:dict(rows=rows),
                              snapshot=lambda:dict(status='done', progress={}))
    manager = CatalogConversion(catalog, jobs, SimpleNamespace(busy=lambda:False))
    refreshes = []
    def refresh():
        refreshes.append(1)
        # A fresh catalog would compare these preserved candidates in both renderers.
        for stem, required in [('AA0011',1),('AA0012',4),('AA0010',4)]:
            candidates = list((root/'artifacts/converted_images/catalog_background_svgs').rglob(stem+'.svg'))
            if len(candidates) >= required:
                next(r for r in rows if Path(r['filename']).stem == stem)['status'] = 'pixel_pass'
            if candidates:
                item = next(r for r in rows if Path(r['filename']).stem == stem)
                item['candidates'] = [dict(svg_sha256=hashlib.sha256(SVG.encode()).hexdigest(),
                                          measurement=quality(item['status'] == 'pixel_pass'))]
        return not manager.stop.is_set()
    monkeypatch.setattr(manager, '_refresh', refresh)
    def run(job_id):
        with jobs.lock:
            job = jobs.jobs[job_id]
            (jobs.folder(job_id)/'result.svg').write_text(SVG, encoding='utf-8')
            (jobs.folder(job_id)/'console.log').write_text('new candidate measured', encoding='utf-8')
            job.update(status='done', result=True, quality='warning', message='Entwurf geprüft.')
            jobs.save(job)
    monkeypatch.setattr(jobs, 'run', run)
    yield manager, rows, refreshes
    manager.close()
    jobs.close()


def test_defers_after_three_failures_then_resets_all_marks_and_repeats(service, monkeypatch):
    manager, rows, refreshes = service
    selections = []
    launch = manager._launch
    def record(item):
        selections.append(manager.snapshot())
        return launch(item)
    monkeypatch.setattr(manager, '_launch', record)
    manager.start()
    manager.thread.join(5)
    result = manager.snapshot()
    assert result['status'] == 'done', result
    assert [r['filename'] for r in result['history']] == ['AA0011.jpg',*['AA0012.jpg']*3,
                                                        *['AA0010.jpg']*3,'AA0012.jpg','AA0010.jpg']
    assert (result['completed'],result['passed'],result['failed']) == (9,3,6)
    assert len(refreshes) == 10
    assert result['round'] == 2
    assert result['failure_counts'] == {} and result['deferred'] == []
    assert [r['round'] for r in result['history']] == [1]*7+[2]*2
    assert [r['attempt'] for r in result['history']] == [1,1,2,3,1,2,3,1,1]
    assert [r['filename'] for r in result['history'] if r['deferred']] == ['AA0012.jpg','AA0010.jpg']
    assert selections[4]['deferred'] == ['AA0012.jpg']
    assert selections[7]['deferred'] == []
    assert 'new candidate' in result['job']['log']
    assert len(list((manager.catalog.root/'artifacts/converted_images/catalog_background_svgs').rglob('*.svg'))) == 9
    assert manager.catalog.conversion_owner is None
    # Once every measurable failure passes, restart must not convert it again.
    manager.start('quick'); manager.thread.join(5)
    assert manager.snapshot()['history'] == []


@pytest.mark.parametrize('status', ['pixel_pass','reserved','source_conflict','no_svg','measurement_error','auxiliary'])
def test_unrankable_status_is_excluded(status):
    assert failure_order(row('AA0010.jpg', status=status)) is None


def test_ranking_uses_worse_renderer_and_rejects_missing_or_nonfinite_metrics():
    item = row('AA0010.jpg', .001)
    item['selected']['measurement']['renderers']['librsvg']['metrics']['normalized_mse'] = .2
    assert failure_order(item)[0] == .2
    for value in (None, float('nan'), float('inf'), True):
        bad = copy.deepcopy(item)
        bad['selected']['measurement']['renderers']['mupdf']['metrics']['normalized_mse'] = value
        assert failure_order(bad) is None
    item['description'] = ''
    assert failure_order(item) is None
    assert failure_order(row('AA0010.jpg', role='auxiliary')) is None


def test_next_preview_obeys_deferrals_and_round_reset(service):
    manager, _, _ = service
    preview = manager.snapshot()['next']
    assert (preview['filename'],preview['attempt'],preview['round']) == ('AA0011.jpg',1,1)
    assert preview['image'].endswith('AA0011.jpg')
    manager._update(failure_counts={'aa0011.jpg':3})
    assert manager.snapshot()['next']['filename'] == 'AA0012.jpg'
    manager._update(failure_counts={f'aa001{i}.jpg':3 for i in range(3)})
    assert manager.snapshot()['next']['filename'] == 'AA0011.jpg'
    assert manager.snapshot()['next']['round'] == 2
    assert manager.state.get('round',1) == 1  # Preview must not advance the real round.


def test_next_preview_explains_conditional_retry_while_current_attempt_runs(service):
    manager, _, _ = service
    manager._update(status='running',phase='convert',filename='AA0011.jpg',attempt=2)
    preview = manager.snapshot()['next']
    assert preview['filename'] == 'AA0011.jpg' and preview['attempt'] == 3
    assert preview['conditional']
    manager._update(attempt=3)
    assert manager.snapshot()['next']['filename'] == 'AA0012.jpg'


def test_existing_worklist_starts_without_any_catalog_measurement(service, monkeypatch):
    manager, rows, _ = service
    monkeypatch.setattr(manager.catalog, 'payload', lambda:dict(rows=rows, summary={'schema':'catalog_inventory_v1'}))
    monkeypatch.setattr(manager.catalog, 'start', lambda **kwargs:pytest.fail('Unexpected inventory measurement'), raising=False)
    assert CatalogConversion._refresh(manager)
    assert manager.catalog.thread is None


def test_quality_index_is_reused_until_a_new_list_is_published(service, monkeypatch):
    from src import imageConverterCatalogConversion as module
    manager, rows, _ = service
    payload = dict(rows=rows, summary={'schema':'catalog_inventory_v1'})
    monkeypatch.setattr(manager.catalog, 'payload', lambda:payload)
    calls = []
    order = module.failure_order
    def record(row):
        calls.append(row['filename'])
        return order(row)
    monkeypatch.setattr(module, 'failure_order', record)
    assert manager.snapshot()['next']['filename'] == 'AA0011.jpg'
    manager.snapshot()
    assert len(calls) == len(rows)
    payload['rows'] = copy.deepcopy(rows)
    payload['rows'][1]['status'] = 'pixel_pass'
    assert manager.snapshot()['next']['filename'] == 'AA0012.jpg'
    assert len(calls) == 2*len(rows)


def test_resuming_validation_records_failure_once_before_selecting_next_image(service, monkeypatch):
    manager, _, _ = service
    refresh = manager._refresh
    def interrupt():
        if manager.state.get('last_attempt') and not manager.state['completed']:
            manager.stop.set()
            return False
        return refresh()
    monkeypatch.setattr(manager, '_refresh', interrupt)
    manager.start(); manager.thread.join(5)
    assert manager.snapshot()['last_attempt']['accounted'] is False
    restored = CatalogConversion(manager.catalog, manager.jobs, manager.workbench)
    attempts = []
    def select(row):
        attempts.append((row['filename'], restored.state['attempt']))
        restored.stop.set()
        return None
    # Keep the interrupted attempt failing when its validation resumes.
    original = manager.catalog.payload()['rows'][1]
    original['candidates'] = [dict(svg_sha256=manager.state['last_attempt']['svg_sha256'], measurement=quality(False))]
    monkeypatch.setattr(restored, '_refresh', lambda:True)
    monkeypatch.setattr(restored, '_launch', select)
    try:
        restored.start(); restored.thread.join(5)
        snapshot = restored.snapshot()
        assert attempts == [('AA0011.jpg', 2)]
        assert snapshot['completed'] == snapshot['failed'] == 1
        assert snapshot['failure_counts'] == {'aa0011.jpg':1}
        assert snapshot['last_attempt']['accounted'] is True
        restored.start(); restored.thread.join(5)
        assert restored.snapshot()['completed'] == 0
        assert restored.snapshot()['failure_counts'] == {'aa0011.jpg':1}
    finally:
        restored.close()


def test_attempt_without_svg_never_triggers_catalog_measurement(service, monkeypatch):
    manager, rows, refreshes = service
    def run(job_id):
        with manager.jobs.lock:
            manager.jobs.jobs[job_id].update(status='error', result=False, message='No SVG')
    monkeypatch.setattr(manager.jobs, 'run', run)
    launch = manager._launch
    def stop_after_three(item):
        if manager.state['completed'] == 3:
            manager.stop.set()
            return None
        return launch(item)
    monkeypatch.setattr(manager, '_launch', stop_after_three)
    manager.start(); manager.thread.join(5)
    assert manager.snapshot()['status'] == 'stopped'
    assert manager.snapshot()['completed'] == manager.snapshot()['failed'] == 3
    assert len(refreshes) == 1  # Initial worklist load only.
    assert manager.snapshot()['failure_counts']['aa0011.jpg'] == 3


def test_inspection_progress_and_log_are_visible_in_service_snapshot(service, monkeypatch):
    manager, _, _ = service
    folder = manager.catalog.directory/('a'*32)
    folder.mkdir(parents=True)
    (folder/'console.log').write_text('Inventar 762/1787; neue Paarprüfungen 1284',encoding='utf-8')
    monkeypatch.setattr(manager.catalog,'snapshot',lambda:dict(id='a'*32,status='running',
        started=time.time()-30,progress=dict(completed=762,total=1787,measured=1284,cached=4)))
    manager._update(status='running',phase='refresh')
    snapshot = manager.snapshot()
    assert snapshot['inspection']['progress']['completed'] == 762
    assert snapshot['inspection']['elapsed'] >= 30
    assert '762/1787' in snapshot['log']
    assert snapshot['next']['provisional']


@pytest.mark.parametrize('passed',[False,True])
def test_result_judges_the_new_svg_instead_of_an_older_passing_candidate(passed):
    attempt = dict(filename='AA0010.jpg',result=True,svg_sha256='new',checking=True)
    current = dict(status='pixel_pass',candidates=[dict(svg_sha256='old',measurement=quality(True)),
        dict(svg_sha256='new',measurement=quality(passed))])
    checked = checked_attempt(attempt,current)
    assert checked['passed'] is passed
    assert checked['catalog_passed'] is True
    assert checked['checking'] is False
    assert checked_attempt(dict(attempt,result=False),current)['passed'] is False
    assert checked_attempt(dict(attempt,svg_sha256='not-measured'),current)['passed'] is None


def test_last_result_is_visible_before_validation_and_survives_restart(service, monkeypatch):
    manager, _, _ = service
    captured = []
    refresh = manager._refresh
    def inspect():
        if manager.state.get('last_attempt'):
            captured.append(manager.snapshot()['last_attempt'])
        return refresh()
    monkeypatch.setattr(manager,'_refresh',inspect)
    manager.start();manager.thread.join(5)
    assert captured[0]['result'] is True
    assert captured[0]['passed'] is None and captured[0]['checking']
    last = manager.snapshot()['last_attempt']
    assert last['passed'] is True and last['result']
    assert last['filename'] == 'AA0010.jpg'
    restored = CatalogConversion(manager.catalog,manager.jobs,manager.workbench)
    assert restored.snapshot()['last_attempt'] == last
    manager.start();manager.thread.join(5)
    assert manager.snapshot()['last_attempt'] == last


def test_interrupted_validation_keeps_svg_without_claiming_success_or_failure(service, monkeypatch):
    manager, _, _ = service
    refresh = manager._refresh
    def interrupt():
        if manager.state.get('last_attempt'):
            manager.stop.set()
            return False
        return refresh()
    monkeypatch.setattr(manager,'_refresh',interrupt)
    manager.start();manager.thread.join(5)
    last = manager.snapshot()['last_attempt']
    assert last['result'] and last['passed'] is None and not last['checking']
    assert 'unterbrochen' in last['message']


def test_stop_while_waiting_leaves_foreground_job_alone_and_allows_restart(service):
    manager, rows, _ = service
    foreground = manager.jobs.upload('manual.png', (manager.catalog.root/rows[0]['image']).read_bytes())
    manager.jobs.jobs[foreground['id']]['status'] = 'running'
    manager.start()
    wait_until(lambda: manager.snapshot().get('phase') == 'waiting')
    with pytest.raises(CatalogError, match='bereits'):
        manager.start()
    manager.cancel(); manager.thread.join(5)
    assert manager.snapshot()['status'] == 'stopped'
    assert manager.jobs.jobs[foreground['id']]['status'] == 'running'
    assert manager.snapshot()['completed'] == 0
    manager.jobs.jobs[foreground['id']]['status'] = 'ready'
    manager.start(); manager.thread.join(5)
    assert manager.snapshot()['completed'] == 9, manager.snapshot().get('message')


def test_stop_cancels_active_conversion_and_starts_no_next_image(service, monkeypatch):
    manager, _, _ = service
    entered = threading.Event()
    def run(job_id):
        entered.set()
        while manager.jobs.jobs[job_id]['status'] == 'running':
            time.sleep(.01)
    monkeypatch.setattr(manager.jobs, 'run', run)
    manager.start()
    assert entered.wait(3)
    wait_until(lambda: manager.snapshot().get('job_id'))
    manager.cancel(); manager.thread.join(5)
    snapshot = manager.snapshot()
    assert snapshot['status'] == 'stopped', snapshot
    assert snapshot['job']['status'] == 'cancelled'
    assert len(manager.jobs.jobs) == 1
    assert manager.snapshot()['failure_counts'] == {}
    assert manager.catalog.conversion_owner is None


def test_failure_stops_service_and_releases_catalog(service, monkeypatch):
    manager, _, _ = service
    monkeypatch.setattr(manager, '_refresh', lambda: (_ for _ in ()).throw(RuntimeError('test refresh failed')))
    manager.start(); manager.thread.join(5)
    assert manager.snapshot()['status'] == 'error'
    assert 'test refresh failed' in manager.snapshot()['message']
    assert manager.catalog.conversion_owner is None


def test_changed_source_is_never_converted(service):
    manager, rows, _ = service
    (manager.catalog.root/rows[1]['image']).write_bytes(b'changed')
    manager.start(); manager.thread.join(5)
    assert manager.snapshot()['status'] == 'error'
    assert not manager.jobs.jobs


@pytest.mark.parametrize('profile', [None, [], {}, 'invalid'])
def test_invalid_profile_has_no_side_effects(service, profile):
    manager, _, _ = service
    with pytest.raises(CatalogError):
        manager.start(profile)
    assert manager.catalog.conversion_owner is None


def test_restarting_server_marks_service_interrupted(service):
    manager, _, _ = service
    atomic_json(manager.directory/'state.json', dict(status='running'))
    restored = CatalogConversion(manager.catalog, manager.jobs, manager.workbench)
    assert restored.snapshot()['status'] == 'interrupted'
    assert restored.thread is None


def test_deferred_marks_and_round_survive_stop_and_server_restart(service, monkeypatch):
    manager, _, _ = service
    launch = manager._launch
    def stop_after_deferral(item):
        if item['filename'] == 'AA0010.jpg':
            manager.stop.set()
            return None
        return launch(item)
    monkeypatch.setattr(manager, '_launch', stop_after_deferral)
    manager.start(); manager.thread.join(5)
    snapshot = manager.snapshot()
    assert snapshot['status'] == 'stopped', snapshot
    assert snapshot['failure_counts'] == {'aa0012.jpg':3}
    assert snapshot['deferred'] == ['AA0012.jpg']
    assert snapshot['round'] == 1
    restored = CatalogConversion(manager.catalog, manager.jobs, manager.workbench)
    def refresh_restored():
        manager._refresh()
        return not restored.stop.is_set()
    monkeypatch.setattr(restored, '_refresh', refresh_restored)
    try:
        restored.start(); restored.thread.join(5)
        snapshot = restored.snapshot()
        assert snapshot['status'] == 'done', snapshot
        assert [item['filename'] for item in snapshot['history']] == [*['AA0010.jpg']*3,'AA0012.jpg','AA0010.jpg']
        assert snapshot['history'][0]['round'] == 1
        assert snapshot['history'][3]['round'] == 2
        assert snapshot['failure_counts'] == {}
    finally:
        restored.close()


def test_recomputes_best_failing_image_after_each_attempt(service, monkeypatch):
    manager, rows, _ = service
    refresh = manager._refresh
    def rerank():
        result = refresh()
        if manager.state['completed'] >= 1:
            rows[2]['selected']['measurement'] = quality(False, .05)
        return result
    monkeypatch.setattr(manager, '_refresh', rerank)
    manager.start(); manager.thread.join(5)
    snapshot = manager.snapshot()
    assert snapshot['status'] == 'done', snapshot.get('message')
    assert [item['filename'] for item in snapshot['history'][:5]] == ['AA0011.jpg','AA0012.jpg',*['AA0010.jpg']*3]


def test_background_candidates_require_both_renderers_before_catalog_admission(tmp_path):
    prepare(tmp_path)
    folder = tmp_path/'artifacts/converted_images/catalog_background_svgs'/('a'*32)
    folder.mkdir(parents=True)
    (folder/'AA0010.svg').write_text(SVG+'\n', encoding='utf-8')
    def measure(image, svg):
        result = quality(False, .05)
        if svg.parent == folder:
            result = quality(True, .001)
            result['renderers']['librsvg']['satisfactory'] = False
        return result
    rows, _, _ = build(tmp_path, measure=measure)
    assert rows[0]['status'] == 'pixel_fail'
    assert len(rows[0]['candidates']) == 2
    rows, _, _ = build(tmp_path, measure=lambda *args:quality(True))
    assert rows[0]['status'] == 'pixel_pass'


def test_real_reports_publish_fresh_background_candidate_and_new_pass(catalog, tmp_path, monkeypatch):
    # Only candidate generation is substituted; both independent renderer
    # measurements and the report CLI run unchanged in subprocesses.
    old = catalog.root/'artifacts/converted_images/converted_svgs/aa0010.svg'
    old.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><rect width="40" height="40" fill="white"/></svg>')
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda:{})
    jobs = gui.Jobs(tmp_path/'gui')
    def run(job_id):
        with jobs.lock:
            (jobs.folder(job_id)/'result.svg').write_text(SVG, encoding='utf-8')
            job = jobs.jobs[job_id]
            job.update(status='done', result=True, quality='warning', message='Candidate ready')
            jobs.save(job)
    monkeypatch.setattr(jobs, 'run', run)
    manager = CatalogConversion(catalog, jobs, SimpleNamespace(busy=lambda:False))
    try:
        # Prepare a failing saved list. Starting the service must reuse it.
        (catalog.root/'artifacts/satisfactory_conversions/svgs/AA0010.svg').write_text(old.read_text())
        rows, summary, _ = build(catalog.root, measure=lambda *args:quality(False, .05))
        write_report(catalog.root, catalog.report_folder(), rows, summary, {})
        manager.start()
        manager.thread.join(45)
        snapshot = manager.snapshot()
        assert snapshot['status'] == 'done', snapshot
        assert snapshot['completed'] == snapshot['passed'] == 1
        assert catalog.payload()['rows'][0]['status'] == 'pixel_pass'
        assert catalog.payload()['summary']['catalog_statuses'] == {'pixel_pass':1}
        assert catalog.snapshot()['progress']['total'] == 1
        assert catalog.payload()['summary']['measurement_scope'] == 'single_candidate'
        assert 'catalog_background_svgs' in catalog.payload()['rows'][0]['selected']['svg']
        assert 'fill="white"' in old.read_text()  # Earlier candidate remains intact.
    finally:
        manager.close(); jobs.close()


def test_stop_during_real_refresh_kills_child_and_preserves_last_report(catalog, tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda:{})
    jobs = gui.Jobs(tmp_path/'gui')
    manager = CatalogConversion(catalog, jobs, SimpleNamespace(busy=lambda:False))
    # Resume the validation of one saved attempt, without a full inventory scan.
    job = jobs.upload('AA0010.jpg', (catalog.root/catalog.payload()['rows'][0]['image']).read_bytes())
    (jobs.folder(job['id'])/'result.svg').write_text(SVG, encoding='utf-8')
    jobs.jobs[job['id']].update(status='done', result=True)
    manager._update(last_attempt=dict(filename='AA0010.jpg', job_id=job['id'], result=True,
        passed=None, checking=False, message='Candidate ready'))
    import sys
    worker = tmp_path/'slow.py'
    worker.write_text('''import pathlib, subprocess, sys, time
folder=pathlib.Path(sys.argv[1])
child="import pathlib,sys,time; p=pathlib.Path(sys.argv[1]); (p/'ready').touch(); time.sleep(1.5); (p/'finished').touch()"
subprocess.Popen([sys.executable,'-c',child,str(folder)])
time.sleep(60)
''', encoding='utf-8')
    monkeypatch.setattr(catalog, 'command', lambda folder,*args:[sys.executable,str(worker),str(folder)])
    previous = catalog.report_folder()
    try:
        manager.start()
        wait_until(lambda: bool(catalog.job.get('id')))
        folder = catalog.directory/catalog.job['id']
        wait_for(folder/'ready')
        with pytest.raises(CatalogError):
            catalog.start()
        manager.cancel(); manager.thread.join(10)
        assert manager.snapshot()['status'] == 'stopped'
        assert catalog.snapshot()['status'] == 'cancelled'
        assert catalog.report_folder() == previous
        assert len(jobs.jobs) == 1
        time.sleep(1.7)
        assert not (folder/'finished').exists()
    finally:
        manager.close(); jobs.close()
