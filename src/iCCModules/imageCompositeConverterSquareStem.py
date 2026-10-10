"""Register a plain square and its centered rightward handle from pixels."""
from __future__ import annotations

import copy
import math

import cv2
import numpy as np


def _observe_slash_and_dot(interior, x0, y0):
    """Resolve two contrast cores: a slender rising slash and a nearby square.

    The raster supplies their positions, widths and shared color. This is a
    constrained geometric observation, without a font or stored glyph outline.
    """
    fill = np.median(interior, axis=(0, 1))
    contrast = np.linalg.norm(interior.astype(float)-fill, axis=2)
    core = contrast > max(40., float(contrast.max())*.6)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(core.astype(np.uint8))
    if count == 2:
        # At small resolutions JPEG fringes can bridge two separate marks.
        # Resolve their stronger cores, then enforce the same two-object
        # topology and register the boundaries against the full raster.
        stronger = contrast > max(40., float(contrast.max())*.75)
        new_count, new_labels, new_stats, _ = cv2.connectedComponentsWithStats(stronger.astype(np.uint8))
        if new_count == 3:
            core,count,labels,stats = stronger,new_count,new_labels,new_stats
        else:
            # A very small slash can itself have a broken high-contrast core.
            # Fit its upper rows and separate a lower-left compact component
            # from the merged core. The ordinary slope/size/dot tests below
            # still apply to both observed parts.
            ys,xs = np.nonzero(core)
            upper = ys < ys.min()+.65*(ys.max()-ys.min()+1)
            if len(np.unique(ys[upper])) < 3:
                return None
            slope,intercept = np.polyfit(ys[upper],xs[upper],1)
            slash_pixels = xs >= slope*ys+intercept-.75
            if slash_pixels.all() or not slash_pixels.any():
                return None
            labels = np.zeros(core.shape,np.int32)
            labels[ys[slash_pixels],xs[slash_pixels]] = 1
            labels[ys[~slash_pixels],xs[~slash_pixels]] = 2
            if cv2.connectedComponents((labels==2).astype(np.uint8))[0] != 2:
                return None
            stats = np.zeros((3,5),np.int32)
            for component in (1,2):
                yy,xx = np.nonzero(labels==component)
                stats[component] = [xx.min(),yy.min(),np.ptp(xx)+1,np.ptp(yy)+1,len(xx)]
            count = 3
    if count != 3:
        return None
    slash, dot = sorted((1, 2), key=lambda i: stats[i, cv2.CC_STAT_HEIGHT], reverse=True)
    sx, sy, sw, sh, area = stats[slash]
    dx, dy, dw, dh, _ = stats[dot]
    if sh < 3 or sh < dh*2 or not .5 <= dw/dh <= 2 or dw > sh*.5:
        return None
    ys, xs = np.nonzero(labels == slash)
    slope, intercept = np.polyfit(ys, xs, 1)
    if not -.8 < slope < -.08 or np.std(xs-(slope*ys+intercept)) > max(1., sw*.25):
        return None
    top_x, bottom_x = slope*sy+intercept+.5, slope*(sy+sh)+intercept+.5
    if not (dx+dw <= bottom_x and sy+sh*.55 <= dy < sy+sh+dh):
        return None
    # Exclude contrast fringes as well as cores from the flat-fill check.
    background = interior[contrast < 25]
    if not len(background) or np.std(background.astype(float), axis=0).max() > 18:
        return None
    mark_color = np.median(interior[core], axis=0)
    return [x0+top_x, y0+sy, x0+bottom_x, y0+sy+sh, area/sh,
            x0+dx, y0+dy, float(dw), float(dh), *mark_color]


def _fit_top_stem_square(geometry_ir, *, image, render_fn, error_fn, description):
    """Rotate the observed body/handle contract while retaining mark direction."""
    original = geometry_ir[0]
    canonical = copy.deepcopy(geometry_ir)
    bx, by, bw, bh = original['body_bbox']
    canonical[0].update(kind='RightStemSquareKelleGlyph', body_bbox=[1-by-bh,bx,bh,bw],
                        connector=[[1-y,x] for x,y in original['connector']])

    def restore(ir):
        result = copy.deepcopy(ir)
        x,y,w,h = result[0]['body_bbox']
        result[0].update(kind=original['kind'], body_bbox=[y,1-x-w,h,w],
                         connector=[[v,1-u] for u,v in result[0]['connector']])
        for mark in result[1:]:
            mark['points'] = [[v,1-u] for u,v in mark['points']]
        return result

    def render(candidate):
        raster = render_fn(restore(candidate))
        return None if raster is None else cv2.rotate(raster,cv2.ROTATE_90_CLOCKWISE)

    fitted = fit_square_stem(canonical, image=cv2.rotate(image,cv2.ROTATE_90_CLOCKWISE),
        description=description, render_fn=render,
        error_fn=lambda raster:error_fn(cv2.rotate(raster,cv2.ROTATE_90_COUNTERCLOCKWISE)),
        _marks_in_original=True)
    if fitted is None:
        return None
    fitted['geometry_ir'] = restore(fitted['geometry_ir'])
    fitted['rendered'] = cv2.rotate(fitted['rendered'],cv2.ROTATE_90_COUNTERCLOCKWISE)
    return fitted


def fit_square_stem(geometry_ir, *, image, render_fn, error_fn, description='', _marks_in_original=False):
    desc = description.casefold()
    marked = ('punkt' in desc and any(word in desc for word in ('schräg', 'schraeg', 'diagonal'))
              and not any(word in desc for word in ('ohne markierung', 'ohne innenmarkierung', 'ohne punkt')))
    if (len(geometry_ir) == 1 and geometry_ir[0].get('kind') == 'Rotated180SquareKelleGlyph'
            and marked):
        arr = np.asarray(image)
        if arr.ndim != 3 or arr.shape[2] != 3 or not arr.size or not np.isfinite(arr).all():
            return None
        return _fit_top_stem_square(geometry_ir,image=arr,render_fn=render_fn,error_fn=error_fn,description=description)
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
    if not interior.size:
        return None
    if marked and _marks_in_original:
        # Observe the slash and dot in the requested orientation. Only the
        # square/handle fit uses canonical axes; the marking is not rotated
        # into a different semantic topology.
        marks = _observe_slash_and_dot(np.rot90(interior), top+margin, w-(right-margin+1))
    else:
        marks = _observe_slash_and_dot(interior, left+margin, top+margin) if marked else None
    if marked and marks is None:
        return None
    if not marked and float(np.std(interior.astype(float),axis=(0,1)).max()) > 18:
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
    if marks is not None:
        p = np.concatenate((p, marks))
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
        if marks is not None:
            tx,ty,bx,by,thickness,dx,dy,dw,dh = values[17:26]
            if not (ty < by and tx > bx and .2 <= thickness < (by-ty)*.4
                    and .2 <= dw <= (by-ty)*.5 and .2 <= dh <= (by-ty)*.5
                    and .5 <= dw/dh <= 2 and dx+dw <= bx and dy >= ty+(by-ty)*.55):
                return None
            shapes = (
                ('slash', [(tx-thickness/2,ty),(tx+thickness/2,ty),
                           (bx+thickness/2,by),(bx-thickness/2,by)]),
                ('dot', [(dx,dy),(dx+dw,dy),(dx+dw,dy+dh),(dx,dy+dh)]),
            )
            for name, points in shapes:
                if _marks_in_original:
                    points = [(w-py,px) for px,py in points]
                if not all(x+bs/2 < px < x+bw-bs/2 and y+bs/2 < py < y+bh-bs/2 for px,py in points):
                    return None
                ir.append({'kind':'PolygonPath','id':'raster_interior_'+name,
                           'role':'observed_interior_mark','closed':True,
                           'points':[[px/w,py/h] for px,py in points],
                           'fill':color(values[26:29]),'stroke':'none','stroke_width':0.})
        rendered = render_fn(ir)
        evaluations += 1
        if rendered is None:
            return None
        score = float(error_fn(rendered))
        if math.isfinite(score) and marks is not None:
            # Small antialiased marks and borders need squared color residuals:
            # the CLI's mean absolute error can hide a wrong contour behind a
            # large flat interior. Keep the caller's error for final acceptance.
            score = float(np.mean(np.sum((arr.astype(float)-rendered.astype(float))**2, axis=2)))
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
        # The marked topology adds two contours and a contrast color. Allow
        # them to settle jointly with the border, with a fixed upper bound.
        for _ in range(6 if marks is not None else 3):
            previous_score = best[0]
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
                    probe[i] += sign*(step if i<8 or 17<=i<26 else shade)
                    result = evaluate(probe)
                    if result is not None and result[0] < best[0]-1e-9:
                        p,best = probe,result
            if marks is not None and best[0] == previous_score:
                break
    final = float(error_fn(best[2]))
    if not math.isfinite(final) or final >= initial-1e-9:
        return None
    return {'geometry_ir':best[1],'rendered':best[2],'initial_error':initial,
            'final_error':final,'evaluations':evaluations,'source':'square_and_handle_raster_profiles_v1'}
