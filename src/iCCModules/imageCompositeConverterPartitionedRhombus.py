"""Description-owned subdivisions, parallel rails, glyphs and background bands.

The language selects the topology before observing pixels. Measurements only
initialize its parameters; no contours or unexplained residuals are emitted.
"""
from __future__ import annotations

import re
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _register, _hex, _image
from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality


def partitioned_rhombus_spec(description):
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description
    words = ' '.join(normalize_description(description).casefold().split())
    # Consume complete clauses. Unknown additions and conflicting assertions
    # cannot silently select a partially understood construction.
    clauses = [s.strip() for s in re.split(r'[.;!?]', words) if s.strip()]
    spec = dict(double=False, signs=False, background=False)
    prefix = r'(?:auf (?:weissem|weißem) hintergrund (?:liegt|befindet sich) |im vordergrund liegt |)'
    shape = (r'eine (?:hellgrau gefüllte,? grau umrandete|grau umrandete,? hellgrau gefüllte) raute')
    children = r'(?:vier|4) (?:kleinere|kleine|gleich grosse|gleich große) rauten'
    main = (prefix + shape + r',? '
            r'(?:unterteilt|aufgeteilt) in ' + children)
    alternate = prefix + shape + r' ist in ' + children + r' (?:unterteilt|aufgeteilt)'
    if not clauses or not re.fullmatch('(?:'+main+'|'+alternate+')', clauses.pop(0)):
        return None
    seen = set()
    for clause in clauses:
        if re.fullmatch(r'eine der diagonalen trennlinien (?:ist als (?:schmale )?doppellinie ausgeführt|besteht aus zwei parallelen linien)', clause):
            key = 'double'; spec[key] = True
        elif (m := re.fullmatch(r'im (oberen|unteren|linken|rechten) feld (?:stehen|befinden sich) ein dunkelgraues pluszeichen und darunter ein minuszeichen', clause)):
            key = 'signs'; spec[key] = m[1]
        elif re.fullmatch(r'(?:hinter der raute|im hintergrund) (?:verläuft|liegt) ein (?:breites,? )?(?:sehr )?hellgraues x bis an die bildränder', clause):
            key = 'background'; spec[key] = True
        elif re.fullmatch(r'die darstellung ist flach und geometrisch, ohne schatten oder farbverläufe|keine weiteren objekte|ma(?:ß|ss)e und farben ergeben sich aus dem bild', clause):
            continue
        else:
            return None
        if key in seen:
            return None
        seen.add(key)
    return spec


def partition_inventory(spec):
    # Subregions share one parent outline, rather than five overlapping shapes.
    inventory = dict(rhombus=1, diagonal=3 if spec['double'] else 2)
    if spec['background']:
        inventory['diagonal'] += 2
        inventory['line'] = 4  # the horizontal, canvas-clipped band ends
    return inventory


def _rails(cx, cy, rx, ry, direction, offset):
    u = np.array([(-1-direction*offset)/2, (1-direction*offset)/2])
    return np.c_[cx+rx*u, cy+ry*(direction*u+offset)]


def build_partitioned_rhombus(width, height, spec, p, double_direction=1):
    (cx,cy,rx,ry,sw,gap, band_width,cap,band_y,
     px,py,plen,pw,mx,my,mlen,mw, bg,fill,rim,ink,band) = p
    color = lambda value: _hex([value]*3)
    def line(points, paint, stroke, tag='line'):
        if tag == 'line':
            (x1,y1),(x2,y2) = points
            geometry = f'x1="{x1:.6f}" y1="{y1:.6f}" x2="{x2:.6f}" y2="{y2:.6f}"'
        else:
            geometry = 'points="'+' '.join(f'{x:.6f},{y:.6f}' for x,y in points)+'"'
        return f'<{tag} {geometry} fill="none" stroke="{color(paint)}" stroke-width="{stroke:.6f}"/>'
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             f'<rect width="{width}" height="{height}" fill="{color(bg)}"/>']
    if spec['background']:
        for sign in (-1,1):
            y0, y1 = cy-sign*band_y, cy+sign*band_y
            # Horizontal caps keep the broad bands inside the source canvas.
            parts.append(line([(0,y0),(cap,y0),(width-cap,y1),(width,y1)],band,band_width,'polyline'))
    corners = [(cx,cy-ry),(cx+rx,cy),(cx,cy+ry),(cx-rx,cy)]
    points = ' '.join(f'{x:.6f},{y:.6f}' for x,y in corners)
    parts.append(f'<polygon points="{points}" fill="{color(fill)}" stroke="{color(rim)}" stroke-width="{sw:.6f}"/>')
    for direction in (-1,1):
        offsets = [-gap/2,gap/2] if spec['double'] and direction==double_direction else [0]
        for offset in offsets:
            parts.append(line(_rails(cx,cy,rx,ry,direction,offset/ry),rim,sw))
    if spec['signs']:
        parts += [line([(px-plen/2,py),(px+plen/2,py)],ink,pw),
                  line([(px,py-plen/2),(px,py+plen/2)],ink,pw),
                  line([(mx-mlen/2,my),(mx+mlen/2,my)],ink,mw)]
    return ''.join(parts)+'</svg>'


def validate_partitioned_rhombus(svg, spec):
    """Check actual geometry and painting order, independent of IDs/metadata."""
    from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform
    from src.iCCModules.imageCompositeConverterRepresentation import EXCLUDED, path_points
    from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles
    from PIL import ImageColor
    root = ET.fromstring(inline_simple_svg_styles(svg))
    shapes = []
    def visit(node, parent=(1.,0.,0.,1.,0.,0.), inherited=None):
        tag = node.tag.rsplit('}',1)[-1]
        if tag in EXCLUDED:
            return
        style = dict(inherited or dict(fill='black',stroke='none', **{'stroke-width':'1'}))
        style.update({key:node.get(key,value) for key,value in style.items()})
        matrix = _compose(parent,_transform(node.get('transform','')))
        a,b,c,d,tx,ty = matrix
        linear = np.array([[a,c],[b,d]])
        if tag in {'polygon','polyline','path','line'}:
            paths = ([(np.array([[float(node.get(k,'0')) for k in ('x1','y1')],
                                [float(node.get(k,'0')) for k in ('x2','y2')]]),False)]
                     if tag=='line' else path_points(node))
            for points,closed in paths:
                if closed and len(points)>1 and np.allclose(points[0],points[-1]):
                    points=points[:-1]
                shapes.append((points@linear.T+[tx,ty],closed,style))
        for child in node:
            visit(child,matrix,style)
    visit(root)
    outlines = [(i,p,s) for i,(p,closed,s) in enumerate(shapes) if closed and len(p)==4]
    if len(outlines)!=1:
        raise ValueError('partition_outline_missing')
    index,corners,paint=outlines[0]
    cx,cy = corners.mean(axis=0)
    rx,ry = np.ptp(corners,axis=0)/2
    expected = np.array([[cx,cy-ry],[cx+rx,cy],[cx,cy+ry],[cx-rx,cy]])
    if min(rx,ry)<=0 or any(np.min(np.linalg.norm(corners-point,axis=1))>1e-4 for point in expected):
        raise ValueError('partition_deformed_rhombus')
    def gray(value):
        try:
            rgb = ImageColor.getrgb(value)
        except ValueError as exc:
            raise ValueError('partition_flat_gray_paint') from exc
        if max(rgb)-min(rgb)>2:
            raise ValueError('partition_gray_paint')
        return float(np.mean(rgb))
    fill,rim=gray(paint['fill']),gray(paint['stroke'])
    if fill-rim<15:
        raise ValueError('partition_outline_contrast')
    bands = [(i,p,s) for i,(p,closed,s) in enumerate(shapes) if not closed and len(p)>2]
    if len(bands)!=(2 if spec['background'] else 0):
        raise ValueError('partition_background_missing')
    if bands:
        axes=[]
        for i,p,s in bands:
            if (i>=index or len(p)!=4 or abs(p[0,1]-p[1,1])>1e-4
                    or abs(p[2,1]-p[3,1])>1e-4 or not np.all(np.diff(p[:,0])>0)
                    or gray(s['stroke'])<=rim or abs(gray(s['stroke'])-fill)>25):
                raise ValueError('partition_background_order_or_geometry')
            axes.append(p[2]-p[1])
        if axes[0][1]*axes[1][1]>=0:
            raise ValueError('partition_background_cross')
    lines = [(p,s) for p,closed,s in shapes if not closed and len(p)==2]
    rails,marks=[],[]
    for points,style in lines:
        delta=(points[1]-points[0])/[rx,ry]
        if min(abs(delta))>1e-5:
            rails.append((points,style))
        else:
            marks.append((points,style))
    if len(rails)!=(3 if spec['double'] else 2):
        raise ValueError('partition_rails_missing')
    axes={-1:[],1:[]}
    for points,style in rails:
        q=(points-[cx,cy])/[rx,ry]
        slope=(q[1,1]-q[0,1])/(q[1,0]-q[0,0])
        if abs(abs(slope)-1)>1e-4 or np.max(abs(abs(q).sum(axis=1)-1))>1e-4:
            raise ValueError('partition_rail_endpoints')
        offset=float(np.mean(q[:,1]-slope*q[:,0]))
        if abs(offset)>.15 or abs(gray(style['stroke'])-rim)>2:
            raise ValueError('partition_rail_position_or_paint')
        axes[1 if slope>0 else -1].append(offset)
    if sorted(map(len,axes.values()))!=([1,2] if spec['double'] else [1,1]):
        raise ValueError('partition_axes_missing')
    for offsets in axes.values():
        if abs(sum(offsets))>1e-4 or len(offsets)==2 and abs(offsets[0]-offsets[1])<.005:
            raise ValueError('partition_parallel_rails')
    if len(marks)!=(3 if spec['signs'] else 0):
        raise ValueError('partition_signs_missing')
    if marks:
        horizontal=[(p,s) for p,s in marks if abs(p[1,1]-p[0,1])<1e-4]
        vertical=[(p,s) for p,s in marks if abs(p[1,0]-p[0,0])<1e-4]
        if len(horizontal)!=2 or len(vertical)!=1:
            raise ValueError('partition_plus_minus')
        horizontal.sort(key=lambda item:item[0][:,1].mean())
        plus,minus=horizontal
        stem=vertical[0]
        if (not np.allclose(plus[0].mean(0),stem[0].mean(0),atol=1e-4)
                or abs(np.linalg.norm(plus[0][1]-plus[0][0])-np.linalg.norm(stem[0][1]-stem[0][0]))>1e-4
                or abs(float(plus[1]['stroke-width'])-float(stem[1]['stroke-width']))>1e-4
                or plus[0][0,1]>=minus[0][0,1]):
            raise ValueError('partition_plus_minus')
        for points,style in marks:
            q=(points-[cx,cy])/[rx,ry]
            cell={'oberen':q[:,1]<-abs(q[:,0]), 'unteren':q[:,1]>abs(q[:,0]),
                  'linken':q[:,0]<-abs(q[:,1]), 'rechten':q[:,0]>abs(q[:,1])}[spec['signs']]
            if not cell.all() or (abs(q).sum(axis=1)>=1).any() or gray(style['stroke'])>=rim-10:
                raise ValueError('partition_sign_cell_or_paint')


def fit_partitioned_rhombus(width,height,*,description,image,render_fn,error_fn):
    spec=partitioned_rhombus_spec(description)
    pixels=_image(width,height,image)
    if spec is None or pixels is None:
        return None
    gray=pixels.mean(axis=2)
    if np.percentile(np.ptp(pixels,axis=2),95)>8:
        return None
    bg=float(np.percentile(gray,98))
    # The dark enclosing contour supplies only a seed for the declared rhombus.
    contours,_=cv2.findContours((gray<bg-45).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour=max(contours,key=cv2.contourArea)
    hull=cv2.convexHull(contour)[:,0].astype(float)+.5
    cx,cy=(hull.min(0)+hull.max(0))/2
    rx,ry=np.ptp(hull,axis=0)/2
    if min(rx,ry)<8:
        return None
    yy,xx=np.indices(gray.shape,dtype=float); xx+=.5; yy+=.5
    u,v=(xx-cx)/rx,(yy-cy)/ry
    inside=abs(u)+abs(v)<.9
    fill=float(np.percentile(gray[inside],75))
    rim=float(np.percentile(gray[(abs(abs(u)+abs(v)-1)<.025)],30))
    # Connected components measure optional declared signs in their own cell.
    px,py=cx,cy-ry*.57
    mx,my=cx,cy-ry*.32
    plen,pw,mlen,mw=rx*.3,rx*.08,rx*.3,rx*.06
    if spec['signs']:
        cells={'oberen':v<-abs(u)-.08,'unteren':v>abs(u)+.08,
               'linken':u<-abs(v)-.08,'rechten':u>abs(v)+.08}
        mask=((gray<rim-20)&inside&cells[spec['signs']]).astype(np.uint8)
        _,_,stats,_=cv2.connectedComponentsWithStats(mask)
        components=[s for s in stats[1:] if s[4]>3]
        if len(components)!=2:
            return None
        components.sort(key=lambda s:s[1]+s[3]/2)
        (x,y,w,h,_),(a,b,c,d,_)=components
        px,py,plen=x+w/2,y+h/2,(w+h)/2
        # Cross area = 2*length*thickness - thickness**2.
        pw=plen-np.sqrt(max(0,plen**2-components[0][4]))
        mx,my,mlen,mw=a+c/2,b+d/2,c,d
    band_width,cap,band_y=height*.085,width*.09,height*.41
    band=float(np.percentile(gray[(~inside)&(gray<bg-8)&(gray>bg-40)],50)) if spec['background'] else fill
    if spec['background']:
        # Fit the declared bent band from its exposed columns. The cap length
        # and diagonal slope are coupled; adjusting them one pixel at a time
        # from a canvas-relative guess traps non-square variants in a valley.
        exposed=(abs(u)+abs(v)>1.12)&(gray<bg-8)&(gray>bg-42)
        xs,ys=[],[]
        for x in range(max(2,int(cx-rx*.35))):
            rows=np.flatnonzero(exposed[:,x]&(yy[:,x]<cy))
            if len(rows)<3:
                continue
            weights=(bg-gray[rows,x])**2
            xs.append(x+.5);ys.append(float(np.average(rows+.5,weights=weights)))
        if len(xs)<5:
            return None
        xs,ys=np.array(xs),np.array(ys)
        choices=[]
        for trial_cap in np.arange(.5,width*.3,.5):
            factor=-1+2*np.maximum(0,xs-trial_cap)/(width-2*trial_cap)
            trial_y=float(factor@(ys-cy)/(factor@factor))
            choices.append((float(np.mean((cy+trial_y*factor-ys)**2)),trial_cap,trial_y))
        _,cap,band_y=min(choices)
        region=(xx<max(2,cap*.8))&(yy<cy)
        band_width=float(np.median([np.sum((bg-gray[:,x])>(bg-band)*.5)
                                    /2 for x in range(max(1,int(cap*.8)))]))
        band=float(np.median(gray[region&(gray<bg-8)&(gray>bg-42)]))
    ink=float(np.percentile(gray[inside],1)) if spec['signs'] else max(0,rim-30)
    p=np.array([cx,cy,rx,ry,1.5,ry*.045,band_width,cap,band_y,
                px,py,plen,pw,mx,my,mlen,mw,bg,fill,rim,ink,band],float)
    def valid(q):
        x,y,a,b,stroke,gap,bw,cap,by=q[:9]
        return (np.isfinite(q).all() and min(a,b)>5 and .3<stroke<min(a,b)*.1
                and .005<gap/b<.15 and 1<bw<height*.3 and 0<cap<width*.3
                and bw/2<=y-by and y+by<=height-bw/2
                and min(x-a-stroke,y-b-stroke)>0 and x+a+stroke<width and y+b+stroke<height
                and min(q[11:13])>1 and min(q[15:17])>1
                and np.all((q[17:]>=0)&(q[17:]<=255)) and q[18]-q[19]>15 and q[19]-q[20]>10)
    results=[]
    # A split axis has a light centre; the other axis has a dark centre.
    # Choose the measured topology first so a wrong rail direction cannot use
    # the shared deadline before the matching construction gets a turn.
    directions=(1,)
    if spec['double']:
        t=np.r_[np.linspace(-.42,-.15,20),np.linspace(.15,.42,20)]
        scores={}
        for direction in (-1,1):
            xs=np.clip(np.floor(cx+rx*t).astype(int),0,width-1)
            ys=np.clip(np.floor(cy+ry*direction*t).astype(int),0,height-1)
            scores[direction]=float(np.mean(gray[ys,xs]))
        first=max(scores,key=scores.get)
        directions=(first,-first)
    for direction in directions:
        build=lambda q:build_partitioned_rhombus(width,height,spec,q,direction)
        result=_register(p,17,build,valid,image,render_fn,error_fn,'description_partitioned_rhombus_v1',
                         allow_portfolio=False,max_evaluations=1600,reconsider_after=0,
                         refinement_steps=(1.,.5,.25,.125,.0625))
        if result:
            results.append(result)
            if pixel_quality(image,result['rendered'])['passed']:
                break
    if not results:
        return None
    result=min(results,key=lambda r:r['error'])
    validate_partitioned_rhombus(result['svg'],spec)
    result['quality']=pixel_quality(image,result['rendered'])
    return result
