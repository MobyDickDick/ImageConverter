"""Real workers retain useful vectors when the description language is incomplete."""
import io
import json
import time
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image
import pytest

from src import imageConverterGui as gui
from src.imageConverterDraft import draft, region_svg
from src.imageConverterSample import prepare_sample, render_svg


@pytest.fixture
def jobs(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    store = gui.Jobs(tmp_path/'jobs')
    store.project_directory = tmp_path/'project'
    yield store
    store.close()


def upload(jobs, image=None):
    if image is None:
        image = np.full((24, 32, 3), 255, dtype=np.uint8)
        image[5:19, 8:24] = [40, 80, 120]
        image[9:15, 12:20] = 255
        image[2, 2:16] = 0
    stream = io.BytesIO()
    Image.fromarray(image).save(stream, format='PNG')
    result = jobs.upload('neutral.png', stream.getvalue())
    return jobs.jobs[result['id']], jobs.folder(result['id'])


def test_native_paths_preserve_holes_and_single_pixel_strokes():
    image = np.full((24, 32, 3), 255, dtype=np.uint8)
    image[5:19, 8:24] = [40, 80, 120]
    image[9:15, 12:20] = 255
    image[2, 2:16] = 0
    svg = prepare_sample(region_svg(image, 8).encode(), 32, 24)
    assert not any(n.tag.rsplit('}', 1)[-1] == 'image' for n in ET.fromstring(svg).iter())
    assert np.abs(render_svg(svg, 32, 24).astype(int)-image).max() <= 1


@pytest.mark.parametrize('description', ['Ein fremdartiges motorgetriebenes Symbol.', 'Ein Kreis mit Schrift "M".'])
def test_unknown_free_search_runs_real_worker_and_keeps_draft(jobs, description):
    job, folder = upload(jobs)
    started = jobs.start(job['id'], description, 'explore5', use_current_svg=False)
    jobs.threads[-1].join(timeout=25)
    result = jobs.snapshot(started['id'])
    assert result['status'] == 'done', result
    assert result['result'] and result['export_available']
    assert result['quality'] == 'warning' and result['image_driven_draft']
    assert result['conversion_policy'] == 'description_guided_v1'
    assert result['pixel_quality']['passed']
    assert not jobs.project_svg(result).exists()  # unconfirmed drafts do not replace project geometry
    assert json.loads((folder/'image-draft.json').read_text())['evaluations'] > 0
    restored = gui.Jobs(jobs.directory)
    try:
        assert restored.snapshot(result['id'])['export_available']
    finally:
        restored.close()


def test_normal_profile_falls_back_after_description_model_produces_nothing(jobs, monkeypatch):
    job, folder = upload(jobs)
    original = gui.subprocess.Popen
    commands = []
    class EmptyModel:
        returncode = 1
        def wait(self, timeout):
            assert 0 < timeout <= gui.PROFILES['quick'][1] - 9
    def launch(command, **kwargs):
        commands.append(command)
        if 'src.imageCompositeConverter' in command:
            return EmptyModel()
        return original(command, **kwargs)
    monkeypatch.setattr(gui.subprocess, 'Popen', launch)
    started = jobs.start(job['id'], 'Ein unbekanntes Symbol.', 'quick', use_current_svg=False)
    jobs.threads[-1].join(timeout=25)
    result = jobs.snapshot(started['id'])
    assert result['status'] == 'done' and result['result'], result
    assert len(commands) == 2 and 'src.imageConverterDraft' in commands[-1]
    assert result['quality'] == 'warning' and result['image_driven_draft']


@pytest.mark.parametrize('collector', ['normal', 'sample', 'preview'])
def test_description_mismatch_is_a_draft_in_guided_mode(jobs, collector):
    job, folder = upload(jobs)
    job.update(description='Zwei Kreise.', conversion_policy='description_guided_v1')
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24"><rect x="8" y="5" width="16" height="14" fill="#285078"/></svg>'
    relative = {'normal':'output/converted_svgs/UPLOAD.svg', 'sample':'output/refined.svg', 'preview':'live-preview.svg'}[collector]
    path = folder/relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)
    if collector == 'sample':
        path.with_suffix('.json').write_text(json.dumps(dict(passed=True, result=True)))
        gui.collect_sample_result(folder, job, 0)
    elif collector == 'normal':
        gui.collect_result(folder, job, 0)
    else:
        gui.retain_best_preview(folder, job)
    assert job['result'] and job['quality'] == 'warning', job
    assert job['description_error']
    assert (folder/'result.svg').is_file()


def test_expired_draft_does_not_overwrite_an_existing_vector(jobs):
    _, folder = upload(jobs)
    output = folder/'image-draft.svg'
    output.write_text('existing')
    report = draft(folder/'source.png', output, deadline=time.time()-1)
    assert report['evaluations'] == 0 and report['stop_reason'] == 'time_limit'
    assert output.read_text() == 'existing'


def test_guided_preview_prefers_existing_description_matching_geometry(jobs):
    job, folder = upload(jobs)
    job.update(description='Ein Kreis.', conversion_policy='description_guided_v1', result=True, quality='warning')
    (folder/'result.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24"><circle cx="16" cy="12" r="7" fill="#285078"/></svg>')
    with Image.open(folder/'source.png') as image:
        (folder/'live-preview.svg').write_text(region_svg(np.asarray(image.convert('RGB')), 8))
    gui.retain_best_preview(folder, job)
    assert any(n.tag.rsplit('}', 1)[-1] == 'circle' for n in ET.parse(folder/'result.svg').getroot().iter())
    assert not job.get('retained_preview')


@pytest.mark.parametrize('profile', ['quick', 'explore5'])
def test_reported_motor_valve_gets_visible_native_draft(jobs, monkeypatch, profile):
    from src.iCCModules.imageCompositeConverterDescriptions import loadCatalogDescriptionMappingImpl
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: loadCatalogDescriptionMappingImpl(gui.ROOT))
    job = jobs.upload('AC0211_L.jpg', (gui.ROOT/'artifacts/images_to_convert/AC0211_L.jpg').read_bytes())
    description = ('Die Form ist wie AC0201_M.jpg .\n'
        'Es ist ein motorgetriebenes Zweiwegventil. Die beiden Ventile sind horizontal angeordnet. '
        'Der Motor ist als Kelle mit Griff nach unten realisiert. Im Kreis der Kelle steht "M". '
        'Bei den Ventilen werden die beiden Formen zusammengehängt und ein Farbübergang gezeichnet.')
    started = jobs.start(job['id'], description, profile, use_current_svg=False)
    jobs.threads[-1].join(timeout=60)
    result = jobs.snapshot(started['id'])
    assert result['status'] == 'done' and result['result'], result
    assert result['quality'] == 'warning'
    assert result['pixel_quality']['foreground_iou'] >= .95
    # Persist reviewable CI evidence outside pytest's temporary data tree.
    evidence = gui.ROOT/'.tmp/description-guided-evidence'/profile
    evidence.mkdir(parents=True, exist_ok=True)
    import shutil
    folder = jobs.folder(result['id'])
    for source, target in [('source.png','original.png'), ('result.svg','draft.svg'), ('image-draft.json','metrics.json')]:
        shutil.copyfile(folder/source, evidence/target)
    (evidence/'job.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')


def test_unknown_reference_does_not_block_manual_conversion(jobs):
    job, _ = upload(jobs)
    description = 'Die Form ist wie AC9999.jpg. Ein unbekanntes Symbol.'
    started = jobs.start(job['id'], description, 'quick', use_current_svg=False)
    jobs.threads[-1].join(timeout=25)
    result = jobs.snapshot(started['id'])
    assert result['status'] == 'done' and result['result'], result
    assert result['description'] == description
    assert result['description_resolution_error']
    assert result['image_driven_draft'] and result['quality'] == 'warning'


def test_unknown_reference_keeps_background_release_policy(jobs):
    job, _ = upload(jobs)
    with pytest.raises(gui.RequestError):
        jobs.start(job['id'], 'Die Form ist wie AC9999.jpg.', 'quick', background=True)
