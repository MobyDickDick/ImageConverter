"""Register two crossing diagonal capsules inside a solid disk from pixels."""
from __future__ import annotations

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def fit_diagonal_cross_disk(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(word in text for word in ('kreis', 'einfarbig', 'diagonal', 'kreuz',
                                         'zwei', 'strich', 'abgerundet', 'innerhalb')):
        return None
    if re.search(r'\b(?:ohne|nicht|zusätzlich|drei|verlauf|rechteck|waagerecht|senkrecht)\b', text):
        return None
    if 'keine schriftzeichen' not in text or 'keine weiteren objekte' not in text:
        return None
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    border = np.r_[pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]]
    background = np.median(border, axis=0)
    mask = (np.max(np.abs(pixels-background), axis=2) > 50).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if count < 2:
        return None
    index = 1+int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x,y,w,h,area = stats[index]
    if not (.88 < w/h < 1.14 and area > .58*w*h):
        return None
    if sum(stats[i,cv2.CC_STAT_AREA] for i in range(1,count) if i!=index) > max(3,area*.003):
        return None
    contours = cv2.findContours((labels==index).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0]
    contour = max(contours,key=cv2.contourArea)[:,0].astype(float)+.5
    coefficients = np.linalg.lstsq(np.c_[2*contour,np.ones(len(contour))],
                                  np.sum(contour**2,axis=1),rcond=None)[0]
    cx,cy = coefficients[:2]
    radius = float(np.sqrt(max(0.,coefficients[2]+cx*cx+cy*cy)))
    if radius<7 or np.mean(np.abs(np.linalg.norm(contour-[cx,cy],axis=1)-radius))>max(.7,radius*.035):
        return None
    yy,xx = np.indices((height,width),dtype=float)
    points = np.stack((xx+.5,yy+.5),axis=-1)
    distance = np.linalg.norm(points-[cx,cy],axis=2)
    core = distance<radius*.88
    fill = np.median(pixels[core],axis=0)
    mark = core & (np.max(np.abs(pixels-fill),axis=2)>70)
    count,mark_labels,mark_stats,_ = cv2.connectedComponentsWithStats(mark.astype(np.uint8))
    if count!=2 or mark_stats[1,cv2.CC_STAT_AREA]<12:
        return None
    coords = points[mark]
    center = np.median(coords,axis=0)
    relative = coords-center
    segments=[]
    for sign in (1,-1):
        # Separate the free arms before PCA; their intersection would bias
        # either line's thickness and direction. Only line parameters survive.
        selected = relative[(relative[:,0]*relative[:,1]*sign>0)
                            & (np.linalg.norm(relative,axis=1)>radius*.2)]
        if len(selected)<8:
            return None
        _,_,axes = np.linalg.svd(selected-selected.mean(axis=0),full_matrices=False)
        direction = axes[0]
        if direction[0]<0:
            direction=-direction
        if not (.35<abs(direction[1]/direction[0])<2.85 and direction.prod()*sign>0):
            return None
        normal = np.array([-direction[1],direction[0]])
        origin = center+selected.mean(axis=0)
        along = (coords-origin)@direction
        across = (coords-origin)@normal
        free = np.abs(along)>radius*.2
        near = free & (np.abs(across)<radius*.18)
        if near.sum()<8:
            return None
        sw = max(2.,4*np.median(np.abs(across[near])))
        own = np.abs(across)<sw*.65
        low,high = np.percentile(along[own],[0,100])
        tips = own & ((along<low+sw*.25) | (along>high-sw*.25))
        # Rounded tips narrow towards their extremum. Square caps retain the
        # body's full perpendicular spread. Tiny marks lack this resolution.
        if sw>=5 and tips.sum()>=8 and np.std(across[tips])>sw*.265:
            return None
        start,end = (origin+direction*t for t in (low+sw/2-.4,high-sw/2+.4))
        segments.extend([*start,*end,sw])
    expected = np.zeros((height,width),dtype=bool)
    for k in (0,5):
        start,end,sw = np.array(segments[k:k+2]),np.array(segments[k+2:k+4]),segments[k+4]
        direction=end-start
        t=np.clip(np.sum((points-start)*direction,axis=2)/np.sum(direction**2),0,1)
        expected |= np.linalg.norm(points-(start+t[...,None]*direction),axis=2)<=sw/2
    if (expected & mark).sum()/max(1,(expected | mark).sum())<.80:
        return None
    clean = core & ~cv2.dilate(mark.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
    ink = cv2.erode(mark.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    if not clean.any() or not ink.any():
        return None
    fill = np.median(pixels[clean],axis=0)
    cross = np.median(pixels[ink],axis=0)
    if np.percentile(np.max(np.abs(pixels[clean]-fill),axis=1),95)>30:
        return None
    outside = distance>radius+2
    if outside.any() and np.percentile(np.max(np.abs(pixels[outside]-background),axis=1),95)>25:
        return None
    p = np.r_[cx,cy,radius+.35,segments,background,fill,cross]

    def build(p):
        cx,cy,r = p[:3]
        bg,fill,cross = p[13:].reshape(-1,3)
        lines=''
        for k in (3,8):
            x1,y1,x2,y2,sw = p[k:k+5]
            lines += (f'<line x1="{x1:.4f}" y1="{y1:.4f}" x2="{x2:.4f}" y2="{y2:.4f}" '
                      f'stroke="{_hex(cross)}" stroke-width="{sw:.4f}" stroke-linecap="round"/>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                f'<rect width="{width}" height="{height}" fill="{_hex(bg)}"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="{_hex(fill)}"/>{lines}</svg>\n')

    def valid(p):
        cx,cy,r = p[:3]
        if not (np.isfinite(p).all() and r>6 and 0<=cx-r and cx+r<=width and 0<=cy-r and cy+r<=height):
            return False
        endpoints=[]
        for k,sign in ((3,1),(8,-1)):
            x1,y1,x2,y2,sw = p[k:k+5]
            if not (1<=sw<r*.35 and x2-x1>sw*2 and (y2-y1)*sign>sw*2):
                return False
            if not all((x-cx)**2+(y-cy)**2<(r-sw/2-1)**2 for x,y in ((x1,y1),(x2,y2))):
                return False
            endpoints.append((np.array([x1,y1]),np.array([x2,y2])))
        a,b=endpoints[0];c,d=endpoints[1]
        def side(a,b,c):
            u,v=b-a,c-a
            return u[0]*v[1]-u[1]*v[0]
        return side(a,b,c)*side(a,b,d)<0 and side(c,d,a)*side(c,d,b)<0

    return _register(p,13,build,valid,pixels.astype(np.uint8),render_fn,error_fn,
                     'raster_diagonal_cross_disk_registration',preserve_initial_error=True)
