from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterSpiralDisk import fit_spiral_disk
from tools.evaluate_oriented_spiral_disk_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/oriented_spiral_disk_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, **kwargs):
    height, width = image.shape[:2]
    return fit_spiral_disk(width, height, description=description, image=image,
                           render_fn=kwargs.get('render_fn', render),
                           error_fn=kwargs.get('error_fn', lambda a, b: normalized_mse(a, b)[0]))


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda case: case['source'])
def test_catalog_geometry_is_measured_and_sources_are_unchanged(case):
    image = cv2.imread(str(EVIDENCE/case['image']))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg'], 'left') == 1
    quality = measure_quality(image, result['svg'])
    if case['source'] in ('AC0424_L.jpg', 'AC0424_M.jpg', 'AC0424_S.jpg'):
        assert quality['failures'] == ['foreground_iou_outside_limit']
    else:
        assert quality['satisfactory']
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('turns,direction,word', [(0, 'left', 'links'), (1, 'down', 'unten'),
                                               (2, 'right', 'rechts'), (3, 'up', 'oben')])
def test_all_directions_on_an_independent_non_square_canvas(turns, direction, word):
    image = np.ascontiguousarray(np.rot90(render(INDEPENDENT, 110, 122), turns))
    description = ('Eine gefüllte Kreisscheibe mit dünnem Rand auf hellem Hintergrund. '
                   f'Zwei schräge Linien durchqueren den Kreis und laufen nach {word} aufeinander zu. '
                   'Im Kreisinneren liegt eine offene Spirale mit nach innen abnehmendem Radius, '
                   'die gegen den Uhrzeigersinn nach innen läuft. Keine Schriftzeichen und kein Griff. '
                   'Lage, Abmessungen, Strichstärken und Farben ergeben sich aus dem Bild.')
    original = image.copy()
    shapes = []

    def checked_render(svg, width, height):
        shapes.append((height, width, 3))
        assert (height, width, 3) == image.shape
        return render(svg, width, height)

    def checked_error(a, b):
        assert a.shape == b.shape == image.shape
        return normalized_mse(a, b)[0]

    result = fit(image, description, render_fn=checked_render, error_fn=checked_error)
    assert result is not None and shapes
    assert symbol_semantics(result['svg'], direction) == 1
    assert symbol_semantics(result['svg'], {'up':'down','down':'up','left':'right','right':'left'}[direction]) == 0
    assert measure_quality(image, result['svg'])['satisfactory']
    assert not any(e.get('transform') for e in ET.fromstring(result['svg']).iter())
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('scale,color', [(.5, '#497caa'), (1, '#b28c45'), (2, '#6c9a64')])
def test_independent_resolution_and_palette(scale, color):
    root = ET.fromstring(INDEPENDENT)
    root.set('width', str(110*scale)); root.set('height', str(122*scale))
    root[1].set('fill', color)
    image = render(ET.tostring(root, encoding='unicode'), round(110*scale), round(122*scale))
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg'], 'left') == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('case', make_variations(INDEPENDENT, DESCRIPTION, 20261017),
                         ids=lambda case: case['case_id'])
def test_independent_subpixel_variations(case):
    image = render(case['svg'], case['width'], case['height'])
    result = fit(image, case['description'])
    assert result is not None
    assert symbol_semantics(result['svg'], 'left') == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('mutation', ['no_spiral', 'no_disk', 'no_line', 'extra_mark', 'detached', 'reversed'])
def test_incompatible_raster_evidence_is_rejected(mutation):
    root = ET.fromstring(INDEPENDENT)
    if mutation.startswith('no_'):
        root.remove({'no_spiral': root[-1], 'no_disk': root[1], 'no_line': root[2]}[mutation])
    elif mutation == 'extra_mark':
        ET.SubElement(root, 'rect', x='28', y='62', width='6', height='6', fill='#000000')
    elif mutation == 'detached':
        ET.SubElement(root, 'rect', x='1', y='1', width='5', height='5', fill='#000000')
    else:
        root[-1].set('transform', 'translate(102 0) scale(-1 1)')
    assert fit(render(ET.tostring(root, encoding='unicode'), 110, 122)) is None


@pytest.mark.parametrize('description', [DESCRIPTION+' ohne Spirale.',
    DESCRIPTION+' Zusätzlich eine Linie.', DESCRIPTION.replace('nach links', 'nach rechts'),
    DESCRIPTION.replace('Zwei schräge Linien', 'Eine schräge Linie'),
    DESCRIPTION.replace('gegen den Uhrzeigersinn', 'im Uhrzeigersinn'),
    DESCRIPTION+' Die Linien laufen nach oben aufeinander zu.'])
def test_conflicting_description_or_orientation_is_rejected(description):
    assert fit(render(INDEPENDENT, 110, 122), description) is None


@pytest.mark.parametrize('failure', ['render', 'nan_error', 'infinite_error', 'dimensions', 'nan_image'])
def test_invalid_inputs_and_measurements_are_rejected(failure):
    image = render(INDEPENDENT, 110, 122)
    kwargs = {}
    if failure == 'render':
        kwargs['render_fn'] = lambda *args: None
    elif failure.endswith('_error'):
        kwargs['error_fn'] = lambda *args: float('nan' if failure == 'nan_error' else 'inf')
    elif failure == 'dimensions':
        image = image[:, :, :2]
    else:
        image = image.astype(float); image[0, 0, 0] = np.nan
    assert fit(image, **kwargs) is None


def test_catalogs_describe_each_variant_without_catalog_references():
    for directory in ('descriptions', 'images_to_convert'):
        tree = ET.parse(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml')
        for case in MANIFEST['cases']:
            entry = next(e for e in tree.iter('entry') if e.get('key') == Path(case['source']).stem)
            assert entry.findtext('beschreibung') == DESCRIPTION


def test_saved_cli_evidence_passes_both_regular_gates_without_regression():
    report = evaluate(MANIFEST, EVIDENCE)
    assert all(case['satisfactory'] and not case['regressed_metrics']
               for case in report['satisfaction_gate']['cases'])
