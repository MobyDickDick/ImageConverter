"""Observe a gradient panel, a hollow diagonal and a central analytic outline.

The cutout is along the diagonal's centre, not a gap at its intersection.
Only raster-derived native geometry is used; no catalog identity or SVG seed.
"""
from __future__ import annotations

import re
import cv2
import numpy as np
from xml.etree import ElementTree as ET

from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description
from src.iCCModules.imageCompositeConverterFilledSymbols import _register


def central_outline(description):
    text = re.sub(r'"[^"\n]*"|„[^“\n]*“', '', normalize_description(description)).casefold()
    match = re.search(r'(?:zentrum|mitte|mittig)[^.;]*?\b(kreis|quadrat|raute)\b', text)
    return 'circle' if match and match[1] == 'kreis' else 'diamond'


def hollow_cross_contract(description):
    text = re.sub(r'"[^"\n]*"|„[^“\n]*“','',normalize_description(description)).casefold()
    text = ' '.join(text.split())
    split_axis = (re.search(r'(?:mitte|mittellinie|inneres).*?(?:ausgeschnitten|ausgespart|hohl)', text)
                  or re.search(r'diagonal\w*[^.;]*?(?:durch|aus)\s+(?:zwei|2)\s+parallele[nrms]?\s+linien\b', text))
    return bool(all(t in text for t in ('rechteck', 'grau', 'diagonal', 'verlauf', 'horizontal'))
                and re.search(r'(?:beiden?|zwei) diagonalen', text)
                and re.search(r'oben rechts.*unten links',text)
                and split_axis
                and re.search(r'(?:zentrum|mitte|mittig).*?(?:quadrat|raute|kreis)', text)
                and 'rand' in text and ('keinen hintergrund' in text or 'ohne füllung' in text
                                         or 'ohne fuellung' in text)
                and not any(t in text for t in ('ohne diagonalen', 'kein quadrat', 'keine raute',
                                                'ohne quadrat', 'ohne raute', 'kein kreis', 'ohne kreis',
                                                'nicht ausgeschnitten')))


def _observe_local_hollow_cross(image, outline='diamond'):
    """Require both long axes, the light slit and the observed outline."""
    pixels = np.asarray(image, dtype=float)
    if pixels.ndim != 3 or pixels.shape[2] != 3 or not np.isfinite(pixels).all():
        return None
    height, width = pixels.shape[:2]
    if width < 20 or height < width*1.5 or np.percentile(np.ptp(pixels, axis=2), 95) > 15:
        return None
    gray = pixels.mean(axis=2)
    yy, xx = np.indices(gray.shape, dtype=float)
    xx += .5
    yy += .5
    profile = np.percentile(gray[2:-2], 80, axis=0)
    peak = float(np.argmax(profile[2:-2])+2.5)
    field = profile[None, :]
    darkness = field-gray
    rows = np.flatnonzero(((yy[:,0] > height*.12) & (yy[:,0] < height*.34))
                         | ((yy[:,0] > height*.66) & (yy[:,0] < height*.88)))
    axes = []
    for ascending in (False, True):
        xs, ys, widths = [], [], []
        for row in rows:
            left = (row < height/2) != ascending
            mask = (xx[row] < width/2 if left else xx[row] > width/2)
            mask &= (xx[row] > 2) & (xx[row] < width-2) & (darkness[row] > 35)
            columns = np.flatnonzero(mask)
            if len(columns) < 2:
                continue
            xs.append(float(np.average(xx[row,mask], weights=darkness[row,mask]**2)))
            ys.append(row+.5)
            widths.append(columns[-1]-columns[0]+1)
        if len(xs) < len(rows)*.8:
            return None
        slope, intercept = np.polyfit(ys, xs, 1)
        if (slope < 0) != ascending or not .03 < abs(slope) < .8:
            return None
        if np.mean(abs(np.asarray(xs)-np.polyval([slope,intercept],ys))) > 1:
            return None
        distance = abs(xx-slope*yy-intercept)/np.hypot(1,slope)
        axes.append((float(intercept),float(slope*height+intercept),float(np.median(widths)),distance))
    # Distinct light centre and dark rails must run along the ascending axis.
    rising = axes[1]
    sample = np.array(rows)
    centers = rising[0]+(rising[1]-rising[0])*(sample+.5)/height
    def values(offset):
        return gray[sample,np.clip(np.floor(centers+offset).astype(int),0,width-1)]
    rails = (values(-rising[2]*.32)+values(rising[2]*.32))/2
    if np.median(values(0)-rails) < 25:
        return None
    residual = ((darkness > 35) & (xx > 2) & (xx < width-2)
                & (yy > height*.3) & (yy < height*.7))
    for axis in axes:
        residual &= axis[3] > axis[2]/2+1
    points = np.column_stack((xx[residual], yy[residual]))
    if len(points) < width*.5:
        return None
    # Diagonals can hide the vertices. The bounds of the *visible* outline
    # then have a biased centre; keeping that centre fixed rejected valid
    # smaller panels before any search. Fit all four sides and the centre
    # jointly, without requiring the hidden tips to supply extrema.
    cx,cy = width/2,height/2
    if outline == 'circle':
        relative = points-[cx,cy]
        matrix = np.c_[2*relative,np.ones(len(points))]
        coefficients,_,rank,_ = np.linalg.lstsq(matrix,(relative**2).sum(axis=1),rcond=None)
        if rank < 3 or not np.isfinite(coefficients).all():
            return None
        radius2 = coefficients[2]+np.dot(coefficients[:2],coefficients[:2])
        if radius2 <= 0:
            return None
        cx,cy = np.array([cx,cy])+coefficients[:2]
        rx = ry = np.sqrt(radius2)
        distance = abs(np.hypot(xx-cx,yy-cy)-rx)
        point_error = abs(np.linalg.norm(points-[cx,cy],axis=1)-rx)/rx
    else:
        for _ in range(6):
            signs = np.where(points >= [cx,cy],1.,-1.)
            matrix = np.c_[signs*points,-signs]
            coefficients,_,rank,_ = np.linalg.lstsq(matrix,np.ones(len(points)),rcond=None)
            if rank < 4 or not np.isfinite(coefficients).all() or np.min(coefficients[:2]) <= 0:
                return None
            cx,cy = coefficients[2:]/coefficients[:2]
        rx,ry = 1/coefficients[:2]
        distance = abs(abs(xx-cx)/rx+abs(yy-cy)/ry-1)/np.hypot(1/rx,1/ry)
        point_error = abs(abs(points[:,0]-cx)/rx+abs(points[:,1]-cy)/ry-1)
    if not (.25*width < rx < .6*width and .55 < rx/ry < 1.8
            and abs(cx-width/2) < width*.15 and abs(cy-height/2) < height*.12):
        return None
    if np.percentile(point_error,80) > .15:
        return None
    for sx,sy in ((-1,-1),(-1,1),(1,-1),(1,1)):
        side = residual & ((xx-cx)*sx > 0) & ((yy-cy)*sy > 0) & (distance < 2)
        if side.sum() < max(3,width*.09):
            return None
    return dict(axes=axes, diamond=(float(cx),float(cy),float(rx),float(ry)),
                diamond_distance=distance, profile=profile, peak=peak, gray=gray,
                darkness=darkness, xx=xx, yy=yy)


def observe_hollow_cross(image, outline='diamond'):
    """Observe in the panel's own bounds, independently of the canvas margin."""
    pixels = np.asarray(image)
    if pixels.ndim != 3 or pixels.shape[2] != 3 or not np.isfinite(pixels).all():
        return None
    height,width = pixels.shape[:2]
    count,labels,stats,_ = cv2.connectedComponentsWithStats((pixels.mean(axis=2) < 245).astype('uint8'))
    if count < 2:
        return None
    index = 1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
    x,y,w,h,area = map(int,stats[index])
    if area < w*h*.45 or w < 20 or h < w*1.5:
        return None
    # Do not silently ignore extra disconnected objects around the panel.
    if sum(stats[i,cv2.CC_STAT_AREA] for i in range(1,count) if i != index) > max(3,area*.001):
        return None
    local = _observe_local_hollow_cross(pixels[y:y+h,x:x+w],outline)
    if local is None:
        return None
    yy,xx = np.indices((height,width),dtype=float)
    xx += .5
    yy += .5
    axes = []
    for top,bottom,thickness,_ in local['axes']:
        slope = (bottom-top)/h
        intercept = top+x-slope*y
        distance = abs(xx-slope*yy-intercept)/np.hypot(1,slope)
        axes.append((intercept,intercept+slope*height,thickness,distance))
    cx,cy,rx,ry = local['diamond']
    cx,cy = cx+x,cy+y
    profile = np.full(width,255.,dtype=float)
    profile[x:x+w] = local['profile']
    gray = pixels.astype(float).mean(axis=2)
    distance = (abs(np.hypot(xx-cx,yy-cy)-rx) if outline == 'circle' else
                abs(abs(xx-cx)/rx+abs(yy-cy)/ry-1)/np.hypot(1/rx,1/ry))
    return dict(axes=axes,diamond=(cx,cy,rx,ry),bounds=(x,y,x+w,y+h),
                diamond_distance=distance,
                profile=profile,peak=local['peak']+x,gray=gray,
                darkness=profile[None,:]-gray,xx=xx,yy=yy)


def fit_hollow_cross_panel(width, height, *, description, image, render_fn, error_fn):
    if not hollow_cross_contract(description):
        return None
    arr = np.asarray(image)
    if arr.shape != (height,width,3):
        return None
    outline = central_outline(description)
    observed = observe_hollow_cross(arr,outline)
    if observed is None:
        return None
    axes, profile, peak = observed['axes'], observed['profile'], observed['peak']
    xx,yy,gray = (observed[k] for k in ('xx','yy','gray'))
    x,y,right,bottom = observed['bounds']
    panel_width,panel_height = right-x,bottom-y
    cx,cy,rx,ry = observed['diamond']
    upper = (yy > y) & (yy < y+panel_height*.3) & (xx > x) & (xx < right)
    descending_paint = (axes[0][3] < 1) & upper
    rising_paint = (axes[1][3] < axes[1][2]/2) & upper
    diamond_paint = (observed['diamond_distance'] < 1) & (axes[0][3] > 6) & (axes[1][3] > 6)
    if not all(mask.any() for mask in (descending_paint,rising_paint,diamond_paint)):
        return None
    p = [x+.5,y+.5,right-.5,bottom-.5,.8,peak,
         *axes[0][:3],*axes[1][:3],max(.6,axes[1][2]*.25),cx,cy,(rx+ry)/2,2.,
         float(profile[x+2]),float(profile[int(peak)]),float(profile[right-3]),
         float(np.percentile(gray[y:bottom,x],50)),
         float(np.percentile(gray[descending_paint],20)),
         float(np.percentile(gray[rising_paint],20)),
         float(np.percentile(gray[diamond_paint],20))]
    geometry_count = 17
    def color(v):
        return '#'+f'{int(np.clip(round(v),0,255)):02x}'*3
    def build(v):
        l,t,r,b,rim,peak,a0,a1,aw,b0,b1,bw,slit,cx,cy,radius,dw = v[:17]
        fl, ft = max(l, rim/2), max(t, rim/2)
        fr, fb = min(r, width-rim/2), min(b, height-rim/2)
        stops = ''.join(f'<stop offset="{offset:.8f}" stop-color="{color(c)}"/>'
                        for offset,c in zip((0,(peak-l)/(r-l),1),v[17:20]))
        # Explicit intersection avoids depending on renderer clipPath support.
        def band(top,bottom,thickness,fill,offset=0.):
            dx = bottom-top
            length = np.hypot(dx,height)
            top,bottom = top+height*offset/length,bottom+height*offset/length
            shift_y = -dx*offset/length
            nx,ny = height*thickness/(2*length),-dx*thickness/(2*length)
            # Extend through the panel before intersecting its four bounds.
            # Each rail is a complete stroke, not an opaque central repaint.
            extension = max(abs(offset),thickness)+2
            ex,ey = dx*extension/length,height*extension/length
            polygon = [(top+nx-ex,shift_y+ny-ey),(top-nx-ex,shift_y-ny-ey),
                       (bottom-nx+ex,height+shift_y-ny+ey),(bottom+nx+ex,height+shift_y+ny+ey)]
            from src.iCCModules.imageCompositeConverterRelations import clip_polygon
            polygon = clip_polygon(polygon,(l,t,r,b))
            points = ' '.join(f'{x:.6f},{y:.6f}' for x,y in polygon)
            return f'<polygon points="{points}" fill="{fill}"/>'
        # Repeat the first point explicitly: MuPDF omits the closing polygon
        # stroke in some versions, although browsers correctly close it.
        diamond = f'{cx:.6f},{cy-radius:.6f} {cx+radius:.6f},{cy:.6f} {cx:.6f},{cy+radius:.6f} {cx-radius:.6f},{cy:.6f} {cx:.6f},{cy-radius:.6f}'
        center = (f'<circle cx="{cx:.6f}" cy="{cy:.6f}" r="{radius:.6f}"' if outline == 'circle'
                  else f'<polygon points="{diamond}"')
        center += f' fill="none" stroke="{color(v[23])}" stroke-width="{dw:.6f}"/>'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="panelPaint" gradientUnits="userSpaceOnUse" x1="{l:.6f}" x2="{r:.6f}" y1="0" y2="0">{stops}</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="white"/>'
                f'<rect x="{l:.6f}" y="{t:.6f}" width="{r-l:.6f}" height="{b-t:.6f}" fill="url(#panelPaint)"/>'
                +band(b0,b1,(bw-slit)/2,color(v[22]),-(bw+slit)/4)
                +band(b0,b1,(bw-slit)/2,color(v[22]),(bw+slit)/4)
                +band(a0,a1,aw,color(v[21]))
                +center
                +f'<rect x="{fl:.6f}" y="{ft:.6f}" width="{fr-fl:.6f}" height="{fb-ft:.6f}" fill="none" stroke="{color(v[20])}" stroke-width="{rim:.6f}"/></svg>')
    def valid(v):
        return (np.isfinite(v).all() and np.max(abs(v[:4]-p[:4])) < 2
                and x <= v[0] < v[2] <= right and y <= v[1] < v[3] <= bottom
                and v[2] > v[0] and v[3] > v[1] and .2 < v[4] < 3
                and x+panel_width*.2 < v[5] < x+panel_width*.8 and v[6] < v[7] and v[9] > v[10]
                and 1 < min(v[8],v[11]) and max(v[8],v[11]) < panel_width*.23
                and .4 < v[12] < v[11]*.6 and abs(v[13]-cx) < 3 and abs(v[14]-cy) < 4
                and min(rx,ry)*.8 < v[15] < max(rx,ry)*1.2 and .4 < v[16] < 4
                and np.all((v[17:] >= 0) & (v[17:] <= 255)))
    detail_regions = [observed['diamond_distance'] < 2.5]
    detail_regions += [(a[3] < a[2]/2+1) & (yy > y+panel_height*.1) & (yy < bottom-panel_height*.1)
                       & (xx > x) & (xx < right) for a in axes]
    def details(rendered):
        error = ((arr.astype(float)-rendered.astype(float))**2).mean(axis=2)/255**2
        errors = [float(error[region].mean()) for region in detail_regions]
        return dict(outline_mse=errors[0],diagonal_mse=errors[1:],passed=max(errors) < .004)
    def loss(reference,rendered):
        error = ((reference.astype(float)-rendered.astype(float))**2).mean(axis=2)
        return float(error.mean()+sum(error[region].mean() for region in detail_regions))
    result = _register(p,geometry_count,build,valid,arr,render_fn,error_fn,'raster_hollow_cross_panel_v1',
                       loss_fn=loss,satisfactory_fn=lambda p,m: details(m[3])['passed'],
                       refinement_steps=(1.,.5,.25,.125,.0625))
    if result is None:
        return None
    result['quality'] = pixel_quality(arr,result['rendered'])
    result['details'] = details(result['rendered'])
    return result if (result['quality']['passed'] and result['details']['passed']
                      and observe_hollow_cross(result['rendered'],outline) is not None) else None


def validate_hollow_cross_panel(svg, outline='diamond'):
    """Check visible structure, including samples and arbitrary path encodings.

    Rendering respects inherited styles, transforms, occlusion and definitions;
    hidden or metadata-only claims cannot stand in for the requested detail.
    No fitting or source-image access happens during assertion validation.
    """
    from src.iCCModules.imageCompositeConverterDependencies import import_with_vendored_fallback
    from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
    root = ET.fromstring(svg)
    try:
        box = [float(v) for v in re.split(r'[\s,]+',root.get('viewBox','').strip())]
        w,h = box[2:] if len(box) == 4 else (float(root.get('width','0')),float(root.get('height','0')))
        if not (np.isfinite([w,h]).all() and w > 0 and h > 0):
            raise ValueError('invalid viewport')
        scale = min(1600/max(w,h), max(1.,40/w))
        width,height = max(1,round(w*scale)),max(1,round(h*scale))
    except (ValueError,TypeError):
        raise ValueError('hollow_cross_panel:invalid_viewport')
    raster = render_svg_to_numpy_inprocess(svg,width,height,
        fitz_module=import_with_vendored_fallback('fitz'),np_module=np,
        cv2_module=import_with_vendored_fallback('cv2'))
    if raster is None or observe_hollow_cross(raster,outline) is None:
        raise ValueError('hollow_cross_panel:missing_outline_or_diagonal_cutout')
    # Pixel similarity cannot certify straightness or an exact central form.
    from src.iCCModules.imageCompositeConverterRepresentation import validate_object_limits
    validate_object_limits(svg,{'circle' if outline == 'circle' else 'square':1})
    # Either two axes with an analytic cutout or three separate straight
    # strokes can encode the same hollow diagonal. Neither permits a kink.
    from src.iCCModules.imageCompositeConverterRepresentation import logical_inventory
    inventory = logical_inventory(svg,{'diagonal':3,'circle' if outline == 'circle' else 'square':1})
    allowed = {'diagonal','rect','circle' if outline == 'circle' else 'square'}
    if (inventory.get('diagonal',0) not in (2,3) or inventory.get('rect',0) != 1
            or any(count for kind,count in inventory.items() if kind not in allowed)):
        raise ValueError('hollow_cross_panel:nonlinear_diagonal')
