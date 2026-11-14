"""Replay the decomposed humidifier CLI and external visual contract."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from tools.check_spray_scene import check_scene
from tools.run_plan_b_variations import render,measure_quality,run_case
from tools.evaluate_svg_text_baseline import render_librsvg

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/spray_panel_v1'
SOURCES = ['src/iCCModules/imageCompositeConverterSprayPanel.py',
           'src/iCCModules/imageCompositeConverterDashedRectangles.py',
           'src/iCCModules/imageCompositeConverterNonCompositeRuntime.py',
           'src/iCCModules/imageCompositeConverterRendering.py','tools/check_spray_scene.py',
           'tools/evaluate_spray_panel.py']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def annotation():
    inputs = json.loads((EVIDENCE/'input_seal.json').read_text(encoding='utf-8'))
    for name,sha in inputs.items():
        if digest(EVIDENCE/'inputs'/name) != sha:
            raise ValueError('Changed source input: '+name)
    seal_path=EVIDENCE/'source_seal.json'
    if seal_path.exists():
        seal=json.loads(seal_path.read_text(encoding='utf-8'))
        if (digest(ROOT/'tools/check_spray_scene.py') != seal['source_sha256']['tools/check_spray_scene.py']
                or digest(EVIDENCE/'annotation.json') != seal['files']['annotation.json']):
            raise ValueError('Changed external scene contract')
    return json.loads((EVIDENCE/'annotation.json').read_text(encoding='utf-8'))


def inspect(svg, image, ann):
    result = dict(native=check_scene(svg,ann),renderers={})
    for name,fn in [('MuPDF',render),('librsvg',render_librsvg)]:
        raster = fn(svg,*ann['size'])
        regions=[]
        boxes=[('housing',[0,0,40,80]),('rail',[1,5,4,74]),('frame',[20,2,17,75])]
        boxes += [('nozzle_'+str(i+1),[4,int(cy)-2,4,5]) for i,cy in enumerate(ann['nozzle_centers'])]
        boxes += [('spray_'+str(i+1),[7,int(cy)-7,12,15]) for i,cy in enumerate(ann['spray_centers'])]
        for part,(x,y,w,h) in boxes:
            y=max(0,y);h=min(h,len(image)-y)
            mse=float(np.square(image[y:y+h,x:x+w].astype(float)-raster[y:y+h,x:x+w]).mean()/255**2)
            regions.append(dict(part=part,normalized_mse=mse,passed=mse<=ann['local_mse_limit']))
        correlations=[float(np.corrcoef(image[5:74,x,0],raster[5:74,x,0])[0,1])
                      if np.std(raster[5:74,x,0]) > 1e-6 else 0. for x in (21,35)]
        quality=measure_quality(image,svg,render_fn=fn)
        passed = quality['satisfactory'] and all(r['passed'] for r in regions)
        passed = passed and all(np.isfinite(c) and c >= ann['dash_correlation_min'] for c in correlations)
        result['renderers'][name]=dict(quality=quality,regions=regions,dash_correlations=correlations,passed=bool(passed))
    result['complete']=result['native']['complete'] and all(r['passed'] for r in result['renderers'].values())
    return result


def controls(svg):
    root=ET.fromstring(svg)
    native=[n for n in root.iter() if n.tag.rsplit('}',1)[-1] in {'rect','polygon','line'}]
    for index,node in enumerate(native):
        if node.tag.rsplit('}',1)[-1] not in {'polygon','line'}:
            continue
        damaged=copy.deepcopy(root)
        nodes=[n for n in damaged.iter() if n.tag.rsplit('}',1)[-1] in {'rect','polygon','line'}]
        victim=nodes[index]
        next(p for p in damaged.iter() if victim in list(p)).remove(victim)
        yield 'missing_'+str(index),ET.tostring(damaged,encoding='unicode')
    for kind in ('solid_frame','wrong_dash_period','missing_rail','missing_housing','missing_frame',
                 'detached_nozzle','wrong_ray','white_ray','hidden_duplicate'):
        damaged=copy.deepcopy(root)
        rects=[n for n in damaged.iter() if n.tag.rsplit('}',1)[-1]=='rect']
        polygons=[n for n in damaged.iter() if n.tag.rsplit('}',1)[-1]=='polygon']
        lines=[n for n in damaged.iter() if n.tag.rsplit('}',1)[-1]=='line']
        frame=next(n for n in rects if n.get('fill')=='none')
        if kind == 'solid_frame':
            frame.attrib.pop('stroke-dasharray')
        elif kind == 'wrong_dash_period':
            frame.set('stroke-dasharray','1 1')
        elif kind.startswith('missing_'):
            victim={'missing_rail':rects[1],'missing_housing':rects[0],'missing_frame':frame}[kind]
            next(p for p in damaged.iter() if victim in list(p)).remove(victim)
        elif kind == 'detached_nozzle':
            values=[float(v) for v in polygons[0].get('points').replace(',',' ').split()]
            polygons[0].set('points',' '.join(f'{x+3},{y}' for x,y in zip(values[::2],values[1::2])))
        elif kind == 'wrong_ray':
            lines[0].set('y2',lines[0].get('y1'))
        elif kind == 'white_ray':
            lines[0].set('stroke','#ffffff')
        else:
            damaged.insert(0,copy.deepcopy(lines[0]))
        yield kind,ET.tostring(damaged,encoding='unicode')


def evaluate(output):
    ann=annotation()
    output.mkdir(parents=True,exist_ok=False)
    name='anonymous_humidifier'
    folder=output/name/'input'
    folder.mkdir(parents=True)
    image=cv2.imread(str(EVIDENCE/'inputs/AC0130_L.jpg'))
    cv2.imwrite(str(folder/(name+'.png')),image)
    description=(EVIDENCE/'description.txt').read_text(encoding='utf-8').strip()
    tree=ET.Element('root')
    entry=ET.SubElement(tree,'entry',kind='wurzelform',key=name)
    ET.SubElement(entry,'beschreibung').text=description
    ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text=name+'.png'
    ET.ElementTree(tree).write(folder/'descriptions.xml',encoding='utf-8')
    row=run_case(dict(case_id=name,width=40,height=80,description=description),output,
        timeout=220,iterations=128,extra_cli_args=('--search-seed','0','--search-seconds','120',
        '--search-max-seconds','180','--search-min-seconds','0','--search-budget','4096'))
    report=dict(cli=row,source_sha256={name:digest(ROOT/name) for name in SOURCES},
        annotation_sha256=digest(EVIDENCE/'annotation.json'),real_holdout=False)
    if row.get('output_svg'):
        svg=(output/row['output_svg']).read_text(encoding='utf-8')
        report['review']=inspect(svg,image,ann)
        report['baseline_review']=inspect((EVIDENCE/'baseline.svg').read_text(encoding='utf-8'),image,ann)
        report['controls']=[dict(damage=name,review=inspect(candidate,image,ann)) for name,candidate in controls(svg)]
    (output/'summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if (not row['satisfactory'] or row.get('blocked_svg_reads') or not report.get('review',{}).get('complete')
            or any(c['review']['complete'] for c in report.get('controls',[]))):
        raise AssertionError('CLI/local part/native contract regression; inspect summary')
    print('CLI and both renderers passed; '+str(len(report['controls']))+' rejected controls',flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    evaluate(parser.parse_args().output)
