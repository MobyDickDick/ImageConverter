from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterArrowPair import fit_arrow_pair
from src.iCCModules.imageCompositeConverterDualArrowRuntime import runDualArrowBadgeIterationImpl
from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles
from tools.run_plan_b_variations import render, measure_quality
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Zwei vertikale Striche: links rot, rechts blau. Unten links ein rotes Dreieck '
               'mit Spitze nach oben, unten rechts ein blaues Dreieck mit Spitze nach unten. '
               'Im unteren Drittel verbindet eine rote horizontale Linie die Striche.')


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
