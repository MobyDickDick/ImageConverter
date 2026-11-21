"""Reusable vectors must survive composition intact and still pass raster gates."""
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterSvgComponents as components
from src.imageConverterSample import render_svg


@pytest.fixture
def library(tmp_path, monkeypatch):
    monkeypatch.setattr(components, 'ROOT', tmp_path)
    folder = tmp_path/'artifacts/converted_images/converted_svgs'
    folder.mkdir(parents=True)
    (folder/'tube.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="100" viewBox="0 0 24 100">
      <defs><linearGradient id="paint"><stop stop-color="#a0a800"/><stop offset="1" stop-color="#308060"/></linearGradient></defs>
      <rect width="24" height="100" fill="url(#paint)"/>
      <rect width="24" height="5" fill="#999999"/>
      <rect y="95" width="24" height="5" fill="#999999"/></svg>''')
    (folder/'motor.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="44" height="28" viewBox="0 0 44 28">
      <defs><linearGradient id="paint"><stop stop-color="#f2f2f2"/><stop offset="1" stop-color="#eeeeee"/></linearGradient></defs>
      <line x1="0" y1="14" x2="18" y2="14" stroke="#808080" stroke-width="2"/>
      <circle cx="30" cy="14" r="12" fill="url(#paint)" stroke="#808080" stroke-width="2"/>
      <text x="30" y="21" text-anchor="middle" fill="#666666" font-family="Arial" font-weight="bold" font-size="19">M</text></svg>''')
    return tmp_path


MANUAL = 'SVG-Bauteil: tube.svg bei 0 0 skaliert 1\nSVG-Bauteil: motor.svg bei 24 36 skaliert 1'


def test_manual_assembly_preserves_gradients_text_and_colliding_ids(library):
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
    svg, references, count = components.compose_components(MANUAL, np.full((100, 70, 3), 255, np.uint8))
    validate_svg_assertions(svg, description_assertions(MANUAL))
    drawing = ET.fromstring(svg)
    ids = [n.get('id') for n in drawing.iter() if n.get('id')]
    assert len(set(ids)) == len(ids) == 4
    assert {n.get('fill') for n in drawing.iter() if n.get('fill', '').startswith('url')} == {
        'url(#component0_paint)', 'url(#component1_paint)'}
    assert [n.text for n in drawing.iter() if n.tag.endswith('}text')] == ['M']
    assert len(references) == 2 and count >= 1


def test_automatic_placement_passes_independent_pixel_gates(library):
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import vector_candidate_quality
    # Independent flat scene: no composition helper or generated wrappers.
    expected = '''<svg xmlns="http://www.w3.org/2000/svg" width="70" height="100">
      <defs><linearGradient id="tube"><stop stop-color="#a0a800"/><stop offset="1" stop-color="#308060"/></linearGradient>
      <linearGradient id="motor"><stop stop-color="#f2f2f2"/><stop offset="1" stop-color="#eeeeee"/></linearGradient></defs>
      <rect width="24" height="100" fill="url(#tube)"/>
      <rect width="24" height="5" fill="#999999"/><rect y="95" width="24" height="5" fill="#999999"/>
      <line x1="24" y1="50" x2="42" y2="50" stroke="#808080" stroke-width="2"/>
      <circle cx="54" cy="50" r="12" fill="url(#motor)" stroke="#808080" stroke-width="2"/>
      <text x="54" y="57" text-anchor="middle" fill="#666666" font-family="Arial" font-weight="bold" font-size="19">M</text></svg>'''
    target = components.render_components(expected, 70, 100)
    svg, references, count = components.compose_components(
        'SVG-Bauteil: tube.svg\nSVG-Bauteil: motor.svg', target, seconds=5.)
    actual = render_svg(svg, 70, 100)
    quality = vector_candidate_quality(target, actual, svg)
    assert quality['passed'], (references, quality)
    assert references[0]['placement'] == [0, 0, 1.]
    assert np.allclose(references[1]['placement'], [24, 36, 1.], atol=.1), references
    assert count >= 2


def test_automatic_placement_allows_empty_donor_margins_outside_canvas(library):
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import vector_candidate_quality
    folder = library/'artifacts/converted_images/converted_svgs'
    (folder/'padded.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg"
      width="45" height="40" viewBox="0 0 45 40">
      <rect x="20" y="12" width="12" height="16" fill="#6b8e23"
            stroke="#222222" stroke-width="2"/></svg>''')
    # Independently positioned paint fits, though the donor viewport cannot.
    expected = '''<svg xmlns="http://www.w3.org/2000/svg" width="26" height="30">
      <rect x="8" y="6" width="12" height="16" fill="#6b8e23"
            stroke="#222222" stroke-width="2"/></svg>'''
    target = components.render_components(expected, 26, 30)
    description = 'SVG-Bauteil: padded.svg'
    svg, references, _ = components.compose_components(description, target, seconds=5.)
    assert np.allclose(references[0]['placement'], [-12, -6, 1.]), references
    assert vector_candidate_quality(target, render_svg(svg, 26, 30), svg)['passed']
    components.validate_components(svg, description)
    manual = 'SVG-Bauteil: padded.svg bei -12 -6 skaliert 1'
    components.validate_components(svg, manual)
    # A stroke crossing the canvas is rejected even if most of the donor is empty.
    drawing = ET.fromstring(svg)
    drawing[0] = components.placed_component(components.load_component('padded.svg', 0), -20, -6, 1.)
    with pytest.raises(ValueError, match='Zeichenfläche'):
        components.validate_components(ET.tostring(drawing, encoding='unicode'), description)


def test_white_paint_is_part_of_component_bounds(library):
    folder = library/'artifacts/converted_images/converted_svgs'
    (folder/'white.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg"
      width="40" height="40" viewBox="0 0 40 40">
      <rect width="40" height="40" fill="white"/>
      <circle cx="20" cy="20" r="5" fill="black"/></svg>''')
    with pytest.raises(ValueError, match='Zeichenfläche'):
        components.compose_components('SVG-Bauteil: white.svg bei -10 -10 skaliert 1',
                                      np.full((20, 20, 3), 255, np.uint8))


@pytest.mark.parametrize('damage', ['missing', 'extra', 'paint', 'text', 'distort', 'move', 'root'])
def test_component_inventory_and_explicit_placement_cannot_be_bypassed(library, damage):
    svg, _, _ = components.compose_components(MANUAL, np.full((100, 70, 3), 255, np.uint8))
    root = ET.fromstring(svg)
    if damage == 'missing':
        root.remove(root[-1])
    elif damage == 'extra':
        ET.SubElement(root, '{'+components.NS+'}line', x1='0', x2='70')
    elif damage == 'paint':
        next(n for n in root.iter() if n.tag.endswith('}circle')).set('fill', 'white')
    elif damage == 'text':
        next(n for n in root.iter() if n.tag.endswith('}text')).text = ' M'
    elif damage == 'distort':
        root[-1].set('height', '20')
    elif damage == 'move':
        root[-1].set('x', '25')
    else:
        root.set('opacity', '0')
    with pytest.raises(ValueError):
        components.validate_components(ET.tostring(root, encoding='unicode'), MANUAL)


@pytest.mark.parametrize('text', ['SVG-Bauteil: ../tube.svg', 'SVG-Bauteil: https://host/tube.svg',
    'SVG-Bauteil: tube.svg bei 0 0 skaliert 0', 'SVG-Bauteil: tube.svg\nEin roter Kreis.'])
def test_invalid_directives_do_not_silently_drop_instructions(text):
    with pytest.raises(ValueError):
        components.parse_components(text)


def test_missing_source_and_active_svg_are_rejected(library):
    with pytest.raises(ValueError, match='gefunden'):
        components.load_component('unknown.svg', 0)
    (library/'artifacts/converted_images/converted_svgs/tube.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>')
    with pytest.raises(ValueError):
        components.load_component('tube.svg', 0)


def test_gui_collects_composition_and_rechecks_pixels(library):
    from src import imageConverterGui as gui
    from src.imageConverterComponents import convert
    from PIL import Image
    svg, _, _ = components.compose_components(MANUAL, np.full((100, 70, 3), 255, np.uint8))
    source = library/'source.png'
    Image.fromarray(render_svg(svg, 70, 100)).save(source)
    output = library/'output/refined.svg'
    convert(source, output, MANUAL, 2)
    job = dict(width=70, height=100, description=MANUAL)
    gui.collect_sample_result(library, job, 0)
    assert job['result'] and job['quality'] == 'passed', job
    # A changed raster invalidates a stale passing worker report.
    Image.new('RGB', (70, 100), '#ff0000').save(source)
    gui.collect_sample_result(library, job, 0)
    assert job['quality'] == 'warning'


def test_gui_starts_component_worker_with_current_svg_disabled(tmp_path, monkeypatch):
    import io
    from PIL import Image
    from src import imageConverterGui as gui
    description = ('SVG-Bauteil: AC0151_L.svg bei 0 0 skaliert 1\n'
                   'SVG-Bauteil: AC1000_L.svg bei 100 185 skaliert 1')
    svg, _, _ = components.compose_components(description, np.full((400, 190, 3), 255, np.uint8))
    stream = io.BytesIO()
    Image.fromarray(render_svg(svg, 190, 400)).save(stream, format='PNG')
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    manager = gui.Jobs(tmp_path/'jobs')
    manager.project_directory = tmp_path/'project'
    try:
        uploaded = manager.upload('assembled.png', stream.getvalue())
        started = manager.start(uploaded['id'], description, 'quick', use_current_svg=False)
        manager.threads[-1].join(timeout=30)
        result = manager.snapshot(started['id'])
        assert result['status'] == 'done' and result['quality'] == 'passed', result
        assert result['sample_report']['stop_reason'] == 'svg_components_composed'
        assert result['project_save']['status'] == 'saved'
    finally:
        manager.close()


def test_real_motor_tube_conversion_passes_gui_worker_and_saved_svg_checks(tmp_path):
    from src import imageConverterGui as gui
    description = 'SVG-Bauteil: AC0151_L.svg\nSVG-Bauteil: AC1002_L.svg hinter AC0151_L.svg'
    donors = [components.load_component(spec['name'], i)[3]
              for i, spec in enumerate(components.parse_components(description))]
    before = [path.read_bytes() for path in donors]
    manager = gui.Jobs(tmp_path/'jobs')
    manager.project_directory = tmp_path/'project'
    try:
        uploaded = manager.upload('AC0152_L.jpg',
                                  (gui.ROOT/'artifacts/images_to_convert/AC0152_L.jpg').read_bytes())
        started = manager.start(uploaded['id'], description, 'quick', seed=42, use_current_svg=False)
        manager.threads[-1].join(timeout=60)
        result = manager.snapshot(started['id'])
        assert result['status'] == 'done' and result['quality'] == 'passed', result
        assert result['pixel_quality']['within_canvas']
        assert result['pixel_quality']['overlap_passed']
        assert result['sample_report']['components'][1]['placement'][2] > 2
        assert result['sample_report']['components'][1]['layer'] == 0
        assert result['project_save']['status'] == 'saved'
        output = manager.folder(started['id'])/'result.svg'
        components.validate_components(output.read_text(encoding='utf-8'), description)
        assert gui.saved_svg_quality(manager.folder(started['id'])/'source.png', output)['passed']
        assert [path.read_bytes() for path in donors] == before
    finally:
        manager.close()


@pytest.mark.parametrize('description', [
    'SVG-Bauteil: a.svg hinter missing.svg',
    'SVG-Bauteil: a.svg hinter a.svg',
    'SVG-Bauteil: a.svg hinter b.svg\nSVG-Bauteil: b.svg hinter a.svg',
    'SVG-Bauteil: a.svg hinter b.svg\nSVG-Bauteil: b.svg\nSVG-Bauteil: b.svg',
])
def test_invalid_layer_references_are_rejected_before_start(description):
    with pytest.raises(ValueError, match='Ebenen'):
        components.parse_components(description)


def overlap_scene(library):
    # The misplaced foreground handle covers a small area of a large panel.
    # The independent raster instead shows the panel in front of the handle.
    folder = library/'artifacts/converted_images/converted_svgs'
    (folder/'panel.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
      <rect width="100" height="100" fill="#408020"/></svg>''')
    (folder/'handle.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="40" height="20">
      <line x1="0" y1="10" x2="40" y2="10" stroke="#777777" stroke-width="4"/></svg>''')
    expected = '''<svg xmlns="http://www.w3.org/2000/svg" width="140" height="100">
      <rect width="100" height="100" fill="#408020"/>
      <line x1="100" y1="50" x2="120" y2="50" stroke="#777777" stroke-width="4"/></svg>'''
    target = components.render_components(expected, 140, 100)
    description = ('SVG-Bauteil: panel.svg bei 0 0 skaliert 1\n'
                   'SVG-Bauteil: handle.svg bei 80 40 skaliert 1')
    return target, description


def test_small_handle_intrusion_fails_local_check_and_order_search_corrects_it(library):
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality, vector_candidate_quality
    target, description = overlap_scene(library)
    drawing = ET.Element('{'+components.NS+'}svg', width='140', height='100',
                         viewBox='0 0 140 100', overflow='hidden')
    for i, spec in enumerate(components.parse_components(description)):
        drawing.append(components.placed_component(components.load_component(spec['name'], i), *spec['placement']))
    wrong = ET.tostring(drawing, encoding='unicode')
    pixels = render_svg(wrong, 140, 100)
    assert pixel_quality(target, pixels)['passed']  # Reproduces the global blind spot.
    quality = vector_candidate_quality(target, pixels, wrong)
    assert not quality['passed'] and not quality['overlap_passed']
    assert quality['overlap_regions'][0]['pixels'] == 80
    svg, references, _ = components.compose_components(description, target, seconds=5.)
    assert [ref['layer'] for ref in references] == [1, 0]
    assert vector_candidate_quality(target, render_svg(svg, 140, 100), svg)['passed']
    assert references[1]['placement'] == [80., 40., 1.]


@pytest.mark.parametrize('relation', ['hinter panel.svg', ''])
def test_layer_constraint_is_validated_against_actual_output(library, relation):
    target, description = overlap_scene(library)
    constrained = description+' '+relation if relation else description.replace(
        'panel.svg bei 0 0 skaliert 1', 'panel.svg bei 0 0 skaliert 1 vor handle.svg')
    svg, _, _ = components.compose_components(constrained, target, seconds=5.)
    drawing = ET.fromstring(svg)
    assert next(n.get('data-svg-component') for n in drawing[0].iter()
                if n.get('data-svg-component')) == 'handle.svg'
    drawing[:] = list(reversed(drawing))
    with pytest.raises(ValueError, match='Reihenfolge'):
        components.validate_components(ET.tostring(drawing, encoding='unicode'), constrained)


def test_explicit_wrong_layer_is_kept_and_result_remains_insufficient(library):
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import vector_candidate_quality
    target, description = overlap_scene(library)
    constrained = description+' vor panel.svg'
    svg, refs, _ = components.compose_components(constrained, target, seconds=5.)
    assert [ref['layer'] for ref in refs] == [0, 1]
    components.validate_components(svg, constrained)
    quality = vector_candidate_quality(target, render_svg(svg, 140, 100), svg)
    assert not quality['passed'] and not quality['overlap_passed']


def test_stale_worker_report_and_cached_gui_result_cannot_hide_intrusion(library, tmp_path):
    import io
    import json
    from PIL import Image
    from src import imageConverterGui as gui
    target, description = overlap_scene(library)
    description += ' vor panel.svg'
    svg, _, _ = components.compose_components(description, target, seconds=5.)
    manager = gui.Jobs(tmp_path/'jobs')
    stream = io.BytesIO()
    Image.fromarray(target).save(stream, format='PNG')
    job = manager.jobs[manager.upload('overlap.png', stream.getvalue())['id']]
    folder = manager.folder(job['id'])
    output = folder/'output'
    output.mkdir()
    (output/'refined.svg').write_text(svg, encoding='utf-8')
    (output/'refined.json').write_text(json.dumps(dict(
        passed=True, improved=False, stop_reason='svg_components_composed')), encoding='utf-8')
    job['description'] = description
    gui.collect_sample_result(folder, job, 0)
    assert job['quality'] == 'warning' and not job['pixel_quality']['overlap_passed']
    assert 'Überlappungsbereich' in job['message']
    job.update(quality='passed', pixel_quality={'passed': True},
               description_validation_version=gui.DESCRIPTION_VALIDATION_VERSION-1)
    manager.save(job)
    restored = gui.Jobs(manager.directory)
    try:
        result = restored.snapshot(job['id'])
        assert result['quality'] == 'warning' and not result['pixel_quality']['overlap_passed']
    finally:
        restored.close()
        manager.close()
