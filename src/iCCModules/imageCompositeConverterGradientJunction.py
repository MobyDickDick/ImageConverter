"""Register a beveled T junction from its two transverse color profiles."""
from __future__ import annotations

import cv2
import numpy as np
import re
from xml.etree import ElementTree as ET

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register


def fit_gradient_junction(width, height, *, description, image, render_fn, error_fn):
    """Normalize the described stem direction, measuring every SVG in source space."""
    text = str(description or '').casefold()
    if not all(token in text for token in ('t-verzweigung', 'waagerecht', 'senkrecht',
                                           'verbunden', 'verlauf', 'heller mitte')):
        return None
    if any(token in text for token in ('zusätzlich', 'kreis', 'dreieck', 'getrennt',
                                       'beschrift', 'zwei schäfte')):
        return None
    # A translation of the whole drawing does not change the stem direction.
    # Retain structural directions and conflicting statements about the stem.
    direction_text = re.sub(r'nach (?:oben|rechts|unten|links)(?: und (?:oben|rechts|unten|links))?\s+'
                            r'(?:versetzt|verschoben)', '', text)
    directions = [(token, turns) for token, turns in
                  (('nach oben', 0), ('nach rechts', 1), ('nach unten', 2), ('nach links', 3))
                  if token in direction_text]
    if len(directions) != 1:
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 12:
        return None
    turns = directions[0][1]
    if not turns:
        return _fit_upright(width, height, image=arr, render_fn=render_fn, error_fn=error_fn)
    canonical = np.ascontiguousarray(np.rot90(arr, turns))
    canonical_height, canonical_width = canonical.shape[:2]

    def render_canonical(svg, w, h):
        raster = render_fn(_orient_svg(svg, turns, width, height), width, height)
        return None if raster is None else np.ascontiguousarray(np.rot90(raster, turns))

    def source_error(reference, raster):
        return error_fn(np.ascontiguousarray(np.rot90(reference, -turns)),
                        np.ascontiguousarray(np.rot90(raster, -turns)))

    result = _fit_upright(canonical_width, canonical_height, image=canonical,
                          render_fn=render_canonical, error_fn=source_error)
    if result is not None:
        def source_alignment(candidate):
            reference = cv2.Canny(arr.astype(np.uint8), 50, 140) > 0
            raster = np.ascontiguousarray(np.rot90(candidate['rendered'], -turns))
            edges = cv2.Canny(raster.astype(np.uint8), 50, 140) > 0
            if not reference.any() or not edges.any():
                return 0.
            distance = cv2.distanceTransform((~edges).astype(np.uint8), cv2.DIST_L2, 3)
            reference_distance = cv2.distanceTransform((~reference).astype(np.uint8), cv2.DIST_L2, 3)
            return float((np.exp(-distance[reference]).mean() + np.exp(-reference_distance[edges]).mean())/2)

        # Retain accepted fits. Only an insufficient source-space contour
        # needs the additional search in the production edge frame.
        alignment = source_alignment(result)
        if alignment < .72:
            refined = _fit_upright(canonical_width, canonical_height, image=canonical,
                render_fn=render_canonical, error_fn=source_error,
                edge_frame=lambda raster: np.ascontiguousarray(np.rot90(raster, -turns)))
            if refined is not None and source_alignment(refined) > alignment:
                refined['evaluations'] += result['evaluations']
                result = refined
    if result is not None:
        for key in ('svg', 'initial_svg'):
            result[key] = _orient_svg(result[key], turns, width, height)
        result['rendered'] = np.ascontiguousarray(np.rot90(result['rendered'], -turns))
    return result


def _orient_svg(svg, turns, width, height):
    """Rotate analytic coordinates and native gradient axes without rasterization."""
    root = ET.fromstring(svg)

    def point(x, y):
        return ((width-y, x) if turns == 1 else
                (width-x, height-y) if turns == 2 else (y, height-x))

    for element in root.iter():
        element.tag = element.tag.rsplit('}', 1)[-1]
        if element.tag == 'rect':
            x, y, w, h = (float(element.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
            corners = np.array([point(a, b) for a, b in ((x,y),(x+w,y),(x,y+h),(x+w,y+h))])
            lo, hi = corners.min(axis=0), corners.max(axis=0)
            for key, value in zip(('x','y','width','height'), (*lo, *(hi-lo))):
                element.set(key, f'{value:g}')
        elif element.tag == 'polygon':
            points = [point(*(float(v) for v in p.split(','))) for p in element.get('points').split()]
            element.set('points', ' '.join(f'{x:g},{y:g}' for x,y in points))
        elif element.tag == 'linearGradient':
            for suffix in ('1','2'):
                x, y = point(float(element.get('x'+suffix, 0)), float(element.get('y'+suffix, 0)))
                element.set('x'+suffix, f'{x:g}')
                element.set('y'+suffix, f'{y:g}')
    root.set('xmlns', 'http://www.w3.org/2000/svg')
    root.set('width', str(width))
    root.set('height', str(height))
    root.set('viewBox', f'0 0 {width} {height}')
    return ET.tostring(root, encoding='unicode')+'\n'


def _fit_upright(width, height, *, image, render_fn, error_fn, edge_frame=lambda raster: raster):
    arr = np.asarray(image)
    pixels = arr.astype(float)
    if not np.isfinite(pixels).all():
        return None
    mask = (np.min(pixels, axis=2) < 230).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
    # The two arms form one T silhouette. Isolated marks, holes and unmodeled
    # branches must not be silently absorbed by a fitted bounding rectangle.
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if count < 2:
        return None
    index = 1+int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if sum(stats[i, cv2.CC_STAT_AREA] for i in range(1,count) if i != index) > 2:
        return None
    foreground = labels == index
    rows = np.flatnonzero(foreground.any(axis=1))
    if len(rows) < 6:
        return None
    spans = np.array([np.flatnonzero(foreground[y])[[0,-1]] for y in rows])
    widths = spans[:,1]-spans[:,0]+1
    wide = widths > widths.max()*.8
    if not wide.any():
        return None
    bar_rows = rows[wide]
    y0, y1 = int(bar_rows[0]), int(bar_rows[-1])+1
    stem_rows = rows[rows < y0]
    if len(stem_rows)<3 or y1-y0<3 or np.any(rows>y1-1):
        return None
    left, right = np.median(spans[wide],axis=0)
    right += 1
    stem_spans = spans[rows < y0]
    sl, sr = np.median(stem_spans,axis=0)
    sr += 1
    top = int(stem_rows[0])
    if not (left+2 < sl < sr < right-2 and sr-sl >= 3
            and y0-top >= max(3,(sr-sl)*.65)):
        return None
    # JPEG ringing can widen the single row immediately beside the bar.
    # Measure shaft uniformity away from that seam, just like its color
    # profile below. The exterior residual still checks the complete shape.
    stem_core = spans[rows < y0-1]
    if not len(stem_core) or np.max(np.abs(stem_core-[sl,sr-1])) > 1.5:
        return None
    expected=np.zeros_like(foreground)
    expected[y0:y1,int(left):int(right)]=True
    expected[top:y0,int(sl):int(sr)]=True
    # A bright specular center may cross the foreground threshold. Only
    # unexplained exterior pixels are a topology contradiction at this stage;
    # the rendered profile checks the complete interior below.
    if np.count_nonzero(foreground & ~expected)>max(2,expected.sum()*.01):
        return None
    # Measure each arm away from the junction. A short dimensionless profile
    # is an observed gradient, never a saved catalog color table.
    bar_columns=np.r_[np.arange(int(left),max(int(left),int(sl)-1)),
                      np.arange(min(int(right),int(sr)+1),int(right))]
    if len(bar_columns)<4:
        return None
    bar_profile=np.median(pixels[y0:y1,bar_columns],axis=1)
    stem_profile=np.median(pixels[top:max(top+1,y0-1),int(sl):int(sr)],axis=0)
    for observations,profile in (
        (pixels[y0:y1,bar_columns].transpose(1,0,2),bar_profile),
        (pixels[top:max(top+1,y0-1),int(sl):int(sr)],stem_profile)):
        if np.percentile(np.max(np.abs(observations-profile),axis=2),95)>30:
            return None
    profiles=[]
    raw_profiles=[]
    seed_profiles=[]
    for profile in (bar_profile,stem_profile):
        middle=len(profile)//2
        edge=max(profile[:middle].mean(axis=1).min(),profile[middle+1:].mean(axis=1).min())
        if len(profile)<3 or profile[middle].mean()<=edge+8:
            return None
        # Robust regional means provide a coarse cylindrical initialization.
        # Its measured production error bounds both detailed profile proposals.
        regions=np.array_split(profile,3)
        seed_profiles.append([(0.,regions[0].mean(axis=0)),
                              (.5,regions[1].mean(axis=0)),
                              (1.,regions[2].mean(axis=0))])
        indices=np.unique(np.rint(np.linspace(0,len(profile)-1,min(9,len(profile)))).astype(int))
        raw_profiles.append([((i+.5)/len(profile),profile[i].copy()) for i in indices])
        profile=profile.copy()
        # Fractional silhouette coverage brightens the first/last observation.
        # Continue the adjacent interior slope instead of baking that fringe
        # into the gradient and rendering it a second time.
        if len(profile)>=5:
            if profile[0].mean()>profile[1].mean():
                profile[0]=2*profile[1]-profile[2]
            if profile[-1].mean()>profile[-2].mean():
                profile[-1]=2*profile[-2]-profile[-3]
        if len(profile)>=8:
            coordinates=(np.arange(len(profile))+.5)/len(profile)
            lo=np.arange(1,middle)
            hi=np.arange(middle+1,len(profile)-1)
            ascending=np.polyfit(coordinates[lo],profile[lo],1)
            descending=np.polyfit(coordinates[hi],profile[hi],1)
            deviation=max(np.max(np.abs(ascending[0]*coordinates[lo,None]+ascending[1]-profile[lo])),
                          np.max(np.abs(descending[0]*coordinates[hi,None]+descending[1]-profile[hi])))
            # A truly linear highlight should keep its analytic three stops;
            # sampling it into many short segments creates quantization edges.
            slope=(ascending[0]-descending[0]).mean()
            peak=(descending[1]-ascending[1]).mean()/slope if abs(slope)>1e-6 else -1
            if deviation<3 and .3<peak<.7:
                profiles.append([(0.,ascending[1]),
                    (peak,(ascending[0]*peak+ascending[1]+descending[0]*peak+descending[1])/2),
                    (1.,descending[0]+descending[1])])
                continue
        indices=np.unique(np.rint(np.linspace(0,len(profile)-1,min(9,len(profile)))).astype(int))
        profiles.append([((i+.5)/len(profile),profile[i]) for i in indices])

    def build(p):
        x0,x1,by0,by1,sx0,sx1,sy=p[:7]
        cx,cy=(sx0+sx1)/2,(by0+by1)/2
        gradients=[]
        for name,axis,start,end,profile in (
            ('bar_color','y',by0,by1,profiles[0]),('stem_color','x',sx0,sx1,profiles[1])):
            coords=(f'x1="0" x2="0" y1="{start:g}" y2="{end:g}"' if axis=='y' else
                    f'y1="0" y2="0" x1="{start:g}" x2="{end:g}"')
            stops=''.join(f'<stop offset="{t:g}" stop-color="{_hex(color+np.array(p[7:10]))}"/>' for t,color in profile)
            gradients.append(f'<linearGradient id="{name}" gradientUnits="userSpaceOnUse" {coords}>{stops}</linearGradient>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs>{"".join(gradients)}</defs><rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<rect x="{x0:g}" y="{by0:g}" width="{x1-x0:g}" height="{by1-by0:g}" fill="url(#bar_color)"/>'
                f'<polygon points="{sx0:g},{sy:g} {sx1:g},{sy:g} {sx1:g},{by0:g} {cx:g},{cy:g} {sx0:g},{by0:g}" fill="url(#stem_color)"/></svg>\n')

    def valid(p):
        x0,x1,by0,by1,sx0,sx1,sy=p[:7]
        return (np.isfinite(p).all() and 0<=x0<sx0<sx1<x1<=width
                and 0<=sy<by0<by1<=height and min(sx1-sx0,by1-by0)>=2)

    # Canny's non-maximum suppression is not invariant under quarter turns
    # at quantized gradient ties. Evaluate edges in the original pixel frame,
    # as the production quality check does, while fitting canonical geometry.
    reference_edges=cv2.Canny(edge_frame(arr.astype(np.uint8)),50,140)>0
    reference_distance=cv2.distanceTransform((~reference_edges).astype(np.uint8),cv2.DIST_L2,3)
    reference_mask=np.min(pixels,axis=2)<210
    border=np.concatenate((pixels[0],pixels[-1],pixels[:,0],pixels[:,-1]))
    background=np.median(border,axis=0)
    reference_silhouette=np.max(np.abs(pixels-background),axis=2)>25
    # For low-contrast profiles a tiny color change can erase the foreground
    # mask while barely affecting MSE. Give that observation explicit weight.
    mask_weight=.003*max(0.,1-np.ptp(bar_profile.mean(axis=1))/100)

    def loss(reference,raster):
        edges=cv2.Canny(edge_frame(np.asarray(raster,dtype=np.uint8)),50,140)>0
        if not edges.any() or not reference_edges.any():
            return float('inf')
        distance=cv2.distanceTransform((~edges).astype(np.uint8),cv2.DIST_L2,3)
        alignment=(np.exp(-distance[reference_edges]).mean()+np.exp(-reference_distance[edges]).mean())/2
        output_mask=np.min(raster,axis=2)<210
        union=np.count_nonzero(reference_mask|output_mask)
        iou=np.count_nonzero(reference_mask&output_mask)/union if union else 1.
        silhouette=np.max(np.abs(np.asarray(raster,dtype=float)-background),axis=2)>25
        silhouette_union=np.count_nonzero(reference_silhouette|silhouette)
        silhouette_iou=np.count_nonzero(reference_silhouette&silhouette)/silhouette_union if silhouette_union else 1.
        return (np.square(pixels-np.asarray(raster,dtype=float)).mean()/255**2
                +.005*(1-alignment)+mask_weight*(1-iou)+.003*(1-silhouette_iou))

    parameters=[left,right,y0,y1,sl,sr,top,0,0,0]
    render_count=0

    def counted_render(svg,w,h):
        nonlocal render_count
        render_count+=1
        return render_fn(svg,w,h)
    # The actual initialization is the coarse regional profile. Detailed
    # fringe correction and analytic regression are refinement proposals and
    # must share that initial production-error ceiling with geometry search.
    refined_profiles=profiles
    profiles=seed_profiles
    initial_svg=build(parameters)
    initial_raster=counted_render(initial_svg,width,height)
    if initial_raster is None:
        return None
    initial_error=float(error_fn(image,initial_raster))
    results=[]
    for profiles in (raw_profiles,refined_profiles):
        candidate=_register(parameters,7,build,valid,image,counted_render,error_fn,
                            'raster_gradient_junction_v1',preserve_initial_error=True,
                            loss_fn=loss,initial_error_bound=initial_error)
        if candidate is not None:
            results.append(candidate)
    if not results:
        return None
    result=min(results,key=lambda candidate:loss(image,candidate['rendered']))
    # Recheck unexplained foreground after the bounded registration, including
    # marks inside a nominally valid T silhouette.
    rendered=np.asarray(result['rendered'],dtype=float)
    unexplained=(np.max(np.abs(pixels-rendered),axis=2)>60).astype(np.uint8)
    n,_,components,_=cv2.connectedComponentsWithStats(unexplained)
    if any(components[i,cv2.CC_STAT_AREA]>max(5,foreground.sum()*.06) for i in range(1,n)):
        return None
    result['initial_svg']=initial_svg
    result['evaluations']=render_count
    return result
