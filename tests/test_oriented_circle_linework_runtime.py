"""Source-space circle linework registration in every declared direction."""
from pathlib import Path
import json
from xml.etree import ElementTree as ET
import cv2
import fitz
import numpy as np
import pytest
from src.iCCModules.imageCompositeConverterCircleLinework import fit_circle_linework
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_oriented_circle_linework_recheck import symbol_semantics
from tools.run_plan_b_variations import measure_quality
from tools.review_conversion_quality import normalized_mse
ET.register_namespace('', 'http://www.w3.org/2000/svg')
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/'artifacts/evaluation/oriented_circle_linework_recheck_v1/manifest.json').read_text(encoding='utf-8'))
DOWN=next(c['description'] for c in MANIFEST['cases'] if c['direction']=='down')
LEFT=MANIFEST['cases'][0]['description']
def render(svg,w,h):
    return render_svg_to_numpy_inprocess(svg,w,h,fitz_module=fitz,np_module=np,cv2_module=cv2)
def fit(image,description):
    h,w=image.shape[:2]
    return fit_circle_linework(w,h,description=description,image=image,render_fn=render,error_fn=lambda a,b: normalized_mse(a,b)[0])
def independent_svg(scale=1, shift=0, color='#315c94', radius=22, slope=.38):
    cx, cy = 36+shift, 32
    chords = []
    for sign in (-1, 1):
        a, b = -sign*slope, sign*radius*.6
        ys = np.sort(np.roots([1+a*a, 2*a*b, b*b-radius*radius]))
        chords.append([(cx+a*y+b, cy+y) for y in ys])
    top = cy-radius*.5
    segments = [*chords, [(cx-radius*.63, top), (cx+radius*.63, top)], [(cx, top), (cx, cy+radius*.77)]]
    lines = ''.join(f'<line x1="{a[0]*scale:g}" y1="{a[1]*scale:g}" x2="{b[0]*scale:g}" y2="{b[1]*scale:g}" '
                    f'stroke="#eef0da" stroke-width="{1.2*scale:g}"/>' for a, b in segments)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{80*scale:g}" height="{68*scale:g}">'
            f'<rect width="{80*scale:g}" height="{68*scale:g}" fill="#ffffff"/>'
            f'<circle cx="{cx*scale:g}" cy="{cy*scale:g}" r="{radius*scale:g}" '
            f'fill="{color}" stroke="#747474" stroke-width="{scale:g}"/>{lines}</svg>')



def oriented_source(direction,scale=1,shift=0,color='#315c94'):
    root=ET.fromstring(independent_svg(scale,shift,color))
    w,h=float(root.get('width')),float(root.get('height'))
    def point(x,y):
        return {'down':(x,y),'left':(h-y,x),'up':(w-x,h-y),'right':(y,w-x)}[direction]
    for e in root:
        tag=e.tag.rsplit('}',1)[-1]
        pairs=[('cx','cy')] if tag=='circle' else [('x1','y1'),('x2','y2')] if tag=='line' else []
        for xk,yk in pairs:
            x,y=point(float(e.get(xk)),float(e.get(yk))); e.set(xk,str(x));e.set(yk,str(y))
        if tag=='rect' and direction in ('left','right'):
            e.set('width',str(h));e.set('height',str(w))
    if direction in ('left','right'): root.set('width',str(h));root.set('height',str(w))
    return ET.tostring(root,encoding='unicode')

def description(direction):
    return DOWN.replace('nach unten','nach '+{'down':'unten','left':'links','up':'oben','right':'rechts'}[direction])

@pytest.mark.parametrize('case',MANIFEST['cases'],ids=lambda c:c['source'])
def test_catalog_family(case):
    image=cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['source']))
    original=image.copy(); result=fit(image,case['description'])
    assert result is not None
    assert symbol_semantics(result['svg'],case['direction'])==1
    assert result['error']<=result['initial_error']
    strict=measure_quality(image,result['svg'])
    if case['source'] in ('AC0414_L.jpg','AC0414_M.jpg','AC0414_S.jpg'):
        assert strict['failures']==['foreground_iou_outside_limit']
        assert normalized_mse(image,result['rendered'])[1]<.002
    else:
        assert strict['satisfactory']
    np.testing.assert_array_equal(image,original)

@pytest.mark.parametrize('direction',['down','left','up','right'])
@pytest.mark.parametrize('scale,shift,color',[(1,0,'#315c94'),(.5,0,'#62497a'),(2,-5,'#39715f'),(1,.25,'#913b28')])
def test_independent_directions_colors_sizes_positions(direction,scale,shift,color):
    svg=oriented_source(direction,scale,shift,color); root=ET.fromstring(svg)
    image=render(svg,int(float(root.get('width'))),int(float(root.get('height'))))
    result=fit(image,description(direction))
    assert result is not None
    assert symbol_semantics(result['svg'],direction)==1
    assert result['error']<=result['initial_error']
    assert measure_quality(image,result['svg'])['satisfactory']
    np.testing.assert_array_equal(result['rendered'],render(result['svg'],image.shape[1],image.shape[0]))

@pytest.mark.parametrize('which',range(4))
@pytest.mark.parametrize('direction',['left','up','right'])
def test_missing_strokes_rejected(which,direction):
    root=ET.fromstring(oriented_source(direction));root.remove([e for e in root if e.tag.endswith('line')][which])
    image=render(ET.tostring(root,encoding='unicode'),int(float(root.get('width'))),int(float(root.get('height'))))
    assert fit(image,description(direction)) is None

@pytest.mark.parametrize('text',['Ein Quadrat.',LEFT+' Zus\u00e4tzlich ein Punkt.',LEFT+' Nach oben.',LEFT+' Ohne T.'])
def test_contradictory_descriptions_rejected(text):
    assert fit(render(oriented_source('left'),68,80),text) is None

@pytest.mark.parametrize('direction',['left','up','right'])
@pytest.mark.parametrize('location',['inside','outside'])
def test_additional_marks_rejected(direction,location):
    root=ET.fromstring(oriented_source(direction))
    w,h=int(float(root.get('width'))),int(float(root.get('height')))
    # Rotate the same independent extra dot with the motif.
    x,y={'left':(35,30),'up':(50,35),'right':(33,50)}[direction] if location=='inside' else (w-6,h-8)
    ET.SubElement(root,'{http://www.w3.org/2000/svg}circle',cx=str(x),cy=str(y),r='3',fill='#111111')
    assert fit(render(ET.tostring(root,encoding='unicode'),w,h),description(direction)) is None
