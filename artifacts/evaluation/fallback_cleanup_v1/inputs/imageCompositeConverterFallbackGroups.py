"""Bounded analytic object groups inferred from raster paint, never catalogue IDs.

Groups are atomic alternatives, not model approvals. Triangles have exactly three
vertices; observed contours are used only for measurement and are not emitted.
"""
from __future__ import annotations

from xml.etree import ElementTree as ET
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def cross(a, b):
    return a[...,0]*b[...,1]-a[...,1]*b[...,0]


def element(parent, tag, role=None, **attrs):
    if role:
        attrs['data-part'] = role
    return ET.SubElement(parent, f'{{{NS}}}{tag}', {k.replace('_', '-'): str(v) for k, v in attrs.items()})


def canvas(image):
    h, w = image.shape[:2]
    border = np.concatenate((image[0], image[-1], image[:, 0], image[:, -1]))
    root = ET.Element(f'{{{NS}}}svg', width=str(w), height=str(h), viewBox=f'0 0 {w} {h}')
    element(root, 'rect', width=w, height=h, fill=_hex(np.median(border, axis=0)))
    return root


def color_masks(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    sat = (hsv[:, :, 1] > 65) & (hsv[:, :, 2] > 60)
    hist = np.bincount(hsv[:, :, 0][sat], minlength=180)
    for _ in range(4):
        peak = int(hist.argmax())
        if hist[peak] < 8:
            return
        distance = np.minimum(abs(np.arange(180)-peak), 180-abs(np.arange(180)-peak))
        yield sat & (distance[hsv[:, :, 0]] <= 15)
        hist[distance <= 15] = 0


def arrow_groups(image, session):
    """A painted triangular head and a long collinear shaft form one object."""
    root = canvas(image)
    count = 0
    for mask in color_masks(image):
        if session.time_reason():
            return
        opened = cv2.morphologyEx(mask.astype('uint8'), cv2.MORPH_OPEN, np.ones((3, 3), 'uint8'))
        contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:4]:
            x, y, w, h = cv2.boundingRect(contour)
            if min(w, h) < 3 or max(w, h) > min(image.shape[:2])*.65:
                continue
            # Recover the thin tip from the original colour mask around the
            # thick head. Opening is for detection only, not output geometry.
            y0, x0 = max(0, y-2), max(0, x-2)
            y1, x1 = y+h+2, x+w+2
            my, mx = np.where(mask)
            if np.ptp(my) > 2*np.ptp(mx):
                if (my < y).sum() > (my >= y+h).sum():
                    y0 = y
                else:
                    y1 = y+h
            elif np.ptp(mx) > 2*np.ptp(my):
                if (mx < x).sum() > (mx >= x+w).sum():
                    x0 = x
                else:
                    x1 = x+w
            patch = mask[y0:y1, x0:x1].astype('uint8')
            cs, _ = cv2.findContours(patch, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not cs:
                continue
            c = max(cs, key=cv2.contourArea).astype('float32') + np.array([[[x0+.5, y0+.5]]], 'float32')
            area, triangle = cv2.minEnclosingTriangle(c)
            if triangle is None or area <= 3 or cv2.contourArea(c)/area < .58:
                continue
            tri = triangle.reshape(3, 2).astype(float)
            yy, xx = np.where(mask)
            points = np.c_[xx+.5, yy+.5]
            outside = ((points[:,0] < x-2) | (points[:,0] > x+w+2)
                       | (points[:,1] < y-2) | (points[:,1] > y+h+2))
            shaft = points[outside]
            if len(shaft) < 8:
                continue
            center = shaft.mean(axis=0)
            _, _, vh = np.linalg.svd(shaft-center, full_matrices=False)
            direction = vh[0]
            across = abs(cross(shaft-center, direction))
            if np.percentile(across, 90) > 1.5:
                continue
            run = (shaft-center) @ direction
            low, high = float(run.min())-.5, float(run.max())+.5
            if high-low < max(8, max(w,h)*2) or len(np.unique(np.floor(run))) < .8*(high-low):
                continue
            a, b = center+direction*low, center+direction*high
            width = float(np.clip(len(run)/(high-low), .7, 3))
            # Align the triangular altitude with the measured shaft rather
            # than a staircase-biased minimum enclosing triangle.
            normal = np.array([-direction[1], direction[0]])
            along = (tri-center) @ direction
            lateral = (tri-center) @ normal
            pair = min(((i,j) for i in range(3) for j in range(i)), key=lambda ij: abs(along[ij[0]]-along[ij[1]]))
            tip = next(i for i in range(3) if i not in pair)
            base_t = float(np.mean(along[list(pair)]))
            tip_t = float(along[tip])
            head_points = points[~outside]
            half = min(abs(lateral[pair[0]]-lateral[pair[1]])/2,
                       np.ptp((head_points-center) @ normal)/2+.5)
            tri = np.array([center+direction*tip_t, center+direction*base_t-normal*half,
                            center+direction*base_t+normal*half])
            near_t = min((base_t,tip_t),key=lambda t: min(abs(t-low),abs(t-high)))
            if min(abs(near_t-low),abs(near_t-high)) > 5:
                continue
            if abs(near_t-low) < abs(near_t-high):
                a = center+direction*near_t
            else:
                b = center+direction*near_t
            color = _hex(np.median(image[mask], axis=0))
            head_pixels = image[y0:y1,x0:x1][patch > 0]
            saturation = cv2.cvtColor(head_pixels.reshape(1,-1,3),cv2.COLOR_BGR2HSV)[0,:,1]
            head_color = _hex(np.median(head_pixels[saturation >= np.percentile(saturation,65)],axis=0))
            group = element(root, 'g', **{'data-fallback-group': 'shaft_triangle'})
            element(group, 'line', 'shaft', x1=a[0], y1=a[1], x2=b[0], y2=b[1], stroke=color, stroke_width=width)
            element(group, 'polygon', 'head', points=' '.join(f'{p[0]},{p[1]}' for p in tri), fill=head_color)
            count += 1
            if count >= 4:
                break
        if count >= 4:
            break
    if count:
        import copy
        for shift in (0., .125, -.125, .25):
            candidate = copy.deepcopy(root)
            for node in candidate.iter():
                if node.get('data-part') == 'shaft':
                    # Subpixel registration is a competing measured hypothesis.
                    for key in ('x1','x2','y1','y2'):
                        node.set(key,str(float(node.get(key))+shift))
            yield ET.tostring(candidate, encoding='unicode'), 'shaft_triangle'


def panel_groups(image, session):
    """Crossed coloured panel, observed connector, ring and oblique linkage."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    neutral = (hsv[:, :, 1] < 65) & (gray < 210)
    contours, hierarchy = cv2.findContours(neutral.astype('uint8'), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    holes = []
    for i, contour in enumerate(contours):
        if hierarchy is None or hierarchy[0, i, 3] < 0:
            continue
        (cx, cy), radius = cv2.minEnclosingCircle(contour)
        x, y, w, h = cv2.boundingRect(contour)
        if 1 <= radius <= 8 and abs(w-h) <= 2 and cv2.contourArea(contour) >= radius*radius*1.3:
            holes.append((np.array([cx+.5, cy+.5]), radius))
    holes = sorted(holes,key=lambda row:-row[1])[:16]
    for mask in color_masks(image):
        if session.time_reason():
            return
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype('uint8'))
        for i in sorted(range(1, n), key=lambda k: -stats[k, 4])[:4]:
            x, y, w, h, area = stats[i]
            if min(w, h) < 8 or not .7 <= w/h <= 1.4 or area < w*h*.6:
                continue
            for center, radius in holes:
                if session.time_reason():
                    return
                cx, cy = center
                if not (x+w+radius < cx < x+3*w and y-2 <= cy <= y+h+2):
                    continue
                # The external linkage has to pass through the observed ring.
                lines = cv2.HoughLinesP(neutral.astype('uint8'), 1, np.pi/180, threshold=6,
                                        minLineLength=max(6, int(w*.65)), maxLineGap=4)
                candidates = []
                for raw in ([] if lines is None else lines[:, 0]):
                    a, b = np.array(raw[:2], float)+.5, np.array(raw[2:], float)+.5
                    direction = b-a
                    length = np.linalg.norm(direction)
                    if length < 1 or min(abs(direction)) < length*.25:
                        continue
                    direction /= length
                    if abs(cross(center-a, direction)) < radius+1 and min(a[0], b[0]) > x+w-2:
                        candidates.append((length, direction))
                if not candidates:
                    continue
                _, direction = max(candidates, key=lambda row: row[0])
                yy, xx = np.where(neutral & (np.indices(gray.shape)[1] > x+w+1))
                points = np.c_[xx+.5, yy+.5]
                along = (points-center) @ direction
                across = abs(cross(points-center, direction))
                run = along[(across < 1.4) & (abs(along) > radius+1)]
                if not len(run) or run.min() > -radius-2 or run.max() < radius+2:
                    continue
                color = _hex(np.median(image[labels == i], axis=0))
                paint = image[neutral]
                stroke = _hex(np.percentile(paint, 25, axis=0))
                for margin in (.5, 1.):
                    root = canvas(image)
                    group = element(root, 'g', **{'data-fallback-group': 'crossed_panel_linkage'})
                    element(group, 'rect', 'panel', x=x-margin, y=y-margin, width=w+2*margin,
                            height=h+2*margin, fill=color, stroke=stroke, stroke_width=1)
                    for j, ends in enumerate(((x+.5, y+.5, x+w-.5, y+h-.5), (x+w-.5, y+.5, x+.5, y+h-.5))):
                        element(group, 'line', 'diagonal'+str(j), **dict(zip(('x1','y1','x2','y2'),ends)),
                                stroke='#eeeeee', stroke_width=1)
                    element(group, 'line', 'connector', x1=x+w+margin, y1=cy, x2=cx-radius, y2=cy,
                            stroke=stroke, stroke_width=1.5)
                    for j, (lo, hi) in enumerate(((float(run.min())-.5, -radius), (radius, float(run.max())+.5))):
                        a, b = center+direction*lo, center+direction*hi
                        element(group, 'line', 'link'+str(j), x1=a[0], y1=a[1], x2=b[0], y2=b[1],
                                stroke=stroke, stroke_width=1.5)
                    element(group, 'circle', 'joint', cx=cx, cy=cy, r=radius+.25, fill='white', stroke=stroke, stroke_width=1.5)
                    import copy
                    for shift in (0., .25, -.25):
                        candidate = copy.deepcopy(root)
                        for node in candidate.iter():
                            if node.get('data-part') in {'connector','link0','link1','joint'}:
                                for key in ('y1','y2','cy'):
                                    if node.get(key) is not None:
                                        node.set(key,str(float(node.get(key))+shift))
                        yield ET.tostring(candidate, encoding='unicode'), 'crossed_panel_linkage'


def group_proposals(image, session):
    yield from arrow_groups(image, session)
    yield from panel_groups(image, session)


def part_regions(svg, width, height):
    """Regions travel with the group through parameter refinement."""
    result = []
    for group in ET.fromstring(svg).iter():
        if not group.get('data-fallback-group'):
            continue
        for node in group:
            role = node.get('data-part')
            if not role:
                continue
            tag = node.tag.rsplit('}', 1)[-1]
            if tag == 'line':
                xs = [float(node.get(k)) for k in ('x1', 'x2')]
                ys = [float(node.get(k)) for k in ('y1', 'y2')]
            elif tag == 'polygon':
                pts = np.array([list(map(float, p.split(','))) for p in node.get('points').split()])
                xs, ys = pts[:, 0], pts[:, 1]
            elif tag == 'circle':
                cx, cy, r = [float(node.get(k)) for k in ('cx','cy','r')]
                xs, ys = [cx-r, cx+r], [cy-r, cy+r]
            elif tag == 'rect':
                x, y, w, h = [float(node.get(k)) for k in ('x','y','width','height')]
                xs, ys = [x,x+w], [y,y+h]
            else:
                continue
            x, X = max(0, int(min(xs))-2), min(width, int(max(xs))+3)
            y, Y = max(0, int(min(ys))-2), min(height, int(max(ys))+3)
            if X > x and Y > y:
                result.append(dict(group=group.get('data-fallback-group'), part=role, box=[x,y,X-x,Y-y]))
    return result


def check_parts(image, raster, regions):
    checks = []
    for region in regions:
        x, y, w, h = region['box']
        a, b = image[y:y+h,x:x+w], raster[y:y+h,x:x+w]
        mse = float(np.square(a.astype(float)-b.astype(float)).mean()/255**2)
        ae, be = cv2.Canny(a,50,140)>0, cv2.Canny(b,50,140)>0
        distance = cv2.distanceTransform((~be).astype('uint8'),cv2.DIST_L2,3)
        recall = float(np.exp(-distance[ae]).mean()) if ae.any() else 0.
        checks.append(dict(**region, normalized_mse=mse, edge_recall=recall, passed=mse <= .04 and recall >= .72))
    return checks


def check_relations(svg):
    """Require actual native connectivity; group labels alone prove nothing."""
    checks = []
    point = lambda n, suffix: np.array([float(n.get('x'+suffix)),float(n.get('y'+suffix))])
    for group in ET.fromstring(svg).iter():
        kind = group.get('data-fallback-group')
        if not kind:
            continue
        parts = {n.get('data-part'):n for n in group if n.get('data-part')}
        passed = False
        if kind == 'shaft_triangle' and set(parts) == {'shaft','head'}:
            line, head = parts['shaft'], parts['head']
            tri = np.array([list(map(float,p.split(','))) for p in head.get('points','').split()],dtype='float32')
            if len(tri) == 3:
                passed = max(cv2.pointPolygonTest(tri,tuple(point(line,s)),True) for s in ('1','2')) >= -1.5
        elif kind == 'crossed_panel_linkage' and set(parts) == {'panel','diagonal0','diagonal1','connector','link0','link1','joint'}:
            panel, joint, connector = parts['panel'], parts['joint'], parts['connector']
            x,y,w,h = [float(panel.get(k)) for k in ('x','y','width','height')]
            c = np.array([float(joint.get('cx')),float(joint.get('cy'))]);r=float(joint.get('r'))
            a,b = point(connector,'1'),point(connector,'2')
            passed = (abs(a[0]-(x+w)) <= 1 and y <= a[1] <= y+h
                      and abs(np.linalg.norm(b-c)-r) <= 1 and abs(a[1]-b[1]) <= 1)
            for role, corners in [('diagonal0',((x,y),(x+w,y+h))),('diagonal1',((x+w,y),(x,y+h)))]:
                passed &= all(np.linalg.norm(point(parts[role],s)-q) <= 2.5 for s,q in zip(('1','2'),corners))
            v0, v1 = point(parts['link0'],'2')-c, point(parts['link1'],'1')-c
            passed &= (abs(np.linalg.norm(v0)-r) <= 1 and abs(np.linalg.norm(v1)-r) <= 1
                       and np.dot(v0,v1) < 0 and abs(cross(v0,v1)) <= r)
        checks.append(dict(group=kind,relation='parts_connected',passed=bool(passed)))
    return checks
