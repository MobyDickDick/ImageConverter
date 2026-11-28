"""Description hints may be incomplete; output must remain real geometry."""
import io
import json
import time
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image
import pytest

from src import imageConverterGui as gui
from src.imageConverterDraft import draft
from src.imageConverterSample import prepare_sample, render_svg
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterSimilarity import resolve_similarity_description
from src.iCCModules.imageCompositeConverterTwoWayValve import two_way_valve_spec


DESCRIPTION = ('Die Form ist wie AC0201_M.jpg .\n'
    'Es ist ein motorgetriebenes Zweiwegventil. Die beiden Ventile sind horizontal angeordnet. '
    'Der Motor ist als Kelle mit Griff nach unten realisiert. Im Kreis der Kelle steht "M". '
    'Bei den Ventilen werden die beiden Formen zusammengehängt und ein Farbübergang gezeichnet.')
PIXEL_COPY = ('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24">'
    '<g shape-rendering="crispEdges"><path fill="#555" d="'
    + ''.join(f'M1 {y}h20v1h-20z' for y in range(16)) + '"/></g></svg>')
NATIVE = ('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24">'
          '<circle cx="16" cy="12" r="7" fill="#285078"/></svg>')


@pytest.fixture
def jobs(tmp_path, monkeypatch):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    store = gui.Jobs(tmp_path/'jobs')
    store.project_directory = tmp_path/'project'
    yield store
    store.close()


def upload(jobs):
    stream = io.BytesIO()
    Image.fromarray(render_svg(NATIVE, 32, 24)).save(stream, format='PNG')
    result = jobs.upload('neutral.png', stream.getvalue())
    return jobs.jobs[result['id']], jobs.folder(result['id'])


def test_pixel_copy_is_rejected_after_export_loses_its_job_metadata():
    with pytest.raises(ValueError, match='Pixelkopien'):
        prepare_sample(PIXEL_COPY.encode(), 32, 24)
    assert '<circle' in prepare_sample(NATIVE.encode(), 32, 24)


def test_legacy_pixel_copies_are_not_previewed_exported_or_reused(jobs):
    job, folder = upload(jobs)
    for name in ('result.svg', 'live-preview.svg', 'sample.svg'):
        (folder/name).write_text(PIXEL_COPY)
    job.update(status='done', result=True, quality='warning', sample=True, sample_pending=True)
    jobs.save(job)
    restored = gui.Jobs(jobs.directory)
    try:
        result = restored.snapshot(job['id'])
        assert not result['result'] and result['result_rejection'] == 'pixel_trace'
        assert not result['export_available'] and not result.get('preview') and not result['sample']
        original = restored.jobs[job['id']]
        restored.use_best_svg(original)
        assert not original['sample']
        assert (folder/'result.svg').read_text() == PIXEL_COPY  # evidence retained, not silently erased
    finally:
        restored.close()


def test_old_pixel_copy_cannot_be_uploaded_as_a_sample(jobs):
    job, _ = upload(jobs)
    with pytest.raises(gui.RequestError, match='Pixelkopien'):
        jobs.attach_sample(job['id'], 'old.svg', PIXEL_COPY.encode())


@pytest.mark.parametrize('description', ['Ein unbekanntes Bauteil.', 'Die Form ist wie AC9999.jpg.'])
def test_unknown_description_finishes_without_manufacturing_pixel_geometry(jobs, description):
    job, folder = upload(jobs)
    started = jobs.start(job['id'], description, 'explore5', use_current_svg=False)
    jobs.threads[-1].join(timeout=25)
    result = jobs.snapshot(started['id'])
    assert result['status'] != 'running', result
    assert not jobs.busy()
    for candidate in folder.glob('*.svg'):
        prepare_sample(candidate.read_bytes(), result['width'], result['height'])
    if not result['result']:
        assert result['status'] == 'error' and 'geometrisch' in result['message']


@pytest.mark.parametrize('collector', ['normal', 'sample', 'preview'])
def test_description_mismatch_can_retain_an_actual_geometric_draft(jobs, collector):
    job, folder = upload(jobs)
    job.update(description='Zwei Kreise.', conversion_policy='description_guided_v1')
    relative = {'normal':'output/converted_svgs/UPLOAD.svg', 'sample':'output/refined.svg', 'preview':'live-preview.svg'}[collector]
    path = folder/relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(NATIVE)
    if collector == 'sample':
        path.with_suffix('.json').write_text(json.dumps(dict(passed=True, result=True)))
        gui.collect_sample_result(folder, job, 0)
    elif collector == 'normal':
        gui.collect_result(folder, job, 0)
    else:
        gui.retain_best_preview(folder, job)
    assert job['result'] and job['quality'] == 'warning' and job['description_error']
    assert '<circle' in (folder/'result.svg').read_text()


def test_expired_search_does_not_overwrite_an_existing_vector(jobs):
    _, folder = upload(jobs)
    output = folder/'geometric-draft.svg'
    output.write_text(NATIVE)
    report = draft(folder/'source.png', output, deadline=time.time()-1)
    assert not report['result'] and report['stop_reason'] == 'time_limit'
    assert output.read_text() == NATIVE


@pytest.mark.parametrize('profile,reuse', [('quick', False), ('explore5', False), ('quick', True)])
def test_reported_valve_has_circle_triangles_gradient_and_native_text(jobs, monkeypatch, profile, reuse):
    from src.iCCModules.imageCompositeConverterDescriptions import loadCatalogDescriptionMappingImpl
    catalog = loadCatalogDescriptionMappingImpl(gui.ROOT)
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: catalog)
    # Neutral filename prevents an image-ID shortcut from choosing the geometry.
    uploaded = jobs.upload('neutral-motor.jpg', (gui.ROOT/'artifacts/images_to_convert/AC0211_L.jpg').read_bytes())
    job, folder = jobs.jobs[uploaded['id']], jobs.folder(uploaded['id'])
    if reuse:
        (folder/'sample.svg').write_text(PIXEL_COPY)
        job.update(sample=True, sample_pending=True)
    started = jobs.start(job['id'], DESCRIPTION, profile, use_current_svg=reuse, seed=17)
    jobs.threads[-1].join(timeout=60)
    result = jobs.snapshot(started['id'])
    evidence = gui.ROOT/'.tmp/description-guided-evidence'/f'{profile}-{reuse}'
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence/'job.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    import shutil
    for path in folder.glob('*console.log'):
        shutil.copyfile(path, evidence/path.name)
    assert result['status'] == 'done' and result['result'], result
    svg = (folder/'result.svg').read_text()
    root = ET.fromstring(svg)
    tags = [node.tag.rsplit('}', 1)[-1] for node in root.iter()]
    assert tags.count('circle') == 1 and tags.count('line') == 1 and tags.count('path') == 2
    assert tags.count('text') == 1 and 'image' not in tags
    assert ''.join(root.itertext()).strip() == 'M'
    resolved = resolve_similarity_description(DESCRIPTION, catalog).text
    assert two_way_valve_spec(resolved)['label'] == 'M'
    validate_svg_assertions(svg, description_assertions(resolved))
    assert result['pixel_quality']['foreground_iou'] >= .85, result['pixel_quality']
    shutil.copyfile(folder/'source.png', evidence/'original.png')
    (evidence/'result.svg').write_text(svg)
    Image.fromarray(render_svg(svg, result['width']*4, result['height']*4)).save(evidence/'preview.png')
