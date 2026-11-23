"""Colored circles retain their declared symmetry, rim contact and full inventory."""
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src import imageConverterGui as gui
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterDescriptionLanguage import (
    DescriptionRejected, description_assertions, draft_assertions, validate_svg_assertions,
)
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration
from src.iCCModules.imageCompositeConverterSymmetricCircleLines import (
    fit_symmetric_circle_lines, symmetric_circle_lines_spec,
)
from tools.evaluate_svg_text_baseline import render_librsvg

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Grauer Kreis mit roter Hintergrundfarbe.\n\n'
               'Zwei weisse Linien, welche den Rand des Kreises berühren. \n\n'
               'Die Form ist symmetrisch in Bezug auf eine horizontale Linie durch die Mitte des Kreises.')


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def test_original_description_and_anonymous_route_preserve_all_claims():
    for folder in ('descriptions', 'images_to_convert'):
        actual = next(e.get('beschreibung') for e in ET.parse(
            ROOT/'artifacts'/folder/'Finale_Wurzelformen_V3.xml').iter('bild') if e.text == 'AC0202_1.jpg')
        assert actual == DESCRIPTION
    assertions = description_assertions(DESCRIPTION)
    assert assertions['objects'] == dict(circle=1, line=2)
    assert assertions['symmetric_circle_lines'] == dict(axis='horizontal', light_lines=True, touches_rim=True)
    _, params = Reflection({'anonymous': DESCRIPTION}).parseDescription('anonymous', 'anonymous.jpg')
    assert params['contract_status'] == 'ok' and params['mode'] == 'non_composite'
    assert params['geometry_ir'] == [] and params['label'] == ''
    assert draft_assertions(assertions)['symmetric_circle_lines'] == assertions['symmetric_circle_lines']


@pytest.mark.parametrize('extra', [' Zusätzlich ein Quadrat.', ' Ohne Linien.', ' Mit Beschriftung "M".'])
def test_extra_claims_are_not_silently_dropped(extra):
    assert symmetric_circle_lines_spec(DESCRIPTION+extra) is None


def independent_svg(axis, size, color):
    radius, cx, cy, rim = size*.34, size*.46, size*.53, size*.018
    direction = np.array([1., .36])
    direction /= np.linalg.norm(direction)
    closest = np.array([-direction[1], direction[0]])*radius*.46
    distance = np.sqrt((radius-rim/2)**2-closest@closest)
    first = np.array([closest-distance*direction, closest+distance*direction])
    if axis == 'vertical':
        first = first[:, ::-1]
    second = first.copy()
    second[:, 1 if axis == 'horizontal' else 0] *= -1
    lines = ''.join(f'<line x1="{a[0]+cx}" y1="{a[1]+cy}" x2="{b[0]+cx}" y2="{b[1]+cy}" '
                    f'stroke="#f4f4f4" stroke-width="{size*.021}"/>' for a, b in (first, second))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
            f'<rect width="{size}" height="{size}" fill="white"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" stroke="#ababab" stroke-width="{rim}"/>'
            +lines+'</svg>')


@pytest.mark.parametrize('axis', ['horizontal', 'vertical'])
@pytest.mark.parametrize('size,word,color', [(48, 'roter', '#b62a40'), (80, 'blauer', '#295cb6')])
def test_independent_colored_sources_in_both_axes(axis, size, word, color):
    description = DESCRIPTION.replace('horizontale', axis.replace('horizontal', 'horizontale').replace('vertical', 'vertikale'))
    description = description.replace('roter', word)
    source = render_librsvg(independent_svg(axis, size, color), size, size)
    with search_configuration(mode='portfolio', seed=42):
        result = fit_symmetric_circle_lines(size, size, description=description, image=source,
            render_fn=render, error_fn=lambda a, b: float(np.mean((a.astype(float)-b)**2)/255**2))
    assert result is not None
    validate_svg_assertions(result['svg'], description_assertions(description))
    assert pixel_quality(source, render_librsvg(result['svg'], size, size))['passed'], result['quality']


@pytest.mark.parametrize('fault', ['detached', 'wrong_axis', 'missing', 'ellipse'])
def test_invalid_geometry_is_rejected_even_in_drafts(fault):
    root = ET.fromstring(independent_svg('horizontal', 80, '#b62a40'))
    circle = next(e for e in root if e.tag.endswith('circle'))
    lines = [e for e in root if e.tag.endswith('line')]
    if fault == 'detached':
        for line in lines:
            for x, y in (('x1', 'y1'), ('x2', 'y2')):
                line.set(x, str(float(circle.get('cx'))+(float(line.get(x))-float(circle.get('cx')))*.9))
                line.set(y, str(float(circle.get('cy'))+(float(line.get(y))-float(circle.get('cy')))*.9))
    elif fault == 'wrong_axis':
        root.set('transform', f'rotate(90 {circle.get("cx")} {circle.get("cy")})')
    elif fault == 'missing':
        root.remove(lines[1])
    else:
        circle.set('transform', 'scale(1.05 1)')
    for assertions in (description_assertions(DESCRIPTION), draft_assertions(description_assertions(DESCRIPTION))):
        with pytest.raises(DescriptionRejected):
            validate_svg_assertions(ET.tostring(root, encoding='unicode'), assertions)


@pytest.mark.parametrize('profile,seed,reuse', [('quick', 17, False), ('quick', 18, False),
                                             ('normal', 17, False), ('quick', 17, True)])
def test_real_worker_and_independent_renderer(tmp_path, monkeypatch, profile, seed, reuse):
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    try:
        uploaded = jobs.upload('anonymous.jpg', (ROOT/'artifacts/images_to_convert/AC0202_1.jpg').read_bytes())
        if reuse:
            target = jobs.project_svg(jobs.jobs[uploaded['id']])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT/'artifacts/converted_images/converted_svgs/AC0202_1.svg').read_bytes())
            assert gui.result_description_error(target, DESCRIPTION)
        started = jobs.start(uploaded['id'], DESCRIPTION, profile, seed=seed, use_current_svg=reuse)
        jobs.threads[-1].join(gui.PROFILES[profile][1]+25)
        result = jobs.snapshot(started['id'])
        (tmp_path/'job.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        assert result['status'] == 'done' and result['quality'] == 'passed', result
        svg = (jobs.folder(result['id'])/'result.svg').read_text(encoding='utf-8')
        validate_svg_assertions(svg, description_assertions(DESCRIPTION))
        source = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0202_1.jpg'))
        independent = render_librsvg(svg, source.shape[1], source.shape[0])
        quality = pixel_quality(source, independent)
        (tmp_path/'result.svg').write_text(svg, encoding='utf-8')
        cv2.imwrite(str(tmp_path/'source.png'), source)
        cv2.imwrite(str(tmp_path/'result-librsvg.png'), independent)
        comparison = np.concatenate([source, independent, cv2.absdiff(source, independent)], axis=1)
        cv2.imwrite(str(tmp_path/'comparison.png'), cv2.resize(comparison, None, fx=6, fy=6, interpolation=cv2.INTER_NEAREST))
        (tmp_path/'quality.json').write_text(json.dumps(dict(seed=seed, profile=profile, reuse=reuse,
            independent_quality=quality, search=result.get('search_summary'), elapsed=result.get('elapsed')), indent=2))
        assert quality['passed'], quality
    finally:
        jobs.close()
