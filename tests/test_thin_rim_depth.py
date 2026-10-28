"""Depth evidence comes from distinct raster pixels, including split thin rims."""
from copy import deepcopy

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterMixedGradientScene as mixed
from tools.run_plan_b_variations import render


def scene(*, reverse=False, stroke=True, offset=0.):
    objects, shapes = [], []
    for x, y in ((11.+offset, 11.+offset), (26.+offset, 26.+offset)):
        objects.append(dict(kind='rectangle', geometry=np.array([x, y, 30., 30., 1.5]),
                            colors=np.array([121., 77., 40., 121., 77., 40., 237., 240., 243.])))
        shapes.append(f'<rect x="{x}" y="{y}" width="30" height="30" fill="#284d79" '
                      f'stroke="{"#f3f0ed" if stroke else "none"}" stroke-width="1.5"/>')
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72"><rect width="72" height="72" fill="white"/>'
    svg += ''.join(reversed(shapes) if reverse else shapes)+'</svg>'
    return render(svg, 72, 72), objects


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('offset', [-.02, 0., .02])
def test_split_pixel_rims_observe_both_painter_orders(reverse, offset):
    pixels, objects = scene(reverse=reverse, offset=offset)
    assert mixed._rim_front(pixels, objects, 0, 1) == (0 if reverse else 1)


def test_unoutlined_union_has_no_depth_evidence_even_with_proposed_rims():
    pixels, objects = scene(stroke=False)
    assert mixed._rim_front(pixels, objects, 0, 1) is None


def test_third_object_cannot_supply_the_missing_depth_evidence():
    pixels, objects = scene()
    foreign = deepcopy(objects[1])
    # A third silhouette obscures all evidence about this pair, regardless
    # of whether the measured paint happens to resemble either child's rim.
    foreign['geometry'] = np.array([5., 5., 60., 60., 1.5])
    assert mixed._rim_front(pixels, [*objects, foreign], 0, 1) is None


def test_subpixel_samples_cannot_turn_four_pixels_into_five_observations():
    pixels, objects = scene()
    # Clip the observed raster to a 2x2 intersection; the subpixel grid may
    # estimate coverage but cannot increase the number of observations.
    for obj in objects:
        obj['geometry'][:2] -= 24
    assert mixed._rim_front(pixels[24:26, 24:26], objects, 0, 1) is None


def test_too_little_stroke_area_cannot_use_bright_pixels_as_depth_evidence():
    pixels, objects = scene()
    for obj in objects:
        obj['geometry'][4] = .5
    assert mixed._rim_front(pixels, objects, 0, 1) is None


def test_conflicting_visible_rims_do_not_establish_a_painter_order():
    pixels, objects = scene()
    reversed_pixels, _ = scene(reverse=True)
    # Retain the bright rim from each contradictory layer ordering.
    pixels = np.maximum(pixels, reversed_pixels)
    assert mixed._rim_front(pixels, objects, 0, 1) is None


def test_rim_like_foreign_color_is_not_supported_by_coverage_alone():
    pixels, objects = scene()
    pixels[:] = [160, 160, 160]
    assert mixed._rim_front(pixels, objects, 0, 1) is None
