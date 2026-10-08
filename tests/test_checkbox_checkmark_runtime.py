from pathlib import Path
import json

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterCheckboxCheckmark import fit_checkbox_checkmark
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_checkbox_checkmark_recheck import checkbox_checkmark_semantics, measure
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'artifacts/evaluation/checkbox_checkmark_recheck_v1/manifest.json'
DESCRIPTION = json.loads(MANIFEST.read_text(encoding='utf-8'))['description']


def render(svg,w,h):
    return render_svg_to_numpy_inprocess(svg,w,h,fitz_module=fitz,np_module=np,cv2_module=cv2)


def fit(image,description=DESCRIPTION,error=None):
    h,w = image.shape[:2]
    return fit_checkbox_checkmark(w,h,description=description,image=image,render_fn=render,
        error_fn=error or (lambda a,b:normalized_mse(a,b)[0]))


def synthetic(scale=1,shift=0,color='#328634',frame=True,mark=True,extra=False):
    points = [(10,20),(26,31),(49,3),(55,7),(27,44),(7,25)]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{60*scale}" height="{60*scale}">'
           '<defs><linearGradient id="shade" x1="0" x2="0" y1="0" y2="1">'
           '<stop offset="0" stop-color="#175822"/>'
           f'<stop offset="0.5" stop-color="{color}"/><stop offset="1" stop-color="#c2cec2"/>'
           '</linearGradient></defs>'
           + (f'<rect x="{(14+shift)*scale}" y="{22*scale}" width="{28*scale}" height="{29*scale}" fill="#ffffff" stroke="#777777" stroke-width="{2*scale}"/>' if frame else '')
           + (f'<polygon points="'+ ' '.join(f'{(x+shift)*scale},{y*scale}' for x,y in points)+f'" fill="url(#shade)" stroke="#203020" stroke-width="{scale}" stroke-linejoin="round"/>' if mark else '')
           + (f'<circle cx="{4*scale}" cy="{52*scale}" r="{3*scale}" fill="#00aa00"/>' if extra else '')
           + '</svg>')
    return svg,render(svg,60*scale,60*scale)


@pytest.mark.parametrize('scale,shift,color',[(1,0,'#328634'),(1,3,'#52993c'),(2,0,'#328634'),(2,3,'#52993c')])
def test_registration_generalizes_lage_resolution_and_green_gradient(scale,shift,color):
    _,image = synthetic(scale,shift,color)
    result = fit(image)
    assert result is not None
    assert result['error'] < result['initial_error']
    assert normalized_mse(image,result['rendered'])[1] < .008
    assert checkbox_checkmark_semantics(result['svg']) == 1
    assert result['evaluations'] <= 417
    assert result['svg'].count('<polygon') == 1 and '<image' not in result['svg']


@pytest.mark.parametrize('frame,mark,extra',[(False,True,False),(True,False,False),(False,False,False),(True,True,True)])
def test_missing_or_extra_evidence_is_rejected(frame,mark,extra):
    _,image = synthetic(frame=frame,mark=mark,extra=extra)
    assert fit(image) is None


@pytest.mark.parametrize('suffix',['Kreis','Text im Rahmen','zusätzlich ein Kreis','horizontaler Farbverlauf','Haken nach links oben'])
def test_contradictory_description_is_rejected(suffix):
    _,image = synthetic()
    assert fit(image,DESCRIPTION+' '+suffix) is None


def test_umlaut_tokens_preserve_positive_and_negative_description_guards():
    _,image = synthetic()
    assert fit(image,DESCRIPTION.replace('Checkbox','Kästchen')) is not None
    assert fit(image,DESCRIPTION+' zusätzlich ein Symbol') is None


@pytest.mark.parametrize('error',[42.,float('nan'),float('inf')])
def test_invalid_or_constant_objective_is_not_accepted(error):
    _,image = synthetic()
    original = image.copy()
    assert fit(image,error=lambda a,b:error) is None
    np.testing.assert_array_equal(image,original)


def convert(image,name,monkeypatch):
    artifacts,logs = [],[]
    h,w = image.shape[:2]
    monkeypatch.setattr(runtime,'_try_load_sample_svg',lambda **kwargs:pytest.fail('reference read'))
    params = {'mode':'non_composite'}
    result = runtime.runNonCompositeIterationImpl(mode='non_composite',params=params,stripe_strategy=None,
        semantic_mode_visual_override=False,width=w,height=h,base_name=name,description=DESCRIPTION,
        perc_img=image,img_path=name+'.png',print_fn=lambda *args:None,
        render_embedded_raster_svg_fn=lambda path:pytest.fail('raster embedding'),
        build_gradient_stripe_svg_fn=lambda *a,**k:None,
        build_gradient_stripe_validation_log_lines_fn=lambda **k:[],write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=render,record_render_failure_fn=lambda *a,**k:None,
        write_attempt_artifacts_fn=lambda svg,raster:artifacts.append((svg,raster)),
        calculate_error_fn=lambda a,b:calculateErrorImpl(a,b,cv2_module=cv2,np_module=np))
    assert result is not None and logs[-1] == ['status=non_composite_raster_checkbox_checkmark']
    assert params['raster_checkbox_checkmark_v1']['evaluations'] <= 417
    return artifacts[-1]


def test_runtime_filename_invariance_and_real_raster(monkeypatch):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/DLG0031.jpg'))
    first,a = convert(image,'neutral_alpha',monkeypatch)
    second,b = convert(image,'neutral_omega',monkeypatch)
    assert first == second and checkbox_checkmark_semantics(first) == 1
    np.testing.assert_array_equal(a,b)
    assert normalized_mse(image,a)[1] < .01


def test_measures_exact_render_and_rejects_topology_mutations(tmp_path):
    svg,image = synthetic()
    assert checkbox_checkmark_semantics(svg) == 1
    source,vector = tmp_path/'source.png',tmp_path/'vector.svg'
    cv2.imwrite(str(source),image)
    vector.write_text(svg,encoding='utf-8')
    record = measure(source,vector)
    assert record['mean_delta2'] == 0 and record['combined_score'] == 1
    for bad in (svg.replace('<rect','<ellipse'),svg.replace('#ffffff','#dddddd'),
                svg.replace('26,31','26,5'),svg.replace('</svg>','<circle r="2"/></svg>'),
                svg.replace('y2="1"','y2="0"')):
        assert checkbox_checkmark_semantics(bad) == 0
