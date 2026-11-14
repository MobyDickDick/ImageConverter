"""Fresh CLI replay of the user's dashed-mist correction; preserve v1 evidence."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2

from tools.evaluate_spray_panel import ROOT,SOURCES as OLD_SOURCES,digest,inspect as old_inspect,controls as old_controls
from tools.check_dashed_spray_scene import check_scene
from tools.run_plan_b_variations import run_case

EVIDENCE=ROOT/'artifacts/evaluation/spray_panel_dashed_v2'
SOURCES=OLD_SOURCES+['tools/check_dashed_spray_scene.py','tools/evaluate_dashed_spray.py']


def annotation():
    seal=json.loads((EVIDENCE/'contract_seal.json').read_text(encoding='utf-8'))
    for name,sha in seal['files'].items():
        if digest(ROOT/name)!=sha:
            raise ValueError('Changed external contract: '+name)
    return json.loads((EVIDENCE/'annotation.json').read_text(encoding='utf-8'))


def inspect(svg,image,ann):
    result=old_inspect(svg,image,dict(ann,schema='spray_panel_visual_contract_v1'))
    result['native']=check_scene(svg,ann)
    result['complete']=result['native']['complete'] and all(r['passed'] for r in result['renderers'].values())
    return result


def controls(svg):
    yield from old_controls(svg)
    root=ET.fromstring(svg)
    for index in range(15):
        damaged=copy.deepcopy(root)
        line=[n for n in damaged.iter() if n.tag.rsplit('}',1)[-1]=='line'][index]
        line.attrib.pop('stroke-dasharray')
        yield f'solid_ray_{index+1}',ET.tostring(damaged,encoding='unicode')
    for kind in ['all_solid_rays','invisible_gaps','oversized_pattern','hidden_gap_phase']:
        damaged=copy.deepcopy(root)
        rays=[n for n in damaged.iter() if n.tag.rsplit('}',1)[-1]=='line']
        if kind=='all_solid_rays':
            for line in rays:
                line.attrib.pop('stroke-dasharray')
        else:
            rays[0].set('stroke-dasharray',{'invisible_gaps':'1 .001','oversized_pattern':'100 1',
                                         'hidden_gap_phase':'8 .5'}[kind])
            rays[0].set('stroke-dashoffset','0')
        yield kind,ET.tostring(damaged,encoding='unicode')


def evaluate(output):
    ann=annotation()
    source_hashes={n:digest(ROOT/n) for n in SOURCES}
    output.mkdir(parents=True,exist_ok=False)
    name='anonymous_dashed_humidifier'
    folder=output/name/'input';folder.mkdir(parents=True)
    image=cv2.imread(str(ROOT/'artifacts/evaluation/spray_panel_v1/inputs/AC0130_L.jpg'))
    cv2.imwrite(str(folder/(name+'.png')),image)
    description=(EVIDENCE/'description.txt').read_text(encoding='utf-8').strip()
    tree=ET.Element('root');entry=ET.SubElement(tree,'entry',kind='wurzelform',key=name)
    ET.SubElement(entry,'beschreibung').text=description
    ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text=name+'.png'
    ET.ElementTree(tree).write(folder/'descriptions.xml',encoding='utf-8')
    row=run_case(dict(case_id=name,width=40,height=80,description=description),output,
        timeout=220,iterations=128,extra_cli_args=('--search-seed','0','--search-seconds','150',
            '--search-max-seconds','180','--search-min-seconds','0','--search-budget','4096'))
    report=dict(cli=row,source_sha256=source_hashes,annotation_sha256=digest(EVIDENCE/'annotation.json'))
    if row.get('output_svg'):
        svg=(output/row['output_svg']).read_text(encoding='utf-8')
        report['review']=inspect(svg,image,ann)
        report['before_review']=inspect((EVIDENCE/'before.svg').read_text(encoding='utf-8'),image,ann)
        report['controls']=[dict(damage=name,review=inspect(candidate,image,ann)) for name,candidate in controls(svg)]
    report['sources_unchanged']=source_hashes=={n:digest(ROOT/n) for n in SOURCES}
    (output/'summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if (not row['satisfactory'] or row.get('blocked_svg_reads') or not report['sources_unchanged']
            or not report.get('review',{}).get('complete')
            or any(c['review']['complete'] for c in report.get('controls',[]))):
        raise AssertionError('CLI or dashed part contract failed; inspect summary')
    print('CLI and both renderers passed; '+str(len(report['controls']))+' controls rejected',flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    evaluate(parser.parse_args().output)
