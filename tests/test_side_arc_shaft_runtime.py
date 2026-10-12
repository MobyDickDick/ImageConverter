"""Independent geometry and rejection contracts for a left-opening arc/shaft."""
from pathlib import Path
import json
import re
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterArcShaft import fit_arc_shaft
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.imageCompositeConverter import Action
from tools.evaluate_side_arc_shaft_recheck import symbol_semantics
from tools.run_plan_b_variations import make_variations, measure_quality

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/side_arc_shaft_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg, w, h, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION, **kwargs):
    h, w = image.shape[:2]
    return fit_arc_shaft(w, h, description=description, image=image,
                         render_fn=kwargs.get('render_fn', render),
                         error_fn=kwargs.get('error_fn', Action.calculateError))


def independent_svg(scale=1, shift=0, color='#375c66', rx=19, ry=24, stroke=5):
    cy = 35+shift
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{130*scale}" height="{80*scale}">'
            f'<defs><linearGradient id="g" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{color}"/>'
            f'<stop offset="0.5" stop-color="#dcecef"/><stop offset="1" stop-color="{color}"/></linearGradient></defs>'
            f'<rect width="{130*scale}" height="{80*scale}" fill="#ffffff"/>'
            f'<path d="M {12*scale} {(cy+ry)*scale} A {rx*scale} {ry*scale} 0 0 0 {12*scale} {(cy-ry)*scale}" '
            f'fill="none" stroke="{color}" stroke-width="{stroke*scale}"/>'
            f'<rect x="{42*scale}" y="{(cy-10)*scale}" width="{75*scale}" height="{20*scale}" fill="url(#g)"/></svg>')


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_catalog_rasters_anonymous_bounded_and_unchanged(case):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['source']))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error'] <= result['initial_error']
    assert measure_quality(image, result['svg'])['satisfactory']
    assert symbol_semantics(result['svg']) == 1
    assert result['evaluations'] <= 2+16*(15+21)
    assert '<image' not in result['svg'] and 'transform=' not in result['svg']
    assert result['opening'] == 'left'
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('scale,shift,color,rx,ry,stroke', [
    (1,0,'#375c66',19,24,5), (1,9,'#753627',24,19,4),
    (2,-3,'#265438',16,25,6), (.5,0,'#694882',19,24,5)])
def test_independent_geometry_color_position_resolution(scale,shift,color,rx,ry,stroke):
    svg = independent_svg(scale,shift,color,rx,ry,stroke)
    assert symbol_semantics(svg) == 1
    image = render(svg,int(130*scale),int(80*scale))
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('case', make_variations(independent_svg(), DESCRIPTION, 20261012),
                         ids=lambda case: case['case_id'])
def test_independent_fractional_pixel_phases(case):
    image = render(case['svg'], case['width'], case['height'])
    result = fit(image, case['description'])
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']
    assert result['error'] <= result['initial_error']
    assert result['evaluations'] <= 2+16*(15+21)


@pytest.mark.parametrize('failure', ['render','nan','infinity','pixels'])
def test_failed_measurements_are_rejected(failure):
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


@pytest.mark.parametrize('description', ['', 'Ein Quadrat.', DESCRIPTION+' Zusätzlich ein Punkt.',
    DESCRIPTION.replace('links offen','rechts offen'), DESCRIPTION+' Ein oben offener Bogen.',
    DESCRIPTION.replace('links neben','rechts neben'), DESCRIPTION.replace('vertikal','horizontal')])
def test_wrong_or_conflicting_description_is_rejected(description):
    assert fit(render(independent_svg(),130,80), description) is None


@pytest.mark.parametrize('change', ['missing_arc','missing_shaft','extra_dot','flat_gradient',
    'shifted_shaft','closed_circle','square_u','opposite_arc','broken_arc'])
def test_wrong_raster_topologies_are_rejected(change):
    source = independent_svg()
    if change == 'missing_arc':
        source = re.sub(r'<path[^>]*/>', '', source)
    elif change == 'missing_shaft':
        source = source.replace('<rect x="42" y="25" width="75" height="20" fill="url(#g)"/>','')
    elif change == 'extra_dot':
        source = source.replace('</svg>','<circle cx="70" cy="65" r="4" fill="#333333"/></svg>')
    elif change == 'flat_gradient':
        source = source.replace('#dcecef','#375c66')
    elif change == 'shifted_shaft':
        source = source.replace('y="25"','y="39"')
    elif change == 'closed_circle':
        source = source.replace('M 12 59 A 19 24 0 0 0 12 11','M 12 59 A 19 24 0 0 0 12 11 A 19 24 0 0 0 12 59')
    elif change == 'square_u':
        source = source.replace('M 12 59 A 19 24 0 0 0 12 11','M 12 59 L 31 59 L 31 11 L 12 11')
    elif change == 'opposite_arc':
        source = source.replace('0 0 0 12 11','0 0 1 12 11')
    elif change == 'broken_arc':
        source = source.replace('</svg>','<rect x="27" y="31" width="10" height="8" fill="#ffffff"/></svg>')
    assert fit(render(source,130,80)) is None


@pytest.mark.parametrize('change', ['missing_arc','extra_object','inverted','nan','horizontal_gradient'])
def test_saved_vector_semantic_checker_rejects_invalid_output(change):
    svg = independent_svg()
    if change == 'missing_arc':
        svg = re.sub(r'<path[^>]*/>', '', svg)
    elif change == 'extra_object':
        root = ET.fromstring(svg)
        ET.SubElement(root, '{http://www.w3.org/2000/svg}circle', cx='70', cy='65', r='4')
        svg = ET.tostring(root, encoding='unicode')
    elif change == 'inverted':
        svg = svg.replace('0 0 0 ', '0 0 1 ')
    elif change == 'horizontal_gradient':
        svg = svg.replace('x1="0" y1="1" x2="0" y2="0"','x1="0" y1="0" x2="1" y2="0"')
    else:
        svg = svg.replace('stroke-width="', 'stroke-width="nan')
    assert symbol_semantics(svg) == 0
