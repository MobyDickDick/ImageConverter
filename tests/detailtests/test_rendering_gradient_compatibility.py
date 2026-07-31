from __future__ import annotations

from src.iCCModules import imageCompositeConverterRendering as rendering


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
