"""Independent left-handle topology and catalog acceptance regressions."""
from pathlib import Path
import json
import re

import cv2
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules.imageCompositeConverterSquareStem import fit_square_stem
from tools.evaluate_top_stem_square_recheck import symbol_semantics, measure
from tools.run_plan_b_variations import render, measure_quality
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'artifacts/evaluation/left_stem_marked_square_recheck_v1/manifest.json'
DESCRIPTION = json.loads(MANIFEST.read_text(encoding='utf-8'))['cases'][0]['description']


def synthetic(scale=1, shift=0., fill='#244ca0', ink='#e8dfc1'):
    # Independent geometry; neither production IR nor fitted catalog vectors.
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{90*scale}" height="{60*scale}" viewBox="0 0 90 60">'
        f'<rect x="{42+shift}" y="10" width="36" height="36" fill="{fill}" stroke="#707070" stroke-width="1.5"/>'
        f'<path d="M {42+shift} 28 L 5 28" stroke="#808080" stroke-width="2"/>'
        f'<path d="M {65+shift} 18 L {67+shift} 18 L {60+shift} 38 L {58+shift} 38 Z" fill="{ink}"/>'
        f'<rect x="{52+shift}" y="34" width="3" height="3" fill="{ink}"/></svg>')


def fit(image, description=DESCRIPTION, error_fn=None, render_fn=None):
    h, w = image.shape[:2]
    return fit_square_stem(geometry.buildGeometryIrFromDescriptionImpl(description), image=image,
        description=description,
        render_fn=render_fn or (lambda ir: render(geometry.renderGeometryIrToSvgImpl(w,h,ir),w,h)),
        error_fn=error_fn or (lambda raster: normalized_mse(image,raster)[0]))


@pytest.mark.parametrize('case', json.loads(MANIFEST.read_text(encoding='utf-8'))['cases'], ids=lambda c:c['source'])
def test_real_variants_retain_marks_and_pass_strict_pixels(case, monkeypatch):
    import tests.test_rotated_square_kelle_runtime as helper
    monkeypatch.setattr(helper, 'DESCRIPTION', DESCRIPTION)
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['source']))
    (svg, raster), logs = helper._convert(image, 'anonymous_left_square', monkeypatch)
    assert logs == ['status=non_composite_raster_square_stem']
    assert symbol_semantics(svg, 'left') == 1.
    assert measure_quality(image, svg)['satisfactory']
    assert '<text' not in svg and '<image' not in svg and 'transform=' not in svg


@pytest.mark.parametrize('scale,shift,fill,ink', [(1,.25,'#244ca0','#e8dfc1'),(2,.5,'#36a050','#222a30'),(1,2.,'#dddddd','#555555')])
def test_independent_geometry_colors_resolution_and_position(scale, shift, fill, ink):
    image = render(synthetic(scale,shift,fill,ink),90*scale,60*scale)
    fitted = fit(image)
    assert fitted is not None
    assert fitted['evaluations'] <= 1442  # Existing search plus one measured rim seed.
    svg = geometry.renderGeometryIrToSvgImpl(90*scale,60*scale,fitted['geometry_ir'])
    assert symbol_semantics(svg,'left') == 1.
    assert symbol_semantics(svg,'top') == 0.
    assert measure_quality(image,svg)['satisfactory']


@pytest.mark.parametrize('change', ['missing_dot','missing_slash','wrong_slash','missing_stem','extra_object'])
def test_missing_or_different_topology_is_rejected(change):
    svg = synthetic()
    if change == 'missing_dot':
        svg = re.sub(r'<rect x="52.0"[^>]*/>', '', svg)
    elif change == 'missing_slash':
        svg = re.sub(r'<path d="M 65.0[^>]*/>', '', svg)
    elif change == 'missing_stem':
        svg = re.sub(r'<path d="M 42.0 28[^>]*/>', '', svg)
    elif change == 'wrong_slash':
        svg = svg.replace('M 65.0 18 L 67.0 18 L 60.0 38 L 58.0 38', 'M 57 18 L 59 18 L 66 38 L 64 38')
    else:
        svg = svg.replace('</svg>', '<circle cx="20" cy="50" r="3" fill="black"/></svg>')
    assert fit(render(svg,90,60)) is None


def test_filename_independence_and_reference_lookup_prohibition(monkeypatch):
    import tests.test_rotated_square_kelle_runtime as helper
    monkeypatch.setattr(helper,'DESCRIPTION',DESCRIPTION)
    image = render(synthetic(),90,60)
    (svg,raster), _ = helper._convert(image,'AC0712_1_S',monkeypatch)
    (other,other_raster), _ = helper._convert(image,'unrelated_holdout',monkeypatch)
    assert svg == other
    np.testing.assert_array_equal(raster,other_raster)


def test_invalid_inputs_and_unavailable_renderer_are_rejected():
    image = render(synthetic(),90,60)
    assert fit(image,render_fn=lambda _:None) is None
    assert fit(image,error_fn=lambda _:float('nan')) is None
    assert fit(np.full(image.shape,np.nan)) is None
    assert fit(image,DESCRIPTION+' Ohne Innenmarkierung.') is None


def test_explicit_text_keeps_legacy_text_contract():
    ir = geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION+' Mit Text "T".')
    assert ir[0]['label'] == 'T'
    assert fit(render(synthetic(),90,60), DESCRIPTION+' Mit Text "T".') is None


def test_semantic_gate_detects_wrong_direction_and_missing_mark(tmp_path):
    fitted = fit(render(synthetic(),90,60))
    svg = geometry.renderGeometryIrToSvgImpl(90,60,fitted['geometry_ir'])
    vector, image = tmp_path/'perfect.svg', tmp_path/'perfect.png'
    vector.write_text(svg,encoding='utf-8')
    assert cv2.imwrite(str(image),render(svg,90,60))
    measured = measure(image,vector,'left')
    assert measured['mean_delta2'] == 0.
    assert measured['metrics']['semantic_score'] == 1.
    assert symbol_semantics(svg,'bottom') == 0.
    assert symbol_semantics(re.sub(r'<path id="raster_interior_dot"[^>]*/>', '', svg),'left') == 0.
