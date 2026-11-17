"""Scale uploaded assemblies together; retain small details and native geometry."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from PIL import Image
import pytest
import time

from src.imageConverterSample import prepare_sample, refine, render_svg
from tools.run_plan_b_variations import measure_quality


@pytest.mark.parametrize('before,after',[('#696969','#a9a9a9'),('#a9a9a9','#696969')])
def test_small_mark_color_follows_raster_in_either_direction(before,after):
    from src.iCCModules.imageCompositeConverterSampleAlignment import align_sample
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="80" viewBox="0 0 40 80">'
           '<rect x="1" y="1" width="38" height="78" fill="#eeeeee"/>'
           f'<rect id="mark" x="16" y="8" width="8" height="2" fill="{before}"/></svg>')
    target = render_svg(svg.replace(before,after),40,80)
    result = align_sample(ET.fromstring(svg),target,render_svg,deadline=time.monotonic()+5,
                          initial=render_svg(svg,40,80))
    assert result['error']<1e-8
    assert ET.fromstring(result['svg']).find('.//{*}rect[@id="mark"]').get('fill')==after

FIXTURES = Path(__file__).parent/'fixtures/sample_alignment'
GEOMETRY = {'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry',
            'width', 'height', 'd', 'points', 'opacity', 'fill-opacity', 'stroke-opacity'}


def assert_parts_preserved(sample, output, width, height):
    original = ET.fromstring(prepare_sample(sample, width, height))
    result = ET.fromstring(output)
    for old in original.iter():
        if old is original or not old.get('id'):
            continue
        found = [node for node in result.iter() if node.get('id') == old.get('id')]
        assert len(found) == 1
        if old.tag.rsplit('}', 1)[-1] == 'path' and found[0].tag.rsplit('}', 1)[-1] == 'line':
            from src.iCCModules.imageCompositeConverterRepresentation import path_points
            paths = path_points(old)
            assert len(paths) == 1 and len(paths[0][0]) == 2
            assert np.allclose(paths[0][0].ravel(), [float(found[0].get(k)) for k in ('x1', 'y1', 'x2', 'y2')])
        else:
            assert found[0].tag == old.tag
            assert {k: v for k, v in old.attrib.items() if k in GEOMETRY} == {
                k: v for k, v in found[0].attrib.items() if k in GEOMETRY}


def test_uploaded_crossed_panel_is_shrunk_without_losing_its_minus(tmp_path):
    output = tmp_path/'result.svg'
    sample = FIXTURES/'panel.svg'
    before = sample.read_bytes()
    report = refine(FIXTURES/'panel.png', sample, output,
                    (FIXTURES/'description.txt').read_text(encoding='utf-8'), 3)
    assert report['passed'], report
    assert report['stop_reason'] in {'sample_alignment_accepted', 'native_search_accepted'}
    assert report['final_mse'] < report['initial_mse']*.05
    assert .88 < report['alignment']['scale_x'] < .92
    assert .88 < report['alignment']['scale_y'] < .92
    assert_parts_preserved(before, output.read_text(encoding='utf-8'), 40, 80)
    assert sample.read_bytes() == before
    # The retained minus must actually be visible in its target location.
    raster = render_svg(output.read_text(encoding='utf-8'), 40, 80)
    assert np.min(raster[10:14, 16:24].mean(axis=2)) < 180
    from tools.evaluate_svg_text_baseline import render_librsvg
    source = cv2.imread(str(FIXTURES/'panel.png'))
    assert measure_quality(source, output.read_text(encoding='utf-8'), render_fn=render_librsvg)['satisfactory']


ASSEMBLY = ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="96" viewBox="0 0 64 96">'
            '<rect id="frame" x="8" y="8" width="48" height="80" fill="#dddddd" stroke="#888888" stroke-width="2"/>'
            '<path id="diagonal1" d="M 9,9 L 55,87" stroke="#888888" stroke-width="3"/>'
            '<path id="diagonal2" d="M 55,9 L 9,87" stroke="#888888" stroke-width="3"/>'
            '<rect id="minus" x="27" y="18" width="10" height="3" fill="#555555"/></svg>')


@pytest.mark.parametrize('scale,dx,dy', [(.5, 5., -2.), (.8, -3., 2.), (1.1, 1., -1.)])
@pytest.mark.parametrize('jpeg', [False, True])
def test_whole_assembly_fit_handles_scale_position_and_jpeg(tmp_path, scale, dx, dy, jpeg):
    root = ET.fromstring(ASSEMBLY)
    group = ET.Element('{http://www.w3.org/2000/svg}g',
                       transform=f'translate({dx} {dy}) translate(32 48) scale({scale}) translate(-32 -48)')
    for child in list(root):
        root.remove(child)
        group.append(child)
    root.append(group)
    target = render_svg(ET.tostring(root, encoding='unicode'), 64, 96)
    source, sample, output = (tmp_path/name for name in ('source.png', 'sample.svg', 'result.svg'))
    Image.fromarray(target).save(source, 'JPEG' if jpeg else 'PNG', quality=90)
    sample.write_text(ASSEMBLY, encoding='utf-8')
    report = refine(source, sample, output, 'Ein graues Rechteck mit Diagonalen und einem Minus.', 3)
    assert report['passed'], report
    assert abs(report['alignment']['scale_x']-scale) < .04
    assert abs(report['alignment']['scale_y']-scale) < .04
    assert_parts_preserved(sample.read_bytes(), output.read_text(encoding='utf-8'), 64, 96)


@pytest.mark.per_test_timeout(70, fail_on_timeout=True)
def test_gui_sample_conversion_uses_the_whole_assembly(tmp_path, monkeypatch):
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    manager = gui.Jobs(tmp_path/'jobs')
    manager.project_directory = tmp_path/'project'
    try:
        uploaded = manager.upload('neutral-panel.png', (FIXTURES/'panel.png').read_bytes())
        manager.attach_sample(uploaded['id'], 'sample.svg', (FIXTURES/'panel.svg').read_bytes())
        started = manager.start(uploaded['id'], (FIXTURES/'description.txt').read_text(encoding='utf-8'), 'quick')
        manager.threads[-1].join(timeout=60)
        result = manager.snapshot(started['id'])
        assert result['status'] == 'done' and result['quality'] == 'passed', result
        assert result['sample_report']['stop_reason'] in {'sample_alignment_accepted', 'native_search_accepted'}
        assert result['project_save']['status'] == 'saved'
        assert result['sample_report']['alignment'] is not None
    finally:
        manager.close()
