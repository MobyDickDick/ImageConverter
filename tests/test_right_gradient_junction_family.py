"""Acceptance of right-facing T junctions using the existing general fitter."""
from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterGradientJunction import fit_gradient_junction
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from tools.evaluate_gradient_junction_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/right_gradient_junction_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def production_error(a, b):
    return calculateErrorImpl(a, b, cv2_module=cv2, np_module=np)


def fit(image, description=DESCRIPTION):
    height, width = image.shape[:2]
    return fit_gradient_junction(width, height, description=description, image=image,
                                 render_fn=render, error_fn=production_error)


def check(image, description=DESCRIPTION):
    original = image.copy()
    result = fit(image, description)
    assert result is not None
    height, width = image.shape[:2]
    assert result['error'] == production_error(image, render(result['svg'], width, height))
    assert result['initial_error'] == production_error(image, render(result['initial_svg'], width, height))
    assert result['error'] <= result['initial_error']
    assert symbol_semantics(result['svg'], 'right') == 1
    assert measure_quality(image, result['svg'])['satisfactory']
    np.testing.assert_array_equal(result['rendered'], render(result['svg'], width, height))
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_catalog_color_size_holdouts(case):
    check(cv2.imread(str(EVIDENCE/case['image'])))


@pytest.mark.parametrize('case', make_variations(INDEPENDENT, DESCRIPTION, 20261016), ids=lambda c: c['case_id'])
def test_independent_subpixel_variations(case):
    check(render(case['svg'], case['width'], case['height']), case['description'])


@pytest.mark.parametrize('scale,color', [(.5, '#315e94'), (1, '#934d31'), (2, '#317952')])
def test_other_resolution_and_palette(scale, color):
    svg = INDEPENDENT.replace('width="144" height="112"', f'width="{144*scale:g}" height="{112*scale:g}"').replace('#654179', color)
    check(render(svg, round(144*scale), round(112*scale)))


@pytest.mark.parametrize('description', [MANIFEST['baseline_description'],
    DESCRIPTION.replace('nach rechts', 'nach links'), DESCRIPTION+' Schaft nach unten.',
    DESCRIPTION.replace('verbunden', 'getrennt'), DESCRIPTION+' Zusätzlich ein Punkt.'])
def test_wrong_descriptions_are_rejected(description):
    assert fit(render(INDEPENDENT, 144, 112), description) is None


@pytest.mark.parametrize('change', ['missing_bar', 'missing_stem', 'dot', 'hole', 'flat'])
def test_topology_contradictions(change):
    svg = INDEPENDENT
    if change == 'missing_bar':
        svg = svg.replace('<rect x="24" y="14" width="16" height="84" fill="url(#bar)"/>', '')
    elif change == 'missing_stem':
        svg = svg.replace('<polygon points="119,49 119,65 40,65 32,57 40,49" fill="url(#stem)"/>', '')
    elif change == 'dot':
        svg = svg.replace('</svg>', '<circle cx="98" cy="20" r="5" fill="#333333"/></svg>')
    elif change == 'hole':
        svg = svg.replace('</svg>', '<rect x="70" y="51" width="12" height="12" fill="#ffffff"/></svg>')
    else:
        svg = svg.replace('#eee4f5', '#654179')
    assert fit(render(svg, 144, 112)) is None


def test_both_catalogs_describe_the_complete_family():
    names = {case['source'] for case in MANIFEST['cases']}
    for catalog in ('images_to_convert', 'descriptions'):
        entries = ET.parse(ROOT/'artifacts'/catalog/'Finale_Wurzelformen_V3.xml').iter('entry')
        entry = next(e for e in entries if e.get('key') == 'GE9032')
        assert entry.findtext('beschreibung') == DESCRIPTION
        assert {e.text for e in entry.findall('./bilder/bild')} == names


def test_saved_cli_evidence():
    report = evaluate(MANIFEST, EVIDENCE)
    assert all(c['satisfactory'] and not c['regressed_metrics'] for c in report['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for c in report['strict_pixel_gates'].values())
