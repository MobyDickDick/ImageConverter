"""Bounded independent check of a native crossed panel with stacked +/-.

No fitter parameters, SVG IDs, filenames, source vectors or runtime inventory
are used. Unknown geometry is unverified rather than certified by pixel error.
This contract currently supports native rectangles and clipped convex bands.
"""
import math
import re
from xml.etree import ElementTree as ET

import numpy as np


def required(description):
    from src.iCCModules.imageCompositeConverterCrossedGradientPanel import crossed_panel_contract
    return crossed_panel_contract(description,stacked_marks=True)


def check_scene(svg,width,height,*,reference=None,rendered=None):
    checks = {}
    def need(name,value):
        checks[name] = bool(value)
        if not value:
            raise ValueError(name)
    def number(node,key,default='0'):
        value = float(node.get(key,default))
        if not math.isfinite(value):
            raise ValueError('nonfinite_geometry')
        return value
    def gray(color):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',color or ''):
            raise ValueError('unverified_paint')
        rgb = [int(color[i:i+2],16) for i in (1,3,5)]
        if max(rgb)-min(rgb)>2:
            raise ValueError('chromatic_paint')
        return sum(rgb)/3
    def box(node):
        return np.array([number(node,k) for k in ('x','y','width','height')])
    try:
        root = ET.fromstring(svg)
        need('viewport',[number(root,'width'),number(root,'height')]==[width,height])
        need('coordinate_system',list(map(float,root.get('viewBox','').split()))==[0,0,width,height])
        gradients = {n.get('id'):n for n in root.iter() if n.tag.rsplit('}',1)[-1]=='linearGradient'}
        clips = {n.get('id'):n for n in root.iter() if n.tag.rsplit('}',1)[-1]=='clipPath'}
        nodes = []
        allowed = {'svg','g','defs','linearGradient','stop','clipPath','rect','polygon','line','desc','title','metadata'}
        forbidden = {'transform','style','opacity','fill-opacity','stroke-opacity','mask','filter','display','visibility','marker-start','marker-end','marker-mid'}
        def walk(node,inherited,in_defs=False):
            tag = node.tag.rsplit('}',1)[-1]
            need('native_supported_geometry',tag in allowed and not (forbidden & node.attrib.keys()))
            attrs = dict(inherited,**node.attrib)
            if tag in {'rect','polygon','line'} and not in_defs:
                nodes.append((node,attrs))
            for child in node:
                walk(child,attrs,in_defs or tag=='defs')
        walk(root,{})
        panels = [(n,a) for n,a in nodes if n.tag.endswith('rect') and a.get('fill','').startswith('url(#')]
        need('one_housing',len(panels)==1)
        panel,paint = panels[0]
        l,t,w,h = box(panel);r,b=l+w,t+h
        need('portrait_housing',0<=l<r<=width and 0<=t<b<=height and h>w>0)
        gradient = gradients.get(paint['fill'][5:-1])
        need('housing_gradient',gradient is not None)
        need('horizontal_gradient',number(gradient,'y1')==number(gradient,'y2') and number(gradient,'x2')>number(gradient,'x1'))
        stops = [(float(n.get('offset','0').rstrip('%'))/(100 if n.get('offset','').endswith('%') else 1),gray(n.get('stop-color')))
                 for n in gradient if n.tag.endswith('stop')]
        need('gray_highlight',3<=len(stops)<=4 and all(math.isfinite(o) for o,_ in stops)
             and stops==sorted(stops) and stops[0][0]==0 and stops[-1][0]==1
             and max(c for _,c in stops[1:-1])>max(stops[0][1],stops[-1][1])+8)
        rims = [(n,a) for n,a in nodes if n.tag.endswith('rect') and a.get('fill')=='none' and a.get('stroke','none')!='none']
        need('one_frame',len(rims)==1)
        rim,attrs = rims[0]
        need('frame_matches_housing',np.max(abs(box(rim)-box(panel)))<.02 and 0<number(rim,'stroke-width','1')<w*.12)
        need('frame_contrast',gray(attrs['stroke'])<min(stops[0][1],stops[-1][1]))
        for _,a in nodes:
            if 'clip-path' in a:
                match = re.fullmatch(r'url\(#([^)]*)\)',a['clip-path'])
                clip = clips.get(match[1]) if match else None
                rects = list(clip) if clip is not None else []
                need('actual_frame_clip',len(rects)==1 and rects[0].tag.endswith('rect') and np.max(abs(box(rects[0])-box(panel)))<.02)
        marks,bands,backgrounds = [],[],[]
        for node,a in nodes:
            if node is panel or node is rim:
                continue
            tag = node.tag.rsplit('}',1)[-1]
            if tag=='rect':
                value = a.get('fill','#000000')
                if value in {'white','#ffffff','#FFFFFF'}:
                    need('white_canvas',np.max(abs(box(node)-[0,0,width,height]))<.02)
                    backgrounds.append(node)
                else:
                    x,y,W,H = box(node)
                    need('native_mark',W>0 and H>0 and l<x<x+W<r and t<y<y+H<b and gray(value)<min(c for _,c in stops)-10)
                    marks.append((x,y,W,H))
            elif tag=='polygon':
                numeric = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
                data = node.get('points','')
                need('numeric_points',not re.sub(numeric,'',data).strip(' ,\t\r\n'))
                values = np.array([float(v) for v in re.findall(numeric,data)])
                need('band_polygon',len(values)%2==0 and 8<=len(values)<=16 and np.isfinite(values).all())
                points = values.reshape(-1,2)
                need('bands_are_clipped',np.all(points[:,0]>=l-1e-4) and np.all(points[:,0]<=r+1e-4)
                     and np.all(points[:,1]>=t-1e-4) and np.all(points[:,1]<=b+1e-4))
                need('band_contrast',gray(a.get('fill'))<min(c for _,c in stops)-10)
                bands.append(points)
            elif tag=='line':
                need('no_unbounded_strokes',False)
        need('no_extra_ink',len(backgrounds)<=1 and len(marks)==3 and len(bands)==2)
        directions=[]
        for points in bands:
            need('complete_arm',np.ptp(points[:,0])>w*.8 and np.ptp(points[:,1])>h*.9)
            # A diagonal band must be convex and narrow; unrelated polygons
            # or extra center spikes cannot supply a complete diagonal.
            first = np.roll(points,-1,axis=0)-points
            second = np.roll(points,-2,axis=0)-np.roll(points,-1,axis=0)
            turns = first[:,0]*second[:,1]-first[:,1]*second[:,0]
            need('convex_band',np.all(turns>=-1e-5) or np.all(turns<=1e-5))
            cov = np.cov(points.T)
            directions.append(np.sign(cov[0,1]))
            eigen = np.linalg.eigvalsh(cov)
            need('thin_diagonal',eigen[0]<eigen[1]*.03)
        need('two_opposite_diagonals',set(directions)=={-1,1})
        horizontal = sorted([m for m in marks if m[2]>m[3]*2],key=lambda m:m[1])
        vertical = [m for m in marks if m[3]>m[2]*2]
        need('plus_and_minus',len(horizontal)==2 and len(vertical)==1)
        cross,minus = horizontal;vert=vertical[0]
        cx,cy,cw,ch=cross;vx,vy,vw,vh=vert;mx,my,mw,mh=minus
        need('plus_intersection',cx<vx<vx+vw<cx+cw and vy<cy<cy+ch<vy+vh)
        need('visible_marks',min(cw,mw)>w*.1 and min(ch,mh,vw)>.25 and vh>h*.04)
        need('stacked_signs',my>vy+vh and my+mh<t+h*.35 and abs(cx+cw/2-(mx+mw/2))<w*.08)
        need('centered_marks',abs(cx+cw/2-(l+r)/2)<w*.15 and abs(vx+vw/2-(cx+cw/2))<w*.03)
        if reference is not None and rendered is not None:
            import cv2
            delta = np.square(reference.astype(float)-rendered.astype(float)).mean(axis=2)/255**2
            for index,points in enumerate(bands,1):
                mask = np.zeros((height,width),np.uint8)
                cv2.fillPoly(mask,[np.rint(points-.5).astype(np.int32)],1)
                need(f'arm_{index}_local_pixels',bool(mask.any()) and float(delta[mask>0].mean())<.02)
            for name,region in [('plus',(min(cx,vx),min(cy,vy),max(cx+cw,vx+vw),max(cy+ch,vy+vh))),
                                ('minus',(mx,my,mx+mw,my+mh))]:
                x,y,X,Y = region
                roi = delta[max(0,int(y)-1):min(height,int(math.ceil(Y))+1),max(0,int(x)-1):min(width,int(math.ceil(X))+1)]
                need(name+'_local_pixels',roi.size>0 and float(roi.mean())<.02)
        return dict(passed=True,checks=checks,schema='crossed_panel_native_scene_v1')
    except (ValueError,TypeError,KeyError,IndexError,ET.ParseError) as exc:
        return dict(passed=False,checks=checks,reason=str(exc),schema='crossed_panel_native_scene_v1')
