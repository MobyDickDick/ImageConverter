"""Frozen synthetic scene composition study. Real family reserves stay sealed."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from xml.etree import ElementTree as ET

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterFallbackGroups import check_relations
from tools.evaluate_fallback_structure import local_regions
from tools.evaluate_svg_text_baseline import render_librsvg
from tools.run_plan_b_variations import measure_quality, render
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/fallback_composition_v1'
MODULES = ['imageCompositeConverterFallbackStructure.py', 'imageCompositeConverterFallbackGroups.py',
           'imageCompositeConverterVectorPolish.py']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases():
    header = '<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144"><rect width="144" height="144" fill="white"/>'
    context = ('<circle id="keep-circle" cx="120" cy="112" r="10" fill="#9944cc"/>'
               '<line id="keep-line" x1="16" y1="112" x2="42" y2="112" stroke="#666666" stroke-width="2"/>')
    panel = ('<rect x="10" y="24" width="24" height="24" fill="#2288bb" stroke="#888888" stroke-width="1"/>'
             '<line x1="11" y1="25" x2="33" y2="47" stroke="#eeeeee" stroke-width="1"/>'
             '<line x1="33" y1="25" x2="11" y2="47" stroke="#eeeeee" stroke-width="1"/>'
             '<line x1="34" y1="36" x2="50" y2="36" stroke="#888888" stroke-width="1.5"/>'
             '<line x1="42" y1="46" x2="62" y2="26" stroke="#888888" stroke-width="1.5"/>'
             '<circle cx="52" cy="36" r="3" fill="white" stroke="#888888" stroke-width="1.5"/>')
    marks = [('panel', [8,22,28,28]), ('cross', [12,26,20,20]),
             ('connector_joint', [34,30,24,13]), ('linkage', [40,24,24,24]),
             ('shaft', [101,6,8,53]), ('head', [97,58,16,17]),
             ('existing_circle', [108,100,24,24]), ('existing_line', [14,109,30,6]),
             ('no_extra_object', [51,99,23,25])]
    for index in range(6):
        color = ['#cc2255', '#55aa33', '#aa6611'][index % 3]
        arrow = (f'<line x1="105" y1="8" x2="105" y2="60" stroke="{color}" stroke-width="2"/>'
                 f'<polygon points="99,60 111,60 105,73" fill="{color}"/>')
        seed_body = context
        if index in (1,4):
            seed_body += f'<rect id="wrong-arrow" x="103" y="8" width="4" height="65" fill="{color}"/>'
        if index in (2,4):
            seed_body += '<rect id="incomplete-panel" x="10" y="24" width="24" height="24" fill="#2288bb"/>'
        if index in (3,4,5):
            seed_body += '<rect id="extra" x="55" y="103" width="16" height="18" fill="#444444"/>'
        yield dict(case_id=f'composition_{index:02d}', width=144, height=144,
                   svg=header+context+panel+arrow+'</svg>', seed_svg=header+seed_body+'</svg>',
                   regions=[dict(name=n, box=b) for n,b in marks],
                   description='Ein blaues Quadrat mit hellen Diagonalen, Anschluss und Gelenkgestänge; daneben ein farbiger Pfeil mit langem Schaft und dreieckigem Kopf. Unten ein violetter Kreis und eine kurze graue Linie.')


def freeze():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    folder = EVIDENCE/'inputs'
    folder.mkdir()
    for name in MODULES:
        (folder/name).write_bytes((ROOT/'src/iCCModules'/name).read_bytes())
    data = dict(schema='fallback_composition_development_v1', role='synthetic_development_not_real_acceptance',
                seconds=5, max_probes=32, seeds=[17,29,43], cases=list(cases()),
                runtime_sha256={n:digest(folder/n) for n in MODULES},
                evaluator_sha256=digest(Path(__file__)), real_reserves_executed=False)
    (EVIDENCE/'manifest.json').write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def review(image, svg, case):
    result = {}
    relations=check_relations(svg)
    for name, renderer in [('MuPDF',render),('librsvg',render_librsvg)]:
        raster = renderer(svg,case['width'],case['height'])
        local = local_regions(image,raster,case['regions'])
        # Empty target zones need error evidence, rather than nonexistent edges.
        for row in local:
            if row['name']=='no_extra_object':
                row['passed'] = row['normalized_mse'] <= .001
        quality = measure_quality(image,svg,render_fn=renderer)
        result[name] = dict(quality=quality, regions=local, relations=relations,
                            complete=quality['satisfactory'] and all(r['passed'] for r in local+relations))
    return result


def damaged_variants(svg):
    """Known scene defects, without changing target pixels or part thresholds."""
    for damage in ('missing_group','missing_context','wrong_connection','missing_head','extra_object'):
        root=ET.fromstring(svg)
        groups=[g for g in root if g.get('data-fallback-group')]
        if damage=='missing_group':
            root.remove(next(g for g in groups if g.get('data-fallback-group')=='crossed_panel_linkage'))
        elif damage=='missing_context':
            root.remove(next(g for g in root if g.get('id')=='keep-circle'))
        elif damage=='wrong_connection':
            node=next(n for n in root.iter() if n.get('data-part')=='connector')
            node.set('x2',str(float(node.get('x2'))-7))
        elif damage=='missing_head':
            group=next(g for g in groups if g.get('data-fallback-group')=='shaft_triangle')
            group.remove(next(n for n in group if n.get('data-part')=='head'))
        else:
            ET.SubElement(root,'{http://www.w3.org/2000/svg}rect',x='55',y='103',width='16',height='18',fill='#444444')
        yield damage,ET.tostring(root,encoding='unicode')


def evaluate_cli(output):
    """Actual supervised CLI from neutral raster inputs, with reference SVG reads blocked."""
    import cv2
    from tools.run_plan_b_variations import run_case
    manifest=json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
    output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for case in manifest['cases']:
        name=case['case_id']
        folder=output/name/'input'
        folder.mkdir(parents=True)
        image=render(case['svg'],144,144)
        cv2.imwrite(str(folder/(name+'.png')),image)
        root=ET.Element('root')
        entry=ET.SubElement(root,'entry',kind='wurzelform',key=name)
        ET.SubElement(entry,'beschreibung').text=case['description']
        ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text=name+'.png'
        ET.ElementTree(root).write(folder/'descriptions.xml',encoding='utf-8')
        row=run_case({k:case[k] for k in ('case_id','width','height','description')},output,
                     timeout=40,iterations=64,extra_cli_args=('--search-seed','17','--search-seconds','8',
                                    '--search-max-seconds','10','--search-min-seconds','5'))
        if row.get('output_svg'):
            row['renderers']=review(image,(output/row['output_svg']).read_text(encoding='utf-8'),case)
        state=output/name/'conversion/reports/conversion_result_map.json'
        row['model_confirmed']=False
        if state.exists():
            row['model_confirmed']=any(v.get('search_satisfactory',False) for v in json.loads(state.read_text(encoding='utf-8')).values())
        rows.append(row)
        (output/'summary.json').write_text(json.dumps(dict(results=rows),indent=2)+'\n',encoding='utf-8')
        print(name, {k:v['complete'] for k,v in row.get('renderers',{}).items()},flush=True)
    if any(r.get('blocked_svg_reads') or r.get('model_confirmed') or not r.get('renderers')
           or not all(c['complete'] for c in r['renderers'].values()) for r in rows):
        raise AssertionError('CLI scene completeness/reference-access/draft regression')
    return rows


def evaluate(output, baseline=False):
    from src.iCCModules import imageCompositeConverterFallbackStructure as current
    from unittest.mock import patch
    manifest=json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
    for name, sha in manifest['runtime_sha256'].items():
        if digest(EVIDENCE/'inputs'/name) != sha:
            raise ValueError('Changed frozen runtime: '+name)
    output.mkdir(parents=True,exist_ok=False)
    modules={}
    for name in MODULES[:2]:
        spec=importlib.util.spec_from_file_location('frozen_'+name,EVIDENCE/'inputs'/name)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[name]=module
    rows=[]
    for case in manifest['cases']:
        image=render(case['svg'],case['width'],case['height'])
        for seed in manifest['seeds']:
            session=ImageSearch(SearchPolicy(seconds=5,max_seconds=5))
            started=time.monotonic()
            group_module='src.iCCModules.imageCompositeConverterFallbackGroups.group_proposals'
            fn=modules[MODULES[0]].explore_structures if baseline else current.explore_structures
            with patch(group_module,modules[MODULES[1]].group_proposals if baseline else __import__(
                    'src.iCCModules.imageCompositeConverterFallbackGroups',fromlist=['group_proposals']).group_proposals):
                with (output/f"{case['case_id']}-{seed}.log").open('w',encoding='utf-8') as log, contextlib.redirect_stdout(log), search_configuration(mode='portfolio',seed=seed,budget=384), image_search(session):
                    fitted, report=fn(case['seed_svg'],image,render(case['seed_svg'],144,144),render,session,{},mode='combined')
            elapsed=time.monotonic()-started
            path=output/f"{case['case_id']}-{seed}.svg"
            path.write_text(fitted['svg'],encoding='utf-8')
            rows.append(dict(case_id=case['case_id'], seed=seed, elapsed_seconds=elapsed,
                             output_sha256=digest(path), renderers=review(image,fitted['svg'],case),
                             report=report, model_confirmed=bool(session.validated)))
            print(case['case_id'],seed,rows[-1]['renderers']['MuPDF']['complete'],flush=True)
    (output/'summary.json').write_text(json.dumps(dict(baseline=baseline,results=rows,
        manifest_sha256=digest(EVIDENCE/'manifest.json'),evaluator_sha256=digest(Path(__file__))),indent=2)+'\n',encoding='utf-8')
    if not baseline:
        controls=[]
        for case in manifest['cases']:
            svg=(output/f"{case['case_id']}-17.svg").read_text(encoding='utf-8')
            image=render(case['svg'],144,144)
            for damage,candidate in damaged_variants(svg):
                controls.append(dict(case_id=case['case_id'],damage=damage,renderers=review(image,candidate,case)))
        (output/'negative_controls.json').write_text(json.dumps(controls,indent=2)+'\n',encoding='utf-8')
        if (any(r['model_confirmed'] or r['elapsed_seconds'] > 5.25 or r['report']['probe_count'] > 32
                or not all(c['complete'] for c in r['renderers'].values()) for r in rows)
                or any(c['complete'] for r in controls for c in r['renderers'].values())):
            raise AssertionError('Scene/negative-control/budget/draft regression')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',action='store_true')
    parser.add_argument('--baseline',action='store_true')
    parser.add_argument('--cli',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.freeze:
        freeze()
    if args.output:
        if args.cli:
            evaluate_cli(args.output)
        else:
            evaluate(args.output,args.baseline)
