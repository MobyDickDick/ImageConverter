from pathlib import Path
import json

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterSquareStem import fit_square_stem
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
from tools.evaluate_right_stem_square_recheck import square_and_right_stem_semantics
from tools.run_plan_b_variations import measure_quality

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT/'artifacts/evaluation/right_stem_square_recheck_v1/manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg,w,h,fitz_module=fitz,np_module=np,cv2_module=cv2)


def fit(image, objective=None):
    h,w = image.shape[:2]
    ir = geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION)
    return fit_square_stem(ir,image=image,
        render_fn=lambda candidate: render(geometry.renderGeometryIrToSvgImpl(w,h,candidate),w,h),
        error_fn=objective or (lambda raster: calculateErrorImpl(image,raster,cv2_module=cv2,np_module=np)))


@pytest.mark.parametrize('case',MANIFEST['cases'],ids=lambda c:c['source'])
def test_real_color_and_size_variants_pass_stricter_plan_b_limits(case):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['source']))
    result = fit(image)
    assert result is not None and result['final_error'] < result['initial_error']
    assert result['evaluations'] <= 433
    h,w = image.shape[:2]
    svg = geometry.renderGeometryIrToSvgImpl(w,h,result['geometry_ir'])
    assert square_and_right_stem_semantics(svg) == 1
    assert measure_quality(image,svg)['satisfactory']


def synthetic(scale=1,shift=0,fill='#227bb8',omit=None):
    # Independent vectors, without the production IR renderer or fitted params.
    parts = [f'<rect x="{3+shift}" y="4" width="20" height="20" fill="{fill}" stroke="#686868" stroke-width="1"/>']
    if omit != 'handle':
        parts.append(f'<path d="M {23+shift} 14 L 43 14" fill="none" stroke="#808080" stroke-width="1.5"/>')
    if omit == 'extra':
        parts.append('<circle cx="40" cy="26" r="2" fill="black"/>')
    if omit == 'mark':
        parts.append('<path d="M 10 8 L 16 20" stroke="white" stroke-width="3"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{46*scale}" height="{30*scale}" viewBox="0 0 46 30">'
           +''.join(parts)+'</svg>')
    return render(svg,46*scale,30*scale)


@pytest.mark.parametrize('scale,shift,fill',[(1,0,'#227bb8'),(1,3,'#e8e8e8'),(2,2,'#369b54')])
def test_independent_position_color_and_resolution_holdouts(scale,shift,fill):
    image = synthetic(scale,shift,fill)
    result = fit(image)
    assert result is not None
    h,w = image.shape[:2]
    svg = geometry.renderGeometryIrToSvgImpl(w,h,result['geometry_ir'])
    assert measure_quality(image,svg)['satisfactory']


@pytest.mark.parametrize('omit',['handle','extra','mark'])
def test_missing_handle_or_unclaimed_objects_are_rejected(omit):
    assert fit(synthetic(omit=omit)) is None


@pytest.mark.parametrize('phrase',[DESCRIPTION, DESCRIPTION.replace('ohne Text','ohne Beschriftung'),
                                  MANIFEST['baseline_description']])
def test_parser_handles_absolute_and_historical_orientation_without_catalog_lookup(phrase):
    ir = geometry.buildGeometryIrFromDescriptionImpl(phrase)
    assert len(ir) == 1 and ir[0]['kind'] == 'RightStemSquareKelleGlyph'
    assert ir[0]['transform']['rotation_deg'] == -90
    assert 'label' not in ir[0]


@pytest.mark.parametrize('suffix',['mit Text "P"','zusätzlich ein Dreieck','Griff nach links','um 180° gedreht'])
def test_conflicting_or_labeled_description_does_not_select_plain_square(suffix):
    ir = geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION+' '+suffix)
    assert not any(e['kind']=='RightStemSquareKelleGlyph' for e in ir)


@pytest.mark.parametrize('value',[float('nan'),float('inf')])
def test_nonfinite_objective_is_rejected(value):
    assert fit(synthetic(),lambda _:value) is None


def test_reflection_passes_standalone_description():
    reflection = Reflection({'anonymous':DESCRIPTION})
    desc,params = reflection.parseDescription('anonymous','anonymous.jpg')
    assert desc and params['mode'] in {'auto','non_composite'}
    assert geometry.buildGeometryIrFromDescriptionImpl(desc)[0]['kind']=='RightStemSquareKelleGlyph'


def test_small_gray_runtime_bypasses_plain_panel_and_is_name_invariant(monkeypatch):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0704_S.jpg'))
    h,w = image.shape[:2]
    monkeypatch.setattr(runtime,'_try_load_sample_svg',lambda **_:pytest.fail('no sample lookup'))
    monkeypatch.setattr(runtime,'_try_build_plain_framed_panel_svg',lambda *a,**k:pytest.fail('square must precede plain panel'))
    outputs = []
    for name in ('AC0704_S','unrelated_holdout'):
        artifacts,logs = [],[]
        result = runtime.runNonCompositeIterationImpl(mode='non_composite',params={},stripe_strategy=None,
            semantic_mode_visual_override=False,width=w,height=h,base_name=name,description=DESCRIPTION,
            perc_img=image,img_path=name+'.jpg',print_fn=lambda *a:None,
            render_embedded_raster_svg_fn=lambda _:None,build_gradient_stripe_svg_fn=lambda *a,**k:None,
            build_gradient_stripe_validation_log_lines_fn=lambda **_:[],write_validation_log_fn=logs.append,
            render_svg_to_numpy_fn=render,record_render_failure_fn=lambda *a,**k:None,
            write_attempt_artifacts_fn=lambda svg,raster:artifacts.append(svg),
            calculate_error_fn=lambda a,b:calculateErrorImpl(a,b,cv2_module=cv2,np_module=np))
        assert result is not None and logs[-1] == ['status=non_composite_raster_square_stem']
        outputs.append(artifacts[-1])
    assert outputs[0] == outputs[1]


def test_recheck_rejects_reused_output(tmp_path,monkeypatch):
    import sys
    from tools.run_right_stem_square_recheck import main
    monkeypatch.setattr(sys,'argv',['recheck','missing.json','--output-dir',str(tmp_path)])
    with pytest.raises(ValueError,match='fresh output directory'):
        main()
