"""The complete described inventory and its symmetry survive every save."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterDescriptionLanguage import (
    DescriptionRejected, description_assertions, normalize_description, validate_svg_assertions,
)
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterRepresentation import logical_inventory
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration
from src.iCCModules.imageCompositeConverterSymmetricCircleLines import (
    fit_symmetric_circle_lines, symmetric_circle_lines_spec,
)

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Es ist ein grauer Kreis mit grauem Rand. Im Kreis sind zwei dunkelgraue Linien enthalten, '
               'welche symmetrisch in bezug auf die senkrechte Symmetrieachse des Kreises sind.')


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg, w, h, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION):
    with search_configuration(mode='portfolio', seed=42):
        return fit_symmetric_circle_lines(image.shape[1], image.shape[0], description=description,
            image=image, render_fn=render,
            error_fn=lambda a, b: float(np.mean((a.astype(float)-b)**2)/255**2))


@pytest.fixture(scope='module')
def original_result():
    return fit(cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0201.jpg')))


def test_catalog_correction_and_neutral_filename_declare_the_same_full_inventory():
    for folder in ('descriptions', 'images_to_convert'):
        actual = next(e.get('beschreibung') for e in ET.parse(
            ROOT/'artifacts'/folder/'Finale_Wurzelformen_V3.xml').iter('bild') if e.text == 'AC0201.jpg')
        assert actual == DESCRIPTION
    _, params = Reflection({'anonymous': DESCRIPTION}).parseDescription('anonymous', 'anonymous.jpg')
    assertions = params['language_assertions']
    assert assertions['objects'] == dict(circle=1, line=2)
    assert assertions['symmetric_circle_lines'] == dict(axis='vertical')


def test_original_now_produces_all_primitives_without_claiming_false_success(original_result):
    result = original_result
    assert result is not None and result['evaluations'] > 0
    assert logical_inventory(result['svg'], dict(circle=1, line=2)) == dict(circle=1, line=2)
    validate_svg_assertions(result['svg'], description_assertions(DESCRIPTION))
    quality = result['quality']
    assert quality['normalized_mse'] < .001
    assert quality['edge_alignment'] > .9
    # Pixel gates are unchanged; the source JPEG remains a borderline fit.
    assert quality['passed'] == (quality['normalized_mse'] <= .01 and quality['foreground_mse'] <= .04
                                  and quality['foreground_iou'] >= .85 and quality['edge_alignment'] >= .72)


@pytest.mark.parametrize('axis', ['vertical', 'horizontal'])
@pytest.mark.parametrize('size', [48, 80])
def test_independent_synthetic_geometry_with_both_symmetry_axes(axis, size):
    radius, cx, cy = size*.31, size*.48, size*.52
    points = np.array([[-.72, .56], [-.24, -.86]])*radius
    if axis == 'horizontal':
        points = points[:, ::-1]
    mirror = points.copy()
    mirror[:, 0 if axis == 'vertical' else 1] *= -1
    lines = ''.join(f'<line x1="{a[0]+cx}" y1="{a[1]+cy}" x2="{b[0]+cx}" y2="{b[1]+cy}" '
                    'stroke="#666666" stroke-width="1.4" stroke-linecap="round"/>' for a, b in (points, mirror))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
           f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="#d2d2d2" stroke="#888888" stroke-width="1.2"/>'
           +lines+'</svg>')
    description = DESCRIPTION.replace('senkrechte', 'horizontale') if axis == 'horizontal' else DESCRIPTION
    result = fit(render(svg, size, size), description)
    assert result is not None and result['quality']['passed']
    validate_svg_assertions(result['svg'], description_assertions(description))


@pytest.mark.parametrize('fault', ['missing', 'symmetry', 'outside', 'ellipse', 'wrong_axis'])
def test_template_changes_cannot_lose_lines_or_their_relations(original_result, fault):
    root = ET.fromstring(original_result['svg'])
    circle = next(n for n in root if n.tag.endswith('circle'))
    lines = [n for n in root if n.tag.endswith('line')]
    description = DESCRIPTION
    if fault == 'missing':
        root.remove(lines[1])
    elif fault == 'symmetry':
        lines[1].set('x1', str(float(lines[1].get('x1'))+1))
    elif fault == 'outside':
        lines[1].set('y2', '-10')
    elif fault == 'ellipse':
        circle.set('transform', 'scale(1.1 1)')
    else:
        description = DESCRIPTION.replace('senkrechte', 'horizontale')
    with pytest.raises(DescriptionRejected):
        validate_svg_assertions(ET.tostring(root, encoding='unicode'), description_assertions(description))


@pytest.mark.parametrize('extra', [' Zusätzlich ein Quadrat.', ' Ohne Linien.', ' Mit Beschriftung "M".'])
def test_unconsumed_claims_are_not_dispatched_to_the_closed_model(extra):
    assert symmetric_circle_lines_spec(DESCRIPTION+extra) is None


def test_typo_normalization_keeps_quoted_labels_unchanged():
    text = 'Zwei dunelgraue Linien und Beschriftung "dunelgraue".'
    assert normalize_description(text) == 'Zwei dunkelgraue Linien und Beschriftung "dunelgraue".'


def test_shared_translation_and_scaling_preserve_relations(original_result):
    root = ET.fromstring(original_result['svg'])
    group = ET.Element('{http://www.w3.org/2000/svg}g', transform='translate(5 8) scale(1.3)')
    for node in list(root):
        if node.tag.endswith('rect'):
            continue
        root.remove(node)
        group.append(node)
    root.append(group)
    validate_svg_assertions(ET.tostring(root, encoding='unicode'), description_assertions(DESCRIPTION))


def test_real_worker_with_neutral_filename_creates_an_honestly_rated_svg(tmp_path, monkeypatch):
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui, 'catalog_descriptions', lambda: {})
    jobs = gui.Jobs(tmp_path/'jobs')
    jobs.project_directory = tmp_path/'project'
    monkeypatch.setattr(jobs, 'publish_best', lambda *args: None)
    try:
        job = jobs.upload('neutral_circle.jpg', (ROOT/'artifacts/images_to_convert/AC0201.jpg').read_bytes())
        started = jobs.start(job['id'], DESCRIPTION, 'quick', seed=42, use_current_svg=False)
        jobs.threads[-1].join(timeout=55)
        result = jobs.snapshot(started['id'])
        assert result['status'] == 'done', result
        svg_path = jobs.folder(started['id'])/'result.svg'
        validate_svg_assertions(svg_path.read_text(encoding='utf-8'), description_assertions(DESCRIPTION))
        measured = gui.saved_svg_quality(jobs.folder(started['id'])/'source.png', svg_path)
        assert result['quality'] == ('passed' if measured['passed'] else 'warning')
        assert measured['within_canvas']
    finally:
        jobs.close()
