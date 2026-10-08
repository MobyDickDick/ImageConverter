from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterThreeWayValve import fit_three_way_valve
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.run_plan_b_variations import make_variations, measure_quality
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('3-Wege-Ventilkopf oben mit drei spitzen Ventilflügeln; darunter ein senkrechter Griff nach unten '
               'zu einem hellen Quadrat mit grauem Rand und beiden Diagonalen.')


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg,width,height,fitz_module=fitz,np_module=np,cv2_module=cv2)


def fit(image, description=DESCRIPTION, render_fn=render, error_fn=None):
    return fit_three_way_valve(image.shape[1],image.shape[0],description=description,image=image,
        render_fn=render_fn,error_fn=error_fn or (lambda a,b:normalized_mse(a,b)[0]))


@pytest.mark.parametrize('index', [0,3,8,15])
def test_frozen_ci_seed_with_crop_scale_and_translation_passes_unchanged_gates(index):
    source = ROOT/'artifacts/images_to_convert/samples/AC0223_L_sia.svg'
    case = make_variations(source.read_text(encoding='utf-8'),DESCRIPTION,5321758631963497707)[index]
    image = render(case['svg'],case['width'],case['height'])
    result = fit(image)
    assert result is not None
    assert result['error'] < result['initial_error']
    assert measure_quality(image,result['svg'])['satisfactory']
    shapes = [e.tag.rsplit('}',1)[-1] for e in ET.fromstring(result['svg']).iter()]
    assert shapes.count('polygon') == 3 and shapes.count('image') == 0


def synthetic(scale=1, color='#182e68', wing=True, cross=True, extra=''):
    w,h = 72*scale,80*scale
    polygons = [(30,29,7,17,7,41), (30,29,53,17,53,41)]
    if wing:
        polygons.append((30,29,19,7,41,7))
    shapes = ''.join(f'<polygon points="{a*scale},{b*scale} {c*scale},{d*scale} {e*scale},{f*scale}" '
                     f'fill="{color}" stroke="#999999" stroke-width="{scale}"/>' for a,b,c,d,e,f in polygons)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
           f'<line x1="{30*scale}" y1="{29*scale}" x2="{30*scale}" y2="{51*scale}" stroke="#888888" stroke-width="{2*scale}"/>'
           f'{shapes}<rect x="{20*scale}" y="{51*scale}" width="{20*scale}" height="{20*scale}" fill="#ededed" stroke="#999999" stroke-width="{scale}"/>'
           + (f'<path d="M {20*scale},{51*scale} l {20*scale},{20*scale} M {40*scale},{51*scale} l {-20*scale},{20*scale}" '
              f'fill="none" stroke="#999999" stroke-width="{scale}"/>' if cross else '')+extra+'</svg>')
    return svg,render(svg,w,h)


@pytest.mark.parametrize('scale,color',[(1,'#182e68'),(2,'#704030')])
def test_raster_observation_generalizes_position_size_and_color(scale,color):
    _,image = synthetic(scale,color)
    result = fit(image)
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']


@pytest.mark.parametrize('kind',['missing_wing','missing_cross','extra'])
def test_other_topologies_are_rejected(kind):
    _,image = synthetic(wing=kind!='missing_wing',cross=kind!='missing_cross',
                       extra='<circle cx="63" cy="68" r="5" fill="#222222"/>' if kind=='extra' else '')
    assert fit(image) is None


def test_constraints_and_failed_renderer_do_not_produce_an_output():
    _,image = synthetic()
    assert fit(image, DESCRIPTION.replace('oben','links')) is None
    assert fit(image, DESCRIPTION+' Zusätzlich ein Kreis.') is None
    assert fit(image, render_fn=lambda *args:None) is None
    assert fit(image, error_fn=lambda *args:float('inf')) is None


def test_real_auto_dispatch_is_filename_invariant_and_catalog_free(monkeypatch):
    _,image = synthetic()
    monkeypatch.setattr(runtime,'_try_load_sample_svg',lambda **kw:pytest.fail('reference read'))
    outputs = []
    for name in ('foreign_valve','unrelated_holdout'):
        logs,params = [],{}
        result = runtime.runNonCompositeIterationImpl(mode='auto',params=params,stripe_strategy=None,
            semantic_mode_visual_override=False,width=image.shape[1],height=image.shape[0],
            base_name=name,description=DESCRIPTION,perc_img=image,img_path=name+'.png',print_fn=lambda *args:None,
            render_embedded_raster_svg_fn=lambda *args:pytest.fail('raster embedding'),
            build_gradient_stripe_svg_fn=lambda *args,**kw:None,build_gradient_stripe_validation_log_lines_fn=lambda **kw:[],
            write_validation_log_fn=logs.append,render_svg_to_numpy_fn=render,
            record_render_failure_fn=lambda *args,**kw:None,write_attempt_artifacts_fn=lambda svg,raster:outputs.append((svg,raster)),
            calculate_error_fn=lambda a,b:normalized_mse(a,b)[0])
        assert result is not None and 'raster_three_way_valve_v1' in params
        assert logs[-1] == ['status=non_composite_raster_three_way_valve']
    assert outputs[0][0] == outputs[1][0]
    np.testing.assert_array_equal(outputs[0][1],outputs[1][1])
