"""Replay both description contexts through the guarded production CLI."""
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
from tools.evaluate_motor_valve_recheck import evaluate

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    output=args.output_dir.resolve()
    output.mkdir(parents=True,exist_ok=False)
    original=json.loads((FOLDER/'manifest.json').read_text(encoding='utf-8'))
    reports={}
    for context in ('neutral','catalog'):
        folder=output/context
        folder.mkdir()
        manifest=json.loads(json.dumps(original))
        for case in manifest['cases']:
            if context == 'catalog':
                case['case_id']=Path(case['source']).stem
            case['image']='inputs/'+case['case_id']+'.jpg'
            target=folder/case['image']
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(ROOT/'artifacts/images_to_convert'/case['source'],target)
            assert hashlib.sha256(target.read_bytes()).hexdigest()==case['source_sha256']
        access={}
        for mode in ('before','after'):
            inputs=folder/('inputs_'+mode)
            inputs.mkdir()
            table=ET.Element('root')
            for case in manifest['cases']:
                shutil.copyfile(folder/case['image'],inputs/Path(case['image']).name)
                entry=ET.SubElement(table,'entry',kind='wurzelform',key=case['case_id'])
                ET.SubElement(entry,'beschreibung').text=case['baseline_description'] if mode=='before' else case['description']
                ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text=Path(case['image']).name
            description=inputs/'descriptions.xml'
            if context=='catalog':
                if mode=='before':
                    description.write_bytes(subprocess.check_output(['git','show',original['provenance']['commit']+
                        ':artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'],cwd=ROOT))
                else:
                    shutil.copyfile(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml',description)
            else:
                ET.ElementTree(table).write(description,encoding='utf-8',xml_declaration=True)
            converted=folder/mode
            names=sorted(c['case_id'] for c in manifest['cases'])
            bounds=['AC0232'] if context=='catalog' else names
            command=[sys.executable,'-m','tools.run_labeled_disk_recheck','--_worker',mode,str(converted),str(inputs),
                '--descriptions-path',str(description),'--output-dir',str(converted),
                '--start',bounds[0],'--end',bounds[-1],'--execution-mode','semantic-only','--deterministic-order']
            env=dict(os.environ,ICC_SEARCH_SEED='20261018',IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0',TINY_ICC_OUTPUT_VARIATION='0',PYTHONHASHSEED='0')
            with (folder/(mode+'.log')).open('w',encoding='utf-8') as log:
                subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
            access[mode]=json.loads((folder/'reference_access.json').read_text(encoding='utf-8'))
            assert not access[mode]['blocked_svg_reads']
            for case in manifest['cases']:
                matches=[p for d in ('converted_svgs','converted_svg_failed') for p in (converted/d).glob('*.svg')
                         if p.stem.casefold()==case['case_id'].casefold()]
                assert len(matches)==1
                case[mode+'_svg']=matches[0].relative_to(folder).as_posix()
                if mode=='before' and context=='neutral':
                    old=next(c for c in original['cases'] if c['case_id']==case['case_id'])
                    if old.get('before_svg'):
                        frozen_svg=FOLDER/old['before_svg']
                    else:
                        frozen=json.loads((FOLDER/'frozen/manifest.json').read_text(encoding='utf-8'))
                        old=next(c for c in frozen['cases'] if c['case_id']==case['case_id'])
                        frozen_svg=FOLDER/'frozen'/old['before_svg']
                    assert matches[0].read_bytes()==frozen_svg.read_bytes()
        report=evaluate(manifest,folder)
        report['reference_access']=access
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        (folder/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        reports[context]=report
        print(context,report['satisfaction_gate']['summary'],flush=True)
    for a,b in zip(reports['neutral']['evidence'],reports['catalog']['evidence']):
        assert a['after_svg_sha256']==b['after_svg_sha256']
    return 0 if all(c['satisfactory'] for r in reports.values() for c in r['satisfaction_gate']['cases']) else 2

if __name__=='__main__':
    raise SystemExit(main())
