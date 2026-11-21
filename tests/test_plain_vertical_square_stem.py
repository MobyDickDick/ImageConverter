"""Plain square handles keep their exact geometry through the real GUI worker."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src import imageConverterGui as gui
from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterCanvas import contain_svg, within_canvas
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterSquareStem import fit_square_stem

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Quadrat mit dunkelgrauem Rand und hellgrauem Hintergrund. Unten am Quadrat graue Linie. '
               'Gesamthatf eine Kelle mit Stil nach unten. '
               'Die graue Linie ist in der horizontalen Mittelachse des Quadrats.')


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg, w, h, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image):
    h, w = image.shape[:2]
    result = fit_square_stem(geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION), image=image,
        description=DESCRIPTION,
        render_fn=lambda ir: render(geometry.renderGeometryIrToSvgImpl(w, h, ir), w, h),
        error_fn=lambda raster: calculateErrorImpl(image, raster, cv2_module=cv2, np_module=np))
    if result is None:
        return None
    return contain_svg(geometry.renderGeometryIrToSvgImpl(w, h, result['geometry_ir']), w, h)


def check(image, svg):
    assert svg is not None
    validate_svg_assertions(svg, description_assertions(DESCRIPTION))
    h, w = image.shape[:2]
    assert within_canvas(svg, w, h)
    assert pixel_quality(image, render(svg, w, h))['passed']
    nodes = list(ET.fromstring(svg).iter())
    assert not any(e.tag.rsplit('}', 1)[-1] in {'text', 'image'} for e in nodes)


def test_reported_original_is_a_complete_square_and_line():
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0701_L.jpg'))
    check(image, fit(image))


def synthetic(scale=1, phase=0, fill='#f2f2f2', fault=None):
    width = 25 if fault == 'rectangle' else 30
    offset = 8 if fault == 'offset' else 0
    parts = [f'<rect x="{6+phase}" y="8" width="{width}" height="30" '
             f'fill="{fill}" stroke="#757575" stroke-width="1.4"/>']
    if fault != 'missing':
        parts.append(f'<path d="M {21+phase+offset} 38 L {21+phase+offset} 65" '
                     'stroke="#818181" stroke-width="2"/>')
    if fault == 'extra':
        parts.append('<circle cx="39" cy="60" r="3" fill="black"/>')
    if fault == 'mark':
        parts.append('<path d="M 14 16 L 28 30" stroke="black" stroke-width="3"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{46*scale}" height="{72*scale}" '
           'viewBox="0 0 46 72">'+''.join(parts)+'</svg>')
    return render(svg, 46*scale, 72*scale)


@pytest.mark.parametrize('scale,phase,fill', [(1,0,'#f2f2f2'), (1,.5,'#c2c2c2'),
                                           (2,.25,'#f2f2f2'), (2,.75,'#cccccc')])
def test_independent_dimensions_subpixel_phase_and_resolution(scale, phase, fill):
    image = synthetic(scale, phase, fill)
    check(image, fit(image))


@pytest.mark.parametrize('fault', ['missing', 'extra', 'mark', 'offset', 'rectangle'])
def test_wrong_topology_and_nonsquare_body_cannot_pass(fault):
    image = synthetic(fault=fault)
    svg = fit(image)
    if svg is not None:
        # A rejected raster may still yield a draft; it cannot pass pixels.
        assert not pixel_quality(image, render(svg, image.shape[1], image.shape[0]))['passed']


@pytest.mark.parametrize('stale_template', [False, True])
def test_gui_worker_passes_without_changing_description(tmp_path, monkeypatch, stale_template):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    monkeypatch.setattr(jobs, 'publish_best', lambda *args: None)
    try:
        job = jobs.upload('neutral_square.jpg', (ROOT/'artifacts/images_to_convert/AC0701_L.jpg').read_bytes())
        if stale_template:
            jobs.attach_sample(job['id'], 'stale.svg',
                b'<svg xmlns="http://www.w3.org/2000/svg" width="25" height="45">'
                b'<rect x="2" y="5" width="22" height="18" fill="#eeeeee"/>'
                b'<path d="M 13 23 L 13 45" stroke="gray"/></svg>')
        started = jobs.start(job['id'], DESCRIPTION, 'quick', seed=42)
        jobs.threads[-1].join(timeout=55)
        result = jobs.snapshot(started['id'])
        assert result['status'] == 'done' and result['quality'] == 'passed', result
        assert result['description'] == DESCRIPTION
        check(cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0701_L.jpg')),
              (jobs.folder(started['id'])/'result.svg').read_text(encoding='utf-8'))
    finally:
        jobs.close()
