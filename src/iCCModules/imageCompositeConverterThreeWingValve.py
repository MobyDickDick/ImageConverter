"""Closed description of three joined wings and a crossed square on the right.

The language declares all shapes and connections before raster registration.
No residual reconstruction or catalog-specific geometry is used.
"""
from __future__ import annotations

import re
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality


def three_wing_valve_spec(description):
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description
    words = ' '.join(normalize_description(description).casefold().split())
    clauses = (
        r'(?:ein )?(?:3-wege-ventil|dreiwegeventil) mit drei spitzen dreiecken links, oben und unten, die sich in einer gemeinsamen spitze treffen',
        r'die dreiecke haben einen diagonalen (?:grau|graustufen|farb)verlauf von dunkel links unten nach hell rechts oben und eine graue randkontur',
        r'von der gemeinsamen spitze führt ein waagerechter gerader griff nach rechts zur linken seite (?:einem|eines) hellen quadrat(?:s)? mit dunkler randkontur',
        r'die (?:beiden )?diagonalen des quadrats sind dunkelgrau gezeichnet',
        r'keine weiteren objekte',
        r'ma(?:ß|ss)e und farben ergeben sich aus dem bild',
    )
    for clause in clauses:
        match = re.match(clause+r'(?:[.;]\s*|$)', words)
        if match is None:
            return None
        words = words[match.end():]
    return dict(motor='square', handle='right') if not words else None


def validate_three_wing_valve(svg):
    from PIL import ImageColor
    from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform
    from src.iCCModules.imageCompositeConverterRepresentation import path_points, EXCLUDED
    from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles
    root = ET.fromstring(inline_simple_svg_styles(svg))
    triangles, squares, lines = [], [], []

    def visit(node, parent=(1., 0., 0., 1., 0., 0.), inherited=None):
        kind = node.tag.rsplit('}', 1)[-1]
        if kind in EXCLUDED:
            return
        style = dict(inherited or dict(fill='black', stroke='none'))
        style.update({k: node.get(k, v) for k, v in style.items()})
        matrix = _compose(parent, _transform(node.get('transform', '')))
        a, b, c, d, tx, ty = matrix
        def mapped(points):
            return np.asarray(points) @ np.array([[a, b], [c, d]]) + [tx, ty]
        if kind == 'rect' and style['stroke'] != 'none':
            x, y, w, h = (float(node.get(k, '0')) for k in ('x', 'y', 'width', 'height'))
            points = mapped([[x,y], [x+w,y], [x+w,y+h], [x,y+h]])
            edges = np.roll(points, -1, axis=0)-points
            lengths = np.linalg.norm(edges, axis=1)
            if min(lengths) <= 0 or not np.allclose(lengths, lengths[0]) or abs(edges[0]@edges[1]) > 1e-5:
                raise ValueError('three_wing_valve_deformed_square')
            squares.append((points,style['fill'],style['stroke']))
        elif kind == 'line':
            lines.append((mapped([[float(node.get(k, '0')) for k in ('x1','y1')],
                                  [float(node.get(k, '0')) for k in ('x2','y2')]]),style['stroke']))
        elif kind in {'polygon', 'path'}:
            paths = path_points(node)
            if len(paths) == 1 and paths[0][1]:
                points = paths[0][0]
                if len(points)>3 and np.allclose(points[0],points[-1]):
                    points = points[:-1]
                if len(points) == 3:
                    triangles.append((mapped(points), style['fill'], style['stroke']))
        for child in node:
            visit(child, matrix, style)
    visit(root)
    if len(triangles)!=3 or len(squares)!=1 or len(lines)!=3:
        raise ValueError('three_wing_valve_incomplete')
    shared = [point for point in triangles[0][0]
              if all(np.min(np.linalg.norm(points-point,axis=1))<1e-4 for points,_,_ in triangles[1:])]
    if len(shared)!=1:
        raise ValueError('three_wing_valve_disconnected_apex')
    apex = shared[0]
    directions = []
    def gray(paint):
        color=ImageColor.getrgb(paint)
        if max(color)-min(color)>2:
            raise ValueError('three_wing_valve_gray_paint')
        return float(np.mean(color))
    for points, paint, stroke in triangles:
        base = points[np.linalg.norm(points-apex,axis=1)>1e-4]
        if len(base)!=2 or stroke=='none':
            raise ValueError('three_wing_valve_wing_border')
        gray(stroke)
        if (np.all(base[:,0]<apex[0]) and abs(base[0,0]-base[1,0])<1e-4
                and min(base[:,1])<apex[1]<max(base[:,1])):
            directions.append('left')
        elif abs(base[0,1]-base[1,1])<1e-4 and min(base[:,0])<apex[0]<max(base[:,0]):
            directions.append('top' if base[0,1]<apex[1] else 'bottom')
        match = re.fullmatch(r'url\(#([^)]*)\)', paint)
        gradient = next((e for e in root.iter() if match and e.get('id')==match[1]
                         and e.tag.rsplit('}',1)[-1]=='linearGradient'), None)
        if gradient is None or gradient.get('gradientUnits','objectBoundingBox')!='objectBoundingBox':
            raise ValueError('three_wing_valve_gradient')
        def number(key, default):
            value = gradient.get(key,default)
            return float(value.rstrip('%'))/(100 if value.endswith('%') else 1)
        if not (number('x2','1')>number('x1','0') and number('y2','0')<number('y1','0')):
            raise ValueError('three_wing_valve_gradient_direction')
        stops = list(gradient)
        colors = [ImageColor.getrgb(e.get('stop-color','black')) for e in stops]
        if len(colors)<2 or any(max(c)-min(c)>2 for c in colors) or np.mean(colors[0])>=np.mean(colors[-1]):
            raise ValueError('three_wing_valve_gradient_colors')
    if sorted(directions)!=['bottom','left','top']:
        raise ValueError('three_wing_valve_orientation')
    corners,fill,rim = squares[0]
    if gray(fill)-gray(rim)<12:
        raise ValueError('three_wing_valve_light_square')
    if any(gray(paint)>=gray(fill)-12 for _,paint in lines):
        raise ValueError('three_wing_valve_dark_lines')
    remaining = list(lines)
    for endpoints in (corners[[0,2]],corners[[1,3]]):
        found = next((i for i,(p,_) in enumerate(remaining) if np.allclose(p,endpoints,atol=1e-4)
                      or np.allclose(p[::-1],endpoints,atol=1e-4)),None)
        if found is None:
            raise ValueError('three_wing_valve_diagonals')
        remaining.pop(found)
    connection = (corners[0]+corners[3])/2
    endpoints = np.array([apex,connection])
    if (connection[0]<=apex[0] or abs(connection[1]-apex[1])>1e-4
            or not (np.allclose(remaining[0][0],endpoints,atol=1e-4)
                    or np.allclose(remaining[0][0][::-1],endpoints,atol=1e-4))):
        raise ValueError('three_wing_valve_handle')


def fit_three_wing_valve(width, height, *, description, image, render_fn, error_fn):
    if three_wing_valve_spec(description) is None:
        return None
    pixels = _image(width,height,image)
    if pixels is None:
        return None
    background = np.median(np.concatenate((pixels[0],pixels[-1],pixels[:,0],pixels[:,-1])),axis=0)
    mask = np.max(abs(pixels-background),axis=2)>35
    spans = np.array([np.ptp(np.flatnonzero(col))+1 if col.any() else 0 for col in mask.T])
    candidates = np.flatnonzero((spans>0)&(spans<=max(3,height*.12))
                               &(np.arange(width)>width*.3)&(np.arange(width)<width*.85))
    if not len(candidates):
        return None
    neck = candidates[-1]
    sy,sx = np.nonzero(mask[:,neck+1:])
    if len(sx)<12:
        return None
    sx = sx+neck+1
    cx,cy = (sx.min()+sx.max()+1)/2,(sy.min()+sy.max()+1)/2
    radius = (np.ptp(sx)+np.ptp(sy))/4
    head = mask.copy(); head[:,neck:] = False
    hy,hx = np.nonzero(head)
    if len(hx)<20:
        return None
    top,bottom,left = hy.min(),hy.max(),hx.min()
    # Observe the exposed horizontal bases, vertical left base and stem axis.
    upper = np.flatnonzero(head[top])+.5
    lower = np.flatnonzero(head[bottom])+.5
    left_rows = np.flatnonzero(head[:,left])+.5
    if min(len(upper),len(lower),len(left_rows))<3:
        return None
    # Apex follows from the two observed upper wing edges, rather than the
    # connector silhouette (which extends all the way to the actuator).
    samples=[]
    for row in range(top+1,int(top+(cy-top)*.65)):
        cols=np.flatnonzero(head[row])
        if len(cols)>=3 and cols[0]>left+2:
            samples.append((row+.5,cols[0]+.5,cols[-1]+.5))
    if len(samples)<3:
        return None
    samples=np.array(samples)
    ax=np.mean([np.polyval(np.polyfit(samples[:,0],samples[:,i],1),cy) for i in (1,2)])
    square_pixels = pixels[sy.min():sy.max()+1,sx.min():sx.max()+1]
    fill = np.percentile(square_pixels.reshape(-1,3),85)
    rim = np.percentile(square_pixels.reshape(-1,3),12)
    edge = np.percentile(pixels[head],15)
    p=np.r_[ax,cy,left+.5,left_rows.min(),left_rows.max(),upper.min(),upper.max(),top+.5,
            lower.min(),lower.max(),min(bottom+.5,height-1.),cx,radius,1.4,1.7,2.,
            [170.,225.]*3,edge,fill,rim,background.mean()]

    def build(v):
        ax,ay,lx,lt,lb,tl,tr,ty,bl,br,by,cx,r,sw,bw,cw=v[:16]
        edge,fill,rim,bg=v[22:26]
        triangles=[(ax,ay,lx,lt,lx,lb),(ax,ay,tl,ty,tr,ty),(ax,ay,bl,by,br,by)]
        gradients=''.join(f'<linearGradient id="wing{i}" x1="0%" y1="100%" x2="100%" y2="0%">'
                          f'<stop offset="0" stop-color="{_hex([lo]*3)}"/>'
                          f'<stop offset="1" stop-color="{_hex([hi]*3)}"/></linearGradient>'
                          for i,(lo,hi) in enumerate(v[16:22].reshape(3,2)))
        wings=''.join(f'<path d="M {a:.5f} {b:.5f} L {c:.5f} {d:.5f} L {e:.5f} {f:.5f} Z" '
                      f'fill="url(#wing{i})" stroke="{_hex([edge]*3)}" stroke-width="{bw:.5f}" stroke-linejoin="round"/>'
                      for i,(a,b,c,d,e,f) in enumerate(triangles))
        diagonals=''.join(f'<line x1="{cx-r:.5f}" y1="{a:.5f}" x2="{cx+r:.5f}" y2="{b:.5f}" '
                          f'stroke="{_hex([rim]*3)}" stroke-width="{sw:.5f}"/>'
                          for a,b in ((ay-r,ay+r),(ay+r,ay-r)))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs>{gradients}</defs><rect width="{width}" height="{height}" fill="{_hex([bg]*3)}"/>'
                f'<line x1="{ax:.5f}" y1="{ay:.5f}" x2="{cx-r:.5f}" y2="{ay:.5f}" '
                f'stroke="{_hex([rim]*3)}" stroke-width="{cw:.5f}"/>'+wings+
                f'<rect x="{cx-r:.5f}" y="{ay-r:.5f}" width="{2*r:.5f}" height="{2*r:.5f}" '
                f'fill="{_hex([fill]*3)}" stroke="{_hex([rim]*3)}" stroke-width="{sw:.5f}"/>'+diagonals+'</svg>')

    def valid(v):
        ax,ay,lx,lt,lb,tl,tr,ty,bl,br,by,cx,r,sw,bw,cw=v[:16]
        return (np.isfinite(v).all() and r>3 and lx<ax<cx-r and tl<ax<tr and bl<ax<br
                and ty<ay<by and lt<ay<lb and .3<=min(sw,bw,cw) and max(sw,bw,cw)<r*.5
                and min(lx-bw/2,tl-bw/2,bl-bw/2,ty-bw/2)>=0
                and max(lb+bw/2,by+bw/2,ay+r+sw/2)<=height
                and ay-r-sw/2>=0 and cx+r+sw/2<=width
                and all(hi-lo>=2 for lo,hi in v[16:22].reshape(3,2))
                and np.all((v[16:]>=0)&(v[16:]<=255)))
    result=_register(p,16,build,valid,image,render_fn,error_fn,'description_three_wing_valve_v1',
                     allow_portfolio=False,max_evaluations=2400,reconsider_after=0)
    if result is None:
        return None
    quality=pixel_quality(image,result['rendered'])
    if not quality or not quality['passed']:
        return None
    validate_three_wing_valve(result['svg'])
    result['quality']=quality
    return result
