"""Probe phrase sensitivity and primitive multiplicity through the real CLI."""
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import cv2
from src.iCCModules import imageCompositeConverterGeometryIr as ir
from tools.perception_detection_contract import (
    PerceptionPrimitiveCandidate, detect_perception_candidates,
    build_perception_seeded_geometry_ir, merge_perception_candidates_into_geometry_ir,
)
from tools.run_plan_b_variations import render, run_case, sha256


def candidate(kind, x, y, width, height, canvas):
    w,h=canvas
    geometry={'geometry_ir_bbox':[x/w,y/h,width/w,height/h],
              'stroke_width_px':4, 'radius_px':width/2}
    return PerceptionPrimitiveCandidate(schema_version='perception_primitive_v1',kind=kind,
        bbox=dict(x=x,y=y,width=width,height=height),center=dict(x=x+width/2,y=y+height/2),
        geometry=geometry,color=dict(fill_hex='none',stroke_hex='#333333'),confidence=.99,
        roi={},evidence={'detector':'independent_known_geometry'},source='diagnostic_oracle')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=False)
    os.environ['IMAGE_CONVERTER_ISOLATE_SVG_RENDER']='0'
    family=ROOT/'artifacts/evaluation/down_gradient_junction_recheck_v1'
    junction=(family/'independent.svg').read_text(encoding='utf-8')
    description=json.loads((family/'manifest.json').read_text(encoding='utf-8'))['description']
    def svg(shapes):
        return '<svg xmlns="http://www.w3.org/2000/svg" width="160" height="104"><rect width="160" height="104" fill="#ffffff"/>'+shapes+'</svg>'
    ring='<circle cx="44" cy="52" r="23" fill="none" stroke="#333333" stroke-width="4"/>'
    rectangle='<rect x="18" y="26" width="44" height="52" fill="none" stroke="#333333" stroke-width="4"/>'
    cases=[
        ('junction_control',junction,description,156,124),
        ('junction_paraphrase',junction,description.replace('heller Mitte','heller zentraler Zone'),156,124),
        ('one_circle',svg(ring),'Ein Kreis mit dunkler Kontur und weißem Inneren auf weißem Hintergrund. Keine Beschriftung.',160,104),
        ('two_circles',svg(ring+ring.replace('cx="44"','cx="116"')),'Zwei voneinander getrennte Kreise mit dunkler Kontur und weißem Inneren nebeneinander auf weißem Hintergrund. Keine Beschriftung.',160,104),
        ('one_rectangle',svg(rectangle),'Ein Rechteck mit dunkler Kontur und weißem Inneren auf weißem Hintergrund. Keine Beschriftung.',160,104),
        ('two_rectangles',svg(rectangle+rectangle.replace('x="18"','x="98"')),'Zwei voneinander getrennte Rechtecke mit dunkler Kontur und weißem Inneren nebeneinander auf weißem Hintergrund. Keine Beschriftung.',160,104),
    ]
    results=[]
    for name,source,text,w,h in cases:
        case_dir=output/name;inputs=case_dir/'input';inputs.mkdir(parents=True)
        reference=output/(name+'.svg');reference.write_text(source,encoding='utf-8',newline='\n')
        image=render(source,w,h);image_path=inputs/(name+'.png');assert cv2.imwrite(str(image_path),image)
        table=ET.Element('root');entry=ET.SubElement(table,'entry',kind='wurzelform',key=name)
        ET.SubElement(entry,'beschreibung').text=text
        ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text=image_path.name
        ET.ElementTree(table).write(inputs/'descriptions.xml',encoding='utf-8',xml_declaration=True)
        detections=detect_perception_candidates(image,description=text)
        seeded=build_perception_seeded_geometry_ir(image,description=text)
        c=dict(case_id=name,description=text,width=w,height=h,reference_svg=name+'.svg',
               reference_svg_sha256=sha256(reference.read_bytes()),input_sha256=sha256(image_path.read_bytes()))
        result=run_case(c,output,timeout=90,iterations=64)
        status_lines=[]
        for p in (case_dir/'conversion').rglob('*validation*.log'):
            status_lines.extend(line for line in p.read_text(encoding='utf-8',errors='replace').splitlines() if line.startswith(('status=','selection_reason=')))
        result['description_ir_kinds']=dict(Counter(e['kind'] for e in ir.buildGeometryIrFromDescriptionImpl(text)))
        result['detected_kinds']=dict(Counter(c.kind for c in detections))
        result['detected_circles']=[c.to_dict() for c in detections if c.kind in {'circle','ring'}]
        result['seeded_ir_kinds']=dict(Counter(e['kind'] for e in seeded))
        result['validation_status']=status_lines
        result['rendering_source']='synthetic analytic SVG; actual saved CLI output independently re-rendered'
        results.append(result)
        (output/'report.json').write_text(json.dumps(dict(cases=results),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(name,result.get('satisfactory'),result.get('metrics'),flush=True)
    oracle=[]
    for kind in ['circle','rectangle']:
        candidates=[candidate(kind,20,28,44,44,(160,104)),candidate(kind,100,28,44,44,(160,104))]
        merged=merge_perception_candidates_into_geometry_ir(render(svg(''),160,104),candidates,[])
        oracle.append(dict(kind=kind,input_candidates=2,output_kinds=dict(Counter(e['kind'] for e in merged)),
                           note='Isolation probe with perfect distinct candidates; not a detector-quality claim'))
    fusion_calls=[]
    for path in (ROOT/'src').rglob('*.py'):
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
                if name=='fuse_description_constraints_with_perception_candidates':
                    fusion_calls.append(dict(path=path.relative_to(ROOT).as_posix(),line=node.lineno))
    report=dict(schema_version='reconstruction_bottleneck_probe_v1',
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        cases=results,oracle_merge_probes=oracle,production_fusion_calls=fusion_calls,
        limits='Six targeted diagnostics, not a representative catalog benchmark. No runtime edits.',
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in [
            'src/iCCModules/imageCompositeConverterNonCompositeRuntime.py',
            'src/iCCModules/imageCompositeConverterGradientJunction.py',
            'src/iCCModules/imageCompositeConverterGeometryIr/runtime.py',
            'tools/perception_detection_contract.py',
            'tools/build_holdout_ablation_matrix.py',
            'tools/run_end_to_end_holdout_acceptance.py']})
    (output/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(oracle_merge_probes=oracle,production_fusion_calls=fusion_calls),indent=2))


if __name__=='__main__':
    main()
