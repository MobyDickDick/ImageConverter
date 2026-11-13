"""Observe a framed grayscale highlight, two complete diagonals and a minus.

The description selects the structure; pixels determine geometry and paint.
Only bounded native primitives and a three-stop gradient are emitted.
"""
from __future__ import annotations

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterFilledSymbols import _register


def fit_crossed_gradient_panel(width, height, *, description, image, render_fn, error_fn):
    text = ' '.join(str(description or '').casefold().split())
    if not (all(t in text for t in ('grau', 'rechteck', 'kreuz', 'diagonal', 'minus', 'horizontal', 'verlauf'))
            and any(t in text for t in ('rand', 'umrandung', 'rahmen'))
            and any(t in text for t in ('abgeschnitten', 'begrenzt'))):
        return None
    if any(t in text for t in ('kreis', 'ohne minus', 'kein minus', 'ohne kreuz', 'vertikaler farbverlauf')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 16 or height <= width:
        return None
    pixels = arr.astype(float)
    if not np.isfinite(pixels).all() or np.percentile(np.ptp(pixels, axis=2), 95) > 12:
        return None
    gray = pixels.mean(axis=2)
    count, labels, stats, _ = cv2.connectedComponentsWithStats((gray < 245).astype('uint8'))
    if count < 2:
        return None
    index = 1+int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x,y,w,h,area = stats[index]
    if w < 14 or h < w*1.25 or area < w*h*.5:
        return None
    left,top,right,bottom = x+1.25,y+1.25,x+w-1.25,y+h-1.25
    profile = np.percentile(gray[y+3:y+h-3, x:x+w],75,axis=0)
    columns = np.arange(x+3,x+w-3)
    peak = float(x+3+np.argmax(profile[3:-3])+.5)
    left_peak = bool(re.search(r'(?:maximum|hellst\w*).*?links (?:der|von)',text))
    if left_peak and not left+w*.2 < peak < (left+right)/2:
        return None
    basis = np.column_stack([np.interp(columns+.5, [left,peak,right], np.eye(3)[i]) for i in range(3)])
    paint = np.clip(np.linalg.lstsq(basis,profile[3:-3],rcond=None)[0],0,255)
    field = np.interp(np.arange(width)+.5, [left,peak,right],paint)[None,:]
    darkness = field-gray
    yy,xx = np.indices(gray.shape,dtype=float)
    yy += .5
    xx += .5
    sample_rows = np.flatnonzero(((yy[:,0] > top+h*.2) & (yy[:,0] < top+h*.37))
                               | ((yy[:,0] > top+h*.63) & (yy[:,0] < top+h*.8)))
    axes = []
    for ascending in (False,True):
        observed_y,observed_x = [],[]
        for row in sample_rows:
            side = (yy[row,0] < (top+bottom)/2) != ascending
            support = ((xx[row] < (left+right)/2) if side else (xx[row] > (left+right)/2))
            support &= (xx[row] > left+2) & (xx[row] < right-2) & (darkness[row] > 30)
            if support.sum() < 1:
                continue
            weights = darkness[row,support]**2
            observed_y.append(row+.5)
            observed_x.append(float(np.average(xx[row,support],weights=weights)))
        if len(observed_x) < h*.22:
            return None
        slope,intercept = np.polyfit(observed_y,observed_x,1)
        if not (.12 < abs(slope) < 1.5) or (slope < 0) != ascending:
            return None
        if np.mean(abs(np.array(observed_x)-np.polyval([slope,intercept],observed_y))) > .8:
            return None
        distance = abs(xx-(slope*yy+intercept))/np.hypot(1,slope)
        # A shared dark crossing cannot substitute for either complete arm.
        # Reject a visibly interrupted source before fitting continuous lines.
        along = ((distance < 1.5) & (darkness > 30)).any(axis=1)
        central_rows = (yy[:,0] > top+h*.1) & (yy[:,0] < top+h*.9)
        if along[central_rows].mean() < .94:
            return None
        region = (distance < .7) & (yy > top+h*.2) & (yy < top+h*.8)
        shade = float(np.percentile(gray[region],15))
        axes.append((float(intercept),float(slope*height+intercept),max(1,w*.075),shade,distance))
    # Observe a separate short horizontal mark above the crossing.
    mark = ((xx > left+w*.25) & (xx < left+w*.75) & (yy > top+h*.03)
            & (yy < top+h*.2) & (darkness > 45))
    count,marks,mark_stats,_ = cv2.connectedComponentsWithStats(mark.astype('uint8'))
    if count < 2:
        return None
    i = 1+int(np.argmax(mark_stats[1:, cv2.CC_STAT_AREA]))
    mx,my,mw,mh,mark_area = mark_stats[i]
    if not (mw >= mh*2.5 and mw >= w*.12 and mark_area >= mw*mh*.7):
        return None
    minus_shade = float(np.percentile(gray[marks==i],10))
    rim = float(np.percentile(np.concatenate((gray[y:y+h,x+1],gray[y:y+h,x+w-2],
                                            gray[y+1,x:x+w],gray[y+h-2,x:x+w])),15))
    p = [left,top,right,bottom,1.2,peak,
         *axes[0][:3],*axes[1][:3],float(mx),float(my),float(mw),float(mh),
         *paint,rim,axes[0][3],axes[1][3],minus_shade]

    def color(v):
        return '#'+f'{int(np.clip(round(v),0,255)):02x}'*3

    def build(v):
        l,t,r,b,sw,peak = v[:6]
        stops = ''.join(f'<stop offset="{offset:.7f}" stop-color="{color(c)}"/>'
                        for offset,c in zip((0,(peak-l)/(r-l),1),v[16:19]))
        lines = ''.join(f'<line x1="{v[k]:.6f}" y1="0" x2="{v[k+1]:.6f}" y2="{height}" '
                        f'stroke="{color(v[20+i])}" stroke-width="{v[k+2]:.6f}"/>'
                        for i,k in enumerate((6,9)))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="panelPaint" gradientUnits="userSpaceOnUse" x1="{l:.6f}" x2="{r:.6f}" y1="0" y2="0">'
                f'{stops}</linearGradient><clipPath id="panelClip"><rect x="{l:.6f}" y="{t:.6f}" '
                f'width="{r-l:.6f}" height="{b-t:.6f}"/></clipPath></defs>'
                f'<rect width="{width}" height="{height}" fill="white"/>'
                f'<rect x="{l:.6f}" y="{t:.6f}" width="{r-l:.6f}" height="{b-t:.6f}" fill="url(#panelPaint)"/>'
                f'<g clip-path="url(#panelClip)">{lines}<rect x="{v[12]:.6f}" y="{v[13]:.6f}" '
                f'width="{v[14]:.6f}" height="{v[15]:.6f}" fill="{color(v[22])}"/></g>'
                f'<rect x="{l:.6f}" y="{t:.6f}" width="{r-l:.6f}" height="{b-t:.6f}" fill="none" '
                f'stroke="{color(v[19])}" stroke-width="{sw:.6f}"/></svg>')

    def valid(v):
        l,t,r,b,sw,peak = v[:6]
        if not (np.isfinite(v).all() and np.max(abs(v[:4]-p[:4])) < max(2,w*.08)
                and r-l > w*.7 and b-t > h*.7 and .4 < sw < w*.12
                and l+(r-l)*.2 < peak < l+(r-l)*(.5 if left_peak else .8)
                and v[6] < v[7] and v[9] > v[10] and .5 < min(v[8],v[11]) and max(v[8],v[11]) < w*.2
                and abs(v[6]-l) < w*.15 and abs(v[7]-r) < w*.15
                and abs(v[9]-r) < w*.15 and abs(v[10]-l) < w*.15
                and l+(r-l)*.25 < v[12]+v[14]/2 < l+(r-l)*.75
                and t < v[13] < t+(b-t)*.2 and .1*w < v[14] < .4*w and .5 < v[15] < h*.07
                and np.all((v[16:] >= 0) & (v[16:] <= 255))
                and min(v[16],v[18]) > v[19]+8 and v[17] > max(v[16],v[18])+12):
            return False
        return max(v[20:]) < min(v[16],v[18])-20

    def details(rendered):
        error = ((pixels-rendered.astype(float))**2).mean(axis=2)/255**2
        minus_error = float(error[max(0,my-1):min(height,my+mh+1),max(0,mx-1):min(width,mx+mw+1)].mean())
        diagonal_errors = [float(error[(a[4] < 2.5) & (yy>top+h*.15) & (yy<top+h*.85)].mean()) for a in axes]
        actual = np.percentile(rendered[y+3:y+h-3,x:x+w].mean(axis=2),75,axis=0)
        profile_error = float(np.percentile(abs(actual[3:-3]-profile[3:-3]),95))
        return dict(minus_mse=minus_error,diagonal_mse=diagonal_errors,profile_error_p95=profile_error,
                    passed=bool(minus_error < .02 and max(diagonal_errors) < .02 and profile_error <= 8))

    result = _register(p,16,build,valid,arr,render_fn,error_fn,'raster_crossed_gradient_panel_v1',
                       satisfactory_fn=lambda p,m: details(m[3])['passed'],
                       refinement_steps=(1.,.5,.25,.125,.0625))
    if result is None:
        return None
    result['details'] = details(result['rendered'])
    result['quality'] = pixel_quality(arr,result['rendered'])
    return result if result['details']['passed'] and result['quality']['passed'] else None
