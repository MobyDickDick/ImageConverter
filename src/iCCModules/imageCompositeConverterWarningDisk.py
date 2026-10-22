"""Register a rounded warning triangle and exclamation mark on a gradient disk."""
from __future__ import annotations

from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description, gradient_direction

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def _triangle(mask):
    """Intersect three regressed straight edges, ignoring the rounded corners."""
    ys, xs = np.nonzero(mask)
    if len(ys) < 12:
        return None
    low, high = int(ys.min()), int(ys.max())+1
    rows = np.arange(low, high)
    left = np.array([np.flatnonzero(mask[y])[0] for y in rows], dtype=float)
    right = np.array([np.flatnonzero(mask[y])[-1]+1 for y in rows], dtype=float)
    selected = (rows > low+(high-low)*.2) & (rows < low+(high-low)*.72)
    if selected.sum() < 3:
        return None
    a,b = np.polyfit(rows[selected]+.5, left[selected], 1)
    c,d = np.polyfit(rows[selected]+.5, right[selected], 1)
    if not (a < -.2 and c > .2):
        return None
    residual = np.r_[np.abs(a*(rows[selected]+.5)+b-left[selected]),
                     np.abs(c*(rows[selected]+.5)+d-right[selected])]
    if np.percentile(residual, 95) > max(.9, (high-low)*.025):
        return None
    ay = (d-b)/(a-c)
    ax = a*ay+b
    return np.array([ax, ay, a*high+b, c*high+d, high], dtype=float)


def fit_warning_disk(width, height, *, description, image, render_fn, error_fn):
    text = normalize_description(description, orientations=True).casefold()
    if not gradient_direction(text, 'senkrecht'):
        return None
    if not re.search(r'\bsenkrecht\w* (?:gerundet\w* )?strich\b', text):
        return None
    if not all(word in text for word in ('kreis', 'senkrecht', 'verlauf', 'warndreieck',
                                         'aufrecht', 'abgerundet', 'rand', 'innenfläche',
                                         'ausrufezeichen', 'senkrecht', 'strich', 'punkt', 'darunter')):
        return None
    if re.search(r'\b(?:ohne|nicht|zusätzlich|zwei|diagonal|waagerecht)\b', text):
        return None
    if 'keine weiteren objekte' not in text:
        return None
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    background = np.median(np.r_[pixels[0],pixels[-1],pixels[:,0],pixels[:,-1]],axis=0)
    mask = (np.max(np.abs(pixels-background),axis=2)>30).astype(np.uint8)
    count,labels,stats,_ = cv2.connectedComponentsWithStats(mask)
    if count < 2:
        return None
    index = 1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
    x,y,w,h,area = stats[index]
    if not (.87 < w/h < 1.15):
        return None
    contour = max(cv2.findContours((labels==index).astype(np.uint8),cv2.RETR_EXTERNAL,
                                  cv2.CHAIN_APPROX_NONE)[0],key=cv2.contourArea)[:,0].astype(float)+.5
    coefficients = np.linalg.lstsq(np.c_[2*contour,np.ones(len(contour))],
                                   np.sum(contour**2,axis=1),rcond=None)[0]
    cx,cy = coefficients[:2]
    radius = float(np.sqrt(max(0.,coefficients[2]+cx*cx+cy*cy)))
    if radius < 9 or np.mean(np.abs(np.linalg.norm(contour-[cx,cy],axis=1)-radius))>max(.7,radius*.035):
        return None
    # Pale triangle interiors can disconnect the ink from the disk mask.
    # Only components outside its circular silhouette are foreign objects.
    for i in range(1,count):
        if i != index and stats[i,4]>2:
            ys,xs = np.nonzero(labels==i)
            if np.any(np.hypot(xs+.5-cx,ys+.5-cy)>radius+1):
                return None
    yy,xx = np.indices((height,width),dtype=float)
    distance = np.hypot(xx+.5-cx,yy+.5-cy)
    t = (yy+.5-(cy-radius))/(2*radius)
    exposed = (distance < radius*.88) & (distance > radius*.67)
    for _ in range(5):
        if exposed.sum() < 15:
            return None
        colors = np.linalg.lstsq(np.c_[1-t[exposed],t[exposed]],pixels[exposed],rcond=None)[0]
        field = (1-t[...,None])*colors[0]+t[...,None]*colors[1]
        residual = np.max(np.abs(pixels-field),axis=2)
        exposed &= residual < max(12.,float(np.percentile(residual[exposed],70)))
    if np.max(np.abs(colors[0]-colors[1])) < 8:
        return None
    dark = ((np.mean(field-pixels,axis=2)>20) & (distance < radius*.94)).astype(np.uint8)
    count,labels,stats,_ = cv2.connectedComponentsWithStats(dark)
    if count < 3:
        return None
    index = 1+int(np.argmax(stats[1:,4]))
    ring = (labels==index).astype(np.uint8)
    contours,hierarchy = cv2.findContours(ring,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
    holes = [i for i,h in enumerate(hierarchy[0]) if h[3]>=0]
    if len(holes)!=1:
        return None
    interior = np.zeros_like(ring)
    cv2.drawContours(interior,contours,holes[0],1,-1)
    interior &= 1-ring
    outer = ring | interior
    outside_triangle = _triangle(outer)
    inside_triangle = _triangle(interior)
    if outside_triangle is None or inside_triangle is None:
        return None
    ax,ay,lx,rx,by = (outside_triangle+inside_triangle)/2
    sw = float(outside_triangle[-1]-inside_triangle[-1])
    if sw < 1 or not lx < ax < rx or by-ay < sw*3:
        return None
    # Separate the two ink components inside the enclosed light triangle.
    core = cv2.erode(interior,np.ones((3,3),np.uint8)).astype(bool)
    if core.sum()<6:
        return None
    light = np.median(pixels[core],axis=0)
    ink_contrast = np.max(np.abs(pixels-light),axis=2)
    cutoff = max(50.,float(np.percentile(ink_contrast[core],95))*.65)
    mark = (ink_contrast>cutoff) & core
    count,mark_labels,mark_stats,_ = cv2.connectedComponentsWithStats(mark.astype(np.uint8))
    components = [i for i in range(1,count) if mark_stats[i,4]>=2]
    if len(components)!=2:
        return None
    bar,dot = sorted(components,key=lambda i:mark_stats[i,1])
    bx,by0,bw,bh,ba = mark_stats[bar]
    dx,dy,dw,dh,da = mark_stats[dot]
    if not (bh>bw*1.5 and bw>=2 and abs(dw-dh)<=max(2,dw*.3)
            and by0+bh<dy and abs(bx+bw/2-dx-dw/2)<max(2,bw*.4)):
        return None
    triangle_color = np.median(pixels[ring.astype(bool)],axis=0)
    ink = np.median(pixels[(mark_labels==bar)|(mark_labels==dot)],axis=0)
    rim = np.median(pixels[(distance > radius*.96)&(distance < radius*1.01)],axis=0)
    p = np.r_[cx,cy,radius+.5,1.,ax,ay,lx,rx,by,sw,
              bx+bw/2,by0+bw/2,by0+bh-bw/2,bw,dx+dw/2,dy+dh/2,(dw+dh)/4,
              background,colors.ravel(),rim,triangle_color,light,ink]

    def build(p):
        cx,cy,r,rs,ax,ay,lx,rx,by,sw,bx,y1,y2,bw,dx,dy,dr = p[:17]
        bg,top,bottom,rim,edge,light,ink = p[17:].reshape(-1,3)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                '<defs><linearGradient id="disk_color" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{_hex(top)}"/><stop offset="1" stop-color="{_hex(bottom)}"/>'
                '</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="{_hex(bg)}"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="url(#disk_color)" stroke="{_hex(rim)}" stroke-width="{rs:.4f}"/>'
                f'<path d="M {ax:.4f} {ay:.4f} L {rx:.4f} {by:.4f} L {lx:.4f} {by:.4f} Z" fill="{_hex(light)}" stroke="{_hex(edge)}" stroke-width="{sw:.4f}" stroke-linejoin="round"/>'
                f'<line x1="{bx:.4f}" y1="{y1:.4f}" x2="{bx:.4f}" y2="{y2:.4f}" stroke="{_hex(ink)}" stroke-width="{bw:.4f}" stroke-linecap="round"/>'
                f'<circle cx="{dx:.4f}" cy="{dy:.4f}" r="{dr:.4f}" fill="{_hex(ink)}"/></svg>\n')

    def valid(p):
        cx,cy,r,rs,ax,ay,lx,rx,by,sw,bx,y1,y2,bw,dx,dy,dr = p[:17]
        if not (np.isfinite(p).all() and r>7 and .1<=rs<=3 and sw>=1
                and 0<=cx-r-rs/2 and cx+r+rs/2<=width and 0<=cy-r-rs/2 and cy+r+rs/2<=height
                and lx<ax<rx and ay<by and 1<=bw<sw*2 and dr>=.6
                and ay+sw<y1-bw/2<y2+bw/2<dy-dr<dy+dr<by-sw/2
                and abs(bx-dx)<bw*.6):
            return False
        if not all((x-cx)**2+(y-cy)**2<(r-rs/2-sw/2)**2 for x,y in ((ax,ay),(lx,by),(rx,by))):
            return False
        for x,y,pad in ((bx,y1,bw/2),(bx,y2,bw/2),(dx,dy,dr)):
            left=ax+(lx-ax)*(y-ay)/(by-ay)
            right=ax+(rx-ax)*(y-ay)/(by-ay)
            if not left+sw/2+pad<x<right-sw/2-pad:
                return False
        return True

    result = _register(p,17,build,valid,pixels.astype(np.uint8),render_fn,error_fn,
                       'raster_warning_disk_registration',preserve_initial_error=True)
    if result is None:
        return None
    # Unexplained connected regions catch foreign marks and wrong topology.
    difference = np.max(np.abs(pixels-np.asarray(result['rendered'],dtype=float)),axis=2)
    unexplained = cv2.erode((difference>45).astype(np.uint8),np.ones((3,3),np.uint8))
    if np.count_nonzero(unexplained)>max(2,area*.001):
        return None
    return result
