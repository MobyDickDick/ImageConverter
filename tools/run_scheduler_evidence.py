"""Compare actual supervised CLI runs with a frozen Git parent implementation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MODULES = ('AdaptiveSearch', 'FilledSymbols', 'SearchBots', 'ShortLabelDisk')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantics(case, svg, image):
    from tools.evaluate_short_label_search import symbol_semantics
    from tools.evaluate_motor_valve_recheck import symbol_semantics as motor_semantics
    from tools.evaluate_labeled_disk_recheck import symbol_semantics as letter_semantics
    from tools.evaluate_primitive_scene import check_objects
    from tools.run_plan_b_variations import render
    return (symbol_semantics(svg,case['label']) if case['kind']=='label' else
            motor_semantics(svg) if case['kind']=='motor' else
            letter_semantics(svg,'Q',bottom_stem=True) if case['kind']=='letter' else
            float(check_objects(render(svg,image.shape[1],image.shape[0]),case['expected_objects'])['passed']))


def verify(output):
    import cv2
    from tools.run_plan_b_variations import measure_quality
    report = json.loads((output/'report.json').read_text(encoding='utf-8'))
    for case in report['cases']:
        image_path = output/case['image']
        assert digest(image_path) == case['input_sha256']
        image = cv2.imread(str(image_path))
        for mode in ('before','after'):
            saved = case[mode]
            path = output/saved['svg']
            assert digest(path) == saved['svg_sha256']
            svg = path.read_text(encoding='utf-8')
            assert measure_quality(image,svg)['satisfactory'], (mode,case['case_id'])
            assert semantics(case,svg,image) == 1., (mode,case['case_id'])
            assert saved['search_control']['isolated']
    return dict(cases=len(report['cases']),checked_outputs=2*len(report['cases']),strict_pixels_and_semantics=True)


def run(output, baseline_ref):
    import cv2
    from tools.run_plan_b_variations import render, measure_quality

    output.mkdir(parents=True)
    sources = output/'sources'
    sources.mkdir()
    prior = ROOT/'artifacts/evaluation/deadline_search_v1'
    manifest = json.loads((prior/'report.json').read_text(encoding='utf-8'))
    cases = []
    # Protected parent sources cover labels, valve topology, a handle and scenes.
    for case in manifest['cases']:
        target = sources/Path(case['image']).name
        shutil.copyfile(prior/case['image'], target)
        cases.append({k:v for k,v in case.items() if k not in {'direct','supervised'}})
    for i,(label,size,weight,spacing) in enumerate((('HX',64,700,0),('mV',80,400,21),('PA',96,700,25))):
        radius = size*.38
        style = f'font-family="Arial" font-size="{size*.32}" font-weight="{weight}" text-anchor="middle" fill="#273746"'
        glyphs = (f'<text x="{size/2}" y="{size*.63}" {style}>{label}</text>' if not spacing else
                  ''.join(f'<text x="{size/2+(j-.5)*spacing}" y="{size*.63}" {style}>{c}</text>' for j,c in enumerate(label)))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
               f'<rect width="{size}" height="{size}" fill="#ffffff"/>'
               f'<circle cx="{size/2}" cy="{size/2}" r="{radius}" stroke="#3d566e" stroke-width="2" fill="#d4e6f1"/>'
               +glyphs+'</svg>')
        name = f'neutral_{len(cases):02}'
        target = sources/(name+'.png')
        cv2.imwrite(str(target), render(svg,size,size))
        cases.append(dict(case_id=name, image=target.relative_to(output).as_posix(),
                          input_sha256=digest(target), kind='label', label=label, holdout=True,
                          description=f'Eine einfarbige Kreisscheibe mit dunkler Randkontur. Serifenlose Beschriftung "{label}". Keine Anschlüsse.'))
    table = ET.Element('root')
    for case in cases:
        entry = ET.SubElement(table,'entry',kind='wurzelform',key=case['case_id'])
        ET.SubElement(entry,'beschreibung').text = case['description']
        ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text = Path(case['image']).name
    descriptions = output/'descriptions.xml'
    ET.ElementTree(table).write(descriptions,encoding='utf-8',xml_declaration=True)

    # Isolate the parent's four changed modules without changing this checkout.
    # sitecustomize applies the same package overlay in Windows spawn workers.
    overlay = output/'parent_modules'
    overlay.mkdir()
    commit = subprocess.check_output(['git','rev-parse',baseline_ref],cwd=ROOT,text=True).strip()
    module_hashes = {}
    for suffix in MODULES:
        name = 'imageCompositeConverter'+suffix+'.py'
        content = subprocess.check_output(['git','show',commit+':src/iCCModules/'+name],cwd=ROOT)
        (overlay/name).write_bytes(content)
        module_hashes[name] = hashlib.sha256(content).hexdigest()
    (overlay/'sitecustomize.py').write_text(
        'import src.iCCModules\nsrc.iCCModules.__path__.insert(0,'+repr(str(overlay))+')\n',encoding='utf-8')
    env = dict(os.environ,IMAGE_CONVERTER_ISOLATE_SVG_RENDER='0',TINY_ICC_OUTPUT_VARIATION='0',
               PYTHONHASHSEED='0',PYTHONIOENCODING='utf-8')
    for mode in ('before','after'):
        inputs = output/('inputs_'+mode)
        shutil.copytree(sources,inputs)
        run_dir = output/mode
        mode_env = dict(env)
        if mode == 'before':
            mode_env['PYTHONPATH'] = str(overlay)+os.pathsep+str(ROOT)
        command = [sys.executable,'-m','tools.run_labeled_disk_recheck','--_worker',mode,str(run_dir),str(inputs),
                   '--descriptions-path',str(descriptions),'--output-dir',str(run_dir),
                   '--start',cases[0]['case_id'],'--end',cases[-1]['case_id'],
                   '--execution-mode','semantic-only','--deterministic-order','--search-seed','20261018']
        with (output/(mode+'.log')).open('w',encoding='utf-8') as log:
            subprocess.run(command,cwd=ROOT,env=mode_env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=480)
        access = json.loads((output/'reference_access.json').read_text(encoding='utf-8'))
        assert not access['blocked_svg_reads']
        rows = json.loads((run_dir/'reports/conversion_result_map.json').read_text(encoding='utf-8'))
        for case in cases:
            path = run_dir/'converted_svgs'/(case['case_id']+'.svg')
            svg = path.read_text(encoding='utf-8')
            image = cv2.imread(str(output/case['image']))
            quality = measure_quality(image,svg)
            assert quality['satisfactory'], (mode,case['case_id'],quality)
            semantic = semantics(case,svg,image)
            assert semantic == 1., (mode,case['case_id'],semantic)
            row = rows[Path(case['image']).name]
            assert row['search_satisfactory'] and not row.get('reference_access',{}).get('blocked_svg_reads')
            case[mode] = dict(svg=path.relative_to(output).as_posix(),svg_sha256=digest(path),quality=quality,
                              semantic_score=semantic,elapsed_seconds=row['elapsed_seconds'],search_control=row['search_control'])
        print(mode, 'completed',flush=True)
    summary = dict(cases=len(cases),strict_passes=len(cases),holdouts=sum(c.get('holdout',False) for c in cases),
                   byte_identical=sum(c['before']['svg_sha256']==c['after']['svg_sha256'] for c in cases))
    slices = []
    for log in (output/'after/reports').glob('*_worker.log'):
        for line in log.read_text(encoding='utf-8').splitlines():
            if line.startswith('[Search] '):
                event = json.loads(line[len('[Search] '):])
                if event.get('event') in {'model_slice','model_schedule_finished'}:
                    slices.append(event)
    (output/'scheduler_events.json').write_text(json.dumps(slices,indent=2)+'\n',encoding='utf-8')
    assert any(e['event']=='model_slice' for e in slices)
    current_hashes = {'imageCompositeConverter'+suffix+'.py':
                      digest(ROOT/'src/iCCModules'/('imageCompositeConverter'+suffix+'.py'))
                      for suffix in (*MODULES,'SearchScheduler')}
    report = dict(baseline_commit=commit,parent_module_hashes=module_hashes,
                  current_module_hashes=current_hashes,cases=cases,summary=summary)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(summary,flush=True)
    print(verify(output),flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--baseline-ref',default='00d48fe5c')
    parser.add_argument('--verify-only',action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        print(verify(args.output_dir.resolve()))
    else:
        run(args.output_dir.resolve(),args.baseline_ref)


if __name__ == '__main__':
    main()
