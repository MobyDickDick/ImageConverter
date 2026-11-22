"""Native polygon strokes must close just like their browser-rendered paths."""
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterRendering import (
    _close_polygons_for_fitz, render_svg_to_numpy_inprocess,
)


def render(svg):
    return render_svg_to_numpy_inprocess(svg,100,80,fitz_module=fitz,np_module=np,cv2_module=cv2)


@pytest.mark.parametrize('points', ['50,10 15,70 85,70', '85,70 15,70 50,10',
                                   '10,10 90,10 50,40 90,70 10,70'])
@pytest.mark.parametrize('fill', ['none','#cccccc','url(#paint)'])
def test_every_contour_edge_matches_an_explicitly_closed_path(points,fill):
    prefix=('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="80">'
            '<defs><linearGradient id="paint"><stop offset="0" stop-color="#eeeeee"/>'
            '<stop offset="1" stop-color="#999999"/></linearGradient></defs>')
    suffix=f' fill="{fill}" stroke="#333333" stroke-width="4" stroke-linejoin="round"/></svg>'
    polygon=prefix+f'<polygon points="{points}"'+suffix
    # Construct an independent explicit path rather than relying on the adapter.
    pairs=points.split()
    path=prefix+'<path d="M '+' L '.join(pair.replace(',',' ') for pair in pairs)+' Z"'+suffix
    actual,expected=render(polygon),render(path)
    assert actual is not None and expected is not None
    assert np.mean(np.square(actual.astype(float)-expected.astype(float)))/255**2 < .0001
    if fill!='url(#paint)':
        assert np.array_equal(actual,expected)


def test_only_private_polygon_input_is_changed_and_polylines_stay_open():
    svg='<svg xmlns="http://www.w3.org/2000/svg"><polygon points="+1e1,.5 20,5 10,20" id="x"/><polyline points="1,1 2,2 3,1"/></svg>'
    root=ET.fromstring(_close_polygons_for_fitz(svg))
    assert root.find('{*}path').get('d').endswith(' Z')
    assert root.find('{*}path').get('id')=='x'
    assert root.find('{*}polyline') is not None
    assert '<polygon ' in svg


@pytest.mark.parametrize('points',['1,2 3','1,2 bad 3,4','1,2 3,4 NaN,8'])
def test_invalid_points_are_left_to_the_svg_reader(points):
    svg=f'<svg><polygon points="{points}"/></svg>'
    assert _close_polygons_for_fitz(svg)==svg
