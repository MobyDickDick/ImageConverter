"""Optional observed starts for a completely declared native scene.

These measurements only propose parameters for existing objects. They cannot
add shapes, accept a conversion, or replace the population's independent starts.
"""
from __future__ import annotations

import math
import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterSceneProgram import STRIDE, geometry


def observed_scene_parameters(program, image):
    if not program:
        return None
    kinds=[o['kind'] for o in program['objects']]
    if sorted(kinds)!=sorted(['circle','line','triangle','triangle','triangle','text']):
        return None
    attached=next((r for r in program['relations'] if r['kind']=='attached'),None)
    if attached is None or attached['direction'] is None:
        return None
    # Canonical coordinates have the actuator on the right. Quarter rotations
    # are exact pixel permutations; text is measured again in original space.
    direction=attached['direction']
    turns=int(round((direction-math.pi)/(math.pi/2)))%4
    pixels=np.rot90(np.asarray(image),turns).astype(float)
    h,w=pixels.shape[:2]
    background=np.median(np.concatenate((pixels[0],pixels[-1],pixels[:,0],pixels[:,-1])),axis=0)
    mask=np.max(abs(pixels-background),axis=2)>35
    ys,xs=np.nonzero(mask)
    if len(xs)<40:
        return None
    contours=cv2.findContours(mask.astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0]
    contour=max(contours,key=cv2.contourArea)[:,0].astype(float)+.5
    arc=contour[contour[:,0]>xs.max()+1-h*.30]
    if len(arc)<8:
        return None
    coeff=np.linalg.lstsq(np.c_[2*arc,np.ones(len(arc))],np.square(arc).sum(axis=1),rcond=None)[0]
    cx,cy=coeff[:2]
    outer=math.sqrt(max(0.,coeff[2]+cx*cx+cy*cy))
    if not 4<outer<h*.48 or np.mean(abs(np.linalg.norm(arc-[cx,cy],axis=1)-outer))>1.:
        return None
    yy,xx=np.indices((h,w),dtype=float)
    head=mask & (xx+.5<cx-outer-1)
    hy,hx=np.nonzero(head)
    if len(hx)<20:
        return None
    top,bottom,left=hy.min()+.5,hy.max()+.5,hx.min()+.5
    samples=[]
    for row in range(int(top)+1,int(top+(cy-top)*.6)):
        cols=np.flatnonzero(head[row])
        if len(cols)>=3 and cols[0]>left+2:
            samples.append([row+.5,cols[0]+.5,cols[-1]+.5])
    if len(samples)<3:
        return None
    samples=np.array(samples)
    fits=[np.polyfit(samples[:,0],samples[:,i],1) for i in (1,2)]
    ax=float(np.mean([np.polyval(f,cy) for f in fits]))
    upper=np.flatnonzero(head[int(top)])+.5
    lower=np.flatnonzero(head[int(bottom)])+.5
    left_rows=np.flatnonzero(head[:,int(left)])+.5
    if min(len(upper),len(lower),len(left_rows))<3 or not left<ax<cx-outer:
        return None
    radius=outer-.75
    p=np.full((len(kinds),STRIDE),.5)
    by_kind={kind:[i for i,k in enumerate(kinds) if k==kind] for kind in set(kinds)}
    def set_shape(i,center,size,angle=0.,stroke=1.5):
        p[i,:6]=[* (np.array(center)/[w,h]),* (np.array(size)/[w,h]),angle/(2*math.pi)%1,
                  stroke/(.1*min(w,h))]
    set_shape(by_kind['circle'][0],[cx,cy],[radius*2]*2,stroke=1.7)
    set_shape(by_kind['line'][0],[(ax+cx-radius)/2,cy],[cx-radius-ax,1],math.pi,2.)
    specs=[([ (ax+left+.5)/2,cy],[ax-left-.5,np.ptp(left_rows)-1],0.),
           ([ax,(cy+top+.5)/2],[cy-top-.5,np.ptp(upper)-1],math.pi/2),
           ([ax,(cy+bottom-.5)/2],[bottom-cy-.5,np.ptp(lower)-1],-math.pi/2)]
    for i,(center,size,angle) in zip(by_kind['triangle'],specs):
        set_shape(i,center,size,angle,1.4)
    # Transform the parameter proposal back to the source coordinate system.
    H,W=image.shape[:2]
    for row in p:
        x,y=row[:2]*[w,h]
        for _ in range(turns):
            x,y=h-y,x
            w,h=h,w
        row[:2]=[x/W,y/H]
        # Reset dimensions after each object's inverse coordinate transform.
        w,h=pixels.shape[1],pixels.shape[0]
        sx,sy=row[2:4]*[w,h]
        row[2:4]=[sx/W,sy/H]
        row[4]=(row[4]+turns*.25)%1
    # Estimate paint on each declared interior, using a linear field rather
    # than importing an SVG, a filename-specific palette or residual contours.
    shapes=geometry(program,p,W,H)
    source=np.asarray(image,dtype=float)
    for obj,row in zip(program['objects'],p):
        shape=shapes[obj['id']]
        coverage=np.zeros((H,W),dtype='uint8')
        if obj['kind']=='triangle':
            cv2.fillConvexPoly(coverage,np.rint(shape['points']-.5).astype('int32'),1)
            core=cv2.erode(coverage,np.ones((3,3),dtype='uint8')).astype(bool)
            iy,ix=np.nonzero(core)
            if len(ix)>5:
                matrix=np.c_[np.ones(len(ix)),ix+.5,iy+.5]
                field=np.linalg.lstsq(matrix,source[core],rcond=None)[0]
                slope=field[1:].mean(axis=1)
                angle=math.atan2(slope[1],slope[0])
                pts=shape['points']; lo=pts.min(axis=0); hi=pts.max(axis=0)
                dx,dy=math.cos(angle),math.sin(angle); extent=(abs(dx)+abs(dy))/2
                center=(lo+hi)/2; span=(hi-lo)*[dx,dy]*extent
                colors=np.array([[1,*(center-span)],[1,*(center+span)]])@field
                row[6:9]=np.clip(colors[0][::-1]/255,0,1)
                row[12:15]=np.clip(colors[1][::-1]/255,0,1)
                row[15]=1.; row[16]=angle/(2*math.pi)%1
        row[9:12]=.55
    circle=shapes['circle_0']; center=circle['center']; radius=circle['size'][0]/2
    yy,xx=np.indices((H,W)); distance=np.hypot(xx+.5-center[0],yy+.5-center[1])
    interior=source[(distance<radius*.8)]
    if not len(interior):
        return None
    fill=np.percentile(interior,85,axis=0)
    glyph=(distance<radius*.8)&(np.mean(fill-source,axis=2)>35)
    gy,gx=np.nonzero(glyph)
    if len(gx)<4:
        return None
    ci=by_kind['circle'][0]; ti=by_kind['text'][0]
    p[ci,6:9]=fill[::-1]/255; p[ci,15]=.5
    p[ti,:2]=center/[W,H]
    p[ti,2:4]=[(np.ptp(gx)+1)/W,(np.ptp(gy)+1)/(.72*H)]
    p[ti,4]=0.; p[ti,6:9]=np.percentile(source[glyph],15,axis=0)[::-1]/255
    return np.clip(p,0.,1.).ravel()
