"""Frozen known-audit development probes; never an independent-family acceptance."""
from __future__ import annotations

import argparse
from collections import Counter
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import time
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions
from src.iCCModules.imageCompositeConverterSearchPortfolio import search_configuration, configured_image_search
from tools.run_plan_b_variations import measure_quality, render as render_svg


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_regions(image, raster, regions):
    checks = []
    for region in regions:
        x, y, w, h = region['box']
        a, b = image[y:y+h, x:x+w], raster[y:y+h, x:x+w]
        mse = float(np.square(a.astype(float)-b.astype(float)).mean()/255**2)
        ae, be = cv2.Canny(a, 50, 140)>0, cv2.Canny(b, 50, 140)>0
        distance = cv2.distanceTransform((~be).astype('uint8'), cv2.DIST_L2, 3)
        recall = float(np.exp(-distance[ae]).mean()) if ae.any() else 0.
        checks.append(dict(**region, normalized_mse=mse, edge_recall=recall,
                           passed=mse <= .04 and recall >= .72))
    return checks


def freeze(snapshot, target):
    target.mkdir(parents=True, exist_ok=False)
    catalog = ET.parse('artifacts/images_to_convert/Finale_Wurzelformen_V3.xml')
    # Regions are annotated on the original raster before runtime development.
    annotations = {
        'AC0030_S': [('left_head', [0, 69, 10, 11]), ('right_head', [19, 69, 11, 11])],
        'AC0303_1_M': [('left_chord', [4, 11, 22, 49]), ('right_chord', [34, 11, 22, 49])],
        'AC0504_1M_sia': [('cross', [2, 5, 17, 19]), ('connector', [19, 3, 27, 24])],
        'GE0362': [('tools', [10, 8, 37, 42]), ('flame', [34, 25, 30, 37])],
    }
    cases = []
    for index, (name, regions) in enumerate(annotations.items()):
        folder = target / f'probe_{index:02d}'
        folder.mkdir()
        original = snapshot / 'files/artifacts/images_to_convert' / (name + '.jpg')
        svg = snapshot / 'files/artifacts/converted_images/converted_svgs' / (name + '.svg')
        shutil.copyfile(original, folder / 'original.jpg')
        shutil.copyfile(svg, folder / 'seed.svg')
        entry = next(e for e in catalog.findall('.//entry')
                     if any(Path(b.text).stem == name for b in e.findall('./bilder/bild')))
        (folder / 'description.txt').write_text(entry.findtext('beschreibung'), encoding='utf-8')
        h, w = cv2.imread(str(original)).shape[:2]
        cases.append(dict(case_id=folder.name, audit_name=name, width=w, height=h,
                          role='known_audit_development', regions=[dict(name=n, box=b) for n, b in regions]))
    shutil.copyfile('src/iCCModules/imageCompositeConverterVectorPolish.py', target / 'baseline.py')
    files = {p.relative_to(target).as_posix(): digest(p) for p in target.rglob('*') if p.is_file()}
    manifest = dict(schema='fallback_structure_development_v1', cases=cases, sha256=files,
                    seeds=[17, 29, 43], seconds=5., max_seconds=5., budget=384,
                    snapshot_sha256=digest(snapshot / 'snapshot.json'),
                    scope='Continuation from historical generated SVGs; not reference reconstruction or new families')
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def evaluate(inputs, output, arms, seeds, seconds):
    manifest = json.loads((inputs / 'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['sha256'].items():
        if digest(inputs / name) != expected:
            raise ValueError('Frozen input changed: '+name)
    output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('frozen_polish', inputs / 'baseline.py')
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    from src.iCCModules.imageCompositeConverterVectorPolish import polish_generated_svg
    results = []
    for case in manifest['cases']:
        folder = inputs / case['case_id']
        image = cv2.imread(str(folder / 'original.jpg'))
        svg = (folder / 'seed.svg').read_text(encoding='utf-8')
        assertions = description_assertions((folder / 'description.txt').read_text(encoding='utf-8'))
        for seed in seeds:
            for arm in arms:
                run = output / f"{case['case_id']}-{seed}-{arm}"
                run.mkdir()
                started = time.monotonic()
                with (run / 'search.log').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log):
                    with search_configuration(mode='portfolio', adaptive=True, seed=seed, budget=384,
                                              minimum_seconds=seconds, seconds=seconds, max_seconds=seconds):
                        with configured_image_search(case['case_id']) as session:
                            fn = baseline.polish_generated_svg if arm == 'baseline' else polish_generated_svg
                            kwargs = {} if arm == 'baseline' else dict(structure_mode=arm)
                            fitted = fn(svg, image, render_svg, assertions=assertions, **kwargs)
                            report = session.report()
                elapsed = time.monotonic()-started
                selected = fitted['svg'] if fitted else svg
                (run / 'output.svg').write_text(selected, encoding='utf-8')
                quality = measure_quality(image, selected)
                raster = render_svg(selected, case['width'], case['height'])
                cv2.imwrite(str(run / 'comparison.png'), cv2.hconcat([image, raster, cv2.absdiff(image, raster)]))
                regions = local_regions(image, raster, case['regions'])
                tags = Counter(n.tag.rsplit('}', 1)[-1] for n in ET.fromstring(selected).iter())
                results.append(dict(case_id=case['case_id'], audit_name=case['audit_name'], seed=seed, arm=arm,
                                    quality=quality, regions=regions, native_inventory=dict(tags),
                                    elapsed_seconds=elapsed, search=report,
                                    structure=(fitted or {}).get('structure_search'),
                                    output_sha256=digest(run / 'output.svg'), model_confirmed=False))
                print(case['audit_name'], seed, arm, quality['satisfactory'],
                      round(quality['metrics']['normalized_mse'], 5), flush=True)
                (output / 'summary.json').write_text(json.dumps(dict(schema='fallback_structure_comparison_v1',
                    manifest_sha256=digest(inputs / 'manifest.json'), seconds=seconds, max_seconds=seconds,
                    results=results), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return results


def review_study(root):
    """Re-measure saved vectors with both renderers and damaged controls."""
    from tools.evaluate_svg_text_baseline import render_librsvg
    inputs = root / 'inputs'
    manifest = json.loads((inputs / 'manifest.json').read_text(encoding='utf-8'))
    checks, negative = [], []
    for stage in ('baseline', 'comparison', 'cli'):
        report = json.loads((root / stage / 'summary.json').read_text(encoding='utf-8'))
        for row in report['results']:
            case = next(c for c in manifest['cases'] if c['case_id'] == row['case_id'])
            if stage == 'cli':
                svg_path = root / stage / row['arm'] / row['output_svg']
            else:
                svg_path = root / stage / f"{row['case_id']}-{row['seed']}-{row['arm']}" / 'output.svg'
            svg = svg_path.read_text(encoding='utf-8')
            image = cv2.imread(str(inputs / row['case_id'] / 'original.jpg'))
            renderers = {}
            for name, renderer in [('MuPDF', render_svg), ('librsvg', render_librsvg)]:
                raster = renderer(svg, case['width'], case['height'])
                renderers[name] = dict(quality=measure_quality(image, svg, render_fn=renderer),
                                       regions=local_regions(image, raster, case['regions']))
            checks.append(dict(stage=stage, case_id=row['case_id'], audit_name=case['audit_name'],
                               arm=row['arm'], seed=row.get('seed', 17),
                               svg_sha256=digest(svg_path), renderers=renderers,
                               model_confirmed=row.get('model_confirmed', False)))
            if row['case_id'] == 'probe_01' and row['arm'] == 'combined':
                for corruption in ('remove_lines', 'remove_one_line', 'shift_line', 'replace_circle'):
                    modified = ET.fromstring(svg)
                    lines = [n for n in modified.iter() if n.tag.rsplit('}', 1)[-1] == 'line']
                    for parent in modified.iter():
                        for child in list(parent):
                            if child in (lines if corruption == 'remove_lines' else lines[:1] if corruption == 'remove_one_line' else []):
                                parent.remove(child)
                    if corruption == 'shift_line':
                        for key in ('x1', 'x2'):
                            lines[0].set(key, str(float(lines[0].get(key))+8))
                    if corruption == 'replace_circle':
                        for n in modified.iter():
                            if n.tag.rsplit('}', 1)[-1] == 'circle':
                                cx, cy, radius = (float(n.get(k)) for k in ('cx', 'cy', 'r'))
                                n.tag = '{http://www.w3.org/2000/svg}rect'
                                for k in ('cx', 'cy', 'r'):
                                    del n.attrib[k]
                                n.attrib.update(x=str(cx-radius), y=str(cy-radius), width=str(2*radius), height=str(2*radius))
                    damaged = ET.tostring(modified, encoding='unicode')
                    render_checks = {}
                    for name, renderer in [('MuPDF', render_svg), ('librsvg', render_librsvg)]:
                        raster = renderer(damaged, case['width'], case['height'])
                        quality = measure_quality(image, damaged, render_fn=renderer)
                        regions = local_regions(image, raster, case['regions'])
                        render_checks[name] = dict(pixel_passed=quality['satisfactory'], regions=regions,
                                                   rejected=not quality['satisfactory'] or not all(c['passed'] for c in regions))
                    negative.append(dict(stage=stage, seed=row.get('seed', 17), corruption=corruption,
                                         renderers=render_checks))
    circle = [r for r in checks if r['case_id'] == 'probe_01' and r['arm'] == 'combined']
    passed = (len(circle) == 4 and all(q['quality']['satisfactory'] and all(r['passed'] for r in q['regions'])
              for row in circle for q in row['renderers'].values())
              and all(q['rejected'] for row in negative for q in row['renderers'].values())
              and not any(r['model_confirmed'] for r in checks))
    result = dict(schema='fallback_structure_independent_checks_v1', passed=passed,
                  saved_output_count=len(checks), cases=checks, negative_controls=negative)
    (root / 'checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    # Compact tracked evidence; full telemetry stays in the local run folders.
    summaries = {stage: json.loads((root / stage / 'summary.json').read_text(encoding='utf-8'))
                 for stage in ('baseline', 'comparison', 'cli')}
    source_files = ['src/iCCModules/imageCompositeConverterFallbackStructure.py',
                    'src/iCCModules/imageCompositeConverterVectorPolish.py',
                    'src/iCCModules/imageCompositeConverterIterationInitialization.py',
                    'src/imageConverterSample.py', 'tools/evaluate_fallback_structure.py',
                    'tests/test_fallback_structure.py']
    compact = dict(schema='fallback_structure_study_v1', manifest=manifest,
                   source_sha256={name: digest(Path(name)) for name in source_files},
                   comparisons=[])
    for stage, summary in summaries.items():
        for row in summary['results']:
            structure = row.get('structure') or row.get('continuation') or {}
            compact['comparisons'].append(dict(stage=stage, case_id=row['case_id'], audit_name=row['audit_name'],
                arm=row['arm'], seed=row.get('seed', 17), elapsed_seconds=row['elapsed_seconds'],
                satisfactory=(row.get('quality') or {}).get('satisfactory', row.get('satisfactory')),
                metrics=(row.get('quality') or {}).get('metrics', row.get('metrics')),
                regions=row.get('regions'), search=row.get('search'),
                svg_element_inventory=row.get('native_inventory'),
                structure={k:v for k,v in structure.items() if k != 'proposals'},
                model_confirmed=row.get('model_confirmed', False)))
    (root / 'summary.json').write_text(json.dumps(compact, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=passed, outputs=len(checks), negative_controls=len(negative))))
    return passed


def evaluate_cli(inputs, output, seconds=8., max_seconds=10.):
    """Real supervised CLI ablation, using only decoded frozen originals/text."""
    from tools.run_plan_b_variations import run_case
    manifest = json.loads((inputs / 'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['sha256'].items():
        if digest(inputs / name) != expected:
            raise ValueError('Frozen input changed: '+name)
    output.mkdir(parents=True, exist_ok=False)
    results = []
    old_mode = os.environ.get('ICC_FALLBACK_STRUCTURE_MODE')
    try:
        for mode in ('off', 'combined'):
            os.environ['ICC_FALLBACK_STRUCTURE_MODE'] = mode
            arm = output / mode
            arm.mkdir()
            for case in manifest['cases']:
                folder = arm / case['case_id'] / 'input'
                folder.mkdir(parents=True)
                original = inputs / case['case_id']
                image = cv2.imread(str(original / 'original.jpg'))
                name = case['case_id']
                cv2.imwrite(str(folder / (name+'.png')), image)
                root = ET.Element('root')
                entry = ET.SubElement(root, 'entry', kind='wurzelform', key=name)
                description = (original / 'description.txt').read_text(encoding='utf-8')
                ET.SubElement(entry, 'beschreibung').text = description
                ET.SubElement(ET.SubElement(entry, 'bilder'), 'bild').text = name+'.png'
                ET.ElementTree(root).write(folder / 'descriptions.xml', encoding='utf-8')
                result = run_case(dict(case_id=name, width=case['width'], height=case['height'],
                                       description=description), arm, timeout=40, iterations=64,
                                  extra_cli_args=('--search-seed', '17', '--search-seconds', str(seconds),
                                                  '--search-max-seconds', str(max_seconds),
                                                  '--search-min-seconds', '5'))
                result.update(arm=mode, audit_name=case['audit_name'])
                # Bind summary to the actual persistent result/quality state.
                result_map = arm / name / 'conversion/reports/conversion_result_map.json'
                if result_map.exists():
                    rows = json.loads(result_map.read_text(encoding='utf-8'))
                    row = next(iter(rows.values()), {})
                    result['model_confirmed'] = row.get('search_satisfactory', False)
                    result['continuation'] = (row.get('params') or {}).get('vector_continuation')
                results.append(result)
                print(case['audit_name'], mode, result['satisfactory'], result.get('failures'), flush=True)
                (output / 'summary.json').write_text(json.dumps(dict(schema='fallback_structure_cli_v1',
                    manifest_sha256=digest(inputs / 'manifest.json'), seconds=seconds,
                    max_seconds=max_seconds, minimum_seconds=5, seed=17, results=results),
                    ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    finally:
        if old_mode is None:
            os.environ.pop('ICC_FALLBACK_STRUCTURE_MODE', None)
        else:
            os.environ['ICC_FALLBACK_STRUCTURE_MODE'] = old_mode
    validate_cli_results(inputs, output, manifest, results)
    return results


def validate_cli_results(inputs, output, manifest, results):
    # Other known audit motifs remain negative. CI requires the narrow circle
    # improvement, both local chords, explicit draft status and actual outputs.
    from tools.evaluate_svg_text_baseline import render_librsvg
    circle = next(r for r in results if r['case_id'] == 'probe_01' and r['arm'] == 'combined')
    if any(r.get('blocked_svg_reads') or 'output_svg' not in r for r in results):
        raise AssertionError('CLI output/reference-access regression')
    path = output / 'combined' / circle['output_svg']
    image = cv2.imread(str(inputs / 'probe_01/original.jpg'))
    svg = path.read_text(encoding='utf-8')
    raster = render_librsvg(svg, 60, 60)
    if (not circle['satisfactory'] or circle.get('model_confirmed')
            or not measure_quality(image, svg, render_fn=render_librsvg)['satisfactory']
            or not all(r['passed'] for r in local_regions(image, raster, manifest['cases'][1]['regions']))):
        raise AssertionError('Frozen circle/detail/draft regression')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--arms', nargs='+', default=['baseline', 'primitives', 'lines', 'combined'])
    parser.add_argument('--seeds', nargs='+', type=int, default=[17, 29, 43])
    parser.add_argument('--seconds', type=float, default=5.)
    parser.add_argument('--cli', action='store_true')
    parser.add_argument('--review', type=Path)
    args = parser.parse_args()
    if args.review:
        if not review_study(args.review):
            raise SystemExit(1)
    elif args.freeze:
        freeze(args.snapshot, args.freeze)
    elif args.cli:
        evaluate_cli(args.inputs, args.output)
    else:
        evaluate(args.inputs, args.output, args.arms, args.seeds, args.seconds)


if __name__ == '__main__':
    main()
