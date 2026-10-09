"""Constrained slash/dot recovery from independent vectors and real rasters."""
from pathlib import Path
import json

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterSquareStem import fit_square_stem
from tools.evaluate_right_stem_square_recheck import square_slash_and_dot_semantics, measure
from tools.run_plan_b_variations import measure_quality

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT/'artifacts/evaluation/marked_square_recheck_v1/manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg, w, h, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION, objective=None):
    h,w = image.shape[:2]
    return fit_square_stem(geometry.buildGeometryIrFromDescriptionImpl(description), image=image,
        description=description,
        render_fn=lambda ir: render(geometry.renderGeometryIrToSvgImpl(w,h,ir),w,h),
        error_fn=objective or (lambda raster: calculateErrorImpl(image,raster,cv2_module=cv2,np_module=np)))


def synthetic(scale=1, shift=0, fill='#2465a7', mark='#f3e5c9', omit=None):
    # Independent coordinates, no fitted parameters or production IR generator.
    parts = [f'<rect x="{3+shift}" y="3" width="24" height="24" fill="{fill}" stroke="#777777" stroke-width="1"/>',
             f'<path d="M {27+shift} 15 L 47 15" fill="none" stroke="#888888" stroke-width="1.5"/>']
    if omit != 'slash':
        parts.append(f'<path d="M {17+shift} 7 L {19+shift} 7 L {15+shift} 23 L {13+shift} 23 Z" fill="{mark}"/>')
    if omit != 'dot':
        parts.append(f'<path d="M {8+shift} 20 L {10+shift} 20 L {10+shift} 22 L {8+shift} 22 Z" fill="{mark}"/>')
    if omit == 'extra':
        parts.append('<circle cx="23" cy="10" r="1.5" fill="black"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{50*scale}" height="{30*scale}" viewBox="0 0 50 30">'
            +''.join(parts)+'</svg>')


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c:c['source'])
def test_real_colors_and_sizes_pass_both_topology_and_stricter_pixel_gate(case):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['source']))
    result = fit(image)
    assert result is not None and result['final_error'] < result['initial_error']
    assert result['evaluations'] <= 1441
    h,w = image.shape[:2]
    svg = geometry.renderGeometryIrToSvgImpl(w,h,result['geometry_ir'])
    assert square_slash_and_dot_semantics(svg) == 1
    assert measure_quality(image,svg)['satisfactory']


@pytest.mark.parametrize('scale,shift,fill,mark', [
    (1,0,'#2465a7','#f3e5c9'), (1,3,'#eeeeee','#555555'), (2,2,'#379b54','#f4e7da'),
])
def test_independent_color_polarity_position_and_resolution_holdouts(scale,shift,fill,mark):
    svg = synthetic(scale,shift,fill,mark)
    image = render(svg,50*scale,30*scale)
    result = fit(image)
    assert result is not None
    reconstructed = geometry.renderGeometryIrToSvgImpl(50*scale,30*scale,result['geometry_ir'])
    assert square_slash_and_dot_semantics(reconstructed) == 1
    assert measure_quality(image,reconstructed)['satisfactory']


@pytest.mark.parametrize('omit', ['slash','dot','extra'])
def test_missing_or_extra_evidence_does_not_invent_a_mark(omit):
    assert fit(render(synthetic(omit=omit),50,30)) is None


@pytest.mark.parametrize('description', [
    MANIFEST['baseline_description'], DESCRIPTION+' Ohne Innenmarkierung.',
    DESCRIPTION.replace('und ein kleiner quadratischer Punkt links neben seinem unteren Ende', ''),
])
def test_description_must_allow_both_marks(description):
    assert fit(render(synthetic(),50,30), description) is None


@pytest.mark.parametrize('value', [float('nan'),float('inf')])
def test_nonfinite_objective_is_rejected(value):
    assert fit(render(synthetic(),50,30), objective=lambda _:value) is None


def test_runtime_is_name_invariant_and_precedes_sample_and_plain_panel(monkeypatch):
    image = render(synthetic(),50,30)
    monkeypatch.setattr(runtime,'_try_load_sample_svg',lambda **_:pytest.fail('no sample lookup'))
    monkeypatch.setattr(runtime,'_try_build_plain_framed_panel_svg',lambda *a,**k:pytest.fail('must retain marks and handle'))
    outputs = []
    for name in ('catalog_like_name','unrelated_holdout'):
        artifacts,logs = [],[]
        result = runtime.runNonCompositeIterationImpl(mode='non_composite',params={},stripe_strategy=None,
            semantic_mode_visual_override=False,width=50,height=30,base_name=name,description=DESCRIPTION,
            perc_img=image,img_path=name+'.png',print_fn=lambda *a:None,
            render_embedded_raster_svg_fn=lambda _:None,build_gradient_stripe_svg_fn=lambda *a,**k:None,
            build_gradient_stripe_validation_log_lines_fn=lambda **_:[],write_validation_log_fn=logs.append,
            render_svg_to_numpy_fn=render,record_render_failure_fn=lambda *a,**k:None,
            write_attempt_artifacts_fn=lambda svg,raster:artifacts.append(svg),
            calculate_error_fn=lambda a,b:calculateErrorImpl(a,b,cv2_module=cv2,np_module=np))
        assert result is not None and logs[-1] == ['status=non_composite_raster_square_stem']
        outputs.append(artifacts[-1])
    assert outputs[0] == outputs[1]


def test_gate_calibration_and_missing_or_misplaced_mark_rejection(tmp_path):
    svg = synthetic()
    svg_path,image_path = tmp_path/'perfect.svg',tmp_path/'perfect.png'
    svg_path.write_text(svg,encoding='utf-8')
    assert cv2.imwrite(str(image_path),render(svg,50,30))
    measured = measure(image_path,svg_path,interior_mark_contract='slash_and_dot')
    assert measured['mean_delta2'] == 0
    assert set(measured['metrics'].values()) == {0.,1.}
    assert measured['metrics']['semantic_score'] == 1
    assert square_slash_and_dot_semantics(synthetic(omit='slash')) == 0
    assert square_slash_and_dot_semantics(synthetic(omit='dot')) == 0
    assert square_slash_and_dot_semantics(synthetic(omit='extra')) == 0
    assert square_slash_and_dot_semantics(svg.replace('M 8 20','M 1 20')) == 0
    assert square_slash_and_dot_semantics(svg.replace('M 17 7 L 19 7','M 9 7 L 11 7')) == 0
