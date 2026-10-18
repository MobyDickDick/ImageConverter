"""Compare fixed and adaptive production CLI searches on protected source copies."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import cv2
from tools.run_plan_b_variations import render,measure_quality
from tools.evaluate_primitive_scene import make_cases,check_objects
from tools.evaluate_motor_valve_recheck import symbol_semantics as motor_semantics
from tools.evaluate_labeled_disk_recheck import symbol_semantics as letter_semantics
from tools.evaluate_short_label_search import symbol_semantics as label_semantics

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--resume-fixed',action='store_true',help='Keep the already completed fixed CLI control after an evidence-collector interruption')
    parser.add_argument('--adaptive-dirname',default='adaptive')
    args=parser.parse_args()
    output=args.output_dir.resolve()
    output.mkdir(parents=True,exist_ok=args.resume_fixed)
    inputs=output/'sources'
    inputs.mkdir(exist_ok=args.resume_fixed)
    catalog=ET.parse(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml')
    cases=[]
    for variant,kind,label in [('AC0232_L','motor','M'),('AC0232_M','motor','M'),('AC0232_S','motor','M'),
                               ('AC0921_M','letter','Q'),('AC0840_M','label','rF'),('AC0910_S','label','Lux')]:
        source=ROOT/'artifacts/images_to_convert'/(variant+'.jpg')
        entry=next(e for e in catalog.iter('entry') if source.name in [p.text for p in e.findall('bilder/bild')])
        name=f'anonymous_{len(cases):02}'
        image=inputs/(name+'.jpg')
        shutil.copyfile(source,image)
        cases.append(dict(case_id=name,source=variant,kind=kind,label=label,image=image.name,
            source_sha256=digest(image),description=entry.findtext('beschreibung')))
    for case in make_cases(43123,9)[-2:]:
        name=f'anonymous_{len(cases):02}'
        image=inputs/(name+'.png')
        cv2.imwrite(str(image),render(case['svg'],case['width'],case['height']))
        cases.append(dict(case_id=name,source='independent_primitives',kind='primitives',
            expected_objects=case['expected_objects'],image=image.name,source_sha256=digest(image),description=case['description']))
    report=dict(cases=cases,policies={})
    for policy in ('fixed','adaptive'):
        folder=output/(policy if policy=='fixed' else args.adaptive_dirname)
        folder.mkdir(exist_ok=args.resume_fixed and policy=='fixed')
        table=ET.Element('root')
        for case in cases:
            shutil.copyfile(inputs/case['image'],folder/case['image'])
            entry=ET.SubElement(table,'entry',kind='wurzelform',key=case['case_id'])
            ET.SubElement(entry,'beschreibung').text=case['description']
            ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text=case['image']
        descriptions=folder/'descriptions.xml'
        ET.ElementTree(table).write(descriptions,encoding='utf-8',xml_declaration=True)
        conversion=folder/'conversion'
        command=[sys.executable,'-m','tools.run_labeled_disk_recheck','--_worker',policy,str(conversion),str(folder),
            '--descriptions-path',str(descriptions),'--output-dir',str(conversion),'--start',cases[0]['case_id'],
            '--end',cases[-1]['case_id'],'--execution-mode','semantic-only','--deterministic-order',
            '--search-policy',policy,'--search-seed','20261018']
        env=dict(os.environ,IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0',TINY_ICC_OUTPUT_VARIATION='0',PYTHONHASHSEED='0',PYTHONIOENCODING='utf-8')
        if not (args.resume_fixed and policy=='fixed'):
            with (folder/'cli.log').open('w',encoding='utf-8') as log:
                subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=360)
        access=json.loads((folder/'reference_access.json').read_text(encoding='utf-8'))
        assert not access['blocked_svg_reads']
        rows=json.loads((conversion/'reports/conversion_result_map.json').read_text(encoding='utf-8'))
        records=[]
        for case in cases:
            matches=[p for d in ('converted_svgs','converted_svg_failed') for p in (conversion/d).glob('*.svg')
                if p.stem.casefold()==case['case_id'].casefold()]
            assert len(matches)==1,case['case_id']
            svg=matches[0].read_text(encoding='utf-8')
            image=cv2.imread(str(inputs/case['image']))
            quality=measure_quality(image,svg)
            semantic=(motor_semantics(svg) if case['kind']=='motor' else
                letter_semantics(svg,'Q',bottom_stem=True) if case['kind']=='letter' else
                label_semantics(svg,case['label']) if case['kind']=='label' else
                float(check_objects(render(svg,image.shape[1],image.shape[0]),case['expected_objects'])['passed']))
            row=rows[case['image']]
            registration=row['params'].get('labeled_disk_registration',row['params'].get('primitive_scene_registration',{}))
            records.append(dict(case_id=case['case_id'],source=case['source'],quality=quality,semantic_score=semantic,
                search_control=row.get('search_control'),satisfactory=row.get('search_satisfactory'),
                fit_evaluations=registration.get('evaluations'),elapsed_seconds=row['elapsed_seconds'],
                output_svg=matches[0].relative_to(output).as_posix(),output_sha256=digest(matches[0])))
            assert (policy=='fixed' or quality['satisfactory']) and semantic==1.,(policy,case['case_id'],quality,semantic)
        report['policies'][policy]=dict(cases=records,reference_access=access)
        (output/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        print(policy,[(r['source'],r['fit_evaluations'],r['satisfactory']) for r in records],flush=True)
    assert all(c['satisfactory'] for c in report['policies']['adaptive']['cases'])

if __name__=='__main__':
    main()
