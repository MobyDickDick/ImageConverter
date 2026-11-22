"""Align an uploaded assembly and repair bounded frame insets without deleting parts."""
from __future__ import annotations

import copy
import math
import time
import xml.etree.ElementTree as ET

import numpy as np


def orientation_angles(root, width, height, *, mirrored=False):
    """Include exact axis alignments, so strict direction claims can be met."""
    from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform
    from src.iCCModules.imageCompositeConverterRepresentation import path_points
    from src.iCCModules.imageCompositeConverterCanvas import _dimensions, _mapping

    _, _, view = _dimensions(root, width, height)
    ax, ay, _, _ = _mapping(root, width, height, view)
    angles = [0., 90., 180., 270., 45., 135., 225., 315.]
    def add(direction):
        direction = np.array(direction, dtype=float)*[ax, ay]
        if mirrored:
            direction[0] *= -1
        if not np.isfinite(direction).all() or np.linalg.norm(direction) < 1e-9:
            return
        angle = math.degrees(math.atan2(direction[1], direction[0]))
        for axis in (0., 90., 180., 270.):
            value = round((axis-angle) % 360, 8)
            if value not in angles and len(angles) < 72:
                angles.append(value)
    def visit(node, parent=(1., 0., 0., 1., 0., 0.)):
        tag = node.tag.rsplit('}', 1)[-1]
        if tag in {'defs', 'clipPath', 'mask', 'pattern', 'metadata', 'style'}:
            return
        matrix = _compose(parent, _transform(node.get('transform', '')))
        a, b, c, d, _, _ = matrix
        if tag in {'line', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'path'}:
            add([a, b])
            add([c, d])
            paths = path_points(node)
            if tag == 'line':
                paths = [(np.array([[float(node.get('x1', 0)), float(node.get('y1', 0))],
                                    [float(node.get('x2', 0)), float(node.get('y2', 0))]]), False)]
            for points, closed in paths:
                differences = np.diff(np.vstack((points, points[:1])) if closed else points, axis=0)
                for x, y in differences:
                    add([a*x+c*y, b*x+d*y])
        for child in node:
            visit(child, matrix)
    try:
        visit(root)
    except ValueError:
        pass  # Unsupported geometry still receives the bounded coarse search.
    return angles+[float(a) for a in range(15, 360, 15) if a not in angles]


def orient_assembly(root, width, height, *, dx=0., dy=0., sx=1., sy=1., angle=0., mirrored=False):
    """Apply a screen-space pose to all content, retaining its local geometry."""
    from src.imageConverterSample import NUMBER, SVG_NS

    candidate = copy.deepcopy(root)
    vx, vy, vw, vh = map(float, NUMBER.findall(root.get('viewBox')))
    aspect = root.get('preserveAspectRatio', 'xMidYMid meet').split()
    if aspect and aspect[0] == 'defer':
        aspect = aspect[1:]
    ax, ay = width/vw, height/vh
    fx = fy = 0.
    if not aspect or aspect[0] != 'none':
        ax = ay = max(ax, ay) if 'slice' in aspect else min(ax, ay)
        alignment = aspect[0] if aspect else 'xMidYMid'
        fx = 0. if 'xMin' in alignment else 1. if 'xMax' in alignment else .5
        fy = 0. if 'YMin' in alignment else 1. if 'YMax' in alignment else .5
    offset = np.array([-vx*ax+(width-vw*ax)*fx, -vy*ay+(height-vh*ay)*fy])
    center = np.array([width/2, height/2])
    radians = math.radians(angle)
    c, s = math.cos(radians), math.sin(radians)
    rotation = np.array([[c, -s], [s, c]])
    screen = rotation @ np.diag([sx*(-1 if mirrored else 1), sy])
    viewport = np.diag([ax, ay])
    local = np.diag([1/ax, 1/ay]) @ screen @ viewport
    translation = (center+np.array([dx, dy])-screen @ center+(screen-np.eye(2)) @ offset)/[ax, ay]
    a, c, b, d = local.ravel()
    tx, ty = translation
    group = ET.Element(f'{{{SVG_NS}}}g', transform=(
        f'matrix({a:.10f} {b:.10f} {c:.10f} {d:.10f} {tx:.10f} {ty:.10f})'))
    # A root transform belongs to the original assembly, inside the new pose.
    original_transform = candidate.attrib.pop('transform', None)
    content = ET.SubElement(group, f'{{{SVG_NS}}}g', transform=original_transform) if original_transform else group
    first_shape = True
    for child in list(candidate):
        if child.tag.rsplit('}', 1)[-1] not in {'defs', 'style', 'title', 'desc', 'metadata'}:
            # A leading white canvas backing is canvas paint, not motif
            # geometry. Rotating it would create overflow and shrink the fit.
            backdrop = False
            if (first_shape and original_transform is None and child.tag.rsplit('}', 1)[-1] == 'rect'
                    and not child.get('transform') and child.get('fill', '').lower() in {'white', '#fff', '#ffffff'}
                    and child.get('stroke', 'none') == 'none'
                    and child.get('opacity', '1') == child.get('fill-opacity', '1') == '1'):
                try:
                    x, y = (float(child.get(key, '0')) for key in ('x', 'y'))
                    w, h = (float(child.get(key, '0')) for key in ('width', 'height'))
                    backdrop = x <= vx and y <= vy and x+w >= vx+vw and y+h >= vy+vh
                except ValueError:
                    pass
            first_shape = False
            if backdrop:
                continue
            candidate.remove(child)
            content.append(child)
    candidate.append(group)
    return candidate


def compatible_sample_pose(root, width, height, assertions, *, deadline):
    """Check whether orientation alone can satisfy the complete description."""
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions
    for mirrored in (False, True):
        for angle in orientation_angles(root, width, height, mirrored=mirrored):
            if time.monotonic() >= deadline:
                return False
            candidate = orient_assembly(root, width, height, angle=angle, mirrored=mirrored)
            try:
                validate_svg_assertions(ET.tostring(candidate, encoding='unicode'), assertions)
            except ValueError:
                continue
            return True
    return False


def lightened_sample_details(*args,**kwargs):
    """Compatibility for a running older GUI; lighter paint is not a defect.

    Current selection compares independently rendered pixels against the raster
    source instead of assigning a penalty for departing from template shades.
    """
    return []


def framed_surface_variants(root):
    """Offer flush frame edges over a solid backing, retaining every element.

    A raster-derived backing can accidentally show as a second rim when the
    foreground rectangle is inset asymmetrically. These are only proposals:
    the source pixels and description must still approve each adjustment.
    Work in each parent's local coordinates, including grouped templates.
    """
    for parent_index, parent in enumerate(root.iter()):
        children = list(parent)
        for index, (back, front) in enumerate(zip(children, children[1:])):
            if (back.tag.rsplit('}', 1)[-1] != 'rect' or front.tag != back.tag
                    or back.get('transform') or front.get('transform')
                    or back.get('stroke', 'none') != 'none'
                    or back.get('fill', 'black') in {'none', 'transparent'}
                    or back.get('fill', '').startswith('url(')
                    or front.get('stroke', 'none') == 'none'
                    or not front.get('fill', '').startswith('url(')):
                continue
            try:
                bx, by, bw, bh = (float(back.get(k, '0')) for k in ('x', 'y', 'width', 'height'))
                x, y, w, h = (float(front.get(k, '0')) for k in ('x', 'y', 'width', 'height'))
                stroke = float(front.get('stroke-width', '1'))
            except ValueError:
                continue
            gaps = np.array([x-bx, y-by, bx+bw-x-w, by+bh-y-h])-stroke/2
            if (not np.isfinite([bx, by, bw, bh, x, y, w, h, stroke]).all()
                    or not 0 < stroke < min(bw, bh)
                    or np.max(abs(gaps)) > max(2*stroke, 2.)
                    or np.max(abs(gaps)) < 1e-6):
                continue
            for axes in ((0,), (1,), (0, 1)):
                candidate = copy.deepcopy(root)
                rect = list(list(candidate.iter())[parent_index])[index+1]
                if 0 in axes:
                    rect.set('x', f'{bx+stroke/2:.8g}')
                    rect.set('width', f'{bw-stroke:.8g}')
                if 1 in axes:
                    rect.set('y', f'{by+stroke/2:.8g}')
                    rect.set('height', f'{bh-stroke:.8g}')
                if ET.tostring(candidate) != ET.tostring(root):
                    yield candidate


def align_sample(root, target, render_fn, *, deadline, initial, assertions=None, seed=0):
    from src.iCCModules.imageCompositeConverterSearchPortfolio import standalone_image_search
    with standalone_image_search('template_alignment', seconds=max(.001, deadline-time.monotonic()), seed=seed) as session:
        session.bind_reference(target)
        return _align_sample(root, target, render_fn, deadline=deadline, initial=initial, assertions=assertions,
                             seed=session.search_seed)


def _align_sample(root, target, render_fn, *, deadline, initial, assertions=None, seed=0):
    from PIL import ImageColor
    from src.iCCModules.imageCompositeConverterStrokeConstraints import constrain_stroke_width, width_bindings
    from src.iCCModules.imageCompositeConverterSearchPortfolio import proposal_rng
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search, pixel_quality, preferred_quality, vector_quality_score
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import validate_svg_assertions

    height, width = target.shape[:2]
    reference = target.astype(np.float32)
    border = np.concatenate((reference[0], reference[-1], reference[:, 0], reference[:, -1]))
    background = np.median(border, axis=0)
    weights = 1 + 4*(np.max(abs(reference-background), axis=2) > 25)
    nodes = list(root.iter())
    rng = proposal_rng('sample_alignment', ET.tostring(root,encoding='unicode'), seed=seed)
    audit = current_search()
    paints = {}
    for index, node in enumerate(nodes):
        for attribute in ('fill', 'stroke', 'stop-color'):
            try:
                rgb = ImageColor.getrgb(node.get(attribute, ''))
            except ValueError:
                continue
            if len(rgb) == 3:
                paints.setdefault(rgb, []).append((index, attribute))
    palette = list(paints)
    paint_indices, values = [], [0., 0., 100., 100., 0., 1.]
    shared_width = bool(assertions and assertions.get('equal_stroke_width'))
    equal_axes = shared_width or any((assertions or {}).get('objects',{}).get(kind)
                                    for kind in ('square','circle','rhombus'))
    bindings = width_bindings(root) if shared_width else []
    if bindings:
        values.append(bindings[0][2]*bindings[0][3])
    for rgb in palette:
        gray = max(rgb)-min(rgb) <= 2
        paint_indices.append((len(values), gray))
        values.extend([float(np.mean(rgb))] if gray else rgb)
    parameters = np.array(values, dtype=float)

    def build(p, assembly=None):
        candidate = copy.deepcopy(root if assembly is None else assembly)
        elements = list(candidate.iter())
        for rgb, (offset, gray) in zip(palette, paint_indices):
            color = np.repeat(p[offset], 3) if gray else p[offset:offset+3]
            color = '#%02x%02x%02x' % tuple(np.rint(color).astype(int))
            for index, attribute in paints[rgb]:
                elements[index].set(attribute, color)
        candidate = orient_assembly(candidate, width, height, dx=p[0], dy=p[1],
                                    sx=p[2]/100, sy=p[3]/100, angle=p[4], mirrored=p[5] < 0)
        return constrain_stroke_width(ET.tostring(candidate, encoding='unicode'), assertions,
                                      width=p[6] if bindings else None)

    def valid(p):
        if (not np.isfinite(p).all() or not (10 <= p[2] <= 400 and 10 <= p[3] <= 400)
                or abs(p[0]) > width*2 or abs(p[1]) > height*2
                or p[5] not in (-1., 1.)
                or np.any(p[6:] < 0) or np.any(p[6:] > 255)
                or (bindings and p[6] <= 0)
                or (equal_axes and not math.isclose(p[2], p[3], abs_tol=1e-8))):
            return False
        for rgb, (offset, gray) in zip(palette, paint_indices):
            color = np.repeat(p[offset], 3) if gray else p[offset:offset+3]
            contrast = float(np.max(abs(np.array(rgb)-background)))
            # Paint refinement must not hide an existing dark detail in the
            # background to reduce a globally averaged error.
            surface = all(attribute=='fill' and nodes[index].tag.rsplit('}',1)[-1]
                          in {'rect','circle','ellipse','polygon','path'} for index,attribute in paints[rgb])
            if not surface and contrast > 35 and np.max(abs(color-background)) < max(35, contrast*.35):
                return False
        return True

    def measure(pixels):
        squared = np.square(reference-pixels.astype(np.float32)).mean(axis=2)/255**2
        return float((squared*weights).mean()), float(squared.mean())

    best, mse = measure(initial)
    best_quality = pixel_quality(target, initial)
    pixels, svg = initial, ET.tostring(root, encoding='unicode')
    try:
        validate_svg_assertions(svg, assertions)
    except ValueError:
        # An invalid initial orientation must not outrank valid alternatives.
        best = mse = float('inf')
    evaluations = accepted = 0
    cache = {}
    rejected, restarts = 0, 0

    def consider(p, assembly=None):
        nonlocal root, parameters, best, mse, pixels, svg, evaluations, accepted, rejected, best_quality
        if time.monotonic() >= deadline or audit.reason() or not valid(p):
            return False
        try:
            candidate = build(p, assembly)
            key = candidate
            if key in cache:
                return False
            validate_svg_assertions(candidate, assertions)
            raster, fresh = audit.render_candidate(target,candidate,render_fn,width,height)
        except ValueError:
            rejected += 1
            return False
        evaluations += int(fresh)
        if raster is None:
            return False
        loss, error = measure(raster)
        quality = pixel_quality(target, raster)
        audit.measured(candidate, error, source='template_alignment', scope='full_scene', valid=True)
        cache[key] = loss
        # Paint can lower MSE while blurring a rim enough to fail the edge
        # gate. Retain a valid, passing assembly's contour/foreground quality.
        if (math.isfinite(best) and best_quality['passed']
                and (not quality['passed'] or vector_quality_score(quality) > vector_quality_score(best_quality)+1e-12)):
            return False
        if loss < best-1e-10 and error <= mse+1e-12:
            if assembly is not None:
                root = assembly
            parameters, best, mse, pixels, svg = p.copy(), loss, error, raster, candidate
            best_quality = quality
            accepted += 1
            return True
        return False

    frame_adjustments = 0
    for assembly in framed_surface_variants(root):
        frame_adjustments += int(consider(parameters.copy(), assembly))

    # Calibrate paint before geometry can shrink a wrongly colored surface.
    # Black/white renders measure coverage only; final proposals still pass
    # the original detail-contrast guard and the full description validation.
    for rgb,(offset, gray) in zip(palette,paint_indices):
        # Neutral paint already has a single local brightness coordinate.
        # Reserve the early analytic stage for chromatic filled surfaces;
        # fitting rims/gradient stops before pose would absorb geometry errors.
        surface = all(attribute=='fill' and nodes[index].tag.rsplit('}',1)[-1]
                      in {'rect','circle','ellipse','polygon','path'} for index,attribute in paints[rgb])
        if gray or not surface:
            continue
        if time.monotonic() >= deadline:
            break
        anchor = parameters.copy()
        probes = []
        for value in (0.,255.):
            probe = anchor.copy()
            probe[offset:offset+(1 if gray else 3)] = value
            try:
                candidate = build(probe)
                validate_svg_assertions(candidate,assertions)
                raster,fresh = audit.render_candidate(target,candidate,render_fn,width,height)
            except ValueError:
                rejected += 1
                probes = []
                break
            evaluations += int(fresh)
            if raster is None:
                probes = []
                break
            probes.append(raster.astype(float))
        if len(probes)!=2:
            continue
        black,white = probes
        alpha = (white-black)/255.
        denominator = np.square(alpha).sum(axis=(0,1))
        if denominator.min()<.1:
            continue
        numerator = (alpha*(reference-black)).sum(axis=(0,1))
        color = numerator.sum()/denominator.sum() if gray else numerator/denominator
        anchor[offset:offset+(1 if gray else 3)] = np.clip(color,0,255)
        consider(anchor)

    def bounds(image):
        contrast = np.max(abs(image.astype(float)-background), axis=2)
        ys, xs = np.where(contrast > 35)
        if not len(xs):
            return None
        return np.array([xs.min(), ys.min(), xs.max()+1, ys.max()+1], dtype=float)

    observed, predicted = bounds(target), bounds(initial)
    if observed is not None and predicted is not None:
        sizes = (observed[2:]-observed[:2])/(predicted[2:]-predicted[:2])
        for sx, sy in [(1., 1.), (float(np.mean(sizes)),)*2, tuple(sizes),
                       *[(s, s) for s in (.25, .5, .75, .9, 1.1, 1.5, 2.)]]:
            p = np.array(values, dtype=float)
            if equal_axes:
                sx = sy = (sx+sy)/2
            scales = np.array([sx, sy])
            p[2:4] = scales*100
            p[:2] = ((observed[:2]+observed[2:])/2
                     - (np.array([width, height])/2
                        + ((predicted[:2]+predicted[2:])/2-np.array([width, height])/2)*scales))
            consider(p)
    # Search rotations and reflections before local fitting. Foreground pixel
    # centers provide pose-dependent bounds without rendering clipped probes.
    # Rotation plus one reflection covers both horizontal and vertical mirrors.
    if observed is not None and predicted is not None and (not math.isfinite(best) or not preferred_quality(pixel_quality(target, initial))):
        ys, xs = np.where(np.max(abs(initial.astype(float)-background), axis=2) > 35)
        center = np.array([width/2, height/2])
        points = np.column_stack((xs+.5, ys+.5))-center
        anchor = np.array(values, dtype=float)
        for mirrored in (False, True):
            for angle in orientation_angles(root, width, height, mirrored=mirrored):
                if time.monotonic() >= deadline or audit.reason() or mse <= 1e-12:
                    break
                radians = math.radians(angle)
                c, s = math.cos(radians), math.sin(radians)
                rotation = np.array([[c, -s], [s, c]])
                oriented = points @ (rotation @ np.diag([-1 if mirrored else 1, 1])).T
                lo, hi = oriented.min(axis=0)-.5, oriented.max(axis=0)+.5
                sizes = (observed[2:]-observed[:2])/(hi-lo)
                # Uniform scaling preserves right angles, circles and symbols.
                scale = float(np.mean(sizes))
                probe = anchor.copy()
                probe[2:6] = [scale*100, scale*100, angle, -1 if mirrored else 1]
                probe[:2] = (observed[:2]+observed[2:])/2-center-(lo+hi)/2*scale
                consider(probe)
    # Correlated jumps explore another placement/scale even when no individual
    # coordinate improves. Keep exact, already passing assemblies untouched.
    if not pixel_quality(target,pixels)['passed']:
        anchor = parameters.copy()
        for _ in range(8):
            if time.monotonic() >= deadline:
                break
            probe = anchor.copy()
            probe[:2] += np.array([rng.uniform(-.15,.15)*width,rng.uniform(-.15,.15)*height])
            probe[2:4] *= rng.uniform(.7,1.3)
            consider(probe)
            restarts += 1
    # Alternate common geometry with shared paint. Individual paths, polygon
    # vertices, opacities and small-symbol dimensions are never edited here.
    for step, paint_step, angle_step in [(2., 32., 7.5), (1., 16., 3.), (.5, 8., 1.5),
                                       (.25, 4., .5), (.125, 2., .125), (.0625, 1., .03125)]:
        steps = [step, step, 100*step/width, 100*step/height, angle_step, 0.] + ([step] if bindings else [])
        steps += [paint_step]*(len(values)-len(steps))
        for _ in range(4):
            changed = False
            order = list(enumerate(steps))
            rng.shuffle(order)
            signs = [-1,1]
            rng.shuffle(signs)
            for index, delta in order:
                if index == 5 or (equal_axes and index == 3):
                    continue
                for sign in signs:
                    candidate = parameters.copy()
                    candidate[index] += sign*delta
                    if equal_axes and index == 2:
                        candidate[3] = candidate[2]
                    changed = consider(candidate) or changed
                if time.monotonic() >= deadline:
                    break
            if not changed or time.monotonic() >= deadline:
                break
        if time.monotonic() >= deadline:
            break
    return dict(svg=svg, rendered=pixels, error=mse, weighted_error=best,
                evaluations=evaluations, accepted=accepted,
                search_control=dict(seed=str(seed),restarts=restarts,rejected_candidates=rejected,
                    frame_adjustments=frame_adjustments,
                    **audit.report(),scope='whole_assembly',
                    stop_reason=('quality_target_reached' if pixel_quality(target,pixels)['passed'] else
                                 audit.reason() or ('time_limit' if time.monotonic()>=deadline else 'schedule_exhausted'))),
                transform=dict(translate_x=float(parameters[0]), translate_y=float(parameters[1]),
                               scale_x=float(parameters[2]/100), scale_y=float(parameters[3]/100),
                               rotation_degrees=float(parameters[4] % 360), mirrored=bool(parameters[5] < 0),
                               mirror_axis='x' if parameters[5] < 0 else None))
