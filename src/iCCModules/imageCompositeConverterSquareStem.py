"""Register a plain square and its centered rightward handle from pixels."""
from __future__ import annotations

import copy
import math

import cv2
import numpy as np


def fit_square_stem(geometry_ir, *, image, render_fn, error_fn):
    if len(geometry_ir) != 1 or geometry_ir[0].get('kind') != 'RightStemSquareKelleGlyph':
        return None
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape[2] != 3 or not arr.size or not np.isfinite(arr).all():
        return None
    h, w = arr.shape[:2]
    mask = np.min(arr, axis=2) < 225
    columns = np.flatnonzero(mask.sum(axis=0) > h*.4)
    if len(columns) < 2:
        return None
    left, right = int(columns[0]), int(columns[-1])
    rows = np.flatnonzero(mask[:, left:right+1].sum(axis=1) > (right-left)*.6)
    if len(rows) < 2:
        return None
    top, bottom = int(rows[0]), int(rows[-1])
    if not .7 < (right-left)/(bottom-top) < 1.3 or right+3 >= w:
        return None
    outside = mask[:, right+2:]
    ys, xs = np.nonzero(outside)
    if not len(xs) or xs.max()-xs.min() < 2 or ys.max()-ys.min()+1 > (bottom-top)*.25:
        return None
    cy = float(np.mean(ys)+.5)
    if abs(cy-(top+bottom+1)/2) > (bottom-top)*.1:
        return None
    # A handle must cover one continuous horizontal interval. Extra disconnected
    # objects, interior marks and curved contours do not fit this topology.
    if cv2.connectedComponents(outside.astype(np.uint8))[0] != 2:
        return None
    margin = max(2, int((bottom-top)*.15))
    interior = arr[top+margin:bottom-margin+1, left+margin:right-margin+1]
    if not interior.size or float(np.std(interior.astype(float),axis=(0,1)).max()) > 18:
        return None
    allowed = np.zeros_like(mask)
    allowed[top:bottom+1, left:right+1] = True
    allowed[max(0,int(ys.min())):int(ys.max())+1, right+1:] = True
    if np.any(mask & ~allowed):
        return None
    fill = np.median(interior, axis=(0,1))
    border = np.percentile(np.concatenate((arr[top:top+2,left:right+1].reshape(-1,3),
                                          arr[bottom-1:bottom+1,left:right+1].reshape(-1,3),
                                          arr[top:bottom+1,left:left+2].reshape(-1,3),
                                          arr[top:bottom+1,right-1:right+1].reshape(-1,3))),15,axis=0)
    line = np.percentile(arr[:,right+2:][outside],10,axis=0)
    p = np.array([left+.5,top+.5,right-left,bottom-top,cy,
                  right+2+xs.max()+1.,1.,1.,*fill,*border,*line],dtype=float)
    evaluations = 0

    def color(values):
        return '#'+''.join(f'{int(v):02x}' for v in np.clip(np.rint(values),0,255)[::-1])

    def evaluate(values):
        nonlocal evaluations
        x,y,bw,bh,hy,end,bs,ls = values[:8]
        if not (0 <= x < x+bw < end <= w and 0 <= y < y+bh <= h
                and .7 < bw/bh < 1.3 and abs(hy-y-bh/2) <= bh*.1
                and .2 <= bs <= min(bw,bh)*.2 and .2 <= ls <= bh*.25):
            return None
        ir = copy.deepcopy(geometry_ir)
        ir[0].update(body_bbox=[x/w,y/h,bw/w,bh/h],body_fill=color(values[8:11]),
                     body_stroke=color(values[11:14]),body_stroke_width=bs/min(w,h),
                     connector=[[ (x+bw)/w,hy/h],[end/w,hy/h]],
                     connector_width=ls/min(w,h),connector_stroke=color(values[14:17]))
        rendered = render_fn(ir)
        evaluations += 1
        if rendered is None:
            return None
        score = float(error_fn(rendered))
        return (score,ir,rendered) if math.isfinite(score) else None

    base = render_fn(geometry_ir)
    if base is None:
        return None
    initial = float(error_fn(base))
    if not math.isfinite(initial):
        return None
    best = evaluate(p)
    if best is None:
        return None
    for step,shade in ((1.,24.),(.5,12.),(.25,6.),(.125,3.)):
        for _ in range(3):
            # A thicker centered border moves both inner edges. Register its
            # width together with the rectangle, preserving the outer bounds.
            # Independent probes can otherwise stall one pixel off at 2x scale.
            for sign in (-1,1):
                probe = p.copy()
                delta = sign*step
                probe[:4] += np.array([delta/2,delta/2,-delta,-delta])
                probe[6] += delta
                result = evaluate(probe)
                if result is not None and result[0] < best[0]-1e-9:
                    p,best = probe,result
            for i in range(len(p)):
                for sign in (-1,1):
                    probe = p.copy()
                    probe[i] += sign*(step if i<8 else shade)
                    result = evaluate(probe)
                    if result is not None and result[0] < best[0]-1e-9:
                        p,best = probe,result
    if best[0] >= initial-1e-9:
        return None
    return {'geometry_ir':best[1],'rendered':best[2],'initial_error':initial,
            'final_error':best[0],'evaluations':evaluations,'source':'square_and_handle_raster_profiles_v1'}
