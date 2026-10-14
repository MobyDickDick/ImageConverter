from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterFlameDisk import fit_flame_disk
from tools.evaluate_flame_disk_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/flame_disk_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, **kwargs):
    height, width = image.shape[:2]
    return fit_flame_disk(width, height, description=description, image=image,
                          render_fn=kwargs.get('render_fn', render),
                          error_fn=kwargs.get('error_fn', lambda a, b: normalized_mse(a, b)[0]))


def accepted(image, description=DESCRIPTION):
    result = fit(image, description)
    assert result is not None
    assert result['error'] <= result['initial_error']
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']
    assert result['evaluations'] <= 1+16*len(result['parameters'])
    return result


def test_catalog_raster_is_registered_without_changing_input():
    image = cv2.imread(str(EVIDENCE/MANIFEST['cases'][0]['image']))
    original = image.copy()
    accepted(image)
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('scale,shift,color', [(.5, 0, '#6e3c63'), (1, -4, '#a13449'),
                                             (1, 4, '#27457b'), (2, 2, '#705028')])
def test_independent_resolution_position_and_palette(scale, shift, color):
    root = ET.fromstring(INDEPENDENT)
    root.set('width', str(104*scale)); root.set('height', str(100*scale))
    for element in list(root)[-4:]:
        if element.get('fill') == '#713e9d':
            element.set('fill', color)
    group = ET.Element('{http://www.w3.org/2000/svg}g', transform=f'translate({shift} 0)')
    for element in list(root)[1:]:
        root.remove(element); group.append(element)
    root.append(group)
    accepted(render(ET.tostring(root, encoding='unicode'), round(104*scale), round(100*scale)))


@pytest.mark.parametrize('case', make_variations(INDEPENDENT, DESCRIPTION, 20261014),
                         ids=lambda c: c['case_id'])
def test_independent_subpixel_variations(case):
    accepted(render(case['svg'], case['width'], case['height']), case['description'])


@pytest.mark.parametrize('mutation', ['no_inner', 'no_outer', 'no_disk', 'smooth',
                                    'upside_down', 'detached', 'extra_mark', 'gap'])
def test_incompatible_raster_evidence_is_rejected(mutation):
    root = ET.fromstring(INDEPENDENT)
    disk, outer, bowl, inner, inner_bowl = list(root)[-5:]
    if mutation == 'no_inner':
        root.remove(inner); root.remove(inner_bowl)
    elif mutation == 'no_outer':
        root.remove(outer); root.remove(bowl)
    elif mutation == 'no_disk':
        root.remove(disk)
    elif mutation == 'smooth':
        outer.set('points', '29,61 49,15 71,61')
    elif mutation == 'upside_down':
        for element in (outer, bowl, inner, inner_bowl):
            element.set('transform', 'rotate(180 50 48)')
    elif mutation == 'detached':
        ET.SubElement(root, 'rect', x='1', y='1', width='5', height='5', fill='#000000')
    elif mutation == 'extra_mark':
        ET.SubElement(root, 'rect', x='33', y='58', width='4', height='5', fill='#000000')
    else:
        ET.SubElement(root, 'rect', x='20', y='45', width='60', height='4', fill='#ffffff')
    assert fit(render(ET.tostring(root, encoding='unicode'), 104, 100)) is None


@pytest.mark.parametrize('description', ['Ein Kreis.', DESCRIPTION+' Zusätzlich eine Linie.',
                                       DESCRIPTION+' ohne Flamme.', DESCRIPTION+' nicht aufrecht.',
                                       DESCRIPTION.replace('vertikal', 'waagerecht'),
                                       DESCRIPTION.replace('kleinere helle', 'weitere dunkle')])
def test_conflicting_descriptions_do_not_register(description):
    assert fit(render(INDEPENDENT, 104, 100), description) is None


@pytest.mark.parametrize('failure', ['render', 'nan_error', 'infinite_error', 'dimensions', 'nan_image'])
def test_invalid_inputs_and_measurements_are_rejected(failure):
    image = render(INDEPENDENT, 104, 100)
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


def test_semantic_gate_rejects_raster_copy_missing_bowl_and_unenclosed_flame():
    assert symbol_semantics(INDEPENDENT) == 1
    root = ET.fromstring(INDEPENDENT)
    root.remove(list(root)[-1])
    assert symbol_semantics(ET.tostring(root, encoding='unicode')) == 0
    ET.SubElement(root, 'image', href='fake.png')
    assert symbol_semantics(ET.tostring(root, encoding='unicode')) == 0
    root = ET.fromstring(INDEPENDENT)
    list(root)[-2].set('points', '1,1 2,3 3,1 4,3 5,1')
    assert symbol_semantics(ET.tostring(root, encoding='unicode')) == 0


def test_saved_cli_evidence_passes_unchanged_gates():
    report = evaluate(MANIFEST, EVIDENCE)
    assert all(c['satisfactory'] and not c['regressed_metrics']
               for c in report['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for c in report['strict_pixel_gates'].values())


def test_catalogs_contain_the_same_self_contained_description():
    for directory in ('descriptions', 'images_to_convert'):
        root = ET.parse(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml')
        entry = next(e for e in root.iter('entry') if e.get('key') == 'b_heating1')
        assert entry.findtext('beschreibung') == DESCRIPTION
