"""Freeze/replay logical segment equivalence on synthetic development only."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.check_segment_scene import SCHEMA, check_scene

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/segment_checker_v1'
SOURCE = ROOT/'tools/check_segment_scene.py'
STRICT = ROOT/'tools/check_native_scene.py'
OLD = ROOT/'artifacts/evaluation/fallback_checker_v1'
NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', 'http://www.w3.org/2000/svg')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def representation(covers):
    return dict(mode='collinear_segments', occluders=covers, max_segments=8,
                join_tolerance=.05, collinearity=.1, hidden_geometry='unverified_if_omitted')


def annotation_v2(annotation):
    result = copy.deepcopy(annotation)
    result['schema'] = SCHEMA
    for obj in result['objects']:
        if obj['id'] == 'linkage':
            obj['representation'] = representation(['joint'])
        elif obj['id'] == 'partly_hidden':
            obj['representation'] = representation(['cover'])
        elif obj['id'] == 'context_line':
            obj['representation'] = representation([])
    return result


def development_cases():
    """Reuse sealed external annotations; independently author segment cuts.

    No emitted converter SVG or Runtime group mark supplies the annotations.
    Five similarities of one construction, with three representations each.
    """
    manifest = json.loads((OLD/'manifest.json').read_text(encoding='utf-8'))
    for original in manifest['cases']:
        for mode in ('intact', 'joint_split', 'multiple_splits'):
            root = ET.fromstring(original['svg'])
            group = root[1]
            nodes = list(group)
            # Explicit authored endpoints in pre-transform construction space.
            cuts = {}
            if mode != 'intact':
                d = 3/(2**.5)
                cuts[6] = [(42,46,52-d,36+d), (52+d,36-d,62,26)]
            if mode == 'multiple_splits':
                cuts[1] = [(16,100,29,100), (29,100,42,100)]
                cuts[10] = [(16,124,40,124), (64,124,86,124)]
            slots = {}
            for node in nodes:
                group.remove(node)
            # Background lives outside the transformed group.
            for index, (obj, node) in enumerate(zip(original['annotation']['objects'][1:], nodes)):
                slots[obj['id']] = []
                for coords in cuts.get(index, [None]):
                    child = copy.deepcopy(node)
                    if coords is not None:
                        for key, value in zip(('x1','y1','x2','y2'), coords):
                            child.set(key, str(value))
                    slots[obj['id']].append(len(group))
                    group.append(child)
            yield dict(case_id=original['case_id']+'-'+mode, representation=mode, slots=slots,
                       annotation=annotation_v2(original['annotation']), svg=ET.tostring(root, encoding='unicode'))


def controls(case):
    for damage in ('missing_segment', 'duplicate_segment', 'parallel_overdraw', 'contour_overdraw',
                   'hidden_extra', 'missing_context', 'missing_head', 'missing_cover', 'missing_hidden',
                   'wrong_connection', 'wrong_segment_width', 'wrong_segment_color', 'wrong_depth',
                   'gap_outside_cover', 'wrong_hidden_geometry', 'wrong_transform', 'transparent_cover'):
        root = ET.fromstring(case['svg'])
        group = root[1]
        slots = case['slots']
        get = lambda name, part=0:group[slots[name][part]]
        if damage.startswith('missing_'):
            name = {'missing_segment':'linkage', 'missing_context':'context_circle', 'missing_head':'head',
                    'missing_cover':'joint', 'missing_hidden':'fully_hidden'}[damage]
            group.remove(get(name))
        elif damage == 'duplicate_segment':
            group.append(copy.deepcopy(get('linkage')))
        elif damage == 'parallel_overdraw':
            node = copy.deepcopy(get('context_line'))
            node.set('y1', '100.4'); node.set('y2', '100.4')
            group.append(node)
        elif damage == 'contour_overdraw':
            ET.SubElement(group, NS+'line', x1='10', y1='24', x2='34', y2='24', stroke='#888888')
        elif damage == 'hidden_extra':
            group.insert(slots['cover'][0], ET.Element(NS+'line', x1='44', y1='120', x2='60', y2='120', stroke='black'))
        elif damage == 'wrong_connection':
            get('connector').set('x2', '48.3')
        elif damage == 'wrong_segment_width':
            get('linkage').set('stroke-width', '2.5')
        elif damage == 'wrong_segment_color':
            get('linkage').set('stroke', '#111111')
        elif damage == 'wrong_depth':
            node = get('joint')
            group.remove(node)
            group.insert(0, node)
        elif damage == 'gap_outside_cover':
            # On split cases, shorten the visible arm by .6 along the diagonal:
            # the new gap extends outside the filled joint. Intact cases get a
            # wrong outer endpoint instead. Both are explicit negative controls.
            node = get('linkage')
            if len(slots['linkage']) == 2:
                node.set('x2', str(float(node.get('x2'))-.6))
                node.set('y2', str(float(node.get('y2'))+.6))
            else:
                node.set('x1','44')
        elif damage == 'wrong_hidden_geometry':
            get('fully_hidden').set('r', '1')
        elif damage == 'wrong_transform':
            group.set('transform', group.get('transform', '')+' translate(3 0)')
        else:
            get('joint').set('opacity', '.5')
        yield damage, ET.tostring(root, encoding='unicode')


def historical_cases():
    old = json.loads((ROOT/'artifacts/evaluation/fallback_composition_v1/manifest.json').read_text(encoding='utf-8'))
    base = json.loads((OLD/'manifest.json').read_text(encoding='utf-8'))['cases'][0]['annotation']
    annotation = annotation_v2(base)
    annotation['objects'] = annotation['objects'][:-3]
    annotation['objects'][2]['points'] = [[16,112],[42,112]]
    annotation['objects'][6]['points'] = [[34,36],[50,36]]
    annotation['relations'] = [r for r in annotation['relations'] if 'cover' not in r['objects']]
    annotation['relations'][1]['tolerance'] = 1
    for case in old['cases']:
        ann = copy.deepcopy(annotation)
        paint = ['#cc2255','#55aa33','#aa6611'][int(case['case_id'][-2:])%3]
        ann['objects'][9]['stroke'] = paint
        ann['objects'][10]['fill'] = paint
        yield dict(case_id=case['case_id'], svg=case['svg'], annotation=ann)


def freeze(output):
    output.mkdir(parents=True, exist_ok=False)
    for name, path in [('checker.py', SOURCE), ('strict_checker.py', STRICT), ('evaluator.py', Path(__file__))]:
        (output/name).write_bytes(path.read_bytes())
    # Controls are frozen as data as well as code; replay does not rebuild them.
    cases = list(development_cases())
    for case in cases:
        case['controls'] = [dict(damage=d, svg=svg) for d, svg in controls(case)]
    historical = []
    targets = list(historical_cases())
    for path in sorted((OLD/'historical').glob('composition_*.svg')):
        case = next(c for c in targets if path.stem.startswith(c['case_id']+'-'))
        historical.append(dict(file=path.name, svg=path.read_text(encoding='utf-8'),
                               sha256=digest(path), annotation=case['annotation']))
    write_json(output/'manifest.json', dict(schema='segment_checker_freeze_v1', role='synthetic_development_only',
        cases=cases, historical=historical, historical_targets=targets, real_reserves_executed=False,
        real_release_ready=False, missing_requirements=['curved_real_geometry_oracle','human_annotation_audit',
                                                       'independent_real_completeness']))
    names = ['checker.py','strict_checker.py','evaluator.py','manifest.json']
    write_json(output/'seal.json', dict(files={name:digest(output/name) for name in names}))


def verify(folder=EVIDENCE):
    seal = json.loads((folder/'seal.json').read_text(encoding='utf-8'))
    sources = {'checker.py':SOURCE, 'strict_checker.py':STRICT, 'evaluator.py':Path(__file__)}
    if set(seal['files']) != set(sources) | {'manifest.json'}:
        raise ValueError('Incomplete segment seal')
    for name, value in seal['files'].items():
        if digest(folder/name) != value or (name in sources and digest(sources[name]) != value):
            raise ValueError('Changed frozen segment evidence: '+name)
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if manifest['real_reserves_executed'] or manifest['real_release_ready']:
        raise ValueError('Invalid reserve status')
    for row in manifest['historical']:
        if hashlib.sha256(row['svg'].encode('utf-8')).hexdigest() != row['sha256']:
            raise ValueError('Historical bytes differ')
    return manifest


def evaluate(output, evidence=EVIDENCE):
    from tools.evaluate_svg_text_baseline import render_librsvg
    from tools.run_plan_b_variations import render
    import numpy as np
    manifest = verify(evidence)
    output.mkdir(parents=True, exist_ok=False)
    positive, negative = [], []
    for case in manifest['cases']:
        positive.append(dict(case_id=case['case_id'], check=check_scene(case['svg'],case['annotation'])))
        size = case['annotation']['size']
        for control in case['controls']:
            svg = control['svg']
            identical = {name:bool(np.array_equal(fn(case['svg'],*size),fn(svg,*size)))
                         for name, fn in [('MuPDF',render),('librsvg',render_librsvg)]}
            negative.append(dict(case_id=case['case_id'], damage=control['damage'],
                check=check_scene(svg,case['annotation']), raster_identical=identical))
    historical = [dict(file=r['file'], sha256=r['sha256'], check=check_scene(r['svg'],r['annotation']))
                  for r in manifest['historical']]
    targets = [dict(case_id=r['case_id'], check=check_scene(r['svg'],r['annotation']))
               for r in manifest['historical_targets']]
    summary = dict(positives=positive, negatives=negative, historical=historical, historical_targets=targets,
        sealed_files=json.loads((evidence/'seal.json').read_text(encoding='utf-8'))['files'],
        real_reserves_executed=False, converter_executions=0, model_promotions=0)
    write_json(output/'summary.json',summary)
    if (not all(r['check']['complete'] for r in positive+targets)
            or any(r['check']['complete'] for r in negative)):
        raise AssertionError('Logical segment controls failed; inspect summary')
    print(f'{len(positive)} positive scenes; {len(negative)} rejected controls; {len(historical)} historical rechecks')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.freeze:
        freeze(args.freeze)
    if args.output:
        evaluate(args.output, args.evidence)


if __name__ == '__main__':
    main()
