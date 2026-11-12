"""Replay known development inputs with frozen and grouped fallback alternatives.

Sealed real families are verified, never converted. No new family acceptance.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
from pathlib import Path
import time
from unittest.mock import patch
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from tools.evaluate_fallback_structure import digest, local_regions, evaluate_cli
from tools.evaluate_svg_text_baseline import render_librsvg
from tools.freeze_real_composition_holdouts import verify
from tools.run_plan_b_variations import render, measure_quality
from src.iCCModules.imageCompositeConverterFallbackGroups import check_relations
from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search
from src.iCCModules.imageCompositeConverterPower import conversion_awake

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/fallback_groups_v1'
INPUTS = ROOT/'artifacts/evaluation/fallback_structure_v1/inputs'

# Additional diagnostic regions are marked on the original development pixels.
# They are not independent holdout annotations and never grant model approval.
REGIONS = {
    'probe_00': [('left_shaft',[2,0,7,72]),('right_shaft',[22,0,7,72]),
                 ('left_head',[0,72,11,8]),('right_head',[20,71,10,9])],
    'probe_02': [('panel',[2,6,18,18]),('cross_interior',[5,9,11,11]),
                 ('connector',[18,12,13,6]),('joint',[26,11,8,8]),('linkage',[20,4,21,21])],
}


def regions(case):
    return [dict(name=name,box=box) for name,box in REGIONS.get(case['case_id'],[])] or case['regions']


def load_frozen(name):
    path = EVIDENCE/'inputs'/name
    spec = importlib.util.spec_from_file_location('frozen_'+path.stem,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review(image, svg, case):
    result = {}
    for name,renderer in [('MuPDF',render),('librsvg',render_librsvg)]:
        raster = renderer(svg,case['width'],case['height'])
        local = local_regions(image,raster,regions(case))
        quality = measure_quality(image,svg,render_fn=renderer)
        result[name] = dict(quality=quality,regions=local,
                            complete=quality['satisfactory'] and all(r['passed'] for r in local))
    return result


def synthetic_cases():
    """Independent geometry, colour and orientation controls, not new families."""
    colors=['#cc2255','#2288bb','#55aa33','#aa6611']
    header='<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80"><rect width="80" height="80" fill="white"/>'
    for k in range(8):
        color=colors[k%4]
        body=(f'<g transform="rotate({(k%4)*90} 40 40)"><line x1="40" y1="8" x2="40" y2="60" '
              f'stroke="{colors[(k//4+k)%4]}" stroke-width="2"/>'
              f'<polygon points="34,60 46,60 40,73" fill="{colors[(k//4+k)%4]}"/></g>')
        marks=[]
        for name,box in [('shaft',[36,6,8,53]),('head',[32,58,16,17])]:
            x,y,w,h=box
            corners=np.array([[x,y],[x+w,y],[x,y+h],[x+w,y+h]],float)-40
            for _ in range(k%4):
                corners=np.c_[-corners[:,1],corners[:,0]]
            lo=(corners+40).min(axis=0).astype(int);hi=(corners+40).max(axis=0).astype(int)
            marks.append(dict(name=name,box=[int(lo[0]),int(lo[1]),int(hi[0]-lo[0]),int(hi[1]-lo[1])]))
        yield dict(case_id=f'arrow_{k}',svg=header+body+'</svg>',width=80,height=80,regions=marks),header+'</svg>'
        offset=k//4
        body=(f'<g transform="translate({offset} {offset})"><rect x="10" y="24" width="24" height="24" '
              f'fill="{color}" stroke="#888888" stroke-width="1"/>'
              '<line x1="11" y1="25" x2="33" y2="47" stroke="#eeeeee" stroke-width="1"/>'
              '<line x1="33" y1="25" x2="11" y2="47" stroke="#eeeeee" stroke-width="1"/>'
              '<line x1="34" y1="36" x2="50" y2="36" stroke="#888888" stroke-width="1.5"/>'
              '<line x1="42" y1="46" x2="62" y2="26" stroke="#888888" stroke-width="1.5"/>'
              '<circle cx="52" cy="36" r="3" fill="white" stroke="#888888" stroke-width="1.5"/></g>')
        yield dict(case_id=f'panel_{k}',svg=header+body+'</svg>',width=80,height=80,
                   regions=[dict(name='cross',box=[12+offset,26+offset,20,20]),
                            dict(name='joint_connector',box=[34+offset,30+offset,24,13])]),header+'</svg>'


def evaluate_synthetic(output):
    from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch,SearchPolicy,image_search
    rows=[]
    for case,seed_svg in synthetic_cases():
        image=render(case['svg'],80,80)
        for arm in ('legacy_combined','groups','combined'):
            session=ImageSearch(SearchPolicy(seconds=5,max_seconds=5))
            with image_search(session):
                fitted,report=explore_structures(seed_svg,image,render(seed_svg,80,80),render,session,{},mode=arm)
            rows.append(dict(case_id=case['case_id'],arm=arm,renderers=review(image,fitted['svg'],case),
                             probe_count=report['probe_count'],model_confirmed=bool(session.validated)))
    (output/'synthetic.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    return rows


def negatives(image, svg, case):
    """Remove, shift and misconnect parts of actual emitted groups."""
    results = []
    groups = [g for g in ET.fromstring(svg).iter() if g.get('data-fallback-group')]
    if not groups:
        return results
    roles = [(i,n.get('data-part')) for i,g in enumerate(groups) for n in g if n.get('data-part')]
    for group_index,role in roles:
        for damage in ('remove','shift','wrong_connection'):
            root = ET.fromstring(svg)
            target_group=[g for g in root.iter() if g.get('data-fallback-group')][group_index]
            for g in [target_group]:
                for node in list(g):
                    if node.get('data-part') != role:
                        continue
                    if damage == 'remove':
                        g.remove(node)
                    elif node.tag.endswith('line'):
                        for k in (('x1','x2') if damage == 'shift' else ('x2',)):
                            node.set(k,str(float(node.get(k))+6))
                    elif node.tag.endswith('circle'):
                        node.set('cx',str(float(node.get('cx'))+6))
                    elif node.tag.endswith('rect'):
                        node.set('x',str(float(node.get('x'))+6))
                    elif node.tag.endswith('polygon'):
                        pts = np.array([list(map(float,p.split(','))) for p in node.get('points').split()])
                        pts[:,0] += 6
                        node.set('points',' '.join(f'{x},{y}' for x,y in pts))
            damaged = ET.tostring(root,encoding='unicode')
            checks = review(image,damaged,case)
            relations = check_relations(damaged)
            # Geometry and original-pixel evidence are both required. The
            # geometry check alone cannot approve a locally wrong rendering.
            for value in checks.values():
                value['rejected'] = not value['complete'] or not all(r['passed'] for r in relations)
            results.append(dict(group_index=group_index,role=role,damage=damage,relations=relations,renderers=checks))
    return results


def evaluate(output, seeds=(17,29,43), seconds=5., cli=False):
    manifest = json.loads((INPUTS/'manifest.json').read_text(encoding='utf-8'))
    frozen = json.loads((EVIDENCE/'inputs/manifest.json').read_text(encoding='utf-8'))
    for root,files in [(INPUTS,manifest['sha256']),(EVIDENCE/'inputs',frozen['files'])]:
        for name,sha in files.items():
            if digest(root/name) != sha:
                raise ValueError('Changed frozen input: '+name)
    reservations = verify(EVIDENCE/'freeze/manifest.json')
    output.mkdir(parents=True,exist_ok=False)
    from src.iCCModules import imageCompositeConverterFallbackStructure as structure
    from src.iCCModules.imageCompositeConverterVectorPolish import polish_generated_svg
    old_structure = load_frozen('imageCompositeConverterFallbackStructure.py')
    old_polish = load_frozen('imageCompositeConverterVectorPolish.py')
    results, controls = [], []
    for case in manifest['cases']:
        image = cv2.imread(str(INPUTS/case['case_id']/'original.jpg'))
        svg = (INPUTS/case['case_id']/'seed.svg').read_text(encoding='utf-8')
        assertions = description_assertions((INPUTS/case['case_id']/'description.txt').read_text(encoding='utf-8'))
        for seed in seeds:
            for arm in ('frozen_lines','groups','combined'):
                folder=output/f"{case['case_id']}-{seed}-{arm}"
                folder.mkdir()
                started=time.monotonic()
                with (folder/'search.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log):
                    with conversion_awake(), search_configuration(mode='portfolio',adaptive=True,seed=seed,budget=384,
                                               minimum_seconds=seconds,seconds=seconds,max_seconds=seconds):
                        with configured_image_search(case['case_id']) as session:
                            if arm == 'frozen_lines':
                                with patch.object(structure,'explore_structures',old_structure.explore_structures):
                                    fitted=old_polish.polish_generated_svg(svg,image,render,assertions=assertions)
                            else:
                                fitted=polish_generated_svg(svg,image,render,assertions=assertions,structure_mode=arm)
                            search=session.report()
                elapsed=time.monotonic()-started
                selected=(fitted or {}).get('svg',svg)
                (folder/'output.svg').write_text(selected,encoding='utf-8')
                checks=review(image,selected,case)
                telemetry=(fitted or {}).get('structure_search',{})
                (folder/'structure.json').write_text(json.dumps(telemetry,indent=2),encoding='utf-8')
                results.append(dict(case_id=case['case_id'],seed=seed,arm=arm,elapsed_seconds=elapsed,
                    renderers=checks,search=search,model_confirmed=bool(session.validated),
                    output_sha256=digest(folder/'output.svg'),output=str((folder/'output.svg').relative_to(output)),
                    structure={k:v for k,v in telemetry.items() if k!='proposals'}))
                if arm=='combined' and seed==seeds[0] and case['case_id'] in REGIONS:
                    controls.extend(dict(case_id=case['case_id'],**r) for r in negatives(image,selected,case))
                print(case['case_id'],seed,arm,[k for k,v in checks.items() if v['complete']],flush=True)
                (output/'summary.json').write_text(json.dumps(dict(results=results,negative_controls=controls,
                    reservations=reservations,seconds=seconds,max_seconds=seconds),indent=2)+'\n',encoding='utf-8')
    if cli:
        rows=evaluate_cli(INPUTS,output/'cli',modes=('legacy_combined','combined'))
        cli_checks=[]
        for row in rows:
            case=next(c for c in manifest['cases'] if c['case_id']==row['case_id'])
            path=output/'cli'/row['arm']/row['output_svg']
            image=cv2.imread(str(INPUTS/case['case_id']/'original.jpg'))
            cli_checks.append(dict(case_id=row['case_id'],arm=row['arm'],elapsed_seconds=row['elapsed_seconds'],
                model_confirmed=row.get('model_confirmed'),blocked_svg_reads=row.get('blocked_svg_reads'),
                renderers=review(image,path.read_text(encoding='utf-8'),case),output_sha256=digest(path)))
        (output/'cli_checks.json').write_text(json.dumps(cli_checks,indent=2)+'\n',encoding='utf-8')
    evaluate_synthetic(output)
    return results,controls


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seeds',nargs='+',type=int,default=[17,29,43])
    parser.add_argument('--seconds',type=float,default=5.)
    parser.add_argument('--cli',action='store_true')
    parser.add_argument('--review',action='store_true',help='Recheck saved outputs, controls and compact reproducibility metadata')
    parser.add_argument('--repeat-interrupted',action='store_true',help='Preserve and replace continuation runs with observation gaps above 250 ms')
    args=parser.parse_args()
    if args.repeat_interrupted:
        repeat_interrupted(args.output)
    elif args.review:
        finalize(args.output)
    else:
        evaluate(args.output,args.seeds,args.seconds,args.cli)


def repeat_interrupted(output):
    """Keep interrupted evidence explicit; a repeated run never erases it."""
    from src.iCCModules.imageCompositeConverterVectorPolish import polish_generated_svg
    study=json.loads((output/'summary.json').read_text(encoding='utf-8'))
    manifest=json.loads((INPUTS/'manifest.json').read_text(encoding='utf-8'))
    for index,row in enumerate(list(study['results'])):
        if row['elapsed_seconds'] <= study['seconds']+.25:
            continue
        if row['arm']=='frozen_lines':
            raise ValueError('Repeat the frozen arm through the original freeze protocol')
        folder=output/f"{row['case_id']}-{row['seed']}-{row['arm']}-repeat"
        folder.mkdir(exist_ok=False)
        case=next(c for c in manifest['cases'] if c['case_id']==row['case_id'])
        image=cv2.imread(str(INPUTS/row['case_id']/'original.jpg'))
        svg=(INPUTS/row['case_id']/'seed.svg').read_text(encoding='utf-8')
        assertions=description_assertions((INPUTS/row['case_id']/'description.txt').read_text(encoding='utf-8'))
        with (folder/'search.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),conversion_awake():
            started=time.monotonic()
            with search_configuration(mode='portfolio',adaptive=True,seed=row['seed'],budget=384,
                                      minimum_seconds=study['seconds'],seconds=study['seconds'],max_seconds=study['max_seconds']):
                with configured_image_search(row['case_id']) as session:
                    fitted=polish_generated_svg(svg,image,render,assertions=assertions,structure_mode=row['arm'])
                    search=session.report()
            elapsed=time.monotonic()-started
        selected=(fitted or {}).get('svg',svg)
        (folder/'output.svg').write_text(selected,encoding='utf-8')
        telemetry=(fitted or {}).get('structure_search',{})
        (folder/'structure.json').write_text(json.dumps(telemetry,indent=2),encoding='utf-8')
        study.setdefault('interrupted_results',[]).append(dict(**row,exclusion='Unexplained monotonic observation gap; not evidence of additional useful search time'))
        study['results'][index]=dict(row,elapsed_seconds=elapsed,search=search,
            output=str((folder/'output.svg').relative_to(output)),output_sha256=digest(folder/'output.svg'),
            renderers=review(image,selected,case),structure={k:v for k,v in telemetry.items() if k!='proposals'},
            repeated_after_observation_gap=True)
    (output/'summary.json').write_text(json.dumps(study,indent=2)+'\n',encoding='utf-8')
    print('Preserved interrupted runs:',len(study.get('interrupted_results',[])))


def finalize(output):
    """Final evidence is remeasured from the saved vectors, never scalar claims."""
    study=json.loads((output/'summary.json').read_text(encoding='utf-8'))
    manifest=json.loads((INPUTS/'manifest.json').read_text(encoding='utf-8'))
    controls=[]
    for row in study['results']:
        case=next(c for c in manifest['cases'] if c['case_id']==row['case_id'])
        path=output/row['output']
        if digest(path)!=row['output_sha256']:
            raise ValueError('Changed saved vector')
        image=cv2.imread(str(INPUTS/row['case_id']/'original.jpg'))
        svg=path.read_text(encoding='utf-8')
        row['renderers']=review(image,svg,case)
        if row['arm']=='combined' and row['seed']==17 and row['case_id'] in REGIONS:
            controls.extend(dict(case_id=row['case_id'],**c) for c in negatives(image,svg,case))
    synthetic=evaluate_synthetic(output)
    cli=json.loads((output/'cli_checks.json').read_text(encoding='utf-8')) if (output/'cli_checks.json').exists() else []
    if cli:
        raw_cli=json.loads((output/'cli/summary.json').read_text(encoding='utf-8'))['results']
        for row in cli:
            raw=next(r for r in raw_cli if r['case_id']==row['case_id'] and r['arm']==row['arm'])
            path=output/'cli'/row['arm']/raw['output_svg']
            if digest(path)!=row['output_sha256'] or row.get('blocked_svg_reads'):
                raise ValueError('Changed or reference-reading CLI output')
            case=next(c for c in manifest['cases'] if c['case_id']==row['case_id'])
            image=cv2.imread(str(INPUTS/row['case_id']/'original.jpg'))
            row['renderers']=review(image,path.read_text(encoding='utf-8'),case)
    if len(study['results'])!=36 or len(cli)!=8 or len(synthetic)!=48:
        raise ValueError('Incomplete three-seed / three-arm / CLI study')
    if any(r['elapsed_seconds']>study['seconds']+.25 for r in study['results']):
        raise ValueError('Unresolved continuation timing gap; preserve and repeat first')
    for row in study.get('interrupted_results',[]):
        if digest(output/row['output'])!=row['output_sha256']:
            raise ValueError('Changed interrupted evidence')
    if any(r['model_confirmed'] for r in study['results']+cli+synthetic):
        raise AssertionError('A fallback draft must not be promoted')
    if not all(v['rejected'] for c in controls for v in c['renderers'].values()):
        raise AssertionError('Damaged group passed all gates')
    if not all(v['complete'] for r in synthetic if r['arm']=='groups' for v in r['renderers'].values()):
        raise AssertionError('Independent synthetic group regression')
    sources=['src/iCCModules/imageCompositeConverterFallbackGroups.py',
             'src/iCCModules/imageCompositeConverterFallbackStructure.py',
             'src/iCCModules/imageCompositeConverterVectorPolish.py','tools/evaluate_fallback_groups.py',
             'tools/evaluate_fallback_structure.py','tools/build_catalog_inventory.py',
             'tests/test_fallback_groups.py','tests/test_catalog_inventory.py']
    result=dict(schema='fallback_groups_study_v1',role='known_development_and_synthetic_only',
        source_sha256={name:digest(ROOT/name) for name in sources},
        baseline_manifest_sha256=digest(EVIDENCE/'inputs/manifest.json'),
        development_manifest_sha256=digest(INPUTS/'manifest.json'),
        diagnostic_regions=REGIONS,seconds=study['seconds'],max_seconds=study['max_seconds'],
        results=study['results'],cli=cli,synthetic=synthetic,
        interrupted_results=study.get('interrupted_results',[]),
        reservations=verify(EVIDENCE/'freeze/manifest.json'),negative_controls=controls)
    # Remove repeated fixed limits while retaining every measured metric/region.
    for row in result['results']+cli+synthetic+controls:
        for value in row['renderers'].values():
            value['quality'].pop('limits',None)
    from tools.run_plan_b_variations import LIMITS
    result['limits']=LIMITS
    (EVIDENCE/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(runs=len(study['results']),cli=len(cli),synthetic=len(synthetic),
                          negative_controls=len(controls),all_controls_rejected=True)))


if __name__=='__main__':
    main()
