"""Observe a framed grayscale highlight, two complete diagonals and a minus.

The description selects the structure; pixels determine geometry and paint.
Only bounded native primitives and a three-stop gradient are emitted.
"""
from __future__ import annotations

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description
from src.iCCModules.imageCompositeConverterFilledSymbols import _register


def _description_parts(description):
    text = ' '.join(normalize_description(description).casefold().split())
    plus = bool(re.search(r'\bplus(?:zeichen)?\b|\+',text))
    minus = bool(re.search(r'\bminus(?:zeichen)?\b|["„]\s*[-−]\s*["“]|(?<!\w)[-−]\s*zeichen\b',text))
    stacked = plus and minus and bool(re.search(r'\bdarunter\b|\buntereinander\b',text))
    crossed = ('kreuz' in text or bool(re.search(r'\b(?:zwei|beide[nr]?|2)\s+(?:\w+\s+){0,3}diagonalen\b',text))
               or (stacked and 'diagonalen' in text))
    return text,plus,minus,stacked,crossed


def crossed_panel_contract(description,*,stacked_marks=False):
    text,plus,minus,stacked,crossed = _description_parts(description)
    return bool(crossed and minus and (not stacked_marks or stacked)
            and all(t in text for t in ('grau','rechteck','diagonal','horizontal','verlauf'))
            and any(t in text for t in ('rand','umrandung','rahmen'))
            and any(t in text for t in ('abgeschnitten','beschnitten','begrenzt'))
            and not any(t in text for t in ('kreis','ohne minus','kein minus','ohne kreuz','vertikaler farbverlauf')))


def _observe_marks(gray, darkness, region, axes, panel_width, stacked, plus):
    # At small sizes antialiasing can join a minus to a diagonal, or bridge
    # the one-pixel gap below a plus. Remove observed diagonal support and try
    # bounded contrast levels; every candidate still needs a complete cross
    # and a distinct horizontal mark before the native render is fitted.
    for threshold in ((45,65,85) if stacked else (45,)):
        mark = region & (darkness > threshold)
        if stacked:
            for axis in axes:
                mark &= axis[4] > axis[2]*.65
        count,labels,stats,_ = cv2.connectedComponentsWithStats(mark.astype('uint8'))
        # A one-pixel-high minus may occupy two antialiased rows. The stacked
        # pair permits one pixel of bounding-box quantization, not a lower
        # final quality threshold or a missing/filled-in plus.
        eligible = sorted((i for i in range(1,count)
                           if stats[i,cv2.CC_STAT_WIDTH] >= 2.5*stats[i,cv2.CC_STAT_HEIGHT]-(1 if stacked else 0)),
                          key=lambda i:stats[i,cv2.CC_STAT_AREA],reverse=True)
        for i in eligible:
            mx,my,mw,mh,area = stats[i]
            if mw < panel_width*.12 or area < mw*mh*.6:
                continue
            shade = float(np.percentile(gray[labels==i],10))
            if not plus:
                return (mx,my,mw,mh),shade,[],None
            if not stacked:
                continue
            candidates = [j for j in range(1,count) if j != i
                          and .65 < stats[j,cv2.CC_STAT_WIDTH]/max(1,stats[j,cv2.CC_STAT_HEIGHT]) < 1.5
                          and stats[j,cv2.CC_STAT_TOP]+stats[j,cv2.CC_STAT_HEIGHT] < my
                          and abs(stats[j,cv2.CC_STAT_LEFT]+stats[j,cv2.CC_STAT_WIDTH]/2-(mx+mw/2)) < panel_width*.1]
            for j in sorted(candidates,key=lambda j:stats[j,cv2.CC_STAT_AREA],reverse=True):
                px,py,pw,ph,_ = stats[j]
                support = labels[py:py+ph,px:px+pw] == j
                hs = int((support.sum(axis=1) >= pw*.7).sum())
                vs = int((support.sum(axis=0) >= ph*.7).sum())
                if pw >= 4 and ph >= 4 and 0 < hs < ph*.6 and 0 < vs < pw*.6:
                    return ((mx,my,mw,mh),shade,
                            [float(v) for v in (px,py,pw,ph,hs,vs)],
                            float(np.percentile(gray[labels==j],10)))
    return None


def fit_crossed_gradient_panel(width, height, *, description, image, render_fn, error_fn):
    text,plus,minus,stacked,crossed = _description_parts(description)
    if not crossed_panel_contract(description):
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
    inset = min(1.25,max(.5,w*.03)) if stacked else 1.25
    left,top,right,bottom = x+inset,y+inset,x+w-inset,y+h-inset
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
    sample_rows = np.flatnonzero(((yy[:,0] > top+h*(.3 if stacked else .2)) & (yy[:,0] < top+h*(.42 if stacked else .37)))
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
    # Observe distinct marks above the crossing; wording selects their relation,
    # while connected raster support determines their positions and sizes.
    region = ((xx > left+w*.25) & (xx < left+w*.75) & (yy > top+h*.03)
              & (yy < top+h*(.3 if stacked else .2)))
    marks = _observe_marks(gray,darkness,region,axes,w,stacked,plus)
    if marks is None:
        return None
    (mx,my,mw,mh),minus_shade,plus_geometry,plus_shade = marks
    if plus:
        px,py,pw,ph,_,_ = map(int,plus_geometry)
    rim = float(np.percentile(np.concatenate((gray[y:y+h,x+1],gray[y:y+h,x+w-2],
                                            gray[y+1,x:x+w],gray[y+h-2,x:x+w])),15))
    rim_width = min(1.2,max(.6,w*.03)) if stacked else 1.2
    p = [left,top,right,bottom,rim_width,peak,
         *axes[0][:3],*axes[1][:3],float(mx),float(my),float(mw),float(mh),
         *plus_geometry,*paint,rim,axes[0][3],axes[1][3],minus_shade,
         *([plus_shade] if plus else [])]
    colors = 16+len(plus_geometry)

    def color(v):
        return '#'+f'{int(np.clip(round(v),0,255)):02x}'*3

    def build(v):
        l,t,r,b,sw,peak = v[:6]
        stops = ''.join(f'<stop offset="{offset:.7f}" stop-color="{color(c)}"/>'
                        for offset,c in zip((0,(peak-l)/(r-l),1),v[colors:colors+3]))
        lines = ''.join(f'<line x1="{v[k]:.6f}" y1="0" x2="{v[k+1]:.6f}" y2="{height}" '
                        f'stroke="{color(v[colors+4+i])}" stroke-width="{v[k+2]:.6f}"/>'
                        for i,k in enumerate((6,9)))
        if stacked:
            # Some SVG rasterizers ignore clipPath, even on individual lines.
            # Intersect each stroke's four corners with the panel explicitly;
            # the delivered native geometry must stay inside the frame too.
            lines = ''
            for i,k in enumerate((6,9)):
                dx = v[k+1]-v[k]
                nx,ny = height*v[k+2]/(2*np.hypot(dx,height)),-dx*v[k+2]/(2*np.hypot(dx,height))
                polygon = [(v[k]+nx,ny),(v[k]-nx,-ny),(v[k+1]-nx,height-ny),(v[k+1]+nx,height+ny)]
                for axis,bound,sign in ((0,l,1),(0,r,-1),(1,t,1),(1,b,-1)):
                    clipped = []
                    for start,end in zip(polygon,polygon[1:]+polygon[:1]):
                        inside_start,inside_end = sign*(start[axis]-bound)>=0,sign*(end[axis]-bound)>=0
                        if inside_start != inside_end:
                            fraction = (bound-start[axis])/(end[axis]-start[axis])
                            clipped.append(tuple(start[j]+fraction*(end[j]-start[j]) for j in (0,1)))
                        if inside_end:
                            clipped.append(end)
                    polygon = clipped
                points = ' '.join(f'{x:.6f},{y:.6f}' for x,y in polygon)
                lines += f'<polygon points="{points}" fill="{color(v[colors+4+i])}"/>'
        glyph = ''
        if plus:
            px,py,pw,ph,hs,vs = v[16:22]
            glyph = (f'<rect x="{px:.6f}" y="{py+(ph-hs)/2:.6f}" width="{pw:.6f}" height="{hs:.6f}" fill="{color(v[colors+7])}"/>'
                     f'<rect x="{px+(pw-vs)/2:.6f}" y="{py:.6f}" width="{vs:.6f}" height="{ph:.6f}" fill="{color(v[colors+7])}"/>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="panelPaint" gradientUnits="userSpaceOnUse" x1="{l:.6f}" x2="{r:.6f}" y1="0" y2="0">'
                f'{stops}</linearGradient><clipPath id="panelClip"><rect x="{l:.6f}" y="{t:.6f}" '
                f'width="{r-l:.6f}" height="{b-t:.6f}"/></clipPath></defs>'
                f'<rect width="{width}" height="{height}" fill="white"/>'
                f'<rect x="{l:.6f}" y="{t:.6f}" width="{r-l:.6f}" height="{b-t:.6f}" fill="url(#panelPaint)"/>'
                f'<g clip-path="url(#panelClip)">{lines}<rect x="{v[12]:.6f}" y="{v[13]:.6f}" '
                f'width="{v[14]:.6f}" height="{v[15]:.6f}" fill="{color(v[colors+6])}"/>{glyph}</g>'
                f'<rect x="{l:.6f}" y="{t:.6f}" width="{r-l:.6f}" height="{b-t:.6f}" fill="none" '
                f'stroke="{color(v[colors+3])}" stroke-width="{sw:.6f}"/></svg>')

    def valid(v):
        l,t,r,b,sw,peak = v[:6]
        if not (np.isfinite(v).all() and np.max(abs(v[:4]-p[:4])) < max(2,w*.08)
                and r-l > w*.7 and b-t > h*.7 and .4 < sw < w*.12
                and l+(r-l)*.2 < peak < l+(r-l)*(.5 if left_peak else .8)
                and v[6] < v[7] and v[9] > v[10] and .5 < min(v[8],v[11]) and max(v[8],v[11]) < w*.2
                and abs(v[6]-l) < w*.15 and abs(v[7]-r) < w*.15
                and abs(v[9]-r) < w*.15 and abs(v[10]-l) < w*.15
                and l+(r-l)*.25 < v[12]+v[14]/2 < l+(r-l)*.75
                and t < v[13] < t+(b-t)*(.3 if stacked else .2) and .1*w < v[14] < .4*w and .5 < v[15] < h*.07
                and np.all((v[colors:] >= 0) & (v[colors:] <= 255))
                and min(v[colors],v[colors+2]) > v[colors+3]+8 and v[colors+1] > max(v[colors],v[colors+2])+12):
            return False
        if plus:
            px,py,pw,ph,hs,vs = v[16:22]
            if not (l < px < r-pw and t < py < v[13]-ph and .12*w < pw < .4*w
                    and .65 < pw/ph < 1.5 and .5 < hs < ph*.6 and .5 < vs < pw*.6
                    and abs(px+pw/2-(v[12]+v[14]/2)) < w*.08):
                return False
        return max(v[colors+4:]) < min(v[colors],v[colors+2])-20

    def details(rendered):
        error = ((pixels-rendered.astype(float))**2).mean(axis=2)/255**2
        minus_error = float(error[max(0,my-1):min(height,my+mh+1),max(0,mx-1):min(width,mx+mw+1)].mean())
        diagonal_errors = [float(error[(a[4] < 2.5) & (yy>top+h*.15) & (yy<top+h*.85)].mean()) for a in axes]
        actual = np.percentile(rendered[y+3:y+h-3,x:x+w].mean(axis=2),75,axis=0)
        profile_error = float(np.percentile(abs(actual[3:-3]-profile[3:-3]),95))
        plus_error = float(error[max(0,py-1):min(height,py+ph+1),max(0,px-1):min(width,px+pw+1)].mean()) if plus else 0.
        return dict(minus_mse=minus_error,plus_mse=plus_error,diagonal_mse=diagonal_errors,profile_error_p95=profile_error,
                    passed=bool(minus_error < .02 and plus_error < .02 and max(diagonal_errors) < .02 and profile_error <= 8))

    result = _register(p,colors,build,valid,arr,render_fn,error_fn,'raster_crossed_gradient_panel_v1',
                       satisfactory_fn=lambda p,m: details(m[3])['passed'],
                       refinement_steps=(1.,.5,.25,.125,.0625))
    if result is None:
        return None
    result['details'] = details(result['rendered'])
    result['quality'] = pixel_quality(arr,result['rendered'])
    return result if result['details']['passed'] and result['quality']['passed'] else None
