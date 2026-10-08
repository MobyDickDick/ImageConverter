from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterAlarmBell import fit_alarm_bell
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_alarm_bell_recheck import alarm_bell_semantics
from tools.run_plan_b_variations import measure_quality

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT/'artifacts/evaluation/alarm_bell_recheck_v1/manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg,width,height,fitz_module=fitz,np_module=np,cv2_module=cv2)


def error(a,b):
    return calculateErrorImpl(a,b,cv2_module=cv2,np_module=np)


def fit(image, description=DESCRIPTION, objective=error):
    h,w = image.shape[:2]
    return fit_alarm_bell(w,h,description=description,image=image,render_fn=render,error_fn=objective)


@pytest.mark.parametrize('case',MANIFEST['cases'],ids=lambda c:c['source'])
def test_real_raster_registration_preserves_bell_topology_and_passes_both_gates(case):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['source']))
    result = fit(image,case['description'])
    assert result is not None and result['error']<result['initial_error']
    assert result['evaluations']<=1746 and alarm_bell_semantics(result['svg'])==1
    assert '<image' not in result['svg']
    # The common gates are exercised by the CLI recheck; the stricter Plan-B
    # pixel and contour limits also hold for the three filled size variants.
    if 'neutral' not in case['source']:
        assert measure_quality(image,result['svg'])['satisfactory']


def synthetic(scale=1, shift=0, blue=False, omit=None):
    # Independent geometry: no fitted target parameters or production builder.
    high, low = ('#4488dd','#183b99') if blue else ('#e74c30','#a41722')
    body = (f'M {20+shift} 8 C {11+shift} 8 {10+shift} 12 {10+shift} 17 '
            f'C {10+shift} 25 {9+shift} 26 {5+shift} 32 L {35+shift} 32 '
            f'C {31+shift} 26 {30+shift} 25 {30+shift} 17 '
            f'C {30+shift} 12 {29+shift} 8 {20+shift} 8 Z')
    parts = [f'<path d="{body}" fill="url(#shade)" stroke="#915c60" stroke-width="1"/>',
             f'<ellipse cx="{20+shift}" cy="32" rx="15" ry="4" fill="{low}" stroke="#915c60" stroke-width="1"/>']
    if omit!='clapper':
        parts.append(f'<ellipse cx="{13+shift}" cy="31" rx="3" ry="2" fill="#eeeeee"/>')
    for i,coords in enumerate(((12,1,2,4,1,15),(14,5,7,8,6,17),(28,1,38,4,39,15),(26,5,33,8,34,17))):
        if omit=='waves' or omit==f'wave_{i}':
            continue
        a,b,c,d,e,f = coords
        parts.append(f'<path d="M {a+shift} {b} Q {c+shift} {d} {e+shift} {f}" fill="none" stroke="#a07070" stroke-width="1.5"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{42*scale}" height="{40*scale}" viewBox="0 0 42 40">'
           f'<defs><linearGradient id="shade" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{high}"/>'
           f'<stop offset="1" stop-color="{low}"/></linearGradient></defs>'+''.join(parts)+'</svg>')
    return render(svg,42*scale,40*scale)


@pytest.mark.parametrize('scale,shift,blue',[(1,0,False),(1,2,True),(2,0,True)])
def test_independent_color_position_and_resolution_holdouts(scale,shift,blue):
    image = synthetic(scale,shift,blue)
    result = fit(image)
    assert result is not None and alarm_bell_semantics(result['svg'])==1
    assert result['error']<15 and result['evaluations']<=1746


@pytest.mark.parametrize('omit',['waves','wave_0','clapper'])
def test_missing_claimed_structure_has_no_registration(omit):
    assert fit(synthetic(omit=omit)) is None


def test_additional_isolated_object_is_not_silently_ignored():
    image = synthetic()
    cv2.rectangle(image,(38,35),(41,39),(0,0,0),-1)
    assert fit(image) is None


@pytest.mark.parametrize('invalid',[np.full((40,42,3),255,np.uint8),np.zeros((40,42)),
                                    np.full((40,42,3),float('nan'))])
def test_absent_or_invalid_raster_evidence_is_rejected(invalid):
    assert fit(invalid) is None


@pytest.mark.parametrize('suffix',['drei Schallwellen','zusätzlich ein Quadrat','umgekehrt','ohne Klöppel','horizontaler Verlauf'])
def test_contradictory_description_is_rejected(suffix):
    assert fit(synthetic(),DESCRIPTION+' '+suffix) is None


@pytest.mark.parametrize('value',[42.,float('nan'),float('inf')])
def test_constant_or_nonfinite_objective_cannot_supply_registration_evidence(value):
    image = synthetic()
    original = image.copy()
    assert fit(image,objective=lambda a,b:value) is None
    np.testing.assert_array_equal(image,original)


def test_runtime_and_reflection_use_raster_and_description_with_neutral_names(monkeypatch):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/GE1420_S.jpg'))
    monkeypatch.setattr(runtime,'_try_load_sample_svg',lambda **kw:pytest.fail('reference read'))
    outputs = []
    for name in ('anonymous_alpha','anonymous_omega'):
        description,params = Reflection({name:DESCRIPTION}).parseDescription(name,name+'.jpg')
        assert params['mode']=='auto' and params['contract_status']=='ok'
        logs = []
        h,w = image.shape[:2]
        result = runtime.runNonCompositeIterationImpl(mode='auto',params=params,stripe_strategy=None,
            semantic_mode_visual_override=False,width=w,height=h,base_name=name,description=description,
            perc_img=image,img_path=name+'.jpg',print_fn=lambda *a:None,
            render_embedded_raster_svg_fn=lambda *a:pytest.fail('embedded raster'),
            build_gradient_stripe_svg_fn=lambda *a,**k:None,
            build_gradient_stripe_validation_log_lines_fn=lambda **k:[],write_validation_log_fn=logs.append,
            render_svg_to_numpy_fn=render,record_render_failure_fn=lambda *a,**k:None,
            write_attempt_artifacts_fn=lambda s,r:outputs.append((s,r)),calculate_error_fn=error)
        assert result is not None and logs[-1]==['status=non_composite_raster_alarm_bell']
        assert params['raster_alarm_bell_v1']['evaluations']<=1746
    assert outputs[0][0]==outputs[1][0]
    np.testing.assert_array_equal(outputs[0][1],outputs[1][1])


def test_semantic_measurement_rejects_missing_and_misplaced_marks():
    result = fit(synthetic())
    assert result is not None
    svg = result['svg']
    assert alarm_bell_semantics(svg)==1
    root = ET.fromstring(svg)
    clapper = next(e for e in root if e.get('data-role')=='clapper')
    clapper.set('cx','1000')
    assert alarm_bell_semantics(ET.tostring(root,encoding='unicode'))==0
    root = ET.fromstring(svg)
    root.remove(next(e for e in root if e.get('data-role')=='wave_0'))
    assert alarm_bell_semantics(ET.tostring(root,encoding='unicode'))==0


def test_catalog_descriptions_distinguish_neutral_outline_from_filled_sizes():
    from src.iCCModules.imageCompositeConverterDescriptions import loadDescriptionMappingImpl
    from src.iCCModules.imageCompositeConverterNaming import getBaseNameFromFileImpl
    for directory in ('descriptions','images_to_convert'):
        mapping = loadDescriptionMappingImpl(str(ROOT/'artifacts'/directory/'Finale_Wurzelformen_V3.xml'),
                                            get_base_name_from_file_fn=getBaseNameFromFileImpl)
        for name in ('GE1420_S','GE1420_M','GE1420_L'):
            assert mapping[name]==DESCRIPTION
        assert mapping['GE1420_M_neutral']==MANIFEST['neutral_description']
