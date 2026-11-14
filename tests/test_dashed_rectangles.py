"""A dashed SVG rect must remain dashed in the private production renderer."""
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterDashedRectangles import normalize_dashed_rectangles,normalize_dashed_lines
from tools.run_plan_b_variations import render
from tools.evaluate_svg_text_baseline import render_librsvg


def rectangle(pattern='5 3',offset=0,extra='',inherited=False):
    attrs=f'stroke="#666666" stroke-width="2" stroke-dasharray="{pattern}" stroke-dashoffset="{offset}"'
    body=f'<rect x="10" y="10" width="60" height="80" fill="none" {extra} '+('' if inherited else attrs)+'/>'
    if inherited:
        body=f'<g {attrs}>{body}</g>'
    return '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="100"><rect width="80" height="100" fill="white"/>'+body+'</svg>'


@pytest.mark.parametrize('pattern,offset',[('5 3',0),('5 3',1),('5 3',-2.3),('5 3',9),
                                        ('5 3 2',0),('4 2',3),('500 3',0)])
@pytest.mark.parametrize('inherited',[False,True])
def test_perimeter_phase_corners_and_closed_seam_match_independent_renderer(pattern,offset,inherited):
    svg=rectangle(pattern,offset,inherited=inherited)
    normalized=normalize_dashed_rectangles(svg)
    reference=render_librsvg(svg,80,100)
    # Independent evaluation of both the normalized vectors and the actual
    # production raster catches direction/phase/seam mistakes in expansion.
    for raster in [render_librsvg(normalized,80,100),render(svg,80,100)]:
        assert np.square(reference.astype(float)-raster).mean()/255**2 < .00004
    assert '<image' not in normalized
    assert 'stroke-dasharray="'+pattern+'"' in svg


def test_visible_gaps_are_retained_in_the_saved_svg_and_production_pixels():
    svg=rectangle()
    raster=render(svg,80,100)
    assert raster[10,11,0] < 150
    assert raster[10,16,0] == 255
    assert 'stroke-dasharray="5 3"' in svg


@pytest.mark.parametrize('pattern,extra',[('0 0',''),('-1 2',''),('.00001 1',''),('1% 2',''),
                                       ('5 3','rx="2"'),('5 3','stroke-linecap="round"'),
                                       ('5 3','pathLength="100"')])
def test_unhandled_semantics_and_expansion_overflow_are_left_untouched(pattern,extra):
    svg=rectangle(pattern,extra=extra)
    assert normalize_dashed_rectangles(svg)==svg


@pytest.mark.parametrize('points',[(10,10,70,10),(10,10,10,90),(10,85,70,15),(70,15,10,85)])
@pytest.mark.parametrize('offset',[0,1.3,-2.6])
def test_horizontal_vertical_oblique_and_reversed_dashed_rays(points,offset):
    x,y,X,Y=points
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="80" height="100">'
         '<rect width="80" height="100" fill="white"/>'
         f'<g stroke="#777777" stroke-width="1.2" stroke-dasharray="2.1 1.3" stroke-dashoffset="{offset}">'
         f'<line x1="{x}" y1="{y}" x2="{X}" y2="{Y}"/></g></svg>')
    reference=render_librsvg(svg,80,100)
    for raster in [render_librsvg(normalize_dashed_lines(svg),80,100),render(svg,80,100)]:
        assert np.square(reference.astype(float)-raster).mean()/255**2 < .00006
