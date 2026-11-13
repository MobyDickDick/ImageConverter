"""Diagnostic evidence must survive failures, retries, cancellation and restart."""
import io
import json
from http.client import HTTPConnection
from pathlib import Path
import subprocess
import sys
import threading
import zipfile

import pytest

from src import imageConverterGui as gui
from tools import plan_b_workbench as wb

SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80"><rect width="80" height="80" fill="white"/><circle cx="40" cy="40" r="12" fill="green"/></svg>'
DESCRIPTION = 'Ein grüner Kreis auf weissem Hintergrund.'


@pytest.mark.parametrize('failures', [1, 5])
def test_report_retries_windows_reader_conflicts(tmp_path, monkeypatch, failures):
    wb.save_report(tmp_path, {'completed': 0})
    replace = Path.replace
    calls = []
    def busy(source, target):
        calls.append(source)
        # Every failed attempt must leave a valid, complete prior report.
        assert wb.read_report(tmp_path) == {'completed': 0}
        if len(calls) <= failures:
            raise PermissionError('Windows reader still holds report.json')
        return replace(source, target)
    monkeypatch.setattr(Path, 'replace', busy)
    monkeypatch.setattr(wb.time, 'sleep', lambda seconds: None)
    wb.save_report(tmp_path, {'completed': 1})
    assert wb.read_report(tmp_path) == {'completed': 1}
    assert len(calls) == failures + 1
    assert not list(tmp_path.glob('report.*.tmp'))


def test_permanent_report_lock_preserves_old_and_unsaved_results(tmp_path, monkeypatch):
    wb.save_report(tmp_path, {'completed': 0})
    def busy(source, target):
        raise PermissionError('persistent lock')
    monkeypatch.setattr(Path, 'replace', busy)
    monkeypatch.setattr(wb.time, 'sleep', lambda seconds: None)
    with pytest.raises(PermissionError, match='persistent lock'):
        wb.save_report(tmp_path, {'completed': 1})
    assert wb.read_report(tmp_path) == {'completed': 0}
    pending, = tmp_path.glob('report.*.tmp')
    assert json.loads(pending.read_text(encoding='utf-8')) == {'completed': 1}


@pytest.fixture
def prepared(tmp_path):
    folder = tmp_path / 'run'
    report = wb.prepare(SVG, DESCRIPTION, folder, seed=9223372036854775807)
    return folder, report


def test_preparation_retains_exact_source_and_17_distinct_rasters(prepared, tmp_path):
    folder, report = prepared
    assert len(report['cases']) == 17
    assert len({c['input_sha256'] for c in report['cases']}) == 17
    assert (folder / 'source.svg').read_text(encoding='utf-8') == SVG
    other = wb.prepare(SVG, DESCRIPTION, tmp_path / 'same', seed=report['seed'])
    assert [c['input_sha256'] for c in other['cases']] == [c['input_sha256'] for c in report['cases']]
    assert report['provenance']['python_sources_sha256']
    assert report['purpose'] == 'diagnostic'
    assert report['variation_profile'] == wb.VARIATION_PROFILE
    assert wb.summary(report)['completed'] == 0
    assert not wb.summary(report)['satisfactory']
    with pytest.raises(FileExistsError):
        wb.prepare(SVG, DESCRIPTION, folder, seed=42)


def test_tight_ac0022_source_keeps_all_transformed_viewports_inside_canvas(tmp_path):
    import math
    source = Path(__file__).resolve().parents[1] / 'fixtures/plan_b_templates/AC0022_canvas.svg'
    svg = source.read_text(encoding='utf-8-sig')
    report = wb.prepare(svg, 'Zwei vertikale Striche mit zwei Dreiecken und einer Verbindung.', tmp_path / 'run', seed=472)
    assert (report['cases'][0]['width'], report['cases'][0]['height']) == (35, 112)
    for case in report['cases'][1:]:
        v, canvas = case['variation'], case['canvas']
        assert case['width'] == 35 + 2 * math.ceil(max(0, ((v['scale'] - 1) / 2 + abs(v['relative_x'])) * 35))
        assert case['height'] == 112 + 2 * math.ceil(max(0, ((v['scale'] - 1) / 2 + abs(v['relative_y'])) * 112))
        assert canvas['policy'] == 'expand_symmetric_v1'
        assert wb.battery.viewport((tmp_path / 'run' / case['reference_svg']).read_text(encoding='utf-8'))[-2:] == (case['width'], case['height'])
    assert (report['cases'][1]['width'], report['cases'][1]['height']) == (39, 124)


@pytest.mark.parametrize('svg,description,seed', [
    (SVG.replace('<circle ', '<script/><circle '), DESCRIPTION, 42),
    (SVG.replace('<circle ', '<image href="https://example.org/x.png"/><circle '), DESCRIPTION, 42),
    (SVG.replace('width="80" height="80"', 'width="100000" height="80"', 1), DESCRIPTION, 42),
    (SVG, '', 42), (SVG, DESCRIPTION, -1), (SVG, DESCRIPTION, 2**63),
])
def test_rejects_unsafe_or_unbounded_inputs_before_creating_a_run(tmp_path, svg, description, seed):
    folder = tmp_path / 'bad'
    with pytest.raises((ValueError, SyntaxError)):
        wb.prepare(svg, description, folder, seed=seed)
    assert not folder.exists()


def test_failed_original_does_not_skip_variations_and_retries_keep_old_evidence(prepared, monkeypatch):
    folder, initial = prepared
    calls = []
    def convert(case, output, **kwargs):
        calls.append(case['case_id'])
        assert kwargs['extra_cli_args'] == ('--search-seed', str(initial['seed']))
        assert kwargs['keep_debug_artifacts']
        return dict(case, satisfactory=False, failures=['conversion_timeout'] if case['case_id'] == 'original' else ['foreground_iou_outside_limit'], elapsed_seconds=1)
    monkeypatch.setattr(wb.battery, 'run_case', convert)
    names = [c['case_id'] for c in initial['cases']]
    report = wb.execute(folder, names, iterations=7, timeout=2)
    assert calls == names
    assert report['status'] == 'completed'
    assert wb.summary(report) == dict(total=17, completed=17, passed=0, quality_failed=16, execution_failed=1,
                                     failure_counts={'conversion_timeout': 1, 'foreground_iou_outside_limit': 16}, satisfactory=False)
    old = (folder / 'attempts/attempt_0001/references/original.svg').read_bytes()
    report = wb.execute(folder, ['original'])
    assert len(report['attempts']) == 2
    assert len(report['attempts'][0]['results']) == 17
    assert (folder / 'attempts/attempt_0001/references/original.svg').read_bytes() == old
    assert (folder / 'original/target.png').is_file()
    csv = wb.export_csv(report).decode('utf-8-sig')
    assert len(csv.splitlines()) == 19
    assert 'attempt_0001' in csv and 'attempt_0002' in csv


def test_exception_preserves_partial_results_and_marks_batch_error(prepared, monkeypatch):
    folder, _ = prepared
    def convert(case, output, **kwargs):
        if case['case_id'] != 'original':
            raise RuntimeError('measurement unavailable')
        return dict(case, satisfactory=True, failures=[], elapsed_seconds=0)
    monkeypatch.setattr(wb.battery, 'run_case', convert)
    with pytest.raises(RuntimeError, match='measurement unavailable'):
        wb.execute(folder, ['original', 'probe_01'])
    report = wb.read_report(folder)
    assert report['status'] == 'error' and report['active_case'] is None
    assert len(report['attempts'][0]['results']) == 1
    assert wb.summary(report)['passed'] == 1


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path / 'jobs')
    server = gui.GuiServer(('127.0.0.1', 0), jobs)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    jobs.close()


def send(server, path, payload=None, headers=None):
    connection = HTTPConnection(*server.server_address, timeout=15)
    try:
        connection.request('GET' if payload is None else 'POST', path,
                           body=None if payload is None else json.dumps(payload).encode('utf-8'),
                           headers=headers if headers is not None else {'X-ImageConverter': '1'})
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def test_http_prepare_notes_exports_seed_precision_and_path_isolation(server):
    assert send(server, '/workbench')[0] == 200
    payload = dict(svg=SVG, description=DESCRIPTION, seed='9223372036854775807', name='ä.svg')
    assert send(server, '/api/workbench/prepare', payload, headers={})[0] == 403
    status, data = send(server, '/api/workbench/prepare', payload)
    report = json.loads(data)
    assert status == 201 and report['seed'] == payload['seed']
    base = '/api/workbench/' + report['id']
    assert send(server, base + '/asset?path=source.svg')[0] == 200
    assert send(server, base + '/asset?path=../outside.txt')[0] == 403
    assert send(server, base + '/asset?path=C:%5CWindows%5Cwin.ini')[0] == 403
    assert send(server, base + '/start', dict(cases=['made_up']))[0] == 400
    assert send(server, base + '/note', dict(case_id='original', note='Kreisrand fehlt. Hypothesen: Konturerkennung; Strichbreitenfit.'))[0] == 200
    status, archive = send(server, base + '/bundle')
    assert status == 200
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        assert 'source.svg' in bundle.namelist() and 'original/target.png' in bundle.namelist()
        assert 'Kreisrand fehlt' in bundle.read('report.json').decode('utf-8')
        assert 'workbench.csv' in bundle.namelist()
    assert send(server, base + '/report')[0] == 200
    assert send(server, base + '/csv')[0] == 200


def test_cancellation_kills_process_and_restart_preserves_completed_results(server):
    workbench = server.workbench
    report = workbench.prepare(dict(svg=SVG, description=DESCRIPTION, seed=42))
    folder = workbench.folder(report['id'])
    saved = wb.read_report(folder)
    saved.update(status='running', active_case='original')
    saved['attempts'].append(dict(status='running', results=[dict(case_id='probe_01', satisfactory=True, failures=[])]))
    wb.save_report(folder, saved)
    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {'start_new_session': True}
    process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], **options)
    workbench.process, workbench.active_id = process, report['id']
    assert workbench.cancel(report['id'])['status'] == 'cancelled'
    assert process.poll() is not None
    saved = wb.read_report(folder)
    saved['status'] = saved['attempts'][0]['status'] = 'running'
    wb.save_report(folder, saved)
    restored = gui.Workbench(server.jobs).snapshot(report['id'])
    assert restored['status'] == 'interrupted'
    assert restored['attempts'][0]['results'][0]['case_id'] == 'probe_01'


def test_http_reprepare_retains_legacy_report_and_source_with_same_seed(server):
    workbench = server.workbench
    original = workbench.prepare(dict(svg=SVG, description=DESCRIPTION, seed=472, name='Quelle.svg'))
    folder = workbench.folder(original['id'])
    legacy = wb.read_report(folder)
    legacy['variation_profile'] = 'whole_motif_scale_0.94_1.06_translate_0.025'
    legacy['notes'] = {'original': 'Bisheriger Befund'}
    wb.save_report(folder, legacy)
    previous_bytes = (folder / 'report.json').read_bytes()
    base = '/api/workbench/' + original['id']
    assert send(server, base + '/reprepare', {}, headers={})[0] == 403
    status, data = send(server, base + '/reprepare', {})
    fresh = json.loads(data)
    assert status == 200 and fresh['id'] != original['id']
    assert fresh['seed'] == '472' and fresh['source_description'] == DESCRIPTION
    assert fresh['variation_profile'] == wb.VARIATION_PROFILE
    assert fresh['reprepared_from'] == original['id']
    assert fresh['attempts'] == [] and fresh['notes'] == {}
    assert (workbench.folder(fresh['id']) / 'source.svg').read_text(encoding='utf-8') == SVG
    assert (folder / 'report.json').read_bytes() == previous_bytes
    assert any(c['width'] > 80 or c['height'] > 80 for c in fresh['cases'][1:])
    legacy['status'] = 'running'
    wb.save_report(folder, legacy)
    assert send(server, base + '/reprepare', {})[0] == 409
    legacy['status'] = 'prepared'
    wb.save_report(folder, legacy)


def test_workbench_respects_active_gui_conversion(server):
    workbench = server.workbench
    report = workbench.prepare(dict(svg=SVG, description=DESCRIPTION, seed=42))
    server.jobs.jobs['other'] = dict(status='running')
    try:
        with pytest.raises(gui.RequestError) as error:
            workbench.start(report['id'], dict(cases=['original']))
        assert error.value.status == 409
    finally:
        server.jobs.jobs.pop('other')


def description_table(root, directory, entries):
    from xml.etree import ElementTree as ET
    path = root / 'artifacts' / directory / 'Finale_Wurzelformen_V3.xml'
    path.parent.mkdir(parents=True, exist_ok=True)
    document = ET.Element('root')
    for key, description, image, detail in entries:
        entry = ET.SubElement(document, 'entry', key=key)
        ET.SubElement(entry, 'beschreibung').text = description
        if image:
            ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = image
            ET.SubElement(ET.SubElement(entry, 'bildbeschreibungen'), 'bildbeschreibung', bild=image).text = detail
    ET.ElementTree(document).write(path, encoding='utf-8')
    return path


def test_description_search_uses_specific_image_before_family_and_reports_file(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'ROOT', tmp_path)
    description_table(tmp_path, 'images_to_convert', [('AC1234', 'Kreis.', '', '')])
    secondary = description_table(tmp_path, 'descriptions', [('AC1234', 'Kreis.', 'AC1234_L.jpg', 'Grün mit schwarzer Kontur.')])
    result = gui.find_svg_description('C:\\irgendwo\\ac1234_L_PlanB.svg')
    assert result['description'] == 'Kreis. Grün mit schwarzer Kontur.'
    assert result['description_source'] == str(secondary.relative_to(tmp_path))
    assert result['description_key'] == 'ac1234_L'
    assert gui.find_svg_description('AC1234_M.svg')['description'] == 'Kreis.'


def test_primary_plan_b_table_and_sidecar_take_precedence(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'ROOT', tmp_path)
    primary = description_table(tmp_path, 'images_to_convert', [('AC1234', 'Aktuelle Beschreibung.', '', '')])
    description_table(tmp_path, 'descriptions', [('AC1234', 'Alte Beschreibung.', '', '')])
    assert gui.find_svg_description('AC1234.svg')['description_source'] == str(primary.relative_to(tmp_path))
    sidecar = tmp_path / 'artifacts/samples/AC1234.txt'
    sidecar.parent.mkdir(parents=True)
    sidecar.write_text('Eigene Beschreibung.', encoding='utf-8-sig')
    result = gui.find_svg_description('AC1234_PlanB.svg')
    assert result['description'] == 'Eigene Beschreibung.'
    assert result['description_source'] == str(sidecar.relative_to(tmp_path))


def test_inspect_previews_unknown_sources_without_preparing_cases(server, monkeypatch, tmp_path):
    monkeypatch.setattr(gui, 'ROOT', tmp_path)
    status, body = send(server, '/api/workbench/inspect', dict(name='neues_motiv.svg', svg=SVG))
    result = json.loads(body)
    assert status == 200
    assert not result['description'] and result['description_source'] is None
    assert len(result['description_searched']) == 3
    assert (result['width'], result['height']) == (80, 80)
    assert '<circle' in result['preview_svg']
    assert not list(server.workbench.directory.iterdir())
    bad = SVG.replace('<circle ', '<script/><circle ')
    assert send(server, '/api/workbench/inspect', dict(name='bad.svg', svg=bad))[0] == 400
    assert send(server, '/api/workbench/inspect', dict(name='bad.svg', svg=SVG), headers={})[0] == 403


def test_inspect_automatically_finds_description_and_does_not_cache_old_file(server, monkeypatch, tmp_path):
    monkeypatch.setattr(gui, 'ROOT', tmp_path)
    description_table(tmp_path, 'images_to_convert', [('AC1234', 'Ein grüner Kreis.', '', '')])
    payload = dict(name='AC1234_L.svg', svg=SVG)
    assert json.loads(send(server, '/api/workbench/inspect', payload)[1])['description'] == 'Ein grüner Kreis.'
    description_table(tmp_path, 'images_to_convert', [('AC1234', 'Korrigierte Beschreibung.', '', '')])
    assert json.loads(send(server, '/api/workbench/inspect', payload)[1])['description'] == 'Korrigierte Beschreibung.'


def test_inspect_catalog_svg_with_local_inherited_gradient(server):
    source = Path(__file__).resolve().parents[2] / 'artifacts/samples/AC0213_L.svg'
    payload = dict(name=source.name, svg=source.read_text(encoding='utf-8-sig'))
    status, body = send(server, '/api/workbench/inspect', payload)
    result = json.loads(body)
    assert status == 200, result
    assert (result['width'], result['height']) == (47, 61)
    assert '#swatch11' in result['preview_svg']
    assert 'linearGradient' in result['preview_svg']
