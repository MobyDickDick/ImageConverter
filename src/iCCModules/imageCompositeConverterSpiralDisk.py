"""Register directed converging chords and an inward spiral on a solid disk.

The spiral is a low dimensional polar regression, rendered as bounded cubic
Hermite segments. Neither pixel contours nor reference vectors are emitted.
"""
from __future__ import annotations

import re
import cv2
import numpy as np
from xml.etree import ElementTree as ET

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register
from src.iCCModules.imageCompositeConverterCircleLinework import _segment_distance


def spiral_points(p, t):
    x, y, outer, decay, angle, sweep, aspect = p
    radius = outer*np.exp(-decay*sweep*t)
    theta = angle-sweep*t
    return np.array([x+radius*np.cos(theta), y+aspect*radius*np.sin(theta)]).T


def spiral_path(p):
    # At most one cubic per quarter turn, independent of raster resolution.
    count = int(np.ceil(p[5]/(np.pi/2)))
    ts = np.linspace(0, 1, count+1)
    points = spiral_points(p, ts)
    radius = p[2]*np.exp(-p[3]*p[5]*ts)
    theta = p[4]-p[5]*ts
    derivative = np.array([(-p[3]*p[5])*radius*np.cos(theta)+radius*p[5]*np.sin(theta),
                           p[6]*((-p[3]*p[5])*radius*np.sin(theta)-radius*p[5]*np.cos(theta))]).T
    parts = [f'M {points[0,0]:.4f} {points[0,1]:.4f}']
    for i in range(count):
        controls = [points[i]+derivative[i]/(3*count),
                    points[i+1]-derivative[i+1]/(3*count), points[i+1]]
        parts.append('C '+' '.join(f'{v:.4f}' for v in np.array(controls).ravel()))
    return ' '.join(parts)


def _polar_seed(points, weights, cx, cy, radius):
    """Find a center and pitch by circular regression, without path tracing."""
    best = None
    for x in np.linspace(cx-radius*.3, cx+radius*.3, 9):
        for y in np.linspace(cy-radius*.05, cy+radius*.55, 9):
            delta = points-[x, y]
            r = np.linalg.norm(delta, axis=1)
            theta = np.arctan2(delta[:,1], delta[:,0])
            for pitch in np.linspace(.08, .24, 32):
                z = np.sum(weights*np.exp(1j*(theta-np.log(np.maximum(r,.1))/pitch)))
                score = abs(z)/weights.sum()
                if best is None or score > best[0]:
                    best = (score, x, y, pitch, np.angle(z))
    score, x, y, pitch, phase = best
    for step in (.04, .015, .005):
        improved = True
        for _ in range(3):
            if not improved:
                break
            improved = False
            for index in range(3):
                for sign in (-1, 1):
                    candidate = np.array([x,y,pitch])
                    candidate[index] += sign*step*(.1 if index == 2 else radius)
                    a,b,c = candidate
                    if c <= .04:
                        continue
                    delta = points-[a,b]
                    r = np.linalg.norm(delta,axis=1)
                    theta = np.arctan2(delta[:,1],delta[:,0])
                    z = np.sum(weights*np.exp(1j*(theta-np.log(np.maximum(r,.1))/c)))
                    value = abs(z)/weights.sum()
                    if value > score:
                        score,x,y,pitch,phase = value,a,b,c,np.angle(z)
                        improved = True
    r = np.linalg.norm(points-[x,y],axis=1)
    theta = np.arctan2(points[:,1]-y,points[:,0]-x)
    turns = np.rint((np.log(np.maximum(r,.1))/pitch+phase-theta)/(2*np.pi))
    unwrapped = theta+turns*2*np.pi
    # Project each observed pixel onto the fitted spiral before selecting ends.
    distance = r-np.exp(pitch*(unwrapped-phase))
    good = np.abs(distance) < max(.9, radius*.065)
    if score < .45 or good.sum() < 12:
        return None
    start, end = np.percentile(unwrapped[good], [99, 1])
    if not 2*np.pi < start-end < 5*np.pi:
        return None
    return [x,y,np.exp(pitch*(start-phase)),pitch,start,start-end,1.]


def fit_spiral_disk(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(token in text for token in ('kreis', 'zwei schräge linien', 'spirale',
                                          'nach innen', 'gegen den uhrzeigersinn')):
        return None
    neutral = text.replace('keine schriftzeichen', '').replace('kein griff', '')
    if re.search(r'\b(?:ohne|kein|keine|nicht|zusätzlich|verlauf|dreieck|gefüllte spirale|im uhrzeigersinn)\b', neutral):
        return None
    directions = re.findall(r'laufen nach (oben|rechts|unten|links) aufeinander zu', text)
    if len(directions) != 1:
        return None
    turns = ('oben', 'rechts', 'unten', 'links').index(directions[0])
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    if not turns:
        return _fit_up(width, height, pixels=pixels, render_fn=render_fn, error_fn=error_fn)
    canonical = np.ascontiguousarray(np.rot90(pixels, turns))

    def render_canonical(svg, w, h):
        raster = render_fn(_orient_svg(svg, turns, width, height), width, height)
        return None if raster is None else np.ascontiguousarray(np.rot90(raster, turns))

    def source_error(reference, raster):
        return error_fn(np.ascontiguousarray(np.rot90(reference, -turns)),
                        np.ascontiguousarray(np.rot90(raster, -turns)))

    result = _fit_up(canonical.shape[1], canonical.shape[0], pixels=canonical,
                     render_fn=render_canonical, error_fn=source_error)
    if result is not None:
        result['svg'] = _orient_svg(result['svg'], turns, width, height)
        result['rendered'] = np.ascontiguousarray(np.rot90(result['rendered'], -turns))
    return result


def _orient_svg(svg, turns, width, height):
    """Rotate native coordinates, including cubic controls, into the input frame."""
    root = ET.fromstring(svg)

    def point(x, y):
        return ((width-y, x) if turns == 1 else
                (width-x, height-y) if turns == 2 else (y, height-x))

    for element in root.iter():
        element.tag = element.tag.rsplit('}', 1)[-1]
        if element.tag == 'rect':  # The white canvas only.
            element.set('width', str(width))
            element.set('height', str(height))
        elif element.tag in ('circle', 'line'):
            pairs = [('cx', 'cy')] if element.tag == 'circle' else [('x1', 'y1'), ('x2', 'y2')]
            for xkey, ykey in pairs:
                x, y = point(float(element.get(xkey)), float(element.get(ykey)))
                element.set(xkey, f'{x:.4f}')
                element.set(ykey, f'{y:.4f}')
        elif element.tag == 'path':
            tokens = re.findall(r'[MC]|[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?', element.get('d', ''))
            transformed = []
            index = 0
            while index < len(tokens):
                if tokens[index] in ('M', 'C'):
                    transformed.append(tokens[index])
                    index += 1
                else:
                    x, y = point(float(tokens[index]), float(tokens[index+1]))
                    transformed.extend([f'{x:.4f}', f'{y:.4f}'])
                    index += 2
            element.set('d', ' '.join(transformed))
    root.set('xmlns', 'http://www.w3.org/2000/svg')
    root.set('width', str(width))
    root.set('height', str(height))
    return ET.tostring(root, encoding='unicode')+'\n'


def _fit_up(width, height, *, pixels, render_fn, error_fn):
    mask = (np.min(pixels, axis=2) < 220).astype(np.uint8)
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if not contours:
        return None
    contour = max(contours,key=cv2.contourArea)
    area = cv2.contourArea(contour)
    if area < width*height*.15 or sum(cv2.contourArea(c) for c in contours if c is not contour) > max(2,area*.001):
        return None
    points = contour[:,0].astype(float)+.5
    coefficients = np.linalg.lstsq(np.c_[2*points,np.ones(len(points))],np.sum(points**2,axis=1),rcond=None)[0]
    cx,cy = coefficients[:2]
    radius = float(np.sqrt(max(0,coefficients[2]+cx*cx+cy*cy)))
    if radius < 7 or np.percentile(np.abs(np.linalg.norm(points-[cx,cy],axis=1)-radius),90) > max(.9,radius*.05):
        return None
    yy,xx = np.indices((height,width),dtype=float); xx += .5; yy += .5
    radial = np.hypot(xx-cx,yy-cy)
    core = radial < radius*.88
    fill = np.median(pixels[core],axis=0)
    strength = np.linalg.norm(pixels-fill,axis=2)
    cutoff = max(12.,np.percentile(strength[core],95)*.32)
    ink = (strength > cutoff) & (radial < radius*.92)
    if not .06 < ink[core].mean() < .5:
        return None
    slopes = []
    segments = []
    for sign in (-1,1):
        best = None
        for a in sign*np.linspace(.15,.8,35):
            for b in sign*np.linspace(radius*.25,radius*.8,40):
                distance = np.abs(xx-cx-a*(yy-cy)-b)/np.sqrt(1+a*a)
                region = (distance < .8) & core & (yy < cy-radius*.05)
                upper = region & (yy < cy-radius*.2)
                if not upper.any():
                    continue
                score = np.sum(strength[region])+np.sum(strength[upper])
                if best is None or score > best[0]:
                    best = (score,a,b)
        _,a,b = best
        for _ in range(3):
            region = ink & (np.abs(xx-cx-a*(yy-cy)-b) < 1.1) & (yy < cy-radius*.05)
            if region.sum() < 5 or np.ptp(yy[region]) < radius*.45:
                return None
            weights = np.sqrt(strength[region])
            a,b = np.linalg.lstsq(np.c_[yy[region]-cy,np.ones(region.sum())]*weights[:,None],
                                  (xx[region]-cx)*weights,rcond=None)[0]
        if not .12 < sign*a < 1 or not .15*radius < sign*b < .9*radius:
            return None
        slopes.extend([a,b])
        roots = np.sort(np.roots([1+a*a,2*a*b,b*b-radius*radius]))
        segments.append([(cx+a*v+b,cy+v) for v in roots])
    distances = [_segment_distance(xx,yy,a,b) for a,b in segments]
    spiral_ink = ink & (np.minimum(*distances) > max(1.1,radius*.055))
    if spiral_ink.sum() < 12:
        return None
    seed = _polar_seed(np.c_[xx[spiral_ink],yy[spiral_ink]],strength[spiral_ink],cx,cy,radius)
    if seed is None:
        return None
    rim = np.median(pixels[(radial > radius*.94) & (radial < radius*1.02)],axis=0)
    stroke = np.median(pixels[ink & (strength >= np.percentile(strength[ink],85))],axis=0)
    border = np.median(np.concatenate([pixels[0],pixels[-1],pixels[:,0],pixels[:,-1]]),axis=0)
    # Disk/rim, two measured line regressions, spiral model, two line widths.
    p = np.r_[np.array([cx,cy,radius-.2,.65,*slopes,*seed,max(.45,radius*.035),max(.45,radius*.04)]),
              fill,rim,stroke,border]

    def chords(p):
        result = []
        for a,b in (p[4:6],p[6:8]):
            roots = np.sort(np.roots([1+a*a,2*a*b,b*b-p[2]**2]))
            result.append([(p[0]+a*v+b,p[1]+v) for v in roots])
        return result

    def valid(p):
        x,y,r,sw = p[:4]
        spiral = p[8:15]
        if not (np.isfinite(p).all() and r > 6 and .1 < sw < r*.15
                and 0 <= x-r-sw/2 and x+r+sw/2 <= width
                and 0 <= y-r-sw/2 and y+r+sw/2 <= height
                and -1 < p[4] < -.1 and .1 < p[6] < 1
                and -r*.9 < p[5] < -r*.1 and r*.1 < p[7] < r*.9
                and 0 < spiral[3] < .4 and spiral[2] < r*1.3
                and 2*np.pi < spiral[5] < 5*np.pi and .7 < spiral[6] < 1.3
                and .1 < min(p[15:17]) <= max(p[15:17]) < r*.15):
            return False
        samples = spiral_points(spiral,np.linspace(0,1,90))
        return np.all(np.linalg.norm(samples-[x,y],axis=1) < r-sw)

    def build(p):
        fill,rim,stroke,bg = p[17:].reshape(-1,3)
        lines = ''.join(f'<line x1="{a[0]:.4f}" y1="{a[1]:.4f}" x2="{b[0]:.4f}" y2="{b[1]:.4f}" '
                        f'stroke="{_hex(stroke)}" stroke-width="{p[15]:.4f}"/>' for a,b in chords(p))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
                f'<rect width="{width}" height="{height}" fill="{_hex(bg)}"/>'
                f'<circle cx="{p[0]:.4f}" cy="{p[1]:.4f}" r="{p[2]:.4f}" fill="{_hex(fill)}" '
                f'stroke="{_hex(rim)}" stroke-width="{p[3]:.4f}"/>{lines}'
                f'<path d="{spiral_path(p[8:15])}" fill="none" stroke="{_hex(stroke)}" '
                f'stroke-width="{p[16]:.4f}" stroke-linecap="round"/></svg>\n')

    scales = np.ones(len(p))
    scales[[4,6,12]] = 1/radius
    scales[13] = .35
    scales[14] = .03
    scales[11] = .01
    result = _register(p/scales,17,lambda q: build(q*scales),lambda q: valid(q*scales),
                       pixels.astype(np.uint8),render_fn,error_fn,'raster_spiral_disk_registration')
    if result is not None:
        result['parameters'] = (np.array(result['parameters'])*scales).tolist()
    if result is None:
        return None
    fitted = result['parameters']
    # Evidence in both directions guards missing chords, gaps and extra marks.
    nearest = cv2.distanceTransform((~ink).astype(np.uint8),cv2.DIST_L2,3)
    curves = [np.linspace(a,b,80) for a,b in chords(fitted)]
    curves.append(spiral_points(fitted[8:15],np.linspace(0,1,200)))
    all_points = np.concatenate(curves)
    for curve in curves:
        curve = curve[np.linalg.norm(curve-[cx,cy],axis=1) < radius*.87]
        ix,iy = np.floor(curve).astype(int).T
        if not len(curve) or np.mean(nearest[iy,ix] <= max(1.1,radius*.04)) < .9:
            return None
    observed = np.c_[xx[ink],yy[ink]]
    residual = np.sqrt(np.min(np.sum((observed[:,None]-all_points[None])**2,axis=2),axis=1))
    explained = residual < max(1.4,radius*.06)
    if np.mean(explained) < .95:
        return None
    # A small connected mark can fit inside the percentage allowance. Reject
    # such an additional object instead of silently discarding its pixels.
    unexplained = np.zeros(ink.shape, dtype=np.uint8)
    unexplained[ink] = (~explained).astype(np.uint8)
    count, _, stats, _ = cv2.connectedComponentsWithStats(unexplained)
    if count > 1 and stats[1:, cv2.CC_STAT_AREA].max() > max(3, radius*.14):
        return None
    return result
