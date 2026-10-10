from pathlib import Path
import json
import re

import cv2
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules.imageCompositeConverterSquareStem import fit_square_stem
from tools.evaluate_top_stem_square_recheck import symbol_semantics
from tools.run_plan_b_variations import render, measure_quality, make_variations
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'artifacts/evaluation/bottom_stem_marked_square_recheck_v1/manifest.json'
DESCRIPTION = json.loads(MANIFEST.read_text(encoding='utf-8'))['cases'][0]['description']


def fit(image, error_fn=None, render_fn=None):
    h, w = image.shape[:2]
    return fit_square_stem(geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION), image=image,
        description=DESCRIPTION,
        render_fn=render_fn or (lambda ir: render(geometry.renderGeometryIrToSvgImpl(w,h,ir),w,h)),
        error_fn=error_fn or (lambda raster: normalized_mse(image,raster)[0]))


def synthetic(scale=1, shift=0., fill='#244ca0', ink='#e8dfc1'):
    # Independent geometry, with no production IR renderer or stored fitted shape.
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{60*scale}" height="{90*scale}" viewBox="0 0 60 90">'
        f'<rect x="{10+shift}" y="8" width="36" height="36" fill="{fill}" stroke="#707070" stroke-width="1.5"/>'
        f'<path d="M {28+shift} 44 L {28+shift} 82" stroke="#808080" stroke-width="2"/>'
        f'<path d="M {33+shift} 16 L {35+shift} 16 L {28+shift} 36 L {26+shift} 36 Z" fill="{ink}"/>'
        f'<rect x="{20+shift}" y="32" width="3" height="3" fill="{ink}"/></svg>')


@pytest.mark.parametrize('variant',['AC0711_1_L','AC0711_1_M','AC0711_1_S','AC0711_L','AC0711_M','AC0711_S'])
def test_all_real_variants_have_both_marks_and_pass_plan_b_pixels(variant, monkeypatch):
    import tests.test_rotated_square_kelle_runtime as helper
    monkeypatch.setattr(helper,'DESCRIPTION',DESCRIPTION)
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/(variant+'.jpg')))
    (svg,raster), logs = helper._convert(image,'anonymous_bottom_square',monkeypatch)
    assert symbol_semantics(svg,'bottom') == 1.
    assert logs == ['status=non_composite_raster_square_stem']
    assert measure_quality(image,svg)['satisfactory']


@pytest.mark.parametrize('scale,shift,fill,ink',[(1,.25,'#244ca0','#e8dfc1'),(2,.5,'#36a050','#222a30'),(1,2.,'#dddddd','#555555')])
def test_independent_color_position_and_resolution(scale,shift,fill,ink):
    image = render(synthetic(scale,shift,fill,ink),60*scale,90*scale)
    fitted = fit(image)
    assert fitted is not None
    assert fitted['final_error'] < fitted['initial_error']*.1
    svg = geometry.renderGeometryIrToSvgImpl(60*scale,90*scale,fitted['geometry_ir'])
    assert symbol_semantics(svg,'bottom') == 1.
    assert measure_quality(image,svg)['satisfactory']


@pytest.mark.parametrize('change',['missing_dot','missing_slash','wrong_slash','extra_object','missing_stem'])
def test_different_or_incomplete_topologies_are_rejected(change):
    svg = synthetic()
    if change == 'missing_dot':
        svg = re.sub(r'<rect x="20.0"[^>]*/>','',svg)
    elif change == 'missing_slash':
        svg = re.sub(r'<path d="M 33.0[^>]*/>','',svg)
    elif change == 'missing_stem':
        svg = re.sub(r'<path d="M 28.0 44[^>]*/>','',svg)
    elif change == 'wrong_slash':
        svg = svg.replace('M 33.0 16 L 35.0 16 L 28.0 36 L 26.0 36','M 25 16 L 27 16 L 34 36 L 32 36')
    else:
        svg = svg.replace('</svg>','<circle cx="50" cy="62" r="3" fill="black"/></svg>')
    assert fit(render(svg,60,90)) is None


def test_filename_invariance_and_no_reference_reads(monkeypatch):
    import tests.test_rotated_square_kelle_runtime as helper
    monkeypatch.setattr(helper,'DESCRIPTION',DESCRIPTION)
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0711_1_M.jpg'))
    (svg,raster), _ = helper._convert(image,'AC0711_1_M',monkeypatch)
    (other,other_raster), _ = helper._convert(image,'unrelated_holdout',monkeypatch)
    assert svg == other
    np.testing.assert_array_equal(raster,other_raster)


def test_invalid_input_objective_and_missing_renderer_do_not_accept():
    image = render(synthetic(),60,90)
    assert fit(image,render_fn=lambda _:None) is None
    assert fit(image,error_fn=lambda _:float('nan')) is None
    assert fit(np.full(image.shape,np.nan)) is None


def test_direction_is_checked_independently():
    fitted = fit(render(synthetic(),60,90))
    svg = geometry.renderGeometryIrToSvgImpl(60,90,fitted['geometry_ir'])
    assert symbol_semantics(svg,'top') == 0.


def test_fractional_pixel_at_body_handle_joint_is_accepted():
    # This shifted/scaled independent source formerly left one gray boundary
    # pixel outside the dense body estimate and rejected the entire topology.
    case = make_variations(synthetic(),DESCRIPTION,20261010)[9]
    image = render(case['svg'],case['width'],case['height'])
    fitted = fit(image)
    assert fitted is not None
    svg = geometry.renderGeometryIrToSvgImpl(case['width'],case['height'],fitted['geometry_ir'])
    assert symbol_semantics(svg,'bottom') == 1.
    assert measure_quality(image,svg)['satisfactory']
