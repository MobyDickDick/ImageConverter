"""Bounded atomic edits of observed native groups in an existing SVG scene."""
from __future__ import annotations

import copy
from xml.etree import ElementTree as ET

import numpy as np
import cv2

from src.iCCModules.imageCompositeConverterFallbackGroups import NS, part_regions

DRAWABLE = {'rect', 'circle', 'ellipse', 'line', 'polygon', 'polyline', 'path', 'text'}


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
    yield ET.tostring(added,encoding='unicode'),'add'
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
        return
    # Replacing a split group removes all its overlapping parts atomically.
    # Unrelated correct paint is independently protected by the caller.
    candidate=copy.deepcopy(root)
    first=paths[0]
    parent=at(candidate,first[:-1])
    for path in sorted(paths,reverse=True):
        at(candidate,path[:-1]).remove(at(candidate,path))
    parent.insert(first[-1],copy.deepcopy(group))
    yield ET.tostring(candidate,encoding='unicode'),'replace'


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
