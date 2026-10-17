"""Construct a catalog-independent analytic reference; never used by conversion."""
from pathlib import Path
import math
from xml.etree import ElementTree as ET


def build():
    # Deliberately different canvas, disk pose, chord angles, pitch and palette.
    root = ET.Element('svg', xmlns='http://www.w3.org/2000/svg', width='110', height='122', viewBox='0 0 110 122')
    ET.SubElement(root, 'rect', width='110', height='122', fill='#ffffff')
    # Quarter-turn counterclockwise from a 122 by 110 construction frame.
    def point(x, y):
        return y, 122-x
    x,y=point(56,51)
    ET.SubElement(root,'circle',cx=str(x),cy=str(y),r='40',fill='#b392cc',stroke='#59416b',**{'stroke-width':'1.2'})
    for slope, offset in ((-.36,-18.2),(.47,19.6)):
        a=1+slope*slope; b=2*slope*offset; c=offset*offset-40*40
        ys=[(-b-math.sqrt(b*b-4*a*c))/(2*a),(-b+math.sqrt(b*b-4*a*c))/(2*a)]
        p,q=[point(56+slope*v+offset,51+v) for v in ys]
        ET.SubElement(root,'line',x1=f'{p[0]:.6f}',y1=f'{p[1]:.6f}',x2=f'{q[0]:.6f}',y2=f'{q[1]:.6f}',stroke='#483657',**{'stroke-width':'1.4'})
    sweep=9.9; pitch=.155; start=-1.5; outer=27; count=7
    def curve(t):
        angle=start-sweep*t; r=outer*math.exp(-pitch*sweep*t)
        return (58+r*math.cos(angle),57+1.02*r*math.sin(angle))
    def derivative(t):
        angle=start-sweep*t; r=outer*math.exp(-pitch*sweep*t)
        return (sweep*r*(-pitch*math.cos(angle)+math.sin(angle)),1.02*sweep*r*(-pitch*math.sin(angle)-math.cos(angle)))
    path=['M '+' '.join(f'{v:.6f}' for v in point(*curve(0)))]
    for index in range(count):
        t=index/count; u=(index+1)/count
        a,b=curve(t),curve(u); da,db=derivative(t),derivative(u)
        controls=[(a[j]+da[j]/(3*count)) for j in (0,1)],[(b[j]-db[j]/(3*count)) for j in (0,1)],b
        path.append('C '+' '.join(f'{v:.6f}' for control in controls for v in point(*control)))
    ET.SubElement(root,'path',d=' '.join(path),fill='none',stroke='#483657',**{'stroke-width':'1.6','stroke-linecap':'round'})
    return ET.tostring(root,encoding='unicode')+'\n'


if __name__=='__main__':
    (Path(__file__).resolve().parent/'independent.svg').write_text(build(),encoding='utf-8')
