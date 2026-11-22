"""Whole-template poses retain the assembly and satisfy the final contract."""
import time
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image
import pytest

from src.imageConverterSample import refine, render_svg
from src.iCCModules.imageCompositeConverterSampleAlignment import align_sample, orient_assembly
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions


BODY = ('<rect id="frame" x="35" y="20" width="32" height="50" fill="#dddddd" stroke="#555555" stroke-width="2"/>'
        '<circle id="mark" cx="43" cy="30" r="4" fill="#333333"/>'
        '<polygon id="head" points="42,50 59,57 42,66" fill="#777777"/>')
SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="96" viewBox="0 0 120 96">'+BODY+'</svg>'
DESCRIPTION = 'Ein Rechteck, ein Kreis und ein Dreieck.'


def target_svg(angle, mirror_x=1, mirror_y=1, scale=1., dx=0., dy=0.):
    # Independent SVG transform, rather than the implementation's matrix helper.
    transform = (f'translate({60+dx} {48+dy}) rotate({angle}) '
                 f'scale({scale*mirror_x} {scale*mirror_y}) translate(-60 -48)')
    return SVG.replace(BODY, f'<g transform="{transform}">{BODY}</g>')


@pytest.mark.parametrize('angle,mx,my,scale,dx,dy', [
    (90, 1, 1, 1., 0., 0.), (180, 1, 1, 1., 0., 0.), (270, 1, 1, 1., 0., 0.),
    (0, -1, 1, 1., 0., 0.), (0, 1, -1, 1., 0., 0.),
    (37, 1, 1, .8, 5., -3.), (123, -1, 1, .9, -4., 2.),
])
def test_refine_fits_rotated_and_mirrored_samples(tmp_path, angle, mx, my, scale, dx, dy):
    source, sample, output = (tmp_path/name for name in ('source.png', 'sample.svg', 'result.svg'))
    target = render_svg(target_svg(angle, mx, my, scale, dx, dy), 120, 96)
    Image.fromarray(target).save(source)
    sample.write_text(SVG, encoding='utf-8')
    report = refine(source, sample, output, DESCRIPTION, 5, seed=17)
    assert report['passed'], report
    assert not report.get('restarted_from_description'), report
    assert report['alignment'] is not None
    result = output.read_text(encoding='utf-8')
    validate_svg_assertions(result, description_assertions(DESCRIPTION))
    original, fitted = ET.fromstring(SVG), ET.fromstring(result)
    for node in original:
        found = fitted.find(f'.//{{*}}*[@id="{node.get("id")}"]')
        assert found is not None and found.tag == node.tag
        assert found.attrib == node.attrib
    assert sample.read_text(encoding='utf-8') == SVG
    actual = render_svg(result, 120, 96)
    assert np.mean((actual.astype(float)-target)**2)/255**2 < .001


@pytest.mark.parametrize('viewport', [
    'viewBox="10 20 60 48"',
    'viewBox="10 20 60 60" preserveAspectRatio="xMaxYMin meet"',
    'viewBox="10 20 60 60" preserveAspectRatio="none"',
])
def test_pose_respects_nonzero_viewbox_aspect_and_root_transform(viewport):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="96" {viewport} transform="translate(2 1)">'
           '<rect x="25" y="35" width="10" height="16" fill="#555555"/></svg>')
    posed = ET.tostring(orient_assembly(ET.fromstring(svg), 120, 96, angle=180, mirrored=True), encoding='unicode')
    original = render_svg(svg, 120, 96)
    # A 180 degree turn after an x reflection equals a vertical reflection.
    actual = render_svg(posed, 120, 96)
    assert np.mean(abs(actual.astype(float)-original[::-1])) < .1
    assert np.array_equal(actual.mean(axis=2) < 150, original[::-1].mean(axis=2) < 150)


def test_directional_description_is_checked_after_orientation(tmp_path):
    # The original heads both point down. A half turn must be tried before
    # rejecting the template for a description that requires upward heads.
    body = ('<polygon points="15,20 35,20 25,40" fill="red"/>'
            '<polygon points="65,20 85,20 75,40" fill="blue"/>')
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60" viewBox="0 0 100 60">'+body+'</svg>'
    description = 'Zwei Dreiecke. Links ein blaues Dreieck mit Spitze nach oben. Rechts ein rotes Dreieck mit Spitze nach oben.'
    assertions = description_assertions(description)
    assert assertions.get('arrow_heads')
    with pytest.raises(ValueError):
        validate_svg_assertions(svg, assertions)
    target = svg.replace(body, '<g transform="translate(100 60) rotate(180)">'+body+'</g>')
    validate_svg_assertions(target, assertions)
    source, sample, output = (tmp_path/name for name in ('source.png', 'sample.svg', 'result.svg'))
    Image.fromarray(render_svg(target, 100, 60)).save(source)
    sample.write_text(svg, encoding='utf-8')
    report = refine(source, sample, output, description, 5, seed=17)
    assert report['passed'] and not report.get('restarted_from_description'), report
    validate_svg_assertions(output.read_text(encoding='utf-8'), assertions)


def test_arbitrarily_rotated_sample_can_meet_an_exact_horizontal_claim(tmp_path):
    body = ('<line x1="25" y1="25" x2="25" y2="60" stroke="red" stroke-width="3"/>'
            '<line x1="75" y1="10" x2="75" y2="45" stroke="blue" stroke-width="3"/>'
            '<polygon points="25,10 15,25 35,25" fill="red"/>'
            '<polygon points="75,60 65,45 85,45" fill="blue"/>'
            '<line x1="20" y1="70" x2="80" y2="70" stroke="red" stroke-width="3"/>')
    target = SVG.replace(BODY, body)
    sample_svg = target.replace(body, '<g transform="rotate(37 60 48)">'+body+'</g>')
    description = ('Zwei vertikale Linien und zwei Dreiecke. Links Spitze nach oben, '
                   'rechts Spitze nach unten. Unteres Drittel rote horizontale Linie.')
    assertions = description_assertions(description)
    assert assertions.get('horizontal_bar') == 'red'
    validate_svg_assertions(target, assertions)
    source, sample, output = (tmp_path/name for name in ('source.png', 'sample.svg', 'result.svg'))
    Image.fromarray(render_svg(target, 120, 96)).save(source)
    sample.write_text(sample_svg, encoding='utf-8')
    report = refine(source, sample, output, description, 5, seed=17)
    assert report['passed'] and not report.get('restarted_from_description'), report
    validate_svg_assertions(output.read_text(encoding='utf-8'), assertions)


def test_mirrored_colors_are_not_calibrated_at_the_wrong_positions(tmp_path):
    svg = SVG.replace('#dddddd', '#bacde1').replace('#333333', '#b72435').replace('#777777', '#26704d')
    root = ET.fromstring(svg)
    target = ET.Element(root.tag, root.attrib)
    group = ET.SubElement(target, '{http://www.w3.org/2000/svg}g', transform='translate(120 0) scale(-1 1)')
    group.extend(list(root))
    source, sample, output = (tmp_path/name for name in ('source.png', 'sample.svg', 'result.svg'))
    Image.fromarray(render_svg(ET.tostring(target, encoding='unicode'), 120, 96)).save(source)
    sample.write_text(svg, encoding='utf-8')
    report = refine(source, sample, output, DESCRIPTION, 5, seed=17)
    assert report['passed'] and report['final_mse'] < .0001, report


@pytest.mark.parametrize('angle', [90, 37])
def test_white_canvas_backing_stays_on_canvas_during_rotation(tmp_path, angle):
    backdrop = '<rect id="background" width="120" height="96" fill="white"/>'
    sample_svg = SVG.replace(BODY, backdrop+BODY)
    target = target_svg(angle, scale=.8, dx=3., dy=-2.)
    source, sample, output = (tmp_path/name for name in ('source.png', 'sample.svg', 'result.svg'))
    Image.fromarray(render_svg(target, 120, 96)).save(source)
    sample.write_text(sample_svg, encoding='utf-8')
    report = refine(source, sample, output, DESCRIPTION, 5, seed=17)
    assert report['passed'] and not report.get('restarted_from_description'), report
    assert report['final_mse'] < .001
    result = ET.fromstring(output.read_text(encoding='utf-8'))
    assert result.find('{*}rect[@id="background"]') is not None


@pytest.mark.per_test_timeout(70, fail_on_timeout=True)
def test_gui_worker_fits_mirrored_rotated_template(tmp_path, monkeypatch):
    from src import imageConverterGui as gui
    import io
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    try:
        buffer = io.BytesIO()
        Image.fromarray(render_svg(target_svg(123, -1, 1, .9, -4., 2.), 120, 96)).save(buffer, 'PNG')
        uploaded = jobs.upload('oriented-template.png', buffer.getvalue())
        jobs.attach_sample(uploaded['id'], 'template.svg', SVG.encode())
        started = jobs.start(uploaded['id'], DESCRIPTION, 'quick', seed='17')
        jobs.threads[-1].join(timeout=60)
        result = jobs.snapshot(started['id'])
        assert result['status'] == 'done' and result['quality'] == 'passed', result
        assert not result['sample_report'].get('restarted_from_description')
        assert result['sample_report']['alignment']['mirrored']
        assert result['project_save']['status'] == 'saved'
    finally:
        jobs.close()


def test_pixel_perfect_wrong_direction_never_passes_description():
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60" viewBox="0 0 100 60">'
           '<polygon points="15,20 35,20 25,40" fill="red"/>'
           '<polygon points="65,20 85,20 75,40" fill="blue"/></svg>')
    assertions = description_assertions('Zwei Dreiecke. Links ein rotes Dreieck mit Spitze nach oben. '
                                      'Rechts ein blaues Dreieck mit Spitze nach oben.')
    target = render_svg(svg, 100, 60)
    result = align_sample(ET.fromstring(svg), target, render_svg, initial=target,
                          assertions=assertions, deadline=time.monotonic()+3, seed=17)
    validate_svg_assertions(result['svg'], assertions)
    assert not pixel_quality(target, result['rendered'])['passed']


@pytest.mark.parametrize('bar', [
    '<g transform="rotate(90)"><line y2="20" stroke="red"/></g>',
    '<g transform="rotate(90)"><rect width="1" height="20" fill="red"/></g>',
    '<g transform="scale(-1 1)"><rect width="20" height="1" fill="red"/></g>',
    '<g transform="rotate(37)"><g transform="rotate(-37)"><line x2="20" stroke="red"/></g></g>',
])
def test_horizontal_bar_contract_uses_displayed_direction(bar):
    validate_svg_assertions('<svg>'+bar+'</svg>', {'horizontal_bar': 'red'})


@pytest.mark.parametrize('angle,mirrored,direction,accepted', [
    (0, False, 'links', True), (0, True, 'rechts', True),
    (0, True, 'links', False), (90, False, 'links', False),
    (180, False, 'rechts', True), (180, True, 'links', True),
])
def test_disk_arrow_contract_uses_displayed_direction(angle, mirrored, direction, accepted):
    from pathlib import Path
    from src.iCCModules.imageCompositeConverterDiskArrow import validate_disk_arrow
    root = ET.parse(Path(__file__).resolve().parents[1]/'artifacts/evaluation/disk_arrow_recheck_v1/independent.svg').getroot()
    posed = orient_assembly(root, 96, 84, angle=angle, mirrored=mirrored)
    assert validate_disk_arrow(posed, direction) == accepted
