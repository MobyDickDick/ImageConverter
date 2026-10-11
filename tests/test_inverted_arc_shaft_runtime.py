"""Independent raster and negative contracts for a lower-opening arc/shaft."""
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
from tools.evaluate_inverted_arc_shaft_recheck import symbol_semantics
from tools.review_conversion_quality import normalized_mse
from tools.run_plan_b_variations import make_variations, measure_quality
from src.imageCompositeConverter import Action

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT/'artifacts/evaluation/inverted_arc_shaft_recheck_v1/manifest.json').read_text())
DESCRIPTION = MANIFEST['cases'][0]['description']


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg, w, h, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION, **kwargs):
    h, w = image.shape[:2]
    return fit_arc_shaft(w, h, description=description, image=image,
                         render_fn=kwargs.get('render_fn', render),
                         error_fn=kwargs.get('error_fn', Action.calculateError))


def independent_svg(scale=1, shift=0, color='#375c66', rx=24, ry=19, stroke=5):
    cx = 35+shift
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{80*scale}" height="{130*scale}">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{color}"/>'
            f'<stop offset="0.5" stop-color="#dcecef"/><stop offset="1" stop-color="{color}"/></linearGradient></defs>'
            f'<rect width="{80*scale}" height="{130*scale}" fill="#ffffff"/>'
            f'<rect x="{(cx-10)*scale}" y="{13*scale}" width="{20*scale}" height="{75*scale}" fill="url(#g)"/>'
            f'<path d="M {(cx-rx)*scale} {118*scale} A {rx*scale} {ry*scale} 0 0 1 {(cx+rx)*scale} {118*scale}" '
            f'fill="none" stroke="{color}" stroke-width="{stroke*scale}"/></svg>')


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c:c['source'])
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
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('scale,shift,color,rx,ry,stroke', [
    (1,0,'#375c66',24,19,5), (1,9,'#753627',19,24,4),
    (2,-3,'#265438',25,16,6), (.5,0,'#694882',24,19,5)])
def test_independent_geometry_color_position_resolution(scale,shift,color,rx,ry,stroke):
    svg = independent_svg(scale,shift,color,rx,ry,stroke)
    assert symbol_semantics(svg) == 1
    image = render(svg,int(80*scale),int(130*scale))
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('case', make_variations(independent_svg(), DESCRIPTION, 20261011),
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
    image = render(independent_svg(),80,130)
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
    DESCRIPTION.replace('unten offen','oben offen'), DESCRIPTION+' Ein oben offener Bogen.',
    DESCRIPTION.replace('unter einem','über einem')])
def test_wrong_or_conflicting_description_is_rejected(description):
    assert fit(render(independent_svg(),80,130), description) is None


@pytest.mark.parametrize('change', ['missing_arc','missing_shaft','extra_dot','flat_gradient',
    'shifted_shaft','closed_circle','square_u','upward_arc','broken_arc'])
def test_wrong_raster_topologies_are_rejected(change):
    source = independent_svg()
    if change == 'missing_arc':
        source = re.sub(r'<path[^>]*/>', '', source)
    elif change == 'missing_shaft':
        source = source.replace('<rect x="25" y="13" width="20" height="75" fill="url(#g)"/>','')
    elif change == 'extra_dot':
        source = source.replace('</svg>','<circle cx="70" cy="20" r="4" fill="#333333"/></svg>')
    elif change == 'flat_gradient':
        source = source.replace('#dcecef','#375c66')
    elif change == 'shifted_shaft':
        source = source.replace('x="25"','x="39"')
    elif change == 'closed_circle':
        source = source.replace('M 11 118 A 24 19 0 0 1 59 118','M 11 118 A 24 19 0 0 1 59 118 A 24 19 0 0 1 11 118')
    elif change == 'square_u':
        source = source.replace('M 11 118 A 24 19 0 0 1 59 118','M 11 118 L 11 99 L 59 99 L 59 118')
    elif change == 'upward_arc':
        source = source.replace('0 0 1 59 118','0 0 0 59 118')
    elif change == 'broken_arc':
        source = source.replace('</svg>','<rect x="31" y="95" width="8" height="10" fill="#ffffff"/></svg>')
    assert fit(render(source,80,130)) is None


@pytest.mark.parametrize('change', ['missing_arc','extra_object','inverted','nan'])
def test_saved_vector_semantic_checker_rejects_invalid_output(change):
    result = fit(render(independent_svg(),80,130))
    svg = result['svg']
    if change == 'missing_arc':
        svg = re.sub(r'<[^>]*path[^>]*/>', '', svg)
    elif change == 'extra_object':
        root = ET.fromstring(svg)
        ET.SubElement(root, '{http://www.w3.org/2000/svg}circle', cx='70', cy='20', r='4')
        svg = ET.tostring(root, encoding='unicode')
    elif change == 'inverted':
        svg = svg.replace('0 0 1 ', '0 0 0 ')
    else:
        svg = svg.replace('stroke-width="', 'stroke-width="nan')
    assert symbol_semantics(svg) == 0
