"""Compose three observed triangular wings, a connector and a labeled disk.

Only straight-edge regressions and a circle fit seed native primitives. The
rendered complete scene, including its glyph and unexplained foreground, is
checked against the source. No catalog coordinates or vector templates are used.
"""
from __future__ import annotations

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def fit_motor_valve(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '')
    words = text.casefold()
    letters = re.findall(r'(?i:einzelne[nr]? dunkle[nr]? großbuchstabe)\s+["„]([A-Z])["“]', text)
    head_description = re.search(r'drei\s+(?:spitze\w*\s+)?dreieck\w*[^.]*',words)
    if (len(letters) != 1 or head_description is None
            or not all(t in head_description.group() for t in ('links','oben','unten'))
            or not all(t in words for t in
            ('gemeinsamen spitze', 'griff nach rechts', 'kreisscheibe', 'aufrecht', 'serifenlos'))
            or not re.search(r'(?:waagerecht\w*|horizontal\w*)',words)
            or any(t in words for t in ('zusätzlich', 'ohne griff', 'ohne buchstabe', 'vier dreieck'))):
        return None
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    mask = np.min(pixels, axis=2) < 215
    ys, xs = np.nonzero(mask)
    if len(xs) < 40:
        return None
    # The actuator's exposed right arc determines the circle independently of
    # the attached left connector and wing silhouette.
    contour = max(cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL,
                                  cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0]+.5
    arc = contour[contour[:, 0] > xs.max()+1-(ys.max()-ys.min()+1)*.30]
    if len(arc) < 10:
        return None
    coeff = np.linalg.lstsq(np.c_[2*arc, np.ones(len(arc))], (arc**2).sum(axis=1), rcond=None)[0]
    cx, cy = coeff[:2]
    radius = float(np.sqrt(max(0, coeff[2]+cx*cx+cy*cy)))
    if (radius < 5 or radius > height*.45
            or np.mean(abs(np.linalg.norm(arc-[cx,cy],axis=1)-radius)) > max(.65,radius*.04)):
        return None
    yy, xx = np.indices(mask.shape, dtype=float)
    distance = np.hypot(xx+.5-cx, yy+.5-cy)
    head = mask & (xx+.5 < cx-radius-1)
    hy, hx = np.nonzero(head & (abs(yy+.5-cy) > radius*.25))
    if len(hx) < 20:
        return None
    left, top, bottom = hx.min()+.5, hy.min()+.5, hy.max()+.5
    if not top+radius*.8 < cy < bottom-radius*.8:
        return None
    fits = []
    for rows in (range(int(top), int(top+(cy-top)*.45)),
                 range(int(bottom-(bottom-cy)*.45)+1, int(bottom)+1)):
        samples = []
        for row in rows:
            cols = np.flatnonzero(head[row])
            if len(cols) >= 3:
                samples.append((row+.5, cols[0]+.5, cols[-1]+.5))
        if len(samples) < 3:
            return None
        samples = np.asarray(samples)
        fits.append([np.polyfit(samples[:,0],samples[:,i],1) for i in (1,2)])
    upper, lower = fits
    if not (upper[0][0] > .1 and upper[1][0] <= .05 and lower[0][0] < -.1 and lower[1][0] >= -.05):
        return None
    apex = np.mean([np.polyval(f,cy) for pair in fits for f in pair])
    if not left+radius*.4 < apex < cx-radius-1:
        return None
    # Outer left base excludes the upper/lower wings, which begin to its right.
    left_rows = np.flatnonzero(head[:, int(left)])
    if len(left_rows) < 4:
        return None
    fill = np.median(pixels[(distance > radius*.55) & (distance < radius*.78)], axis=0)
    glyph = (np.mean(fill-pixels,axis=2) > 35) & (distance < radius*.8)
    gy, gx = np.nonzero(glyph)
    if len(gx) < 4:
        return None
    rim = np.percentile(pixels[(distance > radius*.92) & (distance < radius*1.03)],15,axis=0)
    ink = np.percentile(pixels[glyph],15,axis=0)
    core = cv2.erode(head.astype(np.uint8), np.ones((3,3),np.uint8)).astype(bool)
    if core.sum() < 8:
        return None
    # The diagonal field is estimated on exposed triangle interiors. Its
    # endpoints are fitted colors rather than fixed palette entries.
    t = ((xx-left)/max(1,cx-radius-left)+(bottom-yy)/max(1,bottom-top))/2
    colors = np.linalg.lstsq(np.c_[1-t[core],t[core]],pixels[core],rcond=None)[0].clip(0,255)
    stroke = np.percentile(pixels[head & ~core],25,axis=0)
    line_pixels = pixels[(xx > apex+1) & (xx < cx-radius-1) & (abs(yy+.5-cy) < 1.5)]
    if len(line_pixels) < 2:
        return None
    connector = mask[max(0,int(cy)-1):int(cy)+2, int(apex)+2:int(cx-radius)-1]
    if not connector.size or np.mean(connector.any(axis=0)) < .85:
        return None
    line_color = np.percentile(line_pixels,15,axis=0)
    # Geometry, followed by gradient endpoints, wing rim, disk fill/rim, ink,
    # connector color. Every parameter is registered on the whole image.
    p = np.r_[apex,cy,left,left_rows.min()+.5,left_rows.max()+.5,
              np.polyval(upper[0],top),np.polyval(upper[1],top),top,
              np.polyval(lower[0],bottom),np.polyval(lower[1],bottom),bottom,
              cx,cy,radius-.4,1.,gx.min()+(gx.max()-gx.min()+1)/2,gy.max()+1,
              (gy.max()-gy.min()+1)*1.35,1.,1.5,
              colors.ravel(),stroke,fill,rim,ink,line_color]
    geometry_count = 20

    def build(v, blank=False):
        ax,ay,lx,lt,lb,tl,tr,ty,bl,br,by,cx,cy,r,sw,tx,baseline,size,bw,cw = v[:20]
        low,high,edge,body,rim,ink,line = v[20:].reshape(-1,3)
        triangles = ((ax,ay,lx,lt,lx,lb),(ax,ay,tl,ty,tr,ty),(ax,ay,bl,by,br,by))
        shapes = ''.join(f'<path d="M {a:.5f} {b:.5f} L {c:.5f} {d:.5f} L {e:.5f} {f:.5f} Z" '
                         f'fill="url(#wings)" stroke="{_hex(edge)}" stroke-width="{bw:.5f}" stroke-linejoin="round"/>'
                         for a,b,c,d,e,f in triangles)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<defs><linearGradient id="wings" gradientUnits="userSpaceOnUse" x1="{left}" y1="{bottom}" '
            f'x2="{cx-radius}" y2="{top}"><stop offset="0%" stop-color="{_hex(low)}"/><stop offset="100%" stop-color="{_hex(high)}"/></linearGradient></defs>'
            f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
            f'<line x1="{ax:.5f}" y1="{ay:.5f}" x2="{cx-r:.5f}" y2="{cy:.5f}" stroke="{_hex(line)}" stroke-width="{cw:.5f}"/>'
            +shapes+f'<circle cx="{cx:.5f}" cy="{cy:.5f}" r="{r:.5f}" fill="{_hex(body)}" stroke="{_hex(rim)}" stroke-width="{sw:.5f}"/>'
            +('' if blank else f'<text x="{tx:.5f}" y="{baseline:.5f}" text-anchor="middle" font-family="Arial" font-weight="700" '
              f'font-size="{size:.5f}" fill="{_hex(ink)}">{letters[0]}</text>')+'</svg>\n')

    def valid(v):
        ax,ay,lx,lt,lb,tl,tr,ty,bl,br,by,cx,cy,r,sw,tx,baseline,size,bw,cw = v[:20]
        return (np.isfinite(v).all() and lx < ax < cx-r and tl < ax < tr and bl < ax < br
            and ty < ay < by and lt < ay < lb and abs(ay-cy) < r*.15
            and r > 4 and 0 <= cx-r-sw/2 and cx+r+sw/2 <= width
            and 0 <= cy-r-sw/2 and cy+r+sw/2 <= height
            and .2 < min(sw,bw,cw) and max(sw,bw,cw) < r*.3
            and abs(tx-cx) < r*.25 and cy < baseline < cy+r and 3 < size < r*2
            and np.all((v[20:] >= 0) & (v[20:] <= 255)))
    # Measure the production font's actual silhouette before whole-scene search.
    for _ in range(3):
        drawn, blank = render_fn(build(p),width,height), render_fn(build(p,True),width,height)
        if drawn is None or blank is None:
            return None
        sy,sx = np.nonzero(np.max(abs(drawn.astype(float)-blank.astype(float)),axis=2) > 35)
        if not len(sx):
            return None
        p[15] += (gx.min()+gx.max()-sx.min()-sx.max())/2
        p[16] += (gy.min()+gy.max()-sy.min()-sy.max())/2
        p[17] *= (gy.max()-gy.min()+1)/(sy.max()-sy.min()+1)
    semantic_evaluations = 0
    def satisfactory(parameters, measured):
        nonlocal semantic_evaluations
        raster = measured[3]
        blank = render_fn(build(parameters,True),width,height)
        semantic_evaluations += 1
        if blank is None:
            return False
        predicted = (np.mean(blank.astype(float)-raster.astype(float),axis=2)>35)&(distance<radius*.8)
        union = (glyph|predicted).sum()
        if not union or (glyph&predicted).sum()/union < max(.65,1-3/radius):
            return False
        missing_distance = cv2.distanceTransform((~predicted).astype(np.uint8),cv2.DIST_L2,3)
        extra_distance = cv2.distanceTransform((~glyph).astype(np.uint8),cv2.DIST_L2,3)
        if (missing_distance[glyph].max()>max(1.5,radius*.06)
                or extra_distance[predicted].max()>max(1.5,radius*.06)):
            return False
        ref,out = np.min(image,axis=2)<215,np.min(raster,axis=2)<215
        cover = cv2.dilate(out.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
        reverse = cv2.dilate(ref.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
        return bool((ref&~cover).sum()<=max(3,ref.sum()*.015)
                    and (out&~reverse).sum()<=max(3,out.sum()*.015))

    result = _register(p,geometry_count,build,valid,image,render_fn,error_fn,'raster_motor_valve_v1',
                       satisfactory_fn=satisfactory)
    if result is None or not satisfactory(np.asarray(result['parameters']),
                                         (0.,result['error'],result['svg'],result['rendered'])):
        return None
    result['evaluations'] += 6+semantic_evaluations
    return result
