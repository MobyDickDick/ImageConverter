"""Unchanged independent pixels must certify thin sides as well as total area."""
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from tools.evaluate_clipped_rectangular_parent import parent_regions
from tools.evaluate_layered_scene import check_objects, local_checks
from tools.run_plan_b_variations import render, sha256

CONTROLS = Path(__file__).parents[1]/'fixtures'/'clipped_side_renderer'
CASES = json.loads((CONTROLS/'manifest.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['case_id'])
def test_frozen_subpixel_sides_corners_and_native_objects(case):
    data = (CONTROLS/case['case_id']/'input'/(case['case_id']+'.png')).read_bytes()
    vector = (CONTROLS/case['reference_svg']).read_bytes()
    assert sha256(data) == case['input_sha256']
    assert sha256(vector) == case['reference_svg_sha256']
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    svg = vector.decode('utf-8')
    assert check_objects(svg, case['expected_objects'])['passed']
    corners, sides = parent_regions(case)
    regions = case['expected_objects']+sides+[c for c in corners if c['visibility'] != 'hidden']
    assert all(q['passed'] for q in local_checks(image, svg, regions))


@pytest.mark.parametrize('transformed', [False, True])
def test_sharp_subpixel_stroke_preserves_integrated_coverage(transformed):
    # An independently calculable outer edge on a white background: coverage
    # .98 of a #d2d2d2 stroke must leave 211, rather than snap to 210 or 255.
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32">
    <defs><linearGradient id="g"><stop stop-color="#404040"/>
    <stop offset="1" stop-color="#808080"/></linearGradient></defs>
    <rect x="5.52" y="5.52" width="20" height="20" fill="url(#g)"
    stroke="#d2d2d2" stroke-width="3"/></svg>'''
    if transformed:
        from xml.etree import ElementTree as ET
        root = ET.fromstring(svg)
        root.set('viewBox', '100 100 64 64')
        shape = root[-1]
        root.remove(shape)
        ET.SubElement(root, '{http://www.w3.org/2000/svg}g',
                      transform='translate(100 100) scale(2)').append(shape)
        svg = ET.tostring(root, encoding='unicode')
    raster = render(svg, 32, 32)
    np.testing.assert_array_equal(raster[15, 4], [211, 211, 211])
    np.testing.assert_array_equal(raster[15, 5], [210, 210, 210])
    np.testing.assert_array_equal(raster[15, 3], [255, 255, 255])
