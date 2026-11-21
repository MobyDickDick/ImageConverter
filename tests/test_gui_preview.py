"""Live candidates are observable without changing conversion acceptance."""
import io
from pathlib import Path
import shutil

import numpy as np
import pytest
from PIL import Image

from src import imageConverterGui as gui
from src import imageConverterPreview as preview
from src.imageConverterSample import render_svg

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24" overflow="hidden">'
       '<rect x="5" y="4" width="12" height="16" fill="#225599"/></svg>')


@pytest.fixture(autouse=True)
def close_preview_journal():
    yield
    if preview._publisher is not None:
        preview._publisher.close()


def test_persistent_journal_commits_every_record_before_restart(tmp_path):
    writer = preview.AttemptJournal(tmp_path,persistent=True)
    try:
        for number in range(4):
            writer.append(SVG,float(number))
            reader = preview.AttemptJournal(tmp_path)
            assert reader.count == number+1
            assert reader.read(number+1)['mse'] == number/255**2
        assert reader.best()['mse'] == 0
    finally:
        writer.close()
    preview.AttemptJournal(tmp_path).append(SVG,255**2)
    assert preview.AttemptJournal(tmp_path).count == 5


def test_publishes_only_improving_native_candidates(tmp_path):
    target = render_svg(SVG, 32, 24)
    source, output = tmp_path/'source.png', tmp_path/'preview.svg'
    Image.fromarray(target).save(source)
    publisher = preview.PreviewPublisher(source, output, description='Ein Rechteck.')
    publisher.consider(SVG, np.full_like(target, 255))
    assert not output.exists()  # Empty search seed.
    publisher.consider('<svg><image href="source.png"/></svg>', target, bgr=False)
    assert not output.exists()  # Embedded original is not a vector preview.
    publisher.consider(SVG, target[:, :, ::-1])
    assert output.read_text(encoding='utf-8') == SVG
    revision = output.stat().st_mtime_ns
    publisher.consider(SVG.replace('#225599', '#ff0000'), np.zeros_like(target))
    publisher.consider(SVG, target, bgr=False)  # Duplicate candidates do not refresh.
    publisher.consider(SVG, target[:12], bgr=False)  # Ignore subregion renders.
    assert output.stat().st_mtime_ns == revision
    journal = preview.AttemptJournal(tmp_path)
    assert journal.count == 4  # Blank, best, worse, duplicate; no raster/subregion.
    assert [item['number'] for item in journal.page(after=1, limit=2)['attempts']] == [2, 3]
    assert journal.read(3)['mse'] > journal.read(2)['mse']
    assert journal.read(3)['svg'] == SVG.replace('#225599', '#ff0000')
    assert journal.read(4)['svg'] == SVG
    assert all('svg' not in item for item in journal.page()['attempts'])
    publisher.close()


def test_attempt_journal_continues_after_worker_restart_and_partial_write(tmp_path, monkeypatch):
    journal = preview.AttemptJournal(tmp_path)
    monkeypatch.setenv('ICC_GUI_PREVIEW_PHASE', 'Suche')
    journal.append(SVG, 0)
    with journal.records.open('ab') as stream:
        stream.write(b'{"svg":"interrupted')
    with journal.index.open('ab') as stream:
        stream.write(b'\x01\x02')
    assert journal.count == 1
    journal = preview.AttemptJournal(tmp_path)
    monkeypatch.setenv('ICC_GUI_PREVIEW_PHASE', 'Vektoraufbau')
    journal.append(SVG, 255**2)
    assert journal.count == 2
    assert journal.read(1)['phase'] == 'Suche'
    assert journal.read(2) == dict(number=2, svg=SVG, mse=1, phase='Vektoraufbau')


def test_sample_renderer_publishes_without_a_second_render(tmp_path, monkeypatch):
    source, output = tmp_path/'source.png', tmp_path/'live-preview.svg'
    Image.fromarray(render_svg(SVG, 32, 24)).save(source)
    monkeypatch.setenv('ICC_GUI_PREVIEW_SOURCE', str(source))
    monkeypatch.setenv('ICC_GUI_PREVIEW_OUTPUT', str(output))
    description = tmp_path/'description.txt'
    description.write_text('Ein Rechteck.', encoding='utf-8')
    monkeypatch.setenv('ICC_GUI_PREVIEW_DESCRIPTION_FILE', str(description))
    rendered = render_svg(SVG, 32, 24)
    assert rendered.shape == (24, 32, 3)
    assert output.read_text(encoding='utf-8') == SVG
    # Preview I/O failures must leave conversion usable.
    monkeypatch.setenv('ICC_GUI_PREVIEW_OUTPUT', str(source/'invalid.svg'))
    assert np.array_equal(render_svg(SVG, 32, 24), rendered)


def test_primary_preview_is_exposed_before_recovery(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    buffer = io.BytesIO()
    Image.fromarray(render_svg(SVG, 32, 24)).save(buffer, format='PNG')
    try:
        job = jobs.upload('preview.png', buffer.getvalue())
        folder = jobs.folder(job['id'])
        (folder/'live-preview.svg').write_text(SVG)
        snapshot = jobs.snapshot(job['id'])
        assert snapshot['preview'] and snapshot['preview_revision']
        assert jobs.preview_file(job['id']).name == 'live-preview.svg'
        (folder/'recovery.svg').write_text(SVG)
        assert jobs.preview_file(job['id']).name == 'live-preview.svg'
        (folder/'live-preview.svg').unlink()
        assert jobs.preview_file(job['id']).name == 'recovery.svg'
    finally:
        jobs.close()


def test_recovery_publisher_does_not_reset_previous_phase_best(tmp_path):
    source, output = tmp_path/'source.png', tmp_path/'live-preview.svg'
    target = render_svg(SVG,32,24)
    Image.fromarray(target).save(source)
    first = preview.PreviewPublisher(source,output,description='Ein Rechteck.')
    first.consider(SVG,target,bgr=False)
    first.close()
    worse = SVG.replace('#225599','#ff0000')
    restarted = preview.PreviewPublisher(source,output,description='Ein Rechteck.')
    restarted.consider(worse,render_svg(worse,32,24),bgr=False)
    assert output.read_text(encoding='utf-8') == SVG
    assert preview.AttemptJournal(tmp_path).count == 2
    restarted.close()


def test_better_contours_cannot_publish_an_unverified_inventory(tmp_path):
    fixture = Path(__file__).parent/'fixtures/sample_contrast'
    source, output = tmp_path/'source.png', tmp_path/'live-preview.svg'
    shutil.copyfile(fixture/'source.png', source)
    simpler = (fixture/'faded.svg').read_text()
    fragmented = (fixture/'without_template.svg').read_text()
    publisher = preview.PreviewPublisher(source, output,
        description=(fixture/'description.txt').read_text(encoding='utf-8'))
    target = np.array(Image.open(source).convert('RGB'))
    h, w = target.shape[:2]
    a, b = render_svg(fragmented, w, h), render_svg(simpler, w, h)
    assert np.square(target.astype(float)-a).mean() < np.square(target.astype(float)-b).mean()
    publisher.consider(fragmented, a, bgr=False)
    publisher.consider(simpler, b, bgr=False)
    publisher.close()
    assert not output.exists()
    assert preview.AttemptJournal(tmp_path).count == 2  # diagnostic evidence is kept


def test_preview_prefers_one_native_form_and_checks_description(tmp_path):
    target = render_svg(SVG, 32, 24)
    source, output = tmp_path/'source.png', tmp_path/'live-preview.svg'
    Image.fromarray(target).save(source)
    body = '<rect x="5" y="4" width="12" height="16" fill="#225599"/>'
    fragmented = SVG.replace(body, body*20)
    pixels = render_svg(fragmented, 32, 24)
    assert np.array_equal(target, pixels)
    publisher = preview.PreviewPublisher(source, output, description='Ein Rechteck.')
    assert publisher.rank(fragmented, pixels)[0] is True
    publisher.consider(fragmented, pixels, bgr=False)
    publisher.consider(SVG, target, bgr=False)
    assert output.read_text() == SVG
    assert preview.AttemptJournal(tmp_path).best()['svg'] == SVG
    publisher.close()


def test_final_selection_recovers_better_observation_lost_between_phases(tmp_path,monkeypatch):
    monkeypatch.setattr(gui,'catalog_descriptions',lambda:{})
    Image.fromarray(render_svg(SVG,32,24)).save(tmp_path/'source.png')
    worse = SVG.replace('width="12"','width="4"')
    for name in ('result.svg','recovery.svg','live-preview.svg'):
        (tmp_path/name).write_text(worse,encoding='utf-8')
    journal = preview.AttemptJournal(tmp_path)
    journal.append(SVG,0.)
    journal.append(worse,1000.)
    job = dict(width=32,height=24,description='Ein Rechteck. Keine Schriftzeichen.',result=True,quality='warning')
    gui.retain_best_preview(tmp_path,job)
    assert (tmp_path/'result.svg').read_text(encoding='utf-8') == SVG
    assert job['retained_preview'] and job['pixel_quality']['passed']
    assert job['quality'] == 'warning'  # A preview is not a model certification.


def test_best_observation_cannot_override_an_explicit_description_check(tmp_path,monkeypatch):
    monkeypatch.setattr(gui,'catalog_descriptions',lambda:{})
    contradicted = SVG.replace('</svg>','<text x="100" y="100">X</text></svg>')
    Image.fromarray(render_svg(SVG,32,24)).save(tmp_path/'source.png')
    (tmp_path/'result.svg').write_text(SVG,encoding='utf-8')
    preview.AttemptJournal(tmp_path).append(contradicted,0.)
    job = dict(width=32,height=24,description='Keine Schriftzeichen.',result=True,quality='passed')
    gui.retain_best_preview(tmp_path,job)
    assert (tmp_path/'result.svg').read_text(encoding='utf-8') == SVG
    assert job['quality'] == 'passed' and not job.get('retained_preview')


def test_reported_humidifier_cannot_publish_a_draft_with_missing_described_dashes(tmp_path,monkeypatch):
    monkeypatch.setattr(gui,'catalog_descriptions',lambda:{})
    fixture = Path(__file__).parent/'fixtures/gui_preview_selection'
    shutil.copyfile(fixture/'source.png',tmp_path/'source.png')
    for name in ('result.svg','recovery.svg','live-preview.svg'):
        shutil.copyfile(fixture/'late.svg',tmp_path/name)
    early = (fixture/'early.svg').read_text(encoding='utf-8')
    preview.AttemptJournal(tmp_path).append(early,0.0007040945578886426*255**2)
    job = dict(width=40,height=80,result=True,quality='warning',
               description=(fixture/'description.txt').read_text(encoding='utf-8'))
    gui.retain_best_preview(tmp_path,job)
    from xml.etree import ElementTree as ET
    expected = ET.parse(fixture/'late.svg').getroot()
    actual = ET.parse(tmp_path/'result.svg').getroot()
    def parts(root):
        return [(node.tag, node.attrib) for node in root.iter()
                if node.tag.rsplit('}', 1)[-1] not in {'svg', 'g'}]
    assert parts(actual) == parts(expected)
    assert actual.get('overflow') == 'hidden'
    assert not job.get('retained_preview')
    assert job['quality'] == 'warning'
