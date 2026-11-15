"""The raster fit must preserve both full diagonals and two distinct stacked marks."""
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
import cv2

from tests.test_crossed_gradient_panel_runtime import drawing,fit
from tools.run_plan_b_variations import render,measure_quality,make_original_case,make_variations
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration,configured_image_search

ROOT = Path(__file__).resolve().parents[1]
SVG = (ROOT/'tests/fixtures/stacked_panel_workbench.svg').read_text(encoding='utf-8')
DESCRIPTION = (ROOT/'tests/fixtures/descriptions/stacked_panel_workbench_user.txt').read_text(encoding='utf-8').strip()
SMALL_SVG = (ROOT/'tests/fixtures/stacked_panel_small_workbench.svg').read_text(encoding='utf-8')
SMALL_DESCRIPTION = (ROOT/'tests/fixtures/descriptions/stacked_panel_small_workbench_user.txt').read_text(encoding='utf-8').strip()
medium = ET.fromstring(SMALL_SVG)
medium.set('width','26'); medium.set('height','52')
MEDIUM_SVG = ET.tostring(medium,encoding='unicode')
NS = {'s':'http://www.w3.org/2000/svg'}


def assert_marks(svg):
    root = ET.fromstring(svg)
    group = root.find('s:g',NS)
    diagonals = group.findall('s:polygon',NS)
    assert len(diagonals) == 2
    clip = root.find('s:defs/s:clipPath/s:rect',NS)
    left,top,width,height = [float(clip.get(k)) for k in ('x','y','width','height')]
    for diagonal in diagonals:
        points = [tuple(map(float,pair.split(','))) for pair in diagonal.get('points').split()]
        assert 4 <= len(points) <= 8
        assert all(left-1e-5 <= x <= left+width+1e-5 and top-1e-5 <= y <= top+height+1e-5 for x,y in points)
    minus,horizontal,vertical = group.findall('s:rect',NS)
    n = lambda e,k:float(e.get(k))
    assert n(minus,'y') > n(vertical,'y')+n(vertical,'height')
    assert abs(n(minus,'x')+n(minus,'width')/2-(n(horizontal,'x')+n(horizontal,'width')/2)) < 1.5
    assert n(horizontal,'width') > 2*n(horizontal,'height')
    assert n(vertical,'height') > 2*n(vertical,'width')
    assert root[-1].tag.endswith('rect') and root[-1].get('fill') == 'none'
    assert not root.findall('.//s:image',NS)


@pytest.mark.parametrize('case',[make_original_case(SVG,DESCRIPTION),*make_variations(SVG,DESCRIPTION,984378060012931142,expand_canvas=True)],ids=lambda c:c['case_id'])
def test_workbench_original_and_all_variants_keep_cross_and_stacked_signs(case):
    image = render(case['svg'],case['width'],case['height'])
    result = fit(image,case['description'])
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']
    assert result['details']['passed']
    assert result['details']['plus_mse'] < .02 and result['details']['minus_mse'] < .02
    assert_marks(result['svg'])


@pytest.mark.parametrize('case',[
    make_original_case(SMALL_SVG,SMALL_DESCRIPTION),*make_variations(SMALL_SVG,SMALL_DESCRIPTION,7388058509807368710,expand_canvas=True),
    make_original_case(MEDIUM_SVG,SMALL_DESCRIPTION),*make_variations(MEDIUM_SVG,SMALL_DESCRIPTION,7388058509807368710,expand_canvas=True),
],ids=lambda c:f"{c['width']}x{c['height']}-{c['case_id']}")
def test_small_and_medium_workbench_keep_separate_marks_at_every_subpixel_offset(case):
    image = render(case['svg'],case['width'],case['height'])
    # Exercise the bounded portfolio used by the real CLI. Quantized border
    # placement can require a second search direction after coordinate descent.
    with search_configuration(mode='portfolio',adaptive=True,seed=7388058509807368710,
                              budget=384,seconds=10,max_seconds=10,minimum_seconds=10):
        with configured_image_search('small-panel-registration'):
            result = fit(image,case['description'],error_fn=lambda a,b:float(cv2.absdiff(a,b).mean()))
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']
    assert result['details']['passed']
    assert_marks(result['svg'])


def independent(plus=True,minus=True,swapped=False,second=True):
    svg = drawing(minus=False,second=second)
    py,my = (17,8) if swapped else (8,17)
    marks = (f'<path d="M 16 {py} H 24 M 20 {py-4} V {py+4}" stroke="#606060" stroke-width="2"/>' if plus else '')
    marks += (f'<rect x="16" y="{my}" width="8" height="2" fill="#606060"/>' if minus else '')
    return svg.replace('</g>',marks+'</g>')


@pytest.mark.parametrize('kwargs',[dict(plus=False),dict(minus=False),dict(swapped=True),dict(second=False)])
@pytest.mark.parametrize('width,height',[(20,40),(26,52),(40,80)])
def test_missing_or_swapped_marks_and_missing_diagonal_are_rejected(kwargs,width,height):
    assert fit(render(independent(**kwargs),width,height),DESCRIPTION) is None


@pytest.mark.parametrize('width,height',[(20,40),(26,52),(32,64),(48,96),(60,120)])
def test_independent_native_paths_and_different_sizes(width,height):
    image = render(independent(),width,height)
    result = fit(image,DESCRIPTION)
    assert result is not None
    assert_marks(result['svg'])
