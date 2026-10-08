from __future__ import annotations

from src.iCCModules import imageCompositeConverterRendering as rendering
import pytest


def test_fitz_adapter_expands_gradient_without_changing_conversion_svg() -> None:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10">
      <defs><linearGradient id="g" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#101010"/>
        <stop offset="100%" stop-color="#f0f0f0"/>
      </linearGradient></defs>
      <rect x="2" y="1" width="16" height="8" fill="url(#g)" stroke="#777777"/>
    </svg>"""

    renderer_svg = rendering._expand_axis_aligned_linear_gradients_for_fitz(svg)

    assert '<linearGradient id="g"' in svg
    assert svg.count("<rect") == 1
    assert "url(#g)" not in renderer_svg
    assert renderer_svg.count("<rect") >= 16
    assert 'fill="none" stroke="#777777"' in renderer_svg


def test_fitz_adapter_leaves_non_gradient_svg_byte_for_byte_unchanged() -> None:
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect fill="#abcdef"/></svg>'

    assert rendering._expand_axis_aligned_linear_gradients_for_fitz(svg) == svg


@pytest.mark.parametrize('axis', [('100%', '0%'), ('0%', '100%')])
def test_linear_gradient_has_no_white_seams_and_preserves_rectangle_edges(axis):
    import cv2
    import fitz
    import numpy as np
    x2, y2 = axis
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="30" height="20">'
           f'<defs><linearGradient id="g" x1="0%" y1="0%" x2="{x2}" y2="{y2}">'
           '<stop offset="0" stop-color="#184888"/><stop offset="1" stop-color="#184888"/>'
           '</linearGradient></defs><rect x="2" y="2" width="26" height="16" fill="url(#g)"/></svg>')
    raster = rendering.render_svg_to_numpy_inprocess(svg, 30, 20, fitz_module=fitz, np_module=np, cv2_module=cv2)
    np.testing.assert_array_equal(raster[3:17, 3:27], np.broadcast_to([136, 72, 24], (14, 24, 3)))
    assert np.all(raster[:2] == 255) and np.all(raster[18:] == 255)
    assert np.all(raster[:, :2] == 255) and np.all(raster[:, 28:] == 255)


def test_linear_gradient_tracks_the_analytic_color_profile():
    import cv2
    import fitz
    import numpy as np
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="20">'
           '<defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="0%">'
           '<stop offset="0" stop-color="#0000ff"/><stop offset="1" stop-color="#ff0000"/>'
           '</linearGradient></defs><rect width="40" height="20" fill="url(#g)"/></svg>')
    raster = rendering.render_svg_to_numpy_inprocess(svg,40,20,fitz_module=fitz,np_module=np,cv2_module=cv2)
    t = (np.arange(40)+.5)/40
    expected = np.column_stack((255*(1-t),np.zeros(40),255*t))
    assert np.max(abs(raster[10].astype(float)-expected)) < 8


def curved_gradient_svg(paint='#184888', end='#184888', data=None, extra=''):
    data = data or 'M 6 32 C 6 2 34 2 34 32 Q 20 38 6 32 Z'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
            f'<defs><linearGradient id="curve" x1="0" x2="0" y1="0" y2="1">'
            f'<stop offset="0" stop-color="{paint}"/><stop offset="1" stop-color="{end}"/>'
            f'</linearGradient></defs><path d="{data}" fill="url(#curve)" {extra}/></svg>')


@pytest.mark.parametrize('resolution',[40,80])
def test_bezier_gradient_preserves_native_curves_and_matches_solid_boundary(resolution):
    import cv2
    import fitz
    import numpy as np
    svg = curved_gradient_svg()
    expanded = rendering._expand_bezier_linear_gradients_for_fitz(svg)
    assert 'fill="url(#curve)"' in svg and ' C ' in svg and ' Q ' in svg
    assert 'url(#curve)' not in expanded and ' C ' in expanded and ' Q ' in expanded
    def render(content):
        return rendering.render_svg_to_numpy_inprocess(content,resolution,resolution,fitz_module=fitz,np_module=np,cv2_module=cv2)
    actual = render(svg)
    expected = render(svg.replace('fill="url(#curve)"','fill="#184888"'))
    assert np.max(abs(actual.astype(float)-expected))<=5
    scale = resolution//40
    np.testing.assert_array_equal(actual[15*scale:28*scale,15*scale:25*scale],np.broadcast_to([136,72,24],(13*scale,10*scale,3)))
    assert np.all(actual[:9*scale]==255)


def test_bezier_gradient_follows_analytic_vertical_profile_without_black_fill():
    import cv2
    import fitz
    import numpy as np
    svg = curved_gradient_svg('#0000ff','#ff0000')
    actual = rendering.render_svg_to_numpy_inprocess(svg,40,40,fitz_module=fitz,np_module=np,cv2_module=cv2)
    # The exact cubic extremum is y=9.5 and the closing quadratic peaks at 35.
    t = (np.arange(13,30)+.5-9.5)/(35-9.5)
    expected = np.column_stack((255*(1-t),np.zeros(len(t)),255*t))
    assert np.max(abs(actual[13:30,20].astype(float)-expected))<14


@pytest.mark.parametrize('data,extra',[
    ('M 0 0 L 20 0 L 10 20',''),
    ('M 0 0 L 20 0 L 10 20 Z M 2 2 L 3 2 L 3 3 Z',''),
    ('M 0 0 A 20 10 0 1 0 20 20 Z',''),
    ('M 0 0 L 20 0 L 10 20 Z','transform="translate(2 2)"'),
    ('M 0 0 L 20 0 L 10 20 Z','opacity="0.5"'),
])
def test_bezier_adapter_preserves_unsupported_paths(data,extra):
    svg = curved_gradient_svg(data=data,extra=extra)
    assert rendering._expand_bezier_linear_gradients_for_fitz(svg)==svg


@pytest.mark.parametrize('extra',['gradientTransform="scale(2)"','spreadMethod="repeat"','stop-opacity="0.5"'])
def test_bezier_adapter_preserves_unsupported_gradients(extra):
    svg = curved_gradient_svg()
    if extra.startswith('stop-opacity'):
        svg = svg.replace('<stop offset="0"',f'<stop {extra} offset="0"')
    else:
        svg = svg.replace('id="curve"',f'id="curve" {extra}')
    assert rendering._expand_bezier_linear_gradients_for_fitz(svg)==svg


def test_bezier_adapter_does_not_expand_an_unsupported_viewport_mapping():
    svg = curved_gradient_svg().replace('width="40"','preserveAspectRatio="none" width="40"')
    assert rendering._expand_bezier_linear_gradients_for_fitz(svg)==svg


def radial_svg(extra=''):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
            f'<defs><radialGradient id="arbitrary" {extra}>'
            '<stop offset="0%" stop-color="#eeeeee"/>'
            '<stop offset="100%" stop-color="#888888"/>'
            '</radialGradient></defs>'
            '<ellipse cx="20" cy="20" rx="16" ry="12" fill="url(#arbitrary)" stroke="#777777" stroke-width="1"/>'
            '</svg>')


@pytest.mark.parametrize('reverse',[False,True])
def test_polygon_gradient_respects_user_coordinates_and_concave_boundary(reverse):
    import cv2
    import fitz
    import numpy as np
    a,b = ('30','10') if reverse else ('10','30')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
           f'<defs><linearGradient id="g" gradientUnits="userSpaceOnUse" x1="0" x2="0" y1="{a}" y2="{b}">'
           '<stop offset="0" stop-color="#0000ff"/><stop offset="1" stop-color="#ff0000"/>'
           '</linearGradient></defs><polygon points="2,2 38,2 38,38 22,38 22,20 2,20" fill="url(#g)"/></svg>')
    raster = rendering.render_svg_to_numpy_inprocess(svg,40,40,fitz_module=fitz,np_module=np,cv2_module=cv2)
    y = np.arange(5,35)+.5
    t = np.clip((y-10)/20,0,1)
    if reverse:
        t = 1-t
    expected = np.column_stack((255*(1-t),np.zeros(len(t)),255*t))
    assert np.max(abs(raster[5:35,30].astype(float)-expected)) < 14
    assert np.all(raster[22:38,2:20] == 255)
    assert np.all(raster[:2] == 255) and np.all(raster[:,38:] == 255)
    assert svg.count('<polygon') == 1 and 'fill="url(#g)"' in svg


@pytest.mark.parametrize('extra',['gradientTransform="scale(2)"','spreadMethod="reflect"'])
def test_polygon_adapter_leaves_unsupported_paint_servers_unchanged(extra):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g" {extra}>'
           '<stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#000000"/>'
           '</linearGradient></defs><polygon points="0,0 20,0 10,20" fill="url(#g)"/></svg>')
    assert rendering._expand_polygon_linear_gradients_for_fitz(svg) == svg


def test_radial_adapter_keeps_native_saved_vector_and_draws_light_center():
    import cv2
    import fitz
    import numpy as np
    from xml.etree import ElementTree as ET
    svg = radial_svg()
    expanded = rendering._expand_centered_radial_gradients_for_fitz(svg)
    assert svg.count('<ellipse') == 1 and 'fill="url(#arbitrary)"' in svg
    assert 'url(#arbitrary)' not in expanded
    raster = rendering.render_svg_to_numpy_inprocess(svg,40,40,fitz_module=fitz,np_module=np,cv2_module=cv2)
    assert raster is not None
    assert np.min(raster[20,20]) > 220
    assert 115 < np.mean(raster[20,33]) < 170
    assert np.mean(raster[2,2]) == 255
    shapes = [e for e in ET.fromstring(expanded).iter() if e.tag.endswith('ellipse')]
    assert shapes[-1].get('fill') == 'none' and shapes[-1].get('stroke') == '#777777'


def test_radial_adapter_leaves_unsupported_gradients_and_solid_vectors_unchanged():
    for extra in ('cx="20%"', 'fx="10%"', 'gradientTransform="scale(2)"',
                  'gradientUnits="userSpaceOnUse"', 'spreadMethod="repeat"'):
        svg = radial_svg(extra)
        assert rendering._expand_centered_radial_gradients_for_fitz(svg) == svg
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><ellipse fill="#abcdef"/></svg>'
    assert rendering._expand_centered_radial_gradients_for_fitz(svg) == svg


def test_radial_adapter_supports_circle_geometry_and_rejects_alpha_stops():
    svg = radial_svg().replace('ellipse', 'circle').replace('rx="16" ry="12"', 'r="16"')
    expanded = rendering._expand_centered_radial_gradients_for_fitz(svg)
    assert 'url(#arbitrary)' not in expanded and '<circle' in expanded
    alpha = svg.replace('offset="0%"', 'offset="0%" stop-opacity="0.4"')
    assert rendering._expand_centered_radial_gradients_for_fitz(alpha) == alpha


def test_radial_render_does_not_depend_on_previous_linear_render(monkeypatch):
    import xml.etree.ElementTree as ET
    import cv2
    import fitz
    import numpy as np
    monkeypatch.delitem(ET._namespace_map, 'http://www.w3.org/2000/svg', raising=False)
    svg = radial_svg()
    raster = rendering.render_svg_to_numpy_inprocess(svg, 40, 40, fitz_module=fitz, np_module=np, cv2_module=cv2)
    assert raster is not None
    assert np.min(raster[20, 20]) > 220
