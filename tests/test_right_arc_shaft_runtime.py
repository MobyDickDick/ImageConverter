"""Right-opening arc/shaft geometry, independent inputs and rejection contracts."""
from pathlib import Path
import json
import re

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterArcShaft import mirror_side_arc_shaft_svg
from tests.test_side_arc_shaft_runtime import fit as fit_side, render
from tools.evaluate_side_arc_shaft_recheck import symbol_semantics
from tools.run_plan_b_variations import make_variations, measure_quality

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/right_arc_shaft_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']


def fit(image, description=DESCRIPTION, **kwargs):
    return fit_side(image, description, **kwargs)


def independent_svg(scale=1, shift=0, color='#375c66', rx=19, ry=24, stroke=5):
    cy = 35+shift
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{130*scale}" height="{80*scale}">'
            f'<defs><linearGradient id="g" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{color}"/>'
            f'<stop offset="0.5" stop-color="#dcecef"/><stop offset="1" stop-color="{color}"/></linearGradient></defs>'
            f'<rect width="{130*scale}" height="{80*scale}" fill="#ffffff"/>'
            f'<path d="M {118*scale} {(cy+ry)*scale} A {rx*scale} {ry*scale} 0 0 1 {118*scale} {(cy-ry)*scale}" '
            f'fill="none" stroke="{color}" stroke-width="{stroke*scale}"/>'
            f'<rect x="{13*scale}" y="{(cy-10)*scale}" width="{75*scale}" height="{20*scale}" fill="url(#g)"/></svg>')


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_anonymous_catalog_rasters(case):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['source']))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error'] <= result['initial_error']
    assert measure_quality(image, result['svg'])['satisfactory']
    assert symbol_semantics(result['svg'], 'right') == 1
    assert result['opening'] == 'right'
    assert result['evaluations'] <= 2+16*(15+21)
    assert '<image' not in result['svg'] and 'transform=' not in result['svg']
    np.testing.assert_array_equal(image, original)
    np.testing.assert_array_equal(result['rendered'], render(result['svg'], image.shape[1], image.shape[0]))


@pytest.mark.parametrize('scale,shift,color,rx,ry,stroke', [
    (1,0,'#375c66',19,24,5), (1,9,'#753627',24,19,4),
    (2,-3,'#265438',16,25,6), (.5,0,'#694882',19,24,5)])
def test_independent_geometry(scale,shift,color,rx,ry,stroke):
    svg = independent_svg(scale,shift,color,rx,ry,stroke)
    assert symbol_semantics(svg, 'right') == 1
    image = render(svg,int(130*scale),int(80*scale))
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg'], 'right') == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('case', make_variations(independent_svg(), DESCRIPTION, 20261014), ids=lambda c:c['case_id'])
def test_fractional_phases(case):
    image = render(case['svg'], case['width'], case['height'])
    result = fit(image, case['description'])
    assert result is not None
    assert symbol_semantics(result['svg'], 'right') == 1
    assert measure_quality(image, result['svg'])['satisfactory']
    assert result['error'] <= result['initial_error']


@pytest.mark.parametrize('description', ['', 'Ein Quadrat.', DESCRIPTION+' Zusätzlich ein Punkt.',
    DESCRIPTION.replace('rechts offen','links offen'), DESCRIPTION+' Ein oben offener Bogen.',
    DESCRIPTION.replace('rechts neben','links neben'), DESCRIPTION.replace('vertikal','horizontal'),
    DESCRIPTION+' Ein links offener Bogen.', DESCRIPTION.replace('linker Halbkreis','rechter Halbkreis')])
def test_description_rejection(description):
    assert fit(render(independent_svg(),130,80), description) is None


@pytest.mark.parametrize('change', ['missing_arc','missing_shaft','extra_dot','flat_gradient',
    'shifted_shaft','closed_circle','square_u','opposite_arc','broken_arc'])
def test_topology_rejection(change):
    svg = independent_svg()
    if change == 'missing_arc':
        svg = re.sub(r'<path[^>]*/>', '', svg)
    elif change == 'missing_shaft':
        svg = svg.replace('<rect x="13" y="25" width="75" height="20" fill="url(#g)"/>','')
    elif change == 'extra_dot':
        svg = svg.replace('</svg>','<circle cx="70" cy="65" r="4" fill="#333333"/></svg>')
    elif change == 'flat_gradient':
        svg = svg.replace('#dcecef','#375c66')
    elif change == 'shifted_shaft':
        svg = svg.replace('y="25"','y="39"')
    elif change == 'closed_circle':
        svg = svg.replace('M 118 59 A 19 24 0 0 1 118 11','M 118 59 A 19 24 0 0 1 118 11 A 19 24 0 0 1 118 59')
    elif change == 'square_u':
        svg = svg.replace('M 118 59 A 19 24 0 0 1 118 11','M 118 59 L 99 59 L 99 11 L 118 11')
    elif change == 'opposite_arc':
        svg = svg.replace('0 0 1 118 11','0 0 0 118 11')
    elif change == 'broken_arc':
        svg = svg.replace('</svg>','<rect x="93" y="31" width="10" height="8" fill="#ffffff"/></svg>')
    assert fit(render(svg,130,80)) is None


@pytest.mark.parametrize('failure', ['render','nan','infinity','pixels'])
def test_measurement_rejection(failure):
    image = render(independent_svg(),130,80)
    kwargs = {}
    if failure == 'pixels':
        image = image.astype(float)
        image[0,0] = np.nan
    elif failure == 'render':
        kwargs['render_fn'] = lambda *args: None
    else:
        kwargs['error_fn'] = lambda *args: float('nan' if failure == 'nan' else 'inf')
    assert fit(image, **kwargs) is None


def test_direction_checker_and_reflection():
    svg = independent_svg()
    assert symbol_semantics(svg) == 0
    mirrored = mirror_side_arc_shaft_svg(svg)
    assert symbol_semantics(mirrored) == 1
    assert symbol_semantics(mirrored, 'right') == 0
    assert symbol_semantics(svg.replace('0 0 1 118', '0 0 0 118'), 'right') == 0
    assert symbol_semantics(svg.replace('stroke-width="5"', 'stroke-width="nan"'), 'right') == 0
    assert symbol_semantics(svg.replace('x1="0" y1="1" x2="0" y2="0"', 'x1="0" y1="0" x2="1" y2="0"'), 'right') == 0
    # MuPDF antialiasing is direction-dependent. Check an exact geometric
    # round trip; the fitter scores the directly rendered final orientation.
    np.testing.assert_array_equal(render(mirror_side_arc_shaft_svg(mirrored),130,80), render(svg,130,80))
