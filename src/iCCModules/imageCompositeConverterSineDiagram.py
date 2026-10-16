"""Register perpendicular axes and an analytic sinusoid from raster evidence."""
from __future__ import annotations

import cv2
import numpy as np


def fit_sine_diagram(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(word in text for word in ('sinus', 'achse', 'diagramm')):
        return None
    if any(word in text for word in ('zusätzlich', 'weitere kurve', 'pfeilspitzen vorhanden')):
        return None
    arr = np.asarray(image)
    if arr.shape != (height, width, 3) or min(width, height) < 12 or not np.isfinite(arr).all():
        return None
    data = arr.astype(float)
    chroma = np.ptp(data, axis=2)
    # Channel spread separates the colored trace from neutral axes and paper.
    weights = np.maximum(chroma-18, 0)**2
    mass = weights.sum(axis=0)
    cols = np.flatnonzero(mass > max(50, mass.max()*.045))
    if len(cols) < max(8, width*.45):
        return None
    xx = cols+.5
    yy = (weights[:, cols]*(np.arange(height)[:, None]+.5)).sum(axis=0)/mass[cols]
    span = float(xx[-1]-xx[0])
    trials = []
    for cycles in np.linspace(.65, 2.2, 240):
        k = cycles*2*np.pi/span
        basis = np.column_stack((np.ones_like(xx), np.sin(k*xx), np.cos(k*xx)))
        coeff = np.linalg.lstsq(basis, yy, rcond=None)[0]
        trials.append((float(np.mean((basis@coeff-yy)**2)), k, coeff))
    residual, k, (center, a, b) = min(trials, key=lambda item: item[0])
    amplitude = float(np.hypot(a,b))
    if residual > max(.7, height*.018)**2 or not max(1, height*.035) < amplitude < height*.4:
        return None
    neutral = (chroma < 35) & (data.mean(axis=2) < 190)
    dark = np.maximum(255-data.mean(axis=2),0)*neutral
    ax, by = int(np.argmax(dark.sum(axis=0))), int(np.argmax(dark.sum(axis=1)))
    vertical = np.flatnonzero(neutral[:, ax])
    horizontal = np.flatnonzero(neutral[by])
    if len(vertical) < height*.55 or len(horizontal) < width*.55 or ax > width*.3 or by < height*.65:
        return None
    if yy.max() >= by or yy.min() <= vertical[0]:
        return None
    # Estimate ink colors from cores; bounded rendering search recovers mixed
    # antialiased strokes without copying the observed pixels into vector paths.
    core = chroma > max(30, chroma.max()*.8)
    ink = np.percentile(data[core], 20, axis=0)
    rim = np.percentile(data[neutral], 10, axis=0)
    p = [ax+.5, float(vertical[0]), by+.5, float(horizontal[-1]+1),
         max(.4,float(dark.sum(axis=1).max()/255/len(horizontal))),
         float(cols[0]), float(cols[-1]+1), center, amplitude, k, float(np.arctan2(b,a)),
         max(.45,float(np.sum(chroma)/max(1,chroma.max())/span/1.4)), *ink, *rim]

    def color(values):
        return '#'+''.join(f'{int(round(v)):02x}' for v in np.clip(values[::-1],0,255))

    def svg(values):
        x, top, bottom, right, aw, left, end, cy, amp, freq, phase, sw = values[:12]
        def y(t): return cy+amp*np.sin(freq*t+phase)
        def dy(t): return amp*freq*np.cos(freq*t+phase)
        # Cubic Hermite intervals of at most a sixth turn are already well
        # below raster resolution here and keep this analytic model compact.
        segments = max(4, int(np.ceil((end-left)*freq/(np.pi/3))))
        points = np.linspace(left,end,segments+1)
        path = f'M {left:.6f} {y(left):.6f}'
        for lo, hi in zip(points,points[1:]):
            dt=(hi-lo)/3
            path += f' C {lo+dt:.6f} {y(lo)+dt*dy(lo):.6f} {hi-dt:.6f} {y(hi)-dt*dy(hi):.6f} {hi:.6f} {y(hi):.6f}'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<path d="M {x:.6f} {top:.6f} V {bottom:.6f} H {right:.6f}" fill="none" stroke="{color(values[15:18])}" stroke-width="{aw:.6f}"/>'
                f'<path d="{path}" fill="none" stroke="{color(values[12:15])}" stroke-width="{sw:.6f}" stroke-linecap="round"/></svg>\n')

    def measure(values):
        if not (values[0] < values[3] and values[1] < values[2] and
                min(values[4],values[8],values[11]) > .08 and values[9]>0 and values[5]<values[6]
                and .65*2*np.pi < (values[6]-values[5])*values[9] < 2.3*2*np.pi
                and values[1]<values[7]-values[8]<values[7]+values[8]<values[2]):
            return None
        content=svg(values)
        rendered=render_fn(content,width,height)
        if rendered is None: return None
        error=float(error_fn(image,rendered))
        if not np.isfinite(error) or error<0: return None
        return error,content,rendered

    best=measure(p)
    if best is None: return None
    initial_error, initial_svg, evaluations=best[0],best[1],1
    for step in (1.,.5,.25,.125):
        for _ in range(3):
            for index in range(len(p)):
                delta=step*(8 if index>=12 else (.02 if index==9 else (.08 if index==10 else 1)))
                for sign in (-1,1):
                    candidate=p.copy();candidate[index]+=sign*delta
                    measured=measure(candidate);evaluations+=1
                    if measured is not None and measured[0]<best[0]-1e-9:
                        p,best=candidate,measured
    observed=np.min(arr,axis=2)<210
    covered=cv2.dilate((np.min(best[2],axis=2)<225).astype(np.uint8),np.ones((3,3),np.uint8))>0
    if np.count_nonzero(observed & ~covered)>max(2,.025*np.count_nonzero(observed)):
        return None
    return dict(svg=best[1],rendered=best[2],error=best[0],initial_error=initial_error,
                initial_svg=initial_svg,parameters=p,evaluations=evaluations,source='raster_sine_diagram_v1')
