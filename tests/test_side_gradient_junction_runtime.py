"""Cardinal T registration on independent raster geometry and true render errors."""
from pathlib import Path
import json

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterGradientJunction import fit_gradient_junction
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from tools.evaluate_gradient_junction_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/side_gradient_junction_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def production_error(a, b):
    return calculateErrorImpl(a, b, cv2_module=cv2, np_module=np)


def fit(image, description=DESCRIPTION, **kwargs):
    height, width = image.shape[:2]
    return fit_gradient_junction(width, height, description=description, image=image,
        render_fn=kwargs.get('render_fn', render), error_fn=kwargs.get('error_fn', production_error))


def check(image, description=DESCRIPTION, direction='left'):
    original = image.copy()
    result = fit(image, description)
    assert result is not None
    h, w = image.shape[:2]
    assert result['error'] == production_error(image, render(result['svg'], w, h))
    assert result['initial_error'] == production_error(image, render(result['initial_svg'], w, h))
    assert result['error'] <= result['initial_error']
    assert result['evaluations'] <= 3+32*len(result['parameters'])
    assert symbol_semantics(result['svg'], direction) == 1
    assert measure_quality(image, result['svg'])['satisfactory']
    np.testing.assert_array_equal(result['rendered'], render(result['svg'], w, h))
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_anonymous_catalog_holdouts(case):
    check(cv2.imread(str(EVIDENCE/case['image'])))


@pytest.mark.parametrize('case', make_variations(INDEPENDENT, DESCRIPTION, 20261016), ids=lambda c: c['case_id'])
def test_independent_subpixel_variations(case):
    check(render(case['svg'], case['width'], case['height']), case['description'])


@pytest.mark.parametrize('turns,direction,word', [(0,'left','links'),(1,'down','unten'),
                                                (2,'right','rechts'),(3,'up','oben')])
def test_four_directions_on_rectangular_canvas(turns, direction, word):
    image = np.ascontiguousarray(np.rot90(render(INDEPENDENT,104,140), turns))
    description = DESCRIPTION.replace('nach links', 'nach '+word)
    check(image, description, direction)


@pytest.mark.parametrize('scale,color', [(.5,'#714b86'),(1,'#9b5035'),(2,'#315e94')])
def test_other_resolution_and_palette(scale, color):
    svg = INDEPENDENT.replace('width="104" height="140"', f'width="{104*scale:g}" height="{140*scale:g}"').replace('#28634c',color)
    check(render(svg, round(104*scale), round(140*scale)))


@pytest.mark.parametrize('description', [DESCRIPTION+' Schaft nach rechts.',
    DESCRIPTION.replace('nach links','nach rechts'), DESCRIPTION.replace('nach links',''),
    DESCRIPTION.replace('verbunden','getrennt'), DESCRIPTION+' Zusätzlich ein Punkt.'])
def test_direction_and_text_contradictions(description):
    assert fit(render(INDEPENDENT,104,140), description) is None


@pytest.mark.parametrize('change', ['missing_bar','missing_stem','dot','hole','flat'])
def test_topology_contradictions(change):
    svg = INDEPENDENT
    if change == 'missing_bar':
        svg = svg.replace('<rect x="61" y="16" width="18" height="110" fill="url(#bar)"/>','')
    elif change == 'missing_stem':
        svg = svg.replace('<polygon points="14,87 14,71 61,71 70,79 61,87" fill="url(#stem)"/>','')
    elif change == 'dot':
        svg = svg.replace('</svg>','<circle cx="25" cy="25" r="5" fill="#333333"/></svg>')
    elif change == 'hole':
        svg = svg.replace('</svg>','<rect x="24" y="73" width="12" height="12" fill="#ffffff"/></svg>')
    else:
        svg = svg.replace('#e6f2e8','#28634c')
    assert fit(render(svg,104,140)) is None


def test_invalid_render_and_error():
    image = render(INDEPENDENT,104,140)
    assert fit(image, render_fn=lambda *args: None) is None
    assert fit(image, error_fn=lambda *args: float('nan')) is None
    assert fit(np.full((24,32,3),np.nan)) is None


def test_saved_cli_evidence():
    report = evaluate(MANIFEST, EVIDENCE)
    assert all(c['satisfactory'] and not c['regressed_metrics'] for c in report['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for c in report['strict_pixel_gates'].values())
