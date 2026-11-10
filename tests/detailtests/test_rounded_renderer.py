"""Rounded SVG geometry is bound to analytic areas and frozen librsvg pixels."""
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterRendering as rendering
from tools.evaluate_layered_scene import local_checks
from tools.run_plan_b_variations import measure_quality, render, sha256

FIXTURES = Path(__file__).resolve().parents[1]/'fixtures/rounded_renderer'


@pytest.mark.parametrize('visible', range(5))
def test_at_least_two_unoccluded_corners_still_supply_the_radius(visible):
    from src.iCCModules.imageCompositeConverterMixedGradientScene import _exposed_corner_radius

    data = cv2.imread(str(FIXTURES/'rounded_00.png')).astype(float)
    coverage = (255-data[:, :, 0])/170
    foreign = np.zeros(coverage.shape, dtype=bool)
    corners = [(x, y) for x in (30, 285) for y in (40, 275)]
    for x, y in corners[visible:]:
        foreign[y:y+45, x:x+45] = True
    radius = _exposed_corner_radius(data, np.full_like(data, 255.), np.full(3, 85.),
        coverage, [30, 40, 300, 280], foreign_mask=foreign)
    if visible < 2:
        assert radius is None
    else:
        assert radius is not None and abs(radius-30) < .2


@pytest.mark.parametrize('radius', [3., 12., 30., 60.])
@pytest.mark.parametrize('scale', [1, 2])
def test_solid_rounding_matches_analytic_quarter_circle_area(radius, scale):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="360" height="360">'
           '<rect width="360" height="360" fill="white"/>'
           f'<rect x="30" y="40" width="300" height="280" rx="{radius}" fill="#555555"/></svg>')
    raster = render(svg, 360*scale, 360*scale)
    coverage = (255-raster[:, :, 0].astype(float))/170
    extent = int(radius+5)*scale
    deficit = np.sum(1-coverage[40*scale:40*scale+extent, 30*scale:30*scale+extent])/scale**2
    assert abs(deficit-(1-np.pi/4)*radius**2) < max(1.5, radius*.08)


@pytest.mark.parametrize('attributes,rx,ry', [
    ('rx="30"', 30, 30), ('ry="20"', 20, 20),
    ('rx="20" ry="35"', 20, 35), ('rx="500" ry="500"', 100, 60)])
@pytest.mark.parametrize('transform,scale', [('', 1.), ('translate(6.375 4.625) scale(1.25)', 1.25)])
def test_ellipse_copying_clamping_and_transforms_preserve_analytic_area(attributes, rx, ry, transform, scale):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">'
           '<rect width="400" height="300" fill="white"/>'
           f'<g transform="{transform}"><rect x="30.375" y="40.625" width="200" height="120" '
           f'{attributes} fill="#555555"/></g></svg>')
    coverage = (255-render(svg, 400, 300)[:, :, 0].astype(float))/170
    ideal = (200*120-(4-np.pi)*rx*ry)*scale**2
    assert abs(coverage.sum()-ideal) < ideal*.0006


@pytest.mark.parametrize('index', range(28))
def test_frozen_independent_pixels_pass_global_and_all_local_gates(index):
    case = json.loads((FIXTURES/'manifest.json').read_text(encoding='utf-8'))['cases'][index]
    name = case['case_id']
    svg, png = (FIXTURES/(name+'.svg')).read_bytes(), (FIXTURES/(name+'.png')).read_bytes()
    assert sha256(svg) == case['svg_sha256']
    assert sha256(png) == case['png_sha256']
    reference = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
    assert measure_quality(reference, svg.decode())['satisfactory']
    assert all(q['passed'] for q in local_checks(reference, svg.decode(), case['corners']))


def test_rounded_correction_also_reaches_subprocess_worker():
    from src.iCCModules.imageCompositeConverterRenderWorker import RenderWorker
    svg = (FIXTURES/'rounded_00.svg').read_text(encoding='utf-8')
    worker = RenderWorker()
    try:
        actual = worker.render(svg, 380, 360, np_module=np, timeout_sec=15)
    finally:
        worker.close()
    assert actual is not None
    assert np.array_equal(actual, render(svg, 380, 360))


@pytest.mark.parametrize('attributes', [
    'rx="30"', 'ry="30"', 'rx="300" ry="400"', 'rx="20px" ry="10px"'])
def test_private_geometry_keeps_paint_transform_id_and_source_untouched(attributes):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="160">'
           f'<rect id="shape" x="5" y="6" width="100" height="80" {attributes} '
           'fill="#123456" stroke="#abcdef" stroke-width="3" transform="translate(2 3)"/></svg>')
    rewritten = rendering._normalize_rounded_rectangles_for_fitz(svg)
    path = ET.fromstring(rewritten)[0]
    assert path.tag.rsplit('}', 1)[-1] == 'path'
    assert path.get('id') == 'shape'
    assert path.get('fill') == '#123456'
    assert path.get('stroke') == '#abcdef'
    assert path.get('transform') == 'translate(2 3)'
    assert 'rx' in svg or 'ry' in svg
    assert ET.fromstring(svg)[0].tag.endswith('rect')


@pytest.mark.parametrize('attributes', [
    '', 'rx="0"', 'rx="20" ry="0"', 'rx="-1"', 'rx="nan"', 'rx="10%"',
    'rx="calc(2px)"', 'rx="20" width="0"', 'rx="20" width="10%"'])
def test_sharp_invalid_or_unresolved_geometry_is_left_untouched(attributes):
    # Override width explicitly without duplicate XML attributes.
    width = '' if 'width=' in attributes else 'width="100"'
    svg = f'<svg xmlns="http://www.w3.org/2000/svg"><rect {width} height="80" {attributes}/></svg>'
    assert rendering._normalize_rounded_rectangles_for_fitz(svg) == svg


def test_non_rounded_primitives_keep_their_previous_native_pixels():
    for name in ('sharp', 'circle', 'ellipse', 'bezier'):
        svg = (FIXTURES/(name+'.svg')).read_text(encoding='utf-8')
        with fitz.open(stream=svg.encode(), filetype='svg') as doc:
            pix = doc[0].get_pixmap(alpha=False)
            original = cv2.cvtColor(np.frombuffer(pix.samples, np.uint8).reshape(360, 380, 3), cv2.COLOR_RGB2BGR)
        assert np.array_equal(original, render(svg, 380, 360))
