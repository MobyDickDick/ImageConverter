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
    assert len(references) == 2 and count == 0


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
