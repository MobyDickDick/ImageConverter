from pathlib import Path
import json

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterZigzagPanel import fit_zigzag_panel
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_zigzag_panel_recheck import zigzag_panel_semantics
from tools.run_plan_b_variations import measure_quality, make_variations
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = json.loads((ROOT/'artifacts/evaluation/zigzag_panel_recheck_v1/manifest.json').read_text(encoding='utf-8'))['description']
TEMPLATE_DESCRIPTION = (ROOT/'artifacts/images_to_convert/samples/AC0130_L.txt').read_text(encoding='utf-8')


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg,width,height,fitz_module=fitz,np_module=np,cv2_module=cv2)


def fit(image, description=DESCRIPTION, error=None):
    h,w = image.shape[:2]
    return fit_zigzag_panel(w,h,description=description,image=image,render_fn=render,
                           error_fn=error or (lambda a,b:normalized_mse(a,b)[0]))


def synthetic(scale=1, shift=0, color='#cccccc', count=7, mark=True, inner=True):
    points = ' '.join(f'{(8 if i%2==0 else 20)+shift},{4+i*12}' for i in range(count*2+1))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{50*scale}" height="{100*scale}" viewBox="0 0 50 100">'
           f'<defs><linearGradient id="metal" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{color}"/>'
           f'<stop offset="0.5" stop-color="#fafafa"/><stop offset="1" stop-color="{color}"/></linearGradient></defs>'
           f'<rect x="{2+shift}" y="2" width="44" height="96" fill="url(#metal)" stroke="#808080" stroke-width="1"/>'
           +(f'<rect x="{27+shift}" y="7" width="13" height="84" fill="none" stroke="#888888" stroke-width="1"/>' if inner else '')
           +(f'<polyline points="{points}" fill="none" stroke="#999999" stroke-width="0.7"/>' if mark else '')+'</svg>')
    return render(svg,50*scale,100*scale)


@pytest.mark.parametrize('name',['AC0130_S','AC0130_M','AC0130_L'])
def test_real_raster_and_standalone_description_pass(name):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/f'{name}.jpg'))
    result = fit(image)
    assert result is not None and result['error'] < result['initial_error']
    assert result['evaluations'] <= 609 and zigzag_panel_semantics(result['svg']) == 1
    assert normalized_mse(image,result['rendered'])[1] < .01


@pytest.mark.parametrize('scale,shift,color',[(1,0,'#cccccc'),(1,1,'#c7d0d0'),(2,0,'#cccccc')])
def test_registration_estimates_geometry_under_color_scale_and_position_changes(scale,shift,color):
    # Vertices span the panel height and stay within the observed rectangle.
    image = synthetic(scale,shift,color,count=3)
    result = fit(image)
    assert result is not None
    assert zigzag_panel_semantics(result['svg']) == 1
    assert normalized_mse(image,result['rendered'])[1] < .005


@pytest.mark.parametrize('mark,inner',[(False,True),(True,False),(False,False)])
def test_missing_structure_is_rejected(mark,inner):
    assert fit(synthetic(count=3,mark=mark,inner=inner)) is None


@pytest.mark.parametrize('suffix',['Andreaskreuz','Kreis','zusätzlich ein Zeichen','vertikaler Verlauf'])
def test_conflicting_description_is_rejected(suffix):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0130_S.jpg'))
    assert fit(image,DESCRIPTION+' '+suffix) is None


@pytest.mark.parametrize('value',[42.,float('nan'),float('inf')])
def test_invalid_or_constant_objective_supplies_no_fit_evidence(value):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0130_S.jpg'))
    original = image.copy()
    assert fit(image,error=lambda a,b:value) is None
    np.testing.assert_array_equal(image,original)


def test_runtime_uses_pixels_with_neutral_names_and_no_template_read(monkeypatch):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0130_S.jpg'))
    monkeypatch.setattr(runtime,'_try_load_sample_svg',lambda **kw:pytest.fail('template read during conversion'))
    artifacts = []
    for name in ('anonymous_alpha','anonymous_omega'):
        params,logs = {},[]
        h,w = image.shape[:2]
        result = runtime.runNonCompositeIterationImpl(mode='auto',params=params,stripe_strategy=None,
            semantic_mode_visual_override=False,width=w,height=h,base_name=name,description=DESCRIPTION,
            perc_img=image,img_path=name+'.jpg',print_fn=lambda *a:None,
            render_embedded_raster_svg_fn=lambda *a:pytest.fail('embedded raster'),
            build_gradient_stripe_svg_fn=lambda *a,**k:None,
            build_gradient_stripe_validation_log_lines_fn=lambda **k:[],write_validation_log_fn=logs.append,
            render_svg_to_numpy_fn=render,record_render_failure_fn=lambda *a,**k:None,
            write_attempt_artifacts_fn=lambda s,r:artifacts.append((s,r)),
            calculate_error_fn=lambda a,b:calculateErrorImpl(a,b,cv2_module=cv2,np_module=np))
        assert result is not None and logs[-1]==['status=non_composite_raster_zigzag_panel']
        assert params['raster_zigzag_panel_v1']['evaluations'] <= 609
    assert artifacts[0][0]==artifacts[1][0]
    np.testing.assert_array_equal(artifacts[0][1],artifacts[1][1])


@pytest.mark.parametrize('index',[0,3,5,14])
def test_supplied_template_is_rasterized_and_varied_before_reconstruction(index):
    svg = (ROOT/'artifacts/images_to_convert/samples/AC0130_L.svg').read_text(encoding='utf-8')
    case = make_variations(svg,TEMPLATE_DESCRIPTION,20261008)[index]
    image = render(case['svg'],case['width'],case['height'])
    result = fit(image,case['description'])
    assert result is not None and result['source']=='raster_repeated_line_panel_v1'
    assert result['evaluations'] <= 681 and '<image' not in result['svg']
    assert measure_quality(image,result['svg'])['satisfactory']
