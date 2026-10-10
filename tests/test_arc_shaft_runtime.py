from pathlib import Path
import json

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterArcShaft import fit_arc_shaft
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_arc_shaft_recheck import symbol_semantics
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT/'artifacts/evaluation/arc_shaft_recheck_v1/manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['cases'][0]['description']


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg, w, h, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION, **kwargs):
    h, w = image.shape[:2]
    return fit_arc_shaft(w, h, description=description, image=image,
                         render_fn=kwargs.get('render_fn', render),
                         error_fn=kwargs.get('error_fn', lambda a,b: normalized_mse(a,b)[0]))


def independent_svg(scale=1, shift=0, color='#375c66', rx=24, ry=19, stroke=5):
    cx = 35+shift
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{80*scale}" height="{130*scale}">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{color}"/>'
            f'<stop offset="0.5" stop-color="#dcecef"/><stop offset="1" stop-color="{color}"/></linearGradient></defs>'
            f'<rect width="{80*scale}" height="{130*scale}" fill="#ffffff"/>'
            f'<path d="M {(cx-rx)*scale} {12*scale} A {rx*scale} {ry*scale} 0 0 0 {(cx+rx)*scale} {12*scale}" '
            f'fill="none" stroke="{color}" stroke-width="{stroke*scale}"/>'
            f'<rect x="{(cx-10)*scale}" y="{42*scale}" width="{20*scale}" height="{75*scale}" fill="url(#g)"/></svg>')


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c:c['source'])
def test_catalog_rasters_fit_anonymously_without_mutation(case):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['source']))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error'] <= result['initial_error']
    assert normalized_mse(image,result['rendered'])[1] < .006
    assert symbol_semantics(result['svg']) == 1
    assert result['evaluations'] <= 1+16*len(result['parameters'])
    assert '<image' not in result['svg']
    np.testing.assert_array_equal(image,original)


@pytest.mark.parametrize('scale,shift,color,rx,ry,stroke', [
    (1,0,'#375c66',24,19,5), (1,9,'#753627',19,24,4),
    (2,-3,'#265438',25,16,6), (.5,0,'#694882',24,19,5)])
def test_independent_geometry_colors_and_resolution(scale,shift,color,rx,ry,stroke):
    source = independent_svg(scale,shift,color,rx,ry,stroke)
    image = render(source,int(80*scale),int(130*scale))
    result = fit(image)
    assert result is not None
    assert symbol_semantics(source) == symbol_semantics(result['svg']) == 1
    assert normalized_mse(image,result['rendered'])[1] < .006


@pytest.mark.parametrize('failure', ['render','nan','infinity'])
def test_failed_measurements_are_rejected(failure):
    image = render(independent_svg(),80,130)
    kwargs = {'render_fn': lambda *args:None} if failure == 'render' else {'error_fn':lambda *args:float('nan' if failure=='nan' else 'inf')}
    assert fit(image,**kwargs) is None


@pytest.mark.parametrize('description', ['', 'Ein Quadrat.', DESCRIPTION+' Zusätzlich ein Punkt.', DESCRIPTION.replace('oben offen','unten offen')])
def test_wrong_or_unsupported_description_is_rejected(description):
    assert fit(render(independent_svg(),80,130),description) is None


@pytest.mark.parametrize('change', ['missing_arc','missing_shaft','extra_dot','flat_gradient','shifted_shaft','closed_circle','square_u','upward_arc','broken_arc'])
def test_wrong_raster_topologies_are_rejected(change):
    source = independent_svg()
    if change == 'missing_arc':
        import re
        source = re.sub(r'<path[^>]*/>', '', source)
    elif change == 'missing_shaft':
        source = source.replace('<rect x="25" y="42" width="20" height="75" fill="url(#g)"/>','')
    elif change == 'extra_dot':
        source = source.replace('</svg>','<circle cx="70" cy="20" r="4" fill="#333333"/></svg>')
    elif change == 'flat_gradient':
        source = source.replace('#dcecef','#375c66')
    elif change == 'shifted_shaft':
        source = source.replace('x="25"','x="39"')
    elif change == 'closed_circle':
        source = source.replace('M 11 12 A 24 19 0 0 0 59 12','M 11 12 A 24 19 0 0 0 59 12 A 24 19 0 0 0 11 12')
    elif change == 'square_u':
        source = source.replace('M 11 12 A 24 19 0 0 0 59 12','M 11 12 L 11 31 L 59 31 L 59 12')
    elif change == 'upward_arc':
        source = source.replace('0 0 0 59 12','0 0 1 59 12')
    else:
        source = source.replace('</svg>','<rect x="31" y="24" width="8" height="12" fill="#ffffff"/></svg>')
    assert fit(render(source,80,130)) is None


def test_independent_semantics_rejects_wrong_direction_and_contact():
    source = independent_svg()
    assert symbol_semantics(source.replace('0 0 0 59 12','0 0 1 59 12')) == 0
    assert symbol_semantics(source.replace('y="42"','y="30"')) == 0


def test_perfect_synthetic_vectors_calibrate_both_unchanged_gates(tmp_path):
    from tools.evaluate_arc_shaft_recheck import evaluate
    for scale in (1,2):
        source = independent_svg(scale)
        svg = tmp_path/f'ideal_{scale}.svg'; svg.write_text(source)
        image = tmp_path/f'ideal_{scale}.png'
        cv2.imwrite(str(image),render(source,80*scale,130*scale))
        manifest = {'provenance':MANIFEST['provenance'], 'cases':[{'case_id':'ideal','image':image.name,'before_svg':svg.name,'after_svg':svg.name}]}
        report = evaluate(manifest,tmp_path)
        assert report['satisfaction_gate']['cases'][0]['satisfactory']


@pytest.mark.parametrize('horizontal', [True,False])
@pytest.mark.parametrize('rounded', [True,False])
def test_narrow_rectangle_gradient_preserves_native_mask_and_pixel_center_colors(horizontal,rounded):
    import base64
    from xml.etree import ElementTree as ET
    from src.iCCModules.imageCompositeConverterRendering import _expand_rect_linear_gradients_for_fitz
    geometry = 'x="2.25" y="3.5" width="6" height="22"'+(' rx="2"' if rounded else '')
    axis = 'x2="1" y2="0"' if horizontal else 'x2="0" y2="1"'
    source = (f'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="30"><defs>'
              f'<linearGradient id="g" x1="0" y1="0" {axis}>'
              '<stop offset="0" stop-color="#306090"/><stop offset="1" stop-color="#dcecf0"/>'
              f'</linearGradient></defs><rect {geometry} fill="url(#g)"/></svg>')
    private = ET.fromstring(_expand_rect_linear_gradients_for_fitz(source,fitz_module=fitz,size_w=12,size_h=30))
    image = next(e for e in private.iter() if e.tag.endswith('image'))
    png = base64.b64decode(image.get('href').split(',',1)[1])
    rgba = cv2.imdecode(np.frombuffer(png,np.uint8),cv2.IMREAD_UNCHANGED)
    native = f'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="30"><rect {geometry} fill="#ffffff"/></svg>'
    with fitz.open(stream=native.encode(),filetype='svg') as document:
        pix = document[0].get_pixmap(alpha=True)
    alpha = np.frombuffer(pix.samples,np.uint8).reshape(30,12,4)[:,:,3]
    np.testing.assert_array_equal(rgba[:,:,3],alpha)
    position = (np.arange(12)+.5-2.25)/6 if horizontal else (np.arange(30)+.5-3.5)/22
    colors = np.array([144,96,48])+(np.array([240,236,220])-np.array([144,96,48]))*np.clip(position,0,1)[:,None]
    expected = np.broadcast_to(colors[None,:,:] if horizontal else colors[:,None,:],(30,12,3))
    expected = np.rint(expected*alpha[:,:,None]/255).astype(np.uint8)
    # PNG stores straight RGB; the native pixmap uses premultiplied RGB.
    reconstructed = rgba[:,:,:3].astype(float)*alpha[:,:,None]/255
    np.testing.assert_allclose(reconstructed,expected,atol=1)
