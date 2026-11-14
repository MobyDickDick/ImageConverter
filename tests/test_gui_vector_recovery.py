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
    assert job['status'] == 'done' and job['result'] and job['quality'] == 'warning'
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
    assert job['result'] and job['quality'] == 'warning'


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
    assert job['result'] and job['quality'] == 'warning' and job['pixel_quality']['passed']
