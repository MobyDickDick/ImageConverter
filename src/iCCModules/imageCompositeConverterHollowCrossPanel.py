"""Observe a gradient panel, a hollow diagonal and a central outlined diamond.

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


def hollow_cross_contract(description):
    text = re.sub(r'"[^"\n]*"|„[^“\n]*“','',normalize_description(description)).casefold()
    text = ' '.join(text.split())
    return bool(all(t in text for t in ('rechteck', 'grau', 'diagonal', 'verlauf', 'horizontal'))
                and re.search(r'(?:beiden?|zwei) diagonalen', text)
                and re.search(r'oben rechts.*unten links',text)
                and re.search(r'(?:mitte|mittellinie|inneres).*?(?:ausgeschnitten|ausgespart|hohl)', text)
                and re.search(r'(?:zentrum|mitte|mittig).*?(?:quadrat|raute)', text)
                and 'rand' in text and ('keinen hintergrund' in text or 'ohne füllung' in text
                                         or 'ohne fuellung' in text)
                and not any(t in text for t in ('ohne diagonalen', 'kein quadrat', 'keine raute',
                                                'ohne quadrat', 'ohne raute', 'nicht ausgeschnitten')))


def _observe_local_hollow_cross(image):
    """Require both long axes, the light slit and all four diamond edges."""
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
    cx,cy = (points.min(axis=0)+points.max(axis=0))/2
    # A diamond is four straight edges in this coordinate system, not just
    # a dark spot at the axes' crossing. Fit its two independent half sizes.
    coefficients = np.linalg.lstsq(abs(points-[cx,cy]),np.ones(len(points)),rcond=None)[0]
    if np.min(coefficients) <= 0:
        return None
    rx,ry = 1/coefficients
    distance = abs(abs(xx-cx)/rx+abs(yy-cy)/ry-1)/np.hypot(1/rx,1/ry)
    if not (.25*width < rx < .6*width and .55 < rx/ry < 1.8
            and abs(cx-width/2) < width*.15 and abs(cy-height/2) < height*.12):
        return None
    if np.percentile(abs(abs(points[:,0]-cx)/rx+abs(points[:,1]-cy)/ry-1),80) > .15:
        return None
    for sx,sy in ((-1,-1),(-1,1),(1,-1),(1,1)):
        side = residual & ((xx-cx)*sx > 0) & ((yy-cy)*sy > 0) & (distance < 2)
        if side.sum() < max(3,width*.09):
            return None
    return dict(axes=axes, diamond=(float(cx),float(cy),float(rx),float(ry)),
                diamond_distance=distance, profile=profile, peak=peak, gray=gray,
                darkness=darkness, xx=xx, yy=yy)


def observe_hollow_cross(image):
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
    local = _observe_local_hollow_cross(pixels[y:y+h,x:x+w])
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
    return dict(axes=axes,diamond=(cx,cy,rx,ry),bounds=(x,y,x+w,y+h),
                diamond_distance=abs(abs(xx-cx)/rx+abs(yy-cy)/ry-1)/np.hypot(1/rx,1/ry),
                profile=profile,peak=local['peak']+x,gray=gray,
                darkness=profile[None,:]-gray,xx=xx,yy=yy)


def fit_hollow_cross_panel(width, height, *, description, image, render_fn, error_fn):
    if not hollow_cross_contract(description):
        return None
    arr = np.asarray(image)
    if arr.shape != (height,width,3):
        return None
    observed = observe_hollow_cross(arr)
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
         *axes[0][:3],*axes[1][:3],max(.6,axes[1][2]*.25),cx,cy,rx,ry,2.,
         float(profile[x+2]),float(profile[int(peak)]),float(profile[right-3]),
         float(np.percentile(gray[y:bottom,x],50)),
         float(np.percentile(gray[descending_paint],20)),
         float(np.percentile(gray[rising_paint],20)),
         float(np.percentile(gray[diamond_paint],20))]
    geometry_count = 18
    def color(v):
        return '#'+f'{int(np.clip(round(v),0,255)):02x}'*3
    def build(v):
        l,t,r,b,rim,peak,a0,a1,aw,b0,b1,bw,slit,cx,cy,rx,ry,dw = v[:18]
        stops = ''.join(f'<stop offset="{offset:.8f}" stop-color="{color(c)}"/>'
                        for offset,c in zip((0,(peak-l)/(r-l),1),v[18:21]))
        # Explicit intersection avoids depending on renderer clipPath support.
        def band(top,bottom,thickness,fill):
            dx = bottom-top
            nx,ny = height*thickness/(2*np.hypot(dx,height)),-dx*thickness/(2*np.hypot(dx,height))
            polygon = [(top+nx,ny),(top-nx,-ny),(bottom-nx,height-ny),(bottom+nx,height+ny)]
            for axis,bound,sign in ((0,l,1),(0,r,-1),(1,t,1),(1,b,-1)):
                clipped = []
                for start,end in zip(polygon,polygon[1:]+polygon[:1]):
                    ins,ine = sign*(start[axis]-bound)>=0,sign*(end[axis]-bound)>=0
                    if ins != ine:
                        f = (bound-start[axis])/(end[axis]-start[axis])
                        clipped.append(tuple(start[j]+f*(end[j]-start[j]) for j in (0,1)))
                    if ine:
                        clipped.append(end)
                polygon = clipped
            points = ' '.join(f'{x:.6f},{y:.6f}' for x,y in polygon)
            return f'<polygon points="{points}" fill="{fill}"/>'
        # Repeat the first point explicitly: MuPDF omits the closing polygon
        # stroke in some versions, although browsers correctly close it.
        diamond = f'{cx:.6f},{cy-ry:.6f} {cx+rx:.6f},{cy:.6f} {cx:.6f},{cy+ry:.6f} {cx-rx:.6f},{cy:.6f} {cx:.6f},{cy-ry:.6f}'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="panelPaint" gradientUnits="userSpaceOnUse" x1="{l:.6f}" x2="{r:.6f}" y1="0" y2="0">{stops}</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="white"/>'
                f'<rect x="{l:.6f}" y="{t:.6f}" width="{r-l:.6f}" height="{b-t:.6f}" fill="url(#panelPaint)"/>'
                +band(b0,b1,bw,color(v[23]))+band(b0,b1,slit,'url(#panelPaint)')
                +band(a0,a1,aw,color(v[22]))
                +f'<polygon points="{diamond}" fill="none" stroke="{color(v[24])}" stroke-width="{dw:.6f}"/>'
                f'<rect x="{l:.6f}" y="{t:.6f}" width="{r-l:.6f}" height="{b-t:.6f}" fill="none" stroke="{color(v[21])}" stroke-width="{rim:.6f}"/></svg>')
    def valid(v):
        return (np.isfinite(v).all() and np.max(abs(v[:4]-p[:4])) < 2
                and v[2] > v[0] and v[3] > v[1] and .2 < v[4] < 3
                and x+panel_width*.2 < v[5] < x+panel_width*.8 and v[6] < v[7] and v[9] > v[10]
                and 1 < min(v[8],v[11]) and max(v[8],v[11]) < panel_width*.23
                and .4 < v[12] < v[11]*.6 and abs(v[13]-cx) < 3 and abs(v[14]-cy) < 4
                and rx*.8 < v[15] < rx*1.2 and ry*.8 < v[16] < ry*1.2 and .4 < v[17] < 4
                and np.all((v[18:] >= 0) & (v[18:] <= 255)))
    detail_regions = [observed['diamond_distance'] < 2.5]
    detail_regions += [(a[3] < a[2]/2+1) & (yy > y+panel_height*.1) & (yy < bottom-panel_height*.1)
                       & (xx > x) & (xx < right) for a in axes]
    def details(rendered):
        error = ((arr.astype(float)-rendered.astype(float))**2).mean(axis=2)/255**2
        errors = [float(error[region].mean()) for region in detail_regions]
        return dict(diamond_mse=errors[0],diagonal_mse=errors[1:],passed=max(errors) < .004)
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
                      and observe_hollow_cross(result['rendered']) is not None) else None


def validate_hollow_cross_panel(svg):
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
    if raster is None or observe_hollow_cross(raster) is None:
        raise ValueError('hollow_cross_panel:missing_diamond_or_diagonal_cutout')
