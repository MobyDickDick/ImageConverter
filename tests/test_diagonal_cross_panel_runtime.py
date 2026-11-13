from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import pytest

from src.iCCModules.imageCompositeConverterDiagonalCrossPanel import fit_diagonal_cross_panel
from tools.review_conversion_quality import normalized_mse
from tools.run_plan_b_variations import measure_quality, render

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Stehendes rotes Rechteck mit dunkelrotem Rand und Kreuz oben links, '
               'Diagonale von unten links nach oben rechts mit dunkler Mittellinie '
               'und zwei weißen Seitenlinien, am Rechteck abgeschnitten.')
NS = {'s': 'http://www.w3.org/2000/svg'}


def drawing(width=40, height=80, color='#e52d40', *, cross=True, diagonal=True):
    return (f'<svg xmlns="{NS["s"]}" width="{width}" height="{height}" viewBox="0 0 40 80">'
            '<defs><clipPath id="clip"><rect x="1.5" y="1.5" width="37" height="77"/></clipPath></defs>'
            '<rect width="40" height="80" fill="#d78b99"/>'
            f'<rect x="1.5" y="1.5" width="37" height="77" fill="{color}"/>'
            '<g clip-path="url(#clip)">'
            + ('<path d="M 38 0 L 2 80" stroke="#eadfe8" stroke-width="3"/>'
               '<path d="M 38 0 L 2 80" stroke="#76596a" stroke-width="1.1"/>' if diagonal else '')
            + ('<path d="M 13 6 V 16 M 8 11 H 18" stroke="#7e4652" stroke-width="2.5"/>' if cross else '')
            + '</g><rect x="1.5" y="1.5" width="37" height="77" fill="none" '
              'stroke="#a13f59" stroke-width="1.3"/></svg>')


def fit(image, description=DESCRIPTION, **kwargs):
    height, width = image.shape[:2]
    return fit_diagonal_cross_panel(width, height, description=description, image=image,
        render_fn=kwargs.get('render_fn', render),
        error_fn=kwargs.get('error_fn', lambda a,b: normalized_mse(a,b)[0]))


def assert_inventory(svg):
    root = ET.fromstring(svg)
    group = root.find('s:g', NS)
    clip = root.find('s:defs/s:clipPath', NS)
    assert group.get('clip-path') == f'url(#{clip.get("id")})'
    boundary = clip.find('s:rect', NS)
    frame = root.findall('s:rect', NS)[-1]
    assert all(boundary.get(k) == frame.get(k) for k in ('x', 'y', 'width', 'height'))
    lines = group.findall('s:path', NS)
    assert len(lines) == 2 and lines[0].get('d') == lines[1].get('d')
    assert float(lines[0].get('stroke-width')) > float(lines[1].get('stroke-width')) > 0
    cross = group.findall('s:polygon', NS)[-1]
    assert len(cross.get('points').split()) == 12
    assert not root.findall('.//s:image', NS)


@pytest.mark.parametrize('width,height,color', [(30,60,'#e52d40'), (40,80,'#c83945'), (60,120,'#ed343a')])
def test_independent_sizes_and_colors_keep_cross_and_clipped_three_part_diagonal(width, height, color):
    image = render(drawing(width, height, color), width, height)
    result = fit(image)
    assert result is not None
    assert measure_quality(image, result['svg'])['satisfactory']
    assert_inventory(result['svg'])


def test_pixelated_catalog_jpeg_passes_with_user_description():
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC100_1_M.jpg'))
    description = ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml').find(
        ".//entry[@key='AC100_1_M']/beschreibung").text
    result = fit(image, description)
    assert result is not None
    assert measure_quality(image, result['svg'])['satisfactory']
    assert_inventory(result['svg'])


@pytest.mark.parametrize('cross,diagonal', [(False,True), (True,False), (False,False)])
def test_missing_observed_components_are_rejected(cross, diagonal):
    assert fit(render(drawing(cross=cross, diagonal=diagonal),40,80)) is None


@pytest.mark.parametrize('description', [DESCRIPTION.replace('unten links', 'unten rechts'),
    DESCRIPTION.replace('Kreuz oben links', 'Kreuz unten rechts'), DESCRIPTION+' ohne Mittellinie',
    DESCRIPTION+' kein Kreuz', 'Rotes Rechteck mit heller Diagonale'])
def test_incomplete_or_contradictory_descriptions_are_rejected(description):
    assert fit(render(drawing(),40,80),description) is None


def test_failed_renderer_and_nonfinite_error_cannot_be_accepted():
    image = render(drawing(),40,80)
    assert fit(image,render_fn=lambda *args: None) is None
    assert fit(image,error_fn=lambda *args:float('nan')) is None
