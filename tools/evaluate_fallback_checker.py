"""Freeze/replay independent synthetic checker controls; never run real reserves."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.check_native_scene import SCHEMA, check_scene

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/fallback_checker_v1'
SOURCE = ROOT/'tools/check_native_scene.py'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def development_cases():
    """Explicit authored native inventory, not extracted from candidate SVGs.

    Hidden geometry is known from synthetic construction. This is neither a
    human annotation audit nor evidence that hidden real geometry is inferable.
    """
    objects = [
        dict(id='background', kind='rect', points=[[0,0],[144,0],[144,144],[0,144]], fill='white'),
        dict(id='context_circle', kind='circle', points=[[120,112]], radius=10, fill='#9944cc'),
        dict(id='context_line', kind='line', points=[[16,100],[42,100]], stroke='#666666', stroke_width=2),
        dict(id='panel', kind='rect', points=[[10,24],[34,24],[34,48],[10,48]], fill='#2288bb', stroke='#888888'),
        dict(id='diagonal_a', kind='line', points=[[11,25],[33,47]], stroke='#eeeeee'),
        dict(id='diagonal_b', kind='line', points=[[33,25],[11,47]], stroke='#eeeeee'),
        dict(id='connector', kind='line', points=[[34,36],[49,36]], stroke='#888888', stroke_width=1.5),
        dict(id='linkage', kind='line', points=[[42,46],[62,26]], stroke='#888888', stroke_width=1.5),
        dict(id='joint', kind='circle', points=[[52,36]], radius=3, fill='white', stroke='#888888', stroke_width=1.5),
        dict(id='shaft', kind='line', points=[[105,8],[105,60]], stroke='#cc2255', stroke_width=2),
        dict(id='head', kind='polygon', points=[[99,60],[111,60],[105,73]], fill='#cc2255'),
        dict(id='partly_hidden', kind='line', points=[[16,124],[86,124]], stroke='#222222', stroke_width=2),
        dict(id='fully_hidden', kind='circle', points=[[52,124]], radius=3, fill='black'),
        dict(id='cover', kind='rect', points=[[40,114],[64,114],[64,134],[40,134]], fill='#55aa33'),
    ]
    relations = [
        dict(kind='endpoint_on_boundary', objects=['shaft','head'], tolerance=.3),
        dict(kind='endpoints_on_boundaries', objects=['connector','panel'], other='joint', tolerance=.3),
        dict(kind='crosses', objects=['diagonal_a','diagonal_b']),
        dict(kind='front_of', objects=['diagonal_a','panel']),
        dict(kind='front_of', objects=['diagonal_b','panel']),
        dict(kind='front_of', objects=['joint','linkage']),
        dict(kind='front_of', objects=['cover','partly_hidden']),
        dict(kind='front_of', objects=['cover','fully_hidden']),
    ]
    body = ('<circle cx="120" cy="112" r="10" fill="#9944cc"/>'
            '<line x1="16" y1="100" x2="42" y2="100" stroke="#666666" stroke-width="2"/>'
            '<rect x="10" y="24" width="24" height="24" fill="#2288bb" stroke="#888888"/>'
            '<line x1="11" y1="25" x2="33" y2="47" stroke="#eeeeee"/>'
            '<line x1="33" y1="25" x2="11" y2="47" stroke="#eeeeee"/>'
            '<line x1="34" y1="36" x2="49" y2="36" stroke="#888888" stroke-width="1.5"/>'
            '<line x1="42" y1="46" x2="62" y2="26" stroke="#888888" stroke-width="1.5"/>'
            '<circle cx="52" cy="36" r="3" fill="white" stroke="#888888" stroke-width="1.5"/>'
            '<line x1="105" y1="8" x2="105" y2="60" stroke="#cc2255" stroke-width="2"/>'
            '<polygon points="99,60 111,60 105,73" fill="#cc2255"/>'
            '<line x1="16" y1="124" x2="86" y2="124" stroke="#222222" stroke-width="2"/>'
            '<circle cx="52" cy="124" r="3" fill="black"/>'
            '<rect x="40" y="114" width="24" height="20" fill="#55aa33"/>')
    header = '<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144"><rect width="144" height="144" fill="white"/>'
    variants = [
        ('plain', '', lambda x,y:(x,y), 1),
        ('quarter_turn', 'rotate(90 72 72)', lambda x,y:(144-y,x), 1),
        ('half_turn', 'translate(144 144) rotate(180)', lambda x,y:(144-x,144-y), 1),
        ('scaled', 'translate(18 18) scale(.75)', lambda x,y:(18+.75*x,18+.75*y), .75),
        ('reflected', 'matrix(-1 0 0 1 144 0)', lambda x,y:(144-x,y), 1),
    ]
    for name, tx, convert, scale in variants:
        annotation = dict(schema=SCHEMA, size=[144,144], complete_inventory=True,
                          limits=dict(position=.75, color=0, stroke_width=.05),
                          objects=copy.deepcopy(objects), relations=copy.deepcopy(relations))
        for obj in annotation['objects'][1:]:
            obj['points'] = [list(convert(x,y)) for x,y in obj['points']]
            if 'radius' in obj:
                obj['radius'] *= scale
            if 'stroke' in obj:
                obj['stroke_width'] = obj.get('stroke_width',1)*scale
        yield dict(case_id=name, annotation=annotation, svg=header+f'<g transform="{tx}">'+body+'</g></svg>')


def controls(case):
    """Mutate XML by primitive sequence, never by Runtime IDs or part marks."""
    for damage in ('missing_context','missing_head','missing_diagonal','missing_hidden',
                   'hidden_geometry','wrong_connection','extra_object','wrong_color',
                   'wrong_width','wrong_transform','wrong_depth','extra_hidden'):
        root = ET.fromstring(case['svg'])
        group = root[1]
        if damage.startswith('missing_'):
            group.remove(group[{'missing_context':0,'missing_head':9,'missing_diagonal':3,'missing_hidden':11}[damage]])
        elif damage == 'hidden_geometry':
            group[11].set('r', '1')
        elif damage == 'wrong_connection':
            # Within object-position tolerance, outside independent contact tolerance.
            group[5].set('x2', '48.3')
        elif damage == 'extra_object':
            ET.SubElement(group, '{http://www.w3.org/2000/svg}circle', cx='76',cy='94',r='4',fill='black')
        elif damage == 'extra_hidden':
            node = ET.Element('{http://www.w3.org/2000/svg}circle', cx='48',cy='120',r='1',fill='black')
            group.insert(12,node)
        elif damage == 'wrong_color':
            group[0].set('fill', '#cc4499')
        elif damage == 'wrong_width':
            group[1].set('stroke-width','3')
        elif damage == 'wrong_transform':
            group.set('transform', group.get('transform','')+' translate(3 0)')
        elif damage == 'wrong_depth':
            node = group[11]
            group.remove(node)
            group.append(node)
        yield damage, ET.tostring(root, encoding='unicode')


def freeze(output):
    output.mkdir(parents=True, exist_ok=False)
    (output/'checker.py').write_bytes(SOURCE.read_bytes())
    (output/'evaluator.py').write_bytes(Path(__file__).read_bytes())
    write_json(output/'manifest.json', dict(schema='fallback_checker_freeze_v1',
        role='synthetic_development_only', checker_sha256=digest(output/'checker.py'),
        cases=list(development_cases()), real_reserves_executed=False,
        real_release_ready=False, missing_requirements=['curved_real_geometry_oracle','human_annotation_audit']))
    manifest = output/'manifest.json'
    write_json(output/'seal.json', dict(files={'checker.py':digest(output/'checker.py'),
                                             'evaluator.py':digest(output/'evaluator.py'),
                                             'manifest.json':digest(manifest)}))


def verify(folder=EVIDENCE):
    seal = json.loads((folder/'seal.json').read_text(encoding='utf-8'))
    if set(seal['files']) != {'checker.py','evaluator.py','manifest.json'}:
        raise ValueError('Incomplete checker seal')
    for name, expected in seal['files'].items():
        if digest(folder/name) != expected:
            raise ValueError('Changed frozen checker evidence: '+name)
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if digest(folder/'evaluator.py') != digest(Path(__file__)):
        raise ValueError('Evaluator changed since freeze')
    if manifest['checker_sha256'] != digest(SOURCE) or manifest['real_reserves_executed'] or manifest['real_release_ready']:
        raise ValueError('Checker changed or invalid reserve status')
    return manifest


def evaluate(output, evidence=EVIDENCE, historical=None):
    from tools.evaluate_svg_text_baseline import render_librsvg
    from tools.run_plan_b_variations import render
    import numpy as np
    manifest = verify(evidence)
    output.mkdir(parents=True, exist_ok=False)
    positive, negative = [], []
    for case in manifest['cases']:
        result = check_scene(case['svg'],case['annotation'])
        positive.append(dict(case_id=case['case_id'], check=result))
        for damage,svg in controls(case):
            check = check_scene(svg,case['annotation'])
            identical = {name:bool(np.array_equal(fn(case['svg'],144,144),fn(svg,144,144)))
                         for name,fn in [('MuPDF',render),('librsvg',render_librsvg)]}
            negative.append(dict(case_id=case['case_id'], damage=damage, check=check, raster_identical=identical))
    # Check emitted development SVGs against the complete pre-existing target
    # construction. No runtime part checker contributes to this verdict.
    historical_rows = []
    if historical:
        old = json.loads((ROOT/'artifacts/evaluation/fallback_composition_v1/manifest.json').read_text(encoding='utf-8'))
        annotation = copy.deepcopy(manifest['cases'][0]['annotation'])
        annotation['objects'] = annotation['objects'][:-3]
        annotation['objects'][2]['points'] = [[16,112],[42,112]]
        annotation['objects'][6]['points'] = [[34,36],[50,36]]
        annotation['relations'] = [r for r in annotation['relations'] if 'cover' not in r['objects']]
        # The original construction ends one pixel inside the joint. The target
        # contact annotation explicitly permits that construction, not a shortened gap.
        annotation['relations'][1]['tolerance'] = 1
        target_checks = []
        for case in old['cases']:
            ann = copy.deepcopy(annotation)
            paint = ['#cc2255','#55aa33','#aa6611'][int(case['case_id'][-2:])%3]
            ann['objects'][9]['stroke'] = paint
            ann['objects'][10]['fill'] = paint
            check = check_scene(case['svg'],ann)
            target_checks.append(dict(case_id=case['case_id'],check=check))
        if not all(r['check']['complete'] for r in target_checks):
            raise AssertionError('Historical target annotation mismatch')
        for path in sorted(historical.glob('composition_*.svg')):
            case = next(c for c in old['cases'] if path.stem.startswith(c['case_id']+'-'))
            ann = copy.deepcopy(annotation)
            color = ['#cc2255','#55aa33','#aa6611'][int(case['case_id'][-2:])%3]
            ann['objects'][9]['stroke'] = color
            ann['objects'][10]['fill'] = color
            historical_rows.append(dict(file=path.name, output_sha256=digest(path),
                                        check=check_scene(path.read_text(encoding='utf-8'),ann)))
    summary = dict(checker_sha256=digest(SOURCE), manifest_sha256=digest(evidence/'manifest.json'),
                   evaluator_sha256=digest(Path(__file__)), positives=positive, negatives=negative,
                   historical=historical_rows, real_reserves_executed=False, model_promotions=0)
    if historical:
        summary['historical_targets'] = target_checks
    write_json(output/'summary.json', summary)
    if not all(r['check']['complete'] for r in positive) or any(r['check']['complete'] for r in negative):
        raise AssertionError('Independent oracle control regression')
    print(f"{len(positive)} positive scenes; {len(negative)} rejected controls; {len(historical_rows)} historical rechecks")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--historical', type=Path)
    args = parser.parse_args()
    if args.freeze:
        freeze(args.freeze)
    if args.output:
        evaluate(args.output,args.evidence,args.historical)


if __name__ == '__main__':
    main()
