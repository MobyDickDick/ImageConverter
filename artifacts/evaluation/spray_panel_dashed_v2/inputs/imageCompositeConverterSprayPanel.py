"""Fit an explicitly decomposed humidifier from pixels, without vector samples.

The panel, rail, dashed frame, individual nozzles and individual three-ray
sprays retain separate parameters and local search objectives. No filename,
catalogue coordinates or stored SVG participates in detection or fitting.
"""
from __future__ import annotations

import time
import re
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality
from src.iCCModules.imageCompositeConverterSearchPortfolio import progress

SOURCE = 'raster_spray_panel_v1'


def spray_contract(description):
    text = str(description or '').casefold().replace('ue', 'ü')
    return (all(t in text for t in ('rechteck', 'balken', 'gestrichelt', 'düs', 'sprüh','horizontal','verlauf'))
            and not any(t in text for t in ('zickzack', 'andreaskreuz', 'kreis', 'vertikaler verlauf','durchgezogen'))
            and not re.search(r'\b(?:kein\w*|ohne)\s+(?:düs|sprüh|balken|farbverlauf|rahmen)',text))


def _runs(mask):
    indices = np.flatnonzero(mask)
    return np.split(indices, np.flatnonzero(np.diff(indices) > 1)+1) if len(indices) else []


def fit_spray_panel(width, height, *, description, image, render_fn, error_fn):
    if not spray_contract(description):
        return None
    arr = np.asarray(image)
    if (arr.shape != (height,width,3) or min(width,height) < 20 or max(width,height) > 512
            or not np.isfinite(arr).all() or np.max(np.ptp(arr.astype(float),axis=2)) > 12):
        return None
    pixels = arr.astype(float)
    gray = pixels.mean(axis=2)
    session = current_search()
    if session and session.time_reason():
        return None
    ys, xs = np.nonzero(gray < 235)
    if len(xs) < 50:
        return None
    x,y,X,Y = xs.min(),ys.min(),xs.max()+1,ys.max()+1
    w,h = X-x,Y-y
    if not h > w >= 20:
        return None
    scale = w/40.
    profile = np.median(gray[y+2:Y-2,x:X],axis=0)
    fill = np.percentile(gray[y+1:Y-1,x:X],98,axis=0)
    # Two independently observed right-hand troughs bound the dashed frame.
    troughs = [i for i in range(max(3,int(w*.35)),w-2)
               if profile[i] <= min(profile[i-1],profile[i+1]) and profile[i] < max(profile[i-1],profile[i+1])-8]
    trough_groups=[]
    for i in troughs:
        if trough_groups and i-trough_groups[-1][-1] <= 2:
            trough_groups[-1].append(i)
        else:
            trough_groups.append([i])
    if len(trough_groups) != 2:
        return None
    left,right = [int(np.mean(g)) for g in trough_groups]
    left_position,right_position = [x+float(np.mean(g))+.5 for g in trough_groups]
    if right-left < w*.15:
        return None
    rail = np.flatnonzero((fill-profile > 40) & (np.arange(w) > 0) & (np.arange(w) < w*.2))
    if len(rail) < 1 or np.any(np.diff(rail) != 1):
        return None
    rail_left,rail_right = x+rail[0],x+rail[-1]+1
    # Median samples on either side of the frame supply its underlying fill.
    for edge in (left,right):
        fill[edge] = (fill[edge-1]+fill[edge+1])/2
    top_profile = gray[y:Y,x+left+2:x+right-1].mean(axis=1)
    top = y+1+int(np.argmin(top_profile[1:max(3,h//5)]))
    bottom = Y-max(3,h//5)+int(np.argmin(top_profile[-max(3,h//5):-1]))
    if bottom-top < h*.6:
        return None
    rail_observations = gray[y:Y,int((rail_left+rail_right)/2)] < np.max(fill)-65
    rail_observations[:2] = rail_observations[-2:] = False
    rail_runs = _runs(rail_observations)
    rail_dark = max(rail_runs,key=len) if rail_runs else []
    if len(rail_dark) < h*.5:
        return None
    nozzle_start = int(rail_right)
    nozzle_end = min(x+left-3,nozzle_start+max(2,int(w*.08)))
    contrast = np.maximum(0,fill[None,:]-gray[y:Y,x:X])
    signal = contrast[:,nozzle_start-x:nozzle_end-x].mean(axis=1)
    groups = [r for r in _runs(signal > max(18,float(signal.max())*.35)) if r[0] > 1 and r[-1] < h-2]
    if not 3 <= len(groups) <= 12:
        return None
    nozzle_centers = [y+float(np.average(r+.5,weights=signal[r])) for r in groups]
    pitch = float(np.median(np.diff(nozzle_centers)))
    if pitch < 5*scale or np.max(abs(np.diff(nozzle_centers)-pitch)) > pitch*.25:
        return None
    spray_start = nozzle_end+max(1,int(scale))
    spray_end = x+left-max(2,int(scale*3))
    if spray_end-spray_start < 4:
        return None
    spray_signal = contrast[:,spray_start-x:spray_end-x].sum(axis=1)
    # Select long horizontal paint observations, then associate each with the
    # nearest nozzle. Three-ray geometry is not inferred from a zigzag path.
    centers=[]
    for cy in nozzle_centers:
        lo,hi=max(y+1,int(cy-pitch*.3)),min(Y-1,int(cy+pitch*.3)+1)
        center = lo+int(np.argmax(spray_signal[lo-y:hi-y]))+.5
        if centers and center-centers[-1] < pitch*.5:
            return None
        centers.append(center)
    peak = x+float(np.argmax(fill))+.5
    bg = [x+.5,y+.5,w-1.,h-1.,1.*scale,float(np.median(gray[[y,Y-1],x:X])),
          float(fill[1]),float(np.max(fill)),float(fill[-2]),peak-x-.5,scale]
    # A rail may continue into the bottom rim. Only extend an observed run,
    # never let the separate top/bottom border seed a full-height rail.
    rail_bottom = Y-1 if rail_dark[-1] >= h-3 else y+rail_dark[-1]+1
    rail_p = [float(rail_left),float(y+rail_dark[0]),float(rail_right-rail_left),
              float(rail_bottom-y-rail_dark[0]),float(np.median(profile[rail]))]
    frame = [left_position,top+.5,right_position-left_position,float(bottom-top),.7*scale,
             float(min(profile[left],profile[right])-25),1.*scale,1.*scale,0.]
    nozzles = [[cy,float(nozzle_end-rail_right),1.*scale,2.*scale,
                float(np.percentile(gray[int(cy):int(cy)+1,nozzle_start:nozzle_end],20))]
               for cy in nozzle_centers]
    sprays = [[float(spray_start),cy,float(spray_end-1),float(spray_end-spray_start-2),pitch*.4,
               float(spray_end-spray_start-2),pitch*.4,pitch*.12,.65*scale,175.]
              for cy in centers]

    def ink(value):
        n = int(round(np.clip(value,0,255)))
        return '#'+f'{n:02x}'*3

    def build():
        ox,oy,ow,oh,sw,shade,low,high,end,peak,plateau = bg
        peak = float(np.clip(peak,1,ow-1))
        stops = [(0,low),(max(0,(peak-plateau/2)/ow),high),
                 (min(1,(peak+plateau/2)/ow),high),(1,end)]
        content = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                   '<desc>Luftbefeuchter mit getrennt registriertem Gehäuse, Balken, gestricheltem Rahmen, Düsen und Sprühnebel.</desc>'
                   '<defs><linearGradient id="housing-fill" x1="0%" y1="0%" x2="100%" y2="0%">'
                   + ''.join(f'<stop offset="{o:.7f}" stop-color="{ink(c)}"/>' for o,c in stops)
                   + '</linearGradient></defs>'
                   +f'<g id="background"><rect x="{ox:.6f}" y="{oy:.6f}" width="{ow:.6f}" height="{oh:.6f}" fill="url(#housing-fill)" stroke="{ink(shade)}" stroke-width="{sw:.6f}"/></g>')
        rx,ry,rw,rh,shade = rail_p
        content += f'<g id="left-rail"><rect x="{rx:.6f}" y="{ry:.6f}" width="{rw:.6f}" height="{rh:.6f}" fill="{ink(shade)}"/></g>'
        fx,fy,fw,fh,sw,shade,dash,gap,offset = frame
        content += (f'<g id="dashed-frame"><rect x="{fx:.6f}" y="{fy:.6f}" width="{fw:.6f}" height="{fh:.6f}" fill="none" '
                    f'stroke="{ink(shade)}" stroke-width="{sw:.6f}" stroke-dasharray="{dash:.6f} {gap:.6f}" stroke-dashoffset="{offset:.6f}"/></g>')
        content += '<g id="nozzles">'
        for i,(cy,length,tip,shoulder,shade) in enumerate(nozzles):
            a,b,c = rx+rw,rx+rw+length*.35,rx+rw+length
            pts = [(a,cy-shoulder/2),(b,cy-tip/2),(c,cy-tip/2),(c,cy+tip/2),(b,cy+tip/2),(a,cy+shoulder/2)]
            content += f'<polygon id="nozzle-{i+1}" points="'+ ' '.join(f'{u:.6f},{v:.6f}' for u,v in pts)+f'" fill="{ink(shade)}"/>'
        content += '</g><g id="spray-mists">'
        for i,(ax,cy,bx,upper,rise,lower,fall,gap,sw,shade) in enumerate(sprays):
            content += f'<g id="spray-{i+1}" stroke="{ink(shade)}" stroke-width="{sw:.6f}" stroke-linecap="butt">'
            for a,b,c,d in [(ax,cy-gap,ax+upper,cy-rise),(ax,cy,bx,cy),(ax,cy+gap,ax+lower,cy+fall)]:
                content += f'<line x1="{a:.6f}" y1="{b:.6f}" x2="{c:.6f}" y2="{d:.6f}"/>'
            content += '</g>'
        return content+'</g></svg>'

    def valid():
        vectors = [bg,rail_p,frame,*nozzles,*sprays]
        if not all(np.isfinite(v).all() for v in vectors):
            return False
        if not (0 < bg[4] < 3*scale and bg[2] > w*.8 and bg[3] > h*.8 and 0 <= bg[10] <= w*.15):
            return False
        if not (0 < rail_p[2] < w*.15 and h*.5 < rail_p[3] <= h+2):
            return False
        if not (0 < frame[4] < 2*scale and .2*scale <= min(frame[6:8]) and max(frame[6:8]) < 5*scale):
            return False
        if not (x+w*.3 < frame[0] < frame[0]+frame[2] < X and y < frame[1] < frame[1]+frame[3] < Y):
            return False
        for cy,length,tip,shoulder,shade in nozzles:
            if not (y < cy < Y and .3*scale < length < w*.16 and .2*scale < tip <= shoulder < pitch*.4):
                return False
        for ax,cy,bx,upper,rise,lower,fall,gap,sw,shade in sprays:
            if not (rail_p[0]+rail_p[2] < ax < bx < frame[0]-scale and
                    2*scale < min(upper,lower) < max(upper,lower)+1 and
                    ax+max(upper,lower) < frame[0]-scale and
                    0 < gap < min(rise,fall) < max(rise,fall)+1 and
                    max(rise,fall) < pitch*.55 and .1*scale < sw < 2*scale):
                return False
        return all(0 <= v <= 255 for v in [*bg[5:9],rail_p[4],frame[5],*[n[4] for n in nozzles],*[s[9] for s in sprays]])

    evaluations = 0
    stages = []
    component_masks = {}
    cache = {}

    def measure(mask=None):
        nonlocal evaluations
        if not valid() or (session and session.time_reason()):
            return None
        content = build()
        if content in cache:
            raster = cache[content]
        else:
            raster = render_fn(content,width,height)
            evaluations += 1
            if session:
                session.evaluations += 1
            if raster is None:
                return None
            if len(cache) > 128:
                cache.clear()
            cache[content] = raster
        error = float(error_fn(arr,raster))
        if not np.isfinite(error):
            return None
        delta = np.square(pixels-raster.astype(float)).mean(axis=2)
        loss = float(delta[mask].mean() if mask is not None else delta.mean())
        return loss,error,content,raster

    initial = measure()
    if initial is None:
        return None

    def refine(name, vector, mask, factors, steps=(1.,.5,.25,.125,.0625)):
        component_masks[name] = mask
        begin = time.monotonic()
        count = evaluations
        best = measure(mask)
        if best is None:
            return False
        before = best[0]
        for step in steps:
            for _ in range(3):
                improved = False
                for index,factor in enumerate(factors):
                    if not factor:
                        continue
                    for sign in (-1,1):
                        previous = vector[index]
                        vector[index] += sign*step*factor
                        candidate = measure(mask)
                        if candidate is not None and candidate[0] < best[0]-1e-8:
                            best = candidate
                            improved = True
                        else:
                            vector[index] = previous
                        if session and session.time_reason():
                            stages.append(dict(component=name,completed=False,evaluations=evaluations-count))
                            return False
                if not improved:
                    break
        record = dict(component=name,completed=True,evaluations=evaluations-count,
                      seconds=round(time.monotonic()-begin,4),initial_local_mse=before,local_mse=best[0])
        stages.append(record)
        progress(SOURCE,event='component_fitted',**record)
        return True

    yy,xx = np.indices((height,width))
    clean = np.zeros((height,width),bool)
    clean[y:Y,x:X] = abs(gray[y:Y,x:X]-fill[None,:]) < 4
    clean[[y,Y-1],x:X] = True
    clean[y:Y,X-1] = True
    if not refine('background',bg,clean,[scale]*5+[8]*4+[scale,scale]):
        return None
    rail_mask = (xx >= rail_left-1)&(xx <= rail_right+1)&(yy >= y+rail_dark[0]-1)
    if not refine('left_rail',rail_p,rail_mask,[scale]*4+[8]):
        return None
    frame_mask = ((xx >= x+left-2)&(xx <= x+right+2)&(yy >= top-1)&(yy <= bottom+1)
                  & ((abs(xx+.5-(x+left+.5)) < 2*scale)
                     | (abs(xx+.5-(x+right+.5)) < 2*scale)
                     | (abs(yy+.5-(top+.5)) < 2*scale)
                     | (abs(yy+.5-(bottom+.5)) < 2*scale)))
    # Discrete dash hypotheses cross phase/period valleys before local search.
    best = measure(frame_mask)
    if best is None:
        return None
    saved = frame.copy()
    rows = np.arange(top+2,bottom-1)+.5
    observed = gray[top+2:bottom-1,x+left:x+left+1]
    observed = observed-observed.mean(axis=0)
    periods = np.linspace(max(2.01,1.8*scale),6*scale,800)
    def periodic_strength(period):
        design = np.c_[np.cos(rows*2*np.pi/period),np.sin(rows*2*np.pi/period),np.ones(len(rows))]
        coefficients = np.linalg.lstsq(design,observed,rcond=None)[0]
        return float(np.square(coefficients[:2]).sum())
    period = max(periods,key=periodic_strength)
    if periodic_strength(period) < 25:
        return None
    for duty in (.5,.65,.8):
        for phase in np.arange(16)/16:
            for shade in (100.,125.,150.):
                for stroke_width in (.7*scale,1.*scale):
                    frame[4:9] = [stroke_width,shade,period*duty,period*(1-duty),period*phase]
                    candidate=measure(frame_mask)
                    if candidate is not None and candidate[0] < best[0]:
                        best,saved = candidate,frame.copy()
    frame[:] = saved
    if not refine('dashed_frame',frame,frame_mask,[scale]*5+[8]+[0.,0.,scale],steps=(.25,.125,.0625,.03125)):
        return None
    for i,vector in enumerate(nozzles):
        mask = (xx >= rail_right-1)&(xx <= nozzle_end+1)&(abs(yy+.5-nozzle_centers[i]) < pitch*.25)
        if not refine(f'nozzle_{i+1}',vector,mask,[scale]*4+[8]):
            return None
    for i,vector in enumerate(sprays):
        mask = (xx >= spray_start-1)&(xx <= x+left-2)&(abs(yy+.5-centers[i]) <= pitch*.5)
        if not refine(f'spray_{i+1}',vector,mask,[scale]*9+[8]):
            return None
    final = measure()
    if final is None or final[1] >= initial[1]-1e-9:
        return None
    delta = np.square(pixels-final[3].astype(float)).mean(axis=2)/255**2
    details = [dict(component=name,normalized_mse=float(delta[mask].mean()),
                    passed=bool(delta[mask].mean() <= .002)) for name,mask in component_masks.items()]
    if not all(d['passed'] for d in details):
        return None
    return dict(svg=final[2],rendered=final[3],error=final[1],initial_error=initial[1],
                source=SOURCE,evaluations=evaluations,parameters=dict(background=bg,rail=rail_p,frame=frame,
                nozzles=nozzles,sprays=sprays),stages=stages,details=details,quality=pixel_quality(arr,final[3]))
