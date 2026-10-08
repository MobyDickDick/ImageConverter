"""Register a described upright bell and four sound arcs from raster evidence."""
from __future__ import annotations

import re

import cv2
import numpy as np


def _wave_estimates(signal, cx, top, waist, radius, threshold):
    """Regress two separate ridges per side; pixels never become path vertices."""
    height, width = signal.shape
    groups = [[], [], [], []]
    samples = []
    for y in range(min(height, int(height*.45))):
        columns = np.arange(width)
        fraction = np.clip((y+.5-top)/max(1,waist-top),0,1)
        dome_r = radius*np.sqrt(max(0,1-(1-fraction)**2))
        boundary = max(radius*.2,dome_r)+.5
        active = np.flatnonzero((signal[y]>threshold) & (abs(columns+.5-cx)>boundary))
        for x in active:
            samples.append((x+.5,y+.5,float(signal[y,x])))
    if len(samples)<12:
        return None
    points = np.asarray(samples)
    distances = np.hypot(points[:,0]-cx,points[:,1]-waist)
    centers = np.percentile(distances,[25,75])
    for _ in range(8):
        labels = np.argmin(abs(distances[:,None]-centers),axis=1)
        if len(set(labels))!=2:
            return None
        centers = np.array([np.average(distances[labels==i],weights=points[labels==i,2]) for i in (0,1)])
    if abs(centers[1]-centers[0])<max(1,width*.04):
        return None
    outer = int(np.argmax(centers))
    for side in (0,1):
        for index, label in enumerate((outer,1-outer)):
            selected = points[(labels==label) & ((points[:,0]<cx) if side==0 else (points[:,0]>cx))]
            for y in np.unique(selected[:,1]):
                row = selected[selected[:,1]==y]
                groups[side*2+index].append((np.average(row[:,0],weights=row[:,2]),y))
    result = []
    for group in groups:
        if len(group) < 3:
            return None
        points = np.asarray(group)
        # The arcs have monotonic horizontal travel and measurable curvature.
        coefficients = np.polyfit(points[:, 1], points[:, 0], 2)
        lo, hi = points[:, 1].min(), points[:, 1].max()
        if hi-lo < height*.12:
            return None
        start, end = np.polyval(coefficients, [lo, hi])
        mid = float(np.polyval(coefficients, (lo+hi)/2))
        control = 2*mid-(start+end)/2
        result.extend((start, lo, control, (lo+hi)/2, end, hi))
    return result


def bell_svg(width, height, p, *, neutral=False, omit=None):
    """Native compact vectors with geometric parameters in pixels, colors in BGR."""
    cx, top, shoulder, radius, waist, waist_r, lip_y, lip_rx, lip_ry, stroke = p[:10]
    kx, ky, krx, kry = p[10:14]
    shades = np.clip(np.rint(p[14:23].reshape(3, 3)), 0, 255).astype(int)
    contour = _color(p[23:26])
    wave_color, wave_width = _color(p[26:29]), p[29]
    clapper_color = '#ffffff' if neutral else _color(p[30:33])
    clapper_stroke = p[33]
    arcs = p[34:].reshape(4, 6)
    stops = ''.join(f'<stop offset="{i/2:g}" stop-color="{_color(c)}"/>' for i, c in enumerate(shades))
    fill = '#ffffff' if neutral else 'url(#bell_shade)'
    body = (f'M {cx:g} {top:g} '
            f'C {cx-radius*.55:g} {top:g} {cx-radius:g} {top+(shoulder-top)*.4:g} {cx-radius:g} {shoulder:g} '
            f'C {cx-radius:g} {waist:g} {cx-waist_r:g} {waist:g} {cx-lip_rx:g} {lip_y:g} '
            f'L {cx+lip_rx:g} {lip_y:g} '
            f'C {cx+waist_r:g} {waist:g} {cx+radius:g} {waist:g} {cx+radius:g} {shoulder:g} '
            f'C {cx+radius:g} {top+(shoulder-top)*.4:g} {cx+radius*.55:g} {top:g} {cx:g} {top:g} Z')
    wave_paths = ''.join(f'<path data-role="wave_{i}" d="M {a:g} {b:g} Q {c:g} {d:g} {e:g} {f:g}" '
                         f'fill="none" stroke="{wave_color}" stroke-width="{wave_width:g}"/>'
                         for i, (a,b,c,d,e,f) in enumerate(arcs) if omit != f'wave_{i}')
    clapper = (f'<ellipse data-role="clapper" cx="{kx:g}" cy="{ky:g}" rx="{krx:g}" ry="{kry:g}" '
               f'fill="{clapper_color}" stroke="{contour if neutral else clapper_color}" stroke-width="{clapper_stroke:g}"/>') if omit != 'clapper' else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<defs><linearGradient id="bell_shade" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient></defs>'
            f'<path data-role="bell_body" d="{body}" fill="{fill}" stroke="{contour}" stroke-width="{stroke:g}"/>'
            f'<ellipse data-role="bell_rim" cx="{cx:g}" cy="{lip_y:g}" rx="{lip_rx:g}" ry="{lip_ry:g}" '
            f'fill="{fill if neutral else _color(shades[-1])}" stroke="{contour}" stroke-width="{stroke:g}"/>'
            +clapper+wave_paths+'</svg>\n')


def _color(color):
    return '#'+''.join(f'{int(v):02x}' for v in np.clip(np.rint(color), 0, 255)[::-1])


def fit_alarm_bell(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(t in text for t in ('glocke', 'klöppel', 'schall', 'zwei', 'oval', 'aufrecht')):
        return None
    if any(t in text for t in ('drei', 'zusätzlich', 'schriftzug', 'horizontaler verlauf', 'umgekehrt', 'dreieck', 'quadrat')):
        return None
    if re.search(r'(?:ohne|kein\w*)\s+(?:klöppel|schall|glocke)', text):
        return None
    neutral = 'ungefüllt' in text
    if not neutral and not ('vertikal' in text and 'verlauf' in text):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height)<16 or not np.isfinite(arr).all():
        return None
    pixels = arr.astype(float)
    signal = 255-np.min(pixels, axis=2)
    yy, xx = np.indices((height, width))
    lower = (yy>height*.45) & (signal>35)
    ys, xs = np.nonzero(lower)
    if len(xs)<height:
        return None
    cx = float((xs.min()+xs.max()+1)/2)
    mid = int(np.median(ys[ys<height*.65])) if (ys<height*.65).any() else int(height*.5)
    cols = np.flatnonzero(signal[mid]>35)
    if len(cols)<2:
        return None
    radius = (cols[-1]-cols[0])/2
    if not width*.12<radius<width*.4:
        return None
    central = (abs(xx+.5-cx)<radius*.3) & (yy<mid) & (signal>45)
    ty, _ = np.nonzero(central)
    if not len(ty):
        return None
    top = float(ty.min())
    spans = []
    for row in range(int(height*.65), height):
        active = np.flatnonzero(signal[row]>35)
        spans.append(active[-1]-active[0]+1 if len(active) else 0)
    peak = int(height*.65)+int(np.argmax(spans))
    lip_rx = max(spans)/2-.3
    lip_ry = max(1.,ys.max()+.5-peak)
    lip_y = float(peak)
    if not (top<mid<lip_y and lip_rx>radius and lip_ry<height*.2):
        return None
    arcs = _wave_estimates(signal,cx,top,mid,radius,45 if neutral else 75)
    if arcs is None:
        return None
    # Estimate the clapper from a bright component against the colored opening.
    kx, ky, krx, kry = cx-lip_rx*.43, lip_y-lip_ry*.25, lip_rx*.2, lip_ry*.8
    if not neutral:
        bright = ((pixels.min(axis=2)>165) & (xx>cx-lip_rx*.8) & (xx<cx-lip_rx*.1)
                  & (yy>lip_y-lip_ry*1.5) & (yy<lip_y+lip_ry*.4))
        count, labels, stats, centers = cv2.connectedComponentsWithStats(bright.astype(np.uint8))
        if count<2:
            return None
        index = 1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
        bx,by,bw,bh,area = stats[index]
        if area<2 or bw>lip_rx*.9:
            return None
        kx,ky = centers[index]+.5
        krx,kry = max(.6,bw/2),max(.6,bh/2)
    shades = []
    for row in (top+(mid-top)*.5, mid, lip_y):
        region = (abs(yy-row)<max(1,height*.04)) & (abs(xx+.5-cx)<radius*.45)
        shades.extend(np.median(pixels[region],axis=0))
    if neutral:
        shades = [255.]*9
    elif np.mean(shades[:3]) <= np.mean(shades[-3:])+5:
        return None
    wave_region = (yy<mid) & (abs(xx+.5-cx)>radius*1.4) & (signal>65)
    if not wave_region.any():
        return None
    wave_color = np.percentile(pixels[wave_region],20,axis=0)
    contour = wave_color.copy()
    p = np.r_[cx, top, top+(mid-top)*.7, radius, mid, radius, lip_y, lip_rx, lip_ry,
              max(.4,width*.035), kx,ky,krx,kry,shades,contour,wave_color,
              max(.5,width*.045), [235.]*3, .25, arcs]
    evaluations = 0

    def measure(parameters, omit=None):
        nonlocal evaluations
        if not (0<=parameters[1]<parameters[2]<parameters[4]<parameters[6]<height
                and parameters[3]>1 and parameters[5]>1 and parameters[7]>parameters[3]
                and 0<parameters[8]<height*.2 and .15<parameters[9]<width*.12
                and parameters[0]-parameters[7]>=-.5 and parameters[0]+parameters[7]<=width+.5
                and parameters[6]+parameters[8]<=height+.5
                and parameters[0]-parameters[7]<parameters[10]<parameters[0]
                and parameters[6]-parameters[8]*1.6<parameters[11]<parameters[6]+parameters[8]
                and .4<parameters[12]<parameters[7]*.4 and .4<parameters[13]<parameters[8]*1.4
                and .15<parameters[29]<width*.12 and 0<=parameters[33]<width*.08):
            return None
        if not neutral and np.mean(parameters[14:17])<np.mean(parameters[20:23])+5:
            return None
        content = bell_svg(width,height,parameters,neutral=neutral,omit=omit)
        evaluations += 1
        raster = render_fn(content,width,height)
        if raster is None:
            return None
        error = float(error_fn(image,raster))
        # Thin neutral outlines need a foreground term: global RGB error alone
        # can favor a faint, displaced contour on mostly white rasters.
        ref_mask, out_mask = signal>45, np.min(raster,axis=2)<210
        union = (ref_mask|out_mask).sum()
        iou = float((ref_mask&out_mask).sum()/union) if union else 1.
        score = error*(1+2*(1-iou)) if neutral else error
        return (error,content,raster,score) if np.isfinite(error) else None

    best = measure(p)
    if best is None:
        return None
    initial_error = best[0]
    # Bounded coordinate search: at most 1746 probes, independent of file names.
    steps = (1.,.5,.25,.125,.0625)*3 if neutral else (1.,.5,.25,.125)
    for step in steps:
        for index in range(len(p)):
            if neutral and 14<=index<23:
                continue
            delta = step*(8 if 14<=index<29 or 30<=index<33 else max(1,width/30))
            for sign in (-1,1):
                trial = p.copy()
                trial[index] += sign*delta
                candidate = measure(trial)
                if candidate is not None and candidate[3]<best[3]-1e-9:
                    p,best = trial,candidate
    if best[0]>=initial_error-1e-9:
        return None
    # Extra isolated objects cannot be silently explained by the bell contract.
    support = cv2.dilate((np.min(best[2],axis=2)<210).astype(np.uint8),np.ones((3,3),np.uint8))>0
    unexplained = (signal>65) & ~support
    if unexplained.sum()>max(3,(signal>65).sum()*.03):
        return None
    # Each claimed mark must have independent image evidence: removing it must
    # worsen the same objective used by the actual converter.
    for role in ('clapper','wave_0','wave_1','wave_2','wave_3'):
        ablated = measure(p,omit=role)
        if ablated is None or ablated[0]<=best[0]+max(1e-9,abs(best[0])*.005):
            return None
    return {'svg':best[1],'rendered':best[2],'error':best[0],'initial_error':initial_error,
            'evaluations':evaluations,'parameters':p.tolist(),'source':'raster_alarm_bell_v1'}
