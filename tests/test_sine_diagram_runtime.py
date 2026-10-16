"""Sinusoid registration uses raster geometry and true production render errors."""
from pathlib import Path
import json

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterSineDiagram import fit_sine_diagram
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from tools.evaluate_sine_diagram_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/sine_diagram_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def production_error(a, b):
    return calculateErrorImpl(a, b, cv2_module=cv2, np_module=np)


def fit(image, description=DESCRIPTION, **kwargs):
    height, width = image.shape[:2]
    return fit_sine_diagram(width, height, description=description, image=image,
        render_fn=kwargs.get('render_fn', render), error_fn=kwargs.get('error_fn', production_error))


def check(image, description=DESCRIPTION):
    original = image.copy()
    result = fit(image, description)
    assert result is not None
    h, w = image.shape[:2]
    assert result['error'] == production_error(image, render(result['svg'], w, h))
    assert result['initial_error'] == production_error(image, render(result['initial_svg'], w, h))
    assert result['error'] <= result['initial_error']
    assert result['evaluations'] <= 1+24*len(result['parameters'])
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']
    np.testing.assert_array_equal(result['rendered'], render(result['svg'], w, h))
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_anonymous_catalog_holdouts(case):
    check(cv2.imread(str(EVIDENCE/case['image'])))


@pytest.mark.parametrize('case', make_variations(INDEPENDENT, DESCRIPTION, 20261016), ids=lambda c: c['case_id'])
def test_independent_variations(case):
    check(render(case['svg'], case['width'], case['height']), case['description'])


@pytest.mark.parametrize('scale,color', [(.5,'#714b86'),(1,'#9b5035'),(2,'#315e94')])
def test_other_resolution_and_palette(scale, color):
    svg = INDEPENDENT.replace('width="104" height="88"', f'width="{104*scale:g}" height="{88*scale:g}"').replace('#306cbb',color)
    check(render(svg, round(104*scale), round(88*scale)))


@pytest.mark.parametrize('change', ['missing_axes','missing_wave','dot','flat','second_wave'])
def test_unsupported_topology(change):
    from xml.etree import ElementTree as ET
    root = ET.fromstring(INDEPENDENT)
    if change == 'missing_axes': root.remove(root[1])
    elif change == 'missing_wave': root.remove(root[2])
    elif change == 'dot': ET.SubElement(root,'circle',cx='65',cy='16',r='4',fill='#222222')
    elif change == 'flat': root[2].set('d','M 13 42 H 97')
    else:
        import copy
        wave = copy.deepcopy(root[2]); wave.set('transform','translate(0,-15)');root.append(wave)
    assert fit(render(ET.tostring(root,encoding='unicode'),104,88)) is None


@pytest.mark.parametrize('description', ['',DESCRIPTION.replace('Sinuskurve','Gerade'),DESCRIPTION+' Zusätzlich ein Punkt.'])
def test_unsupported_description(description):
    assert fit(render(INDEPENDENT,104,88),description) is None


@pytest.mark.parametrize('value', [float('nan'),float('inf'),-1])
def test_invalid_error(value):
    assert fit(render(INDEPENDENT,104,88),error_fn=lambda *args:value) is None


def test_invalid_input_and_renderer():
    assert fit(np.full((24,32,3),np.nan)) is None
    assert fit(render(INDEPENDENT,104,88),render_fn=lambda *args:None) is None
    assert fit(np.full((24,32,3),255,dtype=np.uint8)) is None


def test_saved_cli_evidence():
    report = evaluate(MANIFEST,EVIDENCE)
    assert all(c['satisfactory'] and not c['regressed_metrics'] for c in report['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for c in report['strict_pixel_gates'].values())


def test_semantic_checker_rejects_missing_axes_and_extra_shapes():
    svg=(EVIDENCE/MANIFEST['cases'][0]['after_svg']).read_text(encoding='utf-8')
    assert symbol_semantics(svg)==1
    assert symbol_semantics(svg.replace('<path d="M','<path d="L',1))==0
    assert symbol_semantics(svg.replace('</svg>','<circle cx="10" cy="3" r="1"/></svg>'))==0
