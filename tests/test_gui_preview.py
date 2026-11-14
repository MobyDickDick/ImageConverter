"""Live candidates are observable without changing conversion acceptance."""
import io

import numpy as np
from PIL import Image

from src import imageConverterGui as gui
from src import imageConverterPreview as preview
from src.imageConverterSample import render_svg

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24">'
       '<rect x="5" y="4" width="12" height="16" fill="#225599"/></svg>')


def test_publishes_only_improving_native_candidates(tmp_path):
    target = render_svg(SVG, 32, 24)
    source, output = tmp_path/'source.png', tmp_path/'preview.svg'
    Image.fromarray(target).save(source)
    publisher = preview.PreviewPublisher(source, output)
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


def test_sample_renderer_publishes_without_a_second_render(tmp_path, monkeypatch):
    source, output = tmp_path/'source.png', tmp_path/'live-preview.svg'
    Image.fromarray(render_svg(SVG, 32, 24)).save(source)
    monkeypatch.setenv('ICC_GUI_PREVIEW_SOURCE', str(source))
    monkeypatch.setenv('ICC_GUI_PREVIEW_OUTPUT', str(output))
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
        assert jobs.preview_file(job['id']).name == 'recovery.svg'
    finally:
        jobs.close()
