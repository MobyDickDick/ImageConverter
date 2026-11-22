"""A misplaced framed surface must not freeze an exposed backing strip."""
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image
import pytest

from src.imageConverterSample import prepare_sample, refine, render_svg
from src.iCCModules.imageCompositeConverterAdaptiveSearch import vector_quality_score

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT/'tests/fixtures/framed_panel_inset.svg'
DESCRIPTION = ('Liegendes graues Rechteck, graue Umrandung, drei graue vertikale Linien, '
               'vertikaler Farbverlauf des Rechtecks dunkel-hell-dunkel.')


@pytest.mark.parametrize('axis', ['x', 'y'])
def test_frame_edges_can_fit_without_moving_marks_or_changing_the_sample(tmp_path, axis):
    root = ET.fromstring(prepare_sample(SAMPLE.read_bytes(), 40, 20))
    rect = root.findall('{*}rect')[1]
    rect.set('y', '.5')
    rect.set('height', '19')
    target = ET.tostring(root, encoding='unicode')
    if axis == 'y':
        rect.set('y', '2.5')
        rect.set('height', '17')
    else:
        rect.set('x', '1.5')
        rect.set('width', '38')
    original = ET.tostring(root, encoding='unicode')
    source, sample, output = (tmp_path/n for n in ('input.png', 'sample.svg', 'output.svg'))
    Image.fromarray(render_svg(target, 40, 20)).save(source)
    sample.write_text(original, encoding='utf-8')
    report = refine(source, sample, output, DESCRIPTION, 3, seed=17)
    # Nearly neutral RGB paint is intentionally fitted as one gray coordinate.
    assert report['passed'] and report['final_mse'] < 1e-5, report
    assert report['final_mse'] < report['initial_mse']*.02
    assert report['alignment_search']['frame_adjustments'] > 0
    assert sample.read_text(encoding='utf-8') == original
    before = root.findall('{*}line')
    after = list(ET.parse(output).getroot().iter('{http://www.w3.org/2000/svg}line'))
    assert [n.attrib for n in before] == [n.attrib for n in after]


@pytest.mark.parametrize('transform', [
    'matrix(1 0 0 1 0 0)', 'matrix(1.25 0 0 1.25 2 1)',
])
def test_uniform_matrix_does_not_change_gradient_rendering(transform):
    root = ET.fromstring(prepare_sample(SAMPLE.read_bytes(), 40, 20))
    group = ET.Element('{http://www.w3.org/2000/svg}g', transform=transform)
    for child in list(root):
        if child.tag.rsplit('}', 1)[-1] != 'defs':
            root.remove(child)
            group.append(child)
    root.append(group)
    actual = render_svg(ET.tostring(root, encoding='unicode'), 40, 20)
    group.set('transform', 'translate(0 0) scale(1)' if transform.startswith('matrix(1 ') else
              'translate(2 1) scale(1.25)')
    expected = render_svg(ET.tostring(root, encoding='unicode'), 40, 20)
    assert np.array_equal(actual, expected)


def test_a_real_backing_strip_in_the_original_is_retained(tmp_path):
    source, output = tmp_path/'source.png', tmp_path/'result.svg'
    original = SAMPLE.read_bytes()
    Image.fromarray(render_svg(prepare_sample(original, 40, 20), 40, 20)).save(source)
    report = refine(source, SAMPLE, output, DESCRIPTION, 3, seed=17)
    assert report['passed'] and report['final_mse'] == 0
    frame = list(ET.parse(output).getroot().iter('{http://www.w3.org/2000/svg}rect'))[1]
    assert float(frame.get('y')) == 1.5
    assert SAMPLE.read_bytes() == original


def test_reported_jpeg_fits_frame_and_retains_passing_contours(tmp_path):
    output = tmp_path/'output.svg'
    report = refine(ROOT/'artifacts/images_to_convert/AC0512_S.jpg', SAMPLE, output,
                    DESCRIPTION, 5, seed=17)
    assert report['passed'] and report['improved'], report
    assert report['alignment_search']['frame_adjustments'] > 0
    assert report['final_mse'] < report['initial_mse']*.9
    assert vector_quality_score(report['final_quality']) < vector_quality_score(report['initial_quality'])
    frame = list(ET.parse(output).getroot().iter('{http://www.w3.org/2000/svg}rect'))[1]
    assert float(frame.get('y')) == .5 and float(frame.get('height')) == 19


@pytest.mark.per_test_timeout(70, fail_on_timeout=True)
def test_gui_worker_corrects_a_frame_in_an_uploaded_sample(tmp_path, monkeypatch):
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    try:
        upload = jobs.upload('panel.jpg', (ROOT/'artifacts/images_to_convert/AC0512_S.jpg').read_bytes())
        jobs.attach_sample(upload['id'], 'panel.svg', SAMPLE.read_bytes())
        started = jobs.start(upload['id'], DESCRIPTION, 'quick', seed='17')
        jobs.threads[-1].join(timeout=60)
        result = jobs.snapshot(started['id'])
        assert result['status'] == 'done' and result['quality'] == 'passed', result
        assert result['sample_report']['alignment_search']['frame_adjustments'] > 0
        assert result['project_save']['status'] == 'saved'
    finally:
        jobs.close()
