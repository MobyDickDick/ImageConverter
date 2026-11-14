"""Bounded atomic edits of observed native groups in an existing SVG scene."""
from __future__ import annotations

import copy
from xml.etree import ElementTree as ET

import numpy as np
import cv2

from src.iCCModules.imageCompositeConverterFallbackGroups import NS, part_regions

DRAWABLE = {'rect', 'circle', 'ellipse', 'line', 'polygon', 'polyline', 'path', 'text'}


def residual_line_owner(svg, line):
    """Identify a proposed line retracing an existing native group edge.

    Raster registration errors on an outline are parameter errors, not evidence
    for another logical line. Require both near parallelism and 90% longitudinal
    overlap with one actual edge; merely crossing a group or sharing its bounds
    never suffices. This only prunes additions, and grants no scene acceptance.
    Styled/transformed/effected subtrees have no inferred viewport ownership.
    """
    point = lambda node, suffix: np.array([float(node.get('x'+suffix)), float(node.get('y'+suffix))])
    a, b = point(line, '1'), point(line, '2')
    length = np.linalg.norm(b-a)
    if length < 1 or not np.isfinite(length):
        return None
    direction = (b-a)/length
    samples = a + np.linspace(0, 1, min(1025, int(length*2)+2))[:, None]*(b-a)
    proposed_width = float(line.get('stroke-width', '1'))
    unsupported = {'transform', 'style', 'clip-path', 'mask', 'filter', 'opacity',
                   'stroke', 'stroke-width', 'stroke-opacity', 'fill-opacity',
                   'stroke-dasharray', 'vector-effect', 'display', 'visibility'}

    def walk(node, group=None):
        tag = node.tag.rsplit('}', 1)[-1]
        if tag not in {'svg', 'g', 'line', 'rect', 'polygon'}:
            return
        effects = unsupported if tag in {'svg', 'g'} else unsupported-{'stroke', 'stroke-width'}
        if any(key in node.attrib for key in effects):
            return
        group = node.get('data-fallback-group', group)
        if group and tag in {'line', 'rect', 'polygon'}:
            edges = []
            if tag == 'line' and node.get('stroke', 'none') != 'none':
                edges = [(point(node, '1'), point(node, '2'))]
            elif tag == 'rect' and node.get('stroke', 'none') != 'none' and not (node.get('rx') or node.get('ry')):
                x, y = float(node.get('x', '0')), float(node.get('y', '0'))
                w, h = float(node.get('width')), float(node.get('height'))
                corners = np.array([[x,y],[x+w,y],[x+w,y+h],[x,y+h]])
                edges = list(zip(corners, np.roll(corners, -1, axis=0)))
            elif tag == 'polygon':
                # A filled arrow head owns its boundary even without a stroke.
                corners = np.array([list(map(float, p.split(','))) for p in node.get('points', '').split()])
                if len(corners) >= 3 and node.get('fill', 'black') != 'none':
                    edges = list(zip(corners, np.roll(corners, -1, axis=0)))
            width = float(node.get('stroke-width', '1')) if node.get('stroke', 'none') != 'none' else 0.
            for p, q in edges:
                axis = q-p
                span = np.linalg.norm(axis)
                if span < 1 or abs(direction[0]*axis[1]-direction[1]*axis[0])/span > .12:
                    continue
                t = np.clip((samples-p) @ axis / span**2, 0, 1)
                distance = np.linalg.norm(samples-(p+t[:, None]*axis), axis=1)
                # Half-pixel allowance accounts for raster-centre registration;
                # stroke extents supply the remaining geometric neighbourhood.
                coverage = float((distance <= (width+proposed_width)/2+.5).mean())
                if coverage >= .9:
                    yield dict(group=group, primitive=tag, part=node.get('data-part'),
                               coverage=coverage, edge=[p.tolist(), q.tolist()])
        for child in node:
            if child.tag.rsplit('}', 1)[-1] != 'svg':
                yield from walk(child, group)

    try:
        root = ET.fromstring(svg)
        if root.get('viewBox'):
            viewport = [float(v) for v in root.get('viewBox').replace(',', ' ').split()]
            if viewport != [0., 0., float(root.get('width')), float(root.get('height'))]:
                return None
        if float(root.get('x', '0')) != 0 or float(root.get('y', '0')) != 0:
            return None
        return next(walk(root), None)
    except (ValueError, TypeError, OverflowError):
        # Unsupported SVG lengths are never guessed into viewport coordinates.
        return None


def retained_paint(image, before, after):
    """Keep already correct connected objects, including tiny unrelated marks."""
    background = np.median(np.concatenate((image[0],image[-1],image[:,0],image[:,-1])),axis=0)
    foreground = np.max(abs(image.astype(float)-background),axis=2) > 25
    count, _, stats, _ = cv2.connectedComponentsWithStats(foreground.astype('uint8'))
    for x,y,w,h,area in stats[1:count]:
        if area < 3:
            continue
        region=np.s_[max(0,y-2):y+h+2,max(0,x-2):x+w+2]
        old=float(np.square(image[region].astype(float)-before[region]).mean())
        new=float(np.square(image[region].astype(float)-after[region]).mean())
        if old <= 4 and new > old+1:
            return False
    return True


def atoms(root):
    """Paths to atomic groups/primitives; never traverse definitions or effects."""
    def walk(node, path):
        for index, child in enumerate(node):
            tag = child.tag.rsplit('}',1)[-1]
            location = path+(index,)
            if child.get('data-fallback-group') or tag in DRAWABLE:
                yield location, child
            elif tag == 'g':
                yield from walk(child,location)
    yield from walk(root,())


def at(root, path):
    for index in path:
        root=root[index]
    return root


def bounds(node, w, h):
    # Replacement matching only uses viewport-space native geometry. Transformed
    # or styled objects can still be retained or removed, never guessed in-place.
    group=ET.Element(f'{{{NS}}}g',{'data-fallback-group':'bounds'})
    if node.get('data-fallback-group'):
        group.extend(copy.deepcopy(list(node)))
    else:
        child=copy.deepcopy(node)
        child.set('data-part','bounds')
        group.append(child)
    root=ET.Element(f'{{{NS}}}svg')
    root.append(group)
    try:
        regions=part_regions(ET.tostring(root,encoding='unicode'),w,h)
    except (ValueError,TypeError):
        return None
    if not regions:
        return None
    boxes=np.array([r['box'] for r in regions])
    lo=boxes[:,:2].min(axis=0)
    hi=(boxes[:,:2]+boxes[:,2:]).max(axis=0)
    return np.r_[lo,hi]


def overlaps(a,b):
    if a is None or b is None:
        return False
    intersection=np.maximum(0,np.minimum(a[2:],b[2:])-np.maximum(a[:2],b[:2])).prod()
    return intersection/max(1,np.prod(a[2:]-a[:2])) >= .5


def removals(svg, w, h):
    root=ET.fromstring(svg)
    for path,node in atoms(root):
        box=bounds(node,w,h)
        # Do not spend deletion probes on the scene background.
        if box is None or np.prod(box[2:]-box[:2]) >= w*h*.8:
            continue
        candidate=copy.deepcopy(root)
        at(candidate,path[:-1]).remove(at(candidate,path))
        yield ET.tostring(candidate,encoding='unicode')


def edits(svg, group, w, h):
    """Add a group, or replace overlapping atoms at their existing stack slot."""
    root=ET.fromstring(svg)
    added=copy.deepcopy(root)
    added.append(copy.deepcopy(group))
    target=bounds(group,w,h)
    paths=[]
    for path,node in atoms(root):
        ancestors=[at(root,path[:i]) for i in range(len(path))]
        if any(n.get('transform') or n.get('style') or n.get('clip-path') or n.get('mask') for n in ancestors+[node]):
            continue
        box=bounds(node,w,h)
        if box is not None and np.prod(box[2:]-box[:2]) < w*h*.8 and overlaps(box,target):
            paths.append(path)
    if not paths:
        yield ET.tostring(added,encoding='unicode'),'add'
        return
    # Replacing a split group removes all its overlapping parts atomically.
    # Unrelated correct paint is independently protected by the caller.
    candidate=copy.deepcopy(root)
    first=paths[0]
    parent=at(candidate,first[:-1])
    for path in sorted(paths,reverse=True):
        at(candidate,path[:-1]).remove(at(candidate,path))
    parent.insert(first[-1],copy.deepcopy(group))
    # Probe repair before overlay. Otherwise an opaque addition can hide an old
    # incomplete primitive; its pixel-identical replacement can no longer win
    # the strict error comparison, leaving a redundant hidden scene object.
    yield ET.tostring(candidate,encoding='unicode'),'replace'
    yield ET.tostring(added,encoding='unicode'),'add'


def compose(image, session, incumbent, probe, remaining):
    """Use the current best scene after every edit; all renders use caller budget."""
    from src.iCCModules.imageCompositeConverterFallbackGroups import group_proposals
    h,w=image.shape[:2]
    used=0
    # Delete unsupported existing atoms first, reserving most work for observed
    # groups. No separate session, renderer or time allowance is introduced.
    # Rebuild each deletion from the current scene. A later deletion must never
    # silently reintroduce an atom removed by an earlier accepted operation.
    tried=set()
    while used < min(6,remaining) and not session.time_reason():
        source=incumbent()['svg']
        candidates=list(removals(source,w,h))
        candidate=next((c for c in candidates if c not in tried),None)
        if candidate is None:
            break
        tried.add(candidate)
        if session.time_reason() or used >= min(6,remaining):
            break
        probe(candidate,'native_object_group:remove',incumbent(),part_regions(candidate,w,h))
        used+=1
    # Detectors return a few coupled registration alternatives. Process each
    # group separately so different families accumulate in one scene.
    for index,(candidate,family) in enumerate(group_proposals(image,session)):
        if index >= 8 or session.time_reason() or used >= remaining:
            return
        for group in ET.fromstring(candidate):
            if not group.get('data-fallback-group'):
                continue
            parent=incumbent()
            for edited,operation in edits(parent['svg'],group,w,h):
                if session.time_reason() or used >= remaining:
                    return
                probe(edited,'native_object_group:'+operation+':'+family,parent,part_regions(edited,w,h))
                used+=1
