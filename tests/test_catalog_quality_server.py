"""Real report worker, cancellable process tree and local catalog API."""
from http.client import HTTPConnection
from contextlib import contextmanager
import json
from pathlib import Path
import shutil
import sys
import threading
import time

from PIL import Image, ImageDraw
import pytest

from src import imageConverterGui as gui
from src.imageConverterCatalog import CatalogError, CatalogQuality, atomic_json
from tools.build_catalog_inventory import build, write_report
from test_catalog_inventory import prepare, quality


@pytest.fixture
def catalog(tmp_path):
    root = tmp_path/'repo'
    prepare(root, archived=True)
    image = Image.new('RGB',(40,40),'white')
    ImageDraw.Draw(image).rectangle((8,8,31,31),fill='#555555')
    image.save(root/'artifacts/images_to_convert/AA0010.jpg')
    # Signature inputs are copied as metadata; the real project module executes.
    (root/'tools').mkdir()
    for name in ('build_catalog_inventory.py','run_plan_b_variations.py',
                 'evaluate_svg_text_baseline.py','evaluate_quality_complexity_gate.py'):
        shutil.copyfile(gui.ROOT/'tools'/name,root/'tools'/name)
    rows, summary, _ = build(root,measure=lambda *args:quality())
    write_report(root,root/'artifacts/catalog_inventory',rows,summary,{})
    manager = CatalogQuality(root,tmp_path/'jobs',gui.stop_process_tree)
    yield manager
    manager.close()


def test_real_cli_worker_publishes_new_complete_report_and_retains_previous(catalog):
    old = catalog.report_folder()/'manifest.json'
    original = old.read_bytes()
    catalog.start()
    catalog.thread.join(timeout=35)
    result = catalog.snapshot()
    assert result['status'] == 'done', result
    assert result['progress']['completed'] == result['progress']['total'] == 1
    assert result['summary']['fresh_conversion_performed'] is False
    assert result['summary']['semantic_revalidation_performed'] is False
    assert old.read_bytes() == original
    assert catalog.report_folder() != old.parent
    assert len(catalog.payload()['rows']) == 1
    previous = catalog.report_folder()
    catalog.start()
    catalog.thread.join(timeout=35)
    assert catalog.snapshot()['status'] == 'done'
    assert catalog.snapshot()['summary']['measurements_reused'] >= 1
    assert previous.is_dir()


def wait_for(path, timeout=8):
    end = time.monotonic()+timeout
    while not path.exists() and time.monotonic()<end:
        time.sleep(.02)
    assert path.exists()


def test_cancel_kills_worker_and_child_keeps_prior_list_and_allows_restart(catalog,monkeypatch,tmp_path):
    worker = tmp_path/'slow_worker.py'
    worker.write_text('''import pathlib, subprocess, sys, time
folder=pathlib.Path(sys.argv[1])
child="import pathlib,sys,time; p=pathlib.Path(sys.argv[1]); (p/'child-ready').touch(); time.sleep(1.5); (p/'child-finished').touch()"
subprocess.Popen([sys.executable,'-c',child,str(folder)])
(folder/'ready').touch()
time.sleep(60)
''',encoding='utf-8')
    old = catalog.report_folder()/'manifest.json'
    original = old.read_bytes()
    monkeypatch.setattr(catalog,'command',lambda folder,*args:[sys.executable,str(worker),str(folder)])
    first = catalog.start()
    folder = catalog.directory/first['id']
    wait_for(folder/'child-ready')
    with pytest.raises(CatalogError,match='bereits'):
        catalog.start()
    assert catalog.cancel()['status'] in {'cancelling','cancelled'}
    catalog.thread.join(timeout=5)
    assert catalog.snapshot()['status'] == 'cancelled'
    assert catalog.process is None
    assert old.read_bytes() == original
    assert not (catalog.directory/'current.json').exists()
    time.sleep(1.7)
    assert not (folder/'child-finished').exists()
    second = catalog.start()
    assert second['id'] != first['id']
    catalog.cancel()
    catalog.thread.join(timeout=5)
    assert catalog.snapshot()['status'] == 'cancelled'


def test_failed_worker_cannot_publish_incomplete_report(catalog,monkeypatch):
    previous = catalog.report_folder()
    monkeypatch.setattr(catalog,'command',lambda *args:[sys.executable,'-c','raise SystemExit(3)'])
    catalog.start(); catalog.thread.join(timeout=5)
    assert catalog.snapshot()['status'] == 'error'
    assert catalog.report_folder() == previous


@pytest.mark.parametrize('failures', [1,5])
def test_windows_progress_replacement_conflict_does_not_abort_measurement(tmp_path,monkeypatch,failures):
    from tools import build_catalog_inventory as inventory
    path=tmp_path/'progress.json'
    path.write_text('{"completed":0}',encoding='utf-8')
    real_replace=Path.replace
    attempts=[]
    def replace(source,target):
        attempts.append(1)
        if len(attempts)<=failures:
            raise PermissionError('Windows polling reader has file open')
        return real_replace(source,target)
    monkeypatch.setattr(Path,'replace',replace)
    monkeypatch.setattr(inventory.time,'sleep',lambda seconds:None)
    assert inventory.publish_progress(path,dict(completed=1)) == (failures<5)
    assert json.loads(path.read_text())['completed'] == (1 if failures<5 else 0)
    # A later UI tick publishes the current value after the reader releases it.
    assert inventory.publish_progress(path,dict(completed=2))
    assert json.loads(path.read_text())['completed'] == 2


@pytest.mark.parametrize('fail', [False,True])
def test_inventory_work_owns_and_releases_power_scope(catalog,tmp_path,monkeypatch,fail):
    from tools import build_catalog_inventory as inventory
    from src.iCCModules import imageCompositeConverterPower as power
    events=[]
    @contextmanager
    def awake():
        events.append('acquired')
        try:
            yield
        finally:
            events.append('released')
    class Worker:
        def measure(self,*args):
            if fail:
                raise RuntimeError('intentional measurement failure')
            return quality()
        def close(self):
            events.append('worker_closed')
    monkeypatch.setattr(power,'conversion_awake',awake)
    monkeypatch.setattr(inventory,'QualityWorker',Worker)
    monkeypatch.setattr(inventory,'runtime_signature',lambda root:('fixture',{}))
    monkeypatch.setattr(sys,'argv',['inventory','--root',str(catalog.root),'--output',str(tmp_path/'fresh-report')])
    if fail:
        with pytest.raises(RuntimeError,match='intentional'):
            inventory.main()
    else:
        assert inventory.main() == 0
    assert events == ['acquired','released','worker_closed']


def test_restart_marks_interrupted_job_and_preserves_report(catalog):
    atomic_json(catalog.directory/'job.json',dict(status='running',id='a'*32))
    restored = CatalogQuality(catalog.root,catalog.directory,gui.stop_process_tree)
    try:
        assert restored.snapshot()['status'] == 'interrupted'
        assert len(restored.payload()['rows']) == 1
    finally:
        restored.close()


def test_csv_and_assets_are_limited_to_published_inventory(catalog):
    text = catalog.export_csv().decode('utf-8-sig')
    assert 'AA0010.jpg' in text and 'pixel_pass' in text
    assert 'semantic_revalidated' in text
    assert catalog.asset('artifacts/images_to_convert/AA0010.jpg').is_file()
    with pytest.raises(CatalogError):
        catalog.asset('../../README.md')
    with pytest.raises(CatalogError):
        catalog.asset('tools/build_catalog_inventory.py')
    with pytest.raises(CatalogError):
        catalog.start(force='yes')


def test_new_reservations_override_old_published_inventory_without_measurement(catalog):
    assert catalog.payload()['rows'][0]['status'] == 'pixel_pass'
    config=catalog.root/'config'
    config.mkdir()
    atomic_json(config/'real_composition_holdout_new.json',dict(
        evaluation_policy=dict(status='sealed_unrun'),cases=[dict(file='AA0010.jpg')]))
    payload=catalog.payload()
    assert payload['rows'][0]['status'] == 'reserved'
    assert payload['rows'][0]['selected'] is None and not payload['rows'][0]['candidates']
    assert payload['summary']['catalog_statuses'] == {'reserved':1}
    assert payload['summary']['groups']['AA']['statuses'] == {'reserved':1}
    assert payload['summary']['archived_current_pixel_pass'] == 0
    with pytest.raises(CatalogError):
        catalog.asset('artifacts/images_to_convert/AA0010.jpg')


def test_http_catalog_routes_downloads_and_origin_protection(catalog,monkeypatch,tmp_path):
    monkeypatch.setattr(gui,'catalog_descriptions',lambda:{})
    jobs = gui.Jobs(tmp_path/'gui')
    server = gui.GuiServer(('127.0.0.1',0),jobs)
    server.catalog.close()
    server.catalog = catalog
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    def request(path,method='GET',headers=None,body=None):
        connection=HTTPConnection(*server.server_address,timeout=5)
        try:
            connection.request(method,path,headers=headers or {},body=body)
            response=connection.getresponse()
            return response.status,response.read()
        finally:
            connection.close()
    try:
        for path in ('/catalog','/catalog.js','/catalog.css','/api/catalog','/api/catalog/list','/api/catalog/csv','/api/catalog/json','/api/catalog/conversion'):
            assert request(path)[0] == 200
        assert b'AA0010.jpg' in request('/api/catalog/list')[1]
        assert request('/api/catalog/asset?path=tools/build_catalog_inventory.py')[0] == 403
        # These requests are rejected before body parsing. Do not race a second
        # TCP body packet against Windows closing an intentionally unread body.
        assert request('/api/catalog/start','POST',body=b'')[0] == 403
        assert request('/api/catalog/start','POST',{'X-ImageConverter':'1','Origin':'https://example.org'},b'')[0] == 403
        assert request('/api/catalog/start','POST',{'X-ImageConverter':'1'},b'[]')[0] == 400
        assert request('/api/catalog/start','POST',{'X-ImageConverter':'1'},b'{"force":"false"}')[0] == 400
        assert request('/api/catalog/cancel','POST',{'X-ImageConverter':'1'},b'{}')[0] == 200
        assert request('/api/catalog/conversion/start','POST',body=b'')[0] == 403
        assert request('/api/catalog/conversion/stop','POST',{'X-ImageConverter':'1','Origin':'https://example.org'},b'')[0] == 403
        assert request('/api/catalog/conversion/start','POST',{'X-ImageConverter':'1'},b'[]')[0] == 400
        assert request('/api/catalog/conversion/start','POST',{'X-ImageConverter':'1'},b'{"profile":[]}')[0] == 400
        assert request('/api/catalog/conversion/stop','POST',{'X-ImageConverter':'1'},b'{}')[0] == 200
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close();jobs.close()


def test_second_server_cannot_share_port_or_read_the_running_servers_jobs(monkeypatch,tmp_path):
    monkeypatch.setattr(gui,'catalog_descriptions',lambda:{})
    jobs = gui.Jobs(tmp_path/'first')
    server = gui.GuiServer(('127.0.0.1',0),jobs)
    def forbidden(*args, **kwargs):
        pytest.fail('A duplicate server must fail before reading or changing persisted jobs')
    monkeypatch.setattr(gui,'Jobs',forbidden)
    try:
        with pytest.raises(OSError):
            gui.GuiServer(server.server_address,directory=tmp_path/'second')
        assert not (tmp_path/'second').exists()
        if sys.platform == 'win32':
            import socket
            assert server.socket.getsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE) == 1
    finally:
        server.server_close();jobs.close()


@pytest.mark.parametrize('no_browser',[False,True])
def test_start_reuses_matching_server_and_opens_it_without_reading_jobs(monkeypatch,tmp_path,capsys,no_browser):
    monkeypatch.setattr(gui,'catalog_descriptions',lambda:{})
    jobs = gui.Jobs(tmp_path/'first')
    server = gui.GuiServer(('127.0.0.1',0),jobs)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    opened = []
    monkeypatch.setattr(gui.webbrowser,'open',opened.append)
    def forbidden(*args, **kwargs):
        pytest.fail('Opening an existing server must not reload its jobs')
    monkeypatch.setattr(gui,'Jobs',forbidden)
    try:
        args = ['--port',str(server.server_port),'--data-dir',str(jobs.directory)]
        if no_browser:
            args.append('--no-browser')
        assert gui.main(args) == 0
        assert opened == ([] if no_browser else [f'http://127.0.0.1:{server.server_port}'])
        output = capsys.readouterr()
        assert 'läuft bereits' in output.out
        assert not output.err
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close();jobs.close()


def test_start_rejects_server_with_different_data_directory(monkeypatch,tmp_path,capsys):
    monkeypatch.setattr(gui,'catalog_descriptions',lambda:{})
    jobs = gui.Jobs(tmp_path/'first')
    server = gui.GuiServer(('127.0.0.1',0),jobs)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    opened = []
    monkeypatch.setattr(gui.webbrowser,'open',opened.append)
    try:
        assert gui.main(['--port',str(server.server_port),'--data-dir',str(tmp_path/'other')]) == 1
        assert not opened and not (tmp_path/'other').exists()
        assert 'GUI konnte nicht gestartet werden' in capsys.readouterr().err
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close();jobs.close()


@pytest.mark.parametrize('config', [dict(application='other'), [],
    dict(application='imageconverter_gui',api_version=1,project_root='elsewhere',data_directory='elsewhere')])
def test_existing_gui_rejects_unrelated_server_metadata(monkeypatch,tmp_path,config):
    import io
    class Opener:
        def open(self,*args,**kwargs):
            return io.BytesIO(json.dumps(config).encode())
    monkeypatch.setattr(gui,'build_opener',lambda *args:Opener())
    assert gui.existing_gui(8766,tmp_path) is None


def test_service_state_publication_retries_short_windows_file_locks(tmp_path,monkeypatch):
    from src import imageConverterCatalog as module
    destination = tmp_path/'state.json'
    original = Path.replace
    attempts = []
    def replace(source,target):
        attempts.append(1)
        if len(attempts) < 3:
            raise PermissionError('Temporary Windows file lock')
        return original(source,target)
    monkeypatch.setattr(Path,'replace',replace)
    monkeypatch.setattr(module.time,'sleep',lambda seconds:None)
    atomic_json(destination,dict(status='running',completed=1))
    assert json.loads(destination.read_text())['completed'] == 1
    assert len(attempts) == 3
