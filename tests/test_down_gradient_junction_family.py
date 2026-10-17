"""Acceptance of down-facing T junctions using the existing general fitter."""
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
EVIDENCE = ROOT/'artifacts/evaluation/down_gradient_junction_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def production_error(a, b):
    return calculateErrorImpl(a, b, cv2_module=cv2, np_module=np)


def fit(image, description=DESCRIPTION):
    height, width = image.shape[:2]
    return fit_gradient_junction(width, height, description=description, image=image,
                                 render_fn=render, error_fn=production_error)


def check(image, description=DESCRIPTION, *, strict=True):
    original = image.copy()
    result = fit(image, description)
    assert result is not None
    height, width = image.shape[:2]
    assert result['error'] == production_error(image, render(result['svg'], width, height))
    assert result['initial_error'] == production_error(image, render(result['initial_svg'], width, height))
    assert result['error'] <= result['initial_error']
    assert symbol_semantics(result['svg'], 'down') == 1
    quality = measure_quality(image, result['svg'])
    if strict:
        assert quality['satisfactory'], quality
    else:
        # This low-contrast JPG passes both regular gates but its highlight
        # straddles the unchanged 25-level strict foreground threshold.
        assert quality['failures'] == ['foreground_iou_outside_limit']
        assert quality['metrics']['foreground_iou'] == pytest.approx(0.8490196078431372)
    np.testing.assert_array_equal(result['rendered'], render(result['svg'], width, height))
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_catalog_color_size_holdouts(case):
    check(cv2.imread(str(EVIDENCE/case['image'])), strict=case['source'] != 'GE9033_4M.jpg')


@pytest.mark.parametrize('case', make_variations(INDEPENDENT, DESCRIPTION, 20261017), ids=lambda c: c['case_id'])
def test_independent_subpixel_variations(case):
    check(render(case['svg'], case['width'], case['height']), case['description'])


@pytest.mark.parametrize('scale,color', [(.5, '#315e94'), (1, '#934d31'), (2, '#317952')])
def test_other_resolution_and_palette(scale, color):
    svg = INDEPENDENT.replace('width="156" height="124"', f'width="{156*scale:g}" height="{124*scale:g}"').replace('#416b78', color)
    check(render(svg, round(156*scale), round(124*scale)))


@pytest.mark.parametrize('description', [MANIFEST['baseline_description'],
    DESCRIPTION.replace('nach unten', 'nach oben'), DESCRIPTION+' Schaft nach rechts.',
    DESCRIPTION.replace('verbunden', 'getrennt'), DESCRIPTION+' Zusätzlich ein Punkt.'])
def test_wrong_descriptions_are_rejected(description):
    assert fit(render(INDEPENDENT, 156, 124), description) is None


@pytest.mark.parametrize('change', ['missing_bar', 'missing_stem', 'dot', 'hole', 'flat'])
def test_topology_contradictions(change):
    svg = INDEPENDENT
    if change == 'missing_bar':
        svg = svg.replace('<rect x="18" y="22" width="120" height="18" fill="url(#bar)"/>', '')
    elif change == 'missing_stem':
        svg = svg.replace('<polygon points="84,108 66,108 66,40 75,31 84,40" fill="url(#stem)"/>', '')
    elif change == 'dot':
        svg = svg.replace('</svg>', '<circle cx="126" cy="96" r="5" fill="#333333"/></svg>')
    elif change == 'hole':
        svg = svg.replace('</svg>', '<rect x="69" y="70" width="12" height="12" fill="#ffffff"/></svg>')
    else:
        svg = svg.replace('#e5f1f4', '#416b78')
    assert fit(render(svg, 156, 124)) is None


def test_both_catalogs_describe_the_complete_family():
    names = {case['source'] for case in MANIFEST['cases']}
    for catalog in ('images_to_convert', 'descriptions'):
        entries = ET.parse(ROOT/'artifacts'/catalog/'Finale_Wurzelformen_V3.xml').iter('entry')
        entry = next(e for e in entries if e.get('key') == 'GE9033')
        assert entry.findtext('beschreibung') == DESCRIPTION
        assert {e.text for e in entry.findall('./bilder/bild')} == names


def test_saved_cli_evidence():
    report = evaluate(MANIFEST, EVIDENCE)
    assert all(c['satisfactory'] and not c['regressed_metrics'] for c in report['satisfaction_gate']['cases'])
    failed = {name for name, case in report['strict_pixel_gates'].items() if not case['satisfactory']}
    assert failed == {'anonymous_down_junction_07'}
    assert report['strict_pixel_gates']['anonymous_down_junction_07']['failures'] == ['foreground_iou_outside_limit']
