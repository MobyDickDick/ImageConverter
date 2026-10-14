from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterCrossPanelDisk import fit_cross_panel_disk
from tools.evaluate_cross_panel_disk_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/cross_panel_disk_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, **kwargs):
    height, width = image.shape[:2]
    return fit_cross_panel_disk(width, height, description=description, image=image,
                               render_fn=kwargs.get('render_fn', render),
                               error_fn=kwargs.get('error_fn', lambda a, b: normalized_mse(a, b)[0]))


def test_catalog_raster_passes_and_is_not_modified():
    image = cv2.imread(str(EVIDENCE/MANIFEST['cases'][0]['image']))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error'] <= result['initial_error']
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']
    assert result['evaluations'] <= 1+16*len(result['parameters'])
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('scale,shift,color', [(.5, 0, '#683fac'), (1, -5, '#ab3549'),
                                             (1, 5, '#264073'), (2, 2, '#704926')])
def test_independent_resolution_position_and_palette(scale, shift, color):
    root = ET.fromstring(INDEPENDENT)
    root.set('width', str(96*scale)); root.set('height', str(90*scale))
    disk, panel, cross = list(root)[-3:]
    disk.set('cx', str(47+shift)); panel.set('x', str(25+shift)); panel.set('fill', color)
    points = [tuple(map(float, p.split(','))) for p in cross.get('points').split()]
    cross.set('points', ' '.join(f'{x+shift},{y}' for x, y in points))
    image = render(ET.tostring(root, encoding='unicode'), round(96*scale), round(90*scale))
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('case', make_variations(INDEPENDENT, DESCRIPTION, 20261014),
                         ids=lambda c: c['case_id'])
def test_independent_subpixel_variations(case):
    image = render(case['svg'], case['width'], case['height'])
    result = fit(image, case['description'])
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('mutation', ['no_cross', 'no_panel', 'no_disk', 'diagonal',
                                    'one_arm_missing', 'detached', 'extra_mark', 'gap'])
def test_incompatible_raster_evidence_is_rejected(mutation):
    root = ET.fromstring(INDEPENDENT)
    disk, panel, cross = list(root)[-3:]
    if mutation.startswith('no_'):
        root.remove({'no_cross': cross, 'no_panel': panel, 'no_disk': disk}[mutation])
    elif mutation == 'diagonal':
        cross.set('transform', 'rotate(45 49 45)')
    elif mutation == 'one_arm_missing':
        cross.set('points', '46,42 52,42 61,42 61,48 52,48 52,55 46,55 46,48 37,48 37,42')
    elif mutation == 'detached':
        ET.SubElement(root, 'rect', x='2', y='2', width='6', height='6', fill='#000000')
    elif mutation == 'extra_mark':
        ET.SubElement(root, 'rect', x='44', y='19', width='7', height='5', fill='#000000')
    else:
        ET.SubElement(root, 'rect', x='48', y='34', width='2', height='23', fill='#683fac')
    assert fit(render(ET.tostring(root, encoding='unicode'), 96, 90)) is None


@pytest.mark.parametrize('description', ['Ein Kreis.', DESCRIPTION+' Zusätzlich eine Linie.',
                                       DESCRIPTION+' ohne Kreuz.', DESCRIPTION+' Zwei Rechtecke.',
                                       DESCRIPTION.replace('vertikal', 'waagerecht'),
                                       DESCRIPTION+' Das Kreuz ist diagonal.'])
def test_conflicting_descriptions_do_not_register(description):
    assert fit(render(INDEPENDENT, 96, 90), description) is None


@pytest.mark.parametrize('failure', ['render', 'nan_error', 'infinite_error', 'dimensions', 'nan_image'])
def test_invalid_inputs_and_measurements_are_rejected(failure):
    image = render(INDEPENDENT, 96, 90)
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


def test_semantic_gate_rejects_raster_copies_and_missing_arm():
    assert symbol_semantics(INDEPENDENT) == 1
    root = ET.fromstring(INDEPENDENT)
    root.remove(list(root)[-1])
    assert symbol_semantics(ET.tostring(root, encoding='unicode')) == 0
    ET.SubElement(root, 'image', href='fake.png')
    assert symbol_semantics(ET.tostring(root, encoding='unicode')) == 0


def test_saved_cli_evidence_passes_unchanged_gates():
    report = evaluate(MANIFEST, EVIDENCE)
    assert all(c['satisfactory'] and not c['regressed_metrics']
               for c in report['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for c in report['strict_pixel_gates'].values())


def test_catalogs_contain_the_same_self_contained_description():
    for directory in ('descriptions', 'images_to_convert'):
        root = ET.parse(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml')
        entry = next(e for e in root.iter('entry') if e.get('key') == 'GE0300')
        assert entry.findtext('beschreibung') == DESCRIPTION
