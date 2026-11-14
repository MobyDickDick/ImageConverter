"""Real native recovery plus GUI deadline, preview and draft retention contracts."""
import io
import json
from pathlib import Path
import subprocess
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from PIL import Image
import pytest

from src import imageConverterGui as gui
from src import imageConverterRecovery as recovery
from src.iCCModules.imageCompositeConverterArrowPair import fit_arrow_pair
from src.imageConverterSample import render_svg

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Wie AC0020: zwei vertikale Striche links rot, rechts, blau, unten Dreiecke rot blau, '
               'links Spitze nach unten, rechts Spitze nach oben.\nBei ca. 33% eine rote horizontale Linie')
SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24"><circle cx="16" cy="12" r="7" fill="#225599"/></svg>'
MATCHING_DESCRIPTION = ('zwei vertikale Striche links blau, rechts, rot, unten Dreiecke blau rot, '
                        'links Spitze nach unten, rechts Spitze nach oben. '
                        'In ca 33% der Höhe eine blaue waagrechte Linie.')
ARROWS = ('<svg xmlns="http://www.w3.org/2000/svg" width="30" height="80">'
          '<g><rect x="4.5" y="0" width="1" height="76" fill="#2277bb"/>'
          '<polygon points="5,80 1,72 9,72" fill="#2277bb"/>'
          '<rect x="24.5" y="0" width="1" height="76" fill="#ee1111"/>'
          '<polygon points="25,72 21,80 29,80" fill="#ee1111"/>'
          '<rect x="5" y="50" width="20" height="1" fill="#2277bb"/></g></svg>')


def test_conflicting_arrow_description_still_produces_incremental_native_draft(tmp_path):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0070_L.jpg'))
    source = tmp_path/'unrelated.png'
    cv2.imwrite(str(source), image)
    revisions = []
    output = tmp_path/'draft.svg'
    report = recovery.recover(source, output, DESCRIPTION, 2., seed=7,
        on_preview=lambda report: revisions.append((report, output.read_text(encoding='utf-8'))))
    assert report['stop_reason'] == 'time_limit'
    assert 2 <= report['elapsed_seconds'] < 3
    assert report['evaluations'] > 30 and len(revisions) > 4
    assert not report['passed'] and report['description_error'] == 'wrong_described_arrow_direction:left'
    assert report['pixel_quality']['passed'], report
    root = ET.parse(output).getroot()
    tags = [e.tag.rsplit('}', 1)[-1] for e in root.iter()]
    assert tags.count('polygon') == 2 and tags.count('rect') == 3
    assert not {'image', 'path', 'text'} & set(tags)
    counts = [len(list(ET.fromstring(svg))) for _, svg in revisions[:5]]
    assert counts == [1, 2, 3, 4, 5]
    errors = [r['normalized_mse'] for r, _ in revisions]
    assert all(b < a for a, b in zip(errors, errors[1:]))
    # Draft generation must not weaken the normal model's strict contract.
    assert fit_arrow_pair(image.shape[1], image.shape[0], description=DESCRIPTION, image=image,
        render_fn=lambda s,w,h: render_svg(s,w,h)[:,:,::-1].copy(),
        error_fn=lambda a,b: float(np.square(a.astype(float)-b).mean())) is None


def test_unrecognized_motif_uses_structural_element_search(tmp_path):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48">'
           '<rect x="9" y="10" width="18" height="24" fill="#223344"/>'
           '<line x1="27" y1="22" x2="43" y2="22" stroke="#223344" stroke-width="2"/></svg>')
    source, output = tmp_path/'neutral.png', tmp_path/'draft.svg'
    Image.fromarray(render_svg(svg,48,48)).save(source)
    report = recovery.recover(source, output, 'Ein geometrisches Motiv.', 1., seed=7)
    assert report['elapsed_seconds'] >= 1. and report['evaluations'] > 10
    assert report['normalized_mse'] < .02 and not report['passed']
    tags = [e.tag.rsplit('}',1)[-1] for e in ET.parse(output).getroot().iter()]
    assert 'image' not in tags and 'path' not in tags and ('line' in tags or tags.count('rect') > 1)


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    monkeypatch.setattr(jobs, 'publish_best', lambda *args: None)
    buffer = io.BytesIO()
    Image.fromarray(render_svg(SVG,32,24)).save(buffer, format='PNG')
    uploaded = jobs.upload('neutral.png', buffer.getvalue())
    job = jobs.jobs[uploaded['id']]
    yield jobs, job, jobs.folder(job['id'])
    jobs.close()


def test_failed_first_attempt_spends_remaining_budget_and_keeps_killed_worker_draft(case, monkeypatch):
    jobs, job, folder = case
    now, waits, commands = [0.], [], []
    monkeypatch.setattr(gui.time, 'monotonic', lambda: now[0])
    job.update(status='running', started=gui.time.time(), search_seed=7, profile='thorough', description='Ein Kreis.')

    class Process:
        returncode = 2
        def __init__(self, command, **kwargs):
            commands.append(command)
            self.recovery = 'src.imageConverterRecovery' in command
            if self.recovery:
                assert jobs.snapshot(job['id'])['status'] == 'running'
                (folder/'recovery.svg').write_text(SVG)
                (folder/'recovery.json').write_text(json.dumps(dict(evaluations=100, passed=False)))
                snapshot = jobs.snapshot(job['id'])
                assert snapshot['preview'] and snapshot['preview_revision']
            else:
                path = folder/'output/converted_svg_failed/Failed_UPLOAD.svg'
                path.parent.mkdir(parents=True)
                path.write_text('<svg><image href="data:image/png;base64,AA=="/></svg>')
        def wait(self, timeout):
            waits.append(timeout)
            now[0] += timeout if self.recovery else 2.
            if self.recovery:
                raise subprocess.TimeoutExpired('recovery', timeout)

    stopped = []
    monkeypatch.setattr(gui.subprocess, 'Popen', Process)
    monkeypatch.setattr(gui, 'stop_process_tree', lambda p: stopped.append(p))
    jobs.run(job['id'])
    assert waits == [240., 238.]
    assert len(stopped) == 1 and len(commands) == 2
    assert job['status'] == 'done' and job['result'] and job['quality'] == 'passed'
    assert job['pixel_quality']['passed']
    assert job['recovery_report']['stop_reason'] == 'time_limit'
    assert 'result_rejection' not in job and (folder/'result.svg').read_text() == SVG


def test_passed_first_attempt_finishes_without_recovery(case, monkeypatch):
    jobs, job, folder = case
    job.update(status='running', started=gui.time.time(), search_seed=7, description='Ein Kreis.')
    commands = []
    class Process:
        returncode = 0
        def __init__(self, command, **kwargs):
            commands.append(command)
            path = folder/'output/converted_svgs/UPLOAD.svg'
            path.parent.mkdir(parents=True)
            path.write_text(SVG)
        def wait(self, timeout):
            pass
    monkeypatch.setattr(gui.subprocess, 'Popen', Process)
    jobs.run(job['id'])
    assert job['quality'] == 'passed' and job['result'] and len(commands) == 1


def test_cancellation_preserves_a_completed_native_preview(case, monkeypatch):
    jobs, job, folder = case
    job.update(status='running', started=gui.time.time(), search_seed=7, description='Ein Kreis.')
    collected = dict(job, result=False)
    class Process:
        returncode = 0
        def __init__(self, *args, **kwargs):
            (folder/'recovery.svg').write_text(SVG)
            (folder/'recovery.json').write_text('{}')
        def wait(self, timeout):
            jobs.cancel(job['id'])
    monkeypatch.setattr(gui.subprocess, 'Popen', Process)
    monkeypatch.setattr(gui, 'stop_process_tree', lambda p: None)
    jobs.recover_result(job['id'], collected, gui.time.monotonic()+10, {}, {})
    assert job['status'] == 'cancelled' and job['result']
    assert (folder/'result.svg').read_text() == SVG


def test_recovery_cannot_replace_better_existing_vector(case):
    _, job, folder = case
    (folder/'result.svg').write_text(SVG)
    worse = SVG.replace('cx="16"', 'cx="20"')
    (folder/'recovery.svg').write_text(worse)
    (folder/'recovery.json').write_text('{}')
    job.update(status='done', result=True, quality='warning', pixel_quality={'normalized_mse': 0.})
    gui.collect_recovery_result(folder, job, stop_reason='time_limit')
    assert (folder/'result.svg').read_text() == SVG
    assert job['result'] and job['quality'] == 'passed'


def test_raster_diagnostic_cannot_become_a_recovery_preview_result(case):
    _, job, folder = case
    (folder/'recovery.svg').write_text('<svg><image href="data:image/png;base64,AA=="/></svg>')
    (folder/'recovery.json').write_text('{}')
    gui.collect_recovery_result(folder, job, stop_reason='time_limit')
    assert not job['result'] and not (folder/'result.svg').exists()


def test_deadline_between_svg_and_report_write_retains_independently_checked_draft(case):
    _, job, folder = case
    (folder/'recovery.svg').write_text(SVG)
    gui.collect_recovery_result(folder, job, stop_reason='time_limit')
    assert job['result'] and job['quality'] == 'passed' and job['pixel_quality']['passed']


def test_matching_recovery_finishes_early_with_native_heads_and_waagrechte_bar(tmp_path):
    source, output = tmp_path/'neutral.png', tmp_path/'draft.svg'
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0060_S.jpg'))
    cv2.imwrite(str(source), image)
    description = MATCHING_DESCRIPTION
    report = recovery.recover(source, output, description, 10., seed=7)
    assert report['passed'] and report['stop_reason'] == 'quality_target_reached'
    assert report['elapsed_seconds'] < 10.
    assert report['pixel_quality']['passed'] and not report['description_error']
    assert not report['model_confirmed']  # SVG acceptance does not invent a model verdict.
    job = dict(width=image.shape[1], height=image.shape[0], description=description, result=False)
    source.rename(tmp_path/'source.png')
    output.rename(tmp_path/'recovery.svg')
    output.with_suffix('.json').rename(tmp_path/'recovery.json')
    gui.collect_recovery_result(tmp_path, job, stop_reason='worker_finished')
    assert job['quality'] == 'passed'
    assert job['recovery_report']['stop_reason'] == 'quality_target_reached'


@pytest.mark.parametrize('fault', ['wrong_direction', 'missing_head', 'wrong_bar', 'wrong_color', 'invalid_description'])
def test_pixel_pass_and_worker_claim_cannot_override_description_failure(tmp_path, fault):
    svg, description = ARROWS, MATCHING_DESCRIPTION
    if fault == 'wrong_direction':
        description = description.replace('links Spitze nach unten', 'links Spitze nach oben')
    elif fault == 'wrong_bar':
        description = description.replace('blaue waagrechte Linie', 'rote waagrechte Linie')
    elif fault == 'wrong_color':
        description = description.replace('links blau', 'links rot')
    elif fault == 'invalid_description':
        description += ' Es gibt genau drei Dreiecke.'
    else:
        root = ET.fromstring(svg)
        group = root[0]
        group.remove(next(e for e in group if e.tag.endswith('polygon')))
        svg = ET.tostring(root, encoding='unicode')
    Image.fromarray(render_svg(svg,30,80)).save(tmp_path/'source.png')
    (tmp_path/'recovery.svg').write_text(svg, encoding='utf-8')
    (tmp_path/'recovery.json').write_text('{"passed": true, "model_confirmed": true}')
    job = dict(width=30, height=80, description=description, result=False)
    gui.collect_recovery_result(tmp_path, job, stop_reason='worker_finished')
    assert job['pixel_quality']['passed'] and job['quality'] == 'warning'
    assert job['description_error'] and not job['recovery_report']['passed']


def test_completed_recovery_is_rechecked_on_server_reload(case):
    jobs, job, folder = case
    for name in ('result.svg', 'recovery.svg'):
        (folder/name).write_text(SVG)
    job.update(status='done', result=True, quality='warning', recovery=True,
               description='Ein Kreis.', description_validation_version=2)
    jobs.save(job)
    restored = gui.Jobs(jobs.directory)
    try:
        result = restored.jobs[job['id']]
        assert result['quality'] == 'passed' and result['pixel_quality']['passed']
        assert json.loads((folder/'job.json').read_text(encoding='utf-8'))['quality'] == 'passed'
    finally:
        restored.close()


def test_matching_candidate_is_accepted_without_further_search(case, monkeypatch):
    _, _, folder = case
    candidate = folder/'candidate.svg'
    candidate.write_text(SVG)
    def forbidden(*args, **kwargs):
        pytest.fail('a verified candidate must finish without another search')
    monkeypatch.setattr(recovery, 'fit_arrow_pair', forbidden)
    monkeypatch.setattr(recovery, 'polish_generated_svg', forbidden)
    report = recovery.recover(folder/'source.png', folder/'recovery.svg', 'Ein Kreis.',
                              30., candidate=candidate)
    assert report['passed'] and report['stop_reason'] == 'quality_target_reached'
    assert report['evaluations'] == 1 and report['elapsed_seconds'] < 1.


def test_worker_claim_cannot_override_failed_image_comparison(case):
    _, job, folder = case
    (folder/'recovery.svg').write_text(SVG.replace('cx="16"', 'cx="4"'))
    (folder/'recovery.json').write_text('{"passed": true}')
    job['description'] = 'Ein Kreis.'
    gui.collect_recovery_result(folder, job, stop_reason='worker_finished')
    assert job['quality'] == 'warning' and not job['pixel_quality']['passed']
