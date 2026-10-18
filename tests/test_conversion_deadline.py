"""Real spawn/process-tree tests, with short explicit wall-clock budgets."""
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import SearchPolicy, svg_identity
from src.iCCModules.imageCompositeConverterDeadline import ImageDeadline, _atomic_pickle


def blocked_worker(connection, payload):
    stage = Path(payload['stage'])
    # An interrupted write must never reach a final output directory.
    (Path(payload['spec']['svg_out_dir'])/'sample.svg').write_text('unfinished')
    _atomic_pickle(stage/'unfinished.pickle', {'unvalidated': True})
    time.sleep(30)


def completed_worker(connection, payload):
    spec, stage = payload['spec'], Path(payload['stage'])
    row = dict(filename=spec['filename'], params={}, mean_delta2=payload['action'].get('mean', 12.), search_satisfactory=False)
    (Path(spec['svg_out_dir'])/'sample.svg').write_text('<svg>complete</svg>')
    import pickle
    session = pickle.loads(payload['session'])
    _atomic_pickle(stage/'completed.pickle', dict(result=(row, False), failures=[], session=session))
    connection.send(('done', 'completed.pickle'))


def crashing_worker(connection, payload):
    raise RuntimeError('controlled worker failure')


def forbidden_reference_worker(connection, payload):
    from src import imageCompositeConverter as app
    from src.iCCModules.imageCompositeConverterDeadline import conversion_worker
    path = Path(payload['spec']['folder_path'])/'forbidden.svg'
    def read_reference(*args, **kwargs):
        return path.read_text(encoding='utf-8')
    app.Action.renderSvgToNumpy = staticmethod(read_reference)
    conversion_worker(connection, payload)


def checkpoint_worker(connection, payload):
    stage = Path(payload['stage'])
    svg = '<svg>validated</svg>'
    candidate = dict(row=dict(params={}, mean_delta2=2., search_satisfactory=True), svg=svg,
                     source_file_hash=payload['source_file_hash'], png=b'checked png',
                     svg_hash=svg_identity(svg), quality=dict(passed=True))
    mode = payload['action'].get('mode')
    if mode == 'bad_svg':
        candidate['svg'] = 'tampered'
    if mode == 'bad_source':
        candidate['source_file_hash'] = 'wrong source'
    if mode == 'failed_gate':
        candidate['quality']['passed'] = False
    _atomic_pickle(stage/'checked.pickle', candidate)
    connection.send(('checkpoint', 'checked.pickle'))
    time.sleep(30)  # Simulates a blocked final render, after validation.


def progressing_worker(connection, payload):
    started = payload['started']
    connection.send(('progress', (time.monotonic(), 100.)))
    while time.monotonic()-started < 1.8:
        time.sleep(.01)
    connection.send(('progress', (time.monotonic(), 70.)))
    time.sleep(.5)
    completed_worker(connection, payload)


def descendant_worker(connection, payload):
    marker = Path(payload['spec']['folder_path'])/'heartbeat'
    code = ('import pathlib,time; p=pathlib.Path('+repr(str(marker))+'); '
            '\nwhile True:\n p.write_text(str(time.time()))\n time.sleep(.03)')
    subprocess.Popen([sys.executable, '-c', code])
    time.sleep(30)


@pytest.fixture
def spec(tmp_path):
    (tmp_path/'sample.png').write_bytes(b'input fixture')
    result = dict(filename='sample.png', folder_path=str(tmp_path), csv_path='unused',
                  iteration_budget=2, badge_rounds=2, debug_ac0811_dir=None, debug_element_diff_dir=None)
    for key in ('svg_out_dir', 'diff_out_dir', 'png_out_dir', 'reports_out_dir'):
        result[key] = str(tmp_path/key)
        Path(result[key]).mkdir()
    return result


def run(deadline, spec, worker, **action):
    return deadline.run(spec, config={}, action=action, worker=worker)


def test_blocked_worker_is_killed_without_publishing_partial_or_old_outputs(spec):
    original = Path(spec['svg_out_dir'])/'sample.svg'
    original.write_text('protected earlier run')
    deadline = ImageDeadline(SearchPolicy(seconds=1.5, max_seconds=2.))
    started = time.monotonic()
    (row, failed), failures = run(deadline, spec, blocked_worker)
    assert time.monotonic()-started < 3.5
    assert failed and row is None and failures[0]['reason'] == 'TimeoutError'
    assert original.read_text() == 'protected earlier run'
    assert not list(Path(spec['reports_out_dir']).glob('.image-worker-*'))
    before = time.monotonic()
    assert run(deadline, spec, completed_worker)[0] == (None, True)
    assert time.monotonic()-before < .3


@pytest.mark.parametrize('mode', [None, 'bad_svg', 'bad_source', 'failed_gate'])
def test_only_bound_validated_checkpoints_survive_blocked_finalization(spec, mode):
    deadline = ImageDeadline(SearchPolicy(seconds=1.5, max_seconds=2.))
    (row, failed), failures = run(deadline, spec, checkpoint_worker, mode=mode)
    target = Path(spec['svg_out_dir'])/'sample.svg'
    if mode is None:
        assert not failed and not failures and row['search_satisfactory']
        assert row['search_control']['stop_reason'] == 'time_limit'
        assert target.read_text() == '<svg>validated</svg>'
    else:
        assert failed and failures and row is None and not target.exists()


def test_completed_handoff_then_timeout_preserves_best_and_cumulative_budget(spec):
    deadline = ImageDeadline(SearchPolicy(seconds=2., max_seconds=3.))
    (row, failed), failures = run(deadline, spec, completed_worker)
    assert row and not failed and not failures
    assert row['search_control']['isolated']
    spent = deadline.session.elapsed
    assert spent > 0
    (row, failed), failures = run(deadline, spec, blocked_worker)
    assert failed and failures and row['mean_delta2'] == 12.
    assert 2. <= deadline.session.elapsed < 3.5
    assert (Path(spec['svg_out_dir'])/'sample.svg').read_text() == '<svg>complete</svg>'


def test_checked_checkpoint_takes_priority_over_an_unvalidated_lower_score(spec):
    deadline = ImageDeadline(SearchPolicy(seconds=2., max_seconds=3.))
    run(deadline, spec, completed_worker, mean=.1)
    (row, failed), failures = run(deadline, spec, checkpoint_worker)
    assert row['search_satisfactory'] and not failed and not failures
    assert row['mean_delta2'] == 2.
    assert (Path(spec['svg_out_dir'])/'sample.svg').read_text() == '<svg>validated</svg>'


def test_real_late_progress_can_extend_but_never_beyond_maximum(spec):
    events = []
    deadline = ImageDeadline(SearchPolicy(seconds=2., max_seconds=3., extension_seconds=1.),
                             emit=lambda **event: events.append(event))
    (row, failed), failures = run(deadline, spec, progressing_worker)
    assert row and not failed and not failures
    assert deadline.session.extensions == 1
    assert events[0]['event'] == 'time_extended'
    assert 2. < deadline.session.elapsed < 3.5


def test_external_hard_limit_dominates_adaptive_policy(spec):
    deadline = ImageDeadline(SearchPolicy(seconds=3., max_seconds=6.), hard_seconds=1.5)
    (row, failed), _ = run(deadline, spec, blocked_worker)
    assert row is None and failed and deadline.session.elapsed < 3.
    report = json.loads((Path(spec['reports_out_dir'])/'sample_deadline.json').read_text())
    assert report['external_max_seconds'] == 1.5


def test_crash_is_recorded_and_a_new_image_can_still_complete(spec):
    first = ImageDeadline(SearchPolicy(seconds=2., max_seconds=3.))
    (row, failed), failures = run(first, spec, crashing_worker)
    assert failed and row is None and failures[0]['reason'] == 'WorkerError'
    second = ImageDeadline(SearchPolicy(seconds=2., max_seconds=3.))
    assert run(second, spec, completed_worker)[0][1] is False


def test_changed_input_cannot_reuse_a_previous_output_or_search_state(spec):
    deadline = ImageDeadline(SearchPolicy(seconds=2., max_seconds=3.))
    assert run(deadline, spec, completed_worker)[0][0]
    (Path(spec['folder_path'])/spec['filename']).write_bytes(b'changed pixels')
    (row, failed), failures = run(deadline, spec, completed_worker)
    assert failed and row is None and failures
    assert deadline.closed and deadline.best_row is None


def test_descendant_renderer_cannot_keep_running_after_deadline(spec):
    deadline = ImageDeadline(SearchPolicy(seconds=1.5, max_seconds=2.))
    run(deadline, spec, descendant_worker)
    marker = Path(spec['folder_path'])/'heartbeat'
    before = marker.read_text()
    time.sleep(.15)
    assert marker.read_text() == before
    assert not list(Path(spec['reports_out_dir']).glob('.image-worker-*'))


def test_session_serialization_preserves_identity_and_bot_state_without_callbacks():
    import pickle
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch
    session = ImageSearch(SearchPolicy(), emit=lambda **event: None)
    session.validated.add(('svg', 'raster'))
    session.on_validated = lambda *args: None
    session.bot_searches = {'attempt': [1, 2, 3]}
    restored = pickle.loads(pickle.dumps(session))
    assert restored.validated == session.validated
    assert restored.bot_searches == session.bot_searches
    assert restored.on_validated is None


def test_production_cli_does_not_render_in_parent_reporting(tmp_path, monkeypatch):
    import shutil
    from xml.etree import ElementTree as ET
    from src import imageCompositeConverter as app
    import src.overviewTiles as overviews
    root = Path(__file__).resolve().parents[1]
    source = root/'artifacts/images_to_convert/AC0232_M.jpg'
    shutil.copyfile(source, tmp_path/'sample.jpg')
    catalog = ET.parse(root/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml')
    description = next(e.findtext('beschreibung') for e in catalog.iter('entry')
                       if source.name in [p.text for p in e.findall('bilder/bild')])
    table = ET.Element('root')
    entry = ET.SubElement(table, 'entry', key='sample', kind='wurzelform')
    ET.SubElement(entry, 'beschreibung').text = description
    ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = 'sample.jpg'
    descriptions = tmp_path/'descriptions.xml'
    ET.ElementTree(table).write(descriptions, encoding='utf-8')

    def forbidden(*args, **kwargs):
        pytest.fail('Per-image finalization must never launch a renderer in the parent')

    monkeypatch.setattr(app.Action, 'renderSvgToNumpy', forbidden)
    monkeypatch.setattr(app.Action, 'render_svg_to_numpy', forbidden)
    monkeypatch.setattr(overviews, '_renderSvg', forbidden)
    monkeypatch.setattr(app, 'SVG_RENDER_SUBPROCESS_ENABLED', False)
    monkeypatch.setenv('IMAGE_CONVERTER_ISOLATE_SVG_RENDER', '0')
    out = tmp_path/'out'
    assert app.main([str(tmp_path), '--descriptions-path', str(descriptions), '--output-dir', str(out),
                     '--start', 'sample', '--end', 'sample', '--search-seed', '42',
                     '--log-file', str(tmp_path/'cli.log'), '--deterministic-order']) == 0
    rows = json.loads((out/'reports/conversion_result_map.json').read_text(encoding='utf-8'))
    assert rows['sample.jpg']['search_satisfactory']
    assert rows['sample.jpg']['search_control']['isolated']
    assert (out/'reports/overview_svg_tiles.png').exists()


def test_spawned_production_worker_blocks_and_reports_foreign_reference_svg(spec):
    import shutil
    from xml.etree import ElementTree as ET
    from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, settings
    root = Path(__file__).resolve().parents[1]
    source = root/'artifacts/images_to_convert/AC0232_M.jpg'
    folder = Path(spec['folder_path'])
    shutil.copyfile(source, folder/spec['filename'])
    catalog = ET.parse(root/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml')
    description = next(e.findtext('beschreibung') for e in catalog.iter('entry')
                       if source.name in [p.text for p in e.findall('bilder/bild')])
    table = ET.Element('root')
    entry = ET.SubElement(table, 'entry', key='sample', kind='wurzelform')
    ET.SubElement(entry, 'beschreibung').text = description
    ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = spec['filename']
    descriptions = folder/'descriptions.xml'
    ET.ElementTree(table).write(descriptions, encoding='utf-8')
    spec['csv_path'] = str(descriptions)
    foreign = folder/'forbidden.svg'
    foreign.write_text('<svg>reference must not be loaded</svg>', encoding='utf-8')
    with search_configuration(mode='portfolio', adaptive=True, seed=42):
        deadline = ImageDeadline(SearchPolicy(seconds=3., max_seconds=3.))
        (row, failed), failures = deadline.run(spec, config=settings(), action={}, worker=forbidden_reference_worker)
    assert failed and failures and row is None
    access = json.loads((Path(spec['reports_out_dir'])/'sample_reference_access.json').read_text(encoding='utf-8'))
    assert str(foreign.resolve()) in access['blocked_svg_reads']
