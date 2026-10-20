"""Bounded fusion of complete boundaries and partially visible native shapes.

Only observed arcs/edges establish geometry. Hidden sides, reference vectors and
file names are never used. All painter orders compete through the shared fitter.
"""
from __future__ import annotations

import itertools
import re

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterAdaptiveSearch import current_search


def fusion_contract(description):
    from src.iCCModules.imageCompositeConverterLayeredScene import scene_contract
    text = str(description or '').casefold()
    overlap = re.search(r'überlapp\w*|überdeck\w*', text)
    if not overlap:
        return scene_contract(text)
    if not re.search(r'teilweise|partiell', text):
        return None
    if re.search(r'(?:kein\w*|ohne|nicht)\s+(?:(?:auf|vor)\s+)?(?:einem\s+)?weiss\w*\s+hintergrund', text):
        return None
    # A white canvas declaration is not an object-depth constraint.
    text = re.sub(r'\b(?:(?:auf|vor)\s+(?:einem\s+)?)?weiss\w*\s+hintergrund\b', '', text)
    if re.search(r'vordergrund|hintergrund|vorne|hinten|davor|dahinter|\bhinter\b|\bvor\b', text):
        return None  # Typed language-to-painter-order constraints are not modelled.
    if re.search(r'kontur|umriss|rand', text):
        return None  # Occluded outlines require a separate visibility model.
    if re.search(r'(?:nicht|kein\w*|ohne)\s+(?:\w+\s+){0,2}(?:überlapp\w*|überdeck\w*)', text):
        return None
    if re.search(r'(?:überlapp\w*|überdeck\w*)\s+(?:sich\s+)?(?:nicht|kein\w*)', text):
        return None
    # A separate third object may coexist with an overlapping pair. This exact
    # clause carries no claim that *every* pair must be disjoint.
    separate_instance = 'eine form liegt getrennt.' in text
    text = text.replace('eine form liegt getrennt.', '')
    text = re.sub(r'überlapp\w*|überdeck\w*', '', text)
    contract = scene_contract(text)
    if contract is None or contract['nested'] or contract['separate'] or not contract['filled']:
        return None
    if sum(contract['counts'].values()) < 2:
        return None
    if separate_instance and sum(contract['counts'].values()) != 3:
        return None
    return dict(contract, overlap=True, separate_instance=separate_instance)


def _arc(contour, shape):
    """Deterministic robust circle proposals; straight occlusion edges are outliers."""
    points = contour[:, 0].astype(float)+.5
    points = points[np.linspace(0, len(points)-1, min(96, len(points))).astype(int)]
    if len(points) < 12:
        return None
    rng = np.random.default_rng(0)
    best = None
    for _ in range(128):
        three = points[rng.choice(len(points), 3, replace=False)]
        matrix = 2*(three[1:]-three[0])
        if abs(np.linalg.det(matrix)) < 4:
            continue
        center = np.linalg.solve(matrix, (three[1:]**2).sum(axis=1)-(three[0]**2).sum())
        radius = np.linalg.norm(three[0]-center)
        if not 5 <= radius <= min(shape)/2 or np.any(center-radius < 1) or np.any(center+radius > np.array(shape[::-1])-1):
            continue
        residual = abs(np.linalg.norm(points-center, axis=1)-radius)
        inliers = residual < .8
        score = (int(inliers.sum()), -float(residual[inliers].mean()))
        if best is None or score > best[0]:
            best = score, inliers
    if best is None or best[0][0] < len(points)*.50:
        return None
    selected = points[best[1]]
    coefficients = np.linalg.lstsq(np.c_[2*selected, np.ones(len(selected))],
                                  (selected**2).sum(axis=1), rcond=None)[0]
    center = coefficients[:2]
    radius = np.sqrt(max(0., coefficients[2]+(center**2).sum()))
    angles = np.sort(np.arctan2(selected[:, 1]-center[1], selected[:, 0]-center[0]))
    coverage = 2*np.pi-np.diff(np.r_[angles, angles[0]+2*np.pi]).max()
    if coverage < np.pi or abs(np.linalg.norm(selected-center, axis=1)-radius).mean() > .5:
        return None
    radius += .3  # Pixel-center contours lie inside the antialiased boundary.
    return [center[0]-radius, center[1]-radius, 2*radius, 2*radius, 0.]


def visible_candidates(pixels):
    """Color components supply distinct instances; arcs and edges supply alternatives."""
    foreground = np.max(255-pixels.astype(float), axis=2) > 25
    values = pixels[foreground]
    if len(values) < 12:
        return []
    bins, counts = np.unique(values.astype(int)//16, axis=0, return_counts=True)
    proposals = []
    used_colors = []
    for index in np.argsort(-counts, kind='stable')[:16]:
        session = current_search()
        if session and session.time_reason():
            break
        if counts[index] < 20:
            continue
        color = np.median(values[np.all(values.astype(int)//16 == bins[index], axis=1)], axis=0)
        if any(np.max(abs(color-old)) <= 12 for old in used_colors):
            continue
        used_colors.append(color)
        mask = (np.max(abs(pixels.astype(float)-color), axis=2) <= 12).astype('uint8')
        number, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
        for label in range(1, number):
            x, y, w, h, area = stats[label]
            if area < 20 or min(w, h) < 7 or x < 2 or y < 2 or x+w > pixels.shape[1]-2 or y+h > pixels.shape[0]-2:
                continue
            component = (labels == label).astype('uint8')
            # Rings are owned by the complete contour detector. A solid color
            # proposal must have a genuinely filled core, never a thin outline.
            if cv2.distanceTransform(component, cv2.DIST_L2, 3).max() < 2.5:
                continue
            contour = max(cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
            geometries = []
            circle = _arc(contour, pixels.shape[:2])
            if circle is not None:
                cx, cy = circle[0]+circle[2]/2, circle[1]+circle[2]/2
                yy, xx = np.where(component)
                if np.mean(np.hypot(xx+.5-cx, yy+.5-cy) <= circle[2]/2+1) >= .995:
                    geometries.append(('circle', circle, 'visible_arc'))
            # All four sides must retain visible support. Do not infer a fully
            # hidden right edge from the size of some other object.
            # Exposed *exterior* support distinguishes a true side from an
            # occluder's cut edge; a wholly hidden extent remains unknown.
            exterior = ~foreground
            sides = [np.count_nonzero(component[y:y+h, x] & exterior[y:y+h, x-2]),
                     np.count_nonzero(component[y:y+h, x+w-1] & exterior[y:y+h, x+w+1]),
                     np.count_nonzero(component[y, x:x+w] & exterior[y-2, x:x+w]),
                     np.count_nonzero(component[y+h-1, x:x+w] & exterior[y+h+1, x:x+w])]
            if min(sides[:2]) >= max(5, h*.18) and min(sides[2:]) >= max(5, w*.18):
                geometries.append(('rectangle', [float(x), float(y), float(w), float(h), 0.], 'visible_sides'))
            for kind, geometry, detector in geometries:
                proposals.append(dict(kind=kind, geometry=geometry, fill=color, stroke=color,
                                      detectors=[detector]))
    return proposals


def fuse_candidates(pixels):
    from src.iCCModules.imageCompositeConverterLayeredScene import detect_instances, _box
    complete = detect_instances(pixels)
    proposals = [dict(c, detectors=['complete_boundary']) for group in complete for c in group]
    proposals.extend(visible_candidates(pixels))
    groups = []
    for candidate in proposals:
        group = next((g for g in groups if np.max(abs(_box(g[0])-_box(candidate))) <= 3), None)
        if group is None:
            groups.append([candidate])
            continue
        same = next((c for c in group if c['kind'] == candidate['kind']
                     and bool(c['geometry'][4]) == bool(candidate['geometry'][4])
                     and (c['fill'] is None) == (candidate['fill'] is None)
                     and np.max(abs(c['stroke']-candidate['stroke'])) <= 12
                     and (c['fill'] is None or np.max(abs(c['fill']-candidate['fill'])) <= 12)), None)
        if same is None:
            group.append(candidate)
        else:
            same['detectors'] = sorted(set(same['detectors']+candidate['detectors']))
    return groups


def compatible(scene, contract):
    from src.iCCModules.imageCompositeConverterLayeredScene import _compatible, _box
    if not contract.get('overlap'):
        return _compatible(scene, contract)
    if any(sum(c['kind'] == kind for c in scene) != n for kind, n in contract['counts'].items()):
        return False
    if any(c['fill'] is None or c['geometry'][4] for c in scene):
        return False  # Partial outlined objects need a separate visibility model.

    def contained(parent, child):
        # Unlike strict *nesting* with a visible gap, partial overlap must also
        # exclude containment that touches an inner boundary. Keep a one-pixel
        # uncertainty band rather than asserting an unseen protrusion.
        bp, bc = _box(parent), _box(child)
        if parent['kind'] == 'rectangle':
            return np.all(bc[:2] >= bp[:2]-1) and np.all(bc[2:] <= bp[2:]+1)
        center, radius = (bp[:2]+bp[2:])/2, (bp[2]-bp[0])/2
        if child['kind'] == 'circle':
            return np.linalg.norm((bc[:2]+bc[2:])/2-center)+(bc[2]-bc[0])/2 <= radius+1
        return all(np.linalg.norm(np.array([x, y])-center) <= radius+1
                   for x in (bc[0], bc[2]) for y in (bc[1], bc[3]))

    overlaps = 0
    for a, b in itertools.combinations(scene, 2):
        if contained(a, b) or contained(b, a):
            return False
        ba, bb = _box(a), _box(b)
        if not np.all(np.minimum(ba[2:], bb[2:])-np.maximum(ba[:2], bb[:2]) > 1):
            continue
        if a['kind'] == b['kind'] == 'rectangle':
            overlaps += 1
        elif a['kind'] == b['kind'] == 'circle':
            distance = np.linalg.norm((ba[:2]+ba[2:]-bb[:2]-bb[2:])/2)
            overlaps += distance < (ba[2]-ba[0]+bb[2]-bb[0])/2-1
        else:
            circle, rectangle = (a, b) if a['kind'] == 'circle' else (b, a)
            bc, br = _box(circle), _box(rectangle)
            center = (bc[:2]+bc[2:])/2
            nearest = np.clip(center, br[:2], br[2:])
            overlaps += np.linalg.norm(center-nearest) < (bc[2]-bc[0])/2-1
    return overlaps > 0 and (not contract.get('separate_instance') or overlaps == 1)


def fit_fused_scene(width, height, *, description, image, render_fn, error_fn):
    from src.iCCModules.imageCompositeConverterLayeredScene import fit_scene_groups
    contract = fusion_contract(description)
    if contract is None:
        return None
    pixels = np.asarray(image)
    if pixels.shape != (height, width, 3) or min(width, height) < 16 or not np.isfinite(pixels).all():
        return None
    border = np.concatenate([pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]])
    if np.max(abs(border.astype(float)-255)) > 3:
        return None
    groups = fuse_candidates(pixels)
    return fit_scene_groups(width, height, image=pixels, groups=groups, contract=contract,
        render_fn=render_fn, error_fn=error_fn, compatible_fn=compatible,
        all_orders=bool(contract.get('overlap')), source='primitive_fused_scene_v1')
