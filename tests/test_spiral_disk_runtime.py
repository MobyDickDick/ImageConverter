from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterSpiralDisk import fit_spiral_disk
from tools.evaluate_spiral_disk_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/spiral_disk_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, **kwargs):
    height, width = image.shape[:2]
    return fit_spiral_disk(width, height, description=description, image=image,
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


@pytest.mark.parametrize('scale,shift,color', [(.5, -2, '#a64c88'), (1, 3, '#b29051'), (2, -4, '#4e88b2')])
def test_independent_resolution_position_and_palette(scale, shift, color):
    root = ET.fromstring(INDEPENDENT)
    root.set('width', str(98*scale)); root.set('height', str(92*scale))
    disk = list(root)[1]
    disk.set('fill', color)
    group = ET.Element('g', transform=f'translate({shift} 0)')
    for element in list(root)[1:]:
        root.remove(element); group.append(element)
    root.append(group)
    image = render(ET.tostring(root, encoding='unicode'), round(98*scale), round(92*scale))
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('case', make_variations(INDEPENDENT, DESCRIPTION, 20261015),
                         ids=lambda c: c['case_id'])
def test_independent_subpixel_variations(case):
    image = render(case['svg'], case['width'], case['height'])
    result = fit(image, case['description'])
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('mutation', ['no_spiral', 'no_disk', 'no_line', 'extra_mark', 'detached', 'reversed', 'gap'])
def test_incompatible_raster_evidence_is_rejected(mutation):
    root = ET.fromstring(INDEPENDENT)
    if mutation.startswith('no_'):
        root.remove({'no_spiral': list(root)[-1], 'no_disk': list(root)[1], 'no_line': list(root)[2]}[mutation])
    elif mutation == 'detached':
        ET.SubElement(root, 'rect', x='1', y='1', width='5', height='5', fill='#000000')
    elif mutation == 'extra_mark':
        ET.SubElement(root, 'rect', x='41', y='18', width='6', height='5', fill='#000000')
    elif mutation == 'reversed':
        root[-1].set('transform', 'translate(100 0) scale(-1 1)')
    else:
        ET.SubElement(root, 'rect', x='18', y='38', width='9', height='8', fill='#6c9bcc')
    assert fit(render(ET.tostring(root, encoding='unicode'), 98, 92)) is None


@pytest.mark.parametrize('description', ['Ein Kreis.', DESCRIPTION+' Zusätzlich eine Linie.',
                                       DESCRIPTION+' ohne Spirale.',
                                       DESCRIPTION.replace('Zwei schräge Linien', 'Eine schräge Linie'),
                                       DESCRIPTION.replace('gegen den Uhrzeigersinn', 'im Uhrzeigersinn')])
def test_conflicting_descriptions_do_not_register(description):
    assert fit(render(INDEPENDENT, 98, 92), description) is None


@pytest.mark.parametrize('failure', ['render', 'nan_error', 'infinite_error', 'dimensions', 'nan_image'])
def test_invalid_inputs_and_measurements_are_rejected(failure):
    image = render(INDEPENDENT, 98, 92)
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


def test_semantic_gate_rejects_raster_copies_missing_chords_and_reverse_curvature():
    assert symbol_semantics(INDEPENDENT) == 1
    root = ET.fromstring(INDEPENDENT)
    root.remove(list(root)[-1])
    assert symbol_semantics(ET.tostring(root, encoding='unicode')) == 0
    ET.SubElement(root, 'image', href='fake.png')
    assert symbol_semantics(ET.tostring(root, encoding='unicode')) == 0


def test_saved_cli_evidence_passes_regular_gates_and_color_strict_gates():
    report = evaluate(MANIFEST, EVIDENCE)
    assert all(c['satisfactory'] and not c['regressed_metrics']
               for c in report['satisfaction_gate']['cases'])
    for case in MANIFEST['cases']:
        if '_1_' in case['source'] or '_2_' in case['source']:
            assert report['strict_pixel_gates'][case['case_id']]['satisfactory']


def test_interior_spiral_is_not_replaced_by_a_default_font_glyph():
    from src.iCCModules.imageCompositeConverterSemantic import apply_semantic_badge_description_rules
    params = {}
    assert not apply_semantic_badge_description_rules(desc=DESCRIPTION, params=params)
    assert params == {}


def test_catalogs_contain_the_same_self_contained_descriptions():
    for directory in ('descriptions', 'images_to_convert'):
        root = ET.parse(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml')
        for case in MANIFEST['cases']:
            entry = next(e for e in root.iter('entry') if e.get('key') == Path(case['source']).stem)
            assert entry.findtext('beschreibung') == DESCRIPTION
