"""Reproduce layered contour conversion and independent renderer evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from PIL import Image, ImageDraw

from src.iCCModules.imageCompositeConverterDescriptions import loadCatalogDescriptionMappingImpl
from src.iCCModules.imageCompositeConverterPiecewiseScene import (
    fit_piecewise_scene, load_piecewise_companions, align_piecewise_companions,
)
from tools.evaluate_svg_text_baseline import render_librsvg
from tools.run_plan_b_variations import measure_quality, render

ROOT = Path(__file__).resolve().parents[1]


def arc_diagnostic(svg):
    root = ET.fromstring(svg)
    arcs = []
    for path in root.findall('{*}path'):
        commands = re.findall(r'[MCZ][^MCZ]*', path.get('d', ''))
        point = None
        for command in commands:
            if command[0] == 'M':
                point = command[1:].strip()
            elif command[0] == 'C':
                values = command[1:].split()
                color = ('#d93240', '#008a78', '#7744bb', '#d17b00')[len(arcs) % 4]
                arcs.append(f'<path d="M {point} {command}" stroke="{color}" '
                            f'stroke-width=".65" fill="none"/>')
                point = ' '.join(values[-2:])
    root[:] = []
    for arc in arcs:
        root.append(ET.fromstring(arc))
    return ET.tostring(root, encoding='unicode')


def evaluate(path, output, descriptions):
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f'Cannot read {path}')
    h, w = image.shape[:2]
    description = descriptions[path.stem]
    args = dict(description=description, image=image, render_fn=render,
                error_fn=lambda a,b: float(np.mean((a.astype(float)-b)**2)))
    companions = load_piecewise_companions(path)
    single = fit_piecewise_scene(w,h,**args)
    result = fit_piecewise_scene(w,h,companion_images=companions,**args)
    if result is None:
        return dict(input=str(path), passed=False, reason='unsupported_or_failed_local_checks')
    directory = output/path.stem
    directory.mkdir(parents=True,exist_ok=True)
    svg = result['svg']
    (directory/'result.svg').write_text(svg,encoding='utf-8')
    (directory/'background.svg').write_text(result['background_svg'],encoding='utf-8')
    diagnostic = arc_diagnostic(svg)
    (directory/'arcs.svg').write_text(diagnostic,encoding='utf-8')
    renderers = {name:measure_quality(image,svg,render_fn=renderer)
                 for name,renderer in [('mupdf',render),('librsvg',render_librsvg)]}
    independent = render_librsvg(svg,w,h)
    cv2.imwrite(str(directory/'result.png'),independent)
    original = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
    predicted = cv2.cvtColor(render_librsvg(svg,280,280),cv2.COLOR_BGR2RGB)
    difference = np.clip(abs(image.astype(float)-independent)*5,0,255).astype('uint8')
    background = cv2.cvtColor(render_librsvg(result['background_svg'],280,280),cv2.COLOR_BGR2RGB)
    arcs = cv2.cvtColor(render_librsvg(diagnostic,280,280),cv2.COLOR_BGR2RGB)
    aligned, _ = align_piecewise_companions(image,companions)
    overlay = original.copy()//2+127
    for candidate,color in zip([image]+aligned,[(0,100,255),(230,30,30),(0,150,50)]):
        edge = cv2.Canny(candidate,50,140)>0
        overlay[edge] = color
    # Preview is deliberately enlarged: input information remains 50–70 pixels.
    panel = Image.new('RGB',(3*280,2*310),'white')
    draw = ImageDraw.Draw(panel)
    images = [original,background,overlay,arcs,predicted,cv2.cvtColor(difference,cv2.COLOR_BGR2RGB)]
    labels = ['Original','1: Kreis + Verlauf','Ausrichtung: L/M/S Konturen',
              '2: einzelne Kurvenabschnitte','3: verschmolzene Pfade','Differenz x5 (JPEG inklusive)']
    for i,(pixels,label) in enumerate(zip(images,labels)):
        x,y = (i%3)*280,(i//3)*310
        panel.paste(Image.fromarray(pixels).resize((280,280)),(x,y))
        draw.text((x+6,y+286),label,fill='black')
    panel.save(directory/'comparison.png')
    report = {k:v for k,v in result.items() if k not in {'svg','rendered','background_svg'}}
    report.update(input=str(path), source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  description=description, independent_renderers=renderers,
                  single_error=single['error'] if single else None,
                  consensus_gain_percent=(100*(single['error']-result['error'])/single['error']) if single else None,
                  passed=bool(all(r['satisfactory'] for r in renderers.values())
                              and result['details']['passed']))
    (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('images',nargs='+',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    descriptions = loadCatalogDescriptionMappingImpl(ROOT)
    reports = [evaluate(path,args.output,descriptions) for path in args.images]
    summary = dict(passed=sum(r['passed'] for r in reports), total=len(reports),cases=reports)
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k != 'cases'}))
    return 0 if all(r['passed'] for r in reports) else 1


if __name__ == '__main__':
    raise SystemExit(main())
