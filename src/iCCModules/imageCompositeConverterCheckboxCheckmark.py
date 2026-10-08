"""Fit a framed checkbox and a filled two-leg checkmark from observed pixels."""
from __future__ import annotations

import cv2
import numpy as np


def fit_checkbox_checkmark(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not ('haken' in text and any(t in text for t in ('checkbox','kästchen','kaestchen'))
            and 'verlauf' in text and 'rand' in text):
        return None
    if any(t in text for t in ('kreis','text','beschrift','zusätzlich','weitere','nach links oben','horizontal')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height,width,3) or min(width,height) < 12:
        return None
    values = arr.astype(float)
    chroma = values[:,:,1]-np.maximum(values[:,:,0],values[:,:,2])
    green = chroma > 25
    count,labels,stats,_ = cv2.connectedComponentsWithStats(green.astype(np.uint8))
    if count < 2:
        return None
    component = 1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
    if stats[1:,cv2.CC_STAT_AREA].sum()-stats[component,cv2.CC_STAT_AREA] > max(3,stats[component,cv2.CC_STAT_AREA]*.02):
        return None
    green = labels == component
    ys,xs = np.nonzero(green)
    if len(xs) < 15 or np.ptp(xs) < width*.35 or np.ptp(ys) < height*.35:
        return None
    columns = np.unique(xs)
    centers = np.array([np.average(np.flatnonzero(green[:,x])+.5,weights=chroma[green[:,x],x]) for x in columns])
    xc = columns+.5
    best_lines = None
    for split in range(3,len(columns)-3):
        left,right = np.polyfit(xc[:split],centers[:split],1),np.polyfit(xc[split:],centers[split:],1)
        if not (.2 < left[0] < 3 and -4 < right[0] < -.4):
            continue
        joint = (right[1]-left[1])/(left[0]-right[0])
        if not xc[1] < joint < xc[-2]:
            continue
        residual = np.sum((np.polyval(left,xc[:split])-centers[:split])**2)+np.sum((np.polyval(right,xc[split:])-centers[split:])**2)
        if best_lines is None or residual < best_lines[0]:
            best_lines = residual,left,right,joint
    if best_lines is None:
        return None
    _,left,right,joint = best_lines
    a = np.array([xc[0],np.polyval(left,xc[0])])
    c = np.array([joint,np.polyval(left,joint)])
    b = np.array([xc[-1],np.polyval(right,xc[-1])])
    if np.linalg.norm(b-c) < np.linalg.norm(c-a)*1.3:
        return None
    # Three exposed straight sides provide an occluded square's bounds.
    rows = np.indices(green.shape)[0]
    neutral = ((np.ptp(values,axis=2) < 18) & (np.mean(values,axis=2) < 190)
               & (rows >= c[1]-height*.08))
    count,labels,stats,_ = cv2.connectedComponentsWithStats(neutral.astype(np.uint8))
    if count < 2:
        return None
    component = 1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
    x,y,w,h,area = stats[component].astype(float)
    if min(w,h) < min(width,height)*.25 or not .65 < w/h < 2.1:
        return None
    region = labels == component
    # Require support on both vertical sides and along the bottom; dark
    # checkmark outlines alone cannot stand in for a checkbox.
    if (region[int(y):int(y+h),int(x)].sum() < h*.3
            or region[int(y):int(y+h),int(x+w-1)].sum() < h*.3
            or region[int(y+h-1),int(x):int(x+w)].sum() < w*.65):
        return None
    bottom = y+h-.5
    y = bottom-(w-1)
    interior = values[max(0,int(y)+2):int(bottom)-1,int(x)+2:int(x+w)-2]
    if interior.size == 0 or np.count_nonzero(np.min(interior,axis=2) > 230) < interior.shape[0]*interior.shape[1]*.08:
        return None
    frame_color = np.median(values[region],axis=0)
    profile = []
    for lo,hi in ((0,.3),(.3,.7),(.7,1.01)):
        q = green & ((rows-ys.min())/max(1,np.ptp(ys)) >= lo) & ((rows-ys.min())/max(1,np.ptp(ys)) < hi)
        profile.append(np.median(values[q],axis=0) if q.any() else np.median(values[green],axis=0))
    # The ribbon has six vertices: two caps, one concave join and one outer
    # join. All vertices derive from the two fitted axes and their thicknesses.
    length = np.linalg.norm(c-a)+np.linalg.norm(b-c)
    thickness = max(1.,len(xs)/length)
    p = [x+.5,y,w-1,w-1,1.,*a,*c,*b,thickness,thickness,1.,*frame_color,*profile[0],*profile[1],*profile[2]]
    gy0,gy1 = float(ys.min()),float(ys.max()+1)

    def ribbon(v):
        a,c,b = np.array(v[5:7]),np.array(v[7:9]),np.array(v[9:11])
        u,z = c-a,b-c
        n = np.array([u[1],-u[0]])/np.linalg.norm(u)*v[11]/2
        m = np.array([z[1],-z[0]])/np.linalg.norm(z)*v[12]/2
        t = np.linalg.solve(np.column_stack((u,-z)),m-n)[0]
        inner = c+n+t*u
        outer = c-n-t*u
        return np.array([a+n,inner,b+m,b-m,outer,a-n])

    def color(v):
        return '#'+''.join(f'{int(round(c)):02x}' for c in np.clip(v[::-1],0,255))

    def svg(v):
        points = ribbon(v)
        stops = ''.join(f'<stop offset="{off}" stop-color="{color(v[start:start+3])}"/>' for off,start in ((0,17),(.5,20),(1,23)))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<defs><linearGradient id="check_fill" gradientUnits="userSpaceOnUse" x1="0" x2="0" y1="{gy0}" y2="{gy1}">{stops}</linearGradient></defs>'
                f'<rect x="{v[0]:.6f}" y="{v[1]:.6f}" width="{v[2]:.6f}" height="{v[3]:.6f}" fill="#ffffff" stroke="{color(v[14:17])}" stroke-width="{v[4]:.6f}"/>'
                f'<polygon points="'+ ' '.join(f'{a:.6f},{b:.6f}' for a,b in points)+f'" fill="url(#check_fill)" stroke="{color(np.minimum(v[17:20],v[20:23])*.3)}" stroke-width="{v[13]:.6f}" stroke-linejoin="round"/></svg>\n')

    def valid(v):
        if not (min(v[2:4]) > 4 and .7 < v[2]/v[3] < 1.3 and .2 < v[4] < min(v[2:4])*.3
                and v[5] < v[7] < v[9] and v[6] < v[8] and v[10] < v[8]
                and .5 < min(v[11:13]) <= max(v[11:13]) < min(width,height)*.35 and .2 < v[13] < min(v[11:13])):
            return False
        q = ribbon(v)
        d = np.roll(q,-1,axis=0)-q
        cross = d[:,0]*np.roll(d,-1,axis=0)[:,1]-d[:,1]*np.roll(d,-1,axis=0)[:,0]
        return (np.count_nonzero(cross > 0) == 5 and np.count_nonzero(cross < 0) == 1
                and v[0] < q[4,0] < v[0]+v[2] and v[1] < q[4,1] < v[1]+v[3]
                and min(q[2,1],q[3,1]) < v[1])

    evaluations,cache = 0,{}

    def measure(v):
        nonlocal evaluations
        if not valid(v):
            return None
        content = svg(v)
        if content in cache:
            return cache[content]
        evaluations += 1
        raster = render_fn(content,width,height)
        if raster is None:
            return None
        error = float(error_fn(image,raster))
        # Optimize squared RGB error so large contour/color errors cannot be
        # hidden by the CLI's absolute-error objective. Preserve that external
        # objective for the returned error and the strict acceptance check.
        score = float(np.square(values-raster.astype(float)).mean())
        result = (score,content,raster,error) if np.isfinite(error) else None
        if len(cache) >= 128:
            cache.clear()
        cache[content] = result
        return result

    best = measure(p)
    if best is None:
        return None
    initial_error = best[3]
    for step in (1.,.5,.25,.125):
        for _ in range(2):
            for index in range(len(p)):
                for sign in (-1,1):
                    trial = p.copy()
                    trial[index] += sign*step*(12 if index >= 14 else 1)
                    measured = measure(trial)
                    if measured is not None and measured[0] < best[0]-1e-9:
                        p,best = trial,measured
    # A finite, constant objective supplies no evidence of successful fitting.
    if best[3] >= initial_error-1e-9:
        return None
    residual = np.max(np.abs(values-best[2].astype(float)),axis=2) > 65
    if residual.mean() > .04:
        return None
    foreground = np.min(values,axis=2) < 210
    output_mask = np.min(best[2],axis=2) < 210
    covered = cv2.dilate(output_mask.astype(np.uint8),np.ones((3,3),np.uint8)) > 0
    if np.count_nonzero(foreground & ~covered) > max(3,foreground.sum()*.03):
        return None
    return {'svg':best[1],'rendered':best[2],'error':best[3],'initial_error':initial_error,
            'parameters':p,'evaluations':evaluations,'source':'raster_checkbox_checkmark_v1'}
