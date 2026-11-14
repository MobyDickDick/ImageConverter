"""Layered conversion of a gradient disk and a two-paint organic foreground.

No image identity or saved reference shape participates. Visible disk pixels
fit an unconstrained gradient direction, then color matting extracts the two
foreground paints. Local cubic fits are repeatedly split and welded, rendered
and checked against the input. This is a bounded tracing strategy, deliberately
separate from the analytic primitive reconstructions.
"""
from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality
from src.iCCModules.imageCompositeConverterFilledSymbols import _hex, _register
from src.iCCModules.imageCompositeConverterPiecewiseContours import fit_paint_boundary
from src.iCCModules.imageCompositeConverterPrimitiveScene import _circle


def piecewise_contract(description):
    text = ' '.join(str(description or '').casefold().split())
    # A closed scene contract prevents this tracing fallback from interpreting
    # labels or extra objects as disposable JPEG residue. Paint is pixel fitted.
    return bool(re.fullmatch(
        r'im hintergrund liegt ein kreis mit grauem rand und einem (?:blaugrauen|farbigen) farbverlauf\. '
        r'davor liegt eine (?:'
        r'(?:hellbraune|hellgraue|farbige) hand mit dunkler kontur\. '
        r'daumen und zeigefinger bilden eine (?:fast )?geschlossene schlaufe|'
        r'farbige freiform mit dunkler kontur\. '
        r'die vordergrundform kann öffnungen und schmale ausläufer besitzen)\. '
        r'keine beschriftung oder weiteren zeichen\.', text))


def _plane(pixels, core, cancelled=lambda: False):
    yy, xx = np.indices(pixels.shape[:2], dtype=float)
    h, w = core.shape
    design = np.stack((np.ones_like(xx), (xx+.5)/w, (yy+.5)/h), axis=2)
    a, colors = design[core], pixels[core]
    if len(a) < 40:
        return None
    if len(a) > 8000:
        sample = np.linspace(0, len(a)-1, 8000, dtype=int)
        a, colors = a[sample], colors[sample]
    # Deterministic local RANSAC; background need not be the brightest paint.
    rng = np.random.default_rng(1847)
    best = None
    for _ in range(96):
        if cancelled():
            return None
        sample = rng.choice(len(a), 3, replace=False)
        if abs(np.linalg.det(a[sample])) < .003:
            continue
        model = np.linalg.solve(a[sample], colors[sample])
        residual = np.max(abs(colors-a@model), axis=1)
        score = int((residual < 7).sum())
        if best is None or score > best[0]:
            best = score, model
    if best is None or best[0] < .25*len(a):
        return None
    model = best[1]
    for _ in range(5):
        keep = np.max(abs(colors-a@model), axis=1) < 9
        if keep.sum() < 30:
            return None
        model = np.linalg.lstsq(a[keep], colors[keep], rcond=None)[0]
    return design@model, model


def _matte(pixels, background, paints):
    """Nearest palette edge: background/outline or outline/interior.

    Selecting between these two edges avoids an unstable three-color inverse
    at narrow JPEG boundaries. Return silhouette coverage and fill coverage.
    """
    dark, light = paints
    direction = dark-background
    outer = np.clip(np.sum((pixels-background)*direction, axis=2)
                    /np.maximum(1e-9, np.sum(direction**2, axis=2)), 0, 1)
    outer_error = np.sum((pixels-(background+outer[:, :, None]*direction))**2, axis=2)
    direction = light-dark
    fill = np.clip(np.sum((pixels-dark)*direction, axis=2)/max(1e-9, direction@direction), 0, 1)
    fill_error = np.sum((pixels-(dark+fill[:, :, None]*direction))**2, axis=2)
    inside = fill_error < outer_error
    return np.where(inside, 1., outer), np.where(inside, fill, 0.)


def _topology(alpha):
    mask = (alpha >= .5).astype('uint8')
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return 0, 0
    significant = [i for i, c in enumerate(contours) if cv2.contourArea(c) >= 1.5]
    return (int(sum(hierarchy[0, i, 3] < 0 for i in significant)),
            int(sum(hierarchy[0, i, 3] >= 0 for i in significant)))


def load_piecewise_companions(image_path):
    """Only exact size siblings, never another numbered/color variant."""
    path = Path(image_path)
    match = re.fullmatch(r'(.+)_([LMS])', path.stem, re.IGNORECASE)
    if not match:
        return []
    siblings = []
    for size in ('L', 'M', 'S'):
        if size.casefold() == match[2].casefold():
            continue
        candidate = path.with_name(match[1]+'_'+size+path.suffix)
        image = cv2.imread(str(candidate)) if candidate.is_file() else None
        if image is not None:
            siblings.append((candidate.name, image))
    return siblings


def align_piecewise_companions(image, companions, *, cancelled=lambda: False):
    """Zoom, rotate slightly and translate raster siblings into source space.

    The output-to-input ECC affine is recorded together with the initial
    dimension zoom. A low correlation, excessive deformation or paint change
    rejects a proposed sibling instead of contaminating the source contour.
    """
    h, w = image.shape[:2]
    template = cv2.cvtColor(image.astype('uint8'), cv2.COLOR_BGR2GRAY).astype(np.float32)/255
    aligned, report = [], []
    for name, other in list(companions)[:4]:
        if cancelled():
            break
        other = np.asarray(other)
        if (other.ndim != 3 or other.shape[2] != 3 or min(other.shape[:2]) < 24
                or not np.isfinite(other).all()):
            report.append(dict(name=str(name), accepted=False, reason='invalid_image'))
            continue
        oh, ow = other.shape[:2]
        resized = cv2.resize(other.astype('uint8'), (w, h), interpolation=cv2.INTER_CUBIC)
        moving = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY).astype(np.float32)/255
        warp = np.eye(2, 3, dtype=np.float32)
        try:
            correlation, warp = cv2.findTransformECC(template, moving, warp, cv2.MOTION_AFFINE,
                (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-6), None, 3)
        except cv2.error:
            report.append(dict(name=str(name), accepted=False, reason='registration_failed'))
            continue
        singular = np.linalg.svd(warp[:, :2], compute_uv=False)
        registered = cv2.warpAffine(resized, warp, (w, h),
            flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
        paint_difference = float(np.percentile(np.max(abs(image.astype(float)-registered), axis=2), 75))
        accepted = bool(correlation >= .92 and np.all((singular >= .90) & (singular <= 1.10))
                        and np.linalg.det(warp[:, :2]) > 0
                        and np.max(abs(warp[:, 2])) <= max(3, min(w, h)*.06)
                        and paint_difference <= 12)
        report.append(dict(name=str(name), accepted=accepted, correlation=float(correlation),
            initial_zoom=[w/ow, h/oh], affine=warp.tolist(), paint_difference=paint_difference,
            **({} if accepted else dict(reason='registration_or_paint_mismatch'))))
        if accepted:
            aligned.append(registered)
    return aligned, report


def piecewise_details(image, rendered, background, paints, masks):
    predicted = _matte(rendered.astype(float), background, paints)
    regions = []
    for source, target in zip(masks, predicted):
        a, b = source >= .5, target >= .5
        iou = float((a & b).sum()/max(1, (a | b).sum()))
        regions.append(dict(iou=iou, topology=list(_topology(source)),
                            rendered_topology=list(_topology(target))))
    foreground = masks[0] > .1
    delta = abs(image.astype(float)-rendered.astype(float))
    # Local tiles prevent a missing fingertip being hidden by a large disk.
    worst = 0.
    for y in range(0, image.shape[0], 6):
        for x in range(0, image.shape[1], 6):
            tile = delta[y:y+6, x:x+6]
            if foreground[y:y+6, x:x+6].any():
                worst = max(worst, float(np.mean(tile**2)/255**2))
    return dict(passed=bool(all(r['iou'] >= .92 and r['topology'] == r['rendered_topology']
                               for r in regions) and worst <= .012),
                regions=regions, worst_tile_mse=worst)


def validate_piecewise_refinement(fitted, image, registration, render_fn):
    """A later generic SVG polish must retain the extracted local topology."""
    try:
        root = ET.fromstring(fitted['svg'])
        inventory = [node.tag.rsplit('}', 1)[-1] for node in root.iter()]
        if (inventory.count('circle') != 1 or inventory.count('path') != 2
                or inventory.count('rect') != 1
                or any(tag not in {'svg','defs','linearGradient','stop','g','circle','rect','path'}
                       for tag in inventory)):
            return False
        h, w = image.shape[:2]
        background = render_fn(registration['background_svg'], w, h)
        if background is None:
            return False
        paints = np.array(registration['paints'])
        yy, xx = np.indices((h, w), dtype=float)
        cx, cy, radius = registration['extraction_disk']
        core = np.hypot(xx+.5-cx, yy+.5-cy) < radius-3
        masks = tuple(a*core for a in _matte(image.astype(float), background.astype(float), paints))
        quality = pixel_quality(image, fitted['rendered'])
        return bool(quality and quality['passed'] and
                    piecewise_details(image, fitted['rendered'], background, paints, masks)['passed'])
    except (KeyError, ValueError, TypeError, ET.ParseError):
        return False


def fit_piecewise_scene(width, height, *, description, image, render_fn, error_fn, companion_images=()):
    session = current_search()
    cancelled = lambda: bool(session and session.time_reason())
    arr = np.asarray(image)
    if (not piecewise_contract(description) or arr.shape != (height, width, 3)
            or min(width, height) < 24 or max(width, height) > 2048
            or not np.isfinite(arr).all() or cancelled()):
        return None
    pixels = arr.astype(float)
    border = np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]))
    canvas = np.median(border, axis=0)
    mask = (np.max(abs(pixels-canvas), axis=2) > 23).astype('uint8')
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    center, radius, residual = _circle(contour)
    if radius < 10 or residual > .7 or radius > min(width, height)*.52:
        return None
    yy, xx = np.indices((height, width), dtype=float)
    distance = np.hypot(xx+.5-center[0], yy+.5-center[1])
    core = distance < radius-3
    plane = _plane(pixels, core, cancelled)
    if plane is None or cancelled():
        return None
    background, model = plane
    foreground = core & (np.max(abs(pixels-background), axis=2) > 18)
    if not 25 <= foreground.sum() <= .6*core.sum():
        return None
    # Two paints, estimated without global cv2 RNG state or fixed skin hues.
    colors = pixels[foreground]
    paints = np.percentile(colors, [15, 85], axis=0)
    for _ in range(12):
        labels = np.argmin(np.sum((colors[:, None]-paints)**2, axis=2), axis=1)
        if any((labels == i).sum() < 6 for i in range(2)):
            return None
        paints = np.array([np.median(colors[labels == i], axis=0) for i in range(2)])
    paints = paints[np.argsort(paints.mean(axis=1))]
    if np.linalg.norm(paints[1]-paints[0]) < 18:
        return None
    outer, fill = _matte(pixels, background, paints)
    outer *= core
    fill *= core
    # A foreground crossing the disk rim cannot be safely inferred here.
    if np.any((outer > .5) & (distance > radius-max(3.2, radius*.1))):
        return None
    masks = outer, fill
    visible = (outer < .05) & (distance < radius-3)
    if visible.sum() < 30:
        return None
    _, _, vh = np.linalg.svd(model[1:]/np.array([[width], [height]]), full_matrices=False)
    color_axis = vh[0]
    slope = (model[1:]/np.array([[width], [height]]))@color_axis
    if np.linalg.norm(slope) < .03:
        return None
    direction = slope/np.linalg.norm(slope)
    if direction[1] < 0:
        direction *= -1
    projection = ((xx+.5-center[0])*direction[0]+(yy+.5-center[1])*direction[1])/radius
    design = np.c_[np.ones(visible.sum()), projection[visible]]
    colors = np.linalg.lstsq(design, pixels[visible], rcond=None)[0]
    ring = (distance > radius-.6) & (distance < radius+.3)
    rim = np.median(pixels[ring], axis=0) if ring.any() else np.full(3, 225.)
    parameters = np.r_[center, radius-.7, 1.5, np.arctan2(direction[1], direction[0]),
                       np.clip(colors[0]-colors[1], 0, 255),
                       np.clip(colors[0]+colors[1], 0, 255), rim, canvas]

    def disk(p):
        cx, cy, r, sw, angle = p[:5]
        dx, dy = r*np.cos(angle), r*np.sin(angle)
        return (f'<defs><linearGradient id="piecewiseDisk" gradientUnits="userSpaceOnUse" '
                f'x1="{cx-dx:.5f}" y1="{cy-dy:.5f}" x2="{cx+dx:.5f}" y2="{cy+dy:.5f}">'
                f'<stop offset="0" stop-color="{_hex(p[5:8])}"/>'
                f'<stop offset="1" stop-color="{_hex(p[8:11])}"/></linearGradient></defs>'
                f'<rect width="{width}" height="{height}" fill="{_hex(p[14:17])}"/>'
                f'<circle cx="{cx:.5f}" cy="{cy:.5f}" r="{r:.5f}" '
                f'fill="url(#piecewiseDisk)" stroke="{_hex(p[11:14])}" stroke-width="{sw:.5f}"/>')

    header = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
              f'viewBox="0 0 {width} {height}">')
    outside = outer < .05
    fitted_disk = _register(parameters, 5, lambda p: header+disk(p)+'</svg>',
        lambda p: bool(np.isfinite(p).all() and np.linalg.norm(p[:2]-center) < 2
                       and abs(p[2]-radius) < 2 and .3 <= p[3] <= 4
                       and np.all((p[5:] >= 0) & (p[5:] <= 255))),
        arr, render_fn, error_fn, 'piecewise_disk',
        loss_fn=lambda a, b: np.mean((a[outside].astype(float)-b[outside])**2),
        refinement_steps=(1., .5, .25, .125, .0625), allow_portfolio=False)
    if fitted_disk is None or cancelled():
        return None
    parameters = np.array(fitted_disk['parameters'])
    background_svg = header+disk(parameters)+'</svg>'
    background_raster = fitted_disk['rendered'].astype(float)
    # Re-estimate the matte against the registered background at the boundary.
    masks = _matte(pixels, background_raster, paints)
    masks = tuple(a*core for a in masks)
    aligned, alignment_report = align_piecewise_companions(arr, companion_images, cancelled=cancelled)
    mask_candidates = [('single', masks)]
    if aligned:
        other_masks = [_matte(a.astype(float), background_raster, paints) for a in aligned]
        # The requested source remains the dominant observation. Blending is
        # evaluated as an alternative, never silently replacing its evidence.
        consensus = tuple((.6*mask+.4*np.median([m[i] for m in other_masks], axis=0))*core
                          for i, mask in enumerate(masks))
        if all(_topology(a) == _topology(b) for a, b in zip(masks, consensus)):
            mask_candidates.append(('aligned_consensus', consensus))
    rounds, best = [], None
    evaluations = fitted_disk['evaluations']
    for strategy, candidate_masks in mask_candidates:
        for tolerance in (.65, .4, .25, .16):
            if cancelled():
                break
            paths = [fit_paint_boundary(a, tolerance=tolerance, max_segments=100,
                                       cancelled=cancelled) for a in candidate_masks]
            if any(p is None for p in paths) or sum(p.segments+2*len(p.curves) for p in paths) > 160:
                break
            shapes = ''.join(f'<path d="{p.path()}" fill="{_hex(color)}" '
                             f'fill-rule="evenodd" stroke="none"/>' for p, color in zip(paths, paints))
            svg = header+disk(parameters)+shapes+'</svg>'
            raster = render_fn(svg, width, height)
            evaluations += 1
            if session:
                session.evaluations += 1
            if raster is None or cancelled():
                continue
            quality = pixel_quality(arr, raster)
            details = piecewise_details(arr, raster, background_raster, paints, masks)
            error = float(error_fn(arr, raster))
            record = dict(strategy=strategy, tolerance=tolerance, segments=[p.segments for p in paths],
                          max_fit_error=max(p.max_error for p in paths), error=error,
                          quality=quality, details=details)
            rounds.append(record)
            if session:
                session.observe(error, evaluation=False)
                session.emit(event='piecewise_refinement', **record)
            if quality and quality['passed'] and details['passed'] and (best is None or error < best['error']):
                best = dict(svg=svg, rendered=raster, error=error, quality=quality, details=details,
                            segments=record['segments'], tolerance=tolerance, strategy=strategy)
    if best is None or cancelled():
        return None
    best.update(source='piecewise_scene_v1', initial_error=rounds[0]['error'],
                parameters=parameters.tolist(), evaluations=evaluations, rounds=rounds,
                background_svg=background_svg, paints=paints.tolist(),
                alignment=alignment_report,
                extraction_disk=[float(center[0]), float(center[1]), float(radius)],
                gradient_angle_degrees=float(np.degrees(parameters[4])),
                mask_topology=[list(_topology(a)) for a in masks])
    return best
