"""Register an analytic gabled house, door and cross-window on a gradient disk."""
from __future__ import annotations

import re
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register


def fit_house_disk(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '').casefold()
    if not all(word in text for word in ('kreis', 'vertikal', 'verlauf', 'haus', 'satteldach',
                                         'dachüberst', 'fassade', 'tür', 'fenster', 'kreuz', 'links', 'rechts')):
        return None
    if re.search(r'\b(?:ohne|kein|keine|nicht|zwei|zusätzlich|diagonal|schriftzeichen)\b',
                 text.replace('keine schriftzeichen', '')):
        return None
    if 'links in der fassade' not in text or 'rechts ein' not in text:
        return None
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    mask = (np.min(pixels, axis=2) < 235).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if count < 2:
        return None
    index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = stats[index]
    if not (.85 < w/h < 1.18 and area > .65*w*h):
        return None
    if sum(stats[i, cv2.CC_STAT_AREA] for i in range(1, count) if i != index) > max(3, area*.001):
        return None
    contour = cv2.findContours((labels == index).astype(np.uint8), cv2.RETR_EXTERNAL,
                              cv2.CHAIN_APPROX_NONE)[0][0][:, 0].astype(float)+.5
    coefficients = np.linalg.lstsq(np.c_[2*contour, np.ones(len(contour))],
                                   np.sum(contour**2, axis=1), rcond=None)[0]
    cx, cy = coefficients[:2]
    radius = float(np.sqrt(max(0., coefficients[2]+cx*cx+cy*cy)))
    if radius < 10 or np.mean(np.abs(np.linalg.norm(contour-[cx, cy], axis=1)-radius)) > max(.7, radius*.04):
        return None
    yy, xx = np.indices((height, width), dtype=float)
    distance = np.hypot(xx+.5-cx, yy+.5-cy)
    t = (yy+.5-(cy-radius))/(2*radius)
    # Robust regression removes foreground samples without assuming a palette.
    exposed = (distance < radius*.88)
    for _ in range(5):
        if exposed.sum() < 20:
            return None
        colors = np.linalg.lstsq(np.c_[1-t[exposed], t[exposed]], pixels[exposed], rcond=None)[0]
        field = (1-t[..., None])*colors[0]+t[..., None]*colors[1]
        residual = np.max(np.abs(pixels-field), axis=2)
        cutoff = max(12., float(np.percentile(residual[exposed], 65)))
        exposed &= residual < cutoff
    if np.max(np.abs(colors[0]-colors[1])) < 8:
        return None
    contrast = (np.max(np.abs(pixels-field), axis=2) > 48) & (distance < radius*.93)
    count, house_labels, house_stats, _ = cv2.connectedComponentsWithStats(contrast.astype(np.uint8))
    if count < 2:
        return None
    index = 1+int(np.argmax(house_stats[1:, cv2.CC_STAT_AREA]))
    hx, hy, hw, hh, house_area = house_stats[index]
    house = house_labels == index
    # Scanline extrema regress straight roof edges and vertical wall edges;
    # the emitted seven-corner polygon is their analytic intersection model.
    rows = np.arange(hy, hy+hh)
    left = np.array([np.flatnonzero(house[row])[0]+.5 for row in rows])
    right = np.array([np.flatnonzero(house[row])[-1]+.5 for row in rows])
    widths = right-left
    eave_index = int(np.argmax(widths))
    if not (4 <= eave_index <= hh*.65 and hh-eave_index >= 8):
        return None
    fit_rows = slice(1, eave_index)
    if eave_index < 5:
        return None
    a, b = np.polyfit(rows[fit_rows]+.5, left[fit_rows], 1)
    c, d = np.polyfit(rows[fit_rows]+.5, right[fit_rows], 1)
    if not (a < -.3 and c > .3):
        return None
    roof_residual = np.r_[np.abs(a*(rows[fit_rows]+.5)+b-left[fit_rows]),
                          np.abs(c*(rows[fit_rows]+.5)+d-right[fit_rows])]
    if np.percentile(roof_residual,90) > max(1., radius*.03):
        return None
    apex_y = (d-b)/(a-c)
    apex_x = a*apex_y+b
    eave_y = rows[eave_index]+.8
    roof_left, roof_right = a*eave_y+b, c*eave_y+d
    wall_rows = slice(eave_index+3, None)
    wall_left, wall_right = np.median(left[wall_rows])-.5, np.median(right[wall_rows])+.5
    bottom = hy+hh
    if not (roof_left < wall_left < apex_x < wall_right < roof_right):
        return None
    core = cv2.erode(house.astype(np.uint8), np.ones((3,3),np.uint8)).astype(bool)
    if core.sum() < 10:
        return None
    house_color = np.median(pixels[core], axis=0)
    roof_core = ((yy > hy+2) & (yy < eave_y-2)
                 & (xx > a*(yy+.5)+b+2) & (xx < c*(yy+.5)+d-2))
    if roof_core.any() and np.mean(np.max(np.abs(pixels[roof_core]-house_color),axis=1) > 35) > .025:
        return None
    # The five light components are the door and four window panes. They are
    # measured only inside the facade, leaving roof/disk highlights separate.
    interior = ((xx >= wall_left+1) & (xx < wall_right-1)
                & (yy >= eave_y+1) & (yy < bottom-1))
    light = (pixels.mean(axis=2) > house_color.mean()+.5*(255-house_color.mean())) & interior
    count, holes, hole_stats, _ = cv2.connectedComponentsWithStats(light.astype(np.uint8))
    components = [i for i in range(1,count) if hole_stats[i,4] >= max(3,house_area*.003)]
    if len(components) != 5:
        return None
    door = max(components, key=lambda i: hole_stats[i,3])
    dx, dy, dw, dh, da = hole_stats[door]
    panes = [i for i in components if i != door]
    wx = min(hole_stats[i,0] for i in panes)
    wy = min(hole_stats[i,1] for i in panes)
    ww = max(hole_stats[i,0]+hole_stats[i,2] for i in panes)-wx
    wh = max(hole_stats[i,1]+hole_stats[i,3] for i in panes)-wy
    if not (dh > dw >= 3 and da > dw*dh*.85 and dx+dw < wx and min(ww,wh) >= 5):
        return None
    if any(hole_stats[i,4] < .8*hole_stats[i,2]*hole_stats[i,3] for i in panes):
        return None
    pane_mask = np.isin(holes,panes)[wy:wy+wh, wx:wx+ww]
    horizontal = np.flatnonzero(pane_mask.sum(axis=1) < ww*.3)
    vertical = np.flatnonzero(pane_mask.sum(axis=0) < wh*.3)
    if not (len(horizontal) and len(vertical)
            and np.all(np.diff(horizontal)==1) and np.all(np.diff(vertical)==1)):
        return None
    cross_x, cross_y = wx+vertical[0], wy+horizontal[0]
    cross_w, cross_h = len(vertical), len(horizontal)
    light_color = np.median(pixels[np.isin(holes,components)],axis=0)
    rim = np.median(pixels[(distance > radius*.94) & (distance < radius*1.01)],axis=0)
    p = np.r_[cx,cy,radius-.3,1.,apex_x,apex_y,roof_left,roof_right,eave_y,
              wall_left,wall_right,bottom,.5,dx,dy,dw,dh,wx,wy,ww,wh,cross_x,cross_y,cross_w,cross_h,
              colors.ravel(),rim,house_color,light_color]

    def build(p):
        cx,cy,r,sw,ax,ay,rl,rr,ey,wl,wr,by,hs,dx,dy,dw,dh,wx,wy,ww,wh,kx,ky,kw,kh = p[:25]
        top,base,rim,color,light = p[25:].reshape(-1,3)
        path = f'M {rl:.4f} {ey:.4f} L {ax:.4f} {ay:.4f} L {rr:.4f} {ey:.4f} L {wr:.4f} {ey:.4f} L {wr:.4f} {by:.4f} L {wl:.4f} {by:.4f} L {wl:.4f} {ey:.4f} Z'
        rectangles = ''.join(f'<rect x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}" fill="{fill}"/>'
                             for x,y,w,h,fill in ((dx,dy,dw,dh,_hex(light)),(wx,wy,ww,wh,_hex(light)),
                                                  (kx,wy,kw,wh,_hex(color)),(wx,ky,ww,kh,_hex(color))))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                '<defs><linearGradient id="disk_color" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{_hex(top)}"/><stop offset="1" stop-color="{_hex(base)}"/>'
                '</linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="url(#disk_color)" stroke="{_hex(rim)}" stroke-width="{sw:.4f}"/>'
                f'<path d="{path}" fill="{_hex(color)}" stroke="{_hex(rim)}" stroke-width="{hs:.4f}" stroke-linejoin="round"/>'
                +rectangles+'</svg>\n')

    def valid(p):
        cx,cy,r,sw,ax,ay,rl,rr,ey,wl,wr,by,hs,dx,dy,dw,dh,wx,wy,ww,wh,kx,ky,kw,kh = p[:25]
        return (np.isfinite(p).all() and r > 7 and .1 <= sw <= 3 and 0 <= hs <= 2
                and 0 <= cx-r-sw/2 and cx+r+sw/2 <= width
                and 0 <= cy-r-sw/2 and cy+r+sw/2 <= height
                and rl < wl < ax < wr < rr and ay < ey < by
                and wl < dx < dx+dw < wx < wx+ww < wr and ey < min(dy,wy)
                and dy+dh < by and wy+wh < by and dh > dw > 1 and min(ww,wh) > 3
                and wx < kx < kx+kw < wx+ww and wy < ky < ky+kh < wy+wh and min(kw,kh) > .2
                and all((px-cx)**2+(py-cy)**2 < (r-sw)**2
                        for px,py in ((ax,ay),(rl,ey),(rr,ey),(wl,by),(wr,by))))

    result = _register(p,25,build,valid,pixels.astype(np.uint8),render_fn,error_fn,
                       'raster_house_disk_registration')
    if result is None:
        return None
    # Registration must explain all interior regions, including missing or
    # additional marks. A clean average cannot hide a different topology.
    difference = np.max(np.abs(pixels-np.asarray(result['rendered'],dtype=float)),axis=2)
    if np.mean(difference[distance < radius*.88] > 40) > .035:
        return None
    unexplained = cv2.erode((difference > 40).astype(np.uint8),np.ones((3,3),np.uint8))
    if np.count_nonzero(unexplained) > max(2,area*.0005):
        return None
    return result
