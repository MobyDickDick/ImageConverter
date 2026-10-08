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


def radial_svg(extra=''):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
            f'<defs><radialGradient id="arbitrary" {extra}>'
            '<stop offset="0%" stop-color="#eeeeee"/>'
            '<stop offset="100%" stop-color="#888888"/>'
            '</radialGradient></defs>'
            '<ellipse cx="20" cy="20" rx="16" ry="12" fill="url(#arbitrary)" stroke="#777777" stroke-width="1"/>'
            '</svg>')


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
