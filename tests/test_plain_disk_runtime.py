"""Tiny outlined disks retain native geometry without filename-based recipes."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterPlainDisk import fit_plain_disk
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search
from tools.run_plan_b_variations import render, measure_quality, make_variations

DESCRIPTION = 'Grauer Kreis mit grauem Rand und hellgrauem Hintergrund'
ROOT = Path(__file__).resolve().parents[1]
WORKBENCH_SOURCE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">'
    '<rect width="20" height="20" fill="#fefefe"/>'
    '<circle cx="10.0000" cy="9.9299" r="8.9788" stroke-width="1.2000" '
    'fill="#f2f2f2" stroke="#949494"/></svg>'
)


def fit(image, description=DESCRIPTION):
    h, w = image.shape[:2]
    return fit_plain_disk(w, h, description=description, image=image, render_fn=render,
                          error_fn=lambda a, b: float(np.mean((a.astype(float)-b.astype(float))**2)))


@pytest.mark.parametrize('size', ['S', 'M', 'L'])
def test_catalog_jpeg_rings_pass_unchanged_pixel_gates(size):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/AC0800_{size}.jpg'))
    original = image.copy()
    with search_configuration(mode='portfolio', seed=42, adaptive=True,
                              minimum_seconds=0, seconds=5, max_seconds=5):
        with configured_image_search('neutral-upload'):
            result = fit(image)
    assert result is not None
    assert measure_quality(image, result['svg'])['satisfactory']
    tags = [node.tag.rsplit('}', 1)[-1] for node in ET.fromstring(result['svg']).iter()]
    assert tags == ['svg', 'rect', 'circle']
    np.testing.assert_array_equal(image, original)


def synthetic(size, body='', *, fill='#ebf1ed', stroke='#525e58', cx=.46, cy=.53, radius=.32):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
            f'<rect width="{size}" height="{size}" fill="white"/>'
            f'<circle cx="{size*cx}" cy="{size*cy}" r="{size*radius}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{max(.8,size*.025)}"/>'
            f'{body}</svg>')


@pytest.mark.parametrize('size,fill,stroke', [
    (20, '#f2f2f2', '#7f7f7f'), (40, '#ebf1ed', '#525e58'),
    (80, '#d4e5f6', '#345678'), (48, '#f2ded8', '#815e43'),
])
def test_independent_sizes_poses_and_colors(size, fill, stroke):
    image = render(synthetic(size, fill=fill, stroke=stroke), size, size)
    result = fit(image, 'Ein unbeschrifteter Kreis mit Rand.')
    assert result is not None
    assert measure_quality(image, result['svg'])['satisfactory']
    circle = ET.fromstring(result['svg']).find('{http://www.w3.org/2000/svg}circle')
    assert abs(float(circle.get('cx'))-size*.46) < .7
    assert abs(float(circle.get('cy'))-size*.53) < .7
    assert abs(float(circle.get('r'))-size*.32) < .7


@pytest.mark.parametrize('extra', [
    ' Text im Kreis: "VOC".', ' und eine Linie', ' mit Verlauf',
    ' und ein Rechteck', ' mit Griff', ' ohne Rand', ' mit einem Punkt',
])
def test_additional_description_content_is_not_erased(extra):
    assert fit(render(synthetic(40), 40, 40), DESCRIPTION+extra) is None


@pytest.mark.parametrize('pose', ['', ' Die Darstellung ist etwas größer dargestellt und leicht nach rechts und unten verschoben.'])
@pytest.mark.parametrize('body', [
    '<rect x="18" y="19" width="2" height="2" fill="#333333"/>',
    '<line x1="18" y1="17" x2="18" y2="23" stroke="#333333"/>',
    '<circle cx="37" cy="3" r="1" fill="#333333"/>',
])
def test_small_unmentioned_details_cannot_be_certified_as_plain_circle(body, pose):
    assert fit(render(synthetic(40, body), 40, 40), DESCRIPTION + pose) is None


def test_rectangle_is_not_replaced_with_circle():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
           '<rect width="40" height="40" fill="white"/>'
           '<rect x="5" y="5" width="30" height="30" fill="#f2f2f2" '
           'stroke="#7f7f7f" stroke-width="1"/></svg>')
    assert fit(render(svg, 40, 40)) is None


@pytest.mark.parametrize('seed', [8019332433889847450, 47021])
def test_expanded_plan_b_pose_descriptions_keep_circle_model(seed):
    # Tight, subpixel ring and an independent colour/pose holdout. The fitter
    # receives only the raster and the full, unmodified variant description.
    source = WORKBENCH_SOURCE if seed == 8019332433889847450 else synthetic(48)
    for case in make_variations(source, DESCRIPTION, seed, expand_canvas=True):
        image = render(case['svg'], case['width'], case['height'])
        result = fit(image, case['description'])
        assert result is not None, case['case_id']
        assert measure_quality(image, result['svg'])['satisfactory'], case['case_id']
        tags = [node.tag.rsplit('}', 1)[-1] for node in ET.fromstring(result['svg']).iter()]
        assert tags == ['svg', 'rect', 'circle']


@pytest.mark.parametrize('extra', [' Text im Kreis: "VOC".', ' und ein Rechteck', ' mit einem Punkt'])
@pytest.mark.parametrize('before_pose', [False, True])
def test_pose_sentence_does_not_hide_additional_content(extra, before_pose):
    pose = ' Die Darstellung ist etwas größer dargestellt und leicht nach rechts und unten verschoben.'
    description = DESCRIPTION + (extra + pose if before_pose else pose + extra)
    assert fit(render(synthetic(40), 40, 40), description) is None
