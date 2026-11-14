"""Independent arrow geometry across wording, size, placement and JPEG noise."""
from pathlib import Path

import cv2
import pytest

from src.iCCModules.imageCompositeConverterArrowPair import fit_arrow_pair
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
from tools.review_conversion_quality import normalized_mse
from tools.run_plan_b_variations import render, measure_quality


DESCRIPTION = ('Röhren mit links roter und rechts blauer Seite; '
               'der linke Pfeil zeigt nach oben, der rechte Pfeil nach unten.')
CASES = [(24, 84, .7, 0., 0.), (30, 110, 1.1, .4, 1.2),
         (40, 140, 1.4, -.3, -1.5), (56, 190, 2., .7, 2.)]


def drawing(width, height, shaft, dx, dy):
    left, right = width*.2+dx, width*.8+dx
    top, bottom = height*.08+dy, height*.92+dy
    head_height, half = height*.09, max(3.5, width*.10)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            f'<rect x="{left-shaft/2}" y="{top}" width="{shaft}" height="{bottom-top-head_height/2}" fill="#df2422"/>'
            f'<polygon points="{left},{bottom-head_height} {left-half},{bottom} {left+half},{bottom}" fill="#df2422"/>'
            f'<rect x="{right-shaft/2}" y="{top}" width="{shaft}" height="{bottom-top-head_height/2}" fill="#2779b6"/>'
            f'<polygon points="{right},{bottom} {right-half},{bottom-head_height} {right+half},{bottom-head_height}" fill="#2779b6"/>'
            '</svg>')


@pytest.mark.parametrize('condition', CASES)
@pytest.mark.parametrize('jpeg', [False, True])
@pytest.mark.parametrize('noun', ['Röhren', 'Linien', 'Schäfte'])
@pytest.mark.parametrize('head', ['Pfeil', 'Dreieck'])
def test_independent_geometry_is_not_bound_to_catalog_wording(condition, jpeg, noun, head):
    width, height, *_ = condition
    image = render(drawing(*condition), width, height)
    if jpeg:
        ok, encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        assert ok
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    description = DESCRIPTION.replace('Röhren', noun).replace('Pfeil', head)
    _, params = Reflection({'neutral': description}).parse_description('neutral', 'neutral.png')
    assert params['mode'] == 'dual_arrow_badge'
    result = fit_arrow_pair(width, height, description=description, image=image, render_fn=render,
                            error_fn=lambda a, b: normalized_mse(a, b)[0])
    assert result is not None, (condition, jpeg, noun)
    validate_svg_assertions(result['svg'], params['language_assertions'])
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('size', ['L', 'M', 'S'])
def test_exact_catalog_description_reaches_model_and_checks_sample_heads(size):
    root = Path(__file__).resolve().parents[1]
    description = (root/'tests/fixtures/descriptions/arrow_pair_tubes_catalog.txt').read_text(encoding='utf-8')
    # Replace catalogue names as well: they must not select the geometry.
    description = description.replace('AC0030', 'neutral')
    image = cv2.imread(str(root/f'artifacts/images_to_convert/AC0030_{size}.jpg'))
    height, width = image.shape[:2]
    _, params = Reflection({'neutral': description}).parse_description('neutral', 'neutral.png')
    assert params['mode'] == 'dual_arrow_badge'
    result = fit_arrow_pair(width, height, description=description, image=image, render_fn=render,
                            error_fn=lambda a, b: normalized_mse(a, b)[0])
    assert result is not None
    validate_svg_assertions(result['svg'], params['language_assertions'])
    assert measure_quality(image, result['svg'])['satisfactory']
    assert len(description_assertions(description)['arrow_heads']) == 2


@pytest.mark.parametrize('description', [
    DESCRIPTION.replace('links roter', 'links blauer'),
    DESCRIPTION.replace('rechts blauer', 'rechts roter'),
    DESCRIPTION+' Der linke Pfeil zeigt nach unten.',
    DESCRIPTION+' Der rechte Pfeil zeigt nach oben.',
])
def test_flexible_wording_still_rejects_contradictory_relations(description):
    image = render(drawing(*CASES[2]), 40, 140)
    assert fit_arrow_pair(40, 140, description=description, image=image, render_fn=render,
                          error_fn=lambda a, b: normalized_mse(a, b)[0]) is None


@pytest.mark.parametrize('fault', ['missing_head', 'extra_mark'])
def test_weak_shaft_recovery_cannot_excuse_missing_or_extra_objects(fault):
    from xml.etree import ElementTree as ET
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    root = ET.fromstring(drawing(*CASES[0]))
    if fault == 'missing_head':
        root.remove(root[3])
    else:
        ET.SubElement(root, 'rect', x='10', y='35', width='4', height='4', fill='#777777')
    image = render(ET.tostring(root, encoding='unicode'), 24, 84)
    image = cv2.imdecode(cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])[1], cv2.IMREAD_COLOR)
    assert fit_arrow_pair(24, 84, description=DESCRIPTION, image=image, render_fn=render,
                          error_fn=lambda a, b: normalized_mse(a, b)[0]) is None


def test_quoted_pair_wording_cannot_select_the_arrow_model():
    _, params = Reflection({'neutral': 'Ein Rechteck mit Beschriftung "'+DESCRIPTION+'".'}).parse_description('neutral', 'neutral.png')
    assert params['mode'] != 'dual_arrow_badge'
