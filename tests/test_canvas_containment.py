"""Contain actual painted geometry, rather than hiding overflow in raster crops."""
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image
import pytest

from src.iCCModules.imageCompositeConverterCanvas import contain_svg, painted_bounds, within_canvas
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.imageConverterSample import render_svg


PUMP = ('<svg xmlns="http://www.w3.org/2000/svg" width="31" height="31" viewBox="0 0 31 31">'
        '<ellipse id="pump_circle" cx="15.784" cy="15.061" rx="14.873" ry="14.873" '
        'fill="#4fab61" stroke="#719675" stroke-width="0.892"/>'
        '<polygon id="pump_triangle" points="26.5,6.5 15.5,29.5 4.5,7.5" fill="#e0e8e1"/></svg>')


def scene(body, width=31, height=31, extra=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" {extra}>{body}</svg>'


def test_reported_pump_stroke_is_fitted_inside_original_canvas_without_cutting():
    assert not within_canvas(PUMP)
    result = contain_svg(PUMP)
    root = ET.fromstring(result)
    assert (root.get('width'), root.get('height'), root.get('viewBox')) == ('31', '31', '0 0 31 31')
    group = root.find('{*}g')
    values = group.get('transform').removeprefix('matrix(').removesuffix(')').split()
    sx, _, _, sy, tx, ty = map(float, values)
    assert sx == sy and 0 < sx <= 1
    circle = root.find('.//{*}ellipse')
    # Independent analytic bounds include half the stroke, not just the circle.
    cx, cy, radius, stroke = [float(circle.get(k)) for k in ('cx', 'cy', 'rx', 'stroke-width')]
    assert 0 <= sx*(cx-radius-stroke/2)+tx < sx*(cx+radius+stroke/2)+tx <= 31
    assert 0 <= sy*(cy-radius-stroke/2)+ty < sy*(cy+radius+stroke/2)+ty <= 31
    assert [node.get('id') for node in root.iter() if node.get('id')] == ['pump_circle', 'pump_triangle']
    validate_svg_assertions(result, description_assertions('Ein Kreis und ein Dreieck.'))
    assert within_canvas(result) and contain_svg(result) == result


@pytest.mark.parametrize('body', [
    '<circle cx="15" cy="15" r="16" fill="green" stroke="gray" stroke-width="2"/>',
    '<g transform="translate(-8 12) rotate(25)"><rect width="40" height="12" stroke="black" stroke-width="4"/></g>',
    '<path d="M-10 -5 C-30 60 70 -30 40 45" fill="none" stroke="black" stroke-width="3"/>',
    '<line x1="-20" y1="-20" x2="40" y2="40" stroke="blue" stroke-width="5" stroke-linecap="round"/>',
    '<text x="-5" y="36" font-size="18">Motor</text>',
    '<rect x="-10" y="-10" width="50" height="50" fill="white"/>',
])
def test_fills_curves_text_transforms_and_strokes_are_contained(body):
    original = scene(body)
    assert not within_canvas(original)
    bounded = contain_svg(original)
    assert within_canvas(bounded), painted_bounds(bounded)
    assert contain_svg(bounded) == bounded
    assert ET.fromstring(bounded).get('width') == '31'


@pytest.mark.parametrize('aspect', ['none', 'xMidYMid meet', 'xMaxYMin slice'])
def test_nonzero_viewbox_and_aspect_ratio_mapping(aspect):
    original = scene('<circle cx="8" cy="22" r="20" stroke="black" stroke-width="2"/>',
                     width=60, height=31, extra=f'viewBox="10 20 80 60" preserveAspectRatio="{aspect}"')
    bounded = contain_svg(original, 60, 31)
    assert within_canvas(bounded, 60, 31), painted_bounds(bounded, 60, 31)
    assert ET.fromstring(bounded).get('viewBox') == '10 20 80 60'


def test_in_bounds_content_is_unchanged_and_deliberate_clipping_is_preserved():
    original = scene('<circle cx="15" cy="15" r="10"/>')
    bounded = ET.fromstring(contain_svg(original))
    assert bounded.get('overflow') == 'hidden'
    assert list(bounded)[0].attrib == list(ET.fromstring(original))[0].attrib
    from tools.evaluate_svg_text_baseline import find_librsvg
    try:
        find_librsvg()
    except FileNotFoundError:
        pytest.skip('independent SVG clip renderer not installed')
    clipped = scene('<defs><clipPath id="crop"><rect width="31" height="31"/></clipPath></defs>'
                    '<g clip-path="url(#crop)"><line x1="-100" y1="15" x2="200" y2="15" '
                    'stroke="red" stroke-width="2"/></g>')
    assert within_canvas(clipped) and within_canvas(contain_svg(clipped))
    assert ET.fromstring(contain_svg(clipped)).find('{*}g').get('transform') is None


@pytest.mark.parametrize('size', [230, 410, 600])
def test_exact_canvas_background_and_flat_band_caps_are_not_shrunk(size):
    # Conservative display-list bounds reserve a large measurement viewport
    # for thick joins. Fractional raster zoom used to invent outside ink even
    # though all horizontal butt caps and the backing end exactly at the edge.
    original = scene(f'<rect width="{size}" height="{size}" fill="white"/>'
        f'<polyline points="0,20 20,20 {size-20},{size-20} {size},{size-20}" '
        'fill="none" stroke="#e6e6e6" stroke-width="20"/>', width=size,height=size)
    assert painted_bounds(original)==(0.,0.,float(size),float(size))
    assert within_canvas(original)
    bounded=ET.fromstring(contain_svg(original))
    assert bounded.find('{*}g') is None
    assert len(list(bounded))==2


def test_preview_journal_and_saved_artifacts_use_the_bounded_vector(tmp_path):
    from src.imageConverterPreview import PreviewPublisher, AttemptJournal
    from src.iCCModules.imageCompositeConverterIterationArtifacts import writeAttemptArtifactsImpl
    import cv2
    pixels = render_svg(PUMP, 31, 31)
    source, output = tmp_path/'source.png', tmp_path/'preview.svg'
    Image.fromarray(pixels).save(source)
    publisher = PreviewPublisher(source, output, description='Ein Kreis und ein Dreieck.')
    try:
        publisher.consider(PUMP, pixels, bgr=False)
        assert within_canvas(output.read_text())
        assert within_canvas(AttemptJournal(tmp_path).read(1)['svg'])
    finally:
        publisher.close()
    writeAttemptArtifactsImpl(svg_out_dir=str(tmp_path), diff_out_dir=str(tmp_path),
        base_name='result', svg_content=PUMP, target_img=pixels[:, :, ::-1],
        render_svg_to_numpy_fn=lambda svg: render_svg(svg, 31, 31)[:, :, ::-1],
        create_diff_image_fn=lambda a,b: cv2.absdiff(a,b), cv2_module=cv2, create_commented_diff=False)
    saved = (tmp_path/'result.svg').read_text()
    assert within_canvas(saved)
    np.testing.assert_array_equal(render_svg(saved, 31, 31), pixels)


def test_supersampling_keeps_the_original_svg_canvas():
    import fitz
    bounded = contain_svg(PUMP)
    with fitz.open('svg', bounded.encode()) as doc:
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False)
    expected = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
    # The production renderer composites premultiplied alpha onto white;
    # MuPDF's opaque output rounds antialiasing values by up to one level.
    np.testing.assert_allclose(render_svg(PUMP, 124, 124), expected, atol=1, rtol=0)


def test_model_validation_binds_the_bounded_svg_not_the_overflowing_candidate():
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search, svg_identity, raster_identity
    from src.iCCModules.imageCompositeConverterSearchPortfolio import validated_result
    image = render_svg(PUMP, 31, 31)[:, :, ::-1].copy()
    session = ImageSearch(SearchPolicy())
    session.description_assertions = description_assertions('Ein Kreis und ein Dreieck.')
    result = dict(svg=PUMP, rendered=image)
    with image_search(session):
        assert validated_result(result, image)
    assert within_canvas(result['svg'])
    assert (svg_identity(result['svg']), raster_identity(image)) in session.validated
    assert (svg_identity(PUMP), raster_identity(image)) not in session.validated


def test_project_export_replaces_an_older_overflowing_result(tmp_path, monkeypatch):
    import io
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    try:
        buffer = io.BytesIO()
        Image.fromarray(render_svg(PUMP, 31, 31)).save(buffer, format='PNG')
        uploaded = jobs.upload('neutral.png', buffer.getvalue())
        job = jobs.jobs[uploaded['id']]
        job.update(status='done', result=True, quality='passed', description='Ein Kreis und ein Dreieck.')
        folder = jobs.folder(job['id'])
        (folder/'result.svg').write_text(contain_svg(PUMP))
        target = jobs.project_svg(job)
        target.parent.mkdir(parents=True)
        target.write_text(PUMP)
        old = gui.saved_svg_quality(folder/'source.png', target)
        assert not old['within_canvas'] and not old['passed']
        jobs.publish_best(job['id'])
        assert job['project_save']['status'] == 'saved'
        assert within_canvas(target.read_text())
        assert any(path.read_text() == PUMP for path in (jobs.project_directory/'gui_history').rglob('*.svg'))
    finally:
        jobs.close()
