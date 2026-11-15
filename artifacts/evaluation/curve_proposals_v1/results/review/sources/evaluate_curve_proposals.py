"""Frozen paired raster-to-native curve development study; never real releases."""
from __future__ import annotations
import argparse
import contextlib
import importlib.util
import json
from pathlib import Path
import time
import copy
import csv
from unittest.mock import patch
from xml.etree import ElementTree as ET
import cv2
import numpy as np

from tools.curve_proposal_cases import cases
from tools.evaluate_curve_checker import digest, verify, EVIDENCE as CHECKER, ROOT, write_json
from tools.check_curve_scene import check_scene
from tools.run_plan_b_variations import render, measure_quality
from tools.evaluate_svg_text_baseline import render_librsvg

EVIDENCE = ROOT/'artifacts/evaluation/curve_proposals_v1'
MODULES = ['imageCompositeConverterFallbackGroups.py', 'imageCompositeConverterFallbackComposition.py',
           'imageCompositeConverterFallbackStructure.py']
CURRENT_MODULES=MODULES+['imageCompositeConverterFallbackCurves.py']


def freeze(folder=EVIDENCE):
    verify()
    folder.mkdir(parents=True,exist_ok=False)
    (folder/'inputs').mkdir()
    data = list(cases())
    for case in data:
        assert check_scene(case['svg'],case['annotation'])['complete']
        cv2.imwrite(str(folder/'inputs'/(case['case_id']+'.png')),render(case['svg'],128,128))
    for name in MODULES:
        (folder/'inputs'/name).write_bytes((ROOT/'src/iCCModules'/name).read_bytes())
    write_json(folder/'manifest.json',dict(schema='visible_curve_proposal_development_v1', cases=data,
        seconds=5,max_probes=32,seeds=[17,29,43],checker_sha256=digest(CHECKER/'seal.json'),
        files={p.name:digest(p) for p in (folder/'inputs').iterdir()},
        real_reserves_executed=False, model_promotions=0))
    write_json(folder/'seal.json',dict(manifest_sha256=digest(folder/'manifest.json')))


def verified(folder=EVIDENCE):
    verify()
    seal=json.loads((folder/'seal.json').read_text(encoding='utf-8'))
    if digest(folder/'manifest.json') != seal['manifest_sha256']:
        raise ValueError('Changed curve proposal manifest')
    data=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if digest(CHECKER/'seal.json') != data['checker_sha256']:
        raise ValueError('Changed curve checker')
    for name,sha in data['files'].items():
        if digest(folder/'inputs'/name) != sha:
            raise ValueError('Changed curve input: '+name)
    return data


@contextlib.contextmanager
def implementation(baseline,folder):
    if not baseline:
        from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
        yield explore_structures
        return
    import sys
    with patch.dict(sys.modules):
        for name in MODULES:
            key='src.iCCModules.'+name[:-3]
            spec=importlib.util.spec_from_file_location(key,folder/'inputs'/name)
            module=importlib.util.module_from_spec(spec)
            sys.modules[key]=module
            spec.loader.exec_module(module)
        yield module.explore_structures


def evaluate(output,baseline=False,folder=EVIDENCE):
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch,SearchPolicy,image_search
    from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration
    data=verified(folder)
    output.mkdir(parents=True,exist_ok=False)
    rows=[]
    with implementation(baseline,folder) as explore:
        for case in data['cases']:
            image=cv2.imread(str(folder/'inputs'/(case['case_id']+'.png')))
            for seed in data['seeds']:
                session=ImageSearch(SearchPolicy(seconds=data['seconds'],max_seconds=data['seconds']))
                start=time.monotonic()
                with (output/(case['case_id']+'-'+str(seed)+'.log')).open('w',encoding='utf-8') as log, contextlib.redirect_stdout(log), image_search(session),search_configuration(mode='portfolio',seed=seed,budget=384):
                    fitted,report=explore(case['seed_svg'],image,render(case['seed_svg'],128,128),render,
                        session,{},mode='combined',max_probes=data['max_probes'])
                elapsed=time.monotonic()-start
                path=output/(case['case_id']+'-'+str(seed)+'.svg')
                path.write_text(fitted['svg'],encoding='utf-8')
                quality={name:measure_quality(image,fitted['svg'],render_fn=fn)
                         for name,fn in [('MuPDF',render),('librsvg',render_librsvg)]}
                row=dict(case_id=case['case_id'],seed=seed,elapsed_seconds=elapsed,svg_sha256=digest(path),
                         check=check_scene(fitted['svg'],case['annotation']),quality=quality,report=report,
                         model_confirmed=bool(session.validated))
                rows.append(row)
                print(case['case_id'],seed,row['check']['complete'],[q['satisfactory'] for q in quality.values()],flush=True)
    write_json(output/'summary.json',dict(baseline=baseline,results=rows,
        manifest_sha256=digest(folder/'manifest.json'),evaluator_sha256=digest(Path(__file__)),
        source_sha256={n:digest((folder/'inputs' if baseline else ROOT/'src/iCCModules')/n) for n in (MODULES if baseline else CURRENT_MODULES)},
        real_reserves_executed=False,model_promotions=0))
    if any(r['model_confirmed'] or r['elapsed_seconds']>data['seconds']+.25
           or r['report']['probe_count']>data['max_probes'] for r in rows):
        raise AssertionError('Curve study budget or draft status violated')
    if not baseline and any(not all(q['satisfactory'] for q in r['quality'].values()) for r in rows):
        raise AssertionError('Visible curve raster regression; native failures remain separately reported')
    return rows


def damaged(case):
    """Controls from external constructions, never from fitted coordinates."""
    ns='{http://www.w3.org/2000/svg}'
    for damage in ('missing_curve','missing_lead','duplicate_curve','gap','tangent','middle','paint','width','hidden_extra'):
        root=ET.fromstring(case['svg'])
        group=ET.Element(ns+'g',{'data-fallback-group':'open_curve_lead'})
        lead,curve=root[1:]
        root.remove(lead);root.remove(curve);root.append(group)
        lead.set('data-part','lead');curve.set('data-part','curve');group.extend([lead,curve])
        if damage=='missing_curve':
            group.remove(curve)
        elif damage=='missing_lead':
            group.remove(lead)
        elif damage=='duplicate_curve':
            root.append(copy.deepcopy(curve))
        elif damage=='gap':
            lead.set('x2',str(float(lead.get('x2'))+4))
        elif damage in {'tangent','middle'}:
            from src.iCCModules.imageCompositeConverterFallbackCurves import curve_points
            pts=curve_points(curve)
            index=1 if damage=='tangent' else -2
            direction=pts[1]-pts[0]
            offset=7*np.array([-direction[1],direction[0]])/np.linalg.norm(direction)
            pts[index]+=offset
            curve.set('d','M '+' '.join(map(str,pts[0]))+' '+('Q' if len(pts)==3 else 'C')+' '+' '.join(str(v) for p in pts[1:] for v in p))
        elif damage=='paint':
            curve.set('stroke','#cc3322')
        elif damage=='width':
            curve.set('stroke-width',str(float(curve.get('stroke-width'))*.45))
        else:
            extra=copy.deepcopy(curve);extra.set('transform','translate(0 32)');root.append(extra)
            ET.SubElement(root,ns+'rect',x='0',y='0',width='128',height='128',fill='white')
            # Entire original scene redrawn above a redundant hidden curve.
            root.extend(copy.deepcopy(list(ET.fromstring(case['svg']))[1:]))
        yield damage,ET.tostring(root,encoding='unicode')


def evaluate_controls(output,folder=EVIDENCE):
    from src.iCCModules.imageCompositeConverterFallbackGroups import check_parts,check_relations,part_regions
    output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for case in verified(folder)['cases']:
        image=cv2.imread(str(folder/'inputs'/(case['case_id']+'.png')))
        for damage,svg in damaged(case):
            path=output/(case['case_id']+'-'+damage+'.svg');path.write_text(svg,encoding='utf-8')
            renderers={}
            for name,fn in [('MuPDF',render),('librsvg',render_librsvg)]:
                raster=fn(svg,128,128)
                local=check_parts(image,raster,part_regions(svg,128,128))
                relations=check_relations(svg)
                renderers[name]=dict(quality=measure_quality(image,svg,render_fn=fn),parts=local,relations=relations,
                    local_passed=all(p['passed'] for p in local+relations),
                    identical=bool((raster==fn(case['svg'],128,128)).all()))
            rows.append(dict(case_id=case['case_id'],damage=damage,svg_sha256=digest(path),
                check=check_scene(svg,case['annotation']),renderers=renderers))
    write_json(output/'summary.json',dict(results=rows,manifest_sha256=digest(folder/'manifest.json')))
    if any(r['check']['complete'] for r in rows):
        raise AssertionError('Independent curve damage accepted')
    return rows


def evaluate_cli(output,folder=EVIDENCE):
    from tools.run_plan_b_variations import run_case
    output=output.resolve();output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for case in verified(folder)['cases']:
        name=case['case_id'];inputs=output/name/'input';inputs.mkdir(parents=True)
        (inputs/(name+'.png')).write_bytes((folder/'inputs'/(name+'.png')).read_bytes())
        root=ET.Element('root');entry=ET.SubElement(root,'entry',kind='wurzelform',key=name)
        ET.SubElement(entry,'beschreibung').text=case['description']
        ET.SubElement(ET.SubElement(entry,'bilder'),'bild').text=name+'.png'
        ET.ElementTree(root).write(inputs/'descriptions.xml',encoding='utf-8')
        row=run_case({k:case[k] for k in ('case_id','width','height','description')},output,
            timeout=40,iterations=64,extra_cli_args=('--search-seed','17','--search-seconds','5',
                '--search-max-seconds','5','--search-min-seconds','5'),keep_debug_artifacts=True)
        if row.get('output_svg'):
            svg=(output/row['output_svg']).read_text(encoding='utf-8')
            image=cv2.imread(str(folder/'inputs'/(name+'.png')))
            row['check']=check_scene(svg,case['annotation'])
            row['quality']={n:measure_quality(image,svg,render_fn=fn) for n,fn in [('MuPDF',render),('librsvg',render_librsvg)]}
        state=output/name/'conversion/reports/conversion_result_map.json'
        row['model_confirmed']=False
        if state.exists():
            row['model_confirmed']=any(v.get('search_satisfactory',False) for v in json.loads(state.read_text(encoding='utf-8')).values())
        failures=output/name/'conversion/reports/batch_failure_summary.csv'
        row['batch_failures']=list(csv.DictReader(failures.open(encoding='utf-8'),delimiter=';')) if failures.exists() else []
        row['clean_process_completion']=row.get('returncode')==0 and not row['batch_failures']
        rows.append(row)
        write_json(output/'summary.json',dict(results=rows,manifest_sha256=digest(folder/'manifest.json'),
            evaluator_sha256=digest(Path(__file__)),seconds=5,seed=17,real_reserves_executed=False,model_promotions=0))
        print(name,row.get('check',{}).get('complete'),row.get('failures'),flush=True)
    if any(r.get('blocked_svg_reads') or r['model_confirmed'] or not r.get('quality')
           or not all(q['satisfactory'] for q in r['quality'].values()) for r in rows):
        raise AssertionError('CLI reference access, draft status, or raster regression')
    return rows


def evaluate_legacy(output):
    """Post-freeze inspection of the old hidden-geometry constructions."""
    from src.iCCModules.imageCompositeConverterFallbackGroups import group_proposals
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch,SearchPolicy,image_search
    output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for case in verify()['cases']:
        image=render(case['svg'],160,160)
        session=ImageSearch(SearchPolicy(seconds=5,max_seconds=5))
        start=time.monotonic();proposals=[]
        with image_search(session):
            for svg,family in group_proposals(image,session,render):
                if session.time_reason() or len(proposals)>=32:
                    break
                path=output/(case['case_id']+'-'+str(len(proposals))+'.svg')
                path.write_text(svg,encoding='utf-8')
                proposals.append(dict(family=family,sha256=digest(path),check=check_scene(svg,case['annotation'])))
        rows.append(dict(case_id=case['case_id'],elapsed_seconds=time.monotonic()-start,
            proposals=proposals,render_evaluations=session.evaluations,model_confirmed=bool(session.validated)))
    write_json(output/'summary.json',dict(results=rows,checker_sha256=digest(CHECKER/'seal.json'),
        real_reserves_executed=False,model_promotions=0))
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',action='store_true')
    parser.add_argument('--baseline',action='store_true')
    parser.add_argument('--controls',action='store_true')
    parser.add_argument('--cli',action='store_true')
    parser.add_argument('--legacy',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.freeze:
        freeze()
    if args.output:
        if args.legacy:
            evaluate_legacy(args.output)
        elif args.cli:
            evaluate_cli(args.output)
        elif args.controls:
            evaluate_controls(args.output)
        else:
            evaluate(args.output,args.baseline)
