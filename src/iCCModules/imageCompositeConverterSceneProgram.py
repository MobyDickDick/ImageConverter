"""Description-declared primitives, with no image-specific geometry or fitters.

The small vocabulary defines objects and relationships, never their measured
positions. The evolutionary engine may start every object anywhere on canvas.
"""
from __future__ import annotations

import math
import re
from xml.etree import ElementTree as ET

import numpy as np

VERSION = 'primitive_scene_program_v2'
KINDS = ('circle', 'ellipse', 'rect', 'square', 'triangle', 'line')
# Each object has centre, size, angle, stroke width, RGB fill/stroke, and a
# second fill stop. Paint is independent of geometry; the last two values select
# fill mode and gradient direction.
STRIDE = 17


def sample_parameters(program, svg, width, height):
    """Import a native primitive sample as an optional ordinary-search start.

    No image pixels or catalog identifiers are read. Unsupported encodings
    return None so the caller can use its existing fresh-construction path.
    """
    from PIL import ImageColor
    from src.iCCModules.imageCompositeConverterSvgStyles import inline_simple_svg_styles
    from src.iCCModules.imageCompositeConverterRepresentation import path_points, EXCLUDED
    from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform
    root=ET.fromstring(inline_simple_svg_styles(svg))
    gradients={node.get('id'):node for node in root.iter() if node.tag.rsplit('}',1)[-1]=='linearGradient'}
    found=[]
    def visit(node,parent=(1.,0.,0.,1.,0.,0.),inherited=None):
        tag=node.tag.rsplit('}',1)[-1]
        if tag in EXCLUDED:
            return
        style=dict(inherited or {'fill':'black','stroke':'none','stroke-width':'1'})
        for key in style:
            style[key]=node.get(key,style[key])
        matrix=_compose(parent,_transform(node.get('transform','')))
        a,b,c,d,tx,ty=matrix
        def mapped(points):
            return np.asarray(points)@np.array([[a,b],[c,d]])+[tx,ty]
        row=np.full(STRIDE,.5); kind=tag
        if tag=='circle':
            if not np.isclose(math.hypot(a,b),math.hypot(c,d)) or not np.isclose(a*c+b*d,0):
                raise ValueError('Deformed sample circle')
            center=mapped([[float(node.get('cx','0')),float(node.get('cy','0'))]])[0]
            sx=sy=2*float(node.get('r'))*math.hypot(a,b); angle=0.
        elif tag=='line':
            points=mapped([[float(node.get(k,'0')) for k in ('x1','y1')],
                           [float(node.get(k,'0')) for k in ('x2','y2')]])
            center=points.mean(axis=0); direction=points[1]-points[0]
            sx=np.linalg.norm(direction); sy=sx; angle=math.atan2(direction[1],direction[0])
        elif tag in {'polygon','path'}:
            paths=path_points(node)
            if len(paths)!=1 or not paths[0][1]:
                raise ValueError('Unsupported sample path')
            points=paths[0][0]
            if len(points)>3 and np.allclose(points[0],points[-1]):
                points=points[:-1]
            if len(points)!=3:
                raise ValueError('Unsupported sample polygon')
            points=mapped(points); kind='triangle'
            # Program triangles store their apex first. Generic triangles
            # identify it by the two equal edges instead of relying on IDs.
            lengths=np.linalg.norm(np.roll(points,-1,axis=0)-points,axis=1)
            apex=min(range(3),key=lambda i:abs(lengths[i]-lengths[(i-1)%3]))
            tip=points[apex]; base=np.delete(points,apex,axis=0)
            direction=tip-base.mean(axis=0); center=(tip+base.mean(axis=0))/2
            sx=np.linalg.norm(direction); sy=np.linalg.norm(base[0]-base[1])
            angle=math.atan2(direction[1],direction[0])
        elif tag in {'rect','ellipse'}:
            # Backgrounds are inventory-free; other encodings retain their
            # established importer rather than guessing a different shape.
            if tag=='rect' and style['stroke']=='none' and node.get('width')==root.get('width') and node.get('height')==root.get('height'):
                return
            raise ValueError('Unsupported sample shape')
        else:
            for child in node:
                visit(child,matrix,style)
            return
        row[:6]=[* (center/[width,height]),sx/width,sy/height,(angle/(2*math.pi))%1,
                  float(style['stroke-width'])*math.hypot(a,b)/(.1*min(width,height))]
        row[9:12]=np.array(ImageColor.getrgb(style['stroke']))/255
        fill=style['fill']; row[15]=0. if fill=='none' else .5
        gradient=re.fullmatch(r'url\(#([^)]*)\)',fill)
        if gradient:
            node_gradient=gradients[gradient[1]]
            stops=list(node_gradient)
            row[6:9]=np.array(ImageColor.getrgb(stops[0].get('stop-color')))/255
            row[12:15]=np.array(ImageColor.getrgb(stops[-1].get('stop-color')))/255
            def number(key,default):
                value=node_gradient.get(key,default)
                return float(value.removesuffix('%'))/(100 if value.endswith('%') else 1)
            dx=number('x2','1')-number('x1','0'); dy=number('y2','0')-number('y1','0')
            row[16]=(math.atan2(dy,dx)/(2*math.pi))%1; row[15]=1.
        elif fill!='none':
            row[6:9]=np.array(ImageColor.getrgb(fill))/255
        found.append((kind,row))
    try:
        visit(root)
        values=[]
        for obj in program['objects']:
            index=next(i for i,(kind,row) in enumerate(found) if kind==obj['kind'])
            values.append(found.pop(index)[1])
        if found:
            return None
        values=np.array(values)
        for claim in program.get('paint_claims',[]):
            if claim['claim']=='equal_stroke':
                indices=[i for i,obj in enumerate(program['objects']) if obj['kind']==claim['kind']]
                values[indices,5]=np.median(values[indices,5])
        return values.ravel()
    except (ValueError,KeyError,TypeError,StopIteration):
        return None


def scene_program(description):
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description
    from src.iCCModules.imageCompositeConverterRepresentation import description_object_limits
    text = normalize_description(description).casefold()
    from src.iCCModules.imageCompositeConverterScopedPaint import scoped_paint_claims
    paint_claims, text = scoped_paint_claims(text)
    # This is a bounded primitive language, not permission to ignore objects.
    unsupported = (r'\b(?:text|beschriftung|buchstabe\w*|schrift\w*|ziffer\w*|stern\w*|'
                   r'pfeil\w*|bogen\w*|spirale\w*|schraff\w*|sinus\w*|raute\w*|'
                   r'diagonale\w*|symmetr\w*|gestrichelt\w*|innerhalb|ausserhalb|außerhalb)\b')
    check = re.sub(r'\b(?:keine|ohne)\s+(?:schriftzeichen|text|beschriftung)\b', '', text)
    if re.search(unsupported, check):
        return None
    counts = description_object_limits(text)
    if not counts or set(counts)-set(KINDS) or not 1 <= sum(counts.values()) <= 10:
        return None
    # Motor contracts carry additional constraints; the existing dedicated path
    # still owns those. Free primitive search must not discard their claims.
    if 'motorgetrieben' in text:
        return None
    # Reject claims outside this compiler's implemented constraints. Existing
    # specialised models remain available through the ordinary profiles.
    if re.search(r'\b(?:parallel\w*|senkrecht\w*|vertikal\w*|horizontal\w*|waagerecht\w*|'
                 r'konzentr\w*|mittig|zentriert|berühr\w*|überlapp\w*|beschrift\w*|'
                 r'dunkelgrau\w*|hellgrau\w*|grau\w*|rot\w*|blau\w*|grün\w*|gelb\w*|'
                 r'schwarz\w*|weiss\w*|weiß\w*)\b', text):
        return None
    objects = []
    for kind in KINDS:
        for i in range(counts.get(kind, 0)):
            objects.append(dict(id=f'{kind}_{i}', kind=kind))
    nouns=dict(circle=r'kreis\w*|kelle',ellipse=r'ellipse\w*',rect=r'rechteck\w*',
               square=r'quadrat\w*',triangle=r'dreieck\w*',line=r'linie\w*|gerade\w*|kelle')
    for section in re.finditer(r'\b(links|rechts)\s*:\s*([^.]+)',text):
        for kind,pattern in nouns.items():
            if re.search(r'\b(?:'+pattern+r')\b',section[2]):
                for obj in objects:
                    if obj['kind']==kind and 'side' not in obj:
                        obj['side']=section[1]
    stem_direction = None
    match = re.search(r'\bgriff\s+(?:nach\s+)?(rechts|links|oben|unten)\b', text)
    if match:
        stem_direction = dict(rechts=0., unten=math.pi/2, links=math.pi, oben=-math.pi/2)[match[1]]
    relations = []
    circles = [o['id'] for o in objects if o['kind']=='circle']
    lines = [o['id'] for o in objects if o['kind']=='line']
    triangles = [o['id'] for o in objects if o['kind']=='triangle']
    if 'kelle' in text and len(circles)==len(lines)==1:
        relations.append(dict(kind='attached', objects=[circles[0], lines[0]], direction=stem_direction))
    if re.search(r'(?:gleich\w*|gemeinsam\w*)\s+(?:punkt|spitze)', text):
        if len(triangles)==2:
            relations.append(dict(kind='coincident', objects=triangles, anchors=['apex','apex']))
            if re.search(r'\bgriff\w*\b', text) and len(lines)==1:
                relations.append(dict(kind='coincident', objects=[lines[0],triangles[0]], anchors=['end','apex']))
        else:
            return None  # ambiguous referents cannot silently become constraints
    return dict(schema=VERSION, objects=objects, relations=relations,
                paint_claims=paint_claims,
                isosceles='gleichschenklig' in text,
                outline=bool(re.search(r'\b(?:ungefüllt|ohne füllung|nur umriss)\b', text)),
                no_gradient=bool(re.search(r'\b(?:ohne|kein\w*)\s+(?:farb)?verlauf\b',text)))


def geometry(program, parameters, width, height):
    """Interpret independently placed primitives; no raster is read here."""
    values = np.asarray(parameters, dtype=float).reshape(len(program['objects']), STRIDE)
    result = {}
    for obj, p in zip(program['objects'], values):
        cx,cy = p[:2]*[width,height]
        sx,sy = p[2:4]*[width,height]
        angle = p[4]*2*math.pi
        direction = np.array([math.cos(angle),math.sin(angle)])
        normal = np.array([-direction[1],direction[0]])
        center = np.array([cx,cy])
        kind=obj['kind']
        if kind=='circle':
            sx=sy=min(sx,sy)
        if kind=='square':
            sx=sy=min(sx,sy)
        if kind=='triangle':
            # Apex, then the two base ends: always exactly isosceles.
            points=np.array([center+direction*sx/2,center-direction*sx/2+normal*sy/2,
                             center-direction*sx/2-normal*sy/2])
        elif kind=='line':
            points=np.array([center-direction*sx/2,center+direction*sx/2])
        else:
            points=np.array([center-direction*sx/2-normal*sy/2,center+direction*sx/2-normal*sy/2,
                             center+direction*sx/2+normal*sy/2,center-direction*sx/2+normal*sy/2])
        result[obj['id']]=dict(kind=kind,center=center,points=points,size=(sx,sy),
                              angle=angle,stroke=max(.35,p[5]*min(width,height)*.1),paint=p[6:])
    return result


def relation_error(program, shapes, width, height):
    error=0.
    left=[shapes[o['id']]['center'][0] for o in program['objects'] if o.get('side')=='links']
    right=[shapes[o['id']]['center'][0] for o in program['objects'] if o.get('side')=='rechts']
    if left and right:
        error+=max(0.,(max(left)-min(right))/width)**2
    for relation in program['relations']:
        a,b=(shapes[key] for key in relation['objects'])
        if relation['kind']=='coincident':
            pa=a['points'][1 if relation['anchors'][0]=='end' else 0]
            pb=b['points'][1 if relation['anchors'][1]=='end' else 0]
            error+=float(np.square((pa-pb)/[width,height]).sum())
        else:
            start=a['center']
            end=b['points'][0]
            radius=a['size'][0]/2
            error+=float(((np.linalg.norm(end-start)-radius)/min(width,height))**2)
            if relation['direction'] is not None:
                desired=np.array([math.cos(relation['direction']),math.sin(relation['direction'])])
                error+=float(np.square((end-start-radius*desired)/[width,height]).sum())
                unit=(b['points'][1]-end)/max(1e-8,np.linalg.norm(b['points'][1]-end))
                error+=float(np.square(unit-desired).sum())*.05
    return float(error)


def program_svg(program, parameters, width, height, background=(255,255,255)):
    from src.iCCModules.imageCompositeConverterScopedPaint import constrain_parameters
    parameters=constrain_parameters(program,parameters)
    shapes=geometry(program,parameters,width,height)
    defs,parts=[],[]
    def color(rgb):
        return '#'+''.join(f'{int(c):02x}' for c in np.clip(np.rint(np.asarray(rgb)*255),0,255))
    for obj in program['objects']:
        s=shapes[obj['id']]
        paint=s['paint']
        fill=color(paint[:3])
        if program['outline'] or paint[9]<.15:
            fill='none'
        elif not program['no_gradient'] and paint[9]>.65:
            gradient=obj['id']+'_paint'
            dx,dy=math.cos(paint[10]*2*math.pi),math.sin(paint[10]*2*math.pi)
            extent=(abs(dx)+abs(dy))/2
            defs.append(f'<linearGradient id="{gradient}" x1="{.5-dx*extent:.6f}" y1="{.5-dy*extent:.6f}" '
                        f'x2="{.5+dx*extent:.6f}" y2="{.5+dy*extent:.6f}">'
                        f'<stop offset="0" stop-color="{fill}"/><stop offset="1" stop-color="{color(paint[6:9])}"/></linearGradient>')
            fill=f'url(#{gradient})'
        attrs=f'id="{obj["id"]}" fill="{fill}" stroke="{color(paint[3:6])}" stroke-width="{s["stroke"]:.5f}" stroke-linejoin="round"'
        cx,cy=s['center']; sx,sy=s['size']; angle=math.degrees(s['angle'])
        if s['kind']=='circle':
            part=f'<circle cx="{cx:.5f}" cy="{cy:.5f}" r="{sx/2:.5f}" {attrs}/>'
        elif s['kind']=='ellipse':
            part=f'<ellipse cx="{cx:.5f}" cy="{cy:.5f}" rx="{sx/2:.5f}" ry="{sy/2:.5f}" transform="rotate({angle:.5f} {cx:.5f} {cy:.5f})" {attrs}/>'
        elif s['kind'] in {'rect','square'}:
            part=f'<rect x="{cx-sx/2:.5f}" y="{cy-sy/2:.5f}" width="{sx:.5f}" height="{sy:.5f}" transform="rotate({angle:.5f} {cx:.5f} {cy:.5f})" {attrs}/>'
        elif s['kind']=='line':
            (x1,y1),(x2,y2)=s['points']
            part=f'<line x1="{x1:.5f}" y1="{y1:.5f}" x2="{x2:.5f}" y2="{y2:.5f}" {attrs}/>'
        else:
            points=' '.join(f'{x:.5f},{y:.5f}' for x,y in s['points'])
            part=f'<polygon points="{points}" {attrs}/>'
        parts.append(part)
    bg='#'+''.join(f'{int(c):02x}' for c in background)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" data-primitive-scene="1">'
            f'<defs>{"".join(defs)}</defs><rect width="{width}" height="{height}" fill="{bg}" data-role="background"/>'
            +''.join(parts)+'</svg>')


def validate_program_svg(svg, program, tolerance=.01):
    """Recheck relationships on actual exported points, including template edits."""
    root=ET.fromstring(svg)
    from src.iCCModules.imageCompositeConverterScopedPaint import validate_scoped_paint
    validate_scoped_paint(svg,program.get('paint_claims'))
    # Export uses native primitives in source coordinates. A later common
    # transform is handled by the representation parser's matrix helpers.
    from src.iCCModules.imageCompositeConverterArrowAssertions import _compose, _transform
    shapes={}
    def visit(node,parent=(1.,0.,0.,1.,0.,0.)):
        matrix=_compose(parent,_transform(node.get('transform','')))
        a,b,c,d,tx,ty=matrix
        def mapped(points):
            return np.asarray(points)@np.array([[a,b],[c,d]])+np.array([tx,ty])
        identifier=node.get('id')
        kind=node.tag.rsplit('}',1)[-1]
        if identifier:
            if kind=='circle':
                shapes[identifier]=dict(center=mapped([[float(node.get('cx')),float(node.get('cy'))]])[0],
                                        radius=float(node.get('r'))*math.hypot(a,b))
            elif kind=='line':
                shapes[identifier]=dict(points=mapped([[float(node.get('x1')),float(node.get('y1'))],
                                                      [float(node.get('x2')),float(node.get('y2'))]]))
            elif kind=='polygon':
                points=np.array([float(x) for x in re.findall(r'-?\d+(?:\.\d+)?',node.get('points',''))]).reshape(-1,2)
                shapes[identifier]=dict(points=mapped(points))
        for child in node:
            visit(child,matrix)
    visit(root)
    for shape in shapes.values():
        if 'center' not in shape:
            shape['center']=shape['points'].mean(axis=0)
    left=[shapes[o['id']]['center'][0] for o in program['objects'] if o.get('side')=='links' and o['id'] in shapes]
    right=[shapes[o['id']]['center'][0] for o in program['objects'] if o.get('side')=='rechts' and o['id'] in shapes]
    if left and right and max(left)>=min(right):
        raise ValueError('primitive_relation:wrong_left_right_order')
    for rel in program['relations']:
        if any(key not in shapes for key in rel['objects']):
            raise ValueError('primitive_relation:missing_objects')
        a,b=(shapes[key] for key in rel['objects'])
        if rel['kind']=='coincident':
            pa=a['points'][1 if rel['anchors'][0]=='end' else 0]
            pb=b['points'][1 if rel['anchors'][1]=='end' else 0]
            if np.linalg.norm(pa-pb)>tolerance:
                raise ValueError('primitive_relation:disconnected_endpoints')
        else:
            start,end=b['points']
            if abs(np.linalg.norm(start-a['center'])-a['radius'])>tolerance:
                raise ValueError('primitive_relation:detached_handle')
            if rel['direction'] is not None:
                direction=np.array([math.cos(rel['direction']),math.sin(rel['direction'])])
                if (np.linalg.norm(start-a['center']-a['radius']*direction)>tolerance
                        or np.linalg.norm((end-start)-np.linalg.norm(end-start)*direction)>tolerance):
                    raise ValueError('primitive_relation:wrong_handle_direction')
