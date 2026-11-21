"""A description-declared disk, handle and two joined gradient valve wings.

The bounded language contract declares every primitive before pixels are read.
Raster observations register that fixed construction; no residual shapes,
catalog identifiers or reference vectors are used.
"""
from __future__ import annotations

import re
import cv2
import numpy as np
from xml.etree import ElementTree as ET

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality


def two_way_valve_contract(description):
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description
    words = ' '.join(normalize_description(description).casefold().split())
    # Consume the whole description: an unrecognized addition must never
    # silently authorize an incomplete inventory or a different motor symbol.
    clauses = (
        r'(?:es ist ein |ein )?motorgetriebenes (?:zweiwegventil|2-wege-ventil)',
        r'die beiden ventile sind (?:horizontal|waagerecht) angeordnet',
        r'der motor ist (?:als )?kelle mit griff nach unten realisiert',
        r'bei den ventilen werden die beiden formen zusammengehängt und ein farbverlauf gezeichnet',
    )
    rest = words
    for clause in clauses:
        match = re.match(clause+r'(?:[.;]\s*|\s+|$)', rest)
        if match is None:
            return False
        rest = rest[match.end():]
    return not rest.strip(' .;')


def validate_two_way_valve(svg):
    """Also constrain template edits: shared apex, axial handle and shared paint."""
    from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform
    from src.iCCModules.imageCompositeConverterRepresentation import path_points, EXCLUDED
    from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles
    root = ET.fromstring(inline_simple_svg_styles(svg))
    circles, lines, triangles = [], [], []

    def visit(node, parent=(1.,0.,0.,1.,0.,0.), fill='black'):
        kind = node.tag.rsplit('}',1)[-1]
        if kind in EXCLUDED:
            return
        matrix = _compose(parent,_transform(node.get('transform','')))
        a,b,c,d,tx,ty = matrix
        def mapped(points):
            return np.asarray(points)@np.array([[a,b],[c,d]])+np.array([tx,ty])
        fill = node.get('fill',fill)
        if kind=='circle':
            sx,sy=np.hypot(a,b),np.hypot(c,d)
            if not np.isclose(sx,sy) or not np.isclose(a*c+b*d,0.):
                raise ValueError('two_way_valve_deformed_motor')
            circles.append((mapped([[float(node.get('cx','0')),float(node.get('cy','0'))]])[0],float(node.get('r','0'))*sx))
        elif kind=='line':
            lines.append(mapped([[float(node.get('x1','0')),float(node.get('y1','0'))],
                                 [float(node.get('x2','0')),float(node.get('y2','0'))]]))
        elif kind in {'path','polygon'}:
            paths=path_points(node)
            if len(paths)==1 and paths[0][1]:
                points=paths[0][0]
                if len(points)>3 and np.allclose(points[0],points[-1]):
                    points=points[:-1]
                if len(points)==3:
                    triangles.append((mapped(points),fill,matrix))
        for child in node:
            visit(child,matrix,fill)
    visit(root)
    if len(circles)!=1 or len(lines)!=1 or len(triangles)!=2:
        raise ValueError('two_way_valve_incomplete')
    (first,paint,matrix),(second,other_paint,other_matrix)=triangles
    pairs=np.argwhere(np.linalg.norm(first[:,None]-second[None,:],axis=2)<1e-4)
    if len(pairs)!=1:
        raise ValueError('two_way_valve_disconnected_wings')
    i,j=pairs[0]
    apex=first[i]
    bases=[np.delete(first,i,axis=0),np.delete(second,j,axis=0)]
    if (any(abs(base[0,0]-base[1,0])>1e-4 for base in bases)
            or not min(base[0,0] for base in bases)<apex[0]<max(base[0,0] for base in bases)
            or any(not min(base[:,1])<apex[1]<max(base[:,1]) for base in bases)):
        raise ValueError('two_way_valve_wing_orientation')
    center,radius=circles[0]
    line=lines[0]
    if (np.max(abs(line[:,0]-apex[0]))>1e-4 or abs(center[0]-apex[0])>1e-4
            or center[1]+radius>=min(base[:,1].min() for base in bases)
            or min(line[:,1])>center[1]+radius or max(line[:,1])<apex[1]-1e-4):
        raise ValueError('two_way_valve_disconnected_handle')
    match=re.fullmatch(r'url\(#([^)]+)\)',paint)
    gradient=next((e for e in root.iter() if match and e.get('id')==match[1]
                   and e.tag.rsplit('}',1)[-1]=='linearGradient'),None)
    if (paint!=other_paint or not np.allclose(matrix,other_matrix) or gradient is None
            or gradient.get('gradientUnits')!='userSpaceOnUse' or len(gradient)<2
            or len({stop.get('stop-color') for stop in gradient})<2):
        raise ValueError('two_way_valve_unshared_gradient')


def fit_two_way_valve(width, height, *, description, image, render_fn, error_fn):
    if not two_way_valve_contract(description):
        return None
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    background = np.median(np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1])), axis=0)
    mask = np.max(abs(pixels-background), axis=2) > 35
    rows = np.flatnonzero(mask.any(axis=1))
    if len(rows) < 12:
        return None
    top, bottom = rows[[0, -1]]
    spans = np.array([np.ptp(np.flatnonzero(row))+1 if row.any() else 0 for row in mask])
    # A narrow neck separates the top circular actuator and the bottom wings.
    candidates = np.arange(int(top+(bottom-top)*.35), int(top+(bottom-top)*.8))
    if not len(candidates):
        return None
    neck = int(candidates[np.argmin(spans[candidates])])
    if spans[neck] > max(3, width*.18):
        return None
    head = mask.copy()
    head[neck:] = False
    contours = cv2.findContours(head.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)[:, 0].astype(float)+.5
    x, y, w, h = cv2.boundingRect(contour.astype('float32'))
    arc = contour[contour[:, 1] < y+h*.8]
    if len(arc) < 10:
        return None
    coef = np.linalg.lstsq(np.c_[2*arc, np.ones(len(arc))], (arc**2).sum(axis=1), rcond=None)[0]
    cx, cy = coef[:2]
    outer = float(np.sqrt(max(0, coef[2]+cx*cx+cy*cy)))
    if outer < 3 or np.mean(abs(np.linalg.norm(arc-[cx,cy], axis=1)-outer)) > max(.7, outer*.06):
        return None
    wing_rows = np.flatnonzero((np.arange(height)>neck) & (spans > width*.6))
    if len(wing_rows) < 4:
        return None
    wt, wb = wing_rows[[0,-1]]+.5
    wy, wx = np.nonzero(mask & (np.arange(height)[:,None] > neck) & (spans[:,None]>width*.6))
    left, right = wx.min()+.5, wx.max()+.5
    apex_y = (wt+wb)/2
    yy, xx = np.indices(mask.shape, dtype=float)
    radial = np.hypot(xx+.5-cx, yy+.5-cy)
    fill = np.median(pixels[radial < outer*.65], axis=0)
    rim = np.percentile(pixels[(radial > outer*.8)&(radial < outer+1)], 12, axis=0)
    stem = np.percentile(pixels[neck:neck+1, max(0,int(cx)-1):int(cx)+2].reshape(-1,3), 10, axis=0)
    wing = np.zeros(mask.shape, dtype='uint8')
    for points in (((left,wt),(left,wb),(cx,apex_y)), ((right,wt),(right,wb),(cx,apex_y))):
        cv2.fillPoly(wing, [np.rint(points).astype('int32')], 1)
    core = cv2.erode(wing, np.ones((3,3),dtype='uint8')).astype(bool) & mask
    if core.sum() < 6:
        return None
    plane = np.linalg.lstsq(np.c_[xx[core]+.5, yy[core]+.5, np.ones(core.sum())], pixels[core], rcond=None)[0]
    slope = plane[:2].mean(axis=1)
    angle = float(np.arctan2(slope[1], slope[0]))
    direction = np.array([np.cos(angle), np.sin(angle)])
    corners = np.array([(left,wt),(right,wt),(left,wb),(right,wb)])
    projected = corners@direction
    lo, hi = projected.min(), projected.max()
    center = corners.mean(axis=0)
    start, end = center+direction*(lo-center@direction), center+direction*(hi-center@direction)
    colors = np.c_[np.array([start,end]), np.ones(2)]@plane
    edge = np.percentile(pixels[mask & wing.astype(bool)], 12, axis=0)
    # Native geometry, then BGR paint. Circle and connector share an axis;
    # both triangles share exactly one apex and one gradient coordinate space.
    p = np.r_[cx,cy,outer-.45,1.,left,right,wt,wb,apex_y,1.,max(1.,spans[neck]-.3),angle,
              fill,rim,stem,colors.ravel(),edge,background]

    def build(v):
        cx,cy,r,sw,lx,rx,ty,by,ay,bw,cw,angle = v[:12]
        fill,rim,stem,low,high,edge,bg = v[12:].reshape(-1,3)
        direction = np.array([np.cos(angle),np.sin(angle)])
        corners = np.array([(lx,ty),(rx,ty),(lx,by),(rx,by)])
        center = corners.mean(axis=0)
        projection = corners@direction
        start = center+direction*(projection.min()-center@direction)
        end = center+direction*(projection.max()-center@direction)
        wings = ''.join(f'<path d="M {x:.5f} {ty:.5f} L {x:.5f} {by:.5f} L {cx:.5f} {ay:.5f} Z" '
                        f'fill="url(#valve)" stroke="{_hex(edge)}" stroke-width="{bw:.5f}" stroke-linejoin="round"/>'
                        for x in (lx,rx))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="valve" gradientUnits="userSpaceOnUse" x1="{start[0]:.5f}" y1="{start[1]:.5f}" '
                f'x2="{end[0]:.5f}" y2="{end[1]:.5f}"><stop offset="0" stop-color="{_hex(low)}"/>'
                f'<stop offset="1" stop-color="{_hex(high)}"/></linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="{_hex(bg)}"/>'
                f'<line x1="{cx:.5f}" y1="{cy:.5f}" x2="{cx:.5f}" y2="{ay:.5f}" stroke="{_hex(stem)}" stroke-width="{cw:.5f}"/>'
                +wings+f'<circle cx="{cx:.5f}" cy="{cy:.5f}" r="{r:.5f}" fill="{_hex(fill)}" stroke="{_hex(rim)}" stroke-width="{sw:.5f}"/></svg>')

    def valid(v):
        cx,cy,r,sw,lx,rx,ty,by,ay,bw,cw,angle = v[:12]
        return (np.isfinite(v).all() and r>3 and .25 <= min(sw,bw,cw) and max(sw,bw,cw)<r*.5
                and 0<=lx-bw/2<cx<rx+bw/2<=width and 0<=ty-bw/2<ay<by+bw/2<=height
                and r+sw/2<=min(cx,width-cx,cy) and cy+r<ty and ty<ay<by
                and np.all((v[12:]>=0)&(v[12:]<=255)))

    p[12:] = np.clip(p[12:],0,255)
    result = _register(p,12,build,valid,image,render_fn,error_fn,'description_two_way_valve_v1',
                       allow_portfolio=False,max_evaluations=1800,reconsider_after=0)
    if result is None:
        return None
    quality = pixel_quality(image,result['rendered'])
    if not quality or not quality['passed']:
        return None
    validate_two_way_valve(result['svg'])
    result['quality'] = quality
    return result
