from pathlib import Path
import json

import cv2
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules.imageCompositeConverterSquareStem import fit_square_stem
from tests.test_rotated_square_kelle_runtime import _convert
from tools.evaluate_top_stem_square_recheck import measure, symbol_semantics
from tools.run_plan_b_variations import render
from tools.review_conversion_quality import normalized_mse

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'artifacts/evaluation/top_stem_marked_square_recheck_v1/manifest.json'
DESCRIPTION=json.loads(MANIFEST.read_text(encoding='utf-8'))['cases'][0]['description']


@pytest.mark.parametrize('variant',['AC0713_1_L','AC0713_1_M','AC0713_1_S','AC0713_L','AC0713_M','AC0713_S'])
def test_runtime_registers_both_marks_in_all_catalog_sizes(variant,monkeypatch):
    import tests.test_rotated_square_kelle_runtime as helper
    monkeypatch.setattr(helper,'DESCRIPTION',DESCRIPTION)
    image=cv2.imread(str(ROOT/'artifacts/images_to_convert'/(variant+'.jpg')))
    (svg,raster),_=helper._convert(image,'anonymous_top_square',monkeypatch)
    assert symbol_semantics(svg)==1.
    assert normalized_mse(image,raster)[1]<.001


def fit(image,ir):
    h,w=image.shape[:2]
    return fit_square_stem(ir,image=image,description=DESCRIPTION,
        render_fn=lambda candidate:render(geometry.renderGeometryIrToSvgImpl(w,h,candidate),w,h),
        error_fn=lambda raster:normalized_mse(image,raster)[0])


def test_marked_runtime_output_is_independent_of_filename(monkeypatch):
    import tests.test_rotated_square_kelle_runtime as helper
    monkeypatch.setattr(helper,'DESCRIPTION',DESCRIPTION)
    image=cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0713_1_M.jpg'))
    (svg,raster),_=helper._convert(image,'AC0713_1_M',monkeypatch)
    (renamed,renamed_raster),_=helper._convert(image,'unrelated_holdout',monkeypatch)
    assert renamed==svg
    np.testing.assert_array_equal(renamed_raster,raster)


@pytest.mark.parametrize('scale,offset,fill,ink',[(1,.25,'#244ca0','#e8dfc1'),(2,.5,'#36a050','#222a30'),(1,0.,'#dddddd','#555555')])
def test_independent_positions_colors_and_resolutions(scale,offset,fill,ink):
    w,h=60*scale,90*scale
    ir=geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION)
    x,y,bw,bh=(10*scale+offset,40*scale+offset,36*scale,36*scale)
    ir[0].update(body_bbox=[x/w,y/h,bw/w,bh/h],connector=[[(x+bw/2)/w,y/h],[(x+bw/2)/w,5*scale/h]],
                 body_fill=fill,body_stroke='#707070',body_stroke_width=1.5*scale/min(w,h),connector_width=2*scale/min(w,h))
    source=geometry.renderGeometryIrToSvgImpl(w,h,ir)
    tx,ty,bx,by=34*scale+offset,48*scale+offset,27*scale+offset,68*scale+offset
    source=source.replace('</svg>',f'<path d="M {tx-scale} {ty} L {tx+scale} {ty} L {bx+scale} {by} L {bx-scale} {by} Z" fill="{ink}"/>'
        f'<path d="M {20*scale+offset} {64*scale+offset} L {23*scale+offset} {64*scale+offset} L {23*scale+offset} {67*scale+offset} L {20*scale+offset} {67*scale+offset} Z" fill="{ink}"/></svg>')
    fitted=fit(render(source,w,h),ir)
    assert fitted is not None
    assert fitted['final_error']<fitted['initial_error']*.1
    svg=geometry.renderGeometryIrToSvgImpl(w,h,fitted['geometry_ir'])
    assert symbol_semantics(svg)==1.
    assert '<text' not in svg and '<image' not in svg


@pytest.mark.parametrize('change',['missing_dot','missing_slash','wrong_slash','wrong_dot','extra_object'])
def test_observer_rejects_incomplete_or_different_topology(change):
    import re
    root=MANIFEST.parent
    svg=(root/'after/anonymous_symbol_00.svg').read_text(encoding='utf-8')
    if change.startswith('missing_'):
        svg=re.sub(r'\s*<path id="raster_interior_'+change.removeprefix('missing_')+r'"[^>]*/>','',svg)
    elif change=='wrong_slash':
        svg=svg.replace('14.436 21.875','11.354 21.875').replace('16.533 21.875','13.451 21.875')
    elif change=='wrong_dot':
        svg=svg.replace('8.125 32','18.125 32').replace('10.5 32','20.5 32').replace('10.5 34.625','20.5 34.625').replace('8.125 34.625','18.125 34.625')
    else:
        svg=svg.replace('</svg>','<circle cx="3" cy="5" r="2" fill="black"/></svg>')
    assert fit(render(svg,25,45),geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION)) is None


def test_saved_vectors_require_both_marks_and_calibrate_metrics(tmp_path):
    root=MANIFEST.parent
    svg=(root/'after/anonymous_symbol_00.svg').read_text(encoding='utf-8')
    image=tmp_path/'perfect.png';vector=tmp_path/'perfect.svg'
    vector.write_text(svg,encoding='utf-8')
    assert cv2.imwrite(str(image),render(svg,25,45))
    measured=measure(image,vector)
    assert measured['mean_delta2']==0.
    assert all(value==1. for key,value in measured['metrics'].items() if key!='error_per_pixel')
    assert symbol_semantics(svg.replace('raster_interior_dot','unrelated_name'))==1.
    assert symbol_semantics(svg.replace('L 10.5 32','L 10.5 31'))==0.


def test_unavailable_rendering_and_nonfinite_input_do_not_accept():
    ir=geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION)
    image=render((MANIFEST.parent/'after/anonymous_symbol_00.svg').read_text(encoding='utf-8'),25,45)
    assert fit_square_stem(ir,image=image,description=DESCRIPTION,render_fn=lambda _:None,error_fn=lambda _:0.) is None
    assert fit(np.full((45,25,3),np.nan),ir) is None
