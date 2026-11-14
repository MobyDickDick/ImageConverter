"""A separate stricter development contract requiring 15 genuinely dashed rays.

The sealed first checker remains unchanged. It verifies the native geometric
envelopes after dash paint is removed from a private copy. This checker adds
the mandatory paint/gap contract to every logical ray, without granting extra
geometry or relaxing the existing scene inventory and connections.
"""
from __future__ import annotations

import math
from xml.etree import ElementTree as ET

from tools.check_spray_scene import check_scene as check_geometry


def check_scene(svg,annotation):
    try:
        if annotation['schema'] != 'spray_panel_dashed_rays_contract_v2':
            raise ValueError('Wrong annotation schema')
        root=ET.fromstring(svg)
        rays=[n for n in root.iter() if n.tag.rsplit('}',1)[-1]=='line']
        checks=[]
        for line in rays:
            dash=[float(v) for v in line.get('stroke-dasharray','').split()]
            offset=float(line.get('stroke-dashoffset','0'))
            if len(dash)!=2 or not all(math.isfinite(v) and v>0 for v in dash) or not math.isfinite(offset):
                raise ValueError('Every ray needs a finite explicit dash/gap pattern')
            period=sum(dash)
            length=math.hypot(float(line.get('x2'))-float(line.get('x1')),
                              float(line.get('y2'))-float(line.get('y1')))
            # Count actual gap intervals in the finite line, not just an
            # attribute that could place every gap beyond its endpoints.
            phase=offset%period
            gaps=[]
            for k in range(-1,int(length/period)+2):
                lo=max(0,k*period+dash[0]-phase)
                hi=min(length,(k+1)*period-phase)
                if hi-lo>=annotation['min_gap']:
                    gaps.append([lo,hi])
            passed=(annotation['period_range'][0] <= period <= annotation['period_range'][1]
                    and dash[1]>=annotation['min_gap'] and .4 <= dash[0]/period <= .8 and len(gaps)>=2)
            checks.append(dict(passed=passed,dash=dash,offset=offset,gaps=gaps))
            line.attrib.pop('stroke-dasharray',None)
            line.attrib.pop('stroke-dashoffset',None)
        geom_ann=dict(annotation,schema='spray_panel_visual_contract_v1')
        geometry=check_geometry(ET.tostring(root,encoding='unicode'),geom_ann)
        complete=len(checks)==15 and all(r['passed'] for r in checks) and geometry['complete']
        return dict(complete=complete,geometry=geometry,rays=checks,
                    reason='passed' if complete else 'ray_paint_or_geometry')
    except (ValueError,TypeError,KeyError,OverflowError,ET.ParseError) as exc:
        return dict(complete=False,reason='unsupported_or_invalid',error=str(exc))
