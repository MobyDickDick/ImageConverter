"""Explicit geometric relations shared by description checks and scene fitting.

Endpoints are references to a parent, not separately optimized coordinates.
This bounded vocabulary supports arbitrary line arrangements, paint axes and
palettes; it contains no catalogue identity or stored shape.
"""
from __future__ import annotations

import re
from xml.etree import ElementTree as ET

import cv2
import numpy as np

ANCHORS = {'oberen': (.5, 0.), 'unteren': (.5, 1.), 'linken': (0., .5), 'rechten': (1., .5)}
COLORS = {'weiss': 'white', 'weiß': 'white', 'grau': 'gray', 'rot': 'red',
          'blau': 'blue', 'grün': 'green', 'schwarz': 'black', 'gelb': 'yellow'}


def anchor_relations(description):
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description
    text = re.sub(r'"[^"\n]*"|„[^“\n]*“', '', normalize_description(description)).casefold()
    if 'rechteck' not in text:
        return None
    headers = list(re.finditer(r'\b(?:die\s+)?(obere|untere|linke|rechte|erste|zweite|dritte|vierte)\s+'
                              r'(?:linie|gerade)\s+(?:geht|verläuft|führt)\s+', text))
    lines = []
    for i, match in enumerate(headers):
        clause = text[match.end():headers[i+1].start() if i+1 < len(headers) else len(text)].split('.')[0]
        if re.search(r'\b(?:nicht|kein\w*)\b', clause):
            continue
        points = re.findall(r'\bmitte\s+(?:des|vom)\s+(oberen|unteren|linken|rechten)\s+rand(?:s|es)?\b', clause)
        if len(points) != 2 or not re.search(r'\bvon\b', clause) or not re.search(r'\bbis\b', clause):
            continue
        if points[0] == points[1]:
            raise ValueError('anchor_relation:zero_length')
        lines.append(dict(name=match[1], start=list(ANCHORS[points[0]]), end=list(ANCHORS[points[1]])))
    if not lines:
        return None
    if len(lines) != len(headers):
        raise ValueError('anchor_relation:unresolved_endpoint')
    if len({line['name'] for line in lines}) != len(lines):
        raise ValueError('anchor_relation:duplicate_role')
    axis = None
    for key, pattern in (('x', r'(?:horizontal|waagerecht|waagrecht)'), ('y', r'(?:vertikal|senkrecht)')):
        if re.search(r'\b'+pattern+r'\w*(?:\s+(?:rot|blau|grün|grau|gelb|weiss|weiß)\w*)?\s+(?:farb)?verlauf\b', text):
            if axis is not None:
                raise ValueError('anchor_relation:conflicting_gradient_axes')
            axis = key
    fill = None
    for word, color in COLORS.items():
        if re.search(r'\b'+word+r'\w*\s+(?:farb)?verlauf\b', text):
            fill = color
    mark = re.search(r'\b(?:ein[enrms]?|zwei|drei|vier|[1-4])\s+('
                     +'|'.join(COLORS)+r')[enrms]*\s+(?:linien?|geraden?)\b', text)
    symmetry = None
    if re.search(r'\bsymmetr\w*\b', text):
        if re.search(r'\b(?:waagrecht|waagerecht|horizontal)\w*\s+symmetrieachse\b', text):
            symmetry = 'horizontal'
        elif re.search(r'\b(?:senkrecht|vertikal)\w*\s+symmetrieachse\b', text):
            symmetry = 'vertical'
    if symmetry:
        def canonical(points):
            return sorted(tuple(p) for p in points)
        segments = [canonical([line['start'], line['end']]) for line in lines]
        for line in lines:
            reflected = np.array([line['start'], line['end']])
            reflected[:, 1 if symmetry == 'horizontal' else 0] = 1-reflected[:, 1 if symmetry == 'horizontal' else 0]
            if canonical(reflected) not in segments:
                raise ValueError('anchor_relation:conflicting_symmetry')
    peak = re.search(r'(\d+(?:[.,]\d+)?)\s*%\s*(?:vom|von(?:\s+dem)?)\s+(linken|oberen)\s+rand', text)
    return dict(schema='anchor_relations_v1', lines=lines, gradient_axis=axis, fill_color=fill,
                mark_color=COLORS[mark[1]] if mark else None, symmetry=symmetry,
                anchor_tolerance=0. if re.search(r'\bgenau\b.{0,20}\bmitte\b',text) else .06,
                peak_fraction=float(peak[1].replace(',', '.'))/100 if peak else None,
                clipped=bool(re.search(r'\b(?:abgeschnitten|beschnitten|begrenzt)\b', text)),
                under_frame=bool(re.search(r'\bunter\s+(?:den|dem)\s+(?:rand|rahmen)\b', text)))


def clip_polygon(points, bounds):
    """Intersect any convex paint polygon with an axis-aligned parent."""
    polygon = list(map(tuple, points))
    left, top, right, bottom = bounds
    for axis, bound, sign in ((0,left,1), (0,right,-1), (1,top,1), (1,bottom,-1)):
        clipped = []
        for start, end in zip(polygon, polygon[1:]+polygon[:1]):
            ins, ine = sign*(start[axis]-bound) >= 0, sign*(end[axis]-bound) >= 0
            if ins != ine:
                fraction = (bound-start[axis])/(end[axis]-start[axis])
                clipped.append(tuple(start[j]+fraction*(end[j]-start[j]) for j in (0,1)))
            if ine:
                clipped.append(end)
        polygon = clipped
    return np.asarray(polygon, dtype=float).reshape(-1,2)


def stroke_polygon(start, end, width, bounds):
    start, end = np.asarray(start), np.asarray(end)
    direction = end-start
    length = np.linalg.norm(direction)
    if length <= 0:
        return np.empty((0,2))
    direction /= length
    normal = np.array([-direction[1], direction[0]])*width/2
    # Parent clipping determines the ends, including their entire paint width.
    a, b = start-direction*(width+2), end+direction*(width+2)
    return clip_polygon([a+normal, a-normal, b-normal, b+normal], bounds)


def _color_matches(values, color):
    b,g,r = np.moveaxis(values, -1, 0)
    if color == 'white':
        return (values.min(axis=-1) >= 205) & (np.ptp(values,axis=-1) <= 40)
    if color == 'gray':
        return np.ptp(values,axis=-1) < 30
    if color == 'black':
        return values.max(axis=-1) < 80
    if color == 'red':
        return (r > g+20) & (r > b+20)
    if color == 'blue':
        return (b > g+15) & (b > r+20)
    if color == 'green':
        return (g > r+15) & (g > b+10)
    if color == 'yellow':
        return (r > b+30) & (g > b+30)
    return np.ones(values.shape[:-1], dtype=bool)


def _anchor_variables(relations):
    """Share one coordinate for the same port and for mirrored parent ports."""
    groups={}
    if not relations['anchor_tolerance']:
        return []
    for line in relations['lines']:
        for anchor in (line['start'],line['end']):
            coordinate=0 if anchor[1] in (0.,1.) else 1
            symmetry=relations['symmetry']
            if (symmetry=='horizontal' and coordinate==1) or (symmetry=='vertical' and coordinate==0):
                continue  # a midpoint on the symmetry axis cannot move off it
            key=coordinate if symmetry else tuple(anchor)
            group=groups.setdefault(key,dict(coordinate=coordinate,anchors=[]))
            if anchor not in group['anchors']:
                group['anchors'].append(anchor)
    return list(groups.values())


def _observed_offsets(pixels,bounds,relations,variables):
    """Use straight paint evidence to initialize the bounded parent ports."""
    l,t,r,b=bounds;w,h=r-l,b-t
    yy,xx=np.indices(pixels.shape[:2],dtype=float);xx+=.5;yy+=.5
    paint=_color_matches(pixels.astype(float),relations['mark_color'])
    paint &= (xx>l+1)&(xx<r-1)&(yy>t+1)&(yy<b-1)
    measurements={tuple(anchor):[] for group in variables for anchor in group['anchors']}
    for line in relations['lines']:
        a,z=np.array([line['start'],line['end']])*[w,h]+[l,t];direction=z-a
        length=np.linalg.norm(direction);direction/=length
        along=(xx-a[0])*direction[0]+(yy-a[1])*direction[1]
        near=paint & (abs((xx-a[0])*direction[1]-(yy-a[1])*direction[0])<max(3.,min(w,h)*.1))
        near &= (along>length*.15)&(along<length*.85)
        points=np.c_[xx[near],yy[near]]
        if len(points)<6:
            continue
        centre=points.mean(axis=0);axis=np.linalg.svd(points-centre,full_matrices=False)[2][0]
        if abs(np.dot(axis,direction))<.95:
            continue
        for anchor in (line['start'],line['end']):
            if tuple(anchor) not in measurements:
                continue
            coordinate=0 if anchor[1] in (0.,1.) else 1
            fixed=1-coordinate;point=np.array(anchor)*[w,h]+[l,t]
            if abs(axis[fixed])>1e-9:
                value=centre[coordinate]+(point[fixed]-centre[fixed])*axis[coordinate]/axis[fixed]
                measurements[tuple(anchor)].append(value-point[coordinate])
    offsets=[]
    for group in variables:
        observed=[v for anchor in group['anchors'] for v in measurements[tuple(anchor)]]
        limit=[w,h][group['coordinate']]*relations['anchor_tolerance']
        offsets.append(float(np.clip(np.median(observed) if observed else 0.,-limit,limit)))
    return offsets


def _placed_anchor(anchor,bounds,variables,offsets):
    l,t,r,b=bounds
    point=np.array(anchor)*[r-l,b-t]+[l,t]
    for group,offset in zip(variables,offsets):
        if anchor in group['anchors']:
            point[group['coordinate']]+=offset
    return point


def fit_relational_scene(width, height, *, description, image, render_fn, error_fn):
    relations = anchor_relations(description)
    if not relations or not relations['mark_color']:
        return None
    from src.iCCModules.imageCompositeConverterFilledSymbols import _register, _hex
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
    arr = np.asarray(image)
    if arr.shape != (height,width,3) or min(width,height) < 12 or not np.isfinite(arr).all():
        return None
    pixels = arr.astype(float)
    # JPEG chroma ringing can tint isolated white canvas pixels. A connected
    # parent, rather than global extrema of every tinted pixel, supplies bounds.
    count,_,stats,_=cv2.connectedComponentsWithStats((pixels.mean(axis=2)<220).astype('uint8'))
    if count < 2:
        return None
    index=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
    x,y,w,h,area=map(int,stats[index])
    right,bottom=x+w,y+h
    if area<40:
        return None
    margin = max(2, int(min(w,h)*.07))
    if min(w,h) <= 2*margin+4:
        return None
    inner = pixels[y+margin:bottom-margin,x+margin:right-margin]
    horizontal = relations['gradient_axis'] != 'y'
    profile = np.median(inner,axis=0 if horizontal else 1)
    if not _color_matches(np.median(profile,axis=0), relations['fill_color']):
        return None
    lo,hi = (x+.5,right-.5) if horizontal else (y+.5,bottom-.5)
    positions = np.arange(len(profile))+(x if horizontal else y)+margin+.5
    models = []
    for fraction in np.linspace(.15,.85,101):
        peak = lo+(hi-lo)*fraction
        basis = np.column_stack([np.interp(positions,[lo,peak,hi],np.eye(3)[i]) for i in range(3)])
        palette = np.linalg.lstsq(basis,profile,rcond=None)[0]
        models.append((float(np.square(basis@palette-profile).mean()),peak,np.clip(palette,0,255)))
    _,peak,palette = min(models,key=lambda model:model[0])
    if relations['gradient_axis'] is None:
        palette=np.tile(np.median(inner.reshape(-1,3),axis=0),(3,1))
    border = np.concatenate((pixels[y:bottom,x], pixels[y:bottom,right-1], pixels[y,x:right], pixels[bottom-1,x:right]))
    neutral = border[(np.ptp(border,axis=1) < 40) & (border.max(axis=1) < 240)]
    if len(neutral) < 4:
        return None
    rim = np.median(neutral,axis=0)
    marked = inner[_color_matches(inner,relations['mark_color'])]
    if len(marked) < 4:
        return None
    shade = np.percentile(marked,85,axis=0)
    outside=np.ones((height,width),dtype=bool);outside[y:bottom,x:right]=False
    canvas = np.median(pixels[outside],axis=0) if outside.any() else np.repeat(255.,3)
    variables=_anchor_variables(relations)
    initial_bounds=(x+.5,y+.5,right-.5,bottom-.5)
    offsets=_observed_offsets(arr,initial_bounds,relations,variables)
    geometry=7+len(variables)
    seed = np.r_[list(initial_bounds),.9,peak,max(1.,min(w,h)*.055),offsets,palette.ravel(),rim,shade,canvas]
    yy,xx = np.indices((height,width),dtype=float);xx += .5; yy += .5
    regions = []
    for line in relations['lines']:
        a,b = np.array([line['start'],line['end']])*[w-1,h-1]+[x+.5,y+.5]
        d=b-a; length=np.linalg.norm(d); along=((xx-a[0])*d[0]+(yy-a[1])*d[1])/length
        regions.append((abs((xx-a[0])*d[1]-(yy-a[1])*d[0])/length < max(2.,min(w,h)*.08))
                       & (along > length*.08) & (along < length*.92))
    def build(p):
        l,t,r,b,sw,peak,lw = p[:7]
        colors = p[geometry:].reshape(-1,3)
        gl,gr = (l,r) if horizontal else (t,b)
        stops=''.join(f'<stop offset="{offset:.8f}" stop-color="{_hex(c)}"/>' for offset,c in
                      zip((0.,(peak-gl)/(gr-gl),1.),colors[:3]))
        axis=(f'x1="{l:.6f}" x2="{r:.6f}" y1="0" y2="0"' if horizontal else
              f'y1="{t:.6f}" y2="{b:.6f}" x1="0" x2="0"')
        marks=''
        for line in relations['lines']:
            a,z=[_placed_anchor(anchor,(l,t,r,b),variables,p[7:geometry]) for anchor in (line['start'],line['end'])]
            polygon=stroke_polygon(a,z,lw,(l,t,r,b))
            marks += '<polygon points="'+' '.join(f'{px:.6f},{py:.6f}' for px,py in polygon)+f'" fill="{_hex(colors[4])}"/>'
        frame=f'<rect x="{l:.6f}" y="{t:.6f}" width="{r-l:.6f}" height="{b-t:.6f}" fill="none" stroke="{_hex(colors[3])}" stroke-width="{sw:.6f}"/>'
        paint_definition=(f'<defs><linearGradient id="relationalPaint" gradientUnits="userSpaceOnUse" {axis}>{stops}</linearGradient></defs>'
                          if relations['gradient_axis'] else '')
        fill='url(#relationalPaint)' if relations['gradient_axis'] else _hex(colors[0])
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            +paint_definition+
            f'<rect width="{width}" height="{height}" fill="{_hex(colors[5])}"/>'
            f'<rect x="{l:.6f}" y="{t:.6f}" width="{r-l:.6f}" height="{b-t:.6f}" fill="{fill}"/>'
            +(marks+frame if relations['under_frame'] else frame+marks)+'</svg>')
    def valid(p):
        l,t,r,b,sw,pk,lw=p[:7]
        gl,gr=(l,r) if horizontal else (t,b)
        preferred=relations['peak_fraction']
        return (np.isfinite(p).all() and np.max(abs(p[:4]-seed[:4])) <= 2 and min(r-l,b-t) > 5
                and .25 <= sw <= 3 and .5 <= lw <= min(w,h)*.15 and gl+1 < pk < gr-1
                and (preferred is None or abs((pk-gl)/(gr-gl)-preferred) < .15)
                and all(abs(offset)<=[r-l,b-t][group['coordinate']]*relations['anchor_tolerance']
                        for group,offset in zip(variables,p[7:geometry]))
                and np.all((p[geometry:] >= 0) & (p[geometry:] <= 255)))
    def local_errors(raster):
        error=np.square(pixels-raster.astype(float)).mean(axis=2)/255**2
        return [float(error[region].mean()) for region in regions]
    def loss(reference,raster):
        return float(np.square(reference.astype(float)-raster.astype(float)).mean()/255**2+.05*sum(local_errors(raster)))
    result=_register(seed,geometry,build,valid,arr,render_fn,error_fn,'raster_relational_scene_v1',
        loss_fn=loss,satisfactory_fn=lambda p,m:max(local_errors(m[3])) < .004,
        refinement_steps=(1.,.5,.25,.125,.0625))
    if result is None:
        return None
    quality=pixel_quality(arr,result['rendered'])
    # The tighter local target above controls early completion. Acceptance
    # retains the common foreground-error bound plus explicit visible-line
    # checks; JPEG ringing must not be mistaken for a missing relationship.
    if not quality['passed'] or max(local_errors(result['rendered'])) >= .04:
        return None
    try:
        validate_anchor_relations(result['svg'],relations)
    except ValueError:
        return None
    result.update(object_kinds=['rectangle']+['line']*len(relations['lines']),
                  object_quality=local_errors(result['rendered']),neural_scene_selected=False,
                  relations=relations,quality=quality,anchor_offsets=result['parameters'][7:geometry])
    return result


def _match_segments(corners, geometry, relations):
    """Prove shared endpoints and reflection from displayed vector geometry.

    Pixel proximity alone is too permissive: otherwise a later local edit can
    improve a JPEG score by stretching just one member of a symmetric pair.
    """
    basis=np.column_stack((corners[1]-corners[0],corners[3]-corners[0]))
    try:
        inverse=np.linalg.inv(basis)
    except np.linalg.LinAlgError:
        raise ValueError('anchor_relation:degenerate_parent')
    segments=[]
    for points in geometry:
        normalized=(points-corners[0]) @ inverse.T
        edges=np.roll(normalized,-1,axis=0)-normalized
        direction=edges[np.argmax(np.linalg.norm(edges,axis=1))]
        length=np.linalg.norm(direction)
        if length<=1e-9:
            continue
        direction/=length;normal=np.array([-direction[1],direction[0]])
        lateral=normalized @ normal;along=normalized @ direction
        thickness=float(np.ptp(lateral))
        if thickness<=0 or np.ptp(along)<thickness*3:
            continue
        centre=normal*(lateral.min()+lateral.max())/2+direction*(along.min()+along.max())/2
        segments.append((centre,direction,thickness,along.min(),along.max()))
    options=[];epsilon=.003
    for line in relations['lines']:
        choices=[]
        for index,(centre,direction,thickness,lo,hi) in enumerate(segments):
            points=[]
            for port in (line['start'],line['end']):
                fixed=1 if port[1] in (0.,1.) else 0
                if abs(direction[fixed])<1e-8:
                    break
                point=centre+direction*((port[fixed]-centre[fixed])/direction[fixed])
                if (abs(point[1-fixed]-.5)>relations['anchor_tolerance']+epsilon
                        or not lo-thickness<=np.dot(point,direction)<=hi+thickness):
                    break
                points.append(point)
            if len(points)==2:
                choices.append((index,points,thickness))
        options.append(choices)
    def complete(selected):
        ports={}
        for line,(_,points,_) in zip(relations['lines'],selected):
            for port,point in zip((line['start'],line['end']),points):
                key=tuple(port)
                if key in ports and np.linalg.norm(ports[key]-point)>epsilon:
                    return None
                ports[key]=point
        if relations['symmetry']:
            coordinate=1 if relations['symmetry']=='horizontal' else 0
            for index,line in enumerate(relations['lines']):
                expected=np.array([line['start'],line['end']]);expected[:,coordinate]=1-expected[:,coordinate]
                partners=[i for i,other in enumerate(relations['lines']) if
                          sorted(map(tuple,expected))==sorted(map(tuple,[other['start'],other['end']]))]
                reflected=np.array(selected[index][1]);reflected[:,coordinate]=1-reflected[:,coordinate]
                if not any(min(np.max(np.linalg.norm(reflected-np.array(selected[i][1]),axis=1)),
                               np.max(np.linalg.norm(reflected-np.array(selected[i][1])[::-1],axis=1)))<=epsilon
                           and abs(selected[index][2]-selected[i][2])<=max(1e-5,selected[index][2]*.03) for i in partners):
                    return None
        return ports
    def assign(index,selected,used):
        if index==len(options):
            return complete(selected)
        for choice in options[index]:
            if choice[0] not in used:
                result=assign(index+1,selected+[choice],used|{choice[0]})
                if result is not None:
                    return result
        return None
    result=assign(0,[],set())
    if result is None:
        raise ValueError('anchor_relation:inconsistent_endpoints_or_symmetry')
    return result


def validate_anchor_relations(svg, relations):
    """Require visible paint along the specified parent-relative segments."""
    from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
    from src.iCCModules.imageCompositeConverterArrowAssertions import _compose,_transform
    from src.iCCModules.imageCompositeConverterDependencies import import_with_vendored_fallback
    root=ET.fromstring(svg)
    rects=[]; drawing=[];geometry=[]
    def visit(node,matrix=(1.,0.,0.,1.,0.,0.),stroke_width=1.):
        tag=node.tag.rsplit('}',1)[-1]
        if tag in {'defs','clipPath','mask','pattern','marker','symbol'}:
            return
        matrix=_compose(matrix,_transform(node.get('transform','')))
        stroke_width=float(node.get('stroke-width',stroke_width))
        a,b,c,d,tx,ty=matrix
        transform=lambda points:np.asarray(points) @ np.array([[a,b],[c,d]])+[tx,ty]
        if tag in {'line','path','polygon','polyline','rect'}:
            drawing.append(node)
        if tag=='line':
            paths=[(np.array([[float(node.get('x1',0)),float(node.get('y1',0))],
                              [float(node.get('x2',0)),float(node.get('y2',0))]]),False)]
        elif tag in {'path','polygon','polyline'}:
            from src.iCCModules.imageCompositeConverterRepresentation import path_points
            paths=path_points(node)
        else:
            paths=[]
        for points,closed in paths:
            if closed:
                geometry.append(transform(points))
            else:
                for start,end in zip(points,points[1:]):
                    direction=end-start;length=np.linalg.norm(direction)
                    if length>0:
                        normal=np.array([-direction[1],direction[0]])*stroke_width/(2*length)
                        geometry.append(transform([start+normal,start-normal,end-normal,end+normal]))
        if tag=='rect':
            x,y,w,h=(float(node.get(k,0)) for k in ('x','y','width','height'))
            a,b,c,d,tx,ty=matrix
            corners=np.array([[a*px+c*py+tx,b*px+d*py+ty] for px,py in ((x,y),(x+w,y),(x+w,y+h),(x,y+h))])
            fill=node.get('fill','black')
            priority=3 if node.get('stroke','none')!='none' else 2 if 'url(' in fill else 1 if fill not in {'white','#fff','#ffffff','none'} else 0
            rects.append((priority,w*h,corners,node))
        for child in node:
            visit(child,matrix,stroke_width)
    visit(root)
    if not rects:
        raise ValueError('anchor_relation:missing_parent_rectangle')
    _,_,corners,panel=max(rects,key=lambda item:item[:2])
    ports=_match_segments(corners,geometry,relations)
    values=[float(v) for v in re.split(r'[\s,]+',root.get('viewBox','').strip())] if root.get('viewBox') else []
    def number(value):
        match=re.match(r'[-+0-9.eE]+',str(value));return float(match[0]) if match else 0.
    w,h=number(root.get('width')),number(root.get('height'))
    if not values:
        values=[0.,0.,w,h]
    if len(values)!=4 or min(values[2:])<=0 or min(w,h)<=0:
        raise ValueError('anchor_relation:invalid_viewport')
    size=min(1.,1600/max(w,h));width,height=max(1,round(w*size)),max(1,round(h*size))
    sx,sy=width/values[2],height/values[3]
    offset=np.array([0.,0.])
    if root.get('preserveAspectRatio','')!='none':
        sx=sy=min(sx,sy)
        offset=np.array([(width-values[2]*sx)/2,(height-values[3]*sy)/2])
    corners=(corners-values[:2])*[sx,sy]+offset
    raster=render_svg_to_numpy_inprocess(svg,width,height,fitz_module=import_with_vendored_fallback('fitz'),
        np_module=np,cv2_module=cv2)
    if raster is None:
        raise ValueError('anchor_relation:render_failed')
    # Remove foreground strokes for a visibility witness. A white patch in
    # the fill or hidden line metadata must not stand in for a visible line.
    background_root=ET.fromstring(svg)
    def remove_marks(parent):
        for child in list(parent):
            tag=child.tag.rsplit('}',1)[-1]
            if tag in {'defs','clipPath','mask','pattern','marker'}:
                continue
            if tag in {'line','path','polygon','polyline'}:
                parent.remove(child)
            else:
                remove_marks(child)
    remove_marks(background_root)
    background_raster=render_svg_to_numpy_inprocess(ET.tostring(background_root,encoding='unicode'),width,height,
        fitz_module=import_with_vendored_fallback('fitz'),np_module=np,cv2_module=cv2)
    if background_raster is None:
        raise ValueError('anchor_relation:background_render_failed')
    contribution=np.linalg.norm(raster.astype(float)-background_raster.astype(float),axis=2)
    panel_bounds=(*corners.min(axis=0),*corners.max(axis=0))
    left,top,right,bottom=panel_bounds
    margin=max(2,int(min(right-left,bottom-top)*.08))
    inner=background_raster[max(0,int(top)+margin):min(height,int(bottom)-margin),
                            max(0,int(left)+margin):min(width,int(right)-margin)].astype(float)
    if not inner.size:
        raise ValueError('anchor_relation:empty_parent')
    axis=relations['gradient_axis']
    if axis:
        profile=np.median(inner,axis=0 if axis=='x' else 1)
        across=np.median(inner,axis=1 if axis=='x' else 0)
        if np.ptp(profile,axis=0).max()<8 or np.std(profile,axis=0).max()<np.std(across,axis=0).max()*2:
            raise ValueError('anchor_relation:wrong_gradient_axis')
        if not _color_matches(np.median(profile,axis=0),relations['fill_color']):
            raise ValueError('anchor_relation:wrong_fill_color')
        if relations['peak_fraction'] is not None:
            length=(right-left) if axis=='x' else (bottom-top)
            peak=(margin+.5+int(np.argmax(profile.mean(axis=1))))/length
            if abs(peak-relations['peak_fraction'])>.15:
                raise ValueError('anchor_relation:wrong_gradient_peak')
    if relations['clipped']:
        yy,xx=np.indices((height,width),dtype=float);xx+=.5;yy+=.5
        outside=(xx<left-1)|(xx>right+1)|(yy<top-1)|(yy>bottom+1)
        if np.any((contribution>18)&outside):
            raise ValueError('anchor_relation:unclipped_paint')
    def sample(point,radius=0):
        x,y=np.floor(point).astype(int)
        if not(0<=x<width and 0<=y<height):
            return np.empty((0,3))
        return raster[max(0,y-radius):min(height,y+radius+1),max(0,x-radius):min(width,x+radius+1)].reshape(-1,3).astype(float)
    for line in relations['lines']:
        def anchor(p):
            p=ports[tuple(p)]
            return corners[0]+p[0]*(corners[1]-corners[0])+p[1]*(corners[3]-corners[0])
        a,b=anchor(line['start']),anchor(line['end']);d=b-a
        length=np.linalg.norm(d)
        if length<=1:
            raise ValueError('anchor_relation:degenerate_line')
        normal=np.array([-d[1],d[0]])/length
        distance=max(3.,min(np.linalg.norm(corners[1]-corners[0]),np.linalg.norm(corners[3]-corners[0]))*.1)
        supported=[]
        for fraction in np.linspace(.08,.92,19):
            point=a+fraction*d
            centre=sample(point,1)
            neighbours=[sample(point+normal*distance),sample(point-normal*distance)]
            neighbours=[v for v in neighbours if len(v)]
            if not len(centre) or not neighbours:
                supported.append(False);continue
            background=np.median(np.concatenate(neighbours),axis=0)
            plausible=_color_matches(centre,relations['mark_color'])
            x,y=np.floor(point).astype(int)
            witness=contribution[max(0,y-1):min(height,y+2),max(0,x-1):min(width,x+2)].ravel()
            supported.append(bool(np.any(plausible & (np.linalg.norm(centre-background,axis=1)>18) & (witness>18))))
        if np.mean(supported)<.8 or not any(supported[:3]) or not any(supported[-3:]):
            raise ValueError('anchor_relation:missing_or_misplaced_line:'+line['name'])
    if relations['under_frame']:
        frames=[i for i,n in enumerate(drawing) if n.tag.rsplit('}',1)[-1]=='rect'
                and n.get('stroke','none')!='none']
        marks=[i for i,n in enumerate(drawing) if n.tag.rsplit('}',1)[-1] in {'line','path','polygon','polyline'}]
        if not frames or (marks and max(frames)<max(marks)):
            raise ValueError('anchor_relation:frame_must_cover_lines')
