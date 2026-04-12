from src.iCCModules import imageCompositeConverterElementDecomposition as decomposition
from src.iCCModules.imageCompositeConverterCoreClasses import Candidate, Element


def test_candidate_to_svg_impl_generates_circle_with_stroke():
    candidate = Candidate(shape="circle", cx=10.0, cy=12.0, w=8.0, h=8.0)
    svg = decomposition.candidateToSvgImpl(
        candidate,
        gx=2,
        gy=3,
        fill_color="#ffffff",
        stroke_color="#000000",
        stroke_width=2.0,
    )
    assert 'cx="12.00"' in svg
    assert 'cy="15.00"' in svg
    assert 'r="3.00"' in svg
    assert 'stroke="#000000"' in svg


def test_estimate_stroke_style_impl_detects_circle_ring():
    grayscale = [[220 for _ in range(7)] for _ in range(7)]
    element_pixels = [[0 for _ in range(7)] for _ in range(7)]
    for y in range(7):
        for x in range(7):
            if (x - 3) ** 2 + (y - 3) ** 2 <= 9:
                element_pixels[y][x] = 1
                if (x - 3) ** 2 + (y - 3) ** 2 >= 7:
                    grayscale[y][x] = 20
                else:
                    grayscale[y][x] = 210

    element = Element(pixels=element_pixels, x0=0, y0=0, x1=6, y1=6)
    candidate = Candidate(shape="circle", cx=3.0, cy=3.0, w=6.0, h=6.0)
    fill, stroke, stroke_width = decomposition.estimateStrokeStyleImpl(
        grayscale,
        element,
        candidate,
        gray_to_hex_fn=lambda v: f"#{int(round(v)):02x}{int(round(v)):02x}{int(round(v)):02x}",
    )
    assert fill == "#d2d2d2"
    assert stroke == "#141414"
    assert stroke_width == 1.0
