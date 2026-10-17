"""Compare native and separately positioned glyph models for short disk labels."""
from __future__ import annotations

from html import escape
import re
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _image, _register
from src.iCCModules.imageCompositeConverterSearchPortfolio import progress, ranked_models, store_validated_variant
from src.iCCModules.imageCompositeConverterPrimitiveScene import _local_quality


def fit_short_label_disk(width, height, *, description, image, render_fn, error_fn):
    text = str(description or '')
    words = text.casefold()
    labels = re.findall(r'(?:["„])([A-Za-z0-9]{2,4})(?:["“])', text)
    if (len(labels) != 1 or not all(token in words for token in
            ('kreisscheibe', 'einfarbig', 'randkontur', 'serifenlos', 'keine anschlüsse'))
            or any(token in words for token in ('zusätzlich', 'verlauf', 'griff', 'dreieck', 'ohne beschriftung'))):
        return None
    label = escape(labels[0])
    pixels = _image(width, height, image)
    if pixels is None:
        return None
    border = np.concatenate((pixels[0],pixels[-1],pixels[:,0],pixels[:,-1]))
    if np.min(np.median(border,axis=0)) < 245:
        return None
    mask = (np.min(pixels, axis=2) < 210).astype(np.uint8)
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if not contours:
        return None
    outline = max(contours, key=cv2.contourArea)
    x,y,w,h = cv2.boundingRect(outline)
    if not .85 < w/h < 1.18:
        return None
    silhouette = np.zeros_like(mask)
    cv2.drawContours(silhouette, [outline], -1, 1, -1)
    if np.count_nonzero(mask & ~silhouette) > max(2, silhouette.sum()*.005):
        return None
    contour = outline[:,0].astype(float)+.5
    coef = np.linalg.lstsq(np.c_[2*contour,np.ones(len(contour))],(contour**2).sum(axis=1),rcond=None)[0]
    cx,cy = coef[:2]
    radius = float(np.sqrt(max(0,coef[2]+cx*cx+cy*cy)))
    if radius < 5 or np.abs(np.linalg.norm(contour-[cx,cy],axis=1)-radius).mean() > max(.65,radius*.035):
        return None
    yy,xx = np.indices((height,width),dtype=float)
    radial = np.hypot(xx+.5-cx,yy+.5-cy)
    body = pixels[(radial > radius*.66)&(radial < radius*.8)]
    if len(body) < 8:
        return None
    fill = np.median(body,axis=0)
    observed = (np.mean(fill-pixels,axis=2)>45)&(radial<radius*.8)
    ys,xs = np.where(observed)
    if len(xs) < 4:
        return None
    gx,gy,gw,gh = xs.min(),ys.min(),xs.max()-xs.min()+1,ys.max()-ys.min()+1
    if gw > radius*1.65 or gh > radius*1.6:
        return None
    rim = np.percentile(pixels[(radial>radius*.92)&(radial<radius*1.03)],15,axis=0)
    color = np.percentile(pixels[observed],15,axis=0)
    best = None
    attempts = []
    rejected_glyph_models = []

    def prefer(candidate, incumbent):
        if incumbent is None:
            return True
        # Absolute color error can favor a pale fill across the foreground
        # threshold. Prefer an already valid pixel fit before comparing error.
        quality = [_local_quality(np.asarray(image), result['rendered']) for result in (candidate,incumbent)]
        passed = [bool(q and q['passed']) for q in quality]
        return passed[0] if passed[0] != passed[1] else candidate['error'] < incumbent['error']

    def validate_glyphs(fitted, blank, positions=None):
        predicted = (np.mean(blank.astype(float)-fitted['rendered'].astype(float),axis=2)>45)&(radial<radius*.8)
        union = np.count_nonzero(predicted|observed)
        overlap = np.count_nonzero(predicted&observed)/max(1,union)
        distance = cv2.distanceTransform((~observed).astype(np.uint8),cv2.DIST_L2,3)
        exposed = (radial<radius*.85)&~cv2.dilate(observed.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
        accepted = (predicted.any() and overlap>=max(.65,1-3/radius)
                    and distance[predicted].max()<=max(1.5,radius*.035) and exposed.any()
                    and np.percentile(np.max(np.abs(pixels[exposed]-fitted['rendered'][exposed]),axis=1),95)<=25)
        if accepted and positions is not None:
            # Global overlap can hide a capital replacing a lowercase letter.
            # Preserve the observed vertical extent of each individual glyph.
            boundaries = [-np.inf, *((positions[:-1]+positions[1:])/2), np.inf]
            for left,right in zip(boundaries,boundaries[1:]):
                region = (xx>=left)&(xx<right)
                rows = [np.where(mask&region)[0] for mask in (observed,predicted)]
                if (any(not len(row) for row in rows) or
                        max(abs(rows[0].min()-rows[1].min()),abs(rows[0].max()-rows[1].max()))>max(1,radius*.035)):
                    accepted = False
                    break
        return overlap, bool(accepted)

    for separate,weight in ranked_models(((False,400),(False,700),(True,400),(True,700))):
        model = f'{"separate" if separate else "native"}_{weight}'
        progress('short_label_disk',event='model_started',model=model)

        def build(p, blank=False):
            p = np.asarray(p)
            cx,cy,r,sw,tx,ty,size,spacing = p[:8]
            fill,rim,color = p[8:].reshape(-1,3)
            style = f'font-family="Arial" font-weight="{weight}" font-size="{size:.4f}" text-anchor="middle" fill="{_hex(color)}"'
            if separate:
                glyphs = ''.join(f'<text x="{tx+(i-(len(label)-1)/2)*spacing:.4f}" y="{ty:.4f}" {style}>{char}</text>'
                                 for i,char in enumerate(label))
            else:
                glyphs = f'<text x="{tx:.4f}" y="{ty:.4f}" {style}>{label}</text>'
            return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
                    f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                    f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="{_hex(fill)}" stroke="{_hex(rim)}" stroke-width="{sw:.4f}"/>'
                    +('' if blank else glyphs)+'</svg>')

        p = np.r_[cx,cy,radius-.6,max(.5,radius*.08),gx+gw/2,gy+gh,gh*1.35,gw/len(label),fill,rim,color]
        p[2] = min(p[2],cx,width-cx,cy,height-cy)-p[3]/2-1e-4
        for _ in range(3):
            drawn,blank = render_fn(build(p),width,height),render_fn(build(p,True),width,height)
            if drawn is None or blank is None:
                break
            ty,tx = np.where(np.max(np.abs(drawn.astype(float)-blank.astype(float)),axis=2)>45)
            if not len(tx):
                break
            p[4] += gx+gw/2-(tx.min()+tx.max()+1)/2
            p[5] += gy+gh/2-(ty.min()+ty.max()+1)/2
            factor = gh/(ty.max()-ty.min()+1)
            p[6] *= factor
            if separate:
                p[7] *= gw/(tx.max()-tx.min()+1)

        def valid(p):
            cx,cy,r,sw,tx,ty,size,spacing = p[:8]
            return (np.isfinite(p).all() and r>4 and .15<=sw<=r*.25
                    and 0<=cx-r-sw/2 and cx+r+sw/2<=width and 0<=cy-r-sw/2 and cy+r+sw/2<=height
                    and abs(tx-cx)<r*.35 and cy<ty<cy+r*.9 and 3<=size<r*1.9
                    and .5<spacing<r and np.all((p[8:]>=0)&(p[8:]<=255)))

        fitted = _register(p,8,build,valid,np.asarray(image),render_fn,error_fn,'short_label_disk_'+model)
        if fitted is None:
            attempts.append(dict(model=model,accepted=False,reason='invalid_fit'))
            continue
        blank = render_fn(build(fitted['parameters'],True),width,height)
        if blank is None:
            continue
        overlap, accepted = validate_glyphs(fitted, blank)
        attempts.append(dict(model=model,error=fitted['error'],glyph_iou=overlap,accepted=bool(accepted)))
        progress('short_label_disk',event='model_finished',**attempts[-1])
        if accepted:
            store_validated_variant(fitted, image=image, description=text, model=(separate,weight),
                                    quality=_local_quality(np.asarray(image),fitted['rendered']))
        if accepted and prefer(fitted, best):
            best = fitted
        elif separate and not accepted:
            rejected_glyph_models.append((weight, fitted))
    # Keep established successful fits unchanged. Unequal glyph advances and
    # intermediate stroke weights matter at small sizes; explore them only
    # when none of the original four models passes the same silhouette test.
    if best is None:
        for weight, candidate in rejected_glyph_models:
            refined = _refine_glyphs(candidate, width, height, labels[0], weight,
                                     np.asarray(image), render_fn, error_fn)
            if refined is None:
                continue
            fitted, blank = refined
            overlap, accepted = validate_glyphs(fitted, blank,np.asarray(fitted['parameters'][4:4+len(labels[0])]))
            model = f'glyph_offsets_{weight}'
            attempts.append(dict(model=model,error=fitted['error'],glyph_iou=overlap,accepted=accepted))
            progress('short_label_disk',event='model_finished',**attempts[-1])
            if accepted:
                store_validated_variant(fitted, image=image, description=text, model=('glyph_offsets',weight),
                                        quality=_local_quality(np.asarray(image),fitted['rendered']))
                if prefer(fitted, best):
                    best = fitted
    if best:
        best['model_attempts'] = attempts
    return best


def _refine_glyphs(candidate, width, height, label, weight, image, render_fn, error_fn):
    """Refine bounded native glyph positions and stroke weight from a rejected fit."""
    root = ET.fromstring(candidate['svg'])
    texts = [e for e in root.iter() if e.tag.endswith('text')]
    n = len(label)
    if len(texts) != n:
        return None
    base = np.asarray(candidate['parameters'])
    positions = np.array([float(t.get('x')) for t in texts])
    geometry_count = 7+n
    seed = np.r_[base[:4], positions, base[5:7], .2, base[8:]]

    def build(p, blank=False):
        p = np.asarray(p)
        cx,cy,r,sw = p[:4]
        ty,size,stroke = p[4+n:7+n]
        fill,rim,color = p[geometry_count:].reshape(-1,3)
        glyphs = ''.join(f'<text x="{p[4+i]:.4f}" y="{ty:.4f}" font-family="Arial" '
                         f'font-weight="{weight}" font-size="{size:.4f}" text-anchor="middle" '
                         f'fill="{_hex(color)}" stroke="{_hex(color)}" stroke-width="{stroke:.4f}" '
                         f'stroke-linejoin="round">{char}</text>' for i,char in enumerate(label))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" fill="{_hex(fill)}" '
                f'stroke="{_hex(rim)}" stroke-width="{sw:.4f}"/>'
                +('' if blank else glyphs)+'</svg>')

    def valid(p):
        cx,cy,r,sw = p[:4]
        ty,size,stroke = p[4+n:7+n]
        xs = p[4:4+n]
        return (np.isfinite(p).all() and r>4 and .15<=sw<=r*.25
                and 0<=cx-r-sw/2 and cx+r+sw/2<=width and 0<=cy-r-sw/2 and cy+r+sw/2<=height
                and cy<ty<cy+r*.9 and 3<=size<r*1.9 and 0<=stroke<=size*.08
                and np.all(np.diff(xs)>.5) and np.all(np.abs(xs-positions)<=base[7]*.25)
                and np.all((p[geometry_count:]>=0)&(p[geometry_count:]<=255)))

    fitted = _register(seed,geometry_count,build,valid,image,render_fn,error_fn,
                       f'short_label_disk_glyph_offsets_{weight}',initial_error_bound=candidate['error'])
    if fitted is None:
        return None
    blank = render_fn(build(fitted['parameters'], True),width,height)
    return None if blank is None else (fitted,blank)
