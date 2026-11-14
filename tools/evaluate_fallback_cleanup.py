"""Compare clean group construction against sealed synthetic development inputs."""
from __future__ import annotations

import argparse
import contextlib
import copy
import importlib.util
import json
from pathlib import Path
import time
from unittest.mock import patch
from xml.etree import ElementTree as ET

import cv2

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration
from tools.check_segment_scene import check_scene
from tools.evaluate_fallback_composition import EVIDENCE as COMPOSITION, MODULES, digest, review, damaged_variants
from tools.evaluate_segment_checker import EVIDENCE as CHECKER, verify
from tools.run_plan_b_variations import render

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/fallback_cleanup_v1'
RUNTIME = MODULES + ['imageCompositeConverterFallbackComposition.py']


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def freeze(folder=EVIDENCE):
    oracle = verify()
    old = json.loads((COMPOSITION/'manifest.json').read_text(encoding='utf-8'))
    folder.mkdir(parents=True, exist_ok=False)
    (folder/'inputs').mkdir()
    hashes = {}
    for name in RUNTIME:
        path = folder/'inputs'/name
        path.write_bytes((ROOT/'src/iCCModules'/name).read_bytes())
        hashes['inputs/'+name] = digest(path)
    cases = copy.deepcopy(old['cases'])
    for case in cases:
        case['annotation'] = next(c['annotation'] for c in oracle['historical_targets']
                                  if c['case_id'] == case['case_id'])
        path = folder/'inputs'/(case['case_id']+'.png')
        if not cv2.imwrite(str(path), render(case['svg'], case['width'], case['height'])):
            raise ValueError('Cannot freeze raster')
        hashes['inputs/'+path.name] = digest(path)
    write_json(folder/'manifest.json', dict(schema='fallback_cleanup_development_v1', cases=cases,
        seeds=old['seeds'], seconds=old['seconds'], max_probes=old['max_probes'], files=hashes,
        checker_seal_sha256=digest(CHECKER/'seal.json'), composition_sha256=digest(COMPOSITION/'manifest.json'),
        real_reserves_executed=False, model_promotions=0))
    write_json(folder/'seal.json', dict(manifest_sha256=digest(folder/'manifest.json')))


def verified(folder=EVIDENCE):
    verify()
    seal = json.loads((folder/'seal.json').read_text(encoding='utf-8'))
    if digest(folder/'manifest.json') != seal['manifest_sha256']:
        raise ValueError('Changed cleanup manifest')
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if (digest(CHECKER/'seal.json') != manifest['checker_seal_sha256']
            or digest(COMPOSITION/'manifest.json') != manifest['composition_sha256']):
        raise ValueError('Changed upstream evidence')
    for name, sha in manifest['files'].items():
        if digest(folder/name) != sha:
            raise ValueError('Changed cleanup input: '+name)
    if manifest['real_reserves_executed'] or manifest['model_promotions']:
        raise ValueError('Invalid reserve/promotion state')
    return manifest


@contextlib.contextmanager
def implementation(baseline, folder):
    if not baseline:
        from src.iCCModules.imageCompositeConverterFallbackStructure import explore_structures
        yield explore_structures
        return
    # Resolve every dynamic runtime import against the saved pre-change modules.
    import sys
    with patch.dict(sys.modules):
        loaded = {}
        for filename in [RUNTIME[1], RUNTIME[3], RUNTIME[0]]:
            name = 'src.iCCModules.'+filename[:-3]
            spec = importlib.util.spec_from_file_location(name, folder/'inputs'/filename)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            loaded[filename] = module
        yield loaded[RUNTIME[0]].explore_structures


def controls(svg):
    yield from damaged_variants(svg)
    root = ET.fromstring(svg)
    group = next(n for n in root if n.get('data-fallback-group') == 'crossed_panel_linkage')
    extra = copy.deepcopy(next(n for n in group if n.get('data-part') == 'diagonal0'))
    root.append(extra)
    yield 'duplicate_diagonal', ET.tostring(root, encoding='unicode')
    root.remove(extra)
    extra = ET.Element('{http://www.w3.org/2000/svg}line', x1='10', y1='24', x2='34', y2='24',
                       stroke='#888888', **{'stroke-width':'1'})
    root.append(extra)
    yield 'contour_overdraw', ET.tostring(root, encoding='unicode')


def evaluate(output, baseline=False, folder=EVIDENCE):
    manifest = verified(folder)
    output.mkdir(parents=True, exist_ok=False)
    rows, negatives = [], []
    with implementation(baseline, folder) as explore:
        for case in manifest['cases']:
            image = cv2.imread(str(folder/'inputs'/(case['case_id']+'.png')))
            for seed in manifest['seeds']:
                session = ImageSearch(SearchPolicy(seconds=manifest['seconds'], max_seconds=manifest['seconds']))
                started = time.monotonic()
                stem = case['case_id']+'-'+str(seed)
                with (output/(stem+'.log')).open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log), \
                        search_configuration(mode='portfolio', seed=seed, budget=384), image_search(session):
                    fitted, report = explore(case['seed_svg'], image, render(case['seed_svg'],144,144),
                        render, session, {}, mode='combined', max_probes=manifest['max_probes'])
                elapsed = time.monotonic()-started
                path = output/(stem+'.svg')
                path.write_text(fitted['svg'], encoding='utf-8')
                rows.append(dict(case_id=case['case_id'], seed=seed, elapsed_seconds=elapsed,
                    output_sha256=digest(path), check=check_scene(fitted['svg'],case['annotation']),
                    renderers=review(image,fitted['svg'],case), report=report, model_confirmed=bool(session.validated)))
                if not baseline and seed == manifest['seeds'][0]:
                    for damage, svg in controls(fitted['svg']):
                        negatives.append(dict(case_id=case['case_id'], damage=damage,
                            check=check_scene(svg,case['annotation']), renderers=review(image,svg,case)))
                write_json(output/'summary.json', dict(baseline=baseline, results=rows, negatives=negatives,
                    manifest_sha256=digest(folder/'manifest.json'), evaluator_sha256=digest(Path(__file__)),
                    source_sha256={n:digest((folder/'inputs' if baseline else ROOT/'src/iCCModules')/n) for n in RUNTIME},
                    real_reserves_executed=False, model_promotions=0))
                print(stem, rows[-1]['check']['complete'], flush=True)
    if any(r['elapsed_seconds'] > manifest['seconds']+.25 or r['report']['probe_count'] > manifest['max_probes']
           or r['model_confirmed'] or not all(v['complete'] for v in r['renderers'].values()) for r in rows):
        raise AssertionError('Pixel/detail/budget/draft regression')
    if not baseline and (not all(r['check']['complete'] for r in rows)
                         or any(r['check']['complete'] for r in negatives)):
        raise AssertionError('Independent inventory regression')
    return rows


def evaluate_cli(output, folder=EVIDENCE):
    from tools.evaluate_fallback_composition import evaluate_cli as run_cli
    manifest = verified(folder)
    # Existing CLI harness uses precisely the sealed construction/descriptions.
    original = json.loads((COMPOSITION/'manifest.json').read_text(encoding='utf-8'))
    for case, source in zip(manifest['cases'], original['cases']):
        assert all(case[k] == source[k] for k in source)
    rows = run_cli(output)
    for row, case in zip(rows, manifest['cases']):
        path = output/row['output_svg']
        row['output_sha256'] = digest(path)
        row['check'] = check_scene(path.read_text(encoding='utf-8'),case['annotation'])
    write_json(output/'independent_summary.json', dict(results=rows,
        manifest_sha256=digest(folder/'manifest.json'), evaluator_sha256=digest(Path(__file__)),
        source_sha256={n:digest(ROOT/'src/iCCModules'/n) for n in RUNTIME},
        real_reserves_executed=False, model_promotions=0))
    if not all(r['check']['complete'] for r in rows):
        raise AssertionError('CLI independent inventory regression')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--cli', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.freeze:
        freeze()
    if args.output:
        if args.cli:
            evaluate_cli(args.output)
        else:
            evaluate(args.output, args.baseline)
