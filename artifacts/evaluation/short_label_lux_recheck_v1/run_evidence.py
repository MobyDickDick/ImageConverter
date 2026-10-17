"""Reproduce guarded neutral/full-catalog CLI comparisons; retain actual vectors."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.evaluate_short_label_search import evaluate


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n', encoding='utf-8')


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    original = read(FOLDER/'manifest.json')
    bootstrap = ('import sys,runpy; sys.path[:0]='+repr([str(ROOT), str(Path(np.__file__).resolve().parents[1]), *sys.path])+
                 "; runpy.run_module('tools.run_oriented_circle_linework_recheck',run_name='__main__')")
    env = dict(os.environ, IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0',
               TINY_ICC_OUTPUT_VARIATION='0', PYTHONHASHSEED='0', ICC_SEARCH_SEED='20261017')
    reports = {}
    for context in ('neutral', 'catalog'):
        folder = output/context
        folder.mkdir()
        manifest = json.loads(json.dumps(original))
        access = {}
        for case in manifest['cases']:
            if context == 'catalog':
                case['case_id'] = Path(case['source']).stem
            case['image'] = 'inputs/'+case['case_id']+'.jpg'
            target = folder/case['image']
            target.parent.mkdir(exist_ok=True)
            source = ROOT/'artifacts/images_to_convert'/case['source']
            assert hashlib.sha256(source.read_bytes()).hexdigest() == case['source_sha256']
            shutil.copyfile(source, target)
        for mode in ('before', 'after'):
            inputs = folder/('inputs_'+mode)
            inputs.mkdir()
            for case in manifest['cases']:
                shutil.copyfile(folder/case['image'], inputs/Path(case['image']).name)
            table = inputs/'descriptions.xml'
            if context == 'catalog':
                if mode == 'before':
                    table.write_bytes(subprocess.check_output(['git','show',original['provenance']['commit']+
                                                               ':artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'],cwd=ROOT))
                else:
                    shutil.copyfile(ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml',table)
            else:
                root = ET.Element('root')
                for case in manifest['cases']:
                    entry = ET.SubElement(root,'entry',kind='wurzelform',key=case['case_id'])
                    ET.SubElement(entry,'beschreibung').text = case['baseline_description'] if mode == 'before' else case['description']
                    ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text = Path(case['image']).name
                ET.ElementTree(root).write(table,encoding='utf-8',xml_declaration=True)
            converted = folder/mode
            names = sorted(case['case_id'] for case in manifest['cases'])
            with (folder/(mode+'.log')).open('w',encoding='utf-8') as log:
                subprocess.run([sys.executable,'-I','-c',bootstrap,'--_worker',mode,str(converted),str(inputs),
                                '--descriptions-path',str(table),'--output-dir',str(converted),
                                '--start',names[0],'--end',names[-1],'--execution-mode','semantic-only',
                                '--deterministic-order'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,
                               timeout=300,check=True)
            access[mode] = read(folder/'reference_access.json')
            assert not access[mode]['blocked_svg_reads']
            for case in manifest['cases']:
                matches = [p for sub in ('converted_svgs','converted_svg_failed') for p in (converted/sub).glob('*.svg')
                           if p.stem.casefold() == case['case_id'].casefold()]
                assert len(matches) == 1, (context,mode,case['case_id'])
                case[mode+'_svg'] = matches[0].relative_to(folder).as_posix()
                if context == 'neutral' and mode == 'before':
                    frozen = FOLDER/'before'/(case['case_id']+'.svg')
                    assert frozen.read_bytes() == matches[0].read_bytes(), 'Pre-change baseline changed'
        save(folder/'manifest.json',manifest)
        report = evaluate(folder)
        report['reference_access'] = access
        save(folder/'acceptance.json',report)
        reports[context] = report
        print(context,report['satisfaction_gate']['summary'],flush=True)
    for neutral,named in zip(read(output/'neutral/manifest.json')['cases'], read(output/'catalog/manifest.json')['cases']):
        assert (output/'neutral'/neutral['after_svg']).read_bytes() == (output/'catalog'/named['after_svg']).read_bytes()
    assert all(c['satisfactory'] for r in reports.values() for c in r['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for r in reports.values() for c in r['strict_pixel_gates'].values())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
