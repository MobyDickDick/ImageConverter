from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterStripedPanelDisk import fit_striped_panel_disk
from tools.evaluate_striped_panel_disk_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/striped_panel_disk_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, **kwargs):
    height, width = image.shape[:2]
    return fit_striped_panel_disk(width, height, description=description, image=image,
        render_fn=kwargs.get('render_fn', render),
        error_fn=kwargs.get('error_fn', lambda a,b: normalized_mse(a,b)[0]))


def test_catalog_raster_passes_without_mutation():
    image = cv2.imread(str(EVIDENCE/MANIFEST['cases'][0]['image']))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error'] <= result['initial_error']
    assert result['evaluations'] <= 1+16*len(result['parameters'])
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('scale,shift,color', [(.5,0,'#583f94'),(1,-5,'#ab3549'),(1,5,'#263073'),(2,2,'#704926')])
def test_independent_resolution_position_and_palette(scale, shift, color):
    root = ET.fromstring(INDEPENDENT)
    root.set('width', str(96*scale)); root.set('height', str(90*scale))
    circle, group = list(root)[-2:]
    circle.set('cx', str(47+shift))
    for band in group:
        band.set('x', str(25+shift))
    group[0].set('fill', color)
    image = render(ET.tostring(root, encoding='unicode'), round(96*scale), round(90*scale))
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('case', make_variations(INDEPENDENT, DESCRIPTION, 20261015), ids=lambda c:c['case_id'])
def test_independent_subpixel_variations(case):
    image = render(case['svg'], case['width'], case['height'])
    result = fit(image, case['description'])
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('mutation', ['no_band','no_disk','vertical','gap','extra_mark','detached','unequal_width'])
def test_incompatible_raster_is_rejected(mutation):
    root = ET.fromstring(INDEPENDENT)
    circle, group = list(root)[-2:]
    if mutation == 'no_band': group.remove(group[1])
    elif mutation == 'no_disk': root.remove(circle)
    elif mutation == 'vertical': group.set('transform', 'rotate(90 47 44)')
    elif mutation == 'gap': group[1].set('height','8')
    elif mutation == 'extra_mark': ET.SubElement(root,'rect',x='43',y='20',width='7',height='5',fill='#000000')
    elif mutation == 'detached': ET.SubElement(root,'rect',x='2',y='2',width='6',height='6',fill='#000000')
    else: group[1].set('width','33')
    assert fit(render(ET.tostring(root, encoding='unicode'),96,90)) is None


@pytest.mark.parametrize('description', ['Ein Kreis.', DESCRIPTION+' Zusätzlich eine Linie.',
    DESCRIPTION+' ohne Streifen.',DESCRIPTION.replace('drei','zwei'),
    DESCRIPTION.replace('waagerecht','senkrecht'), DESCRIPTION+' Das Rechteck ist diagonal.'])
def test_conflicting_description_is_rejected(description):
    assert fit(render(INDEPENDENT,96,90), description) is None


@pytest.mark.parametrize('failure', ['render','nan_error','infinite_error','dimensions','nan_image'])
def test_invalid_inputs_and_measurements_are_rejected(failure):
    image = render(INDEPENDENT,96,90)
    kwargs = {}
    if failure == 'render': kwargs['render_fn'] = lambda *args:None
    elif failure.endswith('_error'): kwargs['error_fn'] = lambda *args:float('nan' if failure=='nan_error' else 'inf')
    elif failure == 'dimensions': image = image[:,:,:2]
    else: image=image.astype(float); image[0,0,0]=np.nan
    assert fit(image, **kwargs) is None


def test_saved_cli_evidence_passes_unchanged_gates():
    report = evaluate(MANIFEST,EVIDENCE)
    assert all(c['satisfactory'] and not c['regressed_metrics'] for c in report['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for c in report['strict_pixel_gates'].values())


def test_semantic_gate_rejects_missing_stripe_gap_and_raster():
    assert symbol_semantics(INDEPENDENT) == 1
    root=ET.fromstring(INDEPENDENT)
    root[-1][1].set('y','40')
    assert symbol_semantics(ET.tostring(root,encoding='unicode')) == 0
    root[-1].remove(root[-1][1])
    assert symbol_semantics(ET.tostring(root,encoding='unicode')) == 0
    ET.SubElement(root,'image',href='fake.png')
    assert symbol_semantics(ET.tostring(root,encoding='unicode')) == 0


def test_catalogs_only_change_actual_flag_description():
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
    for directory in ('descriptions','images_to_convert'):
        descriptions=loadDescriptionMappingImpl(str(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml'),
                                               get_base_name_from_file_fn=getBaseNameFromFileImpl)
        assert descriptions['GE0306'] == DESCRIPTION
        for suffix in ('L','M','S'):
            assert descriptions['GE0306_'+suffix] == MANIFEST['baseline_description']
