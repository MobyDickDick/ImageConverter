from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterRendering import _resolve_local_gradient_references
from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles
from tools.run_plan_b_variations import render, make_original_case, _make_variation_candidates

ROOT = Path(__file__).resolve().parents[2]


def test_inline_paint_and_stop_styles_without_stylesheet():
    svg = '<svg><rect fill="#ffffff" style="fill:#112233;stroke:none"/></svg>'
    rect = ET.fromstring(inline_simple_svg_styles(svg))[0]
    assert rect.get('fill') == '#112233' and rect.get('stroke') == 'none'
    assert rect.get('style') is None


@pytest.mark.parametrize('href', ['href', 'xlink:href'])
@pytest.mark.parametrize('reverse', [False, True])
def test_independent_chained_gradient_inheritance_and_translated_coordinates(href, reverse):
    low, high = (30, 10) if reverse else (10, 30)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
      width="80" height="60" viewBox="0 0 80 60">
      <defs><linearGradient id="palette"><stop offset="0" style="stop-color:#204080;stop-opacity:1"/>
      <stop offset="1" style="stop-color:#e08040;stop-opacity:1"/></linearGradient>
      <linearGradient id="axis" {href}="#palette" gradientUnits="userSpaceOnUse"
       x1="0" x2="0" y1="{low}" y2="{high}"/>
      <linearGradient id="paint" {href}="#axis"/></defs>
      <g transform="translate(4 5) scale(1.2)"><rect x="10" y="10" width="40" height="20"
       style="fill:url(#paint);stroke:none"/></g></svg>'''
    raster = render(svg, 80, 60)
    rows = np.arange(20, 37)
    t = np.clip(((rows + .5 - 5) / 1.2 - low) / (high - low), 0, 1)
    expected = (1-t[:, None])*[128, 64, 32] + t[:, None]*[64, 128, 224]
    assert np.max(abs(raster[rows, 35].astype(float) - expected)) <= 3
    assert np.all(raster[:16] == 255)


def test_own_stops_and_href_precedence():
    svg = '''<svg xmlns:xlink="http://www.w3.org/1999/xlink"><defs>
    <linearGradient id="a" x1=".25"><stop offset="0" stop-color="#112233"/></linearGradient>
    <linearGradient id="b" x1=".75"><stop offset="0" stop-color="#445566"/></linearGradient>
    <linearGradient id="c" href="#a" xlink:href="#b" x2=".9"><stop offset="1" stop-color="#abcdef"/></linearGradient>
    </defs></svg>'''
    c = ET.fromstring(_resolve_local_gradient_references(svg))[0][2]
    assert c.get('x1') == '.25' and c.get('x2') == '.9'
    assert len(c) == 1 and c[0].get('stop-color') == '#abcdef'


@pytest.mark.parametrize('references', [
    'id="a" href="#a"', 'id="a" href="https://example.invalid/paint.svg#g"',
    'id="a" href="#missing"',
])
def test_invalid_or_external_reference_is_not_followed(references):
    svg = f'<svg><linearGradient {references}/></svg>'
    assert _resolve_local_gradient_references(svg) == svg


def test_cyclic_gradient_reference_is_not_rewritten():
    svg = '<svg><linearGradient id="a" href="#b"/><linearGradient id="b" href="#a"/></svg>'
    assert _resolve_local_gradient_references(svg) == svg


def test_frozen_source_and_transform_controls_are_pink_not_black():
    svg = (ROOT / 'artifacts/samples/z_201.svg').read_text(encoding='utf-8')
    cases = [make_original_case(svg, 'Rechteck'), *_make_variation_candidates(svg, 'Rechteck', 347146220485913939)]
    for case in cases:
        raster = render(case['svg'], case['width']*10, case['height']*10)
        # The rectangle is horizontally uniform and has a light upper and
        # darker lower pink zone. Check the center away from clipping edges.
        column = raster[:, raster.shape[1]//2].astype(float)
        assert column[:, 2].min() > 180
        assert np.max(column[:, 2]-column[:, 1]) > 50
        assert column[:25, 1].max() > column[32:43, 1].min() + 35
