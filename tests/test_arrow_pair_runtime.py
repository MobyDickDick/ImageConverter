from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterArrowPair import fit_arrow_pair
from src.iCCModules.imageCompositeConverterDualArrowRuntime import runDualArrowBadgeIterationImpl
from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles
from tools.run_plan_b_variations import render, measure_quality, make_original_case, make_variations
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('size', ['L', 'M', 'S'])
def test_bottom_arrow_user_wording_reaches_native_fit(size):
    from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions
    description = (ROOT/'tests/fixtures/descriptions/arrow_pair_bottom_user.txt').read_text(encoding='utf-8-sig')
    _, params = Reflection({'neutral': description}).parse_description('neutral', 'neutral.png')
    assert params['mode'] == 'dual_arrow_badge'
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/AC0030_{size}.jpg'))
    h, w = image.shape[:2]
    result = fit_arrow_pair(w, h, description=description, image=image, render_fn=render,
                            error_fn=lambda a,b: normalized_mse(a,b)[0])
    assert result is not None
    validate_svg_assertions(result['svg'], params['language_assertions'])
    assert measure_quality(image, result['svg'])['satisfactory']
    assert len(list(ET.fromstring(result['svg']))) == 4


def test_jpeg_tip_fragment_keeps_red_crossbar_and_opposite_heads():
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions, validate_svg_assertions
    description = (ROOT/'tests/fixtures/descriptions/arrow_pair_red_crossbar_user.txt').read_text(encoding='utf-8')
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0026.jpg'))
    h, w = image.shape[:2]
    fitted = fit_arrow_pair(w, h, description=description, image=image, render_fn=render,
                            error_fn=lambda a, b: normalized_mse(a, b)[0])
    assert fitted is not None
    svg = fitted['svg']
    validate_svg_assertions(svg, description_assertions(description))
    assert measure_quality(image, svg)['satisfactory']
    nodes = list(ET.fromstring(svg))
    assert [e.tag.rsplit('}', 1)[-1] for e in nodes] == ['rect', 'polygon', 'rect', 'polygon', 'rect']
    for index, down in ((0, False), (2, True)):
        shaft, head = nodes[index:index+2]
        points = np.array([float(v) for v in head.get('points').replace(',', ' ').split()]).reshape(3, 2)
        assert bool(points[0, 1] > points[1, 1]) == down
        assert abs(points[:, 0].mean()-(float(shaft.get('x'))+float(shaft.get('width'))/2)) < 1
    assert nodes[-1].get('fill') == nodes[2].get('fill')
    assert h*.5 < float(nodes[-1].get('y')) < h*.75
    # A colored fragment away from the head is not JPEG ringing and cannot
    # be silently omitted, even at the same rows as the tolerated tip fragment.
    image[101:103, 15:20] = (170, 90, 30)
    assert fit_arrow_pair(w, h, description=description, image=image, render_fn=render,
                          error_fn=lambda a, b: normalized_mse(a, b)[0]) is None


DESCRIPTION = ('Zwei vertikale Striche: links rot, rechts blau. Unten links ein rotes Dreieck '
               'mit Spitze nach oben, unten rechts ein blaues Dreieck mit Spitze nach unten. '
               'Im unteren Drittel verbindet eine rote horizontale Linie die Striche.')

# User wording from the failing conversion, including punctuation and typo.
USER_DESCRIPTION = ('zwei vertikale Striche links rot, rechts, blau, unten links Dreieck rot '
                    'links Spitze nach oben, rechtes Dreieck rechts blau, Spitze nach untten, '
                    'unteres Drittel rote horizontale Linie.')

SUBJECT_DESCRIPTION = ('Es sind zwei vertikale Linien und zwei Dreiecke.\n'
                       'Die linke Linie und das linke Dreieck ist rot.\n'
                       'Die rechte Linie und das rechte Dreick ist blau.\n'
                       'Das linke Dreiek zeigt nach oben.\n'
                       'Das rechte Dreieck zeigt nach unten.')


def test_centered_user_description_selects_triangles_and_blue_crossbar():
    from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions
    description = (ROOT/'tests/fixtures/descriptions/arrow_pair_centered_user.txt').read_text(encoding='utf-8').strip()
    _, params = Reflection({'neutral': description}).parse_description('neutral', 'neutral.png')
    assert params['mode'] == 'dual_arrow_badge'
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0025.jpg'))
    height, width = image.shape[:2]
    result = fit_arrow_pair(width, height, description=description, image=image,
                           render_fn=render, error_fn=lambda a,b: normalized_mse(a,b)[0])
    assert result is not None
    validate_svg_assertions(result['svg'], params['language_assertions'])
    assert measure_quality(image, result['svg'])['satisfactory']
    nodes = list(ET.fromstring(result['svg']))
    assert [e.tag.rsplit('}',1)[-1] for e in nodes] == ['rect', 'polygon', 'rect', 'polygon', 'rect']
    for index, down in enumerate((False, True)):
        shaft, head = nodes[index*2:index*2+2]
        points = np.array([float(v) for v in head.get('points').replace(',', ' ').split()]).reshape(3,2)
        assert bool(points[0,1] > points[1,1]) == down
        center = float(shaft.get('x'))+float(shaft.get('width'))/2
        assert abs(center-points[:,0].mean()) < .5
    assert nodes[-1].get('fill') == nodes[0].get('fill')


@pytest.mark.parametrize('original,replacement', [
    ('Spitz gegen oben', 'Spitz gegen unten'),
    ('Spitz nach unten', 'Spitz nach oben'),
    ('horizontale blaue Linie', 'horizontale rote Linie'),
    ('linke Linie ist blau', 'linke Linie ist rot'),
])
def test_centered_user_description_does_not_ignore_contradictions(original, replacement):
    description = (ROOT/'tests/fixtures/descriptions/arrow_pair_centered_user.txt').read_text(encoding='utf-8')
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0025.jpg'))
    height, width = image.shape[:2]
    assert fit_arrow_pair(width, height, description=description.replace(original, replacement),
                          image=image, render_fn=render, error_fn=lambda a,b: normalized_mse(a,b)[0]) is None


def test_triangle_subject_wording_dispatches_and_keeps_four_native_primitives():
    from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import (
        DescriptionRejected, validate_svg_assertions,
    )
    _, params = Reflection({'neutral': SUBJECT_DESCRIPTION}).parse_description('neutral', 'neutral.png')
    assert params['mode'] == 'dual_arrow_badge'
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0024.jpg'))
    h, w = image.shape[:2]
    outputs = []

    def forbidden(*args, **kwargs):
        pytest.fail('subject wording must reach the observed primitive fit')

    result = runDualArrowBadgeIterationImpl(
        perc_img=image, filename='neutral.png', base_name='neutral', description=SUBJECT_DESCRIPTION,
        params=params, width=w, height=h,
        detect_dual_arrow_badge_params_fn=forbidden, generate_dual_arrow_badge_svg_fn=forbidden,
        render_embedded_raster_svg_fn=forbidden, write_validation_log_fn=lambda lines: None,
        render_svg_to_numpy_fn=render, record_render_failure_fn=forbidden,
        write_attempt_artifacts_fn=lambda svg, raster: outputs.append(svg),
        calculate_error_fn=lambda a, b: normalized_mse(a, b)[0])
    assert result and len(outputs) == 1
    svg = outputs[0]
    validate_svg_assertions(svg, params['language_assertions'])
    assert measure_quality(image, svg)['satisfactory']
    nodes = list(ET.fromstring(svg))
    assert [e.tag.rsplit('}', 1)[-1] for e in nodes] == ['rect', 'polygon', 'rect', 'polygon']
    for index, (color, down) in enumerate((('blue', True), ('red', False))):
        shaft, head = nodes[index*2:index*2+2]
        assert shaft.get('fill') == head.get('fill')
        rgb = [int(head.get('fill')[i:i+2], 16) for i in (1, 3, 5)]
        assert (rgb[2] > rgb[0]) == (color == 'blue')
        points = np.array([float(v) for v in head.get('points').replace(',', ' ').split()]).reshape(3, 2)
        assert bool(points[0, 1] > points[1, 1]) == down
    assert float(nodes[2].get('x')) < float(nodes[0].get('x'))
    root = ET.fromstring(svg)
    root.remove(root[1])
    with pytest.raises(DescriptionRejected, match='object_count:triangle:2:1'):
        validate_svg_assertions(ET.tostring(root, encoding='unicode'), params['language_assertions'])


@pytest.mark.parametrize('description', [
    SUBJECT_DESCRIPTION.replace('ist rot', 'ist blau'),
    SUBJECT_DESCRIPTION.replace('ist blau', 'ist rot'),
    SUBJECT_DESCRIPTION.replace('zeigt nach oben', 'zeigt nach unten'),
    SUBJECT_DESCRIPTION.replace('zeigt nach unten', 'zeigt nach oben'),
    SUBJECT_DESCRIPTION + ' Das linke Dreieck zeigt nach unten.',
])
def test_triangle_subject_wording_rejects_color_and_direction_conflicts(description):
    assert fit(drawing(bar=False), description) is None


def drawing(*, red='#e62320', blue='#226ebc', dx=0, extra='', same_direction=False, bar=True):
    right = '80,128 73,144 87,144' if same_direction else '73,128 87,128 80,144'
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="150">'
            f'<g transform="translate({dx} 0)">'
            f'<rect x="19.1" y="8" width="1.8" height="124" fill="{red}"/>'
            f'<polygon points="20,128 13,144 27,144" fill="{red}"/>'
            f'<rect x="79.1" y="8" width="1.8" height="124" fill="{blue}"/>'
            f'<polygon points="{right}" fill="{blue}"/>'
            + (f'<rect x="20" y="90.3" width="60" height="1.8" fill="{red}"/>' if bar else '')
            + '</g>'+extra+'</svg>')


def fit(svg, description=DESCRIPTION, **kwargs):
    return fit_arrow_pair(100, 150, description=description, image=render(svg, 100, 150),
                          render_fn=kwargs.get('render_fn', render),
                          error_fn=kwargs.get('error_fn', lambda a,b: normalized_mse(a,b)[0]))


@pytest.mark.parametrize('red,blue,dx', [('#e62320','#226ebc',0), ('#b52d35','#12628e',3.3)])
def test_native_inventory_generalizes_colors_and_positions(red, blue, dx):
    svg = drawing(red=red, blue=blue, dx=dx)
    result = fit(svg)
    assert result is not None
    assert result['evaluations'] < 1000
    assert measure_quality(render(svg,100,150),result['svg'])['satisfactory']
    root = ET.fromstring(result['svg'])
    assert [e.tag.rsplit('}',1)[-1] for e in root] == ['rect','polygon','rect','polygon','rect']
    polygons = [e for e in root if e.tag.endswith('polygon')]
    # Native triangles retain opposite directions and independent sides.
    tips = []
    for polygon in polygons:
        points = [list(map(float, pair.split(','))) for pair in polygon.get('points').split()]
        assert len(points) == 3
        tips.append(points[0][1] > points[1][1])
    assert tips == [True, False]  # geometry is enumerated blue, red


@pytest.mark.parametrize('kind', ['missing_bar','same_direction','extra','wrong_color','wrong_direction','wrong_bar'])
def test_incomplete_or_contradictory_inventory_is_rejected(kind):
    svg = drawing(bar=kind!='missing_bar', same_direction=kind=='same_direction',
                  extra='<circle cx="50" cy="35" r="4" fill="#222222"/>' if kind=='extra' else '')
    description = DESCRIPTION
    if kind == 'wrong_color':
        description = description.replace('links rot, rechts blau','links blau, rechts rot')
    if kind == 'wrong_direction':
        description = description.replace('Spitze nach oben','Spitze nach unten')
    if kind == 'wrong_bar':
        description = description.replace('rote horizontale','blaue horizontale')
    assert fit(svg,description) is None


def test_failed_renderer_and_nonfinite_error_are_rejected():
    assert fit(drawing(),render_fn=lambda *args:None) is None
    assert fit(drawing(),error_fn=lambda *args:float('nan')) is None


def test_runtime_names_do_not_change_geometry_or_read_vectors():
    image = render(drawing(),100,150)
    outputs = []
    def forbidden(*args, **kwargs):
        pytest.fail('native fit must not need the legacy fallback or reference vectors')
    for name in ('foreign_name', 'unrelated'):
        artifacts, logs, params = [], [], {}
        result = runDualArrowBadgeIterationImpl(perc_img=image, filename=name+'.png',base_name=name,
            description=DESCRIPTION,params=params,width=100,height=150,
            detect_dual_arrow_badge_params_fn=forbidden,generate_dual_arrow_badge_svg_fn=forbidden,
            render_embedded_raster_svg_fn=forbidden,write_validation_log_fn=logs.append,
            render_svg_to_numpy_fn=render,record_render_failure_fn=forbidden,
            write_attempt_artifacts_fn=lambda svg,raster:artifacts.append(svg),
            calculate_error_fn=lambda a,b:normalized_mse(a,b)[0])
        assert result and 'raster_arrow_pair_v1' in params
        assert logs == [['status=dual_arrow_observed_primitives']]
        outputs.extend(artifacts)
    assert outputs[0] == outputs[1]


def test_stylesheet_cascade_matches_independently_authored_native_svg():
    styled = ('<svg xmlns="http://www.w3.org/2000/svg" width="50" height="40">'
        '<style>rect {fill:#111111} .paint {fill:#ff0000} rect.paint {fill:#00ff00}'
        '#chosen {fill:#0000ff} .line {stroke:#aa2222;stroke-width:2}</style>'
        '<rect id="chosen" class="paint" x="5" y="5" width="15" height="20"/>'
        '<path class="line" d="M 30,5 V 25"/></svg>')
    explicit = ('<svg xmlns="http://www.w3.org/2000/svg" width="50" height="40">'
        '<rect x="5" y="5" width="15" height="20" fill="#0000ff"/>'
        '<path d="M 30,5 V 25" stroke="#aa2222" stroke-width="2"/></svg>')
    np.testing.assert_array_equal(render(styled,50,40),render(explicit,50,40))


def test_css_important_source_order_inline_and_inheritance():
    svg = ('<svg><style>.a {fill:red !important}.a {fill:blue !important}'
           '.a {stroke:black}</style><g class="a"><rect class="a" '
           'style="fill:green;stroke:red !important"/><circle class="a" '
           'style="fill:yellow !important"/></g></svg>')
    group = ET.fromstring(inline_simple_svg_styles(svg)).find('g')
    assert group.get('fill') == 'blue'
    assert group[0].get('fill') == 'blue'
    assert group[0].get('stroke') == 'red'
    assert group[1].get('fill') == 'yellow'


@pytest.mark.parametrize('svg', ['<svg><style>.a > rect {fill:red}</style></svg>',
    '<svg><style>@media screen {.a {fill:red}}</style></svg>', '<svg><style>broken', '<svg/>'])
def test_unsupported_styles_or_invalid_xml_are_not_partially_rewritten(svg):
    assert inline_simple_svg_styles(svg) == svg


def test_real_source_retains_stems_and_catalog_description_matches_observed_sides():
    svg = (ROOT/'artifacts/samples/AC0022.svg').read_text(encoding='utf-8')
    image = render(svg,35,112)
    # Independent locations established from the visible source drawing.
    assert image[30,5,2] > image[30,5,0]+100
    assert image[30,29,0] > image[30,29,2]+100
    description = ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml').find(
        ".//entry[@key='AC0022']/beschreibung").text
    assert description == DESCRIPTION
    assert fit_arrow_pair(35,112,description=description,image=image,render_fn=render,
                         error_fn=lambda a,b:normalized_mse(a,b)[0]) is not None


def test_original_catalog_jpeg_is_an_independent_raster_holdout():
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0022.jpg'))
    result = fit_arrow_pair(image.shape[1],image.shape[0],description=DESCRIPTION,image=image,
                            render_fn=render,error_fn=lambda a,b:normalized_mse(a,b)[0])
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']


@pytest.mark.parametrize('description', [USER_DESCRIPTION, USER_DESCRIPTION.replace('untten', 'unten')])
def test_user_punctuation_and_typo_keep_both_catalog_triangle_heads(description):
    from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions
    text, params = Reflection({'neutral': description}).parse_description('neutral', 'neutral.png')
    assert params['mode'] == 'dual_arrow_badge'
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0022.jpg'))
    height, width = image.shape[:2]
    result = fit_arrow_pair(width, height, description=description, image=image,
                            render_fn=render, error_fn=lambda a,b: normalized_mse(a,b)[0])
    assert result is not None
    validate_svg_assertions(result['svg'], params['language_assertions'])
    assert measure_quality(image, result['svg'])['satisfactory']
    polygons = [e for e in ET.fromstring(result['svg']) if e.tag.endswith('polygon')]
    assert len(polygons) == 2
    # Blue/right points down; red/left points up, independently of text order.
    points = [np.array([float(v) for v in e.get('points').replace(',', ' ').split()]).reshape(3, 2)
              for e in polygons]
    assert points[0][0, 1] > points[0][1, 1]
    assert points[1][0, 1] < points[1][1, 1]
    assert points[1][:, 0].mean() < points[0][:, 0].mean()
    # A filled thin rectangle is an exactly horizontal line, not a fitted
    # diagonal. It must bridge the shafts in the lower portion of the image.
    bar = list(ET.fromstring(result['svg']))[-1]
    assert bar.tag.endswith('rect')
    assert float(bar.get('width')) > 3*float(bar.get('height')) > 0
    assert height*.5 < float(bar.get('y')) < height*.75
    assert float(bar.get('x')) < points[1][:, 0].mean()+2
    assert float(bar.get('x'))+float(bar.get('width')) > points[0][:, 0].mean()-2
    red, green, blue = (int(bar.get('fill')[i:i+2], 16) for i in (1, 3, 5))
    assert red > max(green, blue)+30


@pytest.mark.parametrize('description', [
    USER_DESCRIPTION.replace('links rot', 'links, blau'),
    USER_DESCRIPTION + ' Links, Spitze nach untten.',
    USER_DESCRIPTION + ' Rechts, Spitze nach oben.',
])
def test_tolerant_user_wording_still_rejects_contradictions(description):
    assert fit(drawing(), description) is None


@pytest.mark.parametrize('size', ['L', 'M', 'S'])
def test_thin_jpeg_shafts_keep_native_fit_instead_of_legacy_fallback(size):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/AC0020_{size}.jpg'))
    description = ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml').find(
        ".//entry[@key='AC0020']/beschreibung").text
    height, width = image.shape[:2]
    outputs, params = [], {}

    def forbidden(*args, **kwargs):
        pytest.fail('an accurate thin-shaft fit must not fall back to normalized geometry')

    result = runDualArrowBadgeIterationImpl(
        perc_img=image, filename='neutral.png', base_name='neutral', description=description,
        params=params, width=width, height=height,
        detect_dual_arrow_badge_params_fn=forbidden, generate_dual_arrow_badge_svg_fn=forbidden,
        render_embedded_raster_svg_fn=forbidden, write_validation_log_fn=lambda lines: None,
        render_svg_to_numpy_fn=render, record_render_failure_fn=forbidden,
        write_attempt_artifacts_fn=lambda svg, raster: outputs.append(svg),
        calculate_error_fn=lambda a, b: normalized_mse(a, b)[0])

    assert result and 'raster_arrow_pair_v1' in params
    quality = measure_quality(image, outputs[0])
    assert quality['satisfactory'], quality
    assert quality['complexity']['vector_element_count'] == 4
    assert quality['complexity']['embedded_raster_count'] == 0


WORKBENCH_DESCRIPTION = ('zwei vertikale Striche links blau, rechts, rot, unten Dreiecke blau rot, '
                         'links Spitze nach unten, rechts Spitze nach oben')
WORKBENCH_SOURCE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="30" height="110" viewBox="0 0 30 110">'
    '<rect x="4.495054" y="0.000000" width="1.035315" height="108.963981" fill="#2477b4"/>'
    '<polygon points="5.000000,110.515152 1.161310,102.562500 8.838690,102.562500" fill="#2477b4"/>'
    '<rect x="24.635673" y="0.000000" width="0.862745" height="102.127247" fill="#ea0707"/>'
    '<polygon points="24.968750,102.112391 20.623682,110.875000 29.313818,110.875000" fill="#ea0707"/>'
    '</svg>'
)


@pytest.mark.parametrize('case', [make_original_case(WORKBENCH_SOURCE, WORKBENCH_DESCRIPTION),
    *make_variations(WORKBENCH_SOURCE, WORKBENCH_DESCRIPTION, 3309169791913111074, expand_canvas=True)],
    ids=lambda case: case['case_id'])
def test_workbench_translations_keep_native_thin_arrow_pair(case):
    image = render(case['svg'], case['width'], case['height'])
    outputs, params = [], {}

    def forbidden(*args, **kwargs):
        pytest.fail('whole-motif translation must not force the legacy arrow fallback')

    result = runDualArrowBadgeIterationImpl(
        perc_img=image, filename='unrelated.png', base_name='unrelated', description=case['description'],
        params=params, width=case['width'], height=case['height'],
        detect_dual_arrow_badge_params_fn=forbidden, generate_dual_arrow_badge_svg_fn=forbidden,
        render_embedded_raster_svg_fn=forbidden, write_validation_log_fn=lambda lines: None,
        render_svg_to_numpy_fn=render, record_render_failure_fn=forbidden,
        write_attempt_artifacts_fn=lambda svg, raster: outputs.append(svg),
        calculate_error_fn=lambda a, b: normalized_mse(a, b)[0])

    assert result and 'raster_arrow_pair_v1' in params
    quality = measure_quality(image, outputs[0])
    assert quality['satisfactory'], quality
    assert quality['complexity']['vector_element_count'] == 4
    assert quality['complexity']['embedded_raster_count'] == 0


@pytest.mark.parametrize('side,direction', [('links', 'oben'), ('rechts', 'unten')])
@pytest.mark.parametrize('before_pose', [False, True])
def test_translation_does_not_hide_contradictory_head_directions(side, direction, before_pose):
    pose = ' Das Motiv ist etwas kleiner dargestellt und leicht nach links und unten verschoben.'
    contradiction = f'; {side} Spitze nach {direction}'
    description = WORKBENCH_DESCRIPTION + (contradiction + pose if before_pose else pose + contradiction)
    assert fit_arrow_pair(30, 110, description=description, image=render(WORKBENCH_SOURCE, 30, 110),
                          render_fn=render, error_fn=lambda a, b: normalized_mse(a, b)[0]) is None
