"""Observed open polynomial stroke graphs with a tangent straight lead.

Only a single, thin, continuously visible run per scanline is fitted. The
bounded analytic family is Q/C with a linear scan axis; loops, occlusion and
elliptic arcs are not completed from priors. No oracle or catalogue is read.
"""
from __future__ import annotations
import re
from xml.etree import ElementTree as ET
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterFilledSymbols import _hex

NUMBER = r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?'


def curve_points(node):
    """Strict viewport Q/C subset emitted by this detector, without guessing."""
    effects={'transform','style','opacity','stroke-opacity','fill-opacity','stroke-dasharray',
             'clip-path','mask','filter','marker-start','marker-mid','marker-end','vector-effect',
             'display','visibility'}
    if (node.get('fill', 'black') != 'none' or effects.intersection(node.attrib)
            or node.get('stroke', 'none') == 'none'):
        raise ValueError('Unsupported curve part')
    value=node.get('d','')
    tokens=re.findall(NUMBER+r'|[A-Za-z]',value)
    if re.sub(NUMBER+r'|[A-Za-z]','',value).strip(' ,\t\n\r'):
        raise ValueError('Unsupported curve syntax')
    if len(tokens) not in (8,10) or tokens[0]!='M' or tokens[3] not in {'Q','C'}:
        raise ValueError('One absolute Q/C required')
    if len(tokens) != (8 if tokens[3]=='Q' else 10):
        raise ValueError('Invalid curve arity')
    pts=np.array([float(v) for i,v in enumerate(tokens) if i not in (0,3)]).reshape(-1,2)
    if not np.isfinite(pts).all() or np.max(abs(pts))>1e5:
        raise ValueError('Invalid curve coordinates')
    return pts


def sample_curve(points, count=33):
    t=np.linspace(0,1,count)[:,None]
    if len(points)==3:
        return (1-t)**2*points[0]+2*t*(1-t)*points[1]+t*t*points[2]
    return ((1-t)**3*points[0]+3*t*(1-t)**2*points[1]
            +3*t*t*(1-t)*points[2]+t**3*points[3])


def _simplex(start, steps, objective, session, limit=260):
    """Small deterministic Nelder-Mead search, charged to the active deadline."""
    vertices=np.vstack([start,start+np.diag(steps)])
    values=np.array([objective(p) for p in vertices])
    used=len(values)
    while used < limit and not session.time_reason():
        order=np.argsort(values); vertices=vertices[order]; values=values[order]
        center=vertices[:-1].mean(axis=0)
        reflected=2*center-vertices[-1]
        score=objective(reflected); used+=1
        if score < values[0] and used < limit:
            expanded=3*center-2*vertices[-1]
            expanded_score=objective(expanded); used+=1
            vertices[-1],values[-1]=(expanded,expanded_score) if expanded_score<score else (reflected,score)
        elif score < values[-2]:
            vertices[-1],values[-1]=reflected,score
        else:
            contracted=(center+(reflected if score<values[-1] else vertices[-1]))/2
            contracted_score=objective(contracted); used+=1
            if contracted_score < min(score,values[-1]):
                vertices[-1],values[-1]=contracted,contracted_score
            else:
                for i in range(1,len(vertices)):
                    if used>=limit or session.time_reason():
                        break
                    vertices[i]=(vertices[0]+vertices[i])/2
                    values[i]=objective(vertices[i]); used+=1
        if values.min() < 1e-10:
            break
    best=vertices[values.argmin()].copy(); score=float(values.min())
    # SVG rasterizers quantize coverage. A collapsed simplex can sit on a
    # plateau before an endpoint or control has reached the next coverage cell.
    for factor in (2.,1.,.5,.25):
        for _ in range(3):
            improved=False
            for i in range(len(best)):
                if session.time_reason():
                    return best
                for sign in (-1,1):
                    candidate=best.copy(); candidate[i]+=sign*steps[i]*factor
                    value=objective(candidate)
                    if value<score:
                        best,score=candidate,value; improved=True
            if not improved:
                break
    return best


def curve_groups(image, session, render_fn=None):
    from src.iCCModules.imageCompositeConverterFallbackGroups import canvas,element
    if session.time_reason() or max(image.shape[:2])>512:
        return
    background=np.median(np.concatenate((image[0],image[-1],image[:,0],image[:,-1])),axis=0)
    contrast=np.max(abs(image.astype(float)-background),axis=2)
    count,labels,stats,_=cv2.connectedComponentsWithStats((contrast>20).astype('uint8'))
    for label in sorted(range(1,count),key=lambda k:-stats[k,4])[:4]:
        if session.time_reason():
            return
        x,y,w,h,area=stats[label]
        if min(w,h)<6 or max(w,h)<24 or area/max(w,h)>7 or area<35:
            continue
        component=labels==label
        # Core paint supplies the coverage scale. Strongly varying paint or a
        # multicolour crossing is outside this constant-colour stroke family.
        core=image[component & (contrast>=np.percentile(contrast[component],85))]
        color=np.median(core,axis=0)
        delta=background-color
        if delta@delta<1600 or np.max(np.ptp(core.astype(float),axis=0))>12:
            continue
        alpha=np.clip(((background-image.astype(float))@delta)/(delta@delta),0,1)
        # One-pixel dilation includes antialiasing, but never another object.
        alpha*=cv2.dilate(component.astype('uint8'),np.ones((3,3),'uint8'))
        axis=0 if h>=w else 1
        coverage=alpha if axis==0 else alpha.T
        rows=np.where(coverage.sum(axis=1)>.2)[0]
        if len(rows)<24 or np.any(np.diff(rows)!=1):
            continue
        # Multiple separated runs imply branching, a loop, or an occlusion.
        if any(np.any(np.diff(np.where(coverage[r]>.1)[0])>1) for r in rows):
            continue
        scan=rows[2:-2]+.5
        mass=coverage[rows[2:-2]].sum(axis=1)
        across=(coverage[rows[2:-2]]@(np.arange(coverage.shape[1])+.5))/mass
        lo,hi=float(rows[0]),float(rows[-1]+1)
        span=hi-lo
        best=None
        for reverse in (False,True):
            t=(scan-lo)/span
            if reverse:
                t=1-t
            for degree in (2,3):
                for join in np.linspace(.14,.6,48):
                    if session.time_reason():
                        return
                    hinge=np.maximum(0,t-join)
                    design=np.column_stack([np.ones(len(t)),t-join]+[hinge**d for d in range(2,degree+1)])
                    coef=np.linalg.lstsq(design,across,rcond=None)[0]
                    residual=float(np.mean((design@coef-across)**2))
                    bend=abs(sum(coef[d]*(1-join)**d for d in range(2,degree+1)))
                    if residual>.12 or bend<5 or abs(coef[1])>span*.7:
                        continue
                    # Prefer the lower degree unless the raster demands C.
                    score=residual+.002*(degree-2)
                    if best is None or score<best[0]:
                        best=(score,degree,reverse,join,coef)
        if best is None:
            continue
        _,degree,reverse,join,coef=best
        slope=coef[1]/span
        lead_rows=(scan-lo)/span < join-.04 if not reverse else (hi-scan)/span < join-.04
        if lead_rows.sum()<5:
            continue
        width=float(np.median(mass[lead_rows])/np.sqrt(1+slope*slope))
        if not .8<=width<=5:
            continue
        # Explicit parameters: scan endpoints, join coordinate, graph coefficients,
        # stroke width. The line and curve share endpoint and tangent by design.
        scan_start,scan_end=(hi,lo) if reverse else (lo,hi)
        scan_join=scan_start+(scan_end-scan_start)*join
        curve_coef=coef*np.array([(1-join)**d for d in range(len(coef))])
        initial=np.r_[scan_start,scan_end,scan_join,curve_coef,width]
        def build(p):
            start,end_scan,j=p[:3]; coefficients=p[3:-1]; sw=p[-1]
            extent=end_scan-j
            def xy(t):
                v=sum(coefficients[d]*t**d for d in range(len(coefficients)))
                s=j+t*extent
                return np.array([v,s]) if axis==0 else np.array([s,v])
            joint,end=xy(0),xy(1)
            a=joint+np.array([coefficients[1],extent] if axis==0 else [extent,coefficients[1]])*((start-j)/extent)
            start_derivative=np.array([coefficients[1],extent])
            end_derivative=np.array([sum(d*coefficients[d] for d in range(1,degree+1)),extent])
            if axis==1:
                start_derivative=start_derivative[::-1]; end_derivative=end_derivative[::-1]
            controls=([joint+start_derivative/2] if degree==2 else
                      [joint+start_derivative/3,end-end_derivative/3])
            root=canvas(image)
            group=element(root,'g',**{'data-fallback-group':'open_curve_lead'})
            element(group,'line','lead',x1=a[0],y1=a[1],x2=joint[0],y2=joint[1],stroke=_hex(color),stroke_width=sw)
            d='M '+' '.join(f'{v:.9g}' for v in joint)+' '+('Q' if degree==2 else 'C')+' '+' '.join(f'{v:.9g}' for pt in controls+[end] for v in pt)
            element(group,'path','curve',d=d,fill='none',stroke=_hex(color),stroke_width=sw)
            return ET.tostring(root,encoding='unicode')
        parameters=initial
        if render_fn is not None:
            # Isolate this observed component so unrelated context never pulls
            # the fit towards an invented continuation or a different object.
            region=cv2.dilate(component.astype('uint8'),np.ones((7,7),'uint8'))>0
            def objective(p):
                if (session.time_reason() or not np.isfinite(p).all() or abs(p[0]-scan_start)>3 or abs(p[1]-scan_end)>3
                        or abs(p[2]-scan_join)>6 or abs(p[1]-p[2])<8 or not .5<p[-1]<6
                        or np.max(abs(p[3:-1]-curve_coef))>span):
                    return 1.
                raster=render_fn(build(p),image.shape[1],image.shape[0])
                session.evaluations+=1
                if raster is None:
                    return 1.
                return float(np.square(image[region].astype(float)-raster[region]).mean()/255**2)
            steps=np.r_[.3,.3,.3,.15,.3,[.3]*(len(coef)-2),.06]
            parameters=_simplex(initial,steps,objective,session)
            # Compete with an axis-parallel lead only when its observed centres
            # are constant. This removes an ill-conditioned slope fit, while
            # the same raster loss chooses between the two hypotheses.
            if np.ptp(across[lead_rows])<.12 and not session.time_reason():
                aligned=parameters.copy(); aligned[4]=0
                active=np.array([i for i in range(len(initial)) if i!=4])
                def reduced(p):
                    full=aligned.copy(); full[active]=p
                    return objective(full)
                aligned[active]=_simplex(aligned[active],steps[active],reduced,session)
                if objective(aligned)<objective(parameters):
                    parameters=aligned
        if not session.time_reason():
            yield build(parameters),'open_curve_lead'
